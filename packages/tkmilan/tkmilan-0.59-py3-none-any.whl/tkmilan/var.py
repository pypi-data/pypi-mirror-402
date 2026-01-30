'''
Variable classes. Extends the existing variable types defined in `tkinter`.
'''
import typing
import tkinter as tk
from functools import wraps
import collections.abc
import warnings

from . import model as tkmilan_model
from . import validation
if typing.TYPE_CHECKING:
    from . import mixin as tkmilan_mixin
    from . import RootWindow


class Variable(tk.Variable):
    '''Parent class for all value holders'''

    ignoreContainerTrace: bool = False
    '''When this variable is attached to a container, do not consider it for
    tracing purposes.
    '''

    ready: bool = True
    '''Check if the variable is ready for usage.

    Defaults to `True`, this exists for compatibility with `aggregator`.
    '''


class Boolean(tk.BooleanVar, Variable):
    '''Value holder for `bool`.'''
    pass


class Double(tk.DoubleVar, Variable):
    '''Value holder for `float`.'''
    pass


class Int(tk.IntVar, Variable):
    '''Value holder for `int`.'''
    pass


class String(tk.StringVar, Variable):
    '''Value holder for `str`.'''
    pass


# TypeVar
objT = typing.TypeVar('objT')
'''Generic Type-Checking variable type for `ObjectList`.

This is a `typing.TypeVar`, to be used only when typechecking. See `typing`.
'''
spvT = typing.TypeVar('spvT')
'''Generic Type-Checking variable type for `SpecParsed`.

This is a `typing.TypeVar`, to be used only when typechecking. See `typing`.
'''


def trace(var: Variable, function: typing.Callable, *,
          trace_mode: tkmilan_model.TraceModeT = 'write',
          trace_initial: bool = False,
          **kwargs: typing.Any) -> str:
    '''Trace the variable ``var``.

    There is no Python documentation, see ``Tk`` :tcl:`trace variable
    <trace.htm#M14>` documentation.

    The ``function`` arguments will be:

    - ``var``: The traced variable
    - ``etype``: The trace mode (see ``trace_mode``)
    - The other given ``kwargs``

    It is possible to run the function as soon as the trace is defined. This is
    useful if the trace is used to keep state in sync.

    Args:
        var: The traced variable.
        function: The callback function.
        trace_mode: The trace mode, when should the callback be invoked.
            `None` when running on the initial function call (see ``trace_initial``).
        trace_initial: Run the callback function on start.
            Runs async (similar to `model.TimeoutIdle`).
        kwargs: Passed to the callback function.

    Returns:
        Return the function identifier, as stored by ``Tk``.
    '''
    assert not isinstance(var, nothing), f'{var}: Tracing "nothing" is unsupported'

    @wraps(function)
    def trace_wrapper(name: str, index: str, etype: str):  # "Real" tk function
        assert isinstance(name, str) and isinstance(etype, str)
        if __debug__:
            assert etype in ['read', 'write', 'unset'], f'Unsupported trace mode: {etype}'
            etype = typing.cast(tkmilan_model.TraceModeT, etype)
        return function(var, etype, **kwargs)

    if trace_initial:
        assert hasattr(var, '_root'), f'Invalid variable object: {var!r}'

        @wraps(function)
        def trace_wrapper_initial():
            return function(var, None, **kwargs)

        rw: 'RootWindow' = var._root
        rw.after_idle(trace_wrapper_initial)  # No need for a `model.TimeoutIdle` here
    return var.trace_add(
        trace_mode,
        trace_wrapper,
    )


