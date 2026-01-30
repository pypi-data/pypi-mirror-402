'''Validation objects for `Spec <var.Spec>` variables.

All validation representations should be defined here, as standalone objects
that can be tested directly, without ``Tk`` dependencies.
:py:mod:`tkmilan.var` includes the ``Tk`` interfaces.
'''
import typing
import warnings
import math
from dataclasses import dataclass, field as dc_field, InitVar
from collections import UserDict
from abc import ABCMeta
import operator
from numbers import Number

# Limit String
LIMIT_ISTRING: typing.Mapping[bool, str] = {
    True: '[',
    False: ']',
}
'''Mapping between inclusion boolean, and boundary representation.'''
LIMIT_INFINITE: str = '∞'
'''String representation of infinite boundary.'''

INFO_FORMAT_BASE: typing.Mapping[int, typing.Tuple[str, str]] = {
    2: ('0b', 'b'),
    8: ('0o', 'o'),
    10: ('', 'd'),
    16: ('0x', 'X'),
}
'''Metadata for `LimitBounded.format_value`, per supported ``base``.'''

limT = typing.TypeVar('limT', bound=Number)
'''Generic Type for `var.Limit`.

This is a `typing.TypeVar`, to be used only when typechecking. See `typing`.
'''
smvT = typing.TypeVar('smvT')
'''Generic Type-Checking variable type for `SpecParsed`.

This is a `typing.TypeVar`, to be used only when typechecking. See `typing`.
'''


class VSpec(metaclass=ABCMeta):
    '''Abstract parent class for all validation representations.'''
    pass


class StaticList(typing.Tuple[str, ...], VSpec):
    '''Represent a static list of labels, therefore a :py:class:`tuple` of
    `str`.

    The default label must be explicitely given, either directly as
    ``default``, or indirectly as ``defaultIndex``. Either way is validated to
    verify the default is a valid label.

    Arguments:
        values: Values to construct the list.
        default: Default label. Optional.
        defaultIndex: Index for the default label, in the ``values`` sequence.
            Optional.
    '''
    ldefault: str
    '''The default label'''

    def __new__(cls, values: typing.Iterable[str], *,
                default: typing.Optional[str] = None,
                defaultIndex: typing.Optional[int] = None,
                ):
        self = super().__new__(cls, values)
        assert default is not None or defaultIndex is not None, f'{self.__class__.__qualname__}: Missing default'
        if default is None:
            if defaultIndex is None or defaultIndex < 0 or defaultIndex >= len(self):
                raise ValueError(f'{self.__class__.__qualname__}: Invalid defaultIndex: {defaultIndex}')
            ldefault = self[defaultIndex]
        else:
            ldefault = default
        assert ldefault is not None, f'{self.__class__.__qualname__}: Missing default label'
        self.ldefault = ldefault
        if self.ldefault not in self:
            raise ValueError(f'{self.__class__.__qualname__}: Invalid Default Label: {self.ldefault!r}')
        return self


