'''Models to store complex information in unambiguous ways.

Mostly implemented as `dataclasses`.
'''
import sys
import logging
import warnings
from dataclasses import dataclass, field as dc_field, fields, astuple as dc_astuple, replace as dc_replace, asdict as dc_asdict, InitVar
import enum
import abc
from functools import cached_property
import math
import time
from pathlib import Path
from fractions import Fraction
import tkinter as tk
import typing

from . import util

if typing.TYPE_CHECKING:
    import types
    # Avoid circular imports
    from . import mixin
    from . import var
    from . import EntryMultiline, Tooltip

ImageTk: 'typing.Optional[types.ModuleType]'  # Optional Dependency: Pillow
try:
    from PIL import ImageTk
except ImportError:
    ImageTk = None


vsT = typing.TypeVar('vsT')
wsT = typing.TypeVar('wsT')
wsST = typing.TypeVar('wsST')
TraceModeT = typing.Literal['read', 'write', 'unset']
'''The supported operations to watch for a trace.

There is no Python documentation, see ``Tcl`` :tcl:`trace variable
<trace.htm#M14>` documentation.
'''
compoundT = typing.Union['CP', bool, None]
ValidateWhenT = typing.Literal['focus', 'focusin', 'focusout', 'key', 'all', 'none']
'''The supported validation modes, to be set ``when`` arguments.

There is no Python documentation, see ``Tk`` :tk:`trace validation modes
<ttk_entry.htm#M35>` documentation.
'''
ValidateWhyT = typing.Literal[
    # Native
    'key', 'focusin', 'focusout',
    'forced',
    # Synthetic
    'initial', 'self',
]
'''The supported validation modes, to be given for ``why`` arguments.

Includes native and synthetic types.

There is no Python documentation, see ``Tk`` :tk:`trace validation return mode
<ttk_entry.htm#M49>` documentation.
'''
ValidateST = typing.Literal[-1, 0, 1]
'''The supported validation action types.

Their meanings are as follows:

- ``-1``: Post-Validation. The most common usage.
- ``0``: Pre-Validation: Delete
- ``1``: Pre-Validation: Insert

There is no Python documentation, see ``Tk`` :tk:`trace validation action type
<ttk_entry.htm#M43>` documentation.
'''
NotebookTabStateT = typing.Literal[
    # Shown
    'normal', 'disabled',
    # Hidden
    'hidden',
]
'''The supported `NotebookTab` state types.

Their meanings are as follows:

- ``normal``: A regular tab
- ``disabled``: The tab is shown, but disabled. This means it cannot be
   selected, not even programatically.
- ``hidden``: The tab is not shown. If you show it (using `Notebook.wselect`),
   it goes back to ``normal`` state.

There is no Python documentation, see ``Tk`` :tk:`notebook tab state type
<ttk_notebook.htm#M11>` documentation.
'''


# Image Types
__image_types = {
}
# TODO: Support more image types with Pillow
if util.TK_VERSION >= (8, 6):
    # PNG supported out of the box on "tk8.6"
    __image_types['png'] = tk.PhotoImage
else:
    # Require Pillow on older versions
    assert ImageTk is not None, f'Tk {util.TK_VERSION}: Unsupported PNG images: Install "pillow"'
    __image_types['png'] = ImageTk.PhotoImage
# GIF is supported everywhere
__image_types['gif'] = tk.PhotoImage

IMAGE_TYPES = __image_types
'''Supported image types, and corresponding loaders.

See `ImageCache`.
'''

logger = logging.getLogger(__name__)
logger_layout = logging.getLogger('%s.layout' % __name__)
logger_ft = logging.getLogger('%s.ft' % __name__)


class FileType(typing.Tuple[str]):
    def __new__(cls, *args: str):
        true_args = (f'.{s}' for s in args)
        return super().__new__(cls, true_args)

    def matches(self, path: Path):
        if __debug__:
            suff = tuple(path.suffixes[-len(self):])
            res = '==' if self == suff else '<=>'
            logger_ft.debug('F[%s]=%s %s %s', path, suff, res, self)
        return path.name.endswith(self.suffix)

    @cached_property
    def suffix(self):
        return ''.join(self)

    @cached_property
    def pattern(self):
        return f'*{self.suffix}'


class FileTypes(typing.Dict[str, FileType]):
    def allbut(self, *keys: str):
        return {k: v for k, v in self.items() if k not in keys}

    def only(self, *keys: str):
        return {k: self[k] for k in keys}


class EventModifier(enum.Enum):
    '''Event Modifier bitfield object

    Includes all supported event modifier checks.

    There is no Python documentation, nor ``Tk`` documentation anywhere. This
    list was created by trial and error.

    You can read some semi-official references related to this:

    - https://github.com/python/cpython/issues/71481
    - https://wiki.tcl-lang.org/page/Modifier+Keys

    .. note::
        The documentation shows the values for the OS where the documentation
        is built (usually Linux). The values might be different on other
        platforms, like Windows.
    '''
    Control = 0x4
    '''The :kbd:`Ctrl` key'''
    Shift = 0x1
    '''The :kbd:`Shift` key'''
    Alt = 0x20000 if sys.platform == 'win32' else 0x8
    '''The :kbd:`Alt` key'''
    AltGr = 0x20000 | 0x4 if sys.platform == 'win32' else 0x80
    '''The :kbd:`AltGr` key.

    On Windows, this is equivalent to :kbd:`Ctrl` and :kbd:`Alt`.
    '''
    NumLock = 0x8 if sys.platform == 'win32' else 0x10
    '''The :kbd:`NumLock` lock key.

    This is a lock key, can be active even if the user is not clicking any
    key.'''
    CapsLock = 0x2
    '''The :kbd:`CapsLock` lock key.

    This is a lock key, can be active even if the user is not clicking any
    key.'''
    ScrollLock = 0x20 if sys.platform == 'win32' else None
    '''The :kbd:`ScrollLock` lock key.

    On Linux, this might not be supported.

    This is a lock key, can be active even if the user is not clicking any
    key.'''

    def __init__(self, value: typing.Optional[int]):
        if not (sys.platform == 'win32' or sys.platform.startswith('linux')):
            raise NotImplementedError(f'Unsupported Platform: {sys.platform}')

    def on(self, event: tk.Event) -> bool:
        '''Check if the modifier is being applied in the given event.

        Very useful to check if modifiers are being applied in a cross-platform
        manner. Use like this:

        .. code:: python

            def onEvent(self, event):
                if EventModifier.Control.on(event):
                    print('Pressing Control')
        '''
        assert isinstance(self.value, int), f'Invalid EventModifier: {self!r}'
        if isinstance(event.state, str):
            logger.warning('Weird Event state: %r', event)
            return False  # Weird state
        else:
            assert isinstance(event.state, int), f'Invalid Event state: {event.state!r}'
            return event.state & self.value == self.value

    # TODO: On Python 3.11:: -> typing.Self
    @classmethod
    def ALL(cls, event: tk.Event) -> 'typing.Set[EventModifier]':
        ''''''  # Internal, do not document
        # This is very slow, only for debug purposes
        assert __debug__, 'Do not call this in production'
        lst = set()
        for m in cls:
            if m.value is not None and m.on(event):
                lst.add(m)
        return lst


@dataclass
class WStyle:
    '''Widget style object.

    This is super class of all widget-specific style objects.

    All subclass arguments should be optional, with a nice-looking default
    value.

    Args:
        _default: Does this represent a default value?
            When this is set (only for class ``__init__`` definitions), the
            values can be safely overriden.

    Note:
        Not to be confused with `tkinter.ttk.Style` objects.
    '''
    _default: bool = dc_field(repr=False, compare=False, default=False)


class SStyle:
    '''Static Widget Style Options.

    These objects are just common values, useful in several locations. They
    must be calculated once, but used everywhere.

    See Also:
        `DStyle` for static style values.

    .. note::

        This is technically a class, but should not be instanced, it only
        matters to join all values in a single logical location.
    '''
    Size_PadButton_Small: str = '-3' if sys.platform == 'win32' else '-1'
    '''Size: ``padding`` for making a `Button` as small as possible.

    This will keep the button somewhat visible.

    See ``Font_Button_Small``.
    '''
    Font_Button_Small: str = 'TkSmallCaptionFont'
    '''Font: Font for making a `Button` as small as possible.

    This will keep the button somewhat visible.

    See also ``Size_PadButton_Small``.
    '''
    # TODO: Combine `Size_PadButton_Small` and `Font_Button_Small`?
    Size_YF_Frame: int = -17 if sys.platform == 'win32' else -19
    '''Size: ``y`` for insetting a frame in a complex frame.

    Works for `FrameLabelled` and friends: `FrameStateful`, `FrameRadio`, etc.
    '''
    # TODO: `Size_YF_Frame`:: Store `place` arguments, keyed by "anchor": CP.
    Size_PadWidget_FrameSeparator: int = 8
    '''Size: ``padding`` with the same size as a frame separator (e.g.
    `FrameLabelled`, `FrameStateful`, `FrameRadio`).

    When stacking a `FrameRadio` and a `Radio` button vertically, pad the
    `Radio` widget on the left side and align it to the left, to obtain aligned
    `Radio` widgets.
    '''

    def __init__(self):
        raise ValueError('Not to be Instanced')

    @classmethod
    def items(cls):
        '''Get a list of names and values.

        Similar to `dict.items`. Mostly useful for debug.
        '''
        assert __debug__, 'Do not call this in production'  # Maybe this should be a warning only?
        for name in dir(cls):
            if not name.startswith('__'):
                value = getattr(cls, name)
                if not callable(value):
                    yield (name, value)


class DStyle(enum.Enum):
    '''Dynamic Widget Style Options.

    These objects are replaced by the corresponding values, calculated
    dynamically from the theme values.

    See Also:
        `SStyle` for static style values.
    '''
    Color_FG = enum.auto()
    '''Color: Normal Widgets ``foreground``'''
    Color_BG = enum.auto()
    '''Color: Normal Widgets ``background``'''
    Color_FG_Disabled = enum.auto()
    '''Color: Disabled Widgets ``foreground``'''
    Color_BG_Selected = enum.auto()
    '''Color: Selected Widgets ``background``'''
    Font_Default = enum.auto()
    '''Font: Default Font'''

    if __debug__:
        def __repr__(self) -> str:
            return f'{self.__class__.__qualname__}.{self.name}'