# Specification Tower
class Spec(String):
    '''Abstract parent class for validated `String` variables.

    This variable tracks the label value, but also its valid states, which
    makes it so that the state type is a `model.VState`, not a simple `str`.

    Note that this might specify a complex validation, not just a list of
    discrete values, nor a continous range, for example.

    .. note::

        This should not be instanced directly, it's a parent class to be subclassed
        on other variable types.

    See Also:
        For a countable variant of this, see `SpecCountable`. For a valued
        variant of this, see `SpecParsed`.

    .. automethod:: __contains__
    '''
    container: typing.Container[str]
    '''The container object representing the specification.

    Follows the `container <collections.abc.Container>` class interface.
    '''
    ldefault: str
    '''The default label to be shown to the user.'''

    def __new__(cls,
                spec: typing.Optional[validation.VSpec] = None,
                *args, **kwargs):
        if cls in (Spec, SpecCountable, SpecParsed):
            if isinstance(spec, validation.VSpec):
                if __debug__:
                    spec_class = spec.__class__
                    new_class = MAP_VALIDATIONS[spec.__class__]
                assert spec_class in MAP_VALIDATIONS, f'{spec_class.__qualname__}: No mapping for specified variable'
                assert issubclass(new_class, cls), f'{new_class.__qualname__}: Not a subclass for {cls.__qualname__}'
                return MAP_VALIDATIONS[spec.__class__](spec, *args, **kwargs)
            else:
                raise ValueError(f'{cls.__qualname__}: Do not instance directly, abstract class')
        else:
            return super().__new__(cls)

    # @typing.override
    def get(self) -> tkmilan_model.VState[bool]:  # type: ignore[override]
        '''Returns the value of the variable, as `VState`.

        The ``value`` alternates between `True` for valid labels, and `None`
        for invalid labels.
        '''
        label: str = super().get()
        assert isinstance(self.container, collections.abc.Container), f'{self} missing container'
        # Use True/None for "automatic" validation
        value = True if label in self.container else None
        return tkmilan_model.VState(label=label, value=value)

    def set(self, state: typing.Union[str, tkmilan_model.VState[bool]]):
        '''Set the variable to ``state``.

        Only the label is set, either for direct `str` or `VState`.

        .. note::

            In debug mode, when setting the variable using a `VState`, the
            ``value`` itself is re-validated.
        '''
        assert isinstance(self.container, collections.abc.Container), f'{self} missing container'
        label: str  # Support setting labels and VState
        if isinstance(state, tkmilan_model.VState):
            label = state.label
            assert state.value is (True if label in self.container else None), f'Weird value:: {state}'
        else:  # Setting a simple label
            assert isinstance(state, str)
            label = state
        return super().set(label)

    def __contains__(self, label: str) -> bool:
        '''Check if the ``label`` label satisfies the specification.

        Wraps the `container` interface.

        Should be used as ``label in Spec``.
        '''
        assert isinstance(self.container, collections.abc.Container), f'{self} missing container'
        return label in self.container


class SpecCountable(Spec):
    '''Abstract parent class for validated `String` variables, with countable
    amount of valid alternatives.

    This is an alternative to `Spec`, when the amount of possible valid values is countable.

    .. note::

        This should not be instanced directly, it's a parent class to be subclassed
        on other variable types.

    See Also:
        For a simpler version of this, see `Spec`. For a valued variant of the
        base class, see `SpecParsed`.

    .. automethod:: __contains__
    .. automethod:: __len__
    '''
    def lall(self) -> typing.Sequence[str]:
        '''Get all valid labels supported by this variable.'''
        # Default Implementation
        assert isinstance(self.container, collections.abc.Sized), f'Variable "{self}" missing sizable container'
        assert isinstance(self.container, typing.Iterable), f'Variable "{self}" missing iterable container'
        return tuple(self.container)

    def __len__(self) -> int:
        '''Count how many labels this specification contains.

        Should be used as ``len(SpecCountable)``.
        '''
        assert isinstance(self.container, collections.abc.Sized), f'{self} missing sizable container'
        return len(self.container)


