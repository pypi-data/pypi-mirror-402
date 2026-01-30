'''
Functions to manipulate widgets and other objects, that make no sense to be
used externally.

If useful, they should be exposed as methods.
'''
import logging
import warnings
import typing
import sys
import math
from functools import wraps
from fractions import Fraction
from textwrap import dedent
from pathlib import Path

import tkinter as tk
import tkinter.filedialog
import tkinter.messagebox

try:
    # Try to use nicer pretty-print, from Python 3.10
    # | https://github.com/bitranox/pprint3x
    from pprint3x import pformat
except ImportError:
    from pprint import pformat

from . import model
if typing.TYPE_CHECKING:
    from . import mixin


logger = logging.getLogger(__name__)


# TODO: Localisation? Get the localised values from tk?
gettext_ALL_FILES = 'All Files'
gettext_SUPPORTED_FILES = 'All Supported Filetypes'
gettext_LOAD = 'Load'
gettext_OPEN = 'Open'
gettext_SAVE = 'Save'


def label_fallback(*labels: typing.Optional[str]) -> typing.Optional[str]:
    '''Calculate the fallback for several label objects.

    Similar to a series of ``or`` operator applications, considering edge cases
    like the label ``''``.
    '''
    for lbl in labels:
        if lbl is not None:
            return lbl
    return None


def label_size(chars: int) -> int:
    '''Estimate a label size (in pixels) by counting the number of chars.'''
    # TODO: Measure the font size: https://stackoverflow.com/a/30952406
    return math.ceil(-4 + 6 * math.pow(chars, 0.41))


def grid_size(*widgets: 'mixin.MixinWidget') -> 'model.GridSize':
    """Get the grid size for the given widgets.

    This should be used by a frame to calculate its grid size,
    by checking the values for all its children widgets.

    Args:
        widgets: Widgets in the same grid. There should be at least one.
    """
    def maxs(w: 'mixin.MixinWidget') -> typing.Tuple[int, int]:
        info = w.wgrid
        # logger.debug('=> Grid Info: %s', info)
        if info is None:
            return (-1, -1)  # Not included on a grid yet
        else:
            return (info.row + info.rowspan - 1, info.column + info.columnspan - 1)
    if __debug__:
        parents = set()
        for w in widgets:
            if w.wparent:
                parents.add(w.wparent)
        assert len(parents) == 1, f'Grid Size only for sibling widgets. Parents: {parents}'
    m = [maxs(w) for w in widgets]
    num_columns = max([w[1] for w in m]) + 1
    num_rows = max([w[0] for w in m]) + 1
    return model.GridSize(rows=num_rows, columns=num_columns)


def configure_grid(master: 'mixin.ContainerWidget',
                   column_weights: typing.Sequence[int], row_weights: typing.Sequence[int],
                   **kwargs: typing.Mapping[str, typing.Any]) -> None:
    """Configure the grid.

    Weights can be:

        - ``0`` : Fit the widgets, never resize
        - ``>0``: Resize with this number as weight

    Make sure to include all columns and rows. When in doubt, use 0.

    Args:
        column_weights: List of column weights
        row_weights: List of row weights
        kwargs: Extra arguments to the configuration functions
            :tk:`columnconfigure <grid.htm#M8>` / :tk:`rowconfigure
            <grid.htm#M24>`.
    """
    # TODO: Remove, use `mixin.ContainerWidget.pgrid`
    if __debug__:
        gw = master.gsize
        gr = model.GridSize(rows=len(row_weights), columns=len(column_weights))
        assert gw == gr, f'{master!r}: Invalid grid size: W::{gw} R::{gr}'
    assert isinstance(master, (tk.Widget, tk.Tk, tk.Toplevel)), f'{master} is not a valid widget'
    for col, w in enumerate(column_weights):
        master.columnconfigure(col, weight=w, **kwargs)  # type: ignore  # Invalid Types
    for row, h in enumerate(row_weights):
        master.rowconfigure(row, weight=h, **kwargs)  # type: ignore  # Invalid Types


def state_ignore(*toignore: 'mixin.MixinWidget'):
    '''Ignore some subwidgets for container widgets.

    Mark those widgets with the `ignoreContainerState
    <mixin.MixinWidget.ignoreContainerState>` flag. Should be called as part of
    the `setup_widgets <mixin.ContainerWidget.setup_widgets>` function in
    `container widgets <mixin.ContainerWidget>`.
    '''
    assert len(toignore) > 0, 'Nothing to ignore'
    for w in toignore:
        if w.ignoreContainerState is True:
            warnings.warn(f'Already ignored: {w}', stacklevel=2)
        w.ignoreContainerState = True