class CP(enum.Enum):
    '''A Cardinal Point.

    Usually, this defines an anchor point for alignment.

    Corresponds neatly to the same `tkinter` values, but it's simpler to validate
    as an `enum`.

    Here is a table of cardinal points, for visual reference:

    .. tabularcolumns:: |L|C|L|

    .. csv-table:: Cardinal Points

      `NW <CP.NW>`,`N <CP.N>`,`NE <CP.NE>`
      `W <CP.W>`,`center <CP.center>`,`E <CP.E>`
      `SW <CP.SW>`,`S <CP.S>`,`SE <CP.SE>`
    '''
    # value: typing.Optional[str]  # TODO: Improve labelAnchor usages?

    N = tk.N
    '''North'''
    S = tk.S
    '''South'''
    E = tk.E
    '''East'''
    W = tk.W
    '''West'''
    NE = tk.NE
    '''NorthEast = `N` + `E`'''
    NW = tk.NW
    '''NorthWest = `N` + `W`'''
    SE = tk.SE
    '''SouthEast = `S` + `E`'''
    SW = tk.SW
    '''SouthWest = `S` + `W`'''
    center = tk.CENTER
    '''Center element on the container. Not a "cardinal point" in the usual sense.'''
    default = None
    '''OS-specific cardinal point.'''

    if __debug__:
        def __repr__(self) -> str:
            return f'{self.__class__.__qualname__}.{self.name}'


CP_Compound: typing.Mapping[compoundT, str] = {
    CP.default: 'none',  # `image` if present, otherwise `text`
    CP.N: tk.BOTTOM,
    CP.S: tk.TOP,
    CP.E: tk.LEFT,
    CP.W: tk.RIGHT,
    # Special Compound values
    True: 'image',  # No Label, only Image
    False: 'text',  # No Image, only Label
    None: tk.CENTER,  # Image and Label, centered
}
'''The ``compound`` configuration setting.

This is the mapping between `CP` and the ``compound`` configuration string used in several locations.

Besides the cardinal points `CP.N`, `CP.S`, `CP.E`, `CP.W`, there are also special cases:

- `CP.default`: Show only the image if given, otherwise show only label.
- `True`: Show only the image
- `False`: Show only the label
- `None`: Show image and label, both centered

There is no Python documentation, see ``Tk`` :tk:`compound
<ttk_widget.htm#M-compound>` documentation.
'''

CP_ScrollAnchor: typing.Mapping[CP, typing.Tuple[float, float]] = {
    CP.N: (-0.5, +0.0),
    CP.S: (-0.5, -1.0),
    CP.E: (-1.0, -0.5),
    CP.W: (+0.0, -0.5),
    CP.NE: (-1.0, +0.0),
    CP.NW: (+0.0, +0.0),
    CP.SE: (-1.0, -1.0),
    CP.SW: (+0.0, -1.0),
    CP.center: (-0.5, -0.5),
}
'''The `ScrolledWidget`/`Scrolled` scroll anchor configuration setting.

The scroll function aligns the relative coordinates to the `CP.NW` corner, this
includes the adjustments necessary to support all cardinal points.

See `ScrolledWidget.scrollTo` and `Scrolled.scrollTo`.
'''
assert all(cp in CP_ScrollAnchor for cp in CP if cp not in [CP.default])
assert all(-1.0 <= fpoint <= 1.0 for tpl in CP_ScrollAnchor.values() for fpoint in tpl)


class Justification(enum.Enum):
    '''A text justification anchor.

    Corresponds to neatly to the same `tkinter` values, but it's simpler to
    validate as an `enum`.

    Note:
        Not all widgets support ``NoJustify``, sometimes it's necessary to not
        pass the ``justify`` option at all.
    '''
    NoJustify = None
    '''OS-specific justification.'''
    Left = tk.LEFT
    '''Justify Left'''
    Center = tk.CENTER
    '''Justify Center'''
    Right = tk.RIGHT
    '''Justify Right'''

    if __debug__:
        def __repr__(self) -> str:
            return f'{self.__class__.__qualname__}.{self.name}'


Justification_CP: typing.Mapping[Justification, CP] = {
    Justification.NoJustify: CP.default,
    Justification.Left: CP.W,
    Justification.Center: CP.center,
    Justification.Right: CP.E,
}
'''Conversion between `Justification` and `CP` objects.

This is useful to convert between types, since some widgets have weird
interactions between ``justify`` and ``anchor`` settings.
'''
assert set(Justification_CP.keys()) == set(Justification), 'Justification_CP does not cover all cases'