class StaticMap(UserDict, typing.Mapping[str, smvT], typing.Generic[smvT], VSpec):
    '''Represent a static mapping between labels and its corresponding values.

    The ``mapping`` parameter matches labels to values. This must be
    bi-injective, that is, there cannot be values corresponding to multiple
    labels.

    The default label must be explicitely given, either directly as
    ``defaultLabel``, or indirectly as ``defaultValue``. Either way is
    validated to verify the default is a valid label.

    Args:
        mapping: Mapping between labels and values.
        defaultLabel: Default label. Optional.
        defaultValue: Default value, to derive the default label. Optional.
    '''
    ldefault: str
    '''The default label'''
    vdefault: smvT
    '''The default value'''
    rlabels: typing.Mapping[smvT, str]
    '''The reverse mapping, between values and its corresponding labels.'''

    def __init__(self, mapping: typing.Mapping[str, smvT], *,
                 defaultLabel: typing.Optional[str] = None,
                 defaultValue: typing.Optional[smvT] = None,
                 ):
        super().__init__(mapping)
        assert all(isinstance(lbl, str) for lbl in self.keys()), f'{self.__class__.__qualname__}: Mapping Keys must all be strings'
        rlabels: typing.Mapping[smvT, str] = {val: lbl for lbl, val in self.items()}
        if len(self) != len(rlabels):
            raise ValueError(f'{self.__class__.__qualname__}: Mapping is not bi-injective')
        assert defaultValue is not None or defaultLabel is not None, f'{self.__class__.__qualname__}: Missing default'
        # Setup the "other" default
        if defaultValue is None:
            if defaultLabel not in self:
                raise ValueError(f'{self.__class__.__qualname__}: Label {defaultLabel!r} not in mapping')
            assert defaultLabel is not None
            defaultValue = self[defaultLabel]
        if defaultLabel is None:
            if defaultValue not in rlabels:
                raise ValueError(f'{self.__class__.__qualname__}: Value {defaultValue!r} not in mapping')
            defaultLabel = rlabels[defaultValue]
        assert defaultValue is not None and defaultValue in rlabels
        assert defaultLabel is not None and defaultLabel in self
        self.rlabels = rlabels
        self.ldefault = defaultLabel
        self.vdefault = defaultValue
        if __debug__:
            if None in self.values():
                nstr = ' '.join(k for k, v in self.items() if v is None)
                warnings.warn(f'Bad `StaticMap`, `None` aliases invalid values: keys={nstr}', stacklevel=2)


def StaticMapLabels(fn: typing.Callable[[str], smvT], lst: typing.Sequence[str], *, defaultIndex: typing.Optional[int] = None, **kwargs) -> StaticMap[smvT]:
    '''Turn a list of labels into a mapping, by applying a function to get the value.

    Wrapper for `StaticMap`.
    '''
    if defaultIndex is not None:
        kwargs['defaultLabel'] = lst[defaultIndex]
    return StaticMap({e: fn(e) for e in lst}, **kwargs)


def StaticMapValues(fn: typing.Callable[[smvT], str], lst: typing.Sequence[smvT], *, defaultIndex: typing.Optional[int] = None, **kwargs) -> StaticMap[smvT]:
    '''Turn a list of values into a mapping, by applying a function to get the label.

    Wrapper for `StaticMap`.
    '''
    if defaultIndex is not None:
        kwargs['defaultValue'] = lst[defaultIndex]
    return StaticMap({fn(e): e for e in lst}, **kwargs)