def vname(variable: tk.Variable) -> str:
    '''Collect the variable name.

    This is set on the object, but there's no typing support for it. Double check it here.
    '''
    assert hasattr(variable, '_name'), 'tk.Variable has changed the implementation'
    return variable._name  # type: ignore


def bind_mousewheel(widget, up: typing.Callable, down: typing.Callable, **kwargs) -> typing.Union[model.Binding, typing.Tuple[model.Binding, model.Binding]]:
    '''OS-independent mouse wheel bindings.

    This is a digital scroll.

    On Linux, this is implemented as two special mouse buttons ("up" and
    "down". Windows supports analog mouse wheels, but this function emulates a
    digital scroll out of that.

    The return value is platform-specific:

    - On Linux, return the two `Binding` object, for "up" and "down" mouse
      scroll.

    - On Windows, returns the single `Binding` object for the analog mouse
      scroll.

    Note:
        This uses regular `Binding` objects, remember that ``immediate=True``
        is needed to activate the binding on start.
    '''
    if sys.platform == 'linux':
        bup = model.Binding(widget, '<Button-4>', up, **kwargs)
        bdown = model.Binding(widget, '<Button-5>', down, **kwargs)
        return bup, bdown
    elif sys.platform == 'win32':
        def wrap_scroll(event):
            if event.delta > 0:
                return up(event)
            elif event.delta < 0:
                return down(event)
            else:
                raise NotImplementedError
        binding = model.Binding(widget, '<MouseWheel>', wrap_scroll, **kwargs)
        return binding
    else:
        logger.critical('Unsupported system platform: %s', sys.platform)
        return NotImplementedError


def scrollGenCommand(fn: typing.Callable[[float, float], None],
                     why: typing.Optional[bool],
                     what: str,
                     fn_scrollstate: typing.Callable,
                     ) -> typing.Callable[[float, float], None]:
    ''''''  # Internal, do not document
    # Wrap an existing scroll command function with automatic scroll state manipulation.

    # This should take a ``set`` function defined in a scrollbar, and produces
    # the function to attach to the ``xscrollcommand``/``yscrollcommand``
    # parameter in corresponding scrolled widget.

    # See `ScrolledWidget` and `Scrolled` for usage.
    if why:
        # Force Enable, don't change the state
        return fn
    else:
        # Automatic, change the state as needed
        @wraps(fn)
        def scrollGenCommand(sposs: float, eposs: float) -> None:
            # Defensive Programming, for older versions (make REALLY sure those are floats)
            spos: float = float(sposs)
            epos: float = float(eposs)
            allvisible: bool = math.isclose(spos, 0.0) and math.isclose(epos, 1.0)
            # if __debug__:
            #     logger.debug('ScrollCommand[%s]: [%f , %f] = %s', what, spos, epos, allvisible)
            fn_scrollstate(**{what: not allvisible})
            return fn(spos, epos)
        return scrollGenCommand