@dataclass
class PixelSize:
    width: int
    height: int

    @property
    def aspect_ratio(self):
        return Fraction(self.width, self.height)

    tuple = dc_astuple
    '''Get this information as a tuple.'''

    def reduce(self, ratio):
        return dc_replace(self, width=self.width // ratio, height=self.height // ratio)


@dataclass
class GridCoordinates:
    '''Widget Grid Coordinates.

    This includes information about widgets, even if they span more than one
    row or column. It should fully specify the widget grid location.

    The "location string" format is the following: ``R[+RS]xC[+CS]``

    - **R**: Row
    - **RS**: Row Span (optional)
    - **C**: Column
    - **CS**: Column Span (optional)

    .. automethod:: __str__
    '''
    row: int
    column: int
    rowspan: int = 1
    columnspan: int = 1

    dict = dc_asdict
    '''Get this information as a dictionary.'''

    tuple = dc_astuple
    '''Get this information as a tuple.

    Note:
        The order of fields is not ideal.
    '''

    def __post_init__(self):
        assert self.rowspan > 0 and self.columnspan > 0, f'Invalid Spans: R{self.rowspan} C{self.columnspan}'

    def __str__(self):
        '''Convert the grid coordinates into a "location string".

        For the reverse operation, see `parse`.
        '''
        _row = '%d+%d' % (self.row, self.rowspan)
        _col = '%d+%d' % (self.column, self.columnspan)
        return f'{_row}x{_col}'.replace('+1', '')

    def rows(self) -> typing.Iterator[int]:
        '''Generate all grid row indexes spanned by the widget.'''
        yield from range(self.row, self.row + self.rowspan)

    def columns(self) -> typing.Iterator[int]:
        '''Generate all grid column indexes spanned by the widget.'''
        yield from range(self.column, self.column + self.columnspan)

    @classmethod
    def parse(cls, string: str) -> 'GridCoordinates':
        '''Parse a "location string" to a grid coordinates object.

        For the reverse operation, convert the object to `str` (see `__str__`).
        '''
        r, c = string.split('x')
        if '+' in r:
            row, rowspan = [int(n) for n in r.split('+')]
        else:
            row = int(r)
            rowspan = 1
        if '+' in c:
            column, columnspan = [int(n) for n in c.split('+')]
        else:
            column = int(c)
            columnspan = 1
        return cls(row, column, rowspan=rowspan, columnspan=columnspan)


@dataclass
class GridSize:
    '''Widget Grid Size.

    This includes information about all child widgets for a `container
    <mixin.ContainerWidget>`.
    '''
    rows: int
    columns: int

    tuple = dc_astuple
    '''Get this information as a tuple.'''


@dataclass
class WidgetGeometry:
    '''Hold the geometry information for a widget.

    See the `wgeometry <mixin.MixinWidget.wgeometry>` function to obtain this
    information from any widget.

    Args:
        x: X coordinate for the widget's topleft corner, relative to the root
            window
        y: Y coordinate for the widget's topleft corner, relative to the root
            window
        w: Width of the widget.
            Optional, see also ``h`` and `sized`.
        h: Height of the widget.
            Optional, see also ``w`` and `sized`.
    '''
    x: int
    y: int
    w: typing.Optional[int] = None
    h: typing.Optional[int] = None

    if __debug__:
        def __post_init__(self):
            if (self.w is None) is not (self.h is None):
                raise ValueError(f'Weird size setting: w={self.w} h={self.h}')

    @property
    def sized(self) -> bool:
        '''Check if the object has size information'''
        return self.w is not None and self.h is not None

    def tk_geometry(self):
        '''Convert the values into a "geometry string".

        This is mostly used on ``Tk`` functions.
        '''
        str_position = f'+{self.x}+{self.y}'
        if self.sized:
            str_size = f'={self.w}x{self.h}'
            return f'{str_size}{str_position}'
        else:
            return str_position

    def __str__(self):
        str_position = f'@{self.x},{self.y}'
        if self.sized:
            str_size = f'{self.w}x{self.y}'
            return f'{str_size}{str_position}'
        else:
            return str_position


@dataclass
class WidgetView:
    '''Hold the view information for a widget. This is important for scrollable
    widgets.

    See the `wview <mixin.MixinWidget.wview>` function to obtain this
    information from any widget.

    There is no Python documentation, see ``Tk`` :tk:`widget xview
    <ttk_widget.htm#M23>` and :tk:`widget yview <ttk_widget.htm#M28>`
    documentation.

    Args:
        xview: Tuple containing the start and end fractions of the width
            currently visible. Optional, `None` if the widget does not support
            scrolling on the X axis.
        yview: Tuple containing the start and end fractions of the height
            currently visible. Optional, `None` if the widget does not support
            scrolling on the Y axis.
    '''
    xview: typing.Optional[typing.Tuple[float, float]]
    yview: typing.Optional[typing.Tuple[float, float]]

    if __debug__:
        def __post_init__(self):
            if (self.xview is None) and (self.yview is None):
                raise ValueError(f'Invalid WidgetView: {self}')
            assert all(0.0 <= fpoint <= 1.0 for tpl in (self.xview, self.yview) for fpoint in (tpl or []))

    @classmethod
    def fromwidget(cls, widget: tk.Widget) -> 'typing.Optional[WidgetView]':
        '''Gather `WidgetView` information from a widget object.

        When the `wview <mixin.MixinWidget.wview>` function is not available on
        the widget itself, use this.

        Returns:
            Return a `model.WidgetView` object with the view information, if
            the widget supports scrolling in at least one axis. If the widget
            does not support scrolling, returns `None`.
        '''
        if isinstance(widget, tk.XView):
            xview = widget.xview()
        else:
            xview = None
        if isinstance(widget, tk.YView):
            yview = widget.yview()
        else:
            yview = None
        if xview is None and yview is None:
            return None
        else:
            return cls(xview, yview)

    @property
    def specced(self):
        '''Check if this object is fully specced.

        This indicates if scrolling on both widgets is supported.
        '''
        return self.xview is not None and self.yview is not None

    @property
    def deltax(self) -> typing.Optional[float]:
        '''Calculate the visible width fraction.

        Returns:
            Return `None` if the widget does not support scrolling on the X
            axis.
            Otherwise return a `float` represening the visible width fraction.
        '''
        if self.xview is None:
            return None
        else:
            low, high = self.xview
            return high - low

    @property
    def deltay(self) -> typing.Optional[float]:
        '''Calculate the visible height fraction.

        Returns:
            Return `None` if the widget does not support scrolling on the Y
            axis.
            Otherwise return a `float` represening the visible height fraction.
        '''
        if self.yview is None:
            return None
        else:
            low, high = self.yview
            return high - low

    def xshown(self, x: float) -> typing.Optional[bool]:
        '''Check if the given width fraction is visible.

        Args:
            x: Fraction of width.

        Returns:
            Return `None` if the widget does not support scrolling on the X
            axis. Otherwise, return a `bool` representing if ``x`` is contained
            in ``xview``.
        '''
        if self.xview is None:
            return None
        else:
            lx, hx = self.xview
            return lx <= x <= hx

    def yshown(self, y: float) -> typing.Optional[bool]:
        '''Check if the given height fraction is visible.

        Args:
            y: Fraction of height.

        Returns:
            Return `None` if the widget does not support scrolling on the Y
            axis. Otherwise, return a `bool` representing if ``y`` is contained
            in ``yview``.
        '''
        if self.yview is None:
            return None
        else:
            ly, hy = self.yview
            return ly <= y <= hy

    def shown(self, x: typing.Optional[float], y: typing.Optional[float]) -> typing.Optional[bool]:
        '''Check if the given fraction position is visible.

        Args:
            x: Fraction of width. Optional
            y: Fraction of height. Optional

        Return:
            Return `None` if the widget does not support scrolling on the X or
            Y axes. Otherwise, return a `bool` representing if both ``x`` and
            ``y`` fractions are contained in ``xview``/``yview``.

        See Also:
            See `xshown` or `yshown` for a single-axis version of this function.
        '''
        sx = None if x is None else self.xshown(x)
        sy = None if y is None else self.yshown(y)
        if sx is None or sy is None:
            return None
        else:
            assert self.specced is True
            return sx is True and sy is True

    if __debug__:
        def __str__(self) -> str:
            BOTTOM, TOP = 0.0, 1.0
            args = []
            for cname, cview in {'x': self.xview, 'y': self.yview}.items():
                if cview is None:
                    pass
                elif cview == (BOTTOM, TOP):
                    args.append(f'{cname}=ALL')
                else:
                    low: typing.Union[str, float]
                    high: typing.Union[str, float]
                    low, high = cview
                    sep = ':'
                    if low == BOTTOM:
                        low = '|'
                        sep = ''
                    if high == TOP:
                        high = '|'
                        sep = ''
                    args.append(f'{cname}={low}{sep}{high}')
            args_string = ','.join(args)
            string = f'{self.__class__.__qualname__}[{args_string}]'
            return string


@dataclass
class ImageCache:
    '''Image Cache metadata.

    Each cached image has metadata associated with it, to be able to support
    lazy-loading images.

    The ``obj`` point to the image object, the rest are metadata used to
    reconstruct it.
    '''
    # Cached
    obj: typing.Optional[tk.Image] = None
    # UnCached
    fname: typing.Optional[Path] = None
    data: typing.Optional[bytes] = None
    dtype: typing.Optional[str] = None

    def __post_init__(self):
        assert self.dtype is None or self.dtype in IMAGE_TYPES

    @property
    def cached(self) -> bool:
        '''Check if the image object is cached.'''
        return self.obj is not None


class Direction(enum.Enum):
    '''The direction of automatic widget layout.

    Here is a table of direction "cardinal points", for visual reference:

    .. tabularcolumns:: |L|C|L|

    .. csv-table:: Direction Cardinal Points
      :width: 30%

      ,`N <Direction.N>`,`H <Direction.H>`
      `W <Direction.W>`,,`E <Direction.E>`
      `V <Direction.V>`,`S <Direction.S>`,

    .. note:: This is similar to `CP`, but should not be confused with it.
    '''
    # deltaRow, deltaColumn
    N = (-1, 0)
    '''North'''
    S = (+1, 0)
    '''South'''
    E = (0, +1)
    '''East'''
    W = (0, -1)
    '''West'''
    H = (-1, +1)
    '''Reversed Horizontal, combines `North <Direction.N>` and `East <Direction.E>`'''
    V = (+1, -1)
    '''Reversed Vertical, combines `South <Direction.S>` and `West <Direction.W>`'''

    def __init__(self, dR: int, dC: int):
        # This is not really used anywhere, for now
        # It requires complex modulo-with-carry calculations
        self.dR = dR
        self.dC = dC
        assert len(self.name) == 1, 'Direction name must be a single character'

    if __debug__:
        def __repr__(self) -> str:
            return f'{self.__class__.__qualname__}.{self.name}'

    def grid(self, rows: int, cols: int, amount: typing.Optional[int] = None, auto_fill: bool = True) -> typing.Iterable[GridCoordinates]:
        '''Generate `GridCoordinates` for a widget grid.

        If the ``amount`` of widgets to distribute is not given, this assumes the
        coordinates are calculated for an uniform grid (all spaces occupied).

        This ``amount`` must fit on the grid, which mean rejecting amounts of
        widgets that leave an entire row or column unfilled. The
        ``auto_fill`` flag controls adjusting the last widget to completely
        fill the available space.

        Args:
            rows: Number of rows on the grid
            cols: Number of columns on the grid
            amount: Number of widgets to distribute. Optional, defaults to
                having all the grid positions fulfilled.
            auto_fill: Adjust the missing widgets by expanding the last one
                to fill the rest of the empty space. Defaults to enable.
        '''
        size = rows * cols
        amount = amount or size
        if amount > size:
            raise ValueError(f'Too many widgets in too few locations: {amount} > {size}')
        if amount == 0:
            raise ValueError(f'Too few widgets in too much locations: {amount}')
        extra_size = size - amount
        if self.dR != 0 and extra_size >= rows:
            raise ValueError('Too few widgets for this grid: empty columns')
        if self.dC != 0 and extra_size >= cols:
            raise ValueError('Too few widgets for this grid: empty rows')
        if __debug__:
            logger_layout.debug('Grid[%s]: %d (%dx%d=%d) [D%d]', self.name, amount, rows, cols, size, extra_size)
        for idx in range(amount):
            if self in (Direction.E, Direction.W, Direction.H):  # Horizontal
                c = (idx // cols, idx % cols)
            elif self in (Direction.N, Direction.S, Direction.V):  # Vertical
                c = (idx % rows, idx // rows)
            else:
                # Not generic for any delta...
                raise NotImplementedError
            crspan, ccspan = 1, 1
            crow = rows - 1 - c[0] if self.dR < 0 else c[0]
            ccol = cols - 1 - c[1] if self.dC < 0 else c[1]
            if auto_fill and extra_size > 0 and idx == amount - 1:
                if self == Direction.N:
                    crow = crow - extra_size
                    crspan = 1 + extra_size
                elif self in (Direction.S, Direction.V):
                    crspan = 1 + extra_size
                elif self in (Direction.E, Direction.H):
                    ccspan = 1 + extra_size
                elif self == Direction.W:
                    ccol = ccol - extra_size
                    ccspan = 1 + extra_size
                assert 0 <= crow <= rows and 0 <= crow + crspan - 1 <= rows
                assert 0 <= ccol <= cols and 0 <= ccol + ccspan - 1 <= cols
            if __debug__:
                logger_layout.debug('»» %d | %d+%dx%d+%d || %dx%d', idx, crow, crspan, ccol, ccspan, *c)
            yield GridCoordinates(crow, ccol,
                                  rowspan=crspan, columnspan=ccspan)

    def multiples(self, *amounts: typing.Optional[int], amount: typing.Optional[int] = None) -> typing.Iterable[GridCoordinates]:
        '''Generate `GridCoordinates` for sequence of integer amounts.

        ``amounts`` is a series of integers or `None` (refered to as "slots"),
        to be distributed per row/column, depending on the direction.

        There can be any number of "slots", marking a row/column as receiving
        the remaining widgets. The remaining widgets are distributed evenly
        through the existing "slots".

        If the ``amount`` of widgets to distribute is not given, there is no
        support for using `None` as amount. Another possible error is giving an
        amount of slots that do not evenly divide the remaining widgets.

        Args:
            amounts: Amount of widgets per row/column.
            amount: Number of widgets to distribute. Optional.
        '''
        if __debug__:
            logger_layout.debug('Multiple: (%s)[%s]', ' '.join(str(a or 'x') for a in amounts), amount)
        size: int
        if amount is None:
            if None in amounts:
                raise ValueError('"x" requires all `amounts` to be defined')
            # `amounts` has no `None` elements now
            size = sum(typing.cast(typing.Sequence[int], amounts))
            amount = size
        else:
            amount_x = amounts.count(None)
            if amount_x > 0:
                existing_amount = typing.cast(int, sum((a or 0 for a in amounts)))
                remaining_amount = amount - existing_amount
                delta = math.ceil(remaining_amount / amount_x)
                if delta * amount_x != remaining_amount:
                    raise ValueError(f'Unable to distribute {remaining_amount} by {amount_x} slots')
                if __debug__:
                    logger_layout.debug('- Slots : %ds * %d/s = %d', amount_x, delta, remaining_amount)
                amounts = tuple(delta if a is None else a for a in amounts)
            # `amounts` has no `None` elements now
            size = sum(typing.cast(typing.Sequence[int], amounts))
        asize, osize = len(amounts), util.lcm_multiple(*amounts)
        if __debug__:
            logger_layout.debug('- Sizes : A%d O%d = %d', asize, osize, asize * osize)
        # assert isinstance(amount, int)
        if amount > size:
            raise ValueError(f'Too many widgets for these amounts: {amount} > {size}')
        elif amount < size:
            raise ValueError(f'Too few widgets for these amounts: {amount} < {size}')
        elif osize == 0:
            raise ValueError(f'Too few widgets in too much locations: {amount}')
        for idx, this_amount in enumerate(amounts):
            this_width = osize // this_amount
            for other in range(0, osize, this_width):
                if __debug__:
                    logger_layout.debug('» T%d O%d TW%d | TA%d OS%d', idx, other, this_width, this_amount, osize)
                if self in (Direction.E, Direction.W, Direction.H):  # Horizontal
                    # Grid: asize x osize
                    crow, ccol, crspan, ccspan = idx, other, 1, this_width
                    if __debug__:
                        logger_layout.debug('»»» %d+%dx%d+%d', crow, crspan, ccol, ccspan)
                    if self.dR < 0:
                        crow = asize - crow - crspan
                    if self.dC < 0:
                        ccol = osize - ccol - ccspan
                    assert 0 <= crow <= asize and 0 <= crow + crspan - 1 <= asize, f'R ({crow}+{crspan}/{asize})'
                    assert 0 <= ccol <= osize and 0 <= ccol + ccspan - 1 <= osize, f'C ({ccol}+{ccspan}/{osize})'
                elif self in (Direction.N, Direction.S, Direction.V):  # Vertical
                    # Grid: osize x asize
                    crow, ccol, crspan, ccspan = other, idx, this_width, 1
                    if self.dC < 0:
                        ccol = asize - ccol - ccspan
                    if self.dR < 0:
                        crow = osize - crow - crspan
                    assert 0 <= crow <= osize and 0 <= crow + crspan - 1 <= osize, f'R ({crow}+{crspan}/{osize})'
                    assert 0 <= ccol <= asize and 0 <= ccol + ccspan - 1 <= asize, f'C ({ccol}+{ccspan}/{asize})'
                if __debug__:
                    logger_layout.debug('»» %d %d | %d+%dx%d+%d', idx, other, crow, crspan, ccol, ccspan)
                yield GridCoordinates(crow, ccol,
                                      rowspan=crspan, columnspan=ccspan)


@dataclass
class WidgetDynamicState:
    '''Hold the dynamic state for a widget.

    See `mixin.MixinState`.

    Args:
        getter: Function to retrieve the state
        setter: Function to change the state
        noneable: Is this widget noneable? See `tkmilan.mixin.MixinState.isNoneable`.
        container: Is this widget a container? Defaults to `False`.
    '''
    getter: typing.Callable
    setter: typing.Callable
    noneable: bool
    container: bool = False

    def __str__(self):
        strs = []
        if self.container:
            strs.append('C')
        if self.noneable:
            strs.append('N')
        strings = ','.join(strs)
        # TODO: Use `self.__class__.__qualname__`
        return f'WDS[{strings}]'


@dataclass
class VState(typing.Generic[vsT]):
    '''Hold validated state.

    This is needed to make sure the received object is really a validated
    state, or just any regular state.

    Args:
        label: The label present on the widget.
        value: The validated value.
            Can be `None` when invalid, see `valid`.
    '''
    label: str
    value: typing.Optional[vsT] = None

    @property
    def valid(self) -> bool:
        '''Is the validated value valid?'''
        return self.value is not None

    dict = dc_asdict
    '''Get this information as a dictionary.'''

    # Detect weird comparisons involving `VState`
    if __debug__:
        def __eq__(self, other):
            ''''''  # Internal, do not document
            if self.__class__ is other.__class__:
                return (self.label, self.value) == (other.label, other.value)
            else:
                warnings.warn(f'Probably not a valid comparison: {self!r} == {other!r}', stacklevel=2)
                return False


@dataclass
class VWhy:
    '''Validation runtime information.

    There is no Python documentation, see ``Tk`` :tk:`trace validation
    <ttk_entry.htm#M34>` documentation.

    Args:
        vstate: The widget validated state.
        why: Validation script substitution: validation condition (``%V``).

            See `ValidateWhyT`.
        t: Validation script substitution: action type (``%d``).

            See `ValidateST`.
        widget: The widget being validated.
        tt: The widget tooltip. Optional.

            When this is `None`, it means the automatic tooltip handling will
            run, and *vice versa*.
    '''
    vstate: VState
    why: ValidateWhyT  # %V
    t: ValidateST      # %d
    widget: 'mixin.MixinWidget'
    tt: 'typing.Optional[Tooltip]'

    def validation(self) -> typing.Optional[bool]:
        '''Run the natural validation for this reason.

        See `mixin.MixinValidationSingle.setup_validation`.
        '''
        if __debug__:
            from . import mixin
        assert isinstance(self.widget, mixin.MixinValidationSingle)
        return self.widget.setup_validation(self.vstate, self)


@dataclass
class VSettings:
    '''Hold validation settings.

    There are two types of validation, based on timing:

    - **Pre-Validation**: Validate the future state before the widget state
      changes.
      Allows for choosing whether to accept or reject the edit.
      Does not affect the `GuiState`.

      This is not very common, since the UX is not very good.
    - **Post-Validation**: Validate the current widget state, and change the
      `GuiState`. This is the most common validation.

    There are also native validations (supported by ``Tk``), and synthetic
    validations, implemented inside this library.

    Parameters:
        postFocusIn: Post-Validate on widget getting focus.
            Native validation.
        postFocusOut: Post-Validate on widget losing focus.
            Native validation.
        preKey: Pre-Validate on widget getting a key event.
            Native validation.
        postVar: Post-Validate on widget variable changing.
            Synthetic validation, uses ``self`` as `ValidateWhyT`.
        postInitial: Post-Validate on widget creation.
            Synthetic validation, uses ``initial`` as `ValidateWhyT`.

        fn: The parsing function, to validate the state.
            Optional, each widget has a "natural" parsing function.
        fnSimple: Do not calculate the full validation data, send only the
            widget state. This is usually the only thing that matters.
            Defaults to enabled, for performance reasons.
        tt: The corresponding `Tooltip` for this widget, if available.
            This is paired with the `putTooltip
            <mixin.MixinValidationSingle.putTooltip>` function.
            Optional, not to be used directly.
        ttSimple: When `True`, setup a very simple tooltip behaviour: disable
            when valid, enable otherwise. Set this to `False` for more complex
            behaviours.
            Defaults to `None`, meaning dependent on other options. When ``fn``
            is `None` or ``fnSimple`` is `False`, default to `True`, with this
            the user has no way to control this. Otherwise, default to `False`.

        tkWhen: Calculated ``Tk`` setting, based on the other parameters. See
            :tk:`validation modes <ttk_entry.htm#M35>` documentation.
    '''
    # Native Validations
    postFocusIn: InitVar[bool] = False
    postFocusOut: InitVar[bool] = False
    preKey: InitVar[bool] = False
    # Synthetic Validations
    postVar: bool = True
    postInitial: bool = True
    # Function
    fn: typing.Optional[typing.Callable[[VState, typing.Optional[VWhy]], typing.Optional[bool]]] = None
    fnSimple: bool = True
    # Tooltip (Optional)
    tt: 'typing.Optional[Tooltip]' = dc_field(init=False, default=None)
    ttSimple: typing.Optional[bool] = None  # Never `None`
    # tkinter values
    tkWhen: ValidateWhenT = dc_field(init=False)

    def __post_init__(self, postFocusIn: bool, postFocusOut: bool, preKey: bool):
        # tkWhen
        tkWhen: typing.Optional[str] = {
            (True, True, True): 'all',
            (True, False, False): 'focusin',
            (False, True, False): 'focusout',
            (True, True, False): 'focus',
            (False, False, True): 'key',
            (False, False, False): 'none',
        }.get((postFocusIn, postFocusOut, preKey), None)
        assert tkWhen is not None, f'Invalid combination: Fi={postFocusIn} Fo={postFocusOut} K={preKey}'
        assert tkWhen in ('focus', 'focusin', 'focusout', 'key', 'all', 'none')
        tkWhen = typing.cast(ValidateWhenT, tkWhen)  # All good
        self.tkWhen = tkWhen
        # tt
        # - Never check `self.tt` here, it's usually defined later
        if self.ttSimple is None:
            self.ttSimple = self.fn is None or self.fnSimple is True
            # if __debug__:
            #     logger.debug('%s: Default ttSimple=%s', self, self.ttSimple)
        else:
            if self.fnSimple is True:
                assert self.ttSimple is True, f'Invalid combination (unreachable tooltip): fnSimple={self.fnSimple} ttSimple={self.ttSimple}'
        assert isinstance(self.ttSimple, bool), f'Bad ttSimple: {self.ttSimple!r}'


@dataclass
class WState(typing.Generic[wsT, wsST]):
    '''Hold wrapped state.

    This is needed to mark state as being a product of a wrapped container.
    '''

    state: typing.Optional[wsT]  # TODO: Force `bool`
    '''The widget state.

    This is the extra value being stored on the widget.
    Optional, if the variable already exists upstream.
    '''
    substate: wsST
    '''The wrapped state.

    This is the original value being stored on the widget.
    '''

    dict = dc_asdict
    '''Get this information as a dictionary.'''


@dataclass
class WStateR(WState):
    '''Reversed version of the `WState` state.

    This is exactly the same as the other object, but marks the widget state as
    "reversed" compared to the regular version.
    What that means is widget-specific, usually only required for validation.
    '''
    pass


@dataclass
class WindowState:
    '''GUI State for entire windows.

    This object tracks changes to attributes that apply entire windows, not
    individual widgets.

    Args:
        fullscreen: Show the window contents on the entire screen.

    See Also:
        This is used in `RootWindow`, as ``rgstate``.
    '''

    fullscreen: typing.Optional[bool]

    def items(self):
        '''Workaround for `dataclasses.asdict` issue.

        This is a problem-free version of:

        .. code:: python

            return dataclasses.asdict(self).items()
        '''
        for f in fields(self):
            yield (f.name, getattr(self, f.name))


@dataclass
class GuiState:
    '''Widget GUI state.

    This supports all possible states, not all widgets support all states.

    See `GUI_STATES`, `mixin.MixinWidget.gstate`.
    '''
    enabled: typing.Optional[bool] = None
    valid: typing.Optional[bool] = None
    readonly: typing.Optional[bool] = None
    alternate: typing.Optional[bool] = None

    def items(self):
        '''Workaround for `dataclasses.asdict` issue.

        This is a problem-free version of:

        .. code:: python

            return dataclasses.asdict(self).items()
        '''
        for f in fields(self):
            yield (f.name, getattr(self, f.name))

    def states_tk(self, *, widget: 'typing.Optional[mixin.MixinWidget]' = None) -> typing.Sequence[str]:
        '''Calculate the ``Tk`` string to use with state functions.

        See the `state <tkinter.ttk.Widget.state>` function.

        Args:
            widget: Widget to validate if the generated state is consistent
                with supported keys. Optional.
        '''
        # if __debug__:
        #     logger.debug('State < %r', self)
        states = []
        for estr, sval in self.items():
            if sval is not None:
                if __debug__:
                    if widget is not None:
                        assert estr in widget.gkeys, f'{widget.__class__.__qualname__}| Invalid GuiState: {estr}'
                itk = GUI_STATES[estr]
                states.append(itk.sstr(sval))
                # if __debug__:
                #     logger.debug('  %s « S[%-5s %5s]I %s', states[-1], sval, itk.invert, estr)
        return states

    def isCustom(self) -> bool:
        '''Check if this is a custom object.

        Basically, returns `True` when this is a subclass on `GuiState`.
        Useful to detect states with slighly different semantics.
        '''
        return type(self) is not GuiState

    # TODO: On Python 3.11:: -> typing.Self
    @classmethod
    def new(cls, state: 'GuiState') -> 'GuiState':
        '''Create a new object with the same state.

        For performance reasons, since they are readonly on the common case,
        the `GuiState` objects are passed through the hierarchy by reference.

        If you need to make changes to a received object, create a new object
        using this function.
        '''
        return cls(**dict(state.items()))

    if __debug__:
        # Include a nicer representation
        # - Skip `None` values
        # - If printed with fixed width fonts, they align vertically
        def __repr__(self) -> str:
            str_elements = ', '.join(
                f'{estr}={str(sval)[0]}'
                for estr, sval in self.items()
                if sval is not None
            )
            return f'{self.__class__.__qualname__}({str_elements})'


@dataclass
class GuiState_Tk:
    '''Information about ``Tk`` states.

    The states applied to the widgets are very confusing, so store all the
    necessary metadata here.

    See `GuiState`, `GUI_STATES`, `GUI_STATES_common`.

    Example:
        The examples will analyse `GUI_STATES`.

        The simplest example is the ``"readonly"`` element. The ``Tk`` string
        is ``readonly``, so ``invert`` is `False`, the semantic values match.

        On the other hand, for the ``"enabled"`` element, the ``Tk`` string is
        ``disabled``, so ``invert`` is `True`. The semantic values are
        inverted.
    '''

    string: str
    '''The ``Tk`` string used in the state-releated functions.'''
    invert: bool
    '''Is the ``string`` state the opposite from its sematic value?'''

    def gstr(self) -> str:
        '''Calculate the ``Tk`` string to obtain the value.

        This already takes into account the ``invert`` parameter.

        See the `instate <tkinter.ttk.Widget.instate>` function.
        '''
        if self.invert:
            return f'!{self.string}'
        else:
            return self.string

    def sstr(self, value: bool) -> str:
        '''Calculate the ``Tk`` string to define the ``value``.

        This already takes into account the ``invert`` parameter.

        See the `state <tkinter.ttk.Widget.state>` function.
        '''
        if self.invert is not value:
            return self.string
        else:
            return '!%s' % self.string


GUI_STATES: typing.Mapping[str, GuiState_Tk] = {
    'enabled': GuiState_Tk(tk.DISABLED, invert=True),
    'valid': GuiState_Tk('invalid', invert=True),
    'readonly': GuiState_Tk('readonly', invert=False),
    'alternate': GuiState_Tk('alternate', invert=False),
}
'''`GuiState` ``Tk`` metadata.

See `GuiState_Tk`.'''

GUI_STATES_common = ('enabled', 'valid')
'''`GuiState` common to all widgets.

See `GUI_STATES`.'''
assert set(GUI_STATES.keys()) == set(f.name for f in fields(GuiState))
assert set(GUI_STATES_common) < set(f.name for f in fields(GuiState))
assert not (set(GUI_STATES.keys()) < set(('_internal', '_sub')))


class MixinBinding:
    ''''''  # Internal, do not document
    _binding: typing.Callable

    def __init__(self, widget: 'mixin.MixinWidget', sequence: str, action: typing.Callable, *, immediate: bool = False, description: typing.Optional[str] = None):
        assert isinstance(widget, (tk.Widget, tk.Tk, tk.Toplevel)), f'{widget} is not a valid widget'
        self.obj = None
        self.widget = widget
        self.sequence = sequence
        self.action = action
        self.description: str = description or f'Calling "{action.__name__}"'
        if immediate:
            self.enable()

    def __bool__(self):
        '''Check if the binding is enabled.

        Should be used as:

        .. code:: python

            if binding:
                print('Binding is enabled')
            else:
                print('Binding is disabled')
        '''
        return self.obj is not None

    def _bind(self) -> typing.Any:
        raise NotImplementedError

    def _unbind(self, obj: typing.Any) -> None:
        raise NotImplementedError

    def enable(self, *, warn: bool = True) -> None:
        '''Enable the binding.

        Args:
            warn: Warn about redundant operations.
                Enabled by default.

        See Also:
            Use `tryenable` to force ``warn`` to `False`.
        '''
        if self.obj is None:
            self.obj = self._bind()
        else:
            if warn:
                warnings.warn(f'Redundant enable @ {self!r}', stacklevel=2)

    def tryenable(self) -> bool:
        '''Try to enable the binding, don't warn when already enabled.

        Wraps `enable`, with ``warn`` forced to `False`.

        Returns:
            A `bool` indicating if the state has changed.
        '''
        ostate = bool(self)
        self.enable(warn=False)
        return ostate != bool(self)

    def disable(self, *, warn: bool = True) -> None:
        '''Disable the binding.

        Args:
            warn: Warn about redundant operations.
                Enabled by default.

        See Also:
            Use `trydisable` to force ``warn`` to `False`.
        '''
        if self.obj is not None:
            obj = self.obj
            try:
                self.obj = None
                self._unbind(obj)
            except Exception as e:
                self.obj = obj  # Restore
                raise Exception(f'Error when unbinding @ {self.widget!r}') from e
        else:
            if warn:
                warnings.warn(f'Redundant disable @ {self!r}', stacklevel=2)

    def trydisable(self) -> bool:
        '''Try to disable the binding, don't warn when already disabled.

        Wraps `disable`, with ``warn`` forced to `False`.

        Returns:
            A `bool` indicating if the state has changed.
        '''
        ostate = bool(self)
        self.disable(warn=False)
        return ostate != bool(self)


class Binding(MixinBinding):
    '''Wrap a stateful binding.

    Can be enabled and disabled separately from creation. Default to starting
    disabled. Note that this is the opposite from the actions of the wrapped
    functions.

    See Python documentation for `bindings and events
    <https://docs.python.org/3.8/library/tkinter.html#bindings-and-events>`_.

    ..
        Python 3.8 is missing this reference, included in Python 3.9:

        :ref:`bindings and events <python:Bindings-and-Events>`

    Args:
        widget: The widget to apply the binding to.
        sequence: The sequence to bind to. See ``Tk`` :tk:`bind <bind.htm>`
            documentation, not everything applies here.
        action: The function to call when the binding is hit.
        immediate: Enable binding on creation.
            Defaults to ``False``, requiring separate activation.
        description: Optional description of the binding action.
            Useful for debugging, not used for any purpose for now.

    Note:
        When the ``action`` function returns ``"break"``, no more actions are
        considered. Use this with care.

    See Also:
        For the global version of this, see `BindingGlobal`.

    .. automethod:: __bool__
    .. automethod:: enable
    .. automethod:: tryenable
    .. automethod:: disable
    .. automethod:: trydisable
    '''
    def __init__(self, widget: 'mixin.MixinWidget', sequence: str, *args, **kwargs):
        if sequence in widget.wroot._bindings_global:
            # Warn when widget bindings are aliased by global bindings
            warnings.warn(f'Global binding for "{sequence}" aliases {widget!r} binding')
            # Should this be an error?
        super().__init__(widget, sequence, *args, **kwargs)

    def _bind(self):
        return self.widget.bind(sequence=self.sequence, func=self.action, add=True)

    def _unbind(self, obj):
        self.widget.unbind(self.sequence, obj)

    def __repr__(self) -> str:
        return f'Binding("{self.sequence}" @ {self.widget})  # {self.description}'


class BindingGlobal(MixinBinding):
    '''Wrap a stateful global binding.

    This is a global version of the `Binding` object. The main difference is
    that the ``widget`` argument is ignored, the binding applies to the entire
    application (technically, the widget's `mixin.MixinWidget.wroot` (a
    `RootWindow`).

    The `RootWindow` will store a dictionary of sequences to `BindingGlobal`.
    This is similar to `mixin.MixinWidget.binding`.

    Args:
        widget: The widget to apply the binding to. This can be any widget,
            only the corresponding `RootWindow` is considered.
        sequence: The sequence to bind to. See ``Tk`` :tk:`bind <bind.htm>`
            documentation, not everything applies here.
        action: The function to call when the binding is hit.
        immediate: Enable binding on creation.
            Defaults to ``False``, requiring separate activation.
        description: Optional description of the binding action.
            Useful for debugging, not used for any purpose for now.

    Note:
        When the ``action`` function returns ``"break"``, no more actions are
        considered. Use this with care.

    See Also:
        For the widget version of this, see `Binding`.

    .. automethod:: __bool__
    .. automethod:: enable
    .. automethod:: tryenable
    .. automethod:: disable
    .. automethod:: trydisable
    '''
    def __init__(self, widget: 'mixin.MixinWidget', sequence: str, *args, **kwargs):
        root_widget = widget.wroot
        if sequence in root_widget._bindings_global:
            raise ValueError(f'Repeated global binding for "{sequence}"')
        super().__init__(root_widget, sequence, *args, **kwargs)
        # Store all global bindings
        root_widget._bindings_global[sequence] = self

    def _bind(self):
        return self.widget.bind_all(sequence=self.sequence, func=self.action, add=True)

    def _unbind(self, obj):
        self.widget.unbind(self.sequence, obj)

    def __repr__(self) -> str:
        return f'BindingGlobal("{self.sequence}")  # {self.description}'


class BindingTag(MixinBinding):
    '''Wrap a stateful tag binding for `EntryMultiline`.

    This is a version of the `Binding` object which applies only to the tags in
    `EntryMultiline`.

    Args:
        widget: The widget to apply the binding to. This can be any widget,
            only the corresponding `RootWindow` is considered.
        tag: The sub-widget tag where the binding applies.
        sequence: The sequence to bind to. See ``Tk`` :tk:`bind <bind.htm>`
            documentation, not everything applies here.
        action: The function to call when the binding is hit.
        immediate: Enable binding on creation.
            Defaults to ``False``, requiring separate activation.
        description: Optional description of the binding action.
            Useful for debugging, not used for any purpose for now.

    Note:
        When the ``action`` function returns ``"break"``, no more actions are
        considered. Use this with care.

    .. automethod:: __bool__
    .. automethod:: enable
    .. automethod:: tryenable
    .. automethod:: disable
    .. automethod:: trydisable
    '''
    def __init__(self, widget: 'EntryMultiline', tag: str, sequence: str, *args, **kwargs):
        self.tag = tag
        if sequence in widget.wroot._bindings_global:
            # Warn when widget bindings are aliased by global bindings
            warnings.warn(f'Global binding for "{sequence}" aliases {widget!r}(tag "{tag}") binding')
            # Should this be an error?
        super().__init__(widget, sequence, *args, **kwargs)

    def _bind(self):
        return self.widget.tag_bind(tagName=self.tag, sequence=self.sequence, func=self.action, add=True)

    def _unbind(self, obj):
        self.widget.tag_unbind(self.tag, self.sequence, obj)

    def __repr__(self) -> str:
        return f'BindingTag("{self.sequence}" @ {self.widget}|{self.tag})  # {self.description}'


class Timeout:
    '''Schedule an action into the future time, cancellable.

    The ``timeout`` argument (also in `schedule`) acts as a deadline, after
    which the ``action`` is invoked.

    Can be scheduled and unscheduled separately from creation, see the
    ``immediate`` argument.

    See ``Tcl`` :tcl:`after <after.htm>` documentation.

    Args:
        widget: The widget to apply the timeout to. When in doubt, use the
            `wroot <mixin.MixinWidget.wroot>` widget.
        action: The function to call when the timeout expires.
        timeout: The expiration time for the timeout, in milliseconds.
            This only starts to count from the scheduling time, not the object
            creation, but see ``immediate``.
        immediate: Schedule timeout on creation.
            Defaults to `True`, set to `False` to schedule separately.

    See Also:
        For the idling version of this, see `TimeoutIdle`.
    '''
    _obj: typing.Union[None, str, typing.Literal[False]]
    # _obj States:
    # - None: Unscheduled. The default
    # - str: Scheduled, this is the id for `after_cancel`
    # - False: Unscheduled, since it was already triggered.
    # Note the truthy value is enough to know if this is scheduled
    # Get information with `self.widget.tk.call('after', 'info', self._obj)`

    def __init__(self, widget: 'mixin.MixinWidget', action: typing.Callable, timeout: int, immediate: bool = True):
        self._obj = None
        self.widget = widget
        self.action = action
        self.timeout = timeout
        if immediate:
            self.schedule()

    def isScheduled(self) -> bool:
        '''Check if the timeout is scheduled to run in the future.

        This is `True` after calling `schedule`, and before the action runs.
        '''
        return bool(self._obj)

    def isTriggered(self) -> bool:
        '''Check if the timeout has been triggered yet.

        This is `True` just before the action runs. Note that `isScheduled`
        will return `False` in this case.
        '''
        return self._obj is False

    def _action(self, *args, **kwargs) -> None:
        '''Run the saved action, and setup the `isTriggered` flag.'''
        assert self.isScheduled(), f'{self}: Invalid action @ {self._obj!r}'
        # Memory leak, save the old `_obj`? `after_cancel` it?
        self._obj = False  # Mark as triggered
        self.action(*args, **kwargs)

    def schedule(self,
                 _arg1: typing.Any = None,
                 _arg2: typing.Any = None,
                 _arg3: typing.Any = None,
                 *,
                 timeout: typing.Optional[int] = None,
                 ) -> None:
        '''Schedule the timeout to run in the future.

        This tries to unschedule the timeout, and schedules it again, to avoid
        possible race conditions.
        The countdown for the expiration in ``timeout`` milliseconds starts when this function is called.

        Note the override values only take effect in this particular call, they
        are not permanent changes.

        Args:
            timeout: Override the timeout to consider on the next call.

            _arg1: Unused, included for API compatibility with ``Tk`` events
            _arg2: Unused, included for API compatibility with ``Tk`` traces
            _arg3: Unused, included for API compatibility with ``Tk`` event loop.
        '''
        assert isinstance(self.widget, (tk.Widget, tk.Tk, tk.Toplevel)), f'{self} is not a valid widget'
        self.unschedule()  # Try to unschedule first
        self._obj = self.widget.after(
            ms=timeout or self.timeout,
            func=self._action
        )
        assert bool(self._obj), f'Invalid ID: {self._obj!r}'

    def unschedule(self,
                   _arg1: typing.Any = None,
                   _arg2: typing.Any = None,
                   _arg3: typing.Any = None,
                   ) -> None:
        '''Cancel the timeout.

        Args:
            _arg1: Unused, included for API compatibility with ``Tk`` events
            _arg2: Unused, included for API compatibility with ``Tk`` traces
            _arg3: Unused, included for API compatibility with ``Tk`` event loop.
        '''
        assert isinstance(self.widget, (tk.Widget, tk.Tk, tk.Toplevel)), f'{self} is not a valid widget'
        obj = self._obj
        if obj:
            # Can this fail?
            # Possible race with `_action`
            self.widget.after_cancel(obj)
            self._obj = None

    # Alias scheduling function
    reschedule = schedule
    '''Reschedule the timeout (alias for `schedule`).'''

    def toggle(self,
               _arg1: typing.Any = None,
               _arg2: typing.Any = None,
               _arg3: typing.Any = None,
               ) -> bool:
        '''Toggle the schedule state.

        Args:
            _arg1: Unused, included for API compatibility with ``Tk`` events
            _arg2: Unused, included for API compatibility with ``Tk`` traces
            _arg3: Unused, included for API compatibility with ``Tk`` event loop.

        Returns:
            Return the new state, equivalent to calling `isScheduled` right afterwards.
        '''
        if self.isScheduled():
            self.unschedule()
            return False
        else:
            self.schedule()
            return True


class TimeoutIdle:
    '''Schedule an action into the future, whenever there's nothing else to do.

    This adds an idle task to the ``tk`` event loop, to be invoked when there's
    no other action to take. This is very useful to push actions to the future,
    but not block the UI thread.

    Can be scheduled and unscheduled separately from creation, see the
    ``immediate`` argument.

    See ``tcl`` :tcl:`after idle <after.htm#M9>` documentation.

    Args:
        widget: The widget to apply the timeout to. When in doubt, use the
            `wroot <mixin.MixinWidget.wroot>` widget.
        action: The function to call when the application goes idle.
        immediate: Schedule timeout on creation.
            Defaults to `True`, set to `False` to schedule separately.

    See Also:
        For a version of this that specifies a deadline, see `Timeout`.
    '''
    _obj: typing.Union[None, str, typing.Literal[False]]
    # _obj States:
    # - None: Unscheduled. The default
    # - str: Scheduled, this is the id for `after_cancel`
    # - False: Unscheduled, since it was already triggered.
    # Note the truthy value is enough to know if this is scheduled
    # Get information with `self.widget.tk.call('after', 'info', self._obj)`

    def __init__(self, widget: 'mixin.MixinWidget', action: typing.Callable, immediate: bool = True):
        self._obj = None
        self.widget = widget
        self.action = action
        if immediate:
            self.schedule()

    def isScheduled(self) -> bool:
        '''Check if the timeout is scheduled to run in the future.

        This is `True` after calling `schedule`, and before the action runs.
        '''
        return bool(self._obj)

    def isTriggered(self) -> bool:
        '''Check if the timeout has been triggered yet.

        This is `True` after the action runs. Note that `isScheduled` will
        return `False` in this case.

        Note:
            During the action function call, this is `False`, and it will
            never be `True` if it calls `reschedule` inside the action.
        '''
        return self._obj is False

    def _action(self, *args, **kwargs) -> None:
        '''Run the saved action, and setup the `isTriggered` flag.'''
        assert self.isScheduled(), f'{self}: Invalid action @ {self._obj!r}'
        self._obj = False  # Mark as triggered
        # TODO: Use `try`/`catch`? Not used on the `after_idle` function
        self.action(*args, **kwargs)

    def schedule(self,
                 _arg1: typing.Any = None,
                 _arg2: typing.Any = None,
                 _arg3: typing.Any = None,
                 ) -> None:
        '''Schedule the timeout to run in the future.

        This tries to unschedule the timeout, and schedules it again, to avoid
        possible race conditions.
        The action is added to the event loop when this function is called.

        When called for an already scheduled object, this is equivalent to
        moving the action back to the end of the queue.

        Args:
            _arg1: Unused, included for API compatibility with ``Tk`` events
            _arg2: Unused, included for API compatibility with ``Tk`` traces
            _arg3: Unused, included for API compatibility with ``Tk`` event loop.
        '''
        assert isinstance(self.widget, (tk.Widget, tk.Tk, tk.Toplevel)), f'{self} is not a valid widget'
        self.unschedule()  # Try to unschedule first
        # TODO: Track the scheduled time and provide an absolute timeout?
        #       This is only to avoid infinite loops
        self._obj = self.widget.after_idle(
            func=self._action
        )
        assert bool(self._obj), f'Invalid ID: {self._obj!r}'

    def unschedule(self,
                   _arg1: typing.Any = None,
                   _arg2: typing.Any = None,
                   _arg3: typing.Any = None,
                   ) -> None:
        '''Cancel the timeout.

        This removes the action from the event loop.

        Args:
            _arg1: Unused, included for API compatibility with ``Tk`` events
            _arg2: Unused, included for API compatibility with ``Tk`` traces
            _arg3: Unused, included for API compatibility with ``Tk`` event loop.
        '''
        assert isinstance(self.widget, (tk.Widget, tk.Tk, tk.Toplevel)), f'{self} is not a valid widget'
        obj = self._obj
        if obj:
            # Can this fail?
            # Possible race with `_action`
            self.widget.after_cancel(obj)
            self._obj = None

    # Alias scheduling function
    reschedule = schedule
    '''Reschedule the timeout (alias for `schedule`).'''

    def toggle(self,
               _arg1: typing.Any = None,
               _arg2: typing.Any = None,
               _arg3: typing.Any = None,
               ) -> bool:
        '''Toggle the schedule state.

        Args:
            _arg1: Unused, included for API compatibility with ``Tk`` events
            _arg2: Unused, included for API compatibility with ``Tk`` traces
            _arg3: Unused, included for API compatibility with ``Tk`` event loop.

        Returns:
            Return the new state, equivalent to calling `isScheduled` right afterwards.
        '''
        if self.isScheduled():
            self.unschedule()
            return False
        else:
            self.schedule()
            return True


class Interval:
    '''Repeat an action with an interval between calls.

    Can be scheduled and unscheduled separately from creation, see the
    ``immediate`` argument.

    Uses a `Timeout` internally.

    Args:
        widget: The widget to apply the interval to. When in doubt, use the
            `wroot <mixin.MixinWidget.wroot>` widget.
        action: The function to call when the interval elapses.
        interval: The interval time, in milliseconds.
            This only starts to count from the scheduling time, not the object
            creation, but see ``immediate``.
        immediate: Schedule interval on creation.
            Defaults to `False`, set to `True` to schedule automatically.

    See Also:
        To run the action only once, see `Timeout`.
    '''

    scheduled: bool
    '''Scheduled State.

    Checks if the interval is scheduled to repeat.

    The state is one of the following:

    - `True`: Scheduled, the action will be repeated forever.
    - `False`: Unscheduled, but the action might be repeated once again at
      most.
    '''

    def __init__(self,
                 widget: 'mixin.MixinWidget',
                 action: typing.Callable,
                 interval: int,
                 immediate: bool = False,
                 ):
        self.scheduled = False
        self.action = action
        self.timeout = Timeout(widget, self._intervalElapsed, timeout=interval,
                               immediate=False)
        if immediate:
            self.schedule()

    def _intervalElapsed(self) -> None:  # Internal
        '''Function to attach to the `Timeout` action.

        The countdown for expiration of ``interval`` milliseconds starts when
        this function is called.
        '''
        # Run the action
        self.action()  # TODO: Suport `async`: Use `self.after(0, self.action)`, needs a lock
        # `self.reschedule`
        if self.scheduled:
            self.timeout.reschedule()

    def schedule(self,
                 _arg1: typing.Any = None,
                 _arg2: typing.Any = None,
                 _arg3: typing.Any = None,
                 ) -> None:
        '''Schedule the interval to start ticking.

        The countdown for expiration of ``interval`` milliseconds starts when
        this function is called.

        Make sure the interval is not scheduled already. When in doubt, use
        `reschedule` instead.

        Args:
            _arg1: Unused, included for API compatibility with ``Tk`` events
            _arg2: Unused, included for API compatibility with ``Tk`` traces
            _arg3: Unused, included for API compatibility with ``Tk`` event loop.
        '''
        assert not self.scheduled, f'{self!r}: Already scheduled'
        self.scheduled = True
        self.timeout.reschedule()

    def unschedule(self,
                   _arg1: typing.Any = None,
                   _arg2: typing.Any = None,
                   _arg3: typing.Any = None,
                   *,
                   force: bool = False,
                   ) -> None:
        '''Cancel the interval.

        This cancels the interval repetion, but after calling this function,
        the action might still run, at most once. See ``force`` to control
        this behaviour.

        Args:
            force: Unschedule on-flight interval, if exists.
                Disabled by default.

            _arg1: Unused, included for API compatibility with ``Tk`` events
            _arg2: Unused, included for API compatibility with ``Tk`` traces
            _arg3: Unused, included for API compatibility with ``Tk`` event loop.
        '''
        if __debug__:
            if not self.scheduled:
                logger.debug('%r: Already unscheduled', self)
        self.scheduled = False
        if force:
            self.timeout.unschedule()

    def tryunschedule(self,
                      _arg1: typing.Any = None,
                      _arg2: typing.Any = None,
                      _arg3: typing.Any = None,
                      *,
                      force: bool = False,
                      ) -> None:
        '''Try cancelling the interval.

        Call `unschedule` only if the interval is already scheduled, it's a
        no-op otherwise. All arguments are passed through.

        Args:
            force: Unschedule on-flight interval, if exists.
                Disabled by default.

            _arg1: Unused, included for API compatibility with ``Tk`` events
            _arg2: Unused, included for API compatibility with ``Tk`` traces
            _arg3: Unused, included for API compatibility with ``Tk`` event loop.

        See Also:
            See `unschedule` for the underlying function.
        '''
        if self.scheduled:
            self.unschedule(force=force)
        assert self.scheduled is False

    def reschedule(self,
                   _arg1: typing.Any = None,
                   _arg2: typing.Any = None,
                   _arg3: typing.Any = None,
                   ) -> None:
        '''Reschedule the interval.

        If the interval is already scheduled, this resets the interval, so it
        starts ticking from this point. If the interval is unscheduled, it
        schedules it.

        Either way, after ``interval`` milliseconds of calling this function,
        the action will run.

        Args:
            _arg1: Unused, included for API compatibility with ``Tk`` events
            _arg2: Unused, included for API compatibility with ``Tk`` traces
            _arg3: Unused, included for API compatibility with ``Tk`` event loop.
        '''
        if self.scheduled:
            self.timeout.reschedule()
        else:
            self.schedule()

    def doState_Trace(self, variable: 'var.Variable', etype: typing.Optional[str]) -> None:
        '''"Glue" the traced variable state to this interval state.

        This should be attached to the `trace <mixin.MixinTraces.trace>` as the
        callback function. It will change the interval state (using
        `reschedule`/`tryunschedule`) based on the variable state.

        Considers the boolean value for the variable contents, see :ref:`truth
        value testing <python:truth>` documentation.

        Works for all variable types, but should be restricted to
        `var.Boolean`. If you attach a non-boolean variable type, there is a
        warning on debug mode.
        '''
        if __debug__:
            from . import var
            if not isinstance(variable, var.Boolean):
                warnings.warn(f'Weird Variable: {variable} not a `var.Boolean`')
        assert etype in ('write', None)
        if variable.get():
            return self.reschedule()
        else:
            return self.tryunschedule()


class RateLimiter:
    '''Rate Limit an action.

    Define an action and a time limit. No matter how often you `hit` this
    object, the time between actions is never less than the ``limit`` (in
    milliseconds).

    It's ready to use automatically, there's no need to "schedule" it, like
    `Timeout`.
    Uses a `Timeout` internally.

    Args:
        widget: The widget to apply the interval to. When in doubt, use the
            `wroot <mixin.MixinWidget.wroot>` widget.
        action: The function to rate limit.
        limit: The rate-limit, in milliseconds. The ``action`` function is
            called at most once every this time.

    See Also:
        See also other time-related classes like `Interval` and `Timeout`.
    '''

    _last_ns: int
    '''Monotonic timer with nanosecond resolution (see `time.monotonic_ns`).

    On init, a negative value is stored
    '''

    def __init__(self, widget: 'mixin.MixinWidget', action: typing.Callable, limit: int):
        self.limit_ns = limit * int(1e6)  # ms -> ns
        self.action = action
        self.timeout = Timeout(widget, self._doAction, timeout=limit,
                               immediate=False)

        self._last_ns = - self.limit_ns - 1  # Guarantee the first time will work

    def _doAction(self) -> None:  # Internal
        '''Function to attach to the `Timeout` action.

        The last action execution time is stored here.
        '''
        # Re-Arm first (avoid race condition)
        self.timeout.unschedule()
        # Run the action
        self.action()
        # Mark the last action time
        self._last_ns = time.monotonic_ns()

    def hit(self,
            _arg1: typing.Any = None,
            _arg2: typing.Any = None,
            _arg3: typing.Any = None,
            ) -> bool:
        '''Mark the action as "active".

        When this function is called, the action may or may not run, depending
        on the last time it ran. If the rate limit is respected, the action
        runs, otherwise it will wait at least the ``limit`` time. Calling this
        function again before the limit is elapsed will reset the timer.

        Args:
           _arg1: Unused, included for API compatibility with ``Tk`` events
           _arg2: Unused, included for API compatibility with ``Tk`` traces
           _arg3: Unused, included for API compatibility with ``Tk`` event loop.

        Returns:
            If the action ran this time, return `True`, otherwise return `False`.
        '''
        monotime = time.monotonic_ns()
        if monotime - self._last_ns > self.limit_ns:
            self._doAction()  # TODO: Suport `async`: Use `self.after(0, self.action)`, needs a lock
            return True
        else:
            # logger.debug('Rate Limited. Elapsed %d ns', monotime - self._last_ns)
            self.timeout.reschedule()
            # TODO: Return the elapsed time?
            return False

    def cancel(self,
               _arg1: typing.Any = None,
               _arg2: typing.Any = None,
               _arg3: typing.Any = None,
               ) -> None:
        '''Cancel the next action execution.

        This cancels an action execution, when one is pending.

        Be advised, this means a triggered action **WILL NOT RUN**. When used
        for event processing, means events will be lost. Make sure you know
        what you are doing.

        Args:
            _arg1: Unused, included for API compatibility with ``Tk`` events
            _arg2: Unused, included for API compatibility with ``Tk`` traces
            _arg3: Unused, included for API compatibility with ``Tk`` event loop.
        '''
        self.timeout.unschedule()


@dataclass
class NotebookTab:
    '''Information for each `Notebook <tkmilan.Notebook>` tab.

    These are the parameters which can be configured:

    Args:
        name: The visible text on the tab itself
        widget: The widget corresponding to the tab. Must be a `container <mixin.ContainerWidget>`.
        image: Show an icon on the tab. Optional.
        extra:
            more arguments to the `add <tkinter.ttk.Notebook.add>` function. This
            is an escape hatch, optional.
        labelPosition:
            When the "image" is set, adjust the label position. When set to
            `CP.default`, only the image is included and no label is shown.

            Defaults to ``CP.E``, not available on the object.

    There are other parameters which are automatically calculated:

    Parameters:
        identifier: The internal tab identifier. Set by the widget itself.
        imageCompound: The ``compound`` settings. Based on "labelPosition",
            automatically calculated.

    Note:
        Technically, it is possible to have `single widgets <mixin.SingleWidget>` as "widget",
        but this results in broken layouts.
    '''
    name: str
    widget: 'mixin.ContainerWidget'
    image: typing.Optional[tk.Image] = None
    extra: typing.Mapping[str, typing.Any] = dc_field(default_factory=dict)
    labelPosition: InitVar[compoundT] = CP.E  # init-only
    identifier: typing.Optional[str] = dc_field(default=None, init=False)
    imageCompound: str = dc_field(init=False)

    def __post_init__(self, labelPosition: compoundT):
        if self.image:
            if labelPosition not in CP_Compound:
                raise ValueError(f'Invalid CP for "compound": {labelPosition}')
            self.imageCompound = CP_Compound[labelPosition]
        else:
            self.imageCompound = CP_Compound[False]

    @property
    def tk_idx(self) -> str:
        '''Get the ``Tk`` index to be used on upstream functions as needed.

        This uniquely identifies the correct tab.
        '''
        return str(self.widget.wproxy or self.widget)


@dataclass(init=False, frozen=True)
class NotebookTabOrder:
    '''Information for all `Notebook <tkmilan.Notebook>` tab ordering.

    These are the parameters which can be configured:

    Args:
        shown: Tab identiers to be shown, either on normal and disable modes.
            **Mandatory**.
        disabled: Tab identifiers to be shown as disabled.
            Optional, defaults to an empy set.

    Other parameters are automatically calculated:

        active: Tab identifiers to be show as active.
    '''
    shown: typing.Sequence[str]
    disabled: typing.Set[str]
    active: typing.Sequence[str] = dc_field(repr=False, compare=False)

    def __init__(self, shown: typing.Iterable[str], *,
                 disabled: typing.Optional[typing.Iterable[str]] = None):
        object.__setattr__(self, 'shown', tuple(shown))
        object.__setattr__(self, 'disabled', set(disabled or ()))
        if __debug__:
            active_set = tuple(sorted(set(self.shown)))
            active_sort = tuple(sorted(self.shown))
            delta_active = set(active_sort) - set(active_set)
            assert active_set == active_sort, f'Repeated shown keys: `{" ".join(delta_active)}`'
            bad_disabled = self.disabled - set(self.shown)
            assert len(bad_disabled) == 0, f'Invalid disabled keys: `{" ".join(bad_disabled)}`'
        object.__setattr__(self, 'active', tuple(e for e in shown if e not in self.disabled))

    def tk_states(self, allidx: typing.Iterable[str],
                  ) -> typing.Iterator[typing.Tuple[str, typing.Optional[int], NotebookTabStateT]]:
        '''Generate ``Tk`` information about all `NotebookTab`.

        Given all the possible tab identifiers, generate tuples with the following information:

        - ``idx``: The `NotebookTab` identifier
        - ``index``: The index to move the `NotebookTab` to. `None` if the tab
          should be hidden.
        - ``state``: The `NotebookTab` state to be configured. See
          `NotebookTabStateT`.

        Args:
            allidx: All `NotebookTab` identifiers.
        '''
        for index, idx in enumerate(self.shown):
            yield idx, index, tk.DISABLED if idx in self.disabled else tk.NORMAL
        for idx in set(allidx) - set(self.shown):
            # `Normal?` is not used
            yield idx, None, tk.HIDDEN


@dataclass
class TreeColumn:
    '''Configuration for each `tkmilan.Tree` column.

    This includes settings for both the column heading, and the column cells.

    There is no Python documentation, see ``Tk`` :tk:`ttk.Treeview column
    <ttk_treeview.htm#M18>` documentation.

    Args:
        name: The heading name, shown on the top of the column
        identifier: The id string. This is not shown to the user.
            Technically optional, but only when defining the columns, it will
            always have a `str` in normal circumstances.
        stretch: Adjust the column size when resizing the widget. Defaults to
            `True`, automatic resizes.
        image: Show an icon on the right side of the heading. Optional.
        nameAnchor: Anchor the heading name to a `CP`. Defaults to `CP.center`.
        cellAnchor: Anchor the body column cells to a `CP`. Defaults to `CP.W`.
    '''
    name: str
    identifier: typing.Optional[str] = None
    stretch: bool = True
    image: typing.Optional[tk.Image] = None
    nameAnchor: CP = CP.center
    cellAnchor: CP = CP.W

    def __post_init__(self):
        if self.nameAnchor == self.nameAnchor.default:
            raise ValueError(f'Invalid CP for "nameAnchor": {self.nameAnchor}')
        if self.cellAnchor == self.cellAnchor.default:
            raise ValueError(f'Invalid CP for "cellAnchor": {self.cellAnchor}')


@dataclass
class TreeRow:
    '''Configuration for each `tkmilan.Tree` row.

    This includes settings for each `TreeElement` record, applied by tag.

    There is no Python documentation, see ``Tk`` :tk:`ttk.Treeview tag options
    <ttk_treeview.htm#M72>` documentation.
    '''
    foreground: typing.Optional[str] = None
    background: typing.Optional[str] = None
    font: typing.Optional[str] = None
    image: typing.Optional[tk.Image] = None

    def map_tk(self) -> typing.Mapping:
        '''Calculate the ``Tk`` mapping to use.

        There is no Python documentation, see ``Tk`` :tk:`ttk.Treeview tag
        options <ttk_treeview.htm#M72>` documentation.
        '''
        rval = {}
        for f in fields(self):
            if (fval := getattr(self, f.name)) is not None:
                rval[f.name] = fval
        return rval


@dataclass
class TreeElement:
    '''Information for each `tkmilan.Tree` record.

    Technically, this is not enough to reconstruct the entire tree, but it
    should.

    The ``image`` argument is optional, but when created, no resizing is performed.
    By default, the ideal image size is ``16x16`` pixels.

    The ``tags`` information indicates which `TreeRow` configuration applies.

    Args:
        label: The leftmost string shown on the first column. This identifies the entire record.
        columns: A list of strings corresponding to the column data.
            Optional, defaults to `None`.
        children: A list of `TreeElement`, to be shown as children of this
            `TreeElement`. This can recurse without limit.
            Optional, defaults to `None`.
        tags: Record tags. Optional, defaults to an empty list.
        image: Show an icon on the left side of the record. Optional.
        data: Arbitrary data to store on the element.
            Optional, defaults to `None`.
    '''
    label: str
    columns: typing.Optional[typing.Sequence[str]] = None
    children: 'typing.Optional[typing.Sequence[TreeElement]]' = None
    tags: typing.Optional[typing.Sequence[str]] = None
    image: typing.Optional[tk.Image] = None
    data: typing.Any = None


class TextElement(abc.ABC):
    '''Common text element class.

    This is only an abstract class, a common base class for all the possible
    text elements.
    '''
    text: str
    atags: typing.Sequence[str]


@dataclass
class TextElementInline(TextElement):
    '''Text Element: An inline text span, with optional tags.

    This is the most basic text element, just some inline string.
    It can optionally define one main tag, and other secondary tags to apply to
    the text.

    Args:
        text: The string of text. Mandatory
        tag: The main tag for the text. Optional.
        tags: A list of secondary tags. Optional.
        data: A dictionary of ``data-*`` attributes. Default to an empty dictionary.

    Note:
        Setting secondary tags without a main tag is invalid.
    '''
    text: str
    tag: typing.Optional[str] = None
    tags: typing.Optional[typing.Sequence[str]] = None
    data: typing.Mapping[str, str] = dc_field(default_factory=dict)  # TODO: Default to `None`?

    def __post_init__(self):
        if self.tag is not None:
            if self.tags is not None:
                if self.tag in self.tags:
                    raise ValueError(f'Invalid tag complex: {self.tag} @ {self.tags}')
        else:
            assert self.tags is None, 'Secondary tags without main tag'
        if '\n' in self.text:
            tag_name = 'text' if self.tag is None else f'<{self.tag}>'
            warnings.warn(f'{tag_name} should not have newlines, use <br/>', stacklevel=14)
        self.has_tags = True

    @property
    def atags(self):
        '''Get all tags defined in the element.'''
        atags = []
        if self.tag:
            atags.append(self.tag)
        if self.tags:
            atags.extend(self.tags)
        return tuple(atags)


@dataclass
class TextElement_br(TextElement):
    '''Text Element: Line break.

    This is equivalent to a `TextElementInline` with ``"\\n"`` as text.
    '''
    def __post_init__(self):
        self.text = '\n'
        self.atags = tuple()
