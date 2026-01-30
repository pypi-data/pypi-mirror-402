'''Utility functions.'''
import typing
from collections import UserDict
import math
import tkinter as tk


TK_VERSION = tuple(int(n) for n in str(tk.TkVersion).split('.'))
'''
Get the tk version as an integer tuple.

Similar to `sys.version_info`.
'''

RDkT = typing.TypeVar('RDkT')
RDvT = typing.TypeVar('RDvT')


class ReorderableDict(UserDict, typing.Generic[RDkT, RDvT]):
    '''A mix of :py:class:`dict` and :py:class:`list`, a mapping that allows
    for reordering the key list, but still allows for fast random access to the
    values.

    Stores a regular :py:class:`dict`, plus a separate copy of the keys as a
    :py:class:`list`. These are synchronized.

    Should be used as a regular :py:class:`dict`, and there are special
    functions for manipulating the key order.

    See `index` and `at`, `insert` and `move`.
    '''
    def __init__(self, initialdata: typing.Optional[typing.Mapping[RDkT, RDvT]] = None):
        # Keep a list with key ordering
        self.__keys: typing.List[RDkT] = []
        super().__init__(initialdata or {})

    # # Read
    if __debug__:
        def __len__(self) -> int:
            # Implement `len(self)`
            dlen = len(self.data)
            klen = len(self.__keys)
            assert dlen == klen, 'len: data={dlen} keys={klen}'
            return dlen

    # __contains__: Use upstream

    def __iter__(self) -> typing.Iterator[RDkT]:
        # Implement `for _ in self`
        assert set(self.__keys) == set(self.data.keys())
        return iter(self.__keys)

    def keys(self) -> typing.Iterable[RDkT]:  # type: ignore[override]
        '''Return an iterator of keys, using the defined order.

        See Also:
            See the documentation on the upstream function `dict.keys`.

        .. note::

            The return value is technically different from the upstream
            function, but it should not matter in practice.
        '''
        # Implement `self.keys()`
        assert set(self.__keys) == set(self.data.keys())
        for k in self.__keys:
            yield k

    # values: Use upstream

    def items(self) -> typing.Iterator[typing.Tuple[RDkT, RDvT]]:  # type: ignore[override]
        '''Return an iterator of key-value tuples, using the ordered key list.

        See Also:
            See the documentation on the upstream function `dict.items`.

        .. note::

            The return value is technically different from the upstream
            function, but it should not matter in practice.
        '''
        # Implement `self.items()`
        assert set(self.__keys) == set(self.data.keys())
        for k in self.__keys:
            yield k, self.data[k]

    # get: Use upstream

    def index(self, key: RDkT, *args: typing.Any) -> typing.Optional[int]:
        '''Return the first index of the ``key`` in the ordered key list.

        Args:
            key: The key to search for.
            args: Passed to the upstream function

        Returns:
            If the ``key`` is not present in the mapping, return `None`.
            Otherwise, return the first index on the ordered key list.

        See Also:
            See the upstream function :ref:`list.index
            <python:typesseq-common>`
        '''
        if key in self.data:
            return self.__keys.index(key, *args)
        else:
            return None

    def at(self, index: int) -> RDkT:
        '''Return the ``key`` at ``index`` on the ordered key list.

        Supports all upstream functionality, such as negative indexes to count
        from the end of the list. Slices are technically supported, but frowned
        upon.

        Args:
            index: Index to locate the key

        Returns:
            If the ``index`` is out of bounds, raises `IndexError` (just like
            the upstream function).
            Otherwise, return the key located in that index.

            The following invariant holds:

            .. code:: python

                self.index(self.at(X)) == X

        See Also:
            See the upstream function :ref:`list.__getitem__
            <python:typesseq-common>`
        '''
        return self.__keys[index]

    # # Modify
    def clear(self) -> None:
        '''Remove all items from the mapping.

        See Also:
            See the upstream function `dict.clear`.
        '''
        super().clear()
        self.__keys.clear()
        assert set(self.__keys) == set(self.data.keys())

    def __setitem__(self, key: RDkT, value: RDvT) -> None:
        # Implement `self[key] = value`
        # Append or "Move" existing key to end
        if key in self.data:
            self.__keys.remove(key)
        super().__setitem__(key, value)
        self.__keys.append(key)
        assert set(self.__keys) == set(self.data.keys())

    # setdefault: Use upstream
    # update: Use upstream

    def __delitem__(self, key: RDkT) -> None:
        # Implement `del self[key]`
        super().__delitem__(key)
        self.__keys.remove(key)
        assert set(self.__keys) == set(self.data.keys())

    # pop: Use upstream
    # popitem: Use upstream

    def insert(self, index: int, key: RDkT, value: RDvT) -> None:
        '''Insert a key-value pair before the given index.

        To append a key-value pair, use ``self[key] = value``.
        To move an existing key, use `move`.

        Args:
            index: Index to insert the given key-value pair.
            key: The key to insert
            value: The value to insert

        See Also:

            See the upstream function :ref:`list.insert
            <python:typesseq-common>`.
        '''
        assert key not in self.data
        super().__setitem__(key, value)
        self.__keys.insert(index, key)
        assert set(self.__keys) == set(self.data.keys())

    def move(self, index: int, key: RDkT) -> None:
        '''Move an existing key before the given index.

        To append a key-value pair, use ``self[key] = value``.
        To insert a new key-value pair, use `insert`.

        Args:
            index: Index to move the existing key.
            key: The key to move
        '''
        assert key in self.data
        self.__keys.remove(key)
        self.__keys.insert(index, key)
        assert set(self.__keys) == set(self.data.keys())


def lcm_multiple(*numbers):
    '''
    Least Common Multiple: Multiple number

    .. note::

        Python 3.9 has `math.lcm <https://docs.python.org/3.9/library/math.html?highlight=math%20lcm#math.lcm>`_.
    '''
    if len(numbers) > 0:
        lcm = numbers[0]
        for n in numbers[1:]:
            lcm = lcm_single(lcm, n)
        return lcm
    else:
        return None


def lcm_single(a, b):
    '''
    Least Common Multiple: Single Pair
    '''
    if a == 0 and b == 0:
        return 0
    else:
        return int((a * b) / math.gcd(a, b))