def scrollTo(widget: tk.Widget, *,
             x: typing.Optional[float], y: typing.Optional[float],
             anchor: model.CP,
             ) -> None:
    ''''''  # Internal, do not document
    # See `ScrolledWidget` and `Scrolled` for usage.
    if __debug__:
        if x is None and y is None:
            warnings.warn('Redundant `scrollTo`', stacklevel=3)
    assert x is None or (0.0 <= x <= 1.0), f'Invalid x={x}'
    assert y is None or (0.0 <= y <= 1.0), f'Invalid y={y}'
    assert anchor in model.CP_ScrollAnchor, f'Unsupported anchor: {anchor}'
    wview = model.WidgetView.fromwidget(widget)
    assert wview is not None, f'Unsupported widget (no wview): {widget!r}'
    afactor_x, afactor_y = model.CP_ScrollAnchor[anchor]
    if x is not None:
        assert isinstance(widget, tk.XView), f'Invalid Widget: {widget!r}'
        assert wview.deltax is not None, f'Unsupported widget (no X axis): {widget!r}'
        final_x: float = x + wview.deltax * afactor_x
        if __debug__:
            logger.debug('X = %f :: x=%f dx=%f afactor=%f',
                         final_x, x, wview.deltax, afactor_x)
        widget.xview_moveto(final_x)
    if y is not None:
        assert isinstance(widget, tk.YView), f'Invalid Widget: {widget!r}'
        assert wview.deltay is not None, f'Unsupported widget (no Y axis): {widget!r}'
        finaly: float = y + wview.deltay * afactor_y
        logger.debug('Y = %f :: y=%f dy=%f afy=%f',
                     finaly, y, wview.deltay, afactor_y)
        widget.yview_moveto(finaly)
    if __debug__:
        from math import isclose
        assert isinstance(widget, tk.Widget)
        wview_after = model.WidgetView.fromwidget(widget)
        assert wview_after is not None
        # Don't check when `delta==0.0`, this means the widget is now drawn yet
        if x is not None:
            assert wview_after.deltax is not None
            if wview_after.deltax > 0.0:
                assert wview_after.xview is not None
                assert wview_after.xshown(x) or any(isclose(x, v, rel_tol=1e-3) for v in wview_after.xview), f'wview={wview_after} x={x}'
        if y is not None:
            assert wview_after.deltay is not None
            if wview_after.deltay > 0.0:
                assert wview_after.yview is not None
                assert wview_after.yshown(y) or any(isclose(y, v, rel_tol=1e-3) for v in wview_after.yview), f'wview={wview_after} y={y}'


def _filedialog_fts(filetypes, includeSupported, includeAll):
    ''''''  # Internal, do not document
    fts = [(t, ft.pattern) for t, ft in filetypes.items()]
    if includeSupported is True and len(fts) > 1:
        fts.insert(0, (gettext_SUPPORTED_FILES, tuple([s for _, s in fts])))
    if includeAll:
        fts.append((gettext_ALL_FILES, '*'))
    return fts


# TODO: Support `typevariable`: https://www.tcl-lang.org/man/tcl8.6/TkCmd/getOpenFile.htm#M15
#                               Needs a return value change
def _filedialog_directory(initialDirectory: typing.Optional[Path], **kwargs: typing.Any) -> typing.Optional[Path]:
    ''''''  # Internal, do not document
    if initialDirectory:
        kwargs['initialdir'] = str(initialDirectory)
    rvalue = tk.filedialog.askdirectory(**kwargs)
    if rvalue is None or rvalue in ((), ''):  # Support multiple Python/Tk versions
        return None
    else:
        return Path(rvalue)


# TODO: Support `typevariable`: https://www.tcl-lang.org/man/tcl8.6/TkCmd/getOpenFile.htm#M15
#                               Needs a return value change
# TODO: Keep the same `Open`/`SaveAs` object between invocations in the `ask` loop
def _filedialog_file(fn: typing.Callable, initialDirectory: typing.Optional[Path], filetypes: model.FileTypes, real_title: str, includeSupported: bool, includeAll: bool, configureDefault: bool, **kwargs: typing.Any) -> typing.Optional[Path]:
    ''''''  # Internal, do not document
    if initialDirectory:
        kwargs['initialdir'] = str(initialDirectory)
    # Default Extension
    if len(filetypes) > 0 and configureDefault:
        # TODO: configureDefault can be an index into `filetypes.values()`
        defaultPattern = list(filetypes.values())[0]
        defaultextension = defaultPattern.suffix
    else:
        defaultextension = ''
    kwargs.update({
        'filetypes': _filedialog_fts(filetypes, includeSupported, includeAll),
        'defaultextension': defaultextension,
    })
    label_ftypes = [f'- {lbl}: {ft.pattern}' for lbl, ft in filetypes.items()]
    ask: bool = True  # Should we ask again?
    rvalue = None
    while ask:
        rvalue = fn(**kwargs)
        if rvalue is None or rvalue in ((), ''):  # Support multiple Python/Tk versions
            # User clicked cancel, bail with `None`
            ask, rvalue = False, None
        else:
            rvalue = Path(rvalue)
            if includeAll:
                # Accept all file names, independent of filetypes
                ask = False
            else:
                # Accept only the given FileTypes
                ask = not any(ft.matches(rvalue) for ft in filetypes.values())
        if ask:
            # Again! Ask the user for another file (or allow it to leave)
            label = dedent('''
            Invalid File:
            %s
            Allowed File Types:
            %s
            ''').strip() % (rvalue, '\n'.join(label_ftypes))
            if not tk.messagebox.askretrycancel(title=real_title, message=label):
                ask, rvalue = False, None
    return rvalue