@dataclass
class LimitBounded(typing.Mapping[str, int], VSpec):
    '''Represent a bounded range to limit a value, for integers (`int`).

    The range can be made to remove the limits themselves with ``imin`` and
    ``imax``. The default is the limit being closed on both sides.

    The range is bounded, there are no infinite limits. The ``step`` parameter
    controls if all intermediate values are valid.

    The following arguments are not available on the final object:

    Arguments:
        min_entry: Minimum value, as string or number.
        max_entry: Maximum value, as string or number.
        default: Default value to be set, as string, number, or `None` to
            choose a valid value (the default).
            When `None`, a sane value is chosen. If both ``imin`` and ``imax``
            as `False`, ``0`` is chosen, which might not be included on the
            range.
            Configures the default label.

    The following parameters are available on the final object:

    Arguments:
        fn: A function that turns a string into `number <numbers.Number>`.
            Usually some kind of parser.
        step: The step amount for the range of values.
            Defaults to ``1``.
        imin: Include the limit on the minimum value itself.
            Defaults to `True`.
        imax: Include the limit on the maximum value itself.
            Defaults to `True`.

    The following parameters are available on the final object, calculated from the arguments:

    Parameters:
        min: Minimum value, as number.
        min_value: Minimum value, as string. Good for showing to the user.
        max: Maximum value, as number.
        max_value: Maximum value, as string. Good for showing to the user.
        rrange: The `range` object implementing this object.
        ldefault: The default label to be shown to the user.


    See Also:
        Use `LimitUnbounded` if the limit is unbounded in any direction, or if
        the `number <numbers.Number>` is not an `int` subclass.

    .. automethod:: __len__
    .. automethod:: __getitem__
    .. automethod:: __iter__
    .. automethod:: __contains__
    '''
    min_entry: InitVar[typing.Union[int, str]]
    max_entry: InitVar[typing.Union[int, str]]
    fn: typing.Callable[[str], typing.Optional[int]]
    step: int = 1
    imin: bool = True
    imax: bool = True
    # Calculations
    min: int = dc_field(init=False)
    max: int = dc_field(init=False)
    min_value: str = dc_field(init=False)
    max_value: str = dc_field(init=False)
    rrange: range = dc_field(init=False)
    ldefault: str = dc_field(init=False)
    # __init__ variable
    default: InitVar[typing.Union[int, str, None]] = None

    def __post_init__(self, min_entry: typing.Union[int, str], max_entry: typing.Union[int, str],
                      default: typing.Union[int, str, None] = None):
        if isinstance(min_entry, str):
            self.min_value = min_entry
            min_obj = self.fn(self.min_value)
            if min_obj is None:
                raise ValueError(f'Invalid Minimum: {min_entry!r}')
            self.min = min_obj
        else:
            assert isinstance(min_entry, int)
            self.min = min_entry
            self.min_value = str(self.min)
        if isinstance(max_entry, str):
            self.max_value = max_entry
            max_obj = self.fn(self.max_value)
            if max_obj is None:
                raise ValueError(f'Invalid Maximum: {max_entry!r}')
            self.max = max_obj
        else:
            assert isinstance(min_entry, int)
            self.max = max_entry
            self.max_value = str(self.max)
        # Range
        assert isinstance(self.step, int), f'Unsupported step: {self.step!r}'
        if self.step < 1:
            raise ValueError(f'Invalid Step: {self.step!r}')
        imin: int = 0 if self.imin else self.step
        imax: int = 1 if self.imax else 0
        assert isinstance(self.min, int) and isinstance(self.max, int), f'Unsupported Limit type: {self.min!r}/{self.max!r}; use a `LimitUnbounded`'
        rfrom, rto = self.min + imin, self.max + imax
        assert rto > rfrom
        self.rrange = range(rfrom, rto, self.step)
        assert len(self.rrange) > 0
        if self.imax and self.max not in self.rrange:
            # Bad maximum value, help the user
            lastvalue = self.rrange[-1]
            nextvalue = lastvalue + self.step
            assert lastvalue in self.rrange
            assert nextvalue not in self.rrange
            raise ValueError(f'Invalid Step/Maximum: {self.max} not in range; use {lastvalue} or {nextvalue}')
        elif not self.imax:
            if self.rrange[-1] + self.step != self.max:
                nextvalue = self.rrange[-1] + self.step
                raise ValueError(f'Invalid Step/Maximum: {self.max} is not the correct maximum; use {nextvalue}')
        if __debug__:
            assert (self.min in self.rrange) is self.imin
            assert (self.max in self.rrange) is self.imax
        # Default
        if default is None:
            self.ldefault = {
                (True, True): self.min_value,
                (True, False): self.min_value,
                (False, True): self.max_value,
                (False, False): '0',  # `]x,y[`, just choose something
            }[(self.imin, self.imax)]
        elif isinstance(default, str):
            self.ldefault = default
        else:
            assert isinstance(default, int)
            self.ldefault = str(default)
            default_roundtrip = self.fn(self.ldefault)
            if default_roundtrip is None or default != default_roundtrip:
                raise ValueError(f'{self}: Invalid Default Roundtrip: {default!r} != {default_roundtrip!r}')
        if self.ldefault not in self:
            dmessage = '; set a valid "default"' if self.ldefault == '0' else ''
            raise ValueError(f'{self}: Invalid Default Label: {self.ldefault!r}{dmessage}')
        if __debug__:
            if self.fn in (int,):
                warnings.warn('Bad `fn`, throws exception on error, use `fn.valNumber`', stacklevel=3)
            if '' in self:
                warnings.warn('The empty string should be invalid', stacklevel=3)

    def __str__(self):
        lrange = LIMIT_ISTRING[self.imin]
        rrange = LIMIT_ISTRING[not self.imax]
        return '%s%s%s, %s%s' % (  # noqa: UP031
            lrange,
            self.min_value,
            '' if self.step == 1 else f', step={self.step}',
            self.max_value,
            rrange,
        )

    def __len__(self) -> int:
        '''Count the amount of valid values.

        Should be used as ``len(LimitBounded)``.
        '''
        return len(self.rrange)

    def __iter__(self) -> typing.Iterator[str]:
        '''Iterate through all valid labels.

        Should be used as:

        .. code:: python

            for label in LimitBounded:
                print(label)
        '''
        for n in self.rrange:
            yield str(n)

    def __getitem__(self, label: str) -> int:
        '''Get the value corresponding to the label.

        If the value is invalid, `KeyError` is raised.

        Should be used as ``LimitBounded[label]``.
        '''
        value = self.fn(label)
        if value is not None and value in self.rrange:
            return value
        else:
            raise KeyError

    def __contains__(self, label: object) -> bool:
        '''Check if the label is valid. Must be a `str`.

        Should be used as ``label in LimitBounded``.
        '''
        if isinstance(label, str):
            return self.get(label, None) is not None
        else:
            return False

    # TODO: On Python 3.11:: -> typing.Self
    def w(self, **kwargs) -> 'LimitBounded':
        '''Create a new `LimitBounded` with different parameters.

        Reuse all parameters which are not given.

        The only parameters that should be changed are:

        - imin: Include the limit on the minimum value itself.
        - imax: Include the limit on the maximum value itself.
        - step: The step amount for the range of values.
        - default: Default value to be set.
        '''
        if __debug__:
            extras = set(kwargs) - set(['imin', 'imax', 'step', 'default'])
            if len(extras) > 0:
                warnings.warn(f'Use a brand new limit: w({", ".join(extras)})', stacklevel=2)
        return self.__class__(**{
            'min_entry': self.min, 'max_entry': self.max, 'step': self.step,
            'fn': self.fn,
            'imin': self.imin, 'imax': self.imax,
            'default': self.ldefault,
            **kwargs,
        })

    def get_label(self, value: typing.Optional[typing.Any], *, invalid: str = '') -> str:
        '''Get a label that produces the given value.

        The invalid label is produced for all non-`int` values.

        Args:
            value: The value object, or `None` to produce an invalid label.
            invalid: The invalid label. Make sure this is really invalid.
        '''
        label = str(value)
        if value is not None and isinstance(value, int) and label in self:
            return label
        else:
            assert invalid not in self, 'Valid "invalid" value: {invalid!r}'
            return invalid

    def count_padsize(self, base: int = 10) -> int:
        '''Count the strictly necessary amount of padding digits for the range
        of values.

        Depending on the range of supported values, this will calculate the
        necessary amount of digits to store all possible values, when formatted
        with the given base. This allows for a label with fixed size.

        Args:
            base: The base for the positional numeral system, amount of
                different symbols. For example, hexadecimal uses ``base=16``.


        See Also:
            Use `format_value` to format a value directly.
        '''
        assert base > 0
        assert isinstance(self.min, int) and isinstance(self.max, int), f'Unsupported Limit type: {self.min!r}/{self.max!r}'
        maxn: int = max(abs(self.min), abs(self.max))
        return math.ceil(math.log(maxn + 1, base))

    def format_value(self, value: int, *,
                     base: typing.Literal[2, 8, 10, 16],
                     invalid: str = '') -> str:
        '''Format a given ``value`` with the strictly necessary amount of
        padding.

        Uses standard format for integers with the given ``base``.
        The amount of padding is given by the `count_padsize` function.

        Args:
            value: The value to format
            base: The base for the positional numeral system, amount of
                different symbols. For example, hexadecimal uses ``base=16``.
            invalid: The invalid label. Make sure this is really invalid.
        '''
        assert isinstance(self.min, int) and isinstance(self.max, int), f'Unsupported Limit type: {self.min!r}/{self.max!r}'
        if str(value) in self:
            prefix, fchar = INFO_FORMAT_BASE[base]
            return ('%s{:0%d%s}' % (prefix, self.count_padsize(base), fchar)).format(value)
        else:
            assert invalid not in self, 'Valid "invalid" value: {invalid}'
            return invalid