class SpecParsed(Spec, typing.Generic[spvT]):
    '''Abstract parent class for validated `String` variables, with a parsed
    value (instead of a boolean validation).

    .. note::

        This should not be instanced directly, it's a parent class to be subclassed
        on other variable types.

    See Also:
        For a simpler version of this, see `Spec`. For a countable variant of
        the base class, see `SpecCountable`.
    '''
    container: typing.Mapping[str, spvT]
    '''The container object representing the specification, a mapping between
    label and value.

    Follows the `mapping <collections.abc.Mapping>` class interface.
    '''
    lempty: str = ''
    '''The default label for invalid values.

    This is only necessary on rare circumstances.
    Should map to an invalid value.
    '''

    # @typing.override
    def get(self) -> tkmilan_model.VState[typing.Optional[spvT]]:  # type: ignore[override]
        '''Returns the value of the variable, as `VState`.

        The ``value`` alternates between the parsed label, and `None` for
        invalid labels.

        See Also:
            The base class version is `Spec.get`. It is compatible, but with
            different semantics.
        '''
        label: str = super(String, self).get()
        return tkmilan_model.VState(label=label, value=self.container.get(label))

    # @typing.override
    def set(self, state: typing.Union[str, tkmilan_model.VState[typing.Optional[spvT]]]):  # type: ignore[override]
        '''Set the variable to ``state``.

        Only the label is set, either for direct `str` or `VState`.

        .. note::

            In debug mode, when setting the variable using a `VState`, the
            ``value`` itself is re-validated.

            In debug mode, mark the variable with ``_complexValidation = True``
            to skip the validation about broken VState.

        See Also:
            The base class version is `Spec.set`. It is compatible, but with
            different semantics.
        '''
        label: str  # Support setting labels and VState
        if isinstance(state, tkmilan_model.VState):
            label = state.label
            if __debug__:
                wvalue = self.container.get(label)
                if state.value != wvalue and getattr(self, '_complexValidation', False) is False:
                    warnings.warn(f'{self}: Setting broken VState: new={state!r} value={self.container.get(label)!r}')
        else:  # Setting a simple label
            assert isinstance(state, str)
            label = state
        return super(String, self).set(label)

    def getLabel(self, value: typing.Optional[spvT]) -> str:
        '''Return the first label corresponding to the given ``value``.

        This is not very efficient, and the mapping might not be bi-injective.
        It's mostly implemented for completeness' sake.

        Returns:
            `lempty` if the value is not valid.
        '''
        # This is very inneficcient, but always works
        for label, cvalue in self.container.items():
            if value == cvalue:
                return label
        assert self.lempty not in self.container, f'{self} has an valid "empty" label: "{self.lempty}"'
        return self.lempty


# Other Special Variables
class nothing(Variable):
    '''Value holder for `None`.

    Useful for widgets that don't store anything, like buttons.
    '''
    def get(self):
        return None

    def set(self, value: None):
        pass


class aggregator(Variable):
    '''Synthetic value holder for an aggregation of other variables.

    Useful for container widgets.
    '''
    _default: str = ''
    tout: typing.Optional[tkmilan_model.TimeoutIdle]
    '''Hold the `TimeoutIdle <model.TimeoutIdle>` object that indicates
    this variable is setup.

    Since this variable is a synthetic variable, useful only when triggered
    from other function, it needs configuration before it can be used. For
    optimisation reasons, this is not done right on ``__init__`` like most
    other variables.

    Defaults to `None`, indicating it is not ready. See `ready`.
    '''
    # TODO: Save the child variables? `children: typing.Set[Variable]`
    def __init__(self, master=None, value=None, name=None, *, cwidget: 'tkmilan_mixin.MixinWidget'):
        super().__init__(master, value, name)
        self.tout = None
        self.cwidget = cwidget

    @property
    def ready(self) -> bool:  # type: ignore[override]
        '''Check if the variable is ready for usage.'''
        return self.tout is not None

    def get(self) -> None:
        assert self.ready, f'{self}: Unprepared aggregator variable'
        super().get()  # Trigger variable read
        return None

    def set(self, value: None = None):
        assert self.ready, f'{self}: Unprepared aggregator variable'
        return super().set('')  # Trigger variable write


# Actual Implementations
class StringList(Variable):
    '''Value holder for a list of `str`.

    In ``Tk``, everything is a string and the syntax for lists is similar to
    Python, so this is technically supported, but sounds like a coincidence.

    Works well, though.

    See Also:
        `ObjectList` for an arbitrary list of Python objects.
    '''
    _default: typing.Iterable = []

    def get(self) -> typing.Iterable[str]:
        return [x for x in super().get()]

    def set(self, value: typing.Iterable[str]) -> None:
        return super().set([x for x in value])


class ObjectList(Variable, typing.Generic[objT]):
    '''Generic value holder for a sequence of object of `objT` type.

    Just keep an instance variable with the "actual" value. Pretend the value
    is just an empty `str`.

    See Also:
        `StringList`: Simpler version of this, supports only `str`.
    '''
    # The dummy read/writes are necessary for traces to work correctly
    _default: typing.Sequence[objT] = []
    __actual_value: typing.Optional[typing.Sequence[objT]] = None

    def get(self) -> typing.Sequence[objT]:
        super().get()  # Dummy read
        return self.__actual_value or list(self._default)

    def set(self, value: typing.Sequence[objT]) -> None:
        self.__actual_value = value
        return super().set('')  # Dummy write