def ask_directory_load(parent: 'mixin.MixinWidget',
                       title: str = 'Folder', full_title: typing.Optional[str] = None,
                       initialDirectory: typing.Optional[Path] = None,
                       **kwargs) -> typing.Optional[Path]:
    '''Wrap a file dialog that returns a directory name, for loading data.

    ..
        Python 3.8 is missing this reference, included in Python 3.9:

        See Python documentation in `tkinter.filedialog.askdirectory`.

    Since this is for loading data, it will guarantee the directory exists.

    Args:
        title: Window Title, prefixed by the operation mode.
        full_title: Override final ``title``, ignoring the operation mode.
            Optional.
        initialDirectory: Initial Directory to open the dialog, or `None` to use the
            OS-specific default.

            Optional, defaults to `None`.
        kwargs: Passed to the upstream function.

    Returns:
        If the user bails, return `None`.
        Otherwise return a `Path <pathlib.Path>`, guaranteed to be a directory.

    See Also:
        See `ask_directory_save` for the Save alternative to this function.
    '''
    kwargs.update({
        'parent': parent,
        'title': full_title or f'{gettext_LOAD} {title}',
        'mustexist': True,
    })
    path = _filedialog_directory(initialDirectory, **kwargs)
    if __debug__:
        # `mustexist` already guarantees this, just double checking on debug mode
        if path is not None:
            assert path.is_dir(), f'Invalid directory: {path!r}'
    return path


def ask_directory_save(parent: 'mixin.MixinWidget',
                       title: str = 'Folder', full_title: typing.Optional[str] = None,
                       initialDirectory: typing.Optional[Path] = None,
                       **kwargs) -> typing.Optional[Path]:
    '''Wrap a file dialog that returns a directory name, for saving data.

    ..
        Python 3.8 is missing this reference, included in Python 3.9:

        See Python documentation in `tkinter.filedialog.askdirectory`.

    Since this is for saving data, it allows for non-existing directories.

    Args:
        title: Window Title, prefixed by the operation mode.
        full_title: Override final ``title``, ignoring the operation mode.
            Optional.
        initialDirectory: Initial Directory to open the dialog, or `None` to use the
            OS-specific default.

            Optional, defaults to `None`.
        kwargs: Passed to the upstream function.

    Returns:
        If the user bails, return `None`.
        Otherwise return a `Path <pathlib.Path>`.

    See Also:
        See `ask_directory_load` for the Load alternative to this function.
    '''
    kwargs.update({
        'parent': parent,
        'title': full_title or f'{gettext_SAVE} {title}',
        'mustexist': False,
    })
    return _filedialog_directory(initialDirectory, **kwargs)


def ask_file_load(parent: 'mixin.MixinWidget',
                  title: str = 'File', full_title: typing.Optional[str] = None,
                  initialDirectory: typing.Optional[Path] = None,
                  filetypes: typing.Optional[model.FileTypes] = None,
                  includeSupported: bool = True, includeAll: bool = True, configureDefault: bool = False,
                  **kwargs) -> typing.Optional[Path]:
    '''Wrap a file dialog that returns a file name, for loading data.

    ..
        Python 3.8 is missing this reference, included in Python 3.9:

        See ``Tk`` documentation in `tk.filedialog.askopenfilename`.

    Since this is for loading data, it will guarantee the file exists.

    Args:
        title: Window Title, prefixed by the operation mode.
        full_title: Override final ``title``, ignoring the operation mode.
            Optional.
        initialDirectory: Initial Directory to open the dialog, or `None` to use the
            OS-specific default.
            Optional, defaults to `None`.
        filetypes:
            `FileTypes <model.FileTypes>` object with all supported
            `FileType` patterns.

            This is a mapping from UI string, to `FileType` object.
            The default option is the first one, but this interacts with
            ``includeSupported``.

            Optional, when not given it acts as no filetypes are supported. See
            ``includeAll``.
        includeSupported:
            Include a pattern for all supported filetypes, on the filetypes list.

            This is included as the first pattern, therefor it acts as the default selection.
            Only included if there is more that one filetype.

            Defaults to `True`.
        includeAll:
            Include a pattern for all files, on the filetypes list.

            This is included as the last pattern, so it will be the default
            only if there are no supported filetypes.

            Defaults to `True`.
        configureDefault:
            Configure the default suffix as the first element on ``filetypes``
            (if exists). This is pure evil because the user will get a suffix
            added that is not shown anywhere.

            Defaults to `False`.

        kwargs: Passed to the upstream function.

    Note:
        Giving no ``filetypes`` forces ``includeAll`` to `True`.

    Returns:
        If the user bails or the selected file is not supported, return `None`.
        Otherwise return a `Path <pathlib.Path>`, guaranteed to be a file.

    See Also:
        See `ask_file_save` for the Save alternative to this function.
    '''
    # Setup the filetype argument
    if filetypes is None:
        filetypes = model.FileTypes()
        includeAll = True
    real_title = full_title or f'{gettext_LOAD} {title}'
    kwargs.update({
        'parent': parent,
        'title': real_title,
    })
    path = _filedialog_file(tk.filedialog.askopenfilename,
                            initialDirectory, filetypes, real_title, includeSupported, includeAll, configureDefault, **kwargs)
    if __debug__:
        if path is not None:
            assert path.is_file(), f'Invalid file: {path!r}'
    return path