@dataclass
class LimitUnbounded(typing.Mapping[str, limT], typing.Generic[limT], VSpec):
    '''Represent a potentially unbounded range to limit a value, generic for
    any `number <numbers.Number>` type.

    The range can be made to remove the limits themselves with ``imin`` and
    ``imax``. The default is the limit being closed on both sides.

    The range is unbounded, which mean some limits might be infinite.
    If both limits are infinite and this is intended, set ``infinite`` to avoid
    warnings.

    The following arguments are not available on the final object:

    Arguments:
        min_entry: Minimum value, as string or number.
            `None` represents an infinite value.
        max_entry: Maximum value, as string or number.
            `None` represents an infinite value.
        default: Default value to be set, as string, number, or `None` to
            choose a valid value (the default).
            When `None`, a sane value is chosen. If both ``imin`` and ``imax``
            as `False`, ``0`` is chosen, which might not be included on the
            range.
            Configures the default label.
        infinite: Do not warn about completely unbounded min and max.

    The following parameters are available on the final object:

    Arguments:
        fn: A function that turns a string into `number <numbers.Number>`.
            Usually some kind of parser.
        step: The step amount for the range of values.
            Changing this value is unsupported for now, it included for
            compatibility with `LimitBounded`.
            Defaults to ``None``.
        imin: Include the limit on the minimum value itself.
            Defaults to `True`.
        imax: Include the limit on the maximum value itself.
            Defaults to `True`.

    The following parameters are available on the final object, calculated from the arguments:

    Parameters:
        min: Minimum value, as number. `None` if infinite.
        min_value: Minimum value, as string. Good for showing to the user.
        max: Maximum value, as number. `None` if infinite.
        max_value: Maximum value, as string. Good for showing to the user.
        ldefault: The default label to be shown to the user.

    .. automethod:: __getitem__
    .. automethod:: __contains__
    '''
    min_entry: InitVar[typing.Union[limT, str, None]]
    max_entry: InitVar[typing.Union[limT, str, None]]
    fn: typing.Callable[[str], typing.Optional[limT]]
    imin: bool = True
    imax: bool = True
    step: typing.Optional[limT] = None
    # Calculations
    min: typing.Optional[limT] = dc_field(init=False)
    max: typing.Optional[limT] = dc_field(init=False)
    min_value: str = dc_field(init=False)
    max_value: str = dc_field(init=False)
    ldefault: str = dc_field(init=False)
    # __init__ variable
    default: InitVar[typing.Union[limT, str, None]] = None
    infinite: InitVar[bool] = False

    def __post_init__(self, min_entry: typing.Union[limT, str, None], max_entry: typing.Union[limT, str, None],
                      default: typing.Union[limT, str, None],
                      infinite: bool):
        if min_entry is None:
            self.min = None
            self.min_value = f'-{LIMIT_INFINITE}'
            self.imin = False
        elif isinstance(min_entry, str):
            self.min_value = min_entry
            min_obj = self.fn(self.min_value)
            if min_obj is None:
                raise ValueError(f'Invalid Minimum: {min_entry!r}')
            self.min = min_obj
        else:  # isinstance(min_entry, limT)
            self.min = min_entry
            self.min_value = str(self.min)
        if max_entry is None:
            self.max = None
            self.max_value = f'+{LIMIT_INFINITE}'
            self.imax = False
        elif isinstance(max_entry, str):
            self.max_value = max_entry
            max_obj = self.fn(self.max_value)
            if max_obj is None:
                raise ValueError(f'Invalid Maximum: {max_entry!r}')
            self.max = max_obj
        else:  # isinstance(min_entry, limT)
            self.max = max_entry
            self.max_value = str(self.max)
        if self.step is not None:
            raise ValueError(f'Invalid Step: Not Supported `{self.step!r}`')
        # Default
        if default is None:
            self.ldefault = {
                (True, True): self.min_value,
                (True, False): self.min_value,
                (False, True): self.max_value,
                (False, False): '0',  # Any number is valid (or `]x,y[`, just choose something)
            }[(self.min is not None and self.imin, self.max is not None and self.imax)]
        elif isinstance(default, str):
            self.ldefault = default
        else:  # isinstance(default, limT)
            self.ldefault = str(default)
            default_roundtrip = self.fn(self.ldefault)
            if default_roundtrip is None or default != default_roundtrip:
                raise ValueError(f'{self}: Invalid Default Roundtrip: {default!r} != {default_roundtrip!r}')
        if self.ldefault not in self:
            raise ValueError(f'{self}: Invalid Default Label: {self.ldefault!r}')
        if __debug__:
            if self.fn in (int,):
                warnings.warn('Bad `fn`, throws exception on error, use `fn.valNumber`', stacklevel=3)
            if not infinite and (self.min is None and self.max is None):
                warnings.warn('No limit to possible values', stacklevel=3)
            if '' in self:
                warnings.warn('The empty string should be invalid', stacklevel=3)

    def __iter__(self):
        raise NotImplementedError

    def __len__(self):
        raise NotImplementedError

    def __str__(self):
        lrange = LIMIT_ISTRING[self.imin]
        rrange = LIMIT_ISTRING[not self.imax]
        # TODO: Support "step"
        return '%s%s, %s%s' % (  # noqa: UP031
            lrange,
            self.min_value,
            self.max_value,
            rrange,
        )

    def __getitem__(self, label: str) -> limT:
        '''Get the value corresponding to the label.

        If the value is invalid, `KeyError` is raised.

        Should be used as ``LimitUnbounded[label]``.
        '''
        value = self.fn(label)
        if value is None:
            raise KeyError
        else:
            OPERATOR: typing.Mapping[bool, typing.Callable[..., bool]] = {True: operator.le, False: operator.lt}
            omin = OPERATOR[self.imin]
            omax = OPERATOR[self.imax]
            if all((
                (omin(self.min, value) if self.min is not None else True),  # vmin
                (omax(value, self.max) if self.max is not None else True),  # vmax
                # TODO: Support "step"
                # ((value - self.min) % self.step == 0 if self.step is not None else True)  # step
            )):
                return value
            else:
                raise KeyError

    def __contains__(self, label: object) -> bool:
        '''Check if the label is valid. Must be a `str`.

        Should be used as ``label in LimitUnbounded``.
        '''
        if isinstance(label, str):
            return self.get(label, None) is not None
        else:
            return False

    # TODO: On Python 3.11:: -> typing.Self
    def w(self, **kwargs) -> 'LimitUnbounded':
        '''Create a new `LimitUnbounded` with different parameters.

        Reuse all parameters which are not given.

        The only parameters that should be changed are:

        - imin: Include the limit on the minimum value itself.
        - imax: Include the limit on the maximum value itself.
        - step: The step amount for the range of values.
        - default: Default value to be set.
        '''
        if __debug__:
            extras = set(kwargs) - set(['imin', 'imax', 'step', 'default'])
            if len(extras) > 0:
                warnings.warn(f'Use a brand new limit: w({", ".join(extras)})', stacklevel=2)
        return self.__class__(**{
            'min_entry': self.min, 'max_entry': self.max, 'step': self.step,
            'fn': self.fn,
            'imin': self.imin, 'imax': self.imax,
            'infinite': self.min is None and self.max is None,
            'default': self.ldefault,
            **kwargs,
        })

    def get_label(self, value: typing.Optional[limT], *, invalid: str = '') -> str:
        '''Get a label that produces the given value.

        Args:
            value: The value object, or `None` to produce an invalid label.
            invalid: The invalid label. Make sure this is really invalid.
        '''
        label = str(value)
        if value is not None and label in self:
            return label
        else:
            assert invalid not in self, 'Valid "invalid" value: {invalid!r}'
            return invalid