class StaticList(SpecCountable):
    '''Specifies a static list of labels.

    Args:
        spec: The list validation object.
        name: Name of the variable (passed to `String`).
            Optional, defaults to an autogenerated name.

    .. note::

        The ``name`` is defined in a global namespace, common to the
        entire application.
    '''
    def __init__(self, spec: validation.StaticList, *,
                 name: typing.Optional[str] = None,
                 # Do not document "master", internal-ish
                 master: typing.Optional[tk.Widget] = None,
                 ):
        assert isinstance(spec, validation.StaticList), f'Invalid Spec: {spec}'
        super().__init__(master=master, name=name, value=spec.ldefault)
        # Set `Spec` parameters
        self.container = spec
        self.ldefault = spec.ldefault


class StaticMap(SpecCountable, SpecParsed[spvT]):
    '''Specifies a static mapping between labels and its corresponding values.

    Args:
        spec: The mapping validation object.
        name: Name of the variable (passed to `String`).
            Optional, defaults to an autogenerated name.

    .. note::

        The ``name`` is defined in a global namespace, common to the
        entire application.
    '''
    def __init__(self, spec: validation.StaticMap[spvT], *,
                 name: typing.Optional[str] = None,
                 # Do not document "master", internal-ish
                 master: typing.Optional[tk.Widget] = None,
                 ):
        assert isinstance(spec, validation.StaticMap), f'Invalid Spec: {spec}'
        super().__init__(master=master, name=name, value=spec.ldefault)
        assert self.lempty not in spec, f'{self.__class__.__qualname__}: Valid Empty String: {self.lempty}'
        # Set `SpecCountable`/`SpecParsed` parameters
        self.container = spec
        self.rlabels = spec.rlabels
        self.ldefault = spec.ldefault

    def getLabel(self, value: typing.Optional[spvT]) -> str:
        '''Return the label corresponding to the given ``value``.

        This is very efficient, and the mapping is enforced to be bi-injective.

        See Also:
            The upstream function this aliases is `SpecParsed.getLabel`.
        '''
        if value is None:
            return self.lempty
        else:
            return self.rlabels.get(value, self.lempty)


class Limit(SpecParsed[int]):
    '''Represent a range to limit a value, for simple integers.

    The range is represented as the ``container`` parameter, one of the
    `LimitBounded <validation.LimitBounded>` or ``LimitUnbounded
    <validation.LimitUnbounded>``.

    When instancing directly, the ``limit`` parameter will instance the right
    subclass. This means this class can not be instanced directly without
    arguments, and when instance with a validation representation, it will
    create an object of the right subclass.

    Arguments:
        limit: The validation representation for this type. **Mandatory**.

    All other arguments are passed to the right subclass.

    See Also:
        The supported subclasses:

        - `LimitBounded`
        - `LimitUnbounded`
    '''
    container: typing.Union[validation.LimitBounded, validation.LimitUnbounded]

    def __new__(cls,
                limit: typing.Union[validation.LimitBounded, validation.LimitUnbounded],
                *args, **kwargs,
                ):
        if cls is Limit:
            if isinstance(limit, validation.LimitBounded):
                return LimitBounded(limit, *args, **kwargs)
            elif isinstance(limit, validation.LimitUnbounded):
                return LimitUnbounded(limit, *args, **kwargs)
            else:
                raise NotImplementedError
        else:
            # Sub-Class, instance as usual
            return super().__new__(cls)

    def get_spinargs(self, *, dincrement: float = 1.0) -> typing.Tuple[float, float, float]:
        '''Get all `SpinboxN` value arguments.

        Arguments:
            dincrement: Default ``increment`` value, when the limit does not
                support it.
                Defaults to ``1.0``.

        Return Value:
            Returns a tuple with three floating point values:

            - ``from``
            - ``to``
            - ``increment``
        '''
        infinite: float = float('+inf')
        sfrom: float
        if self.container.min is None:
            sfrom = -1 * infinite
        else:
            assert isinstance(self.container.min, typing.SupportsFloat), f'Invalid min value: {self.container.min!r}'
            sfrom = float(self.container.min)
        sto: float
        if self.container.max is None:
            sto = +1 * infinite
        else:
            assert isinstance(self.container.max, typing.SupportsFloat), f'Invalid max value: {self.container.max!r}'
            sto = float(self.container.max)
        sincrement: float = float(self.container.step or dincrement)
        if not self.container.imin:
            sfrom += sincrement
        if not self.container.imax:
            sto -= sincrement
        if __debug__:
            if isinstance(self.container, validation.LimitBounded):
                rrange = self.container.rrange
                assert int(sfrom) in rrange
                assert int(sto) in rrange
                assert int(sincrement) == int(rrange.step)
        return sfrom, sto, sincrement

    def getLabel(self, value: typing.Optional[spvT]) -> str:
        '''Return the label corresponding to the given ``value``.

        This is very efficient.

        See Also:
            The upstream function this aliases is `SpecParsed.getLabel`.
        '''
        return self.container.get_label(value, invalid=self.lempty)