def ask_file_save(parent: 'mixin.MixinWidget',
                  title: str = 'File', full_title: typing.Optional[str] = None,
                  initialDirectory: typing.Optional[Path] = None,
                  filetypes: typing.Optional[model.FileTypes] = None,
                  includeSupported: bool = False, includeAll: bool = False, configureDefault: bool = False,
                  **kwargs) -> typing.Optional[Path]:
    '''Wrap a file dialog that returns a file name, for saving data.

    ..
        Python 3.8 is missing this reference, included in Python 3.9:

        See ``Tk`` documentation in `tk.filedialog.askopenfilename`.

    Since this is for saving data, it allows for non-existing files.

    Args:
        title: Window Title, prefixed by the operation mode.
        full_title: Override final ``title``, ignoring the operation mode.
            Optional.
        initialDirectory: Initial Directory to open the dialog, or `None` to use the
            OS-specific default.
            Optional, defaults to `None`.
        filetypes:
            `FileTypes <model.FileTypes>` object with all supported
            `FileType` patterns.

            This is a mapping from UI string, to `FileType` object.
            The default option is the first one, but this interacts with
            ``includeSupported``.

            Optional, when not given it acts as no filetypes are supported. See
            ``includeAll``.
        includeSupported:
            Include a pattern for all supported filetypes, on the filetypes list.

            This is included as the first pattern, therefor it acts as the default selection.
            Only included if there is more that one filetype.

            Defaults to `False`.
        includeAll:
            Include a pattern for all files, on the filetypes list.

            This is included as the last pattern, so it will be the default
            only if there are no supported filetypes.

            Defaults to `False`.
        configureDefault:
            Configure the default suffix as the first element on ``filetypes``
            (if exists). This is pure evil because the user will get a suffix
            added that is not shown anywhere.

            Defaults to `False`.

        kwargs: Passed to the upstream function.

    Note:
        Giving no ``filetypes`` forces ``includeAll`` to `True`.

    Returns:
        If the user bails or the selected file is not supported, return `None`.
        Otherwise return a `Path <pathlib.Path>`.

    See Also:
        See `ask_file_load` for the Load alternative to this function.
    '''
    # Setup the filetype argument
    if filetypes is None:
        filetypes = model.FileTypes()
        includeAll = True
    real_title = full_title or f'{gettext_SAVE} {title}'
    kwargs.update({
        'parent': parent,
        'title': real_title,
    })
    return _filedialog_file(tk.filedialog.asksaveasfilename,
                            initialDirectory, filetypes, real_title, includeSupported, includeAll, configureDefault, **kwargs)


def binding_disable(event=None):
    '''Disable the binding (stop chaining the bind functions).

    Attach this function to a `Binding` event to disable the processing, even
    for further validations.
    '''
    return 'break'


# TODO: Rename `valInteger`
def valNumber(string: str) -> typing.Optional[int]:
    '''Validate a number in any supported base.

    Returns:
        `None` if not a number, `int` otherwise.
    '''
    try:
        return int(string, base=0)
    except ValueError:
        return None


def valFloat(string: str) -> typing.Optional[float]:
    '''Validate a number is a `float`.

    This ignores all possible whitespace.

    Returns:
        `None` if cannot be parsed as a floating point, `float` otherwise.
    '''
    try:
        return float(string)
    except ValueError:
        return None


def valFraction(string: str) -> typing.Optional[Fraction]:
    '''Validate a number is a `Fraction <fractions.Fraction>` (ratio between
    integers).

    This ignores all possible whitespace, it is more lenient than the upstream
    `Fraction <fractions.Fraction>` function.

    Returns:
        `None` if cannot be parsed as fraction, `Fraction <fractions.Fraction>`
        otherwise.
    '''
    try:
        return Fraction(''.join(string.split(sep=None)))
    except ValueError:
        return None


def validation_pass(label: str, why: typing.Optional[model.VWhy] = None, **kwargs) -> typing.Optional[bool]:
    '''Neutral validation function, accepts everything.

    Use this function to validate all states, as the ``fn`` parameter for
    `model.VSettings`.
    '''
    return True


def validation_fail(label: str, why: typing.Optional[model.VWhy] = None, **kwargs) -> typing.Optional[bool]:
    '''Absorvent validation function, denies everything.

    Use this function to invalidate all states, as the ``fn`` parameter for
    `model.VSettings`.
    '''
    return False


def state_bindtags(widget: tk.Widget, state: bool, *,
                   bt_on: typing.Tuple[str, ...],
                   bt_off: typing.Tuple[str, ...],
                   ):
    '''Change the widget state based on ``bindtags`` state.

    This is useful to truly disable all events flowing to a ``widget``, since
    the ``Tk`` state might keep some events enabled.

    There is no Python documentation, see ``Tk`` :tk:`bindtags <bindtags.htm>`
    documentation.

    Args:
        widget: Widget to modify
        state: Should the widget be enabled (regular state) or disabled (fully
            dead).
        bt_on: BindTags when enabled.
            Mandatory, usually ``widget.bindtags()`` when the widget is
            created.
        bt_off: BindTags when disabled.
            Mandatory, usually ``widget.bindtags()[-2:]`` when the widget is
            created.
    '''
    # This should not be moved to `mixin.MixinWidget`, since it might be used
    # on non-tkmilan widgets.
    if state:
        # Restore BindTags
        return widget.bindtags(bt_on)
    else:
        # Disable BindTags for this widget
        return widget.bindtags(bt_off)


def widget_toolwindow(window: typing.Union[tk.Wm]):
    '''Change the widget "toolwindow" state.

    This state makes the window present itself as a kind of toolbar window for
    another window. Can also be used on the `RootWindow`, in which case the
    window takes similar properties.

    See ``Tk`` :tk:`wm transient <wm.htm#M64>` documentation. This is only a
    window manager hint.

    This is an irreversible action.
    Depending on the platform, this is defined in several ways:

    - On Windows, set the ``toolwindow`` window attribute, see ``Tk``
      :tk:`wm attributes toolwindow <wm.htm#M13>` documentation.
    - On Linux, mark the ``type`` window attribute as ``dialog``, see ``Tk``
      :tk:`wm attributes type dialog <wm.htm#M26>` documentation.

    All other platforms are unsupported.
    '''
    if sys.platform == 'win32':
        window.wm_attributes('-toolwindow', True)
    elif sys.platform.startswith('linux'):
        window.wm_attributes('-type', 'dialog')
    else:
        if __debug__:
            raise ValueError(f'Unsupported ToolWindow Platform: "{sys.platform}"')


def window_center(window: typing.Union[tk.Tk, tk.Toplevel], where: tk.Tk,
                  deltaW: typing.Optional[int] = None, deltaH: typing.Optional[int] = None,
                  ) -> bool:
    '''Center ``window`` on a root window ``where``.

    Considers the sizes of both elements. The ``delta*`` arguments are useful
    to center the window in a single direction.

    This is only a window manager hint, the geometry might not actually move.
    This is confirmed in tiling window managers.

    Args:
        window: The window to move.
        where: The `RootWindow` to consider as the "center".

        deltaW: Override the calculated delta width.
        deltaH: Override the calculated delta height.

    Returns:
        Returns `True` is the window moved to its requested location, `False`
        otherwise.
    '''
    iW = window.winfo_reqwidth()
    iH = window.winfo_reqheight()
    # if __debug__:
    #     logger.debug('Window: %dx%d', iW, iH)
    #     logger.debug('  Geometry: %s', window.winfo_geometry())
    oW = where.winfo_width()
    oH = where.winfo_height()
    oX = where.winfo_rootx()
    oY = where.winfo_rooty()
    # if __debug__:
    #     logger.debug(' Where: %dx%d @ %d:%d', oW, oH, oX, oY)
    if deltaW is None:
        deltaW = (oW - iW) // 2
    if deltaH is None:
        deltaH = (oH - iH) // 2
    # if __debug__:
    #     logger.debug('Delta:: %dx%d', deltaW, deltaH)
    x, y = oX + deltaW, oY + deltaH
    geometry = '+%d+%d' % (x, y)
    # if __debug__:
    #     logger.debug('Geometry:: %s', geometry)
    window.geometry(geometry)
    return window.geometry() == geometry