class LimitBounded(Limit, SpecCountable):
    '''A bounded variant of the `Limit` range.

    Since this is bounded, it's a countable specification.

    Args:
        limit: The `LimitBounded <validation.LimitBounded>` range object..
        name: Name of the variable (passed to `String`).
            Optional, defaults to an autogenerated name.

    .. note::

        The ``name`` is defined in a global namespace, common to the
        entire application.
    '''
    def __init__(self, limit: validation.LimitBounded, *,
                 name: typing.Optional[str] = None,
                 # Do not document "master", internal-ish
                 master: typing.Optional[tk.Widget] = None,
                 ):
        assert isinstance(limit, validation.LimitBounded), f'Invalid LimitBounded: {limit}'
        super().__init__(master=master, name=name, value=limit.ldefault)
        # Set `SpecCountable`/`SpecParsed` parameters
        self.container: validation.LimitBounded = limit
        self.ldefault = limit.ldefault


class LimitUnbounded(Limit):
    '''An unbounded variant of the `Limit` range.

    Since this is unbounded, it's not a countable specification.

    Args:
        limit: The `LimitUnbounded <validation.LimitUnbounded>` range object.
        name: Name of the variable (passed to `String`).
            Optional, defaults to an autogenerated name.

    .. note::

        The ``name`` is defined in a global namespace, common to the
        entire application.
    '''
    def __init__(self, limit: validation.LimitUnbounded, *,
                 name: typing.Optional[str] = None,
                 # Do not document "master", internal-ish
                 master: typing.Optional[tk.Widget] = None,
                 ):
        assert isinstance(limit, validation.LimitUnbounded), f'Invalid LimitUnbounded: {limit}'
        super().__init__(master=master, name=name, value=limit.ldefault)
        # Set `SpecCountable`/`SpecParsed` parameters
        self.container: validation.LimitUnbounded = limit
        self.ldefault = limit.ldefault


MAP_VALIDATIONS = {
    validation.StaticList: StaticList,
    validation.StaticMap: StaticMap,
    validation.LimitBounded: LimitBounded,
    validation.LimitUnbounded: LimitUnbounded,
}
'''Mapping between `validation.VSpec` representations, and the corresponding variable class.'''
if __debug__:
    vspec_subclasses = set(validation.VSpec.__subclasses__())
    map_subclasses = set(MAP_VALIDATIONS.keys())
    delta_subclasses_names = [cls.__qualname__ for cls in map_subclasses.symmetric_difference(vspec_subclasses)]
    assert len(delta_subclasses_names) == 0, f'Missing `MAP_VALIDATIONS` for {" ".join(delta_subclasses_names)}'


# Custom Validation Settings
def __vfn_limit(vstate, why):
    assert why is not None, 'Need `fnSimple=False`'
    wvalidation = why.widget
    assert isinstance(wvalidation.variable, Spec), f'{wvalidation}: Not a widget with Spec variable'
    assert why.tt is not None, f'{wvalidation}: Not Tooltip configured'  # Don't repeat the tooltip handling
    vspec = wvalidation.variable.container
    vstate_raw = vspec.fn(vstate.label)
    if vstate.valid:
        # Valid; No Tooltip
        message = ''
        why.tt.disable()
    else:
        # Invalid:
        if vstate_raw is None:
            # Invalid: bad Spec
            message = 'Spec Violation'
        else:
            # Invalid: outside the value spec
            message = f'Value out of Spec: {vspec}'
        why.tt.enable()
    if __debug__:
        from . import TooltipValidation  # Avoid circular import
        assert isinstance(why.tt, TooltipValidation)
    why.tt.wstate = message
    return vstate.valid


ValidationLimit = tkmilan_model.VSettings(
    fnSimple=False, ttSimple=False,
    fn=__vfn_limit,
)
'''Configure widget validation to enhance the tooltip information with `Spec`
violation information.

This distinguishes between an invalid value, and a value outside the `Spec`.
This is more apparent on `Limit`.

This is only experimental code, but should work as intended on this narrow
case.

To be used as:

.. code:: python

    Widget(self, ...
                validation=var.ValidationLimit,
                ...
                ).putTooltip()
'''