if __debug__:
    def debugWidget(widget):
        '''Log all information about the given widget.

        As the name implies, this is a debug function, only available on
        `__debug__`.

        This should be used like this, on the `RootWindow`:

        .. code:: python

            def setup_adefaults(self):
                if __debug__:
                    BindingGlobal(self, '<Shift-Button-2>', fn.onDebugWidget,
                                  immediate=True, description='Debug GUI for Current Widget')
                    BindingGlobal(self, '<Control-Shift-Button-2>', fn.onDebugPWidget,
                                  immediate=True, description='Debug GUI on Parent Widget')

        Choose your own binding keys, these are just an example.

        See Also:
            See the wrapper functions `onDebugWidget`, `onDebugPWidget`.

            See the :envvar:`TKMILAN_DEBUG` environment variable for extra
            debug settings.
        '''
        assert __debug__
        import os
        from . import mixin
        from . import Scrolled

        DEBUG_LIST = os.environ.get('TKMILAN_DEBUG', '').split(',')

        logger.debug('%s [%s]', widget, widget.__class__.__qualname__)
        if widget is None:
            return
        if not isinstance(widget, mixin.MixinWidget):
            # Not a "proper" widget, some internal helper
            pass
        else:
            logger.debug('| %s', widget.gstate)
            if widget.gstate.__class__ != model.GuiState:
                logger.debug('| - Real: %s', widget.gstate.real())
            if hasattr(widget, 'wlabel'):
                logger.debug('| Label: %s', widget.wlabel)
            if isinstance(widget, tk.Toplevel) or isinstance(widget.wproxy, tk.Toplevel):
                wview = None
            elif isinstance(widget, Scrolled) or isinstance(widget.wproxy, Scrolled):
                wview = model.WidgetView.fromwidget((widget.wproxy or widget).canvas)
            else:
                wview = widget.wview
            if wview:
                logger.debug('| View: %s', wview)
            wgrid = widget.wgrid
            if wgrid:
                logger.debug('| Grid: %s', wgrid)
                if (wparent := widget.wparent) is not None:
                    logger.debug('| | r=%r', wparent.rowconfigure(wgrid.row))
                    logger.debug('| | c=%r', wparent.columnconfigure(wgrid.column))
            if isinstance(widget, mixin.ContainerWidget):
                logger.debug('| Widgets:')
                for wname, w in widget.widgets.items():
                    logger.debug('| | %s: %s Grid(%s)', wname, w.gstate, w.wgrid)
                gsize = widget.gsize
                wcols, wrows = widget.grid_size()
                logger.debug('| %r widget=%dR%dC', gsize, wrows, wcols)
                if 'grid' in DEBUG_LIST:
                    if gsize is not None:
                        for r in range(gsize.rows):
                            logger.debug('| | R#%d: %r', r, widget.rowconfigure(r))
                        for c in range(gsize.columns):
                            logger.debug('| | C#%d: %r', c, widget.columnconfigure(c))
                if widget != widget.wroot:
                    wstate_lines = pformat(widget.wstate).splitlines()
                    logger.debug('State: %s', wstate_lines[0])
                    for ln in wstate_lines[1:]:
                        logger.debug('     : %s', ln)
            elif isinstance(widget, mixin.SingleWidget):
                logger.debug('| Widget: %r', widget.wstate)
                logger.debug('| - Variable: %s', widget.variable)
            else:
                raise NotImplementedError(f'{widget}: Unknown class: {widget.__class__.__qualname__}')

    def onDebugWidget(event):
        '''Run `debugWidget` on the event widget.'''
        return debugWidget(event.widget)

    def onDebugPWidget(event):
        '''Run `debugWidget` on the event widget's parent widget.'''
        widget = event.widget
        if widget.wparent is None:
            assert str(widget) == '.', f'Invalid widget parent: {widget!r} » {widget.wparent!r}'
        return debugWidget(widget.wparent)
