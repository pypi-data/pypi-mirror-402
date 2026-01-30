#!/usr/bin/env python
"""
`tkinter`'s evil twin.

Includes also some aliases to other models:

- ``Binding``: Alias for `model.Binding`.
- ``Direction``: Alias for `model.Direction`.
- ``Justification``: Alias for `model.Justification`.
- ``CP``: Alias for `model.CP`.
"""
import sys
import typing
from importlib.metadata import version as metadata_version, PackageNotFoundError
import logging
import warnings
from contextlib import contextmanager
from collections import defaultdict
from functools import lru_cache
from dataclasses import dataclass
from pathlib import Path

import tkinter as tk
import tkinter.font
from tkinter import ttk
import tkinter.simpledialog  # Implemented in newer typeshed versions

from . import util
from . import autolayout
from . import model
from . import diagram
from . import drender
from . import var
from . import validation
from . import mixin
from . import exception
from . import parser
from . import bg
from . import fn


__VERBOSE_MODULES = (
    'PIL',
)
if __debug__:
    __VERBOSE_MODULES_DEBUG: typing.Mapping[str, typing.Sequence[str]] = {
    }
    assert all('' not in lst for lst in __VERBOSE_MODULES_DEBUG.values())
__VERBOSE_SUBMODULES = (
    'autolayout', 'autostate',
    'image',
    'styling',
    'model.layout', 'model.ft',
    'mixin.traces', 'mixin.valid', 'mixin.grid', 'mixin.autolayout',
    'drender',
    'bg',
    'eventbus',
)
if __debug__:
    __VERBOSE_SUBMODULES_DEBUG: typing.Mapping[str, typing.Sequence[str]] = {
        'grid:debug': ['mixin.grid'],
        'layout:debug': ['autolayout', 'mixin.autolayout'],
        'validation:debug': ['mixin.valid'],
        'eventbus:debug': ['eventbus'],
        'canvas:render': ['drender'],
    }
    assert all('' not in lst for lst in __VERBOSE_SUBMODULES_DEBUG.values())
MODULES_VERBOSE = [1]  # `logging.getLogger` results in a TypeError, on purpose
'''DEPRECATED. See `LOGGING_VERBOSE`.'''  # TODO: Remove in v0.40


def LOGGING_VERBOSE(modules: bool = True, submodules: bool = True) -> typing.Iterator[logging.Logger]:
    '''Shows spammy modules, should be silenced by the calling application.

    These sub-modules sent enormous amount of logs, bordering on spam, on the
    ``logging.DEBUG`` setting.

    The calling application should use something like this to silence them:

    .. code:: python

        if loglevel == logging.DEBUG:
            for log in LOGGING_VERBOSE():
                log.setLevel(logging.INFO)

    .. note:: A similar feature existed in the past, as `MODULES_VERBOSE`.
        Migrate to this alternative ASAP.

    .. only:: debug

        .. note::
            See the :envvar:`TKMILAN_DEBUG` environment variable for
            information on how to configure this at runtime.
    '''
    if __debug__:
        # Un-Silence spammy modules, based on `TKMILAN_DEBUG`
        import os
        DEBUG_LIST = os.environ.get('TKMILAN_DEBUG', '').split(',')
        # Keep these modules as verbose
        kmodules = set(m for lkey, ms in __VERBOSE_MODULES_DEBUG.items() for m in ms if lkey in DEBUG_LIST)
        ksubmodules = set(m for lkey, ms in __VERBOSE_SUBMODULES_DEBUG.items() for m in ms if lkey in DEBUG_LIST)
        kcount = len(kmodules) + len(ksubmodules)
        if kcount > 0:
            logger.debug('Extra Debug Logs: #%d `%s`', kcount, ' '.join(DEBUG_LIST))
    if modules:
        for dmodule in __VERBOSE_MODULES:
            if __debug__:
                if dmodule in kmodules:
                    continue
            yield logging.getLogger(dmodule)
    if submodules:
        for dmodule in __VERBOSE_SUBMODULES:
            if __debug__:
                if dmodule in ksubmodules:
                    continue
            yield logging.getLogger(f'{__package__}.{dmodule}')


# Store the project version number
__version__: typing.Optional[str]
__version_numeric__: typing.Tuple[int, ...]
try:
    # The "project" name is the same as the package
    __version__ = metadata_version(__package__)
    __version_numeric__ = tuple(int(n) for n in __version__.split('.')[:2])
except PackageNotFoundError:
    __version__ = None
    __version_numeric__ = (-1,)


# TypeChecking
class varTree(var.ObjectList[model.TreeElement]):
    '''Type-Checking variable type for `Tree`.'''
    pass


varOrientation = typing.Union[typing.Literal['vertical'], typing.Literal['horizontal']]
'''Type-Checking variable type for ``orientation`` in `FramePaned`/`Separator`'''
varEventBusEventType = typing.Union[None, typing.Type[bool], typing.Type[bg.ELRes]]
'''Type-Checking variable type for ``event`` in `RootWindow.register_eventbus_response`'''
varSidSettings = typing.Union[
    str, typing.Tuple[str, ...],
    typing.Tuple[int, ...],
    bool,
    model.DStyle
]
'''Type-Checking variable type for `RootWindow.styleIDs` mapping'''


# Aliases
CP = model.CP
Direction = model.Direction
Justification = model.Justification
Binding = model.Binding

# Layouts
# TODO: Transform into a `enum.Enum`?
AUTO = autolayout.AUTO
'''Automatic Layout.
'''
HORIZONTAL = autolayout.HORIZONTAL
'''Horizontal (1 row) Layout.
'''
VERTICAL = autolayout.VERTICAL
'''Vertical (1 column) Layout.
'''

logger = logging.getLogger(__name__)
logger_autostate = logging.getLogger('%s.autostate' % __name__)
logger_image = logging.getLogger('%s.image' % __name__)
logger_model_layout = logging.getLogger('%s.model.layout' % __name__)
logger_styling = logging.getLogger('%s.styling' % __name__)
logger_eventbus = logging.getLogger('%s.eventbus' % __name__)


# Usable Widgets


class RootWindow(tk.Tk, mixin.ContainerWidget):
    '''A root window, the toplevel widget for the entire application.

    Usually there's only one of this in a single application. Multiple root
    windows are unsupported.

    The `setup_images` function can be overriden to load any number of images
    in any way. The common usage of loading all images in a folder is supported
    directly with ``imgfolder``.

    On debug mode, this will sanity check the entire GUI, by reading its state.
    This doesn't happen in production.

    See `tkinter.Tk`.

    Args:
        theme: Theme to use.
            Default to choosing a tasteful choice depending on the OS and ``theme_simple``.
        theme_simple: When choosing a default theme, prefer a beautiful theme,
            without the full feature range.
            If you use the full feature range (custom colours, complex state
            validation), set this to `False`.
            Does nothing if ``theme`` is chosen, this only affects the default
            selection. Defaults to `True`.
        rpad: Recursively pad all container widgets.
            See `ContainerWidget.pad_container`.
            Disable with `None`, defaults to ``5`` pixels.
        imgfolder: Folder with images to be loaded (see `setup_images_folder`). Optional.
        cls: Window Class Name. Defaults to ``"tkinter"``, the project name, so
            that it can be distiguished from the upstream default, ``"Tk"``.
        style: Configure the widget style.

    Note:
        Technically, it should be OK to use multiple root windows per-process,
        but this hasn't been tested, there are no test cases where this makes
        sense.
    '''
    isNoneable: bool = False  # Always present, no matter what
    styleIDs: typing.Optional[typing.Mapping[str, typing.Mapping[str, varSidSettings]]] = None
    '''Configure `tkinter.ttk.Style` for registered "styleID".

    See Also:
        Register styleID using `register_styleID` function. This function is
        defined on the root window, use `MixinWidget.wroot` to reach it from
        any widget.
    '''
    eL: typing.Mapping[str, bg.EventLoop]
    '''Mapping between friendly name and `EventLoop` to configure.

    Define using `setup_eventloops`, defaults to an empty mapping.
    '''
    eL_strict: bool = False
    '''When calling `register_eventbus_response`, it is validated the
    corresponding eventloop exists, on the post processing step.

    When set, this validation will produce an error, otherwise it will be a
    simple warning. Defaults to producing a warning.
    '''
    layout_expand = False  # Hardcode, `tk.Tk` has no parent grid to expand
    images_builtin: typing.Sequence[str]
    '''Set of builtin image names. Always available.'''

    @dataclass
    class Style(model.WStyle):
        '''`RootWindow` style object.

        These are the settings:

        Args:
            tool_window: When enabled, marks the window as a tool window, not a
                regular window. The precise meaning of this setting depends on
                the OS.
            toplevel: When enabled, shows the window above all other windows.
            clear_ro: When enabled, set this color as the readonly background
                for particular widgets: `ComboboxN` and `SpinboxN`.
                This is useful to distinguish readonly from normal and disabled
                widgets.
            combobox_ro: When enabled, tweak the default `Checkbox` style to
                distinguish the readonly and the true disabled states visually
                (there is a complex logic with the states, see the `Checkbox`
                documentation).
                Enabled by default.

        Note:
            To control window fullscreen state, see `rgstate`.
        '''
        # These attributes should remain forever, it doesn't make sense to
        # change them at runtime. Not to be confused with `WindowState` for
        # dynamic state.
        tool_window: bool = False
        toplevel: bool = False
        clear_ro: typing.Optional[str] = 'white smoke'
        checkbox_ro: bool = True

    def __init__(self, *args,
                 theme: typing.Optional[str] = None, theme_simple: bool = True,
                 rpad: typing.Optional[int] = 5,
                 imgfolder: typing.Optional[Path] = None,
                 cls: str = 'tkmilan',
                 style: Style = Style(_default=True),
                 **kwargs):
        self.wstyle = style
        self._bindings_global: typing.MutableMapping[str, model.BindingGlobal] = {}
        self.images_cache: typing.MutableMapping[str, model.ImageCache] = {}
        self._styleIDs: typing.MutableSet[str] = set()
        self._styleComplex: typing.MutableMapping[str, typing.Tuple[str, ...]] = {}
        if __debug__:
            self.__styleIDs_other: typing.MutableMapping[str, typing.MutableSet[str]] = defaultdict(set)
        super().__init__(baseName=None, className=cls)  # tk.Tk
        self.setup_images(imgfolder)  # Register all images before the child widgets are setup
        self.__event_bus: typing.MutableMapping[
            typing.Union[None, str, bg.EventLoop],
            typing.MutableMapping[
                varEventBusEventType,
                typing.MutableSequence[bg.callbackT]],
        ] = {}
        self.__event_bus_processed = False
        self.init_container(*args, **kwargs)
        self.eL = self.setup_eventloops() or {}
        self.process_event_bus()
        if rpad:
            self.pad_container(pad=rpad, recursive=True)
        self.style = self.setup_style(theme, theme_simple)
        if self.wstyle.clear_ro is not None:
            self.after_idle(self.__setstyle_clear_ro, self.wstyle.clear_ro)  # No need for a `TimeoutIdle` here
        if self.wstyle.checkbox_ro:
            self.after_idle(self.__setstyle_checkbox_ro)
        self.after_idle(self.setup_styleID)  # No need for a `TimeoutIdle` here
        # Set window style attributes. See
        # - https://wiki.tcl-lang.org/page/wm+attributes
        if self.wstyle.tool_window:
            fn.widget_toolwindow(self)
        if self.wstyle.toplevel:
            self.wm_attributes('-topmost', True)
        if __debug__:
            self.after_idle(self.__sanity_check)  # No need for a `TimeoutIdle` here

    if __debug__:
        def __sanity_check(self):
            import traceback
            logger.debug('=> Sanity Check GUI State')
            try:
                self.wstate_get()
            except Exception:
                traceback.print_exc()
                sys.exit(100)

    def setup_style(self, theme: typing.Optional[str], theme_simple: bool) -> ttk.Style:
        '''Configure root `tkinter.ttk.Style` object'''
        style = ttk.Style(self)
        if theme is None:
            if sys.platform == 'win32':
                # On Windows
                if theme_simple:
                    # Simple Theme
                    theme = 'vista'
                else:
                    # Complex Theme
                    theme = 'winnative'
            elif sys.platform.startswith('linux'):
                # On Linux, 'alt' supports everything and is "beautiful"
                theme = 'alt'
        if theme is not None:
            if __debug__:
                all_themes = style.theme_names()
                logger_styling.debug('Available Themes: %s', ' '.join(all_themes))
                assert theme in all_themes, f'Invalid Theme: {theme}'
            style.theme_use(theme)
        # Calculate Dynamic Styles
        map_root_fg = dict(style.map('.', 'foreground'))
        assert 'disabled' in map_root_fg
        lookup_root_font = style.lookup('.', 'font')
        lookup_root_fg = style.lookup('.', 'foreground')
        lookup_root_bg = style.lookup('.', 'background')
        lookup_root_selectbg = style.lookup('.', 'selectbackground')
        assert None not in [lookup_root_font, lookup_root_selectbg]
        self.styleDynamic: typing.Mapping[model.DStyle, str] = {
            model.DStyle.Color_FG: lookup_root_fg,
            model.DStyle.Color_BG: lookup_root_bg,
            model.DStyle.Color_FG_Disabled: map_root_fg['disabled'],
            model.DStyle.Font_Default: lookup_root_font,
            model.DStyle.Color_BG_Selected: lookup_root_selectbg,
        }
        assert len(self.styleDynamic) == len(model.DStyle), 'Missing Dynamic Style Definitions'
        if __debug__:
            logger_styling.debug('Style Static')
            for i, value in model.SStyle.items():
                logger_styling.debug('- %s: %s', i, value)
            logger_styling.debug('Style Dynamic')
            for i, string in self.styleDynamic.items():
                logger_styling.debug('- %s: %s', i, string)
        return style

    def setup_styleID(self) -> None:
        widget_sids = self._styleIDs
        wcomplex_sids = self._styleComplex
        self_sids = typing.cast(typing.MutableMapping[str, typing.Mapping[str, varSidSettings]], self.styleIDs or {})
        cfg_sids = set(self_sids.keys())
        if __debug__:
            logger_styling.debug('Set styleID Settings: CFG#%d Widgets#%d WComplex#%d', len(self_sids), len(widget_sids), len(wcomplex_sids))
        if __debug__:
            widget_other_sids = set(sid for sval in self.__styleIDs_other.values() for sid in sval)
            widget_main_sids = widget_sids - widget_other_sids
            if not (widget_main_sids <= cfg_sids):
                logger_styling.critical('Missing styleID configuration for `%r`', tuple(widget_main_sids - cfg_sids))
                sys.exit(100)
            for used_mainsid in cfg_sids.intersection(set(self.__styleIDs_other.keys())):
                logger_styling.debug('» %s: Check other classes `%s`', used_mainsid, ' '.join(self.__styleIDs_other[used_mainsid]))
            del self.__styleIDs_other  # Save RAM
        for csid, ssids in wcomplex_sids.items():
            if csid in self_sids:
                logger_styling.warning('| %s: Existing settings', csid)
            else:
                sid_options: typing.MutableMapping[str, varSidSettings] = {}
                if __debug__:
                    logger_styling.debug('| %s: %s', csid, ' '.join(ssids))
                for sid in ssids:
                    sid_simple_options = self_sids.get(sid, {})
                    if __debug__:
                        sid_simple_repetitions = set(sid_simple_options).intersection(set(sid_options))
                        if len(sid_simple_repetitions) > 0:
                            logger_styling.critical('Alias on complex styleID "%s": Aliased "%s"', csid, " ".join(sid_simple_repetitions))
                            sys.exit(100)
                    sid_options.update(sid_simple_options)
                self_sids[csid] = sid_options
        for sid, style_rawoptions in self_sids.items():
            style_options: typing.MutableMapping[str, varSidSettings] = {}
            if __debug__:
                style_showoptions = {}
            for sopt, svalue in style_rawoptions.items():
                srealvalue: varSidSettings
                sshowvalue: str
                if svalue in self.styleDynamic:
                    assert isinstance(svalue, model.DStyle)
                    srealvalue = self.styleDynamic[svalue]
                    if __debug__:
                        sshowvalue = f'$({svalue.name}={srealvalue})'
                else:
                    srealvalue = svalue
                    if __debug__:
                        sshowvalue = str(svalue)
                style_options[sopt] = srealvalue
                if __debug__:
                    style_showoptions[sopt] = sshowvalue
            if __debug__:
                logger_styling.debug('- %s: %s', sid, ' '.join('='.join((sopt, svalue)) for sopt, svalue in style_showoptions.items()))
            self.style.configure(sid, **style_options)

    def __setstyle_clear_ro(self, color_readonly__fieldbg: str):
        logger_styling.debug('Clear RO: "%s"', color_readonly__fieldbg)
        color_disabled__fieldbg = self.styleDynamic[model.DStyle.Color_BG]
        combobox_fieldbg_readonly = color_readonly__fieldbg
        combobox_fieldbg_disabled = dict(self.style.map('TCombobox', query_opt='fieldbackground')).get('disabled', color_disabled__fieldbg)
        logger_styling.debug('- TCombobox[fieldbackground]: disabled="%s" readonly="%s"', combobox_fieldbg_disabled, combobox_fieldbg_readonly)
        self.style.map('TCombobox',
                       fieldbackground=[
                           ('disabled', combobox_fieldbg_disabled),
                           ('readonly', combobox_fieldbg_readonly),
                       ],
                       )
        spinbox_fieldbg_readonly = color_readonly__fieldbg
        spinbox_fieldbg_disabled = dict(self.style.map('TSpinbox', query_opt='fieldbackground')).get('disabled', color_disabled__fieldbg)
        logger_styling.debug('-  TSpinbox[fieldbackground]: disabled="%s" readonly="%s"', spinbox_fieldbg_disabled, spinbox_fieldbg_readonly)
        self.style.map('TSpinbox',
                       fieldbackground=[
                           ('disabled', spinbox_fieldbg_disabled),
                           ('readonly', spinbox_fieldbg_readonly),
                       ],
                       )

    def __setstyle_checkbox_ro(self):
        logger_styling.debug('Checkbox RO')
        root_map = self.style.map('.')
        if __debug__:
            checkbox_map = self.style.map('TCheckbutton')
            checkbox_cfg = self.style.configure('TCheckbutton')
            if any(e in checkbox_map or e in checkbox_cfg for e in ('foreground', 'embossed')):
                logger_styling.warn('TCheckbutton: theme widget settings being ignored:: map=%r cfg=%r', checkbox_map, checkbox_cfg)
            if 'embossed' in root_map:
                valid = []
                for mk, mval in root_map['embossed']:
                    if mk == 'disabled':
                        valid.append(str(mval) == '1')
                assert all(valid), f'Weird Embossed Settings: {root_map["embossed"]!r}'
        color_disabled_fg = self.styleDynamic[model.DStyle.Color_FG_Disabled]
        color_normal_fg = self.styleDynamic[model.DStyle.Color_FG]
        # state_rw_enabled = ('!disabled', '!readonly')  # No Changes
        state_ro_enabled = ('disabled', 'readonly')
        state_disabled = ('disabled', '!readonly')       # No ro/rw selection
        self.style.map('TCheckbutton',
                       foreground=[
                           (state_ro_enabled, color_normal_fg),
                           (state_disabled, color_disabled_fg),
                       ],
                       embossed=([
                           (state_ro_enabled, 0),  # No embossing
                           (state_disabled, 1),    # Regular embossing
                       ] if 'embossed' in root_map else []),
                       )

    def setup_images(self, imgfolder: typing.Optional[Path]):
        '''Register all images here.

        This is called before the child widgets are defined.

        Lazy loads all images on production, see `__debug__`.

        Args:
            imgfolder: Folder with images to be loaded (using `setup_images_folder`). Optional.
        '''
        builtins = set()
        for iname in self.image_names():
            if __debug__:
                logger_image.debug('Builtin Image "%s"', iname)
            builtins.add(iname)
        self.images_builtin = tuple(builtins)
        if imgfolder:
            self.setup_images_folder(imgfolder, lazy=not __debug__)

    @lru_cache
    def wimage(self, key: str) -> typing.Optional[tk.Image]:
        '''Get image data by key.

        This function will cache the image object, so no extra Python
        references are needed. The cache will store all used image, avoid
        runaway memory consumption by using enormous amounts of images.

        See Python documentation for `images <https://docs.python.org/3/library/tkinter.html#images>`_.

        Args:
            key: The key to find the image data.

        Returns:
            If the key exists, return the ``tkinter.Image`` object, otherwise
            return `None`.
        '''
        iobj = self.images_cache.get(key)
        if iobj is None:
            if __debug__:
                warnings.warn(f'Missing image: {key}', stacklevel=2)
            return None
        else:
            if not iobj.cached:
                img_function = tk.PhotoImage  # Default Function
                img_kwargs: typing.Dict[str, typing.Any] = {}
                if iobj.dtype and iobj.dtype in model.IMAGE_TYPES:
                    img_function = model.IMAGE_TYPES[iobj.dtype]
                    img_kwargs['format'] = iobj.dtype
                # Load the image
                if iobj.fname:
                    if __debug__:
                        logger_image.debug('Load Image "%s" from file "%s"', key, iobj.fname)
                    iobj.obj = img_function(file=iobj.fname, **img_kwargs)
                elif iobj.data:
                    if __debug__:
                        logger_image.debug('Load Image "%s" from data', key)
                    iobj.obj = img_function(data=iobj.data, **img_kwargs)
                    # TODO: Remove the data copy: `iobj.data = None`
                else:
                    raise ValueError(f'Invalid Cache Metadata for Image {key}')
            return iobj.obj

    def instate(self, statespec: typing.Sequence[str], callback: typing.Optional[typing.Callable] = None) -> typing.Optional[bool]:
        ''''''  # Do not document
        # Not applicable to the root window
        return None

    def state(self, statespec):
        ''''''  # Do not document
        # Not applicable to root window
        raise NotImplementedError

    def get_gui_windowstate(self) -> model.WindowState:
        return model.WindowState(
            fullscreen=bool(self.wm_attributes('-fullscreen') == 1)
        )

    def set_gui_windowstate(self, rgstate: model.WindowState) -> None:
        if rgstate.fullscreen is not None:
            self.wm_attributes('-fullscreen', 1 if rgstate.fullscreen is True else 0)

    rgstate = property(get_gui_windowstate, set_gui_windowstate)
    '''Window State

    See `WindowState`.
    '''

    def gbinding(self, *args, immediate: bool = True, **kwargs) -> model.BindingGlobal:
        '''Create a `model.BindingGlobal` for this application.

        Args:
            immediate: Passed to the upstream object, default to enabling the
                binding on creation. This is the opposite from upstream.

        All arguments are passed to the `model.BindingGlobal` object.
        '''
        return model.BindingGlobal(self, *args, immediate=immediate, **kwargs)

    def register_styleID(self, argument: typing.Optional[str],
                         thisClass: str, *otherClasses: str,
                         ) -> str:
        '''Register a styleID, based on an argument, and the current widget
        style classes.

        The styleID can represent a combination of simpler styles, by using
        ``|`` to separate the corresponding keys.

        Called by each widget type, it must define "thisClass" as mentioned in
        ``Tk`` documentation, a different string for each widget type.
        "otherClasses" are configured the same way, but they do not gate

        See Python docs in :ref:`Ttk Styling <python:ttkstyling>`, see ``Tk``
        :tk:`style <ttk_style.htm>` documentation.

        Args:
            argument: The styleID subclasses, separated by ``|``.
                This is defined by the final GUI designer. Optional.
            thisClass: The class for the current widget.

        Returns:
            An empty string indicates no style is applied, see ``Tk``
            :tk:`widget style argument <ttk_widget.htm#M-style>`
            documentation.
        '''
        # TODO: Turn `argument` type into a string or string tuple: `typing.Optional[typing.Union[str, typing.Tuple[str, ...]]]`
        # TODO: Support validating the style options in `setup_styleID`
        if argument is None:
            return ''  # Equivalent to `None`, no styling is applied
        else:
            for tclass in (thisClass, *otherClasses):
                theseID = set()
                for subclass in argument.split('|'):
                    assert '.' not in subclass, f'Invalid StyleID: "{subclass}"'
                    styleSubID = f'{subclass}.{tclass}'
                    theseID.add(styleSubID)
                    if __debug__:
                        if tclass != thisClass:
                            self.__styleIDs_other[f'{subclass}.{thisClass}'].add(styleSubID)
                self._styleIDs |= theseID  # .update()
                if len(theseID) > 1:
                    self._styleComplex[f'{argument}.{tclass}'] = tuple(theseID)
            return f'{argument}.{thisClass}'

    def setup_image_data(self, key: str, data: bytes, dtype: str, *, cache_clear: bool = True, lazy: bool = True) -> None:
        '''Register a single image, from arbitrary data.

        This is useful to avoid external image files and hardcode all image
        data on the binary itself.

        The data can be given as a base64 byte string. This can be computed
        from a file ``$IMAGE`` using the following command

        .. code:: shell

            base64 --wrap=0 <"$IMAGE"

        By default, the image data itself is lazy loaded, that is, only read
        from the files as the images are requested, controlled by the ``lazy``
        parameter.

        Args:
            key: The key to store the image under
            data: The image data, as bytes.
            dtype: The image format. Only `tkinter` supported images.

            cache_clear: Clear the image cache after register these new image.
                Default to `True`.
            lazy: Lazy load image data, on demand as the image is requested.
                Default to `True`.

        See Also:
            - `setup_images_folder`: Register several images from a folder.
            - `wimage`: Get the loaded image data.
        '''
        if key in self.images_cache:
            raise exception.InvalidImageKey(key)
        if dtype not in model.IMAGE_TYPES:
            raise exception.InvalidImageType(dtype)
        if __debug__:
            logger_image.debug('Register %s Image "%s"', dtype.upper(), key)
        self.images_cache[key] = model.ImageCache(data=data, dtype=dtype)
        if cache_clear:
            self.wimage.cache_clear()
        if not lazy:
            self.wimage(key)

    # TODO: Accept multiple formats (`model.IMAGE_TYPES`), by that order (first wins)
    def setup_images_folder(self, folder: Path, *, cache_clear: bool = True, lazy: bool = True) -> None:
        '''Register all supported images from a folder.

        Registers all supported images on the given folder, does not recurse
        into subfolders. Unsupported file extensions are skipped.

        The key for finding the images is the file name, without the last
        extension. Multiple images with the same key and different extensions
        are unsupported.

        By default, the image data itself is lazy loaded, that is, only read
        from the files as the images are requested. This can be worked around
        by setting ``lazy`` to ``False``, to immediately load all the image
        data. This is mostly useful to detect errors as soon as possible,
        mostly for debug purposes.

        Args:
            folder: The source folder. Optional.
            cache_clear: Clear the image cache after register these new images.
                Default to `True`.
            lazy: Lazy load image data, on demand as the images are requested.
                Default to `True`.

        See Also:
            - `setup_image_data`: Register a single image from raw data.
            - `wimage`: Get the loaded image data.
        '''
        if not folder.is_dir():
            raise ValueError(f'Invalid Folder: {folder}')
        new_images: typing.Optional[typing.Set[str]] = None if lazy else set()
        for imgfile in folder.iterdir():
            imgext = imgfile.suffix
            dtype = None if imgext == '' else imgext[1:].lower()
            if imgfile.is_file() and dtype in model.IMAGE_TYPES:
                imgkey = imgfile.stem
                if __debug__:
                    logger_image.debug('Register %s Image "%s": "%s"', dtype.upper(), imgkey, imgfile)
                if imgkey in self.images_cache:
                    raise exception.InvalidImageKey(imgkey)
                if dtype not in model.IMAGE_TYPES:
                    raise exception.InvalidImageType(dtype)
                self.images_cache[imgkey] = model.ImageCache(fname=imgfile, dtype=dtype)
                if new_images is not None:
                    new_images.add(imgkey)
        if cache_clear:
            self.wimage.cache_clear()
        if new_images is not None:
            logger_image.debug('Load %d Images', len(new_images))
            for image in new_images:
                self.wimage(image)

    def setup_eventloops(self) -> typing.Optional[typing.Mapping[str, bg.EventLoop]]:
        '''Define the application `Event Loops <EventLoop>`.

        Runs after `setup_defaults <ContainerWidget.setup_defaults>`, so all
        child widgets should be ready.

        Returns:
            Return a :py:class:`dict` mapping friendly names and objects. See `eL`.
            Optional, is this returns `None`, an empty mapping is stored.

        See Also:
            See `use_eventbus` to configure an Event Bus for the `Event Loop
            <EventLoop>`.

            See `start_eventloops` for a simple way to start the event loops.
            Make sure this is done later.
        '''
        return {}

    def get_eventloops(self, *,
                       bus: typing.Optional[bool] = None,
                       ) -> typing.Iterator[typing.Tuple[str, bg.EventLoop]]:
        '''Get all `Event Loops <EventLoop>` objects, with possible filters.

        Arguments:
            bus: Consider the `EventLoop` configured for Event Bus (see `use_eventbus`).

                - If `True`, only configured are included.
                - If `False`, only not configured are included.
                - If `None`, all are included.

                Defaults to `None`.
        '''
        for elID, el in self.eL.items():
            wcallback = el.wcallback
            use_eventbus = wcallback is not None and wcallback.callback == self.use_eventbus
            doit: bool = True if bus is None else bus == use_eventbus
            # if __debug__:
            #     logger.debug('%s "%s" bus=%s',
            #                  'Including' if doit else ' Skipping',
            #                  elID,
            #                  use_eventbus,
            #                  )
            if doit:
                yield elID, el

    def start_eventloops(self, **kwargs) -> None:
        '''Start all `Event Loops <EventLoop>`, with possible filters.

        Starting the `EventLoop` threads should be done on `setup_adefaults
        <ContainerWidget.setup_adefaults>` or later. This is verified.

        Arguments:
            kwargs: All arguments are passed to `get_eventloops`, for
                filtering.

        See Also:
            Use `get_eventloops` to filter all `Event Loops <EventLoop>`.
        '''
        if not self.__event_bus_processed:
            raise exception.EventLoopConcurrencyError('EventLoops started too soon')
        for elID, el in self.get_eventloops(**kwargs):
            if __debug__:
                logger.debug('Starting "%s" tName=%r', elID, el.tName)
            el.start()

    def eventloop_queue(self,
                        eventloop: str,
                        task: typing.Union[typing.Type[bg.ELReq], bg.ELReq],
                        priority: typing.Optional[int] = None,
                        ) -> None:
        '''Queue a task on the given `EventLoop`.

        Arguments:
            eventloop: The `EventLoop` friendly name. See `eL`.
            task: Task to queue, or a simplified class to instance.
            priority: Task priority, Optional.

        See Also:
            See the upstream `queue <bg.EventLoop.queue>` function
            documentation.
        '''
        if eventloop not in self.eL:
            raise ValueError(f'Undefined EventLoop: "{eventloop}"')
        if isinstance(task, type):
            # Create a new simple instances
            # TODO: Use a single instance only? A kind of Singleton?
            task_object = task()
        else:
            assert isinstance(task, bg.ELReq)
            task_object = task
        self.eL[eventloop].queue(task_object, priority=priority)

    # TODO: Suport inserting in a specific location? Only start/end
    def register_eventbus_response(self, callback: bg.callbackT, *,
                                   eventloop: typing.Optional[str] = None,
                                   event: typing.Union[
                                       varEventBusEventType,
                                       typing.Sequence[varEventBusEventType],
                                   ] = None,
                                   ) -> None:
        '''Register an Event Bus callback, optionally filtering by `Event Loop
        <EventLoop>`, and one or more event types.

        Register the given ``callback`` on the Event Bus, to be called when an
        event appears on a configured `Event Loop <EventLoop>`.
        Each response can be registered with multiple overlapping callbacks.

        This must be called before the Event Bus is processed for runtime
        usage, it's not a dynamic registration. Make sure to call this from
        `setup_defaults <ContainerWidget.setup_defaults>`.

        To filter the `Event Loop <EventLoop>` where this applies use the
        ``eventloop`` argument.
        To filter the event type where this applies use the ``event``
        arguments. See below for more information on how this is supported.

        Arguments:
            callback: The callback to register. See the `bg.ELCallback`
                ``callback`` definition for the function requirements.
            eventloop: Filter by `EventLoop`, given as a `str` (key for `eL`).
                Optional, when `None`, runs for all available `EventLoop`.
            event: Filter by event type.
                Can be given as any of the following types:

                - `bg.ELRes` subclass, to filter only those response types
                - `bool` to filter only `EventLoop` signals
                - `None`, to run for all events and signals

                A sequence of any combination of the previous types is also
                accepted, equivalent to calling the function for each type.
                Mixing `None` and any other type in a sequence is an error.

        .. note::

            There is a limitation on how the `Event type <bg.ELRes>` is
            processed, subclasses are not supported.
            That is, when you subscribe to an event type, subclasses of that
            event type are not considered.
            They can be registered manually if needed.

            Avoid mixin `Event type <bg.ELRes>` subclassing and Event Bus.

        See Also:

            Configure the `EventLoop` on `setup_eventloops`, and
            `use_eventbus`.
        '''
        events = set(event) if isinstance(event, typing.Sequence) else set([event])
        if len(events) > 1 and None in events:
            raise ValueError('Do not mix `None` and other response types')
        if __debug__:
            event_str = '|'.join(
                '"ALL"' if sevent is None else '"SIGNAL"' if sevent is bool else sevent.__qualname__
                for sevent in events
            )
            logger_eventbus.debug('Register callback `%s` for eventloop=%s event=%s',
                                  callback.__qualname__,
                                  '"ALL"' if eventloop is None else eventloop,
                                  event_str,
                                  )
        if self.__event_bus_processed:
            raise exception.EventBusRegisterError('Event Bus Registration too late')
        # Implement "defaultdict"
        if eventloop not in self.__event_bus:
            if __debug__:
                logger_eventbus.debug('* New EventLoop @ Event Bus registration: %s', eventloop)
            self.__event_bus[eventloop] = defaultdict(list)
        # Register callbacks
        for sevent in events:
            callback_list = self.__event_bus[eventloop][sevent]
            callback_list.append(callback)

    def process_event_bus(self) -> None:
        '''Post-Process EventBus registrations.

        This runs after `setup_eventloops`. Validates all EventBus registration
        calls are valid, aggregates "ALL" `EventLoop` registrations, and uses
        the `EventLoop` object as dictionary key, instead of a simple string.
        This greatly improves performance on the EventBus implementation, and
        validates errors as soon as possible.

        Most deep validations are only done on debug mode, for performance
        reasons.
        '''
        if self.__event_bus_processed:
            raise exception.EventLoopConcurrencyError('EventLoops processed several times')
        logger_eventbus.debug('Processing Event Bus...')
        elEventsCommon = self.__event_bus.pop(None, {})
        count_common = len(elEventsCommon)
        elRegisteredIDs = set(typing.cast(typing.Iterable[str], self.__event_bus.keys()))
        if __debug__:
            for elStringId in elRegisteredIDs:
                assert isinstance(elStringId, str), f'Invalid EventLoop {elStringId!r} @ EventBus: Use keys from `self.eL`'
            unknown_elID = elRegisteredIDs - set(self.eL)
            if len(unknown_elID) > 0:
                unknown_elID_str = ' '.join(typing.cast(typing.Iterable[str], unknown_elID))
                assert len(unknown_elID) > 0, f'Undefined EventLoop @ EventBus: {unknown_elID_str}'
        if count_common > 0:
            logger_eventbus.debug('* eventloop="ALL": %d common events', count_common)
            # Make sure all eventloops are defined
            for elStringId in set(self.eL) - elRegisteredIDs:
                assert isinstance(elStringId, str)
                wcallback = self.eL[elStringId].wcallback
                # Check needs Python3.8: https://github.com/python/cpython/issues/44345
                if wcallback is not None and wcallback.callback == self.use_eventbus:
                    logger_eventbus.debug('  * eventloop=%s: register, uses Event Bus', elStringId)
                    # Implement "defaultdict"
                    self.__event_bus[elStringId] = defaultdict(list)
                else:
                    logger_eventbus.debug('  * eventloop=%s: skipping, no `use_eventbus`', elStringId)
        elProcessedIDs = set()
        for elID, elEvents in self.__event_bus.items():
            assert elID is not None
            assert isinstance(elID, str)
            count_specific = len(elEvents)
            count_all = count_common + count_specific
            logger_eventbus.debug('- eventloop=%s: events common=%d specific=%d', elID, count_common, count_specific)
            if elID not in self.eL:
                if __debug__:
                    if not self.eL_strict:
                        logger_eventbus.warning('EventLoop %r: not setup, skipping %d registered events', elID, count_specific)
                continue
            elProcessedIDs.add(elID)
            assert count_all > 0
            wcallback = self.eL[elID].wcallback
            # Check needs Python3.8: https://github.com/python/cpython/issues/44345
            assert wcallback is not None and wcallback.callback == self.use_eventbus
            elEventsIDs = set((*elEvents, *elEventsCommon))
            for event in elEventsIDs:
                specific_callbacks = elEvents.get(event, [])
                common_callbacks = elEventsCommon.get(event, [])
                logger_eventbus.debug('  - event=%s: callbacks common=%d specific=%d',
                                      '"ALL"' if event is None else '"SIGNAL"' if event is bool else event.__qualname__,
                                      len(common_callbacks), len(specific_callbacks))
                # TODO: Suport inserting in a specific location?
                elEvents[event].extend(common_callbacks)
                assert self.use_eventbus not in elEvents[event]  # Avoid infinite loops
            if __debug__:
                count_actual = sum(len(callbacks) for callbacks in elEvents.values())
                assert count_actual == count_all, f'eventloop={elID} event={event}: unmatched count actual={count_actual} spec={count_all}'
        if __debug__:
            elMissingIDs = elRegisteredIDs - elProcessedIDs
            if self.eL_strict and len(elMissingIDs) > 0:
                logger.critical('Event Bus Registration of missing EventLoop:')
                for elID in elMissingIDs:
                    logger.critical('- %s: %d events', elID, len(self.__event_bus[elID]))
                sys.exit(100)
        for elID in elRegisteredIDs:
            assert isinstance(elID, str)
            if elID in elProcessedIDs:
                assert elID in self.__event_bus
                assert elID != self.eL[elID]
                self.__event_bus[self.eL[elID]] = self.__event_bus.pop(elID)
            else:
                assert elID in self.__event_bus
                self.__event_bus.pop(elID)
                assert elID not in self.__event_bus
        assert all(isinstance(el, bg.EventLoop) for el in self.__event_bus)
        logger_eventbus.debug('Processed Event Bus! #%d', len(elProcessedIDs))
        self.__event_bus_processed = True

    def use_eventbus(self,
                     eventloop: bg.EventLoop,
                     ridx: typing.Optional[int],
                     response: typing.Union[bool, bg.ELRes]
                     ) -> None:
        '''Configure the `EventLoop` to use an Event Bus.

        Attach this function to the ``wcallback`` ``EventBus`` configuration to
        use a managed Event Bus.

        This is a fully managed Event Bus, configured using
        `register_eventbus_response`.

        This is very useful for async communication with a background thread:
        Each widget in the tree can add events to an `EventLoop` and register
        callback functions for processing the returning events, without
        cluttering the `RootWindow` with a large forwarding helper function.

        Arguments:
            All arguments are the same as `ELCallback <bg.ELCallback>`
            ``callback`` defintion.

        .. note::

            If the `EventLoop` is not configured with this ``wcallback``
            function, it is considered unmanaged.

        See Also:

            Configure the `EventLoop` on `setup_eventloops`. Register callbacks
            with `register_eventbus_response`.
        '''
        assert eventloop in self.__event_bus, f'Weird EventLoop @ EventBus: {eventloop}'
        assert eventloop.wcallback is not None and eventloop.wcallback.callback == self.use_eventbus
        bus = self.__event_bus[eventloop]
        response_type = type(response)
        functions = [*bus.get(None, []), *bus.get(response_type, [])]
        if __debug__:
            if ridx is None:
                assert response_type is bool
            count_common, count_specific = len(bus.get(None, [])), len(bus.get(response_type, []))
            if len(functions) == 1:
                logger_eventbus.debug('eventloop=%s event=%s: Trigger `%s`',
                                      eventloop.tName,
                                      '"SIGNAL"' if response_type is bool else response_type.__qualname__,
                                      functions[0].__qualname__)
            else:
                logger_eventbus.debug('eventloop=%s event=%s: common=%d specific=%d',
                                      eventloop.tName,
                                      '"SIGNAL"' if response_type is bool else response_type.__qualname__,
                                      count_common, count_specific)
        if len(functions) == 0:
            logger_eventbus.warning('eventloop=%s event=%s: Unprocessed: ridx=%s response=%r',
                                    eventloop.tName,
                                    '"SIGNAL"' if response_type is bool else response_type.__qualname__,
                                    ridx, response)
        for function in functions:
            if __debug__:
                if len(functions) != 1:
                    logger_eventbus.debug('- Trigger `%s`', function.__qualname__)
            function(eventloop, ridx, response)


class FrameUnlabelled(ttk.Frame, mixin.ContainerWidget):
    '''A simple frame to hold other widgets, visually invisible.

    This is the simplest form of `mixin.ContainerWidget`, just a bunch of
    widgets. There's no separation between the outside and the inside of the
    frame.

    There is no Python documentation, see ``Tk`` :tk:`ttk.Frame
    <ttk_frame.htm>` documentation.

    Args:
        styleID: Set a style identifier. Combined with the widget type in `RootWindow.register_styleID`.
        parent: The parent widget. Can be a `RootWindow` or another `mixin.ContainerWidget`.

    See Also:
        `FrameLabelled`: Visible version, with a label.
    '''
    def __init__(self, parent: mixin.ContainerWidget, *args,
                 styleID: typing.Optional[str] = None,
                 **kwargs):
        assert isinstance(parent, tk.Misc), f'{parent} is not a valid parent widget'
        super().__init__(parent,
                         style=parent.wroot.register_styleID(styleID, 'TFrame'),
                         )  # ttk.Frame
        self.init_container(*args, **kwargs)


class FrameLabelled(ttk.LabelFrame, mixin.ContainerWidget):
    '''A frame to hold other widgets surrounded by a line, including a label.

    This is a frame with a label. It is visually separated from the other
    widgets. You can control the label position.

    There is no Python documentation, see ``Tk`` :tk:`ttk.LabelFrame
    <ttk_labelframe.htm>` documentation.

    Args:
        label: The label to include on the frame separator. Can be given as a class variable.
        labelAnchor: The position of the label on the frame separator.
            Given as one of the cardinal points.
            Defaults to a OS-specific location (`model.CP.default`).

        styleID: Set a style identifier. Combined with the widget type in
            `RootWindow.register_styleID`.
        parent: The parent widget. Can be a `RootWindow` or another
            `mixin.ContainerWidget`.

    See Also:
        `FrameUnlabelled`: Invisible version, without a label.

        `FrameStateful`: Support for an embedded `Checkbox` as label.

        `FrameRadio`: Support for an embedded `Radio` as label.
    '''
    label: typing.Optional[str] = None

    def __init__(self, parent: mixin.ContainerWidget, *args,
                 label: typing.Optional[str] = None,
                 labelAnchor: model.CP = model.CP.default,
                 styleID: typing.Optional[str] = None,
                 **kwargs):
        chosen_label = fn.label_fallback(label, self.label)
        if chosen_label is None:
            raise exception.InvalidWidgetDefinition('Missing required label')
        # TODO: Improve labelAnchor object
        assert isinstance(parent, tk.Misc), f'{parent} is not a valid parent widget'
        super().__init__(parent, text=chosen_label, labelanchor=labelAnchor.value,
                         style=parent.wroot.register_styleID(styleID, 'TLabelframe', 'TLabelframe.Label'),
                         )  # ttk.LabelFrame
        if __debug__:
            if 'labelwidget' in kwargs:
                warnings.warn(f'{self}: Unsupported "labelwidget"', stacklevel=2)
        kwargs.pop('labelwidget', None)  # Unsupported
        self.init_container(*args, **kwargs)

    @property
    def wlabel(self) -> str:
        '''Calculate the chosen label text.'''
        chosen_label = self['text']
        assert isinstance(chosen_label, str), f'{self}: Invalid label: {chosen_label!r}'
        return chosen_label


class Label(ttk.Label, mixin.SingleWidget):
    '''A label, can be text, image, or both.

    This is a label, a static-ish widget without interaction.

    This must include at least some text or an image, even though both are optional.

    No state is included.

    There is no Python documentation, see ``Tk`` :tk:`ttk.Label <ttk_label.htm>` documentation.

    Args:
        label: The text to show. Optional. Can be given as a class variable.
        anchor: Align the text inside the widget. See below for how the default is calculated.
        justify: The text justification. See below for how the default is calculated.
        labelPosition: Label position, how to combine label and image.
            See `model.CP_Compound` for the possible values.
        image: The image to show. Optional.
            See ``Tk`` :tk:`tk.Image <image.htm>` documentation.
        expand: Grow the widget to match the container grid size, horizontally.
            See below for how the default is calculated.

        styleID: Set a style identifier. Combined with the widget type in
            `RootWindow.register_styleID`.
        parent: The parent widget. Can be a `RootWindow` or another
            `mixin.ContainerWidget`.

    .. note::

        There are at least 4 align options that might interact in weird ways.

        ``labelPosition`` only concerns how the label and image are aligned.
        This only matters when both are included.

        If only the image is included, ``expand`` defaults to `False`.

        If the label exists, the other 3 options govern its alignment.

        If the label has a single line, the default ``expand`` value depends if
        ``justify`` is given and not `model.Justification.NoJustify`. The
        default is not expanding, but if there's a non-default justification,
        ``expands`` defaults to `True` (otherwise it would have no effect).
        If ``expand`` is `True`, the ``justify`` value is used to calculate the
        ``anchor`` value, and the "real" ``justify`` value defaults to
        `model.Justification.Center`.

        If the label has multiple lines, ``expand`` defaults to `False`,
        ``justify`` defaults to `model.Justification.Center` and ``anchor``
        defaults to `model.CP.center`.

        **In a nutshell**, if the label has a single line, set ``justify``
        only. If it has multiple lines, set both ``align`` and ``justify``.
        The image and ``labelPosition`` options are orthogonal, they do not
        interact with the text alignment.
    '''
    label: typing.Optional[str] = None
    state_type = var.nothing

    def __init__(self, parent: mixin.ContainerWidget, *,
                 label: typing.Optional[str] = None,
                 anchor: typing.Optional[model.CP] = None,
                 justify: typing.Optional[model.Justification] = None,
                 labelPosition: model.compoundT = model.CP.E,
                 image: typing.Optional[tk.Image] = None,
                 expand: typing.Optional[bool] = None,
                 styleID: typing.Optional[str] = None,
                 **kwargs):
        chosen_label = fn.label_fallback(label, self.label)
        if chosen_label is None and image is None:
            raise exception.InvalidWidgetDefinition('Missing an image or a label')
        self.init_single(vspec=None)  # No state here
        if chosen_label is not None:
            if '\n' in chosen_label:
                # Multi-Line Label
                expand = True if expand is None else expand
                justify = justify or model.Justification.Center
                anchor = anchor or model.CP.center
            else:
                # Single Line Label
                if expand is None:
                    expand = justify is not None and justify is not model.Justification.NoJustify
                justify = justify or model.Justification.Center
                if expand:
                    # - Adjust anchor to mimic justification
                    anchor = anchor or model.Justification_CP[justify]
                else:
                    anchor = anchor or model.CP.center
            assert anchor is not None
            assert justify is not None
            kwargs.update({
                'justify': justify.value,  # TODO: Move to `Style`?
                'anchor': anchor.value,  # TODO: Move to `Style`?
            })
        else:
            expand = False if expand is None else expand
        assert expand is not None
        kwargs.update({
            'image': image or '',
            'text': chosen_label or '',
            'compound': model.CP_Compound[labelPosition],
            'style': parent.wroot.register_styleID(styleID, 'TLabel'),
        })
        assert isinstance(parent, tk.Misc), f'{parent} is not a valid parent widget'
        super().__init__(parent, **kwargs)  # ttk.Label
        if expand:
            self.grid(sticky=tk.NSEW)
        if __debug__:
            if 'textvariable' in kwargs:
                warnings.warn(f'{self}: To use a variable as label, see LabelStateful', stacklevel=2)
                # TODO: Enforce this, using `assert`?

    @property
    def wlabel(self) -> str:
        '''Calculate the chosen label text.'''
        chosen_label = self['text']
        assert isinstance(chosen_label, str), f'{self}: Invalid label: {chosen_label!r}'
        return chosen_label

    def change(self,
               label: typing.Optional[str] = None,
               image: typing.Optional[tk.Image] = None,
               ) -> None:
        '''Change cosmetic aspects of the label.

        The label text must remain in the same "shape": Single or
        Multiline strings are supported, but cannot be changed at runtime
        between them.

        The label image must remain in the same "shape": Labels without image
        cannot get a new one, and Labels with image cannot lose its image.
        The image size (``width`` and ``height``) should also remain the same,
        but this is not enforced.

        Arguments:
            label: The new text to show. Optional.
            image: The new image to show. Optional.

        .. note:: These are the same parameters as the constructor for `Label`.
        '''
        if label is not None:
            assert ('\n' in label) == ('\n' in self['text']), f'{self}: Cannot change the nature of the Label: Moved between single and multi lines'
            self['text'] = label
        if image is not None:
            if __debug__:
                assert self['image'] != '', f'{self}: Cannot change the nature of the Label: New image'
            self['image'] = image

    def set_label(self, label: str) -> None:
        '''DEPRECATED. See `change` with ``label``.'''  # TODO: Remove in v0.50
        logger.warning('%s: Deprected. Use `self.change` instead', self)
        return self.change(label=label)

    def set_image(self, image: typing.Optional[tk.Image]) -> None:
        '''DEPRECATED. See `change` with ``image``.'''  # TODO: Remove in v0.50
        logger.warning('%s: Deprected. Use `self.change` instead', self)
        return self.change(image=image)


class LabelStateful(ttk.Label, mixin.SingleWidget):
    '''A stateful `Label`, where the text is controlled by a variable.

    This is an alternative `Label`, where the text is controlled by a variable.
    It's an alternative to manually calling `Label.change`, or a read-only
    `EntryRaw`.

    There is no Python documentation, see ``Tk`` :tk:`ttk.Label
    <ttk_label.htm>` documentation.

    Args:
        variable: Use an externally defined variable, instead of creating a new
            one specific for this widget.
        anchor: Align the text inside the widget. Optional.
        justify: The text justification. Optional.
        labelPosition: Label position, how to combine label and image.
            See `model.CP_Compound` for the possible values.
        image: The image to show. Optional.
            See ``Tk`` :tk:`tk.Image <image.htm>` documentation.
        expand: Grow the widget to match the container grid size, horizontally.
            Defaults to `False`.

        styleID: Set a style identifier. Combined with the widget type in
            `RootWindow.register_styleID`.
        parent: The parent widget. Can be a `RootWindow` or another
            `mixin.ContainerWidget`.
    '''
    state_type = var.String

    def __init__(self, parent: mixin.ContainerWidget, *,
                 variable: typing.Optional[var.String] = None,
                 anchor: typing.Optional[model.CP] = None,
                 justify: typing.Optional[model.Justification] = None,
                 labelPosition: model.compoundT = model.CP.E,
                 image: typing.Optional[tk.Image] = None,
                 expand: bool = False,
                 styleID: typing.Optional[str] = None,
                 **kwargs):
        self.init_single(variable)
        kwargs.update({
            'image': image or '',
            'textvariable': self.variable,
            'compound': model.CP_Compound[labelPosition],
            'style': parent.wroot.register_styleID(styleID, 'TLabel'),
        })
        if justify is not None:
            kwargs['justify'] = justify.value
        if anchor is not None:
            kwargs['anchor'] = anchor.value
        if __debug__:
            if 'text' in kwargs:
                warnings.warn('To use static text on a label, see Label', stacklevel=2)
        kwargs.pop('text', None)  # Ignore the given text
        assert isinstance(parent, tk.Misc), f'{parent} is not a valid parent widget'
        super().__init__(parent, **kwargs)  # ttk.Label
        if expand:
            self.grid(sticky=tk.NSEW)

    def change(self,
               label: typing.Optional[str] = None,
               image: typing.Optional[tk.Image] = None,
               anchor: typing.Optional[model.CP] = None,
               justify: typing.Optional[model.Justification] = None,
               ) -> None:
        '''Change "cosmetic" aspects of the label.

        The label text is technically not a cosmetic aspect, but it is provided
        here for compatibility with `Label.change`.

        The label image must remain in the same "shape": LabelStateful without
        image cannot get a new one, and LabelStateful with image cannot lose
        its image.
        The image size (``width`` and ``height``) should also remain the same,
        but this is not enforced.

        Arguments:
            label: The new text to show. Optional.
            image: The new image to show. Optional.
            anchor: The new anchor setting. Optional.
            justify: The new justification setting. Optional.

        .. note:: These are the same parameters as the constructor for
            `LabelStateful`.
        '''
        if label is not None:
            assert self.variable is not None, f'{self!r}: Missing variable'
            self.variable.set(label)
        if image is not None:
            if __debug__:
                assert self['image'] != '', f'{self}: Cannot change the nature of the Label: New image'
            self['image'] = image
        if justify is not None:
            self['justify'] = justify.value
        if anchor is not None:
            self['anchor'] = anchor.value


class Button(ttk.Button, mixin.SingleWidget):
    '''A button with a label and/or an image.

    This is a button, with a label and/or an image. The main interaction is being clicked on.

    No state is included.

    There is no Python documentation, see ``Tk`` :tk:`ttk.Button
    <ttk_button.htm>` documentation.

    Args:
        label: The label to include inside the button. Optional.
            Can be given as a class variable.
        labelPosition: Label position, how to combine label and image.
            See `model.CP_Compound` for the possible values.
        image: The image to show. Optional.
            See ``Tk`` :tk:`tk.Image <image.htm>` documentation.
        width: The button width, in pixels.
            Defaults to an ad-hoc calculation based on the length of the label.

        styleID: Set a style identifier. Combined with the widget type in `RootWindow.register_styleID`.
        parent: The parent widget. Can be a `RootWindow` or another `mixin.ContainerWidget`.
    '''
    label: typing.Optional[str] = None
    state_type = var.nothing

    def __init__(self, parent: mixin.ContainerWidget, *,
                 label: typing.Optional[str] = None,
                 labelPosition: model.compoundT = model.CP.E,
                 image: typing.Optional[tk.Image] = None,
                 width: typing.Optional[int] = None,
                 styleID: typing.Optional[str] = None,
                 **kwargs):
        chosen_label = fn.label_fallback(label, self.label)
        if chosen_label is None:
            raise exception.InvalidWidgetDefinition('Missing required label')
        self.init_single(vspec=None)  # No state here
        assert isinstance(chosen_label, str)
        if labelPosition not in model.CP_Compound:
            raise exception.InvalidWidgetDefinition(f'Invalid "labelPosition": {labelPosition}')
        kwargs.update({
            'text': chosen_label,
            'width': width or fn.label_size(len(label or 'M')),
            'command': self.invoke_onClick,
            'image': image or '',
            'compound': model.CP_Compound[labelPosition],
            'style': parent.wroot.register_styleID(styleID, 'TButton'),
        })
        assert isinstance(parent, tk.Misc), f'{parent} is not a valid parent widget'
        super().__init__(parent, **kwargs)  # ttk.Button

    @property
    def wlabel(self) -> str:
        '''Calculate the chosen label text.'''
        chosen_label = self['text']
        assert isinstance(chosen_label, str), f'{self}: Invalid label: {chosen_label!r}'
        return chosen_label

    def change(self,
               label: typing.Optional[str] = None,
               image: typing.Optional[tk.Image] = None,
               ) -> None:
        '''Change cosmetic aspects of the button.

        Changing the button text changes the button width too, using the same
        ad-hoc calculation as the widget creation.
        Be advised this text is not stored anywhere, it's calculation must be
        completely deterministic.

        The button image must remain in the same "shape": Buttons without image
        cannot get a new one, and Buttons with image cannot lose its image.
        The image size (``width`` and ``height``) should also remain the same,
        but this is not enforced.

        Arguments:
            label: The new text to show. Optional.
            image: The new image to show. Optional.

        .. note:: These are the same parameters as the constructor for `Button`.
        '''
        if label is not None:
            # Make sure this is actually the same as `__init__`
            self.configure(
                text=label,
                width=fn.label_size(len(label)),
            )
        if image is not None:
            if __debug__:
                assert self['image'] != '', f'{self}: Cannot change the nature of the Button: New image'
            self['image'] = image or ''

    def set_label(self, label: str) -> None:
        '''DEPRECATED. See `change` with ``label``.'''  # TODO: Remove in v0.50
        logger.warning('%s: Deprected. Use `self.change` instead', self)
        return self.change(label=label)

    def set_image(self, image: typing.Optional[tk.Image]) -> None:
        '''DEPRECATED. See `change` with ``image``.'''  # TODO: Remove in v0.50
        logger.warning('%s: Deprected. Use `self.change` instead', self)
        return self.change(image=image)

    def bindClick(self, action: typing.Callable, **kwargs):
        '''Create a binding to be called when clicking this widget.

        This is similar to a `trace <MixinTraces.trace>`.

        Args:
            action: The function to be called when clicking the widget.

        All other arguments are passed to the ``action`` function.

        See Also:
            See `onClick` for an alternative to this.
        '''
        if __debug__:
            if getattr(self.onClick, '__func__', self.onClick) != Button.onClick:
                warnings.warn(f'{self}: Overriding existing `onClick` function', stacklevel=2)
        self.configure(command=lambda: action(**kwargs))

    def invoke_onClick(self):
        ''''''  # Internal, do not document
        self.onClick()

    def onClick(self):
        """Callback to be called when clicking this widget.

        Defaults to doing nothing.

        Available for subclass redefinition.

        See Also:
            See `bindClick` for an alternative to configure this.
        """
        pass


class Checkbox(ttk.Checkbutton, mixin.SingleWidget):
    '''A checkbox, simple boolean choice.

    This is a checkbox with a label. The main interaction is being clicked on,
    which toggles its value.
    Technically, the ``alternate`` GUI state allows for a trinary choice, but
    this is not directly supported as regular state.

    The state is a single `bool` value.

    There is no Python documentation, see ``Tk`` :tk:`ttk.Checkbutton
    <ttk_checkbutton.htm>` documentation.

    Args:
        label: The label to include besides the checkbox. Can be given as a class variable.
            It is included on the right side of the checkbox.
        readonly: Should the widget allow interaction to toggle its value.
            Default to *allowing* interaction.

        styleID: Set a style identifier. Combined with the widget type in `RootWindow.register_styleID`.
        parent: The parent widget. Can be a `RootWindow` or another `mixin.ContainerWidget`.
        variable: Use an externally defined variable, instead of creating a new one specific for this widget.

    .. note::

        The upstream widget does not disable user interaction when ``readonly``
        GUI state is enabled.

        This is worked around when the ``readonly`` argument is used, but this
        is not a dynamic setting like the GUI state.
        The "true" ``enabled`` state is tracked on the ``readonly`` state. This
        only matters for advanced styling uses, `gstate <MixinWidget.gstate>`
        returns the correct values.

        Uses a custom GUI state object, see `GuiState <Checkbox.GuiState>`.

    See Also:
        `CheckboxFrame` for multiple checkboxen managed at once.
    '''
    label: typing.Optional[str] = None
    state_type = var.Boolean

    class GuiState(model.GuiState):
        '''Custom `GuiState <model.GuiState>` for `Checkbox`.

        Since the ``readonly`` argument changes the semantics for the GUI
        state, in those cases the returned object uses this `GuiState
        <model.GuiState>` subclass.
        '''
        def real(self) -> model.GuiState:
            '''Return the underlying "real" `GuiState <model.GuiState>`.

            This is the state that matters for the Tk capabilites, like style
            mappings.
            '''
            # Reverse the change on `get_gui_state`/`set_gui_state`
            newstate = model.GuiState.new(self)
            newstate.enabled = False
            newstate.readonly = self.enabled
            return newstate

    def __init__(self, parent: mixin.ContainerWidget, *,
                 label: typing.Optional[str] = None,
                 readonly: bool = False,
                 variable: typing.Optional[var.Boolean] = None,
                 styleID: typing.Optional[str] = None,
                 **kwargs):
        self.__readonly: bool = readonly
        chosen_label = fn.label_fallback(label, self.label)
        if chosen_label is None:
            raise exception.InvalidWidgetDefinition('Missing required label')
        self.init_single(variable, gkeys=['readonly', 'alternate'])
        assert isinstance(chosen_label, str)
        kwargs.update({
            'text': chosen_label,
            'onvalue': True,
            'offvalue': False,
            'variable': self.variable,
            'style': parent.wroot.register_styleID(styleID, 'TCheckbutton'),
        })
        assert isinstance(parent, tk.Misc), f'{parent} is not a valid parent widget'
        super().__init__(parent, **kwargs)  # ttk.Checkbutton
        if readonly:
            # Trigger the readonly state adjustment
            if __debug__:
                assert self.__readonly is True  # Check that "Enabled by default" is correct
                self.__readonly = False
                assert self.get_gui_state().enabled is True
                self.__readonly = True
            self.set_gui_state(enabled=True)  # Enabled by default

    def get_gui_state(self) -> model.GuiState:
        ''''''  # Internal, do not document
        # Wrap `mixin.MixinWidget.get_gui_state`
        state = super().get_gui_state()
        if self.__readonly:
            # Track the "true" enabled state on the readonly option
            newstate = self.__class__.GuiState.new(state)  # New object
            newstate.enabled = state.readonly
            newstate.readonly = True
            if __debug__:
                logger_autostate.debug('%s: Readonly State <%s >%s', self, state, newstate)
            state = newstate
        return state

    def set_gui_state(self, state: typing.Optional[model.GuiState] = None, **kwargs) -> model.GuiState:
        ''''''  # Internal, do not document
        # Wrap `mixin.MixinWidget.set_gui_state`
        if state is None:
            state = model.GuiState(**kwargs)
        # Read-only checkboxen are editable, for some reason
        # Make sure readonly checkboxen are always disabled
        if self.__readonly:
            newstate = self.__class__.GuiState.new(state)  # New object
            # Track the "true" enabled state on the readonly state
            if state.enabled is not None:
                newstate.readonly = state.enabled is True
            # Force disable the widget
            newstate.enabled = False
            if __debug__:
                logger_autostate.debug('%s: Readonly State <%s >%s', self, state, newstate)
            state = newstate
        return super().set_gui_state(state)

    @property
    def wlabel(self) -> str:
        '''Calculate the chosen label text.'''
        chosen_label = self['text']
        assert isinstance(chosen_label, str), f'{self}: Invalid label: {chosen_label!r}'
        return chosen_label

    def toggle(self, _a1: typing.Any = None, _a2: typing.Any = None) -> None:
        '''Switch the variable state to its opposite (`not <not>`).

        Args:
            _a1: Optional, unused. This exists for API compatibility with
                bindings.
            _a2: Optional, unused. This exists for API compatibility with
                traces.
        '''
        self.wstate = not self.wstate


class Radio(ttk.Radiobutton, mixin.SingleWidget):
    '''A radio button, a choice between several options.

    This is a radio button with a label. The main interaction is being clicked
    on, which sets its value. The same variable is shared between several
    widgets, each one contributing a single ``value``. When each widget is
    enabled, the variable is set to that value.

    Unlike other widgets, the variable must be created separately and given. It
    does not make much sense to create a variable to be used in a single radio
    button.

    The state is a single `str` value.

    There is no Python documentation, see ``Tk`` :tk:`ttk.Radiobutton
    <ttk_radiobutton.htm>` documentation.

    Args:
        label: The label to include besides the widget. Can be given as a class variable.
            It is included on the right side of the radio button.
        variable: The shared `specified variable <var.Spec>` attached to this
            widget. **Mandatory**.
        value: The value for this particular widget. Must be specified by the
            ``variable``, this is checked.
            **Mandatory**.

        styleID: Set a style identifier. Combined with the widget type in `RootWindow.register_styleID`.
        parent: The parent widget. Can be a `RootWindow` or another `mixin.ContainerWidget`.
    '''
    label: typing.Optional[str] = None
    state_type = var.Spec

    def __init__(self, parent: mixin.ContainerWidget, variable: var.Spec, *,
                 value: str,
                 label: typing.Optional[str] = None,
                 styleID: typing.Optional[str] = None,
                 **kwargs):
        chosen_label = fn.label_fallback(label, self.label)
        if chosen_label is None:
            raise exception.InvalidWidgetDefinition('Missing required label')
        self.init_single(variable, gkeys=['alternate'])
        assert self.variable is not None and isinstance(self.variable, self.state_type)
        if value not in self.variable:
            raise exception.InvalidWidgetDefinition(f'Value "{value}" outside spec')
        assert isinstance(chosen_label, str)
        kwargs.update({
            'text': chosen_label,
            'value': value,
            'variable': self.variable,
            'style': parent.wroot.register_styleID(styleID, 'TRadiobutton'),
        })
        assert isinstance(parent, tk.Misc), f'{parent} is not a valid parent widget'
        super().__init__(parent, **kwargs)  # ttk.Radiobutton
        if __debug__:
            assert self.variable is not None

    def isSelected(self) -> bool:
        '''Check if this specific widget is selected.

        This is equivalent to checking if the ``variable`` is set to the
        ``value`` chosen for this particular widget.
        '''
        return self.instate(['selected']) is True

    @property
    def wlabel(self) -> str:
        '''Calculate the chosen label text.'''
        chosen_label = self['text']
        assert isinstance(chosen_label, str), f'{self}: Invalid label: {chosen_label!r}'
        return chosen_label


class EntryRaw(ttk.Entry, mixin.SingleWidget):
    '''An entry widget, single-line text editor.

    This is an entry box, a single-line editor for strings. The main
    interaction is editing the text contained within.

    The state is a single `str` value, there is no validation.

    There is no Python documentation, see ``Tk`` :tk:`ttk.Entry
    <ttk_entry.htm>` documentation.

    Args:
        variable: Use an externally defined variable, instead of creating a new
            one specific for this widget.
        readonly: Should the widget allow interaction to toggle its value.
            Default to *allowing* interaction.
        justify: Justify entry text. Defaults to
            `model.Justification.NoJustify`, the upstream default.
        expand: Grow the widget to match the container grid size, horizontally.
            Defaults to `False`.

        label: The label to include besides the entry. **Not implemented yet**.
        styleID: Set a style identifier. Combined with the widget type in
            `RootWindow.register_styleID`.
        parent: The parent widget. Can be a `RootWindow` or another
            `mixin.ContainerWidget`.
    '''
    state_type = var.String

    def __init__(self, parent: mixin.ContainerWidget, *,
                 variable: typing.Optional[var.String] = None,
                 readonly: bool = False,
                 justify: model.Justification = model.Justification.NoJustify,
                 expand: bool = False,
                 label: typing.Optional[str] = None,
                 styleID: typing.Optional[str] = None,
                 **kwargs):
        self.init_single(variable, gkeys=['readonly'])
        self.label = label or ''  # TODO: Show label somehow?
        kwargs.update({
            'textvariable': self.variable,
            'justify': justify.value,
            'style': parent.wroot.register_styleID(styleID, 'TEntry'),
        })
        assert isinstance(parent, tk.Misc), f'{parent} is not a valid parent widget'
        super().__init__(parent, **kwargs)  # ttk.Entry
        if expand:
            self.grid(sticky=tk.EW)
        if readonly:
            self.gstate = model.GuiState(readonly=True)
        if __debug__:
            if label is not None:
                warnings.warn(f'{self}: Labels on entries are still unsupported. Include a Label manually.', stacklevel=2)


# TODO: Rename to `Entry` in v0.40
class EntryN(ttk.Entry, mixin.SingleWidget, mixin.MixinValidationSingle):  # type: ignore[misc]
    '''A validated `EntryRaw`.

    This is an alternative `EntryRaw`, validated.

    The widget state is a `VState`, with the value being specified on the
    variable. A simple `str` label can also be set.

    There is no Python documentation, see ``Tk`` :tk:`ttk.Entry
    <ttk_entry.htm>` documentation.

    .. note::

       The ``validation`` and ``readonly`` parameters are conflicting.

       When ``readonly`` is set, and the validation is unchanged from its
       default (`True`, validating based on variable state), the value is
       disabled instead (set to `False`).
       This is to avoid what seems unnecessary validations.

       If you need to override this behavious, use manually define a
       `model.VSettings` object ``validation=tkmilan.model.VSettings(fnSimple=True)``,
       this is the equivalent to the default `True` setting.
       The warning will be triggered in that case (only for debug binaries).

    Args:
        vspec: The shared `specified variable <var.Spec>` or the `specification
            itself <validation.VSpec>` attached to this widget. **Mandatory**.
        readonly: Should the widget allow interaction to toggle its value.
        validation: Configure widget validation.
            Defaults to validating based on variable state.
        justify: Justify combobox text.
            Defaults to `model.Justification.Center`.
        expand: Grow the widget to match the container grid size, horizontally.
            Defaults to `False`.

        label: The label to include besides the entry. **Not implemented yet**.
        styleID: Set a style identifier. Combined with the widget type in
            `RootWindow.register_styleID`.
        parent: The parent widget. Can be a `RootWindow` or another
            `mixin.ContainerWidget`.
    '''
    state_type = var.Spec

    def __init__(self, parent: mixin.ContainerWidget, vspec: typing.Union[var.Spec, validation.VSpec], *,
                 readonly: bool = False,
                 validation: typing.Union[model.VSettings, typing.Callable, bool, None] = True,
                 justify: model.Justification = model.Justification.Center,
                 expand: bool = False,
                 label: typing.Optional[str] = None,
                 styleID: typing.Optional[str] = None,
                 **kwargs):
        self.init_single(vspec, gkeys=['readonly'])
        self.label = label or ''  # TODO: Show label somehow?
        kwargs.update({
            'textvariable': self.variable,
            'justify': justify.value,
            'style': parent.wroot.register_styleID(styleID, 'TEntry'),
        })
        assert isinstance(parent, tk.Misc), f'{parent} is not a valid parent widget'
        super().__init__(parent, **kwargs)  # ttk.Entry
        if expand:
            self.grid(sticky=tk.EW)
        if readonly:
            if validation is True:
                validation = False
            if __debug__:
                if validation not in (None, False):
                    warnings.warn(f'{self}: ReadOnly but Validated widget, are you sure about this? validation={validation!r}', stacklevel=2)
            self.gstate = model.GuiState(readonly=True)
        self.vsettings = self.init_validation(validation)
        if __debug__:
            if label is not None:
                warnings.warn(f'{self}: Labels on entries are still unsupported. Include a Label manually.', stacklevel=2)


# TODO: Support `SpinboxString` with values as a list of strings
# TODO: Rename to `SpinboxNum` in v0.40
class SpinboxN(ttk.Spinbox, mixin.SingleWidget, mixin.MixinValidationSingle):    # type: ignore[misc]
    '''A spinbox widget, a numeric entry with buttons to change the value.

    This is spinbox, an `EntryRaw` storing a numeric value. The main
    interaction consists of two extra buttons to increment and decrement the
    value.

    The state changes do no wrap around by default, unless this is requested
    using the ``wrap`` argument.

    The widget state is a `VState`, with the value being specified on the
    variable. A simple `str` label can also be set.

    There is no Python documentation, see ``Tk`` :tk:`ttk.Spinbox
    <ttk_spinbox.htm>` documentation.

    Args:
        vspec: The `variable <var.Limit>` or the `specification itself
            <validation.VSpec>` attached to this widget. **Mandatory**.
        readonly: Should the widget allow arbitrary state changes, possibly to
            unknown values. Defaults to `True`, the only way to change the state is
            by using the extra buttons.
        validation: Configure widget validation.
            Defaults to validating based on variable state.
        wrap: Wrap changes around the limits. Defaults to `False`.
        justify: Justify entry box text. Defaults to `model.Justification.Center`.

        label: The label to include besides the entry. **Not implemented yet**.
        styleID: Set a style identifier. Combined with the widget type in `RootWindow.register_styleID`.
        parent: The parent widget. Can be a `RootWindow` or another `mixin.ContainerWidget`.
    '''
    state_type = var.Limit

    def __init__(self, parent: mixin.ContainerWidget, vspec: typing.Union[var.Limit, validation.VSpec], *,
                 readonly: bool = True,
                 validation: typing.Union[model.VSettings, typing.Callable, bool, None] = True,
                 wrap: bool = False,
                 justify: model.Justification = model.Justification.Center,
                 label: typing.Optional[str] = None,
                 styleID: typing.Optional[str] = None,
                 **kwargs):
        assert isinstance(parent, tk.Misc), f'{parent} is not a valid parent widget'
        self.init_single(vspec, gkeys=['readonly'])
        assert self.variable is not None and isinstance(self.variable, self.state_type)
        sfrom, sto, sincrement = self.variable.get_spinargs()
        kwargs.update({
            'textvariable': self.variable,
            'from': sfrom, 'to': sto, 'increment': sincrement,
            'wrap': wrap,
            'justify': justify.value,
            'style': parent.wroot.register_styleID(styleID, 'TSpinbox'),
        })
        if 'values' in kwargs:
            raise exception.InvalidWidgetDefinition('Invalid `values` setting, unsupported')
        super().__init__(parent, **kwargs)  # ttk.Spinbox
        if readonly:
            self.gstate = model.GuiState(readonly=True)
        self.vsettings = self.init_validation(validation)
        if __debug__:
            if label is not None:
                warnings.warn(f'{self}: Labels on Spinbox are still unsupported. Include a Label manually.', stacklevel=2)


# TODO: Rename to `Combobox` in v0.40
class ComboboxN(ttk.Combobox, mixin.SingleWidget, mixin.MixinValidationSingle):    # type: ignore[misc]
    '''A combobox widget, combining an entry and a listbox.

    This is a combobox, an `EntryRaw` with a button that shows a pop-up `Listbox`
    with the variable options.

    The entry can be ``readonly``, in which case the only possible values are
    the ones shown on the value list, otherwise the entry is editable with
    arbitrary values, just like any `EntryRaw`.

    The widget state is a `VState`, with the value being specified on the
    variable. A simple `str` label can also be set.

    There is no Python documentation, see ``Tk`` :tk:`ttk.Combobox
    <ttk_combobox.htm>` documentation.

    Args:
        vspec: The shared `specified variable <var.SpecCountable>` or the
            `specification itself <validation.VSpec>` attached to this widget.
            **Mandatory**.
        readonly: Should the widget allow arbitrary state changes, possibly to
            unknown values. Defaults to `True`, the only way to change the state is
            by using the listbox selection.
        validation: Configure widget validation.
            Defaults to validating based on variable state.
        justify: Justify combobox text.
            Defaults to `model.Justification.Center` if ``readonly`` (the
            default), `model.Justification.NoJustify` otherwise.

        label: The label to include besides the combobox. **Not implemented yet**.
        styleID: Set a style identifier. Combined with the widget type in `RootWindow.register_styleID`.
        parent: The parent widget. Can be a `RootWindow` or another `mixin.ContainerWidget`.

    .. note::

        Even though this widget is configured as ``readonly``, it's still
        possible to have invalid values if the variable is used on other
        non-``readonly`` widgets, or if it is programatically changed ignoring
        the specification.

        If you want to make sure this is truly read-only (and therefore always
        valid), do not reuse the variable anywhere else.
    '''
    state_type = var.SpecCountable

    @dataclass
    class Style(model.WStyle):
        '''`ComboboxN` style object.

        There are the settings:

        Args:
            manyvalues: This combobox is used with many values.
                The UX is not very good for comboboxes with many values.
            complexvalidation: Skip warning about `ComboboxN.change`
                ``valuesState`` argument.
                This is for values changes with very complex validation,
                requiring avoiding infinite loops.
                Advanced usage, make sure you know what you are doing.
        '''
        # TODO: Do something about this? Popup with fuzzy search box?
        manyvalues: bool = False
        complexvalidation: bool = False

    def __init__(self, parent: mixin.ContainerWidget, vspec: typing.Union[var.SpecCountable, validation.VSpec], *,
                 readonly: bool = True,
                 validation: typing.Union[model.VSettings, typing.Callable, bool, None] = True,
                 label: typing.Optional[str] = None,
                 justify: typing.Optional[model.Justification] = None,
                 style: Style = Style(_default=True),
                 styleID: typing.Optional[str] = None,
                 **kwargs):
        self.wstyle = style
        assert isinstance(parent, tk.Misc), f'{parent} is not a valid parent widget'
        self.init_single(vspec, gkeys=['readonly'])
        assert self.variable is not None and isinstance(self.variable, self.state_type)
        self.label = label or ''  # TODO: Show label somehow
        if justify is None:
            justify = model.Justification.Center if readonly else model.Justification.NoJustify
        assert justify is not None
        kwargs.update({
            'textvariable': self.variable,
            'justify': justify.value,  # TODO: Move to `Style`?
            'values': list(reversed(self.variable.lall())),  # Same order as Spinbox
            'style': parent.wroot.register_styleID(styleID, 'TCombobox', 'ComboboxPopdownFrame'),
        })
        super().__init__(parent, **kwargs)  # ttk.Combobox
        if readonly:
            self.gstate = model.GuiState(readonly=True)
            # Visual cleanup
            self.trace(self.__combobox_rocls, trace_name='__:ro_cls')
        self.vsettings = self.init_validation(validation)
        if __debug__:
            if label is not None:
                warnings.warn(f'{self}: Labels on Combobox are still unsupported. Include a Label manually.', stacklevel=2)
            if self.wstyle.manyvalues is False and len(self.variable) > 30:  # Just an arbitrary heuristic
                warnings.warn(f'{self}: Too many choices ({len(self.variable)}), this has bad UX', stacklevel=2)

    def __combobox_rocls(self, rstate, etype):
        self.selection_clear()

    def change(self,
               values: typing.Optional[typing.Sequence[str]],
               valuesState: bool = False,
               ) -> None:
        '''Change some aspects of the combobox.

        You can change the values shown on the combobox dropdown, but by
        default this does not change the validation itself. That is, values not
        shown, but present on the original spec are still valid.
        See `ValidationLabels` if you want to enforce the shown value list.

        Usually, this is used to filter the values shown on the combobox. If
        you extend the supported values, you get a warning on debug mode.

        If the widget validation is complex, use ``valuesState`` to change the
        state when changing the values, otherwise the validation state is not
        fully calculated. There is a warning about this in debug mode, if
        detected.

        Arguments:
            values: The new values to show.
            valuesState: Update the state when changing the values. When
                `False`, just force the post validation function.
                Defaults to `False`, make sure to set to `True` when using
                complex validations, like `ValidationLabels`.
        '''
        if values is not None:
            vlist = list(reversed(values))  # Same order as widget creation
            if __debug__:
                assert self.variable is not None and isinstance(self.variable, self.state_type)
                vinvalid = [val for val in vlist if val not in self.variable.container]
                if len(vinvalid) > 0:
                    if (len(vinvalid) < 5) or ((100 // 20) * len(vinvalid) <= len(vlist)):
                        # < 5 || <= 20%
                        vinvalid_str = f'`{" ".join(vinvalid)}`'
                    else:
                        vinvalid_str = f'#{len(vinvalid)} new values'
                    warnings.warn(f'{self}: Expanding #{len(vlist)} valid values with {vinvalid_str}', stacklevel=2)
                if self.wstyle.complexvalidation is False:
                    if valuesState is False and self.vsettings is not None and self.vsettings.fn != self.setup_validation:
                        warnings.warn(f'{self}: Use `valuesState=True` to change the values', stacklevel=2)
            self.configure(values=vlist)
            if valuesState:
                self.wstate = self.wstate
            else:
                self.doValidation()

    # Validation Helpers
    @staticmethod
    def __vlabels_Combobox(vstate, why):
        assert why is not None, 'Need `fnSimple=False`'
        assert isinstance(why.widget, ComboboxN), f'Invalid Widget: {why.widget}'
        return vstate.label in why.widget.cget('values')

    ValidationLabels = model.VSettings(
        # Fixup descriptor usage
        fnSimple=False, fn=__vlabels_Combobox.__func__,  # type: ignore[attr-defined]
    )
    '''Configure widget validation to consider the configured widget labels.

    To be used as:

    .. code:: python

        ComboboxN(self, ...
                  validation=ComboboxN.ValidationLabels,
                  ...
                  )
    '''


class FrameStateful(ttk.LabelFrame, mixin.ContainerWidget):
    '''A frame to hold other widgets, with a checkbox.

    This is a frame with an embedded checkbox `cstate_widget` as "label". This
    label controls the enabled state of the child widgets. You can control the
    checkbox position.

    Note that ``styleID`` is reused for the embedded checkbox. This means that
    applying a style here requires `Checkbox` to be styled too.

    There is no Python documentation, see ``Tk`` :tk:`ttk.LabelFrame
    <ttk_labelframe.htm>` documentation. Note the ``labelwidget`` option.

    Args:
        label: The label to include on the frame separator. Can be given as a class variable.
        labelAnchor: The position of the label on the frame separator.
            Given as one of the cardinal points.
            Defaults to a OS-specific location (`model.CP.default`).
        cvariable: Use an externally defined `cstate` variable, instead of
            creating a new one specific for the `cstate` widget.
        cvariableDefault: The default value for `cstate`.
            When `None`, the value is not changed at start.
            Defaults to starting enabled, unless ``cvariable`` is given, for
            which the value is not changed.
        cstateReadonly: Make the `cstate` widget readonly, that is, the user
            cannot change it directly. It can still be changed programatically
            (e.g. calculated based on other widget values).
            Defaults to `False`.
        cstateReversed: Reverse the `cstate` value that controls the child
            widget state.
            This means when the embedded checkbox is disabled, the inner
            widgets are enabled, and *vice versa*.
            Defaults to `False`.
        cstateArgs: Extra arguments for the `cstate` widget, `cstate_widget`.
            The following keys are overriden: ``variable`` (see ``cvariable``),
            ``label`` (see ``label``), ``readonly`` (see ``cstateReadonly``),
            ``styleID`` (see ``styleID``).

        styleID: Set a style identifier. Combined with the widget type in
            `RootWindow.register_styleID`.
        parent: The parent widget. Can be a `RootWindow` or another
            `mixin.ContainerWidget`.

    See Also:
        - `FrameLabelled`: A simpler version of this, without the embedded checkbox.
        - `FrameRadio`: A variant of this widget, with a radio button.
    '''
    label: typing.Optional[str] = None

    class __w_cstate(Checkbox):
        isAuto = None  # Isolate from GUI state, taken care in `set_gui_state`

    cstate_widget: __w_cstate
    '''The widget for the embedded `Checkbox`.

    Uses the `cstate` variable.

    Note:
        The widget type is a local `Checkbox` subclass, specific for this widget.

    Note:
        When tracing this, use `atrace` to guarantee your callback runs after
        the child widgets are changed.
    '''
    cstate: var.Boolean
    '''The variable holding the embedded `Checkbox` state.

    Used on the `cstate_widget`.

    See Also:
        ``cvariable``: This can be configured as an external variable.
    '''

    def __init__(self, parent: mixin.ContainerWidget, *args,
                 label: typing.Optional[str] = None, labelAnchor: model.CP = model.CP.default,
                 cvariable: typing.Optional[var.Boolean] = None, cvariableDefault: typing.Optional[bool] = None,
                 cstateReadonly: bool = False, cstateReversed: bool = False,
                 cstateArgs: typing.Optional[typing.Mapping[str, typing.Any]] = None,
                 styleID: typing.Optional[str] = None,
                 **kwargs):
        chosen_label = fn.label_fallback(label, self.label)
        if chosen_label is None:
            raise exception.InvalidWidgetDefinition('Missing required label')
        # Usual Initialization, without any label widget
        assert isinstance(parent, tk.Misc), f'{parent} is not a valid parent widget'
        super().__init__(parent, labelanchor=labelAnchor.value,
                         style=parent.wroot.register_styleID(styleID, 'TLabelframe'),
                         )  # ttk.LabelFrame
        # Create the checkbox widget, children of `self`
        cstateArgs = dict(cstateArgs or {})
        cstateArgs.update({  # Override cstate arguments
            'variable': cvariable,
            'label': chosen_label,
            'readonly': cstateReadonly,
            'styleID': styleID,
        })
        cstate_widget = self.__class__.__w_cstate(self, **cstateArgs)
        assert isinstance(cstate_widget.variable, var.Boolean), '`cvariable` is not a simple `var.Boolean`'
        self.configure(labelwidget=cstate_widget)
        self.__cstate_reversed = cstateReversed
        cstate_widget.trace(self.onChanged_cstate, trace_name='__:substate')
        self.init_container(*args, **kwargs)
        # Configure the checkbox variable and widget
        self.cstate = cstate_widget.variable
        self.cstate_widget = cstate_widget
        assert cstate_widget.wparent is None
        cstate_widget.wparent = self
        # Setup the default value for that widget
        if __debug__:
            if cvariable is not None and cvariableDefault is not None:
                warnings.warn(f'{self}: cvariable: Setting a default with an external variable')
        if cvariable is None and cvariableDefault is None:
            cvariableDefault = True
        if cvariableDefault is not None:
            # if __debug__:
            #     logger.debug('%s: Default %s=%s', self, self.cstate, cvariableDefault)
            self.cstate.set(cvariableDefault)

    def state_get(self, *args, vid_upstream: typing.Optional[typing.Set[str]] = None, **kwargs) -> typing.Union[None, bool, model.WState[bool, typing.Any]]:
        ''''''  # Do not document
        cid = fn.vname(self.cstate)
        if vid_upstream and cid in vid_upstream:
            cstate = None
        else:
            cstate = self.cstate.get()
        if __debug__:
            logger_autostate.debug('%s: %scstate=%s', self, 'R-' if self.__cstate_reversed else '', cstate)
        upstream = super().state_get(*args, vid_upstream=vid_upstream, **kwargs)
        if self.wstate_single is True and upstream is None:
            if __debug__:
                if self.wstate_single_wstate is False:
                    # TODO: Not sure this is a valid warning
                    warnings.warn('{self}: Missing "wstate_single_wstate" marking', stacklevel=3)
                logger_autostate.debug('%s: cstate only', self)
            return cstate
        else:
            assert self.wstate_single_wstate is False, f'{self}: Invalid "wstate_single_wstate" marking, has one element'
            return (model.WStateR if self.__cstate_reversed else model.WState)(
                cstate,
                upstream,
            )

    def state_set(self, state: typing.Union[bool, model.WState[bool, typing.Any]], *args, **kwargs):
        ''''''  # Do not document
        assert state is not None, f'Invalid empty WState: {state!r}'
        if isinstance(state, bool):
            assert self.wstate_single_wstate is True, f'{self}: Missing "wstate_single_wstate"'
            if __debug__:
                logger_autostate.debug('%s: cstate only=%s', self, state)
            self.cstate.set(state)
        else:
            if state.state is not None:
                assert isinstance(state.state, bool), f'Invalid WState: {state!r}'
                if __debug__:
                    logger_autostate.debug('%s: cstate=%s', self, state.state)
                self.cstate.set(state.state)
            super().state_set(state.substate, *args, **kwargs)

    def set_gui_state(self, state: typing.Optional[model.GuiState] = None, _sub: bool = False, **kwargs) -> model.GuiState:
        ''''''  # Do not document
        # "Trace" the frame enabled status
        frame_enabled = kwargs.get('enabled', None) if state is None else state.enabled
        self_state = super().set_gui_state(state, _sub=False, **kwargs)
        if frame_enabled is None:
            if __debug__:
                logger_autostate.debug('S| %s: V=%s', self, self_state.valid)
            self.cstate_widget.gstate = model.GuiState(valid=self_state.valid)
        else:
            state_enabled = self.cstate.get() ^ self.__cstate_reversed  # XOR
            if __debug__:
                logger_autostate.debug('S| %s: [F=%s S%s=%s] V=%s', self,
                                       frame_enabled, '[R]' if self.__cstate_reversed else '', state_enabled,
                                       self_state.valid)
            self.cstate_widget.gstate = model.GuiState(enabled=frame_enabled, valid=self_state.valid)
            self.set_gui_substate(model.GuiState(enabled=frame_enabled and state_enabled))
            # TODO: unsetOnDisable?
            # TODO: setOnEnable?
        return self_state

    def onChanged_cstate(self, cstate, etype):
        ''''''  # Internal, do not document
        assert etype == 'write'
        status = cstate.get() ^ self.__cstate_reversed  # XOR
        frame_enabled = self.gstate.enabled
        if __debug__:
            logger_autostate.debug('%s: S%s=%s Fe=%s', self,
                                   '[R]' if self.__cstate_reversed else '', status, frame_enabled)
        self.set_gui_substate(model.GuiState(enabled=frame_enabled and status))

    @property
    def wlabel(self) -> str:
        '''Calculate the chosen label text.'''
        return self.cstate_widget.wlabel

    def toggle(self, _a1: typing.Any = None, _a2: typing.Any = None) -> None:
        '''Switch the `cstate` variable state to its opposite (`not <not>`).

        This should only be used if the current frame has the
        `wstate_single_wstate` marking.
        This is checked for debug binaries, and a warning is produced.

        Args:
            _a1: Optional, unused. This exists for API compatibility with
                bindings.
            _a2: Optional, unused. This exists for API compatibility with
                traces.
        '''
        if __debug__:
            if self.wstate_single_wstate is False:
                logger.warning('%s: Toggling without "wstate_single_wstate", only part of the state is affected', self)
        self.cstate_widget.toggle()


class FrameRadio(ttk.LabelFrame, mixin.ContainerWidget):
    '''A frame to hold other widgets, with a radio button.

    This is a frame with an embedded radio button `rstate_widget` as "label".
    This label controls the enabled state of the child widgets. You can control
    the radio button position.

    Unlike other widgets, the variable must be created separately and given in
    addition to the value. See `Radio`.

    Note that ``styleID`` is reused for the embedded radio button. This means
    that applying a style here requires `Radio` to be styled too.

    There is no Python documentation, see ``Tk`` :tk:`ttk.LabelFrame
    <ttk_labelframe.htm>` documentation. Note the ``labelwidget`` option.

    Args:
        rvariable: The shared variable attached to this widget. Requires a
            specification too, see `var.Spec` for more information.
            **Mandatory**.
        rvalue: The value for this particular widget. Must be specified by the
            ``rvariable``, this is checked.
            **Mandatory**.
        label: The label to include besides the widget. Can be given as a class variable.
        labelAnchor: The position of the label on the frame separator.
            Given as one of the cardinal points.
            Defaults to a OS-specific location (`model.CP.default`).
        rstateReversed: Reverse the `rstate` value that controls the child
            widget state.
            This means when the embedded radio button is selected, the inner
            widgets are disabled, and *vice versa*.
            Defaults to `False`.
        rstateArgs: Extra arguments for the `rstate` widget, `rstate_widget`.

        styleID: Set a style identifier. Combined with the widget type in `RootWindow.register_styleID`.
        parent: The parent widget. Can be a `RootWindow` or another `mixin.ContainerWidget`.

    See Also:
        - `FrameLabelled`: A simpler version of this, without the embedded radio button.
        - `FrameStateful`: A variant of this widget, with a checkbox.
    '''
    label: typing.Optional[str] = None

    class __w_rstate(Radio):
        isAuto = None  # Isolate from GUI state, taken care in `set_gui_state`

    rstate_widget: __w_rstate
    '''The widget for the embedded `Radio`.

    Uses the `rstate` variable.

    Note:
        The widget is a local `Radio` subclass, specific for this widget.

    Note:
        When tracing this, use `atrace` to guarantee your callback runs after
        the child widgets are changed.
    '''

    rstate: var.Spec
    '''The variable holding the embedded `Radio` state.

    Used on the `rstate_widget`.
    '''

    def __init__(self, parent: mixin.ContainerWidget, *args,
                 rvariable: var.Spec, rvalue: str,
                 label: typing.Optional[str] = None, labelAnchor: model.CP = model.CP.default,
                 rstateReversed: bool = False,
                 rstateArgs: typing.Optional[typing.Mapping[str, typing.Any]] = None,
                 styleID: typing.Optional[str] = None,
                 **kwargs):
        chosen_label = fn.label_fallback(label, self.label)
        if chosen_label is None:
            raise exception.InvalidWidgetDefinition('Missing required label')
        # Create the "label" widget
        rstateArgs = dict(rstateArgs or {})
        assert rvalue in rvariable
        rstateArgs.update({  # Override rstate arguments
            'variable': rvariable, 'value': rvalue,
            'label': chosen_label,
            'styleID': styleID,
        })
        rstate_widget = self.__class__.__w_rstate(parent, **rstateArgs)
        assert rvariable == rstate_widget.variable
        # Usual Initialization
        assert isinstance(parent, tk.Misc), f'{parent} is not a valid parent widget'
        super().__init__(parent, labelwidget=rstate_widget, labelanchor=labelAnchor.value,
                         style=parent.wroot.register_styleID(styleID, 'TLabelframe'),
                         )  # ttk.LabelFrame
        self.__rstate_reversed = rstateReversed
        rstate_widget.trace(self.__onChanged_rstate(rvalue),
                            trace_name='__:substate', trace_initial=True)
        self.init_container(*args, **kwargs)
        # Configure the radio variable and widget
        self.rstate = rvariable
        self.rstate_widget = rstate_widget
        rstate_widget.wparent = self

    # TODO: Define `state_get` produce WState/WStateR?

    def set_gui_state(self, state: typing.Optional[model.GuiState] = None, _sub: bool = False, **kwargs) -> model.GuiState:
        ''''''  # Do not document
        # "Trace" the frame enabled status
        frame_enabled = kwargs.get('enabled', None) if state is None else state.enabled
        self_state = super().set_gui_state(state, _sub=False, **kwargs)
        if frame_enabled is None:
            if __debug__:
                logger_autostate.debug('S| %s: V=%s', self, self_state.valid)
            self.rstate_widget.gstate = model.GuiState(valid=self_state.valid)
        else:
            state_enabled = self.isSelected() ^ self.__rstate_reversed  # XOR
            if __debug__:
                logger_autostate.debug('S| %s: [F=%s S%s=%s] V=%s', self,
                                       frame_enabled, '[R]' if self.__rstate_reversed else '', state_enabled,
                                       self_state.valid)
            self.rstate_widget.gstate = model.GuiState(enabled=frame_enabled, valid=self_state.valid)
            self.set_gui_substate(model.GuiState(enabled=frame_enabled and state_enabled))
        return self_state

    def __onChanged_rstate(self, rvalue: str) -> typing.Callable[[var.Variable, typing.Optional[str]], None]:
        def onChanged_rstate(rstate: var.Variable, etype: typing.Optional[str]) -> None:
            assert etype in ('write', None)
            rresult = rstate.get()
            status = (rresult.valid and rresult.label == rvalue) ^ self.__rstate_reversed  # XOR
            frame_enabled = self.gstate.enabled
            if __debug__:
                logger_autostate.debug('%s: S%s=%s Fe=%s', self,
                                       '[R]' if self.__rstate_reversed else '', status, frame_enabled)
            self.set_gui_substate(model.GuiState(enabled=frame_enabled and status))
        return onChanged_rstate

    def isSelected(self) -> bool:
        '''Check if this specific widget is selected.'''
        return self.rstate_widget.isSelected()

    @property
    def wlabel(self) -> str:
        '''Calculate the chosen label text.'''
        return self.rstate_widget.wlabel


class EntryMultiline(tk.Text, mixin.SingleWidget):
    '''A multiline text widget, supporting `LTML` contents.

    This is a multiline version of the `EntryRaw` widget, with rich text
    capabilities.
    Supports only the readonly state, that is, the widget contents can only be
    edited programatically.

    The state is a single `str` value, internally parsed to `parser.LTML
    <LTML>`.

    There is no Python documentation, see ``Tk`` :tk:`tk.Text <text.htm>` or
    ``effbot`` :tkinter_effbot:`tk.Text <text.htm>` documentation.

    Args:
        variable: Use an externally defined variable, instead of creating a new
            one specific for this widget.
        style: Configure the widget style.

        parent: The parent widget. Can be a `RootWindow` or another `mixin.ContainerWidget`.

    Note:

        The underlying widget is not part of `ttk <tkinter.ttk>` like most others. All
        efforts are expended to make this an implementation detail, without
        practical effects.
    '''
    state_type = var.String
    _bindings_tag: typing.MutableMapping[typing.Tuple[str, str], model.BindingTag]
    '''Store all widget `BindingTag` objects, keyed by ``(tag, name)`` (see `binding_tag`).'''
    styleSheet: typing.Optional[typing.Mapping[str, typing.Mapping[str, typing.Any]]] = None
    '''Store a style sheet mapping identifiers/classes to styling configuration.

    Identifiers are marked on LTML as ``<span id="something">``, and on the
    style sheet as ``#something``.

    Classes are marked on LTML as ``<span class="something">``, and on the
    style sheet as ``.something``.

    There is no Python documentation, see ``Tk`` :tk:`text tags <text.htm#M43>`
    documentation.
    '''

    @dataclass
    class Style(model.WStyle):
        '''`EntryMultiline` style object.

        These are the settings:

        Args:
            font_base: Base Font name, for all the widget.
            colour_bg_on: Widget background, when enabled.
            colour_bg_off: Widget background, when disabled.
            colour_link_normal: Hyperlink foreground colour, normal links.
            colour_link_visited: Hyperlink foreground colour, visited links.
            cursor_link: Hyperlink cursor. Set only when hovering over the links.
                Optional, disabled when set to `None`.
        '''
        font_base: str = 'TkTextFont'  # This font should be used for user text in entry widgets, listboxes etc.
        colour_bg_on: str = 'white'
        colour_bg_off: str = 'lightgrey'
        colour_link_normal: str = 'blue'
        colour_link_visited: str = 'purple'
        cursor_link: typing.Optional[str] = 'hand2'

    def __init__(self, parent: mixin.ContainerWidget, *,
                 variable: typing.Optional[var.String] = None,
                 style: Style = Style(_default=True),
                 **kwargs):
        self.wstyle = style
        self.init_single(variable)
        kwargs.pop('state', None)  # Support only readonly state
        kwargs['font'] = style.font_base  # Override the base font
        assert isinstance(parent, tk.Misc), f'{parent} is not a valid parent widget'
        super().__init__(parent, **kwargs)  # tk.Text
        readonly = True  # Support only readonly state, for now...
        # GUI State Tracker
        # - Since this is not a `ttk.Widget`, this need to be emulated
        self.__gstate: model.GuiState = model.GuiState(enabled=True, valid=True)
        # - Set the internal readonly state out-of-the-box
        self.set_gui_state(readonly=readonly, _internal=True)
        assert self.variable is not None, f'{self!r}: Missing variable'
        self.wstate = getattr(self.variable, '_default', '')  # Set the default (before the trace)
        # State Tracker
        self.trace(self._varChanged, trace_name=f'__:{__name__}')
        # StyleSheet
        if self.styleSheet:
            if __debug__:
                def _setupStylesheet():
                    try:
                        self._setupStylesheet()
                    except tk.TclError as e:
                        logger.error('%s:: Invalid StyleSheet: %s', self, e)
                        sys.exit(100)
            else:
                _setupStylesheet = self._setupStylesheet
            self.after_idle(_setupStylesheet)  # No need for a `TimeoutIdle` here

        # Bindings
        self._bindings_tag = {}
        self.binding_tag('a', '<Button-1>', self._onClickTag)
        if self.wstyle.cursor_link is not None:
            self.binding_tag('a', '<Enter>', self._onCursor)
            self.binding_tag('a', '<Leave>', self._onCursor)
        if readonly:
            # Disable Double-Click event, when readonly
            self.binding('<Double-Button-1>', fn.binding_disable, key='__:nodouble')

    def _varChanged(self, var, etype):
        assert etype == 'write'
        # This function is called when the value changes
        # It's the implementation that binds the variable and the widget,
        #  so this should be idempotent
        vs = var.get()
        with self.as_editable():
            # Delete the entire state
            # From: First line, first character
            #   To: End
            self.delete('1.0', 'end')
            # Reset styles
            self.style_reset()
            # Add the current state
            # TODO: Save the parsed LTML state somewhere in this object, with `data`?
            for te in parser.parse_LTML(vs):
                assert isinstance(te, model.TextElement)
                self.insert(tk.END, te.text, te.atags)

    def _setupStylesheet(self) -> None:
        assert self.styleSheet is not None
        if __debug__:
            logger_styling.debug('Set StyleSheet [%s]:', self)
        for sid, skwargs in self.styleSheet.items():
            if __debug__:
                logger_styling.debug('| %s: %s', sid, ' '.join(f'{kk}={kv!r}' for kk, kv in skwargs.items()))
            self.tag_configure(sid, **skwargs)

    def get_gui_state(self) -> model.GuiState:
        ''''''  # Do not document
        if __debug__:
            logger_autostate.debug('State > %r', self.__gstate)
        # return a copy of the object
        return model.GuiState(**dict(self.__gstate.items()))

    def set_gui_state(self, state: typing.Optional[model.GuiState] = None, *, _internal: bool = False, **kwargs) -> model.GuiState:
        ''''''  # Do not document
        if state is None:
            state = model.GuiState(**kwargs)
        if __debug__:
            logger_autostate.debug('State < %r', state)
        # Adjust current state
        for sname, svalue in state.items():
            assert sname != '_internal'  # Should be impossible...
            if svalue is not None:
                if sname == 'readonly' and _internal is False:
                    raise ValueError(f'{self}: No support for external readonly state manipulation')
                setattr(self.__gstate, sname, svalue)
        # Adjust widget state
        cfg = {}
        if self.__gstate.enabled is True:
            if self.__gstate.readonly is not None:
                cfg['state'] = tk.NORMAL if not self.__gstate.readonly else tk.DISABLED
            cfg['background'] = self.wstyle.colour_bg_on
        elif self.__gstate.enabled is False:
            cfg['state'] = tk.DISABLED
            cfg['background'] = self.wstyle.colour_bg_off
            self.style_reset()
        if __debug__:
            logger_autostate.debug('C %s', self.__gstate)
            logger_autostate.debug('| %s', cfg)
        self.configure(**cfg)
        # Valid: TBD
        assert state is not None
        return state

    @contextmanager
    def as_editable(self):
        '''Temporarily mark the widget as editable.

        A context manager, used to change the contents of the widget while keep
        it "readonly".
        Technically, this should only be used internally, using the state
        tracker functions, but it might be useful externally.

        This is to be used like this:

        .. code:: python

            # `widget` is readonly
            with widget.as_editable():
                pass  # `widget` is editable
            # `widget` is readonly
        '''
        oenabled = self.__gstate.enabled
        assert self.__gstate.readonly is True
        self.set_gui_state(enabled=True, readonly=False, _internal=True)
        try:
            yield
        finally:
            self.set_gui_state(enabled=oenabled, readonly=True, _internal=True)

    def binding_tag(self,
                    tag: str, sequence: str,
                    *args,
                    key: typing.Optional[str] = None,
                    immediate: bool = True,
                    **kwargs,
                    ) -> model.BindingTag:
        '''Binds a sequence to a tag.

        Stores all widget tag bindings on a per-instance dictionary, for later
        usage. Note that all dictionary keys must be different. For the same
        bindings on a single widget tag, this requires passing the ``key``
        argument.

        See the ``Tk`` :tk:`tag bind <text.htm#M166>` documentation.

        Args:
            key: Optional. Defaults to the ``sequence`` itself. Useful to
                support multiple bindings on the same sequence, for the same tag.

        All other arguments are passed to `model.BindingTag` object.
        '''
        name = (tag, key or sequence)
        if name in self._bindings_tag:
            raise ValueError(f'Repeated binding for "{sequence}" in {self!r}(tag "{tag}"). Change the "key" parameter.')
        if __debug__:
            if len(tag) == 0 or tag[0] == '<':
                warnings.warn(f'{self}: binding_tag requires tag[{tag}] and sequence[{sequence}], by this order', stacklevel=2)
        self._bindings_tag[name] = model.BindingTag(self, tag, sequence, *args, immediate=immediate, **kwargs)
        return self._bindings_tag[name]

    # TODO: Use proper `Font` settings
    def _font(self, fontbase: typing.Optional[tk.font.Font] = None,
              *,
              size: typing.Optional[int] = None,
              bold: typing.Optional[bool] = None,
              italic: typing.Optional[bool] = None,
              ):
        fontbase = fontbase or tk.font.nametofont(self.wstyle.font_base)
        # Start from the base font options
        options = fontbase.actual()
        if size:
            options['size'] = size
        if bold is True:
            options['weight'] = tk.font.BOLD
        if italic is True:
            options['slant'] = tk.font.ITALIC
        return tk.font.Font(**options)

    def _style_a(self, tag: str = 'a', *, visited: bool) -> None:
        fg = self.wstyle.colour_link_visited if visited else self.wstyle.colour_link_normal
        self.tag_configure(tag, foreground=fg, underline=True)

    def style_reset(self, event=None, *, a: bool = True, b: bool = True, i: bool = True) -> None:
        '''Reset the style to the original.

        Args:
            a: Reset ``a`` anchors.
            b: Reset ``b`` bold inline spans.
            i: Reset ``i`` italic inline spans.

            event: Optional, unused. This exists for API compatibility with the
                ``onClick`` functions.
        '''
        # TODO: Why not reset everything always? YAGNI.
        if b:
            self.tag_configure('b', font=self._font(bold=True))
        if i:
            self.tag_configure('i', font=self._font(italic=True))
        for tag in self.tag_names():
            # a
            if a and tag == 'a' or tag.startswith('a::'):
                self._style_a(tag=tag, visited=False)

    def _onClickTag(self, event, *, tag_name: str = 'a'):
        if not self.__gstate.enabled:  # TODO: disable the binding?
            return  # Do nothing when disabled
        dobj = self.dump(f'@{event.x},{event.y}', text=True, tag=True)
        if __debug__:
            logger.debug('D: %r', dobj)
        dwhat = [dinner[0] for dinner in dobj]
        tags_cl = []  # Ignore the "sel" tag
        if 'tagon' in dwhat:
            # Click in the start of the tag
            tags_cl = [lst[1] for lst in dobj if lst[0] == 'tagon' and lst[1] != tk.SEL]
            # For nested tags, this might not be the same as the text method
        if len(tags_cl) == 0 and 'text' in dwhat:
            # Click in the middle of the tag
            click_location = [lst[2] for lst in dobj if lst[0] == 'text'][0]
            tp = self.tag_prevrange(tag_name, click_location)
            if __debug__:
                logger.debug(' | Text @ <%s', tp)
            tags_cl = [lst[1] for lst in self.dump(*tp, tag=True) if lst[1] != tk.SEL]
        if len(tags_cl) == 0:
            raise NotImplementedError
        if __debug__:
            logger.debug(' | Tags %s', tags_cl)
        assert len(tags_cl) >= 2, f'Missing tags: {tags_cl}'
        tags_proc = [t for t in tags_cl if '::' in t]
        assert len(tags_proc) == 1
        tagi = tags_proc[0]
        tag = tagi.split('::')[0]
        assert tag_name == tag, f'Wrong onClickTag: Requested[{tag_name}] != Found[{tag}]'
        assert tag in tags_cl, f'Wrong tag_index: {tag}[{tagi}]'
        tags_other = [t for t in tags_cl if t not in (tag, tagi)]
        if __debug__:
            logger.debug(' = %s[%s]', tag, tagi)
        self._style_a(tag=tagi, visited=True)
        self.onClickTag(tag, tagi, tags_other)

    def _onCursor(self, event: typing.Any = None) -> None:
        if not self.__gstate.enabled:  # TODO: disable the binding?
            return  # Do nothing when disabled
        assert event is not None
        assert event.type in (tk.EventType.Enter, tk.EventType.Leave), f'Invalid EventType: {event.type!r}'
        widget = event.widget
        assert self.wstyle.cursor_link is not None, f'{widget!r}: Disabled link hovering'
        hover = event.type == tk.EventType.Enter
        cname: str = self.wstyle.cursor_link if hover else ''
        # if __debug__:
        #     logger.debug('| %s: %s > "%s"', widget, event.type.name, cname)
        widget['cursor'] = cname

    def onClickTag(self, tag: str, tag_index: str, tags_other: typing.Sequence[str]) -> None:
        '''Callback to be called when clicking ``a`` tags in this widget.

        Defaults to doing nothing.

        Available for subclass redefinition.

        Args:
            tag: The main tag type. In this case, it's always ``a``.
            tag_index: The tag index. See `LTML <parser.LTML>` Automatic Counter tags.
            tags_other: List of extra tags attached to the anchor. Might be empty.
        '''
        pass

    def wstateLTML(self) -> typing.Iterable[model.TextElement]:
        '''Return the parsed LTML state, as a generator of `model.TextElement`.

        See Also:
            - `wstate`: Return the LTML string.
            - `wstateText`: Return the underlying text, without any tags.
        '''
        # TODO: Save the parsed LTML state somewhere in this object, with `data`?
        yield from parser.parse_LTML(self.wstate)

    def wstateText(self) -> str:
        '''Strip all LTML tags and return the underlying text.

        See Also:
            - `wstate`: Return the LTML string.
            - `wstateLTML`: Generate a list of LTML parsed objects.
        '''
        # TODO: Save the parsed LTML state somewhere in this object, with `data`?
        return ''.join(
            te.text
            for te in parser.parse_LTML(self.wstate)
        )


class Notebook(ttk.Notebook, mixin.ContainerWidget):
    '''A tabbed interface to hold other containers.

    This is a tabbed interface to show several containers in the same space.

    You can manipulate the tab order and visibility with `torder` and
    `torder_change`, see `NotebookTabOrder <model.NotebookTabOrder>`.

    The individual tabs must all be containers (include proxy widgets for
    containers), there's no support for single widgets.
    Use a holder `FrameUnlabelled` to show a single widget for each tab.

    There is no Python documentation, see ``Tk`` :tk:`ttk.Notebook
    <ttk_notebook.htm>` documentation.

    Args:
        traversal: Setup tab traversal with special keyboard shortcuts, and
            also with mouse wheel scrolling. See the Tk documentation for the
            keyboard part. Enabled by default.
        traversalWraparound: When ``traversal`` is setup, configure wraparound.
            That is, scrolling to the next tab from the last one should "scroll"
            into the first tab, and vice-versa for the first tab.
            This only matters for the mouse wheel traversal, the keyboard
            shortcuts always enable this traversal.
            Disabled by default.

        styleID: Set a style identifier. Combined with the widget type in `RootWindow.register_styleID`.
        layout: Ignored, it is hardcoded to `None` always.
        parent: The parent widget. Can be a `RootWindow` or another `mixin.ContainerWidget`.

    See Also:
        `NotebookUniform`: A simpler version of this, when each individual tab is the same type

    .. note::
        The ``traversalWraparound`` setting cannot be harmonised with the
        existing :kbd:`Control-Tab`/:kbd:`Control-Shift-Tab`, this is an
        upstream limitation. See the ``Tk`` :tk:`Notebook keyboard traversal
        <ttk_notebook.htm#M35>` documentation.

    .. note:: As mentioned above, use the following code to support a single widget per tab:

        .. code:: python

            class NB_Inner(tkmilan.FrameUnlabelled):
                wstate_single = 'inner'

                def setup_widgets(self):
                    self.inner = InnerWidget(self)

            class NB(tkmilan.Notebook):
                def setup_tabs(self):
                    return {
                        't1': NB_Inner(self),
                    }
    '''
    Tab = model.NotebookTab  # Alias the notebook tab information  # TODO: Move NotebookTab class here?
    '''Alias for `model.NotebookTab` class.'''
    wtabs: typing.Mapping[str, model.NotebookTab]
    '''Mapping of tab identifiers, and `Tab` objects.'''
    layout_padable = False
    __t_rindex: typing.Optional[typing.MutableMapping[str, str]] = None

    def __init__(self, parent: mixin.ContainerWidget, *args,
                 layout: None = None,
                 traversal: bool = True,
                 traversalWraparound: bool = False,
                 styleID: typing.Optional[str] = None,
                 **kwargs):
        self.__t_rindex = {}
        assert isinstance(parent, tk.Misc), f'{parent} is not a valid parent widget'
        super().__init__(parent,
                         style=parent.wroot.register_styleID(styleID, 'TNotebook', 'TNotebook.Tab'),
                         )  # ttk.Notebook
        # No `layout` is used, force it to `None`
        self.init_container(*args, layout=None, **kwargs)
        assert len(self.wtabs) == len(self.__t_rindex), f'{self}: Missing rindex, run `Notebook.setup_widgets`'
        # Tab Traversal
        self.tWraparound = traversalWraparound
        if traversal:
            self.enable_traversal()
            # Bind mouse wheel: Digital Scrolling
            self.__t_bind_mousewheel = fn.bind_mousewheel(self,
                                                          up=self._tabScrollUp, down=self._tabScrollDown,
                                                          immediate=True)

    def setup_widgets(self, *args, **kwargs):
        '''Define the sub widgets based on the tabs.

        Do not overwrite this unless you know what you are doing.

        To edit the tabs, see `setup_tabs`.
        '''
        assert self.__t_rindex is not None, f'{self}: Invalid rindex'
        self.wtabs = self.setup_tabs(*args, **kwargs)
        # Setup the reverse tab index
        for idx, wtab in self.wtabs.items():
            self.__t_rindex[wtab.tk_idx] = idx
        # if __debug__:
        #     logger.debug('%s: %d Tabs', self, len(self.wtabs))
        widgets = {}
        for identifier, ti in self.wtabs.items():
            # if __debug__:
            #     logger.debug('> %s: %r', ti.name, ti.widget)
            assert isinstance(ti.widget, mixin.ContainerWidget), f'{self!r}: Tab Widget [{ti.identifier or identifier}]"{ti.name}" must be a container'
            extra = {
                **ti.extra,
                'text': ti.name,
                'image': ti.image or '',
                'compound': ti.imageCompound,
            }
            self.add(ti.widget.wproxy or ti.widget, **extra)
            ti.identifier = identifier
            widgets[identifier] = ti.widget
        return widgets

    def setup_tabs(self, *args, **kwargs) -> typing.Mapping[str, model.NotebookTab]:
        '''Define the tabs here.

        Similar to `setup_widgets <mixin.ContainerWidget.setup_widgets>`, but
        defines `model.NotebookTab`, extra information about each widget.
        '''
        raise NotImplementedError

    def torder_get(self) -> model.NotebookTabOrder:
        ''''''  # Internal, do not document
        assert self.__t_rindex is not None, f'{self}: Missing rindex'
        wactive, wdisabled = [], set()
        # if __debug__:
        #     logger.debug('> %s: Tabs:', self)
        for w in self.tabs():
            assert w in self.__t_rindex, f'{self}: Missing tab widget `{w}`'
            idx = self.__t_rindex[w]
            tstate = self.tab(w, option='state')
            # if __debug__:
            #     logger.debug('| %s[%s]: %r', idx, w, tstate)
            if tstate == tk.NORMAL:
                wactive.append(idx)
            elif tstate == tk.DISABLED:
                wactive.append(idx)
                wdisabled.add(idx)
            else:
                assert tstate == tk.HIDDEN
        return model.NotebookTabOrder(wactive, disabled=wdisabled)

    def torder_set(self, order: model.NotebookTabOrder):
        ''''''  # Internal, do not document
        for idx, index, state in order.tk_states(self.wtabs.keys()):
            assert idx in self.wtabs, f'Invalid Tab: {idx}'
            widx = self.wtabs[idx].tk_idx
            if index is not None:
                self.insert(index, widx)
            self.tab(widx, state=state)
        if __debug__:
            neworder = self.torder_get()
            assert order == neworder, f'wants={order} gets={neworder}'

    torder = property(torder_get, torder_set, doc='Tab Order')

    def torder_change(self, *,
                      enable: typing.Optional[typing.Iterable[str]] = None,
                      disable: typing.Optional[typing.Iterable[str]] = None,
                      hide: typing.Optional[typing.Iterable[str]] = None,
                      ):
        '''Change the tab order settings.

        Manipulate the `torder` with a simplified interface for incremental
        changes. Accept sequences of tab identifiers.

        The validation covers most common cases: manipulating missing
        identifiers, ambigous changes, etc. This is fully validated in debug
        mode, but fully skipped in production, for performance characteristics.

        See the `NotebookTabStateT` for further explanation of the "types".

        Args:
            enable: Put the given tabs in visible normal state.
            disable: Put the given tabs in visible disable state.
            hide: Hide the given tabs.
        '''
        what = (
            (tk.NORMAL, enable or ()),
            (tk.DISABLED, disable or ()),
            (tk.HIDDEN, hide or ()),
        )
        if __debug__:
            did: typing.Mapping[str, typing.MutableSequence[str]] = {nstate: [] for nstate, _ in what}
        for nstate, sequence in what:
            for idx in sequence:
                assert idx in self.wtabs, f'Invalid Tab @ {nstate}: {idx}'
                widx = self.wtabs[idx].tk_idx
                # if __debug__:
                #     cstate = self.tab(widx, option='state')
                #     logger.debug('%s: %s » %s', idx, cstate, nstate)
                self.tab(widx, state=nstate)
                if __debug__:
                    did[nstate].append(idx)
        if __debug__:
            import itertools
            for ((t1, _), (t2, _)) in itertools.combinations(what, 2):
                if set(did[t1]).intersection(set(did[t2])):
                    warnings.warn(f'{self}: Changing invalid indexes ({t1}/{t2})')
            torder = self.torder
            assert all(idx in torder.shown for idx in did[tk.NORMAL])
            assert all(idx in torder.shown and idx in torder.disabled for idx in did[tk.DISABLED])
            assert all(idx not in torder.shown for idx in did[tk.HIDDEN])

    def torder_cidx(self, *idxs: str,
                    enable: typing.Optional[bool] = None,
                    disable: typing.Optional[bool] = None,
                    hide: typing.Optional[bool] = None,
                    ):
        '''Change the tab order settings for several tabs.

        This is an ergonomic alternative to `torder_change` for applying the
        same operation on several tabs, using simple boolean values.

        To use, call this function with a list of tab indexes to operate, and
        one of the three optional keyword arguments, setting a boolean value.

        This will set the corresponding tab states to the following mappings
        (`True`/`False`):

        - ``enable``: ``enable``/``disable``
        - ``disable``: ``disable``/``enable``
        - ``hide``: ``hide``/``enable``

        Arguments:
            idxs: The tab indexes to consider
            enable: Enable or Disable the tabs.
                Defaults to `None`, see above.
            disable: Disable or Enable the tabs.
                Defaults to `None`, see above.
            enable: Hide or Enable the tabs.
                Defaults to `None`, see above.

        See Also:
            Wraps `torder_change` with a different interface.
        '''
        lenable = []
        ldisable = []
        lhide = []
        assert len([b for b in (enable, disable, hide) if b is not None]) == 1, 'Select exactly one of enable/disable/hide'
        for idx in idxs:
            assert idx in self.wtabs, f'Invalid Tab ChangeIndex: {idx}'
            if enable is not None:
                if enable:
                    lenable.append(idx)
                else:
                    ldisable.append(idx)
            elif disable is not None:
                if disable:
                    ldisable.append(idx)
                else:
                    lenable.append(idx)
            elif hide is not None:
                if hide:
                    lhide.append(idx)
                else:
                    lenable.append(idx)
        return self.torder_change(enable=lenable, disable=ldisable, hide=lhide)

    def wtab(self, idx: str) -> mixin.ContainerWidget:
        '''Get the tab widget by identifier.

        This is just an helper function to get the correct widget value out of
        `wtabs`.

        Args:
            idx: The tab identifier.

        Note:
            In debug mode, this will fail if called with the wrong identifier.
            This check is skipped for performance on optimized mode.
        '''
        wtab = self.wtabs.get(idx, None)
        assert wtab is not None, f'Invalid Tab: {idx}'
        return wtab.widget

    def wselection(self) -> str:
        '''Search for the current selected tab.

        Returns:
            This functions searches for the currently selected tab, and returns its
            identifier (the key on the `wtabs` dictionary).
        '''
        assert self.__t_rindex is not None, f'{self}: Invalid rindex'
        assert self.__t_rindex[self.select()] in self.wtabs, f'Invalid Current Selection: {self.select()}'
        return self.__t_rindex[self.select()]

    def wselect(self, idx: str) -> None:
        '''Select a tab by identifier.

        Args:
            idx: The tab identifier.

        Note:
            In debug mode, this will fail if called with the wrong identifier.
            This check is skipped for performance on optimized mode.
        '''
        assert idx in self.wtabs, f'Invalid Tab Selection: {idx}'
        if __debug__:
            if idx not in self.torder.shown:
                warnings.warn(f'{self}: Selecting a disabled tab `{idx}`, this will enable it')
        self.select(tab_id=self.wtabs[idx].tk_idx)

    def _tabScrollUp(self, event=None):
        keys = self.torder.active
        selected = self.wselection()
        if selected == keys[0]:
            # First Tab
            if self.tWraparound:
                new_selected = keys[-1]
            else:
                new_selected = None
        else:
            selected_idx = keys.index(selected)
            new_selected = keys[selected_idx - 1]
        if new_selected:
            self.wselect(new_selected)

    def _tabScrollDown(self, event=None):
        keys = self.torder_get().active
        selected = self.wselection()
        if selected == keys[-1]:
            # Last Tab
            if self.tWraparound:
                new_selected = keys[0]
            else:
                new_selected = None
        else:
            selected_idx = keys.index(selected)
            new_selected = keys[selected_idx + 1]
        if new_selected:
            self.wselect(new_selected)


class NotebookUniform(Notebook):
    '''A tabbed interface to hold a series of uniform containers.

    This is a variant of the regular `Notebook` specially created to simplify
    the usual case where all the tabs are very similar (usually, they are the
    same underlying class).

    Args:
        tabids: A mapping of tab identifiers and tab titles.
        tabArgs: Arguments passed to the `Tab <model.NotebookTab>` object.

        All other keyword arguments are passed to the `setup_tab` function.

    See Also:
        `Notebook`: A fully generic version of this. Don't try to make the
        `setup_tab` function too complex, move to this widget instead.
    '''
    tabids: typing.Optional[typing.Mapping[str, str]] = None

    def __init__(self, *args, tabids: typing.Optional[typing.Mapping[str, str]] = None, **kwargs):
        self.tabids = self.tabids or tabids
        if self.tabids is None:
            raise exception.InvalidWidgetDefinition('Missing required tabids')
        super().__init__(*args, **kwargs)  # Notebook

    def setup_tabs(self, *args,
                   tabArgs: typing.Optional[typing.Mapping[str, typing.Any]] = None,
                   **kwargs: typing.Any,
                   ) -> typing.Mapping[str, model.NotebookTab]:
        '''Define the sub tabs, based on the common tab.

        Do not overwrite this unless you know what you are doing.

        To edit the common tab, see `setup_tab`.
        '''
        assert self.tabids is not None
        tabs = {}
        for tid, tname in self.tabids.items():
            tabs[tid] = Notebook.Tab(tname,
                                     self.setup_tab(tid, tname, *args, **kwargs),
                                     **(tabArgs or {}))
        return tabs

    def setup_tab(self, identifier: str, name: str, **kwargs) -> mixin.ContainerWidget:
        '''Define the common tab `ContainerWidget` here.

        Similar to `setup_tabs <Notebook.setup_tabs>`, but for a single tab widget.
        '''
        raise NotImplementedError


class Tree(ttk.Treeview, mixin.SingleWidget):
    '''A hierarchical multicolumn data display widget.

    This widget is capable of showing a hierarchy of data records (one per
    row). Each record can have multiple columns of data.
    Each record can store arbitrary data on its `Element <model.TreeElement>`,
    exposed on the `onSelect` function.

    The widget support selectable data records (see ``selectable``). See also
    `onSelect` for a callback triggered by this action.

    You can also unselect the current data record by clicking empty space (if
    available), or by holding :kbd:`Ctrl` when clicking the currently selected
    data record.
    This unselecting behaviour can be controlled independently, see
    ``selectable_unselect``).

    Note that if ``selectable`` is `True` and ``selectable_unselect`` is
    `False`, it is impossible for the user to unselect a data record (this
    might be a desirable behaviour).

    You can define a mapping between tags and the corresponding `model.TreeRow`
    configuration. When an element has multiple tags, the priority is the one
    on the dictionary. Internal tags that might be used for implementing other
    features always have less priority.

    See `Python ttk.Treeview <tkinter.ttk.Treeview>` and ``Tk``
    :tk:`ttk.Treeview <ttk_treeview.htm>` documentation.

    Args:
        variable: Use an externally defined variable, instead of creating a new
            one specific for this widget.
        label: The heading text for the first column, which includes the labels.
            Supports also a `Column <model.TreeColumn>` object directly.
        columns: Mapping between column identifiers and its titles. Supports
            also a direct map between identifier and `Column <model.TreeColumn>`.
        columns_stretch: Select which columns to stretch, a list of
            identifiers. `None` marks the label column.
            There are also special values:

            - `True` stretches all columns
            - `False` stretches no columns
            - `None` stretches only the label column. This is the default.

            There should be at least one stretchable column, or the container
            is not completely filled with the data. This is checked, but as a
            warning only.
        columns_autosize: Configure column automatic sizing, calling the
            `columns_autosize` function.

            - When `True` (the default), the function is called for all content changes.
            - When `False`, the function is never called automatically.
            - When `None`, there's a small checkbox on the upper left corner
              of the widget that controls if the function is called or not.
        columnConfig: Default configuration for basic string ``columns``
            mapping.
            This also applies to the label column. Advanced usage only.
            Overrides ``columns_stretch``.
        selectable: Should the user be able to select one of the values?
            Defaults to `False`.
        selectable_unselect: Should the user be able to unselect after
            selecting one of the values?
            Optional, follows ``selectable`` configuration.
        tags: A mapping of record tags to `Row` configuration.
            Optional.
        openlevel: The hierarchy level to open the elements. Defaults to ``1``,
            only the toplevel elements are opened.
            Set to ``0`` to close all, and to a really big number to open all.
        expand: Grow the widget to match the container grid size. This is
            usually supported for containers, but it is included here.
        style: Configure the widget style.

        styleID: Set a style identifier. Combined with the widget type in `RootWindow.register_styleID`.
        parent: The parent widget. Can be a `RootWindow` or another `mixin.ContainerWidget`.

    See Also:
        `Listbox`: Simplified version of this
    '''
    # TODO: Move Tree* classes here?
    Element = model.TreeElement  # Alias the tree element information
    Row = model.TreeRow  # Alias the tree row configurator
    Column = model.TreeColumn  # Alias the tree column configurator

    class __w_autosize(Checkbox):
        isAuto = None  # Isolate from GUI state, taken care in `set_gui_state`

    @dataclass
    class Style(model.WStyle):
        '''`Tree` style object.

        These are the style configurations:

        Args:
            show_headings: Show column title headings.
            show_labels: Show the first column, which includes the labels.
            selectable_nodoubleclick: Disable double-click binding. This is to
                avoid detecting spuriours double click events. Defaults to `True`.
            altbg: Show alternate backgrounds for each record.
            altbg_sindex: ``altbg`` initial alternate colour index.
            autosize_label: Label for the ``columns_autosize`` state checkbox.
            autosize_lcolumn_lspace: Spacing for each level indentation (parent items).
            autosize_lcolumn_osize: Width of the ``[+]`` button on each item.
            autosize_heading_multiplier: Multiplier to the regular label size,
                since this is a boldface. Use ``0`` if you want to ignore the
                heading label when automatically resizing.

        These are the colours:

        Args:
            colour_altbg: ``altbg`` alternate line colour.
                Used as the background colour.
        '''
        show_headings: bool = True
        show_labels: bool = True
        selectable_nodoubleclick: bool = True
        altbg: bool = True
        altbg_sindex: typing.Literal[0, 1] = 1
        # Colours
        colour_altbg: str = 'lightgrey'
        # AutoSize
        autosize_label: str = 'AutoSize'
        autosize_lcolumn_lspace: int = 20
        autosize_lcolumn_osize: int = 20
        autosize_heading_multiplier: int = 6

        def __post_init__(self):
            assert self.autosize_lcolumn_lspace >= 0
            assert self.autosize_lcolumn_osize >= 0
            assert self.autosize_heading_multiplier >= 0

    state_type = varTree
    __lines_alt: str = '__:lines-alt'

    lcolumn: model.TreeColumn
    '''The label `Column <model.TreeColumn>` object.'''
    wcolumns: typing.Mapping[str, model.TreeColumn]
    '''Map principal column identifiers to `Column <model.TreeColumn>` objects.

    See Also:
        `lcolumn` has the label column.
        `wcol` can map all the columns (including label column) and more.
    '''
    wdata: util.ReorderableDict[str, typing.Any]
    '''Map element id to `TreeElement <model.TreeElement>` data.

    This will have the same order as the GUI itself, it can be used as an
    ordered list of element id.
    '''

    def __init__(self, parent: mixin.ContainerWidget, *,
                 variable: typing.Optional[varTree] = None,
                 label: typing.Union[model.TreeColumn, str, None],
                 columns: typing.Mapping[str, typing.Union[model.TreeColumn, str]],
                 columns_stretch: typing.Union[None, bool, typing.Sequence[typing.Union[str, None]]] = None,
                 columns_autosize: typing.Optional[bool] = True,
                 columnConfig: typing.Optional[typing.Mapping[str, typing.Any]] = None,
                 selectable: bool = False,
                 selectable_unselect: typing.Optional[bool] = None,
                 tags: typing.Optional[typing.Mapping[str, model.TreeRow]] = None,
                 openlevel: int = 1,
                 expand: bool = True,
                 style: Style = Style(_default=True),
                 styleID: typing.Optional[str] = None,
                 **kwargs):
        columnConfig = columnConfig or {}
        self.wstyle = style
        if 'stretch' in columnConfig:  # Overriden manually, don't touch
            warnings.warn('Settings Override: "columnConfig" "stretch" overrides "columns_stretch"', stacklevel=2)
            columns_stretch = []
        if columns_stretch is False:  # Special Setting: No columns
            columns_stretch = []
        elif columns_stretch is True:  # Special Setting: All the columns
            columns_stretch = [None, *columns.keys()]
        elif columns_stretch is None:  # Special Setting: Only the label column
            columns_stretch = [None]
        else:
            if __debug__:
                if isinstance(columns_stretch, typing.Sequence) and len(columns_stretch) == 0:
                    warnings.warn('Stretch some columns, or the container is not fully filled', stacklevel=2)
                if columns_autosize in [True, None] and len(columns_stretch) == len(columns) + 1:
                    warnings.warn('Stretching all columns means autosize does not work well', stacklevel=2)
                if columns_autosize in [True, None] and (len(columns) + (0 if label is None else 1)) == 1:
                    warnings.warn('AutoSize for a single column is unnecessary', stacklevel=2)
        assert all(c is None or isinstance(c, str) for c in columns_stretch), f'Invalid Columns Stretch: "{columns_stretch}"'
        if __debug__:
            for k in ('identifier', 'name'):
                assert k not in columnConfig, f'Invalid Column Config Key "{k}"'
            if tags is not None and not isinstance(tags, typing.Mapping):
                raise exception.InvalidWidgetDefinition('Invalid tags configuration (not a mapping)')
        wcolumns = {}
        for cid, cobj in columns.items():
            if isinstance(cobj, model.TreeColumn):
                ccol = cobj
                cobj.identifier = cid
            elif isinstance(cobj, str):
                ccol = model.TreeColumn(
                    identifier=cid,
                    name=cobj,
                    **columnConfig,
                )
            else:
                raise exception.InvalidWidgetDefinition(f'Invalid column "{cid}": {cobj!r}')
            if ccol.identifier is None:
                raise exception.InvalidWidgetDefinition(f'Missing column id: "{cid}"')
            if len(columns_stretch) > 0:  # Override stretch value
                ccol.stretch = cid in columns_stretch
            wcolumns[cid] = ccol
        self._var_autosize: typing.Optional[var.Boolean] = None
        self.wcolumns = wcolumns
        if isinstance(label, model.TreeColumn):
            self.lcolumn = label
            self.lcolumn.identifier = '#0'
        else:
            self.lcolumn = model.TreeColumn(
                identifier='#0',
                name=label or '',
                **columnConfig,
            )
        if len(columns_stretch) > 0:  # Override stretch value
            self.lcolumn.stretch = None in columns_stretch
        if columns_autosize is None and tk.W in self.lcolumn.nameAnchor.value:
            warnings.warn('AutoSize: Make sure the label anchor is not on the CP.W side', stacklevel=2)
        wshow = []
        if self.wstyle.show_headings:
            wshow.append('headings')
        if self.wstyle.show_labels:
            wshow.append('tree')
        # Initialise Variable and Data
        self.init_single(variable)
        kwargs.update({
            'show': wshow,  # Override the given `show` argument
            'selectmode': tk.BROWSE if selectable else tk.NONE,
            'columns': list(self.wcolumns.keys()),
            'style': parent.wroot.register_styleID(styleID, 'Treeview', 'Heading', 'Item', 'Cell'),
        })
        assert isinstance(parent, tk.Misc), f'{parent} is not a valid parent widget'
        super().__init__(parent, **kwargs)  # ttk.Treeview
        self.wdata = util.ReorderableDict()
        __etags = dict(tags or {})
        # Selection
        if selectable_unselect is None:
            selectable_unselect = selectable
        assert isinstance(selectable_unselect, bool)
        if selectable:
            self.binding('<<TreeviewSelect>>', self._onSelect, key='__:selectable')
            # Disable Double-Click event, when selectable
            if self.wstyle.selectable_nodoubleclick:
                self.binding('<Double-Button-1>', fn.binding_disable, key='__:selectable:nodouble')
            if selectable_unselect:
                self.tidle(self.__wsel_unselect, key='__:selectable:unselect')
                self.binding('<Button-1>', self._onSelectUnselect, key='__:selectable:unselect')
        else:
            if selectable_unselect:
                logger.warning('%s: `selectable_unselect` without `selectable`', self)
        # Appearance
        if expand:
            self.grid(sticky=tk.NSEW)
        self.openlevel: int = openlevel  # TODO: Support opening all levels, explicit?
        # # Headers
        self._widget_autosize: typing.Optional[Tree.__w_autosize] = None
        for wcol in [self.lcolumn, *self.wcolumns.values()]:
            assert wcol.identifier is not None, f'{wcol!r}: Missing identifier'
            self.heading(wcol.identifier, text=wcol.name, image=wcol.image or '', anchor=wcol.nameAnchor.value,
                         command=self.__tree_header_click(wcol.identifier))
            self.column(wcol.identifier, anchor=wcol.cellAnchor.value, stretch=wcol.stretch)
        self.__autosize: typing.Optional[model.TimeoutIdle] = None
        if columns_autosize in [True, None]:
            self.__autosize = self.tidle(self.columns_autosize)
            self.binding('<Double-Button-1>', self.__tree_header_autoresize, key='__:autoresize:dbl_left')
            self.binding('<Button-2>', self.__tree_header_autoresize, key='__:autoresize:middle')  # Middle Mouse Button
            # Control Widget
            self._var_autosize = var.Boolean()
            if columns_autosize is None:
                # Pretend "self" is a ContainerWidget
                # This works due to the `place` usage, I think.
                wautosize_parent = typing.cast(mixin.ContainerWidget, self)
                wautosize = self.__class__.__w_autosize(wautosize_parent, variable=self._var_autosize,
                                                        label=self.wstyle.autosize_label,
                                                        takefocus=False)
                wautosize.place(anchor=tk.NW, relx=0, rely=0,  # Top Right (NW)
                                x=2, y=2,  # Delta (x Left, y Down)
                                height=18)   # Force Height
                wautosize.wparent = wautosize_parent  # Pretend "self" is a ContainerWidget
                self._widget_autosize = wautosize
            self._var_autosize.set(True)  # Default autosize state
        # # Alternate Backgrounds
        if self.wstyle.altbg:
            assert Tree.__lines_alt not in __etags
            __etags[Tree.__lines_alt] = model.TreeRow(background=self.wstyle.colour_altbg)
            # Minor issue: There is a nearly impercetible flash of badness with
            # `TimeoutIdle` that doesn't happen when calling the function
            # directly.
            # Possible fix: in `__tree_lsvisible`, pass an optional
            # `self.focus()` ID (when != '') and open/close state, that
            # replaces `wopen`.
            altbg = self.tidle(self.__tree_altbg, key='altbg')
            self.binding('<<TreeviewOpen>>', altbg.reschedule, key='__:altbg:open')
            self.binding('<<TreeviewClose>>', altbg.reschedule, key='__:altbg:close')
        # Configure element tags
        assert all(isinstance(k, str) for k in __etags.keys())
        assert all(isinstance(v, model.TreeRow) for v in __etags.values())
        self.__etags = typing.cast(typing.Mapping[str, model.TreeRow], __etags)
        # - First tags have priority
        for tag, trow in self.__etags.items():
            if __debug__:
                if self.wstyle.show_labels is False and trow.image not in (None, ''):
                    warnings.warn(f'{self}: Need `Style.show_labels`: Tag "{tag}"', stacklevel=2)
            self.tag_configure(tag, **trow.map_tk())
        # Trace variable state
        self.__gui_changed: bool = False  # Mark the GUI as changed already
        self.trace(self.__tree_set, trace_name=f'__:{__name__}')
        # Save bindtags
        self.__bindtags_enabled = self.bindtags()
        self.__bindtags_disabled = (str(self.winfo_toplevel()), 'all')
        assert self.__bindtags_enabled[-2:] == self.__bindtags_disabled, f'{self}: Weird bindtags: {self.__bindtags_enabled}'
        if __debug__:
            self.trace(self.__tree_check_wdata, trace_name='__:check:wdata')

    def _tree_get(self, variable: var.Variable) -> typing.Sequence[model.TreeElement]:
        '''Generate a `varTree` object, based on the variable.

        Should be reimplemented by subclasses that change the variable type.
        '''
        assert isinstance(variable, varTree)
        return variable.get()

    def __tree_lslevel(self, parent: typing.Optional[str] = None, _level: int = 0) -> typing.Iterable[typing.Tuple[str, int]]:
        '''Generate a list all widget ids and its corresponding tree level, in GUI order.

        The toplevel has level ``0``.

        See Also:
            `__tree_ls`: Generate a list of all widgets only, without the tree level.
            `__tree_lsvisible`: Generate a list of all visible widgets.
        '''
        for wtop in self.get_children(item=parent):
            yield wtop, _level
            yield from self.__tree_lslevel(parent=wtop, _level=_level + 1)

    def __tree_ls(self, parent: typing.Optional[str] = None) -> typing.Iterable[str]:
        '''Generate a list all widget ids, in GUI order.

        See Also:
            `__tree_lslevel`: Generate a list of all widgets and its tree level.
            `__tree_lsvisible`: Generate a list of all visible widgets.
        '''
        for wtop, _ in self.__tree_lslevel(parent):
            yield wtop

    def __tree_lsvisible(self, parent: typing.Optional[str] = None, _kids=None) -> typing.Iterable[str]:
        '''Generate a list of all visible widget ids, in GUI order.

        This guarantees the yielded values are visible to the user, as long as
        the tree is stable.

        See Also:
            `__tree_ls`: Generate a list of all widgets, even the not currently shown.
            `__tree_lslevel`: Generate a list of all widgets and its tree level.

        Note:
            When called directly from the ``<<TreeviewOpen>>`` or
            ``<<TreeviewClose>>`` event, this will "fail", that event runs too
            early. Use a `model.TimeoutIdle` in there to get the correct
            results.
        '''
        for wtop in _kids or self.get_children(item=parent):
            yield wtop
            wopen = self.item(wtop, option='open') == 1
            wkids = self.get_children(item=wtop)
            if len(wkids) > 0 and wopen:
                yield from self.__tree_lsvisible(parent=wtop, _kids=wkids)

    def __tree_clean(self, parent: typing.Optional[str] = None) -> None:
        self.delete(*self.__tree_ls(parent=parent))
        self.wdata.clear()

    def __tree_put(self, elements: typing.Sequence[model.TreeElement], *,
                   parent: typing.Optional[str] = None,
                   openlevel: typing.Optional[int] = None, _level: int = 0):
        parent_loc: typing.Optional[int] = None if parent is None else self.index(parent)
        openlevel = openlevel or self.openlevel
        for eid, element in enumerate(elements):
            # if __debug__:
            #     tpl_text = f'{parent or "__top__"}::#{eid}'
            #     logger.debug('%s %s: L:"%s" C:|%s|', ">" * (_level + 1), tpl_text, element.label, " ".join(element.columns))
            if element.columns is not None:
                # TODO: Support a dict with keys corresponding to the `self.wcolumns`, possible subset
                assert len(element.columns) == len(self.wcolumns), f'Invalid Column #{eid}: Size: E{len(element.columns)} W{len(self.wcolumns)}'
            child_loc: typing.Union[int, typing.Literal['end']]
            if parent_loc is None:
                child_loc = tk.END
            else:
                child_loc = parent_loc + eid
            # TODO: Migrate to a common function
            cid = self.insert(parent or '', child_loc,
                              text=element.label, values=tuple(element.columns or []),
                              open=_level < openlevel,
                              image=element.image or '',
                              tags=list(element.tags or []),
                              )
            if parent_loc is None:
                self.wdata[cid] = element.data
            else:
                assert isinstance(child_loc, int)
                self.wdata.insert(child_loc, key=cid, value=element.data)
            # if __debug__:
            #     logger.debug('%s ID: %s', "|" * (_level + 1), cid)
            if element.children:
                # if __debug__:
                #     logger.debug('%s Children: %d', "|" * (_level + 1), len(element.children))
                self.__tree_put(element.children,
                                parent=cid,
                                openlevel=openlevel, _level=_level + 1)

    def __tree_set(self, *args, **kwargs) -> None:
        assert self.variable is not None, f'{self!r}: Missing variable'
        value = self._tree_get(self.variable)
        if self.__gui_changed:
            # if __debug__:
            #     logger.debug('%s:   Keep GUI state', self)
            self.__gui_changed = False
        else:
            # if __debug__:
            #     logger.debug('%s: Change GUI state', self)
            self.__tree_clean()
            self.__tree_put(value)
        if self.wstyle.altbg:
            self._tidles['altbg'].schedule()
        if self._var_autosize and self._var_autosize.get() is True:
            assert self.__autosize is not None
            self.__autosize.schedule()
        self._tree_onset(value)

    def __tree_header_click(self, cid: str):
        # Search column by cid, or else it's the label column
        return lambda: self.onClickHeader(self.wcolumns.get(cid, self.lcolumn))

    def __tree_header_autoresize(self, event):
        # self.identify_region(event.x, event.y)  # Alternative, only for tk8.6
        if self.identify('region', event.x, event.y) != 'separator':
            return
        asizes = self.__columns_autosize()
        if event.num == 2:  # Check if it's Middle Mouse Button
            # if __debug__:
            #     logger.debug('Resize All Columns')
            self.columns_size(asizes)
        else:
            # wcol = self.wcol(self.identify_column(event.x, event.y))  # Alternative, only for tk8.6
            wcol = self.wcol(self.identify('column', event.x, event.y))
            # if __debug__:
            #     logger.debug('Column: %s', wcol)
            if not wcol.stretch:
                self.columns_size({wcol.identifier: asizes[wcol.identifier]})

    def set_gui_state(self, state: typing.Optional[model.GuiState] = None, **kwargs) -> model.GuiState:
        ''''''  # Do not document
        self_state = super().set_gui_state(state, **kwargs)
        if self._widget_autosize:
            self._widget_autosize.genabled(self_state.enabled)
        assert self_state.enabled is not None
        fn.state_bindtags(self, self_state.enabled,
                          bt_on=self.__bindtags_enabled,
                          bt_off=self.__bindtags_disabled)
        return self_state

    def __columns_autosize(self) -> typing.Mapping[str, int]:
        cols = {wcol.identifier: wcol for wcol in [self.lcolumn, *self.wcolumns.values()]}
        assert None not in cols
        # widths: Only the non-stretched("fixed") columns
        widths: typing.MutableMapping[str, int] = {cid: 0 for cid, wcol in cols.items() if cid and not wcol.stretch}
        if len(widths) == 0:
            # if __debug__:
            #     logger.debug('Nothing to Calculate')
            return {}
        # if __debug__:
        #     logger.debug('AutoSize Columns: %s', ' '.join(widths))
        cid: typing.Optional[str]
        for iid, ilevel in self.__tree_lslevel():
            item = self.item(iid)
            # if __debug__:
            #     logger.debug('| %5s | %r', iid, item)  # 5 should enough for the auto-generated ID
            # Label Column
            cid = '#0'
            if cid in widths:
                lsize = fn.label_size(len(str(item['text'])))  # Label Size
                psize = self.wstyle.autosize_lcolumn_lspace * (ilevel + 1)
                isize = 0 if item['image'] == '' else 16  # TODO: Calculate the image width, from the ID
                widths[cid] = max(widths[cid], lsize + psize + isize)
                # if __debug__:
                #     logger.debug('  %5s | %s | %d+%d+%d = %d', 'LPI', '#0', lsize, psize, isize, widths[cid])
            # Other Columns
            for cid, cval in zip(self.wcolumns, item['values']):
                if cid in widths:
                    lsize = fn.label_size(len(str(cval)))  # Label Size
                    widths[cid] = max(widths[cid], lsize)
                    # if __debug__:
                    #     logger.debug('  %5s | %s | %d = %d', 'L', cid, lsize, widths[cid])
        # logger.debug('AutoSize Delta Values')
        for cid in widths:
            assert cid is not None
            wcol = cols[cid]
            lsize = fn.label_size(len(wcol.name)) * self.wstyle.autosize_heading_multiplier  # Bold
            psize = self.wstyle.autosize_lcolumn_osize if wcol.identifier == '#0' else 0
            isize = wcol.image.width() if wcol.image else 0
            # if __debug__:
            #     logger.debug('  %s | %d + %d+%d+%d', cid, widths[cid], lsize, psize, isize)
            widths[cid] += lsize + psize + isize
        return widths

    def columns_size(self, widths: typing.Mapping[str, int]) -> None:
        '''Set the column widths.

        Args:
            widths: Mapping between column identifiers and column ``width``.
        '''
        assert all(cid in self.wcolumns or cid == '#0' for cid in widths)
        # logger.debug('Set Widths:')
        for cid, cwidth in widths.items():
            # logger.debug('> %s | %d', cid, cwidth)
            self.column(cid, width=cwidth)

    def columns_autosize(self) -> None:
        '''Automatically set the column widths.

        Uses heristics to find the "natural" column widths, it might not work
        perfectly.
        '''
        self.columns_size(self.__columns_autosize())

    def element_move(self, wid: str, newindex: int) -> bool:
        '''Move element on the `Tree` without recreating the state.

        This is a `wstate` alternative, for moving an existing element without
        having to regenerate the entire state. This has much better performance
        characteristics, particularly for big trees.

        For now this does not support any children elements anywhere.
        Everything must remain on the toplevel level.

        Arguments:
            wid: The element identifier to move.
            newindex: The new index for the element.

        Returns:
            `True` when the state is effectively changed, `False` otherwise.
            The reasons for not changing the state might be a no-op (the
            current and the new indexes are the same), or an invalid operation
            (moving an element outside the range).

        See Also:
            You can get the selected element using `wsid`.

            See `element_rm` to remove an element in an efficient way,
            `element_append`/`element_insert` to insert an element in an
            efficient way.
        '''
        pid = ''  # Only for the toplevel elements
        oldindex = self.index(wid)
        assert wid in self.wdata, f'{self}: Missing element "{wid}"'
        if __debug__:
            old_pid = self.parent(wid)
            assert old_pid == pid, f'{self}: Element "{wid}" child of "{old_pid}"'
            assert len(self.get_children(item=wid)) == 0, f'{self}: Element "{wid}" has children'
        if oldindex == newindex:
            return False  # No-Op
        if newindex < 0 or newindex >= len(self.wdata):
            return False  # Outside the range
        # if __debug__:
        #     logger.debug('%d > %d: T%d', oldindex, newindex, len(self.wdata))
        if __debug__:
            new_id = self.get_children(item=pid)[newindex]
            assert new_id == self.wdata.at(newindex)
            new_pid = self.parent(new_id)
            assert new_pid == pid, f'{self}: Moving "{wid}" into the middle of children ("{newindex}")'
        # Calculate Variable State
        state = self.wstate
        if __debug__:
            # Make sure the state is consistent with the GUI
            assert list(self.get_children(item=pid)) == list(self.wdata.keys())
            map__idx_state = {idx: sidx for idx, sidx in zip(self.get_children(item=pid), state)}
        state.insert(newindex, state.pop(oldindex))
        # Change the GUI State
        self.move(wid, pid, newindex)
        # Change the `wdata`
        self.wdata.move(newindex, key=wid)
        # Change the Variable State (no GUI changes)
        if __debug__:
            # Make sure the state is consistent with the GUI
            right_state = [map__idx_state[idx] for idx in self.get_children(item=pid)]
            delta = {idx: (r, s) for idx, (r, s) in enumerate(zip(right_state, state)) if r != s}
            if len(delta) != 0:
                logger.debug('G: %s', ' '.join(f'{idx}:{r}' for idx, (r, _) in delta.items()))
                logger.debug('B: %s', ' '.join(f'{idx}:{s}' for idx, (_, s) in delta.items()))
            assert len(delta) == 0
        self.__gui_changed = True
        self.wstate = state
        return True

    def element_rm(self, wid: str) -> bool:
        '''Remove element on the `Tree` without recreating the state.

        This is a `wstate` alternative, for removing an existing element without
        having to regenerate the entire state. This has much better performance
        characteristics, particularly for big trees.

        For now this does not support any children elements anywhere.
        The element must be on the toplevel and must not have any children.

        Arguments:
            wid: The element identifier to remove.

        Returns:
            Returns `True` if the element is actually removed (always).

        See Also:
            See `element_move` to move an element in an efficient way,
            `element_append`/`element_insert` to insert an element in an
            efficient way.
        '''
        assert wid in self.wdata, f'{self}: Missing element "{wid}"'
        assert self.parent(wid) == '', f'{self}: Removing "{wid}" not on the toplevel'
        assert len(self.get_children(item=wid)) == 0, f'{self}: Element "{wid}" has children'
        windex = self.index(wid)
        # Calculate Variable State
        state = self.wstate
        if __debug__:
            # Make sure the state is consistent with the GUI
            map__idx_state = {idx: sidx for idx, sidx in zip(self.get_children(item=''), state)}
        state[windex:windex + 1] = []
        # Change the GUI State
        self.delete(wid)  # Alternative: `self.detach`
        del self.wdata[wid]
        # Change the Variable State (no GUI changes)
        if __debug__:
            # Make sure the state is consistent with the GUI
            right_state = [map__idx_state[idx] for idx in self.get_children(item='')]
            delta = {idx: (r, s) for idx, (r, s) in enumerate(zip(right_state, state)) if r != s}
            if len(delta) != 0:
                logger.debug('G: %s', ' '.join(f'{idx}:{r}' for idx, (r, _) in delta.items()))
                logger.debug('B: %s', ' '.join(f'{idx}:{s}' for idx, (_, s) in delta.items()))
            assert len(delta) == 0
        self.__gui_changed = True
        self.wstate = state
        return True

    def element_append(self, element: model.TreeElement) -> str:
        '''Append an element on the `Tree` without recreating the state.

        This is a `wstate` alternative, for appending an existing element
        without having to regenerate the entire state. This has much better
        performance characteristics, particularly for big trees.

        The element must be on the toplevel and must not have any children.

        Arguments:
            element: The new element to append.

        Returns:
            Returns the element ID of the appended element.

        See Also:
            See `element_insert` to insert an element in an efficient way,
            `element_rm` to remove an element in an efficient way,
            `element_move` to move an element in an efficient way.
        '''
        return self.element_insert(element, where=None)

    def element_insert(self, element: model.TreeElement, where: typing.Optional[int] = 0) -> str:
        '''Insert an element on any index of the `Tree` without recreating the
        state.

        This is a `wstate` alternative, for inserting an existing element
        without having to regenerate the entire state. This has much better
        performance characteristics, particularly for big trees.

        For now this does not support any children elements anywhere.
        The element must be on the toplevel and must not have any children.

        Arguments:
            element: The new element to append.
            where: The new index for the new element.
                Defaults to ``0``, to insert at the beginning.

        Returns:
            Returns the element ID of the inserted element.

        See Also:
            See `element_append` to append an element in an efficient way,
            `element_rm` to remove an element in an efficient way,
            `element_move` to move an element in an efficient way.
        '''
        pid = ''
        assert pid == '', f'{self}: Appending element not on the toplevel'
        assert not element.children, f'{self}: Appending element with children'
        # Calculate Variable State
        state = self.wstate
        if __debug__:
            # Make sure the state is consistent with the GUI
            map__idx_state = {idx: sidx for idx, sidx in zip(self.get_children(item=pid), state)}
        location: typing.Union[int, typing.Literal['end']]
        if where is None:  # Append
            state.append(element.label)
            location = tk.END
        else:
            if where > len(state) or where < 0:
                raise ValueError(f'{self}: Invalid insertion: {where}')
            state.insert(where, element.label)
            location = where
        # Change the GUI State
        # TODO: Migrate to a common function
        cid = self.insert(pid, location,
                          text=element.label, values=tuple(element.columns or []),
                          open=True,  # New elements are always open
                          image=element.image or '',
                          tags=list(element.tags or []),
                          )
        if where is None:
            self.wdata[cid] = element.data
        else:
            assert isinstance(location, int)
            self.wdata.insert(location, key=cid, value=element.data)
        # Change the Variable State (no GUI changes)
        if __debug__:
            # Include the new element
            map__idx_state[cid] = element.label
            # Make sure the state is consistent with the GUI
            right_state = [map__idx_state[idx] for idx in self.get_children(item=pid)]
            delta = {idx: (r, s) for idx, (r, s) in enumerate(zip(right_state, state)) if r != s}
            if len(delta) != 0:
                logger.debug('G: %s', ' '.join(f'{idx}:{r}' for idx, (r, _) in delta.items()))
                logger.debug('B: %s', ' '.join(f'{idx}:{s}' for idx, (_, s) in delta.items()))
            assert len(delta) == 0
        self.__gui_changed = True
        self.wstate = state
        return cid

    def etag(self, wid: str,
             *tags: str,
             add: typing.Union[None, str, typing.Sequence[str]] = None,
             remove: typing.Union[None, str, typing.Sequence[str]] = None,
             ) -> typing.Set[str]:
        '''Manipulate tags for an element.

        There are two exclusive modes for this function to work:

        - The ``add``/``remove`` parameters allow for *delta* updates to the
          existing tags, acting as a set.
        - Otherwise, set ``tags`` as the only tags, overriding the current
          settings.
        '''
        if add is None and remove is None:
            new_tags = set(tags)
        else:
            # TODO: Implement this keeping the order of the original tags
            assert len(tags) == 0, f'{self}: Mixing tags with add/remove'
            old_tags = set(self.item(wid, 'tags'))
            # logger.debug('%s: wid=%s: Get %s', self, wid, old_tags)
            add_tags = set([] if add is None else [add] if isinstance(add, str) else add)
            remove_tags = set([] if remove is None else [remove] if isinstance(remove, str) else remove)
            new_tags = set(old_tags)
            # logger.debug('%s: wid=%s:   - %s', self, wid, remove_tags)
            new_tags.difference_update(remove_tags)
            # logger.debug('%s: wid=%s:   + %s', self, wid, add_tags)
            new_tags.update(add_tags)
        # logger.debug('%s: wid=%s: Set %s', self, wid, new_tags)
        if __debug__:
            delta_tags = new_tags - set(self.__etags.keys())
            assert len(delta_tags) == 0, f'{self}: Unknown tags: {" ".join(delta_tags)}'
        self.item(wid, tags=list(new_tags))
        return new_tags

    def __tree_altbg(self, *, remove: bool = False) -> None:
        '''Setup the alternate background, based on tags.

        Args:
            remove: Force removing all the backgrounds
        '''
        tname = Tree.__lines_alt
        index: int = self.wstyle.altbg_sindex
        for rid in self.__tree_lsvisible():
            if not remove and index % 2 == 0:
                self.etag(rid, add=tname)
            else:
                self.etag(rid, remove=tname)
            index += 1
        # if __debug__:
        #     # This should run only once, even with multiple changes
        #     if index > self.wstyle.altbg_sindex:
        #         logger.debug('%s: Calculated AltBG', self)

    if __debug__:
        def __tree_check_wdata(self, var, etype):
            '''Make sure wdata is correct'''
            wlst = list(Tree._Tree__tree_ls(self))
            wdata = list(self.wdata.keys())
            if isinstance(self, Listbox):  # TODO: Fixup this for nested trees too
                assert wlst == wdata, f'w={wlst} wdata={wdata}'

    def wcol(self, identifier: str) -> model.TreeColumn:
        '''Get the `Column <model.TreeColumn>` corresponding to the given identifier.

        The identifier can be one of the following formats:

        - ``#0``: The label column
        - Any of the `wcolumns` keys: The corresponding column
        - ``#n`` for any numeric ``n``: The index (starts on 1) for the visible column.

        Note:
            There is no support for the visible columns being different from
            the data columns, so ``#n`` always refers to the index into
            `wcolumns`.

        There is no Python documentation, see ``Tk`` :tk:`Treeview column
        identifiers <ttk_treeview.htm#M77>` documentation.

        Args:
            identifier: The column identifier.
                See above for all the possible formats.
        '''
        if identifier == '#0':
            column = self.lcolumn
        elif identifier in self.wcolumns:
            column = self.wcolumns[identifier]
        elif identifier.startswith('#'):  # This is an index into the "displaycolumns"
            # TODO: Suport display columns? This is technically wrong for now
            int_id = int(identifier[1:]) - 1  # Starts on 1
            assert int_id >= 0 and int_id < len(self.wcolumns)
            column = list(self.wcolumns.values())[int_id]
        else:
            raise ValueError(f'Unsupported ID: "{identifier}"')
        return column

    def wwhere(self, wid: str) -> typing.Tuple[typing.Optional[str], int]:
        '''Get the element location.

        Returns the element location in a non-ambigous manner.

        Args:
            wid: The element identifier to locate

        Returns:
            A tuple of parent element identifier (`None` when it is a toplevel
            element), and the index on its children.
        '''
        parent_tk = self.parent(wid)
        idx_tk = self.index(wid)
        parent_obj = None if parent_tk == '' else parent_tk
        assert parent_obj is None or parent_obj in self.wdata
        assert list(self.get_children(parent_obj or ''))[idx_tk] == wid
        if __debug__:
            if parent_obj is None:
                assert self.wdata.at(idx_tk) == wid
        return (
            parent_obj,
            idx_tk,
        )

    def wsid(self) -> typing.Optional[str]:
        '''Get the selected element identifier.

        Returns:
            `Element <model.TreeElement>` id, or `None` when nothing is selected.

            If the widget was created without the ``selectable`` flag, this always
            returns `None`.

        See Also:
            Use `wsel` to set the currently selected element identifier.
        '''
        selection = self.selection()
        if __debug__:
            selectmode = str(self['selectmode'])
            assert selectmode in [tk.BROWSE, tk.NONE], f'{self!r}: Invalid Selection Mode: {selectmode}'
            # logger.debug('Selection: %r', selection)
        if len(selection) == 0:
            # Skip un-selections
            # Usually the Tree contents changed...
            return None
        else:
            # Regular Selection
            assert len(selection) == 1, f'{self!r}: Invalid selection mode'
            treeid = selection[0]
            return treeid

    def wsel(self, wid: typing.Optional[str], *, see: bool = True, focus: bool = True) -> typing.Optional[str]:
        '''Set the currently selected element identifier.

        Defaults to ensuring the selected element is visible and focused, by
        scrolling the view. This is controlled by the ``see`` and ``focus``
        arguments, enabled by default.

        Args:
            wid: The element identifier to select. `None` to clear the
                selection.
            see: Ensure the element is visible.
            focus: Ensure the element has focus.

        Returns:
            Return the source ``wid`` argument.

        See Also:
            Use `wsid` to get the currently selected data.
        '''
        if wid is None:
            # Clear selection
            self.selection_remove(*self.wdata.keys())
        else:
            assert wid in self.wdata, f'{self}: Missing element "{wid}"'
            self.selection_set(wid)
            if see:
                self.see(wid)
            if focus:
                self.focus(wid)
        return wid

    def __wsel_unselect(self, event=None):
        ''''''  # Internal, do not document
        # TODO: Run `onSelect` with `None` values, to mark unselection?
        self.wsel(None)

    def wselection(self) -> typing.Optional[typing.Any]:
        '''Get the selected data.

        Returns:
            Since this supports only a single selection, return the selected
            value, or `None` when nothing is selected.

            If the widget was created without the ``selectable`` flag, this always
            returns `None`.

        See Also:
            Use `wselect` to set the currently selected data.
        '''
        wsid = self.wsid()
        return None if wsid is None else self.wdata[wsid]

    def wselect(self, selection: typing.Optional[typing.Any], *, see: bool = True) -> typing.Optional[str]:
        '''Set the current selection data.

        This will select the element with the given data. This will need to
        read the whole data, and does not support multiple elements with the
        same data. Avoid using this unless absolutely needed, use `wsel`
        directly.

        Args:
            selection: The element data to select. `None` clears the selection.
            see: Ensure the element is visible.

        Returns:
            Return the selected element identifier.

        See Also:
            Use `wsel` to select a specific identifier.
            Use `wselection` to get the currently selected data.
        '''
        if selection is None:
            wsid = None
        else:
            wsids = [wsid for wsid in self.__tree_ls() if self.wdata[wsid] == selection]
            assert len(wsids) > 0, f'{self}: Missing selection "{selection}"'
            assert len(wsids) == 1, f'{self}: Multiple selections "{selection}" > {wsids}'
            wsid = wsids[0]
        return self.wsel(wsid, see=see)

    def _onSelectUnselect(self, event) -> None:
        ''''''  # Internal, do not document
        if __debug__:
            selectmode = str(self['selectmode'])
            assert selectmode in [tk.BROWSE], f'{self!r}: Invalid Selection Mode: {selectmode}'
            # logger.debug('Selection: %r', self.selection())
        assert '__:selectable:unselect' in self._tidles
        region = self.identify_region(event.x, event.y)
        # if __debug__:
        #     logger.info('Click[%d:%d]: region=%r', event.x, event.y, region)
        unselect: bool = False
        if region == 'nothing':
            # Unselect: Click on nothing, empty "rows"
            unselect = True
        elif region in ('cell', 'tree') and model.EventModifier.Control.on(event) and self.identify_row(event.y) == self.wsid():
            # Unselect: Control-Click on the selected row/row label
            unselect = True
        if unselect:
            self._tidles['__:selectable:unselect'].schedule()

    def _onSelect(self, event=None) -> None:
        ''''''  # Internal, do not document
        selection: tuple = self.selection()
        if __debug__:
            selectmode = str(self['selectmode'])
            assert selectmode in [tk.BROWSE, tk.NONE], f'{self!r}: Invalid Selection Mode: {selectmode}'
            # logger.debug('Selection: %r', self.selection())
        if len(selection) == 0:
            # Skip
            # - NONE selectmode
            # - un-selections (usually the Tree contents changed)
            pass
        else:
            # Regular Selection
            assert len(selection) == 1, f'{self!r}: Invalid selection mode'
            treeid = selection[0]
            data = self.wdata[treeid]
            self.onSelect(treeid, data)

    def _tree_onset(self, value: typing.Sequence[model.TreeElement]) -> None:
        '''Callback to be executed when setting a different value.

        Available for subclass redefinition.
        '''
        pass

    def onClickHeader(self, column: model.TreeColumn):
        '''Callback to be executed when clicking any header.

        Defaults to doing nothing.

        Available for subclass redefinition.

        Args:
            column: The `Column <model.TreeColumn>` object
        '''
        pass

    def onSelect(self, treeid: str, data: typing.Any = None) -> None:
        '''Callback to be executed when clicking this widget.

        Defaults to doing nothing.

        Available for subclass redefinition.

        Args:
            treeid: The selected tree id
            data: The arbitrary data associated with the element. Defaults to `None`.
        '''
        pass


class Listbox(Tree):
    '''A listbox widget, a list of strings.

    This is a modern variation of the listbox, a way to display several rows of
    content (simple strings, in this case), and be able to select one at a
    time.

    The ``height`` can be hardcoded to a value, or it can vary with the
    contents. Note that the ``maxHeight`` is smaller than the amount of rows to
    display, no scrollbar is shown, but the list can be
    scrolled with the mouse wheel.
    The automatic variation on the height size (AKA auto-height) can be
    completely disabled by setting all height-related arguments to `None`. This
    is the default. The ``expand`` argument is set to `False` when the
    auto-height is disabled.

    Each string is centered on the list. This can be tweaked using the
    ``columnConfig`` argument.

    The state is a `list` of `str` values, `var.StringList`.

    This is a variation on the `Tree` widget, with a single column, a different
    variable type and some overriden default values.

    See also `Python ttk.Treeview <tkinter.ttk.Treeview>` and ``Tk``
    :tk:`ttk.Treeview <ttk_treeview.htm>` documentation.

    Args:
        variable: Use an externally defined variable, instead of creating a new
            one specific for this widget.
        label: The label to include besides the listbox. Can be given as a
            class variable.
            Optional, when given is show as the single column heading.
        columnConfig: Override configuration for the single column. Advanced
            usage only.
        height: If given, always show this quantity of rows.
            If it is `None`, the number of permanently shown rows will vary between
            ``minHeight`` and ``maxHeight``.
        minHeight: If ``height`` is `None`, make sure this number of rows is
            always visible.
            Optional, when `None`, there's no lower limit on the visible number
            of rows.
        maxHeight: If ``height`` is `None`, make sure there are no more
            visible rows than this number.
            Optional, when `None`, there's no upper limit on the visible
            number of rows.
        selectable: See `Tree` for its meaning.
            Defaults to `True`.
        style_altbg: See `Tree` for its meaning.
            Defaults to `False`.
        expand: See `Tree` for its meaning.
            Defaults to `False`, but interacts with the auto-height settings.
        style: Configure the widget style.

        styleID: Set a style identifier. Combined with the widget type in `RootWindow.register_styleID`.
        parent: The parent widget. Can be a `RootWindow` or another `mixin.ContainerWidget`.
    '''
    label: typing.Optional[str] = None

    @staticmethod
    def ListboxElement(string: str) -> model.TreeElement:
        '''Create a `model.TreeElement` from a single `str`.

        Since a `Listbox` is a specialized `Tree`, it needs this function to
        create the `Tree` state, not exposed on `Listbox`.
        '''
        return model.TreeElement(label=string, columns=[string], data=string)

    @dataclass
    class Style(Tree.Style):
        '''`Listbox` style object.

        See `Tree.Style` for upstream values, these are the differences:

        Args:
            altbg: Disabled by default.
            show_labels: As upstream, also hides the other column.

                This is necessary if you want to show row-level images on the
                `Listbox`, but it will have a gap even when there is no image,
                which is why it's not the default.
                This is verified on debug mode, see `etag <Tree.etag>`.

                Disabled by default.
        '''
        altbg: bool = False
        show_labels: bool = False

    state_type = var.StringList  # type: ignore  # Change the variable type

    def __init__(self, *args, variable: typing.Optional[var.StringList] = None,
                 label: typing.Optional[str] = None,
                 columnConfig: typing.Optional[typing.Mapping[str, typing.Any]] = None,
                 height: typing.Optional[int] = None, minHeight: typing.Optional[int] = None, maxHeight: typing.Optional[int] = None,
                 selectable: bool = True, expand: typing.Optional[bool] = None,  # Override
                 style: Style = Style(_default=True),
                 **kwargs):
        chosen_label = fn.label_fallback(label, self.label)
        if style._default:
            style.show_headings = chosen_label is not None
        if style.show_labels:
            # Hide the "label" column
            assert 'displaycolumns' not in kwargs, 'Listbox.Style.show_labels: Overriding displaycolumns'
            kwargs['displaycolumns'] = []
        kwargs.update({
            'label': chosen_label,
            'variable': variable,
            'selectable': selectable,  # Override
            'columns': {'label': chosen_label or 'Label'},  # Single Column "label"
            'style': style,
            'columns_autosize': False,  # Single Column
        })
        # Configure height
        self.heightRange: typing.Optional[typing.Tuple[typing.Optional[int], typing.Optional[int]]]
        if height is None:
            self.heightRange = minHeight, maxHeight
        else:
            kwargs['height'] = height  # Hardcode the height value
            self.heightRange = None
        if height or minHeight or maxHeight and expand is None:
            # Don't expand when the fixed or varying height is set
            expand = False
        # Configure (single) column
        # - Don't use `#0` since that is not properly centered, it has the tree
        #   elements in there, even hidden.
        cConfig = {
            'anchor': tk.CENTER,
            'stretch': True,
        }
        if expand is not None:
            kwargs['expand'] = expand
        if columnConfig:
            cConfig.update(columnConfig)
        super().__init__(*args, **kwargs)  # Tree
        # Make sure cConfig keys match options for `tkinter.ttk.Treeview.column`
        self.column('label', **cConfig)  # type: ignore

    def _tree_get(self, variable: var.Variable) -> typing.Sequence[model.TreeElement]:
        return [self.ListboxElement(e) for e in variable.get()]

    def _tree_onset(self, value: typing.Sequence[model.TreeElement]) -> None:
        if self.heightRange is not None:
            minHeight, maxHeight = self.heightRange
            wsize = None
            if minHeight:
                wsize = max(minHeight, len(value))
            if maxHeight:
                wsize = min(maxHeight, wsize or len(value))
            if wsize:
                if __debug__:
                    logger_model_layout.debug('%s: Auto Height: %s', self, wsize)
                self.configure(height=wsize)

    def wsidx(self) -> typing.Optional[int]:
        '''Get the selected element identifier index.

        Returns:
            `None` when nothing is selected, or the index for the selected
            element on `wdata`.

            If the widget was created without the ``selectable`` flag, this always
            returns `None`.

        See Also:
            See the upstream `wsid` function.
        '''
        wsid = self.wsid()
        if wsid is None:
            return None
        else:
            if __debug__:
                parent, idx = self.wwhere(wsid)
                assert parent is None, f'{self}: Selected element not on the toplevel'
                assert idx == self.wdata.index(wsid)
            return self.wdata.index(wsid)

    def elementAppend(self, string: str) -> str:
        '''Append a string to the `Listbox` without recreating the state.

        Uses `ListboxElement` to create the necessary `model.TreeElement`.

        See Also:
            See the underlying `Tree.element_append` function for usage and
            return value.
        '''
        return super().element_append(self.ListboxElement(string))

    def elementInsert(self, string: str, where: typing.Union[None, int, str] = 0) -> str:
        '''Insert a string on the `Listbox` without recreating the state.

        Uses `ListboxElement` to create the necessary `model.TreeElement`.

        See Also:
            See the underlying `Tree.element_insert` function for usage and
            return value.
        '''
        widx: typing.Optional[int]
        if isinstance(where, str):
            widx = self.wdata.index(where)
            if __debug__:
                _parent, _widx = self.wwhere(where)
                assert _parent is None, f'{self}: Selected element not on the toplevel'
                assert widx == _widx
        else:
            widx = where
        return super().element_insert(self.ListboxElement(string), widx)

    def genRemoveSelected(self) -> typing.Callable:
        '''Generate a function to remove the currently selected element.

        Returns:
            A function that can be used as callback for ``onClick`` functions.
        '''
        def genRemoveSelected(event: typing.Any = None) -> bool:
            wsid = self.wsid()
            if wsid is None:
                return False
            else:
                rval = self.element_rm(wsid)
                if rval:
                    pass  # TODO: Re-Select some element?
                return rval
        return genRemoveSelected

    def genRemoveAll(self) -> typing.Callable:
        '''Generate a function to remove all elements.

        Returns:
            A function that can be used as callback for ``onClick`` functions.
        '''
        def genRemoveAll(event: typing.Any = None) -> bool:
            self.wstate = []
            return True
        return genRemoveAll

    def genMoveSelected(self, delta: typing.Union[int, typing.Literal['top'], typing.Literal['bottom']]) -> typing.Callable:
        '''Generate a function to move the currently selected element to a new
        index.

        The ``delta`` argument difference between the current index and the
        intended location. There are also two special values:

        - ``top``: Move the element to the top of the list
        - ``bottom``: Move the element to the bottom of the list.

        Arguments:
            delta: Where to move the element. See above.

        Returns:
            A function that can be used as callback for ``onClick`` functions.
        '''
        if delta == 0:
            raise ValueError(f'Invalid delta: {delta}')

        def genMoveSelected(event: typing.Any = None) -> bool:
            wsid = self.wsid()
            if wsid is None:
                return False
            else:
                # TODO: Test this logic
                if delta == 'top':
                    newidx = 0
                elif delta == 'bottom':
                    newidx = len(self.wdata) - 1
                else:
                    oldidx = self.index(wsid)
                    newidx = oldidx + delta
                rval = self.element_move(wsid, newidx)
                if rval:
                    # Re-Select the old element
                    self.wsel(wsid)
                return rval
        return genMoveSelected


class FramePaned(ttk.PanedWindow, mixin.ContainerWidget):
    '''A frame to hold other widgets, with user-controllable relative sizes.

    This is similar to a `FrameUnlabelled`, restricted to horizontal or
    vertical layouts, but where the interfaces between the children can be
    adjusted by the user, to resize them at will.

    This allows some child widgets to be hidden, by resizing the other panes to
    fully occupy the widget area.

    When resizing this widget, the space difference is distributed among child
    widgets, using ``weight``. The default is ``1`` for all children, all are
    resized equally. When setting ``0`` as weight, the child widget will not be
    automatically resized.
    This weight can be defined in four ways (mappings will be merged), from
    less to more specific:

    - Argument ``weight``: Use this value for all widgets.
    - Object parameter ``pweigth``: Use this value for all widgets.
    - Argument ``weights``: Use the mapping between widget names and its
      weight.
    - Object parameter ``pweigths``: Use the mapping between widget names and
      its weight.

    Note that using this with more than two children can be confusing for the
    users, particularly when resizing takes place.

    There is no Python documentation, see ``Tk`` :tk:`ttk.PanedWindow
    <ttk_panedwindow.htm>` documentation.

    Args:
        layout: The orientation of the child widgets.
            Restricted to `VERTICAL` or `HORIZONTAL`.
        orient: Alias for "layout".
        weight: The weight for each children widget. Optional, defaults to 1.
        weights: Per-child widget. Optional, defaults to the common "weight".

        styleID: Set a style identifier. Combined with the widget type in `RootWindow.register_styleID`.
        parent: The parent widget. Can be a `RootWindow` or another `mixin.ContainerWidget`.

    Note:
        The ``layout``/``orient`` argument has similar semantics to ``layout``
        argument on other frame types.

    See Also:
        - `FrameUnlabelled`, `FrameLabelled`: Similar versions, without user
          control over sizing.
    '''
    layout: typing.Optional[str] = None
    '''Default value for `layout <mixin.ContainerWidget.layout>`.'''
    layout_padable = False
    '''Default value for `layout_padable <mixin.ContainerWidget.layout_padable>`.'''
    pweigth: int = 1
    '''Default weight for all widgets.

    See complete documentation on the description above.
    '''
    pweigths: typing.Optional[typing.Mapping[str, int]] = None
    '''Map widget names to weight.

    See complete documentation on the description above.
    '''

    def __init__(self, parent: mixin.ContainerWidget,
                 *args,
                 orient: typing.Optional[varOrientation] = None,
                 weight: typing.Optional[int] = None,
                 weights: typing.Optional[typing.Mapping[str, int]] = None,
                 styleID: typing.Optional[str] = None,
                 **kwargs):
        # Orientation can be given as the layout
        # But the ContainerWidget layout is always None
        # No Default Orientation, must be given somewhere
        orientation = kwargs.pop('layout', None) or orient or self.layout
        assert orientation in (HORIZONTAL, VERTICAL), 'Invalid Orientation: {orientation}'
        if typing.TYPE_CHECKING:
            orientation = typing.cast(varOrientation, orientation)
        assert isinstance(parent, tk.Misc), f'{parent} is not a valid parent widget'
        super().__init__(parent, orient=orientation,
                         style=parent.wroot.register_styleID(styleID, 'TPanedwindow', 'Sash'),
                         )  # ttk.PanedWindow
        self.init_container(*args, layout=None, **kwargs)
        # Per-Widget Weight Override
        all_weights: typing.MutableMapping[str, int] = {}
        if self.pweigths is not None:
            all_weights.update(self.pweigths)
        if weights is not None:
            all_weights.update(weights)
        fallback_weight: int = weight if weight is not None else self.pweigth
        for wname, raw_widget in self.widgets.items():
            widget = raw_widget.wproxy or raw_widget  # Use the proxy widget, if applies
            wweight = all_weights.get(wname, fallback_weight)
            assert isinstance(widget, tk.Widget)
            self.add(widget,
                     weight=wweight)
        assert len(self.panes()) == len(self.widgets)
        # Save bindtags
        self.__bindtags_enabled = self.bindtags()
        self.__bindtags_disabled = (str(self.winfo_toplevel()), 'all')
        assert self.__bindtags_enabled[-2:] == self.__bindtags_disabled, f'{self}: Weird bindtags: {self.__bindtags_enabled}'

    def set_gui_state(self, state: typing.Optional[model.GuiState] = None, _sub: bool = True, **kwargs) -> model.GuiState:
        ''''''  # Do not document
        self_state = super().set_gui_state(state, _sub=_sub, **kwargs)
        assert self_state.enabled is not None
        fn.state_bindtags(self, self_state.enabled,
                          bt_on=self.__bindtags_enabled,
                          bt_off=self.__bindtags_disabled)
        return self_state


class ScrolledWidget(ttk.Frame, mixin.ProxyWidget):
    '''A proxy widget to include functional scrollbars.

    This is a proxy frame, with a single child widget, which includes
    functional scrollbars. Both horizontal and vertical scrollbars are
    supported (depending on the child widget).

    A corner widget to hide the "blank" space between scrollbars is
    automatically included if needed, this is implemented as a so-called
    "sizegrip".

    There is no Python documentation, see ``Tk`` :tk:`ttk.Scrollbar
    <ttk_scrollbar.htm>` and :tk:`ttk.Sizegrip <ttk_sizegrip.htm>`
    documentation.

    The scrollbars can be forced to be shown, or they can be configured in
    automatic mode, independenty. This will show or hide the scrollbars as
    needed. This amounts to hide them when the child widget needs no
    scrollbars. The default behaviour is this automatic showing/hiding for both
    scrollbars.

    Note:
        Only a small subset of `SingleWidget` support scrollbars. They are
        referenced on its documentation. See `Scrolled` for an alternative.

        Like any `ProxyWidget`, creating an instance of this type will return a
        ``childClass`` instance.

        If you want to access the functions defined in this class, you need to
        use the `wproxy <mixin.MixinWidget.wproxy>` reference.
        See also the `proxee <mixin.MixinWidget.proxee>` reference to get a
        reference to the child widget from the proxy.

    Args:
        childClass: The children class (called to create the child widget).
            Must be a `SingleWidget`.
        scrollVertical: Show the vertical scrollbar.
            Use a `bool` to force a state, or `None` to automatically show or hide the scrollbar.
            Defaults to `None`.
        scrollHorizontal: Include a horizontal scrollbar.
            Use a `bool` to force a state, or `None` to automatically show or hide the scrollbar.
            Defaults to `None`.
        scrollExpand: Expand the parent widget.
            This is analogous to the ``expand`` argument on
            `mixin.ContainerWidget.init_container`.

        proxyStyleID: Set a style identifier for the proxy frame. Combined with
            the widget type in `RootWindow.register_styleID`.
        parent: The parent widget. Can be a `RootWindow` or another `mixin.ContainerWidget`.

    All other arguments are passed to the children ``childClass`` invocation.

    See Also:
        There is some anciliary Python documentation in `scrollable widget
        options
        <https://docs.python.org/3.8/library/tkinter.ttk.html#scrollable-widget-options>`_.

        Use `Scrolled` if the widget does not support direct scrollbars.

    ..
        Python 3.8 is missing this reference, included in Python 3.9:

        :ref:`scrollable widget options <python:Scrollable-Widget-Options>`
    '''
    class __w_scrollbar(ttk.Scrollbar):
        def __init__(self, parent, **kwargs):
            super().__init__(parent, **kwargs)
            # Bare minimum to be a "proper" widget
            self.wparent = parent

    class __w_corner(ttk.Sizegrip):
        def __init__(self, parent, **kwargs):
            super().__init__(parent, **kwargs)
            # Bare minimum to be a "proper" widget
            self.wparent = parent

    def __init__(self, parent: mixin.ContainerWidget, childClass: typing.Type[mixin.SingleWidget],
                 *args,
                 scrollVertical: typing.Optional[bool] = None,
                 scrollHorizontal: typing.Optional[bool] = None,
                 scrollExpand: bool = True,
                 proxyStyleID: typing.Optional[str] = None,
                 **kwargs):
        assert childClass is not ScrolledWidget, f'{parent}: Do not nest ScrolledWidget'
        if __debug__:
            badkeys = ('xscrollcommand', 'yscrollcommand')
            assert all(k not in kwargs for k in badkeys), f'Invalid Keys: {" ".join(badkeys)}'

        # Current Frame
        assert isinstance(parent, tk.Misc), f'{parent} is not a valid parent widget'
        super().__init__(parent,
                         style=parent.wroot.register_styleID(proxyStyleID, 'TFrame'),
                         )  # ttk.Frame
        rweight = [1]
        cweight = [1]

        # Widgets
        self.__vbar: typing.Optional[ttk.Scrollbar] = None
        self.__hbar: typing.Optional[ttk.Scrollbar] = None
        self.__corner: typing.Optional[ttk.Sizegrip] = None
        if scrollHorizontal in (None, True):
            self.__hbar = self.__w_scrollbar(self, orient=HORIZONTAL)
            kwargs['xscrollcommand'] = fn.scrollGenCommand(self.__hbar.set, scrollHorizontal, 'hstate',
                                                           fn_scrollstate=self.set_scroll_state)
            cweight.append(0)
            # Save bindtags
            self.__hbar_bindtags_enabled = self.__hbar.bindtags()
            self.__hbar_bindtags_disabled = (str(self.__hbar.winfo_toplevel()), 'all')
            assert self.__hbar_bindtags_enabled[-2:] == self.__hbar_bindtags_disabled, f'{self}: Weird hbar bindtags: {self.__hbar_bindtags_enabled}'
        if scrollVertical in (None, True):
            self.__vbar = self.__w_scrollbar(self, orient=VERTICAL)
            kwargs['yscrollcommand'] = fn.scrollGenCommand(self.__vbar.set, scrollVertical, 'vstate',
                                                           fn_scrollstate=self.set_scroll_state)
            rweight.append(0)
            # Save bindtags
            self.__vbar_bindtags_enabled = self.__vbar.bindtags()
            self.__vbar_bindtags_disabled = (str(self.__vbar.winfo_toplevel()), 'all')
            assert self.__vbar_bindtags_enabled[-2:] == self.__vbar_bindtags_disabled, f'{self}: Weird vbar bindtags: {self.__vbar_bindtags_enabled}'
        if scrollVertical in (None, True) and scrollVertical in (None, True):
            # This is not stricly necessary, but nice to have.
            self.__corner = self.__w_corner(self, cursor='', takefocus=False)
            # Disable sizegrip events
            self.__corner.bind('<Button-1>', fn.binding_disable)
        cwidget = childClass(self, *args, **kwargs)  # type: ignore

        # State
        self.state_type = cwidget.state_type
        self.init_single(cwidget.variable)  # Wrap child widget variable
        # Special Widget state
        self.wparent = parent

        # Glue scrollbars with child widget
        if self.__hbar:
            assert isinstance(cwidget, tk.XView), f'Invalid Child Widget: {cwidget!r}'
            self.__hbar['command'] = cwidget.xview
        if self.__vbar:
            assert isinstance(cwidget, tk.YView), f'Invalid Child Widget: {cwidget!r}'
            self.__vbar['command'] = cwidget.yview

        # Layout
        if scrollExpand:
            self.grid(sticky=tk.NSEW)
        assert isinstance(cwidget, tk.Grid), f'Invalid Child Widget: {cwidget!r}'
        cwidget.grid(row=0, column=0, sticky=tk.NSEW)
        self.set_scroll_state(scrollHorizontal or None, scrollVertical or None)
        # Emulate `fn.configure_grid(self, rweight, cweight)`
        for ridx, weight in enumerate(rweight):
            self.rowconfigure(ridx, weight=weight)
        for cidx, weight in enumerate(cweight):
            self.columnconfigure(cidx, weight=weight)

        # Proxy all access to `cwidget`
        self.proxee = cwidget

    def set_gui_state(self, state: typing.Optional[model.GuiState] = None, **kwargs) -> model.GuiState:
        ''''''  # Do not document
        self_state = super().set_gui_state(state, **kwargs)
        if __debug__:
            logger_autostate.debug('%s: State %s', self, self_state)
        states_tk = model.GuiState(enabled=self_state.enabled).states_tk()
        # Glue scrollbars with child widget GUI state
        # Must change the state and fully disable events with `bindtags`
        if self.__hbar:
            if __debug__:
                logger_autostate.debug('> H Bar')
            self.__hbar.state(states_tk)
            assert self_state.enabled is not None
            fn.state_bindtags(self.__hbar, self_state.enabled,
                              bt_on=self.__hbar_bindtags_enabled,
                              bt_off=self.__hbar_bindtags_disabled)
        if self.__vbar:
            if __debug__:
                logger_autostate.debug('> V Bar')
            self.__vbar.state(states_tk)
            assert self_state.enabled is not None
            fn.state_bindtags(self.__vbar, self_state.enabled,
                              bt_on=self.__vbar_bindtags_enabled,
                              bt_off=self.__vbar_bindtags_disabled)
        return self_state

    def get_scroll_state(self) -> typing.Tuple[bool, bool]:
        '''Get the current scrollbar visibility state.

        If the scrollbar is completely disabled, `False` is returned.

        This is a tuple with the state for both scrollbars, horizontal and
        vertical.

        See Also:
            - `set_scroll_state`: Change the current state
        '''
        return (
            self.__hbar is not None and bool(self.__hbar.grid_info()),
            self.__vbar is not None and bool(self.__vbar.grid_info()),
        )

    def set_scroll_state(self, hstate: typing.Optional[bool] = None, vstate: typing.Optional[bool] = None) -> None:
        '''Change the current scrollbar visibility state.

        This can change both horizontal and vertical state independently. The
        corner widget is managed automatically.

        Args:
            hstate: If not `None`, set the horizontal scrollbar visibility.
            vstate: If not `None`, set the vertical scrollbar visibility.

        See Also:
            - `get_scroll_state`: Get the current state
        '''
        if hstate is not None and self.__hbar is not None:
            h_wgrid = self.__hbar.grid_info()
            if hstate:
                if not h_wgrid:
                    self.__hbar.grid(row=1, column=0, sticky=tk.EW)
                    # if __debug__:
                    #     logger.debug('%s: Show hbar', self)
            else:
                if h_wgrid:
                    # if __debug__:
                    #     logger.debug('%s: Hide hbar', self)
                    self.__hbar.grid_remove()
        if vstate is not None and self.__vbar is not None:
            v_wgrid = self.__vbar.grid_info()
            if vstate:
                if not v_wgrid:
                    self.__vbar.grid(row=0, column=1, sticky=tk.NS)
                    # if __debug__:
                    #     logger.debug('%s: Show vbar', self)
            else:
                if v_wgrid:
                    # if __debug__:
                    #     logger.debug('%s: Hide vbar', self)
                    self.__vbar.grid_remove()
        if self.__corner is not None:
            isHorizontal = self.__hbar is not None and self.__hbar.grid_info()
            isVertical = self.__vbar is not None and self.__vbar.grid_info()
            c_wgrid = self.__corner.grid_info()
            if isHorizontal and isVertical:
                if not c_wgrid:
                    self.__corner.grid(row=1, column=1)
                    # if __debug__:
                    #     logger.debug('%s: Show corner', self)
            else:
                if c_wgrid:
                    # if __debug__:
                    #     logger.debug('%s: Hide corner', self)
                    self.__corner.grid_remove()

    def scrollTo(self, *,
                 x: typing.Optional[float] = None,
                 y: typing.Optional[float] = None,
                 anchor: model.CP = model.CP.center,
                 ) -> None:
        '''Adjust the scrollbars to show fractions of the total size.

        The anchor to consider the adjustment is configurable as ``anchor``.

        Arguments:
            x: Fraction of the total size to show on anchor, as a floating
                point. Adjusts the horizontal scroll position. Optional.
            y: Fraction of the total size to show on the anchor, as a floating
                point. Adjusts the vertical scroll position. Optional.
            anchor: The anchor to adjust the fractional positions.
        '''
        assert self.proxee is not None, f'{self}: Proxee Widget manipulation too soon'
        assert isinstance(self.proxee, tk.Widget)
        if anchor not in model.CP_ScrollAnchor:
            raise ValueError(f'Unsupported anchor: {anchor}')
        if __debug__:
            if x is not None and self.__hbar is None:
                warnings.warn('{self}: scrolling without horizontal scrollbar', stacklevel=2)
            if y is not None and self.__vbar is None:
                warnings.warn('{self}: scrolling without vertical scrollbar', stacklevel=2)
        if __debug__:
            logger.debug(' < %s', self.proxee.wview)
        fn.scrollTo(self.proxee,
                    x=x, y=y, anchor=anchor)
        if __debug__:
            logger.debug(' > %s', self.proxee.wview)


class Scrolled(ttk.Frame, mixin.ProxyWidget):
    '''A proxy widget to include functional scrollbars that works for all widgets.

    This is a proxy frame, with a child widget, which includes functional
    scrollbars. Both horizontal and vertical scrollbars are supported
    (depending on the child widget).
    Uses the `Canvas` method, include the widget on the canvas and scroll the
    canvas. Avoids overlapping errors by using an extra frame.

    A corner widget to hide the "blank" space between scrollbars is
    automatically included if needed, this is implemented as a so-called
    "sizegrip".

    There is no Python documentation, see ``Tk`` :tk:`ttk.Scrollbar
    <ttk_scrollbar.htm>` and :tk:`ttk.Sizegrip <ttk_sizegrip.htm>`
    documentation.

    The scrollbars can be forced to be shown, or they can be configured in
    automatic mode, independenty. This will show or hide the scrollbars as
    needed. This amounts to hide them when the child widget needs no
    scrollbars. The default behaviour is this automatic showing/hiding for both
    scrollbars.

    Note:
        Like any `ProxyWidget`, creating an instance of this type will return a
        ``childClass`` instance.

        If you want to access the functions defined in this class, you need to
        use the `wproxy <mixin.MixinWidget.wproxy>` reference.
        See also the `proxee <mixin.MixinWidget.proxee>` reference to get a
        reference to the child widget from the proxy.

    Args:
        childClass: The children class (called to create the child widget).
        scrollVertical: Show the vertical scrollbar.
            Use a `bool` to force a state, or `None` to automatically show or hide the scrollbar.
            Defaults to `None`.
        scrollHorizontal: Include a horizontal scrollbar.
            Use a `bool` to force a state, or `None` to automatically show or hide the scrollbar.
            Defaults to `None`.
        scrollExpand: Expand the parent widget.
            This is analogous to the ``expand`` argument on
            `mixin.ContainerWidget.init_container`.
        argCanvas: Extra arguments passed to the canvas widget.

        proxyStyleID: Set a style identifier for the proxy frame. Combined with
            the widget type in `RootWindow.register_styleID`.
        parent: The parent widget. Can be a `RootWindow` or another `mixin.ContainerWidget`.

    All other arguments are passed to the children ``childClass`` invocation.

    See Also:
        Use `ScrolledWidget` if the widget supports direct scrollbars.
    '''
    # Extra documentation:
    # - https://web.archive.org/web/20200805122438/http://effbot.org/zone/tkinter-scrollbar-patterns.htm
    # - https://stackoverflow.com/questions/3085696/adding-a-scrollbar-to-a-group-of-widgets-in-tkinter
    # - https://stackoverflow.com/questions/16188420/tkinter-scrollbar-for-frame
    class __w_icframe(ttk.Frame):
        def __init__(self, *, parent, wroot):
            super().__init__(parent)
            # Bare minimum to be a "proper" widget
            self.wroot = wroot

    class __w_scrollbar(ttk.Scrollbar):
        def __init__(self, parent, **kwargs):
            super().__init__(parent, **kwargs)
            # Bare minimum to be a "proper" widget
            self.wparent = parent

    class __w_corner(ttk.Sizegrip):
        def __init__(self, parent, **kwargs):
            super().__init__(parent, **kwargs)
            # Bare minimum to be a "proper" widget
            self.wparent = parent

    def __init__(self, parent: mixin.ContainerWidget, childClass: typing.Type[mixin.ContainerWidget],
                 *args,
                 scrollVertical: typing.Optional[bool] = None,
                 scrollHorizontal: typing.Optional[bool] = None,
                 scrollExpand: bool = True,
                 argCanvas: typing.Optional[typing.Mapping[str, typing.Any]] = None,
                 __fps: int = 30,
                 proxyStyleID: typing.Optional[str] = None,
                 **kwargs):
        assert childClass is not Scrolled, f'{parent}: Do not nest Scrolled'
        assert 'xscrollcommand' not in (argCanvas or {}) and 'yscrollcommand' not in (argCanvas or {})

        # Current Frame
        assert isinstance(parent, tk.Misc), f'{parent} is not a valid parent widget'
        super().__init__(parent,
                         style=parent.wroot.register_styleID(proxyStyleID, 'TFrame'),
                         )  # ttk.Frame
        rweight = [1]
        cweight = [1]

        # Widgets
        self.__vbar: typing.Optional[ttk.Scrollbar] = None
        self.__hbar: typing.Optional[ttk.Scrollbar] = None
        self.__corner: typing.Optional[ttk.Sizegrip] = None
        ckwargs = dict(argCanvas or {})
        if scrollHorizontal in (None, True):
            self.__hbar = self.__w_scrollbar(self, orient=tk.HORIZONTAL)
            ckwargs['xscrollcommand'] = fn.scrollGenCommand(self.__hbar.set, scrollHorizontal, 'hstate',
                                                            fn_scrollstate=self.set_scroll_state)
            cweight.append(0)
            # Save bindtags
            self.__hbar_bindtags_enabled = self.__hbar.bindtags()
            self.__hbar_bindtags_disabled = (str(self.__hbar.winfo_toplevel()), 'all')
            assert self.__hbar_bindtags_enabled[-2:] == self.__hbar_bindtags_disabled, f'{self}: Weird hbar bindtags: {self.__hbar_bindtags_enabled}'
        if scrollVertical in (None, True):
            self.__vbar = self.__w_scrollbar(self, orient=VERTICAL)
            ckwargs['yscrollcommand'] = fn.scrollGenCommand(self.__vbar.set, scrollVertical, 'vstate',
                                                            fn_scrollstate=self.set_scroll_state)
            rweight.append(0)
            # Save bindtags
            self.__vbar_bindtags_enabled = self.__vbar.bindtags()
            self.__vbar_bindtags_disabled = (str(self.__vbar.winfo_toplevel()), 'all')
            assert self.__vbar_bindtags_enabled[-2:] == self.__vbar_bindtags_disabled, f'{self}: Weird vbar bindtags: {self.__vbar_bindtags_enabled}'
        if scrollVertical in (None, True) and scrollVertical in (None, True):
            # This is not really not necessary, but it is visually pleasing
            # TODO: Remove?
            self.__corner = self.__w_corner(self, cursor='', takefocus=False)
            # Disable sizegrip events
            self.__corner.bind('<Button-1>', fn.binding_disable)
        icframe = self.__w_icframe(parent=self, wroot=parent.wroot)
        icanvas = tk.Canvas(icframe, borderwidth=0, **ckwargs)
        assert issubclass(childClass, tk.Misc)
        iwidget = childClass(icframe, *args, **kwargs)  # type: ignore
        assert isinstance(iwidget, tk.Misc)
        if __debug__:
            if isinstance(iwidget, (tk.XView, tk.YView)):
                warnings.warn(f'{self}: `{childClass.__qualname__}` supports `ScrolledWidget`, prefer')

        # State
        self.state_type = var.nothing
        self.init_single(vspec=None)
        # Special Widget state
        self.wparent = parent

        # Glue scrollbars with inner widget
        if self.__hbar:
            assert isinstance(icanvas, tk.XView)
            self.__hbar['command'] = icanvas.xview
        if self.__vbar:
            assert isinstance(icanvas, tk.YView)
            self.__vbar['command'] = icanvas.yview
        # Glue inner widget with canvas
        assert isinstance(iwidget, tk.Widget)
        icanvas_window = icanvas.create_window([0, 0], anchor=tk.NW,
                                               window=iwidget)

        # Layout
        if scrollExpand:
            self.grid(sticky=tk.NSEW)
        assert isinstance(icanvas, tk.Grid)
        icanvas.grid(row=0, column=0, sticky=tk.NSEW)
        assert isinstance(icframe, tk.Grid)
        icframe.rowconfigure(0, weight=1)
        icframe.columnconfigure(0, weight=1)
        icframe.grid(row=0, column=0, sticky=tk.NSEW)
        self.set_scroll_state(scrollHorizontal or None, scrollVertical or None)
        # Emulate `fn.configure_grid(self, rweight, cweight)`
        for ridx, weight in enumerate(rweight):
            self.rowconfigure(ridx, weight=weight)
        for cidx, weight in enumerate(cweight):
            self.columnconfigure(cidx, weight=weight)

        # Reconfigure complex on size change
        self.__cfg_weigths: typing.Optional[typing.Tuple[int, int]] = None
        self.__ti_cfg_weights = iwidget.tidle(self.__onConfigure_weights, immediate=False,
                                              key='__:cfg:weigths')
        self.__ti_cfg_calc = iwidget.tidle(self.__onConfigure_calculate, immediate=False,
                                           key='__:cfg:calc')
        self.__rl_cfg_calc = model.RateLimiter(self, self.__ti_cfg_calc.reschedule,
                                               limit=1000 // __fps)
        icanvas.bind('<Configure>', self.__rl_cfg_calc.hit)

        # Save references to all important objects
        self.canvas: tk.Canvas = icanvas
        self.__canvas_iframe = icframe
        self.__canvas_iwindow = icanvas_window
        self.__fps = __fps

        # Proxy all access to `iwidget`
        self.proxee = iwidget
        if __debug__:
            if scrollExpand is False:
                warnings.warn(f'{self}: `scrollExpand=False` might have some issues')

    def __gweights(self) -> typing.Tuple[int, int]:
        # Capture the weigths
        wparent = self.wparent
        assert wparent is not None
        assert isinstance(wparent, tk.Widget)
        if (wgrid := self.wgrid) is not None:
            # Parent widget is a regular gridded widget
            return (
                wparent.columnconfigure(wgrid.column)['weight'],
                wparent.rowconfigure(wgrid.row)['weight'],
            )
        else:
            # Parent widget is does not have a grid, expand always
            # TODO: Controllable with `scrollExpand`?
            assert isinstance(wparent, (Notebook, FramePaned)), f'{self}: Bad parent widget type `{wparent.__class__.__qualname__}`'
            return (1, 1)

    def __onConfigure_weights(self):
        assert self.__cfg_weigths is None
        self.__cfg_weigths = self.__gweights()

    # TODO: Merge with `set_scroll_state`?
    def __onConfigure_calculate(self, event=None):
        inner = self.proxee
        canvas = self.canvas
        iwidth, iheight = int(inner.winfo_reqwidth()), int(inner.winfo_reqheight())
        cwidth, cheight = int(canvas.winfo_width()), int(canvas.winfo_height())
        assert self.__cfg_weigths is not None, f'{self}: Race: No weights yet'
        if __debug__:
            cfg_weigths = self.__gweights()
            assert self.__cfg_weigths == cfg_weigths, f'{self}: Changed weights: {self.__cfg_weigths} > {cfg_weigths}'
        widthw, widthh = self.__cfg_weigths
        # if __debug__:
        #     cfwidth, cfheight = int(self.__canvas_iframe.winfo_reqwidth()), int(self.__canvas_iframe.winfo_reqheight())
        #     logger.debug('%s | weight[w=%d h=%d]', self, widthw, widthh)
        #     logger.debug('  C[%dx%d] F[%dx%d] Cf[%dx%d]', cwidth, cheight, iwidth, iheight, cfwidth, cfheight)
        if (cwidth, cheight) == (1, 1) or (iwidth, iheight) == 1:
            # if __debug__:
            #     logger.debug('  » Skip: Initial?')
            pass
        else:
            rcanvas = {}
            riwindow = {}
            # Don't know where do these extra pixels come from...
            # TODO: Check if these don't appear when forcing a border somewhere to `0`
            deltaw, deltah = -2, -2
            if widthw == 0:
                # Don't grow width
                riwindow['width'] = iwidth + deltaw
                rcanvas['width'] = iwidth + deltaw
            else:
                # Grow width
                if self.__hbar is None:
                    # No Scrollbar: Grow to canvas
                    riwindow['width'] = cwidth + deltaw
                else:
                    # Scrollbar: Grow as much as possible
                    riwindow['width'] = max(iwidth, cwidth) + deltaw
            if widthh == 0:
                # Don't grow height
                riwindow['height'] = iheight + deltah
                rcanvas['height'] = iheight + deltah
            else:
                # Grow height
                if self.__vbar is None:
                    riwindow['height'] = cheight + deltah
                else:
                    riwindow['height'] = max(iheight, cheight) + deltah
            if riwindow:
                # if __debug__:
                #     logger.debug('  » InnerW: %s | %s',
                #                  ' '.join(f'{k}={v}' for k, v in riwindow.items()),
                #                  canvas.bbox(tk.ALL),
                #                  )
                canvas.itemconfig(self.__canvas_iwindow, **riwindow)
                # Setup the canvas scroll region
                canvas.configure(scrollregion=canvas.bbox(tk.ALL))
            if rcanvas:
                # if __debug__:
                #     logger.debug('  » Canvas: %s', ' '.join(f'{k}={v}' for k, v in rcanvas.items()))
                canvas.configure(**rcanvas)

    def set_gui_state(self, state: typing.Optional[model.GuiState] = None, **kwargs) -> model.GuiState:
        ''''''  # Do not document
        self_state = super().set_gui_state(state, **kwargs)
        if __debug__:
            logger_autostate.debug('%s: State %s', self, self_state)
        states_tk = model.GuiState(enabled=self_state.enabled).states_tk()
        # Glue scrollbars with child widget GUI state
        # Must change the state and fully disable events with `bindtags`
        if self.__hbar:
            if __debug__:
                logger_autostate.debug('> H Bar')
            self.__hbar.state(states_tk)
            assert self_state.enabled is not None
            fn.state_bindtags(self.__hbar, self_state.enabled,
                              bt_on=self.__hbar_bindtags_enabled,
                              bt_off=self.__hbar_bindtags_disabled)
        if self.__vbar:
            if __debug__:
                logger_autostate.debug('> V Bar')
            self.__vbar.state(states_tk)
            assert self_state.enabled is not None
            fn.state_bindtags(self.__vbar, self_state.enabled,
                              bt_on=self.__vbar_bindtags_enabled,
                              bt_off=self.__vbar_bindtags_disabled)
        return self_state

    def get_scroll_state(self) -> typing.Tuple[bool, bool]:
        '''Get the current scrollbar visibility state.

        If the scrollbar is completely disabled, `False` is returned.

        This is a tuple with the state for both scrollbars, horizontal and
        vertical.

        See Also:
            - `set_scroll_state`: Change the current state
        '''
        return (
            self.__hbar is not None and bool(self.__hbar.grid_info()),
            self.__vbar is not None and bool(self.__vbar.grid_info()),
        )

    def set_scroll_state(self, hstate: typing.Optional[bool] = None, vstate: typing.Optional[bool] = None) -> None:
        '''Change the current scrollbar visibility state.

        This can change both horizontal and vertical state independently. The
        corner widget is managed automatically.

        Args:
            hstate: If not `None`, set the horizontal scrollbar visibility.
            vstate: If not `None`, set the vertical scrollbar visibility.

        See Also:
            - `get_scroll_state`: Get the current state
        '''
        if hstate is not None and self.__hbar is not None:
            h_wgrid = self.__hbar.grid_info()
            if hstate:
                if not h_wgrid:
                    self.__hbar.grid(row=1, column=0, sticky=tk.EW)
                    # if __debug__:
                    #     logger.debug('%s: Show hbar', self)
            else:
                if h_wgrid:
                    # if __debug__:
                    #     logger.debug('%s: Hide hbar', self)
                    self.__hbar.grid_remove()
        if vstate is not None and self.__vbar is not None:
            v_wgrid = self.__vbar.grid_info()
            if vstate:
                if not v_wgrid:
                    self.__vbar.grid(row=0, column=1, sticky=tk.NS)
                    # if __debug__:
                    #     logger.debug('%s: Show vbar', self)
            else:
                if v_wgrid:
                    # if __debug__:
                    #     logger.debug('%s: Hide vbar', self)
                    self.__vbar.grid_remove()
        if self.__corner is not None:
            isHorizontal = self.__hbar is not None and self.__hbar.grid_info()
            isVertical = self.__vbar is not None and self.__vbar.grid_info()
            c_wgrid = self.__corner.grid_info()
            if isHorizontal and isVertical:
                if not c_wgrid:
                    self.__corner.grid(row=1, column=1)
                    # if __debug__:
                    #     logger.debug('%s: Show corner', self)
            else:
                if c_wgrid:
                    # if __debug__:
                    #     logger.debug('%s: Hide corner', self)
                    self.__corner.grid_remove()

    def scrollTo(self, *,
                 x: typing.Optional[float] = None,
                 y: typing.Optional[float] = None,
                 anchor: model.CP = model.CP.center,
                 ) -> None:
        '''Adjust the scrollbars to show fractions of the total size.

        The anchor to consider the adjustment is configurable as ``anchor``.

        Arguments:
            x: Fraction of the total size to show on anchor, as a floating
                point. Adjusts the horizontal scroll position. Optional.
            y: Fraction of the total size to show on the anchor, as a floating
                point. Adjusts the vertical scroll position. Optional.
            anchor: The anchor to adjust the fractional positions.
        '''
        assert self.canvas is not None, f'{self}: Proxy Canvas Widget manipulation too soon'
        if anchor not in model.CP_ScrollAnchor:
            raise ValueError(f'Unsupported anchor: {anchor}')
        if __debug__:
            if x is not None and self.__hbar is None:
                warnings.warn('{self}: scrolling without horizontal scrollbar', stacklevel=2)
            if y is not None and self.__vbar is None:
                warnings.warn('{self}: scrolling without vertical scrollbar', stacklevel=2)
        if __debug__:
            logger.debug('< %s', model.WidgetView.fromwidget(self.canvas))
        fn.scrollTo(self.canvas,
                    x=x, y=y, anchor=anchor)
        if __debug__:
            logger.debug('> %s', model.WidgetView.fromwidget(self.canvas))


class ListboxControl(FrameUnlabelled):
    '''A listbox widget, with extra controls for a set of strings.

    This is complex variation on `Listbox`, with extra widgets for manipulating
    the string list. This is useful to manipulate string lists.

    The extra widget controls can be grouped as follows:

    - There is a `ComboboxN` to select the element to add.
      There is a button to insert after the currently selected element, or
      append otherwise; clicking on this button with the middle mouse button
      will always append to the end of the list.
      There is another button to add all supported elements (keeping the
      existing order); clicking on this button with the middle mouse button
      replaces all elements with all supported elements, in the original order.
    - There are buttons to remove the currently selected element, or clear all
      elements.
    - There are buttons to manipulate the order of the currently selected
      element, upwards or downwards. Clicking on these buttons with the middle
      mouse button moves the currently selected element to the top or bottom of
      the list.

    All these groups are configurable, see the ``button*`` arguments.

    .. note::
        When ``buttonOne`` is set to `False`, it might be interesting to move
        the button widgets to the right side.
        Set the ``layout`` argument as ``layout='C1,x'`` to achieve this
        configuration.

    Args:
        selAll: Specification for all supported elements.
        selList: Initial selected string list.
        buttonOne: Include buttons for adding a single element, and removing
            the selected element. This controls the `ComboboxN` placement too.
        buttonAll: Include buttons for adding all supported elements and clean
            all elements. Defaults to include.
        buttonOrder: Include buttons to manipulate the order of selected
            element. Defaults to not include.
        allKwargs: Passed to `ComboboxN` object.
        kwargs: All other arguments are passed to `Listbox`.

    .. note::

        The container widget is `FrameUnlabelled`, and the inner widgets are:

        - `Listbox` (with `ScrolledWidget` handling): ``selected``
        - `ComboboxN`: ``all``
        - `Button`: ``moveUp`` ``rmAll`` ``rm`` ``add`` ``addAll`` ``moveDown``
    '''
    layout = 'R1,x'
    wstate_single = 'selected'
    '''Default value for `wstate_single <mixin.MixinStateContainer.wstate_single>`.'''

    # TODO: Refactor to something closer to CheckboxFrame, with IButton lists
    def setup_widgets(self,
                      selAll: typing.Union[var.SpecCountable, validation.VSpec, None] = None,
                      selList: typing.Optional[typing.Sequence[str]] = None,
                      buttonOne: bool = True, buttonAll: bool = True, buttonOrder: bool = False,
                      allKwargs: typing.Optional[typing.Mapping[str, typing.Any]] = None,
                      **kwargs,
                      ) -> None:
        ''''''  # Do not document
        assert any((buttonOne, buttonAll, buttonOrder)), f'{self}: This is just a Listbox'
        assert 'scrollHorizontal' not in kwargs and 'scrollVertical' not in kwargs, f'{self}: Unsupported scrolling options'
        assert kwargs.get('selectable', False) is False, f'{self}: Unsupported selectable=True option'
        assert (allKwargs or {}).get('vspec') is None, f'{self}: Unsupported vspec on allKwargs'
        if (buttonOne or buttonAll) and selAll is None:
            raise exception.InvalidWidgetDefinition('ListboxControl: When "buttonOne"/"buttonAll" are selected, "selAll" must be given')
        vall: typing.Optional[var.SpecCountable]
        if isinstance(selAll, var.SpecCountable):
            vall = selAll
        elif isinstance(selAll, validation.VSpec):
            vall = var.SpecCountable(selAll)
        else:
            vall = None

        # Listbox
        kwargs['selectable'] = True  # Force selectable
        self.selected = ScrolledWidget(self, Listbox, **kwargs,
                                       scrollHorizontal=False, scrollVertical=None)

        # Buttons
        self.moveUp = Button(self, label='↑') if buttonOrder else None
        self.rmAll = Button(self, label='---') if buttonAll else None
        self.rm = Button(self, label='-') if buttonOne else None
        if buttonOne:
            # TODO: Support `EntryN` too?
            # TODO: Support validation, check the missing elements
            assert vall is not None
            self.all: typing.Optional[mixin.MixinWidget] = ComboboxN(self,
                                                                     vspec=vall,
                                                                     **(allKwargs or {}),
                                                                     ).putIgnoreState()
        else:
            self.all = None
        self.add = Button(self, label='+') if buttonOne else None
        self.addAll = Button(self, label='+++') if buttonAll else None
        self.moveDown = Button(self, label='↓') if buttonOrder else None

        # State
        self._selectionAll = vall
        if selList is None:
            self._selectionList: typing.Sequence[str] = []
        else:
            if __debug__:
                if vall is not None:
                    assert all(e in vall for e in selList), f'ListboxControl: Invalid selList: {selList}'
                else:
                    warnings.warn(f'{self}: selList without selAll, will not validate', stacklevel=4)
            self._selectionList = selList

    def setup_layout(self, layout):
        # Don't grow any buttons
        grid_h = layout.startswith(('R', 'r', 'H'))
        grid_v = layout.startswith(('C', 'c', 'V'))
        grid = (grid_h, grid_v)
        # Generate a sticky setup
        # - It's the opposite side from the grid
        if grid == (False, True):
            sticky = tk.EW
        elif grid == (True, False):
            sticky = tk.NS
        else:
            sticky = None
        if __debug__:
            logger_model_layout.debug('%s: ListboxControl Automatic Layout (R=%s C=%s)', self, grid_h, grid_v)
        forsticky = []
        if self.rm and self.add:
            self.pgrid(self.rm, self.add,
                       row=grid_h, column=grid_v,
                       weight=0, uniform='button_one')
            forsticky.extend((self.rm, self.add))
        if self.rmAll and self.addAll:
            self.pgrid(self.rmAll, self.addAll,
                       row=grid_h, column=grid_v,
                       weight=0, uniform='button_all')
            forsticky.extend((self.rmAll, self.addAll))
        if self.moveUp and self.moveDown:
            self.pgrid(self.moveUp, self.moveDown,
                       row=grid_h, column=grid_v,
                       weight=0, uniform='button_order')
            forsticky.extend((self.moveUp, self.moveDown))
        if sticky:
            for w in forsticky:
                w.grid(sticky=sticky)

    def setup_defaults(self):
        if self._selectionList:
            self.selected.wstate = self._selectionList

    def setup_adefaults(self):
        swidget = self.selected
        if self.rm:
            self.rm.onClick = swidget.genRemoveSelected()
        if self.rmAll:
            self.rmAll.onClick = swidget.genRemoveAll()
        if self.moveDown:
            self.moveDown.onClick = swidget.genMoveSelected(+1)
            self.moveDown.binding('<ButtonPress-2>', swidget.genMoveSelected('bottom'), key='__:control:bottom')
        if self.all:
            self.all.binding('<Return>', self.onAppendInsert, key='__:control:return')
        if self.add:
            self.add.onClick = self.onAppendInsert
            self.add.binding('<ButtonPress-2>', self.onAppend, key='__:control:append')
        if self.moveUp:
            self.moveUp.onClick = swidget.genMoveSelected(-1)
            self.moveUp.binding('<ButtonPress-2>', swidget.genMoveSelected('top'), key='__:control:top')
        if self.addAll:
            self.addAll.onClick = self.onAddAll
            self.addAll.binding('<ButtonPress-2>', self.onReplaceAll, key='__:control:replaceall')

    def setup_variable(self, variable: typing.Optional[var.Variable]) -> var.Variable:
        ''''''  # Override `var.aggregator` setup
        assert variable is None, f'{self!r}: Container Widget aggregator?'
        assert self.selected.variable is not None
        return self.selected.variable

    def onAppendInsert(self, event: typing.Any = None) -> None:
        assert self.all, f'{self}: Calling `onAppendInsert` without "buttonOne" argument'
        assert isinstance(self.all, mixin.SingleWidget) and self.all.wstate.valid
        swidget = self.selected
        assert isinstance(swidget, Listbox)
        lbl = self.all.wstate.label
        if lbl not in swidget.wstate:
            wsidx = swidget.wsidx()
            if wsidx is None:
                swidget.elementAppend(lbl)
            else:
                nid = swidget.elementInsert(lbl, where=wsidx + 1)
                swidget.wsel(nid)

    def onAppend(self, event: typing.Any = None) -> None:
        assert self.all, f'{self}: Calling `onAppend` without "buttonOne" argument'
        assert isinstance(self.all, mixin.SingleWidget) and self.all.wstate.valid
        swidget = self.selected
        assert isinstance(swidget, Listbox)
        lbl = self.all.wstate.label
        if lbl not in swidget.wstate:
            swidget.elementAppend(lbl)

    def onAddAll(self, event: typing.Any = None) -> None:
        assert self._selectionAll is not None
        swidget = self.selected
        assert isinstance(self.selected, Listbox)
        # Keep the existing state, add missing
        for lbl in (e for e in self._selectionAll.lall() if e not in swidget.wstate):
            swidget.elementAppend(lbl)

    def onReplaceAll(self, event: typing.Any = None) -> None:
        assert self._selectionAll is not None
        swidget = self.selected
        assert isinstance(self.selected, Listbox)
        # Replace the existing state
        swidget.wstate = self._selectionAll.lall()


class CheckboxFrame(FrameUnlabelled):
    '''A frame filled with checkboxes, with optional buttons for full state
    manipulation.

    This is a bunch of checkboxes, with optional buttons to enable or disable
    them all at once. Each checkbox is independent.
    Supports a nested specification for multiple checkboxen inside nested
    `FrameLabelled`, there's no limit to the nesting level.

    Each widget can be traced separately, with a non-ambigous function
    generator (see ``traceFn``).
    The widget ID and the labels can be customised using ``labelsCheckboxes``.

    Args:
        stateCheckboxes: Mapping from identifier to `Checkbox` label.
            Can be a nested mapping, keys and values must always be `str`.
        stateDefault: Default state for all child widgets. Optional, is `None`
            it's not changed from the `Checkbox` default.
        traceFn: Function generator for tracing each individual `Checkbox` widget.
            Receives the tree of nested widget ID as positional arguments.
        hasButtons: Include state manipulation buttons. Can be given as:

            - `True`: Include ``Enable All``/``Disable All`` buttons. This is
              the **default**.
            - `False`: Do not include any buttons
            - A list of `IButton <CheckboxFrame.IButton>` objects.

        layout: Layout setting for this frame. Only some values make sense:

            - ``R1,x``: "Enable" / "Disable" buttons on bottom. This is the
              **default**.
            - ``H1,x``: "Enable" / "Disable" buttons on top.
            - ``C1,x``: "Enable" / "Disable" buttons on the right side
            - ``V1,x``: "Enable" / "Disable" buttons on the left side
            - `VERTICAL`: Buttons on bottom, in a single column.
            - `HORIZONTAL`: Buttons on the left side, in a single line.

            All other layouts are possible, but they are ugly.
            Override `CheckboxFrame.setup_layout` in that case, for further
            tweaking.
        layoutCheckboxes: ``layout`` setting for the internal nested frames.
            Can be a single string, to be applied everywhere, or a list of strings
            to be applied on each nested level.
            This affects the orientation of the child widgets only.
            Defaults to automatic layout, whenever is not given.
        label: Include a toplevel label, keeping the state as-is.
            Optional, similar to a choice between `FrameLabelled` and
            `FrameUnlabelled`.
        labelsCheckboxes: Labels for internal nested widgets. Given as a
            mapping between nested identifiers and the label.
            For a simple case of a single level, the mapping key can be a
            simple string, instead of a tuple with a single string.
        argCheckboxes: Extra arguments passed to each individual `Checkbox` widget.
        argButtons: Extra arguments passed to each individual `Button` widget.
            Overriden by the `IButton.args <CheckboxFrame.IButton>` arguments.

    .. note::

        To create a version if this widget with a different base class (i.e.
        `FrameStateful` for example), use the following workaround:

        .. code:: python

            class CheckboxFrameStateful(FrameStateful):
                wstate_single = 'frame'

                def setup_widgets(self, **kwargs):
                    self.frame = tkmilan.CheckboxFrame(self, **kwargs)
            ...

            frame = CheckboxFrameStateful(PARENT, label='Frame Label', ...)

        Note this is different from setting a ``label``.

    See Also:
        Use `RadioFrame` for a simpler version of this with radio buttons.

    .. note::

        The child widgets are placed on an internal `FrameUnlabelled`, named
        ``cbox``. The buttons are also child widget, identified by their `id
        <IButton.id>`.
    '''
    wstate_single = 'cbox'
    '''Default value for `wstate_single <mixin.MixinStateContainer.wstate_single>`.'''

    @dataclass
    class IButton:
        '''`CheckboxFrame` button configuration object.

        Args:
            identifier: Identifies the button
            label: Button Label.
                Optional, if `None`, uses a label derived from the ``identifier``
            onClick: Widget ``onClick`` changes. Optional.
            onClickFn: Function generator for ``onClick`` function.
                Optional, overrides the ``onClick`` function.
                Receives the current widget as a single argument.
            onClickSetAll: Generate a `setAll <CheckboxFrame.setAll>` call,
                with the correct target.
                Optional, overrides the ``onClick`` function.
            args: Other arguments, passed to `Button`. Optional.
        '''
        identifier: str
        label: typing.Optional[str] = None
        onClick: typing.Optional[typing.Union[bool, typing.Callable]] = None
        onClickFn: typing.Optional[typing.Callable] = None
        onClickSetAll: typing.Optional[bool] = None
        args: typing.Optional[typing.Mapping[str, typing.Any]] = None

        def __post_init__(self):
            if __debug__:
                cnt_none_clicks = sum(1 for e in (
                    self.onClick,
                    self.onClickFn,
                    self.onClickSetAll,
                ) if e is not None)
                if cnt_none_clicks > 1:
                    raise ValueError(f'Button "{self.identifier}": Ambigous `onClick` definition')

        @property
        def id(self) -> str:
            '''The final identifier'''
            return f'b:{self.identifier}'

        @property
        def lbl(self) -> str:
            '''The final widget label'''
            return self.label or f'ID[{self.identifier}]'

    class __w_checkboxen:
        ''''''  # Internal, do not document
        _ID: typing.Tuple[str, ...]
        _subclass: 'CheckboxFrame.__w_checkboxen'

        def setup_widgets(self, *,
                          stateCheckboxes: typing.Mapping[str, typing.Any],
                          layoutCheckboxes: typing.Union[str, typing.Sequence[str]],
                          labelsCheckboxes: typing.Mapping[typing.Union[str, typing.Tuple[str, ...]], str],
                          argCheckboxes: typing.Optional[typing.Mapping[str, typing.Any]] = None,
                          ):
            ''''''  # Internal, do not document
            widgets = {}  # typing.MutableMapping[str, typing.Union[Checkbox, __w_lcheckboxen]]
            this_layout, next_layout = autolayout.gnested(layoutCheckboxes)

            assert callable(self._subclass), f'{self._subclass!r}: Invalid sub class'
            for cid, cobj in stateCheckboxes.items():
                c_id = (*self._ID, cid)
                c_label: str
                if isinstance(cobj, typing.Mapping):
                    c_label = labelsCheckboxes.get(cid, cid) if len(self._ID) == 0 else cid
                    widgets[cid] = self._subclass(self, thisID=c_id,
                                                  label=labelsCheckboxes.get(c_id, c_label),
                                                  stateCheckboxes=cobj,
                                                  layout=this_layout, layoutCheckboxes=next_layout,
                                                  labelsCheckboxes=labelsCheckboxes,
                                                  argCheckboxes=argCheckboxes)
                elif isinstance(cobj, str):
                    c_label = labelsCheckboxes.get(cid, cobj) if len(self._ID) == 0 else cobj
                    assert isinstance(self, mixin.ContainerWidget)
                    widgets[cid] = Checkbox(self, label=labelsCheckboxes.get(c_id, c_label),
                                            **(argCheckboxes or {}))
                else:
                    raise NotImplementedError
            return widgets

        def _setup_trace(self, traceFn):
            for wid, w in self.widgets.items():
                if isinstance(w, Checkbox):
                    w.trace(traceFn(*self._ID, wid))
                else:
                    assert hasattr(w, '_setup_trace'), f'Invalid Internal Checkbox Widget: {w}'
                    w._setup_trace(traceFn)

        def _state_all(self, state: bool):
            rval = {}
            assert isinstance(self, mixin.ContainerWidget), '{self} is not a valid tkmilan container widget'
            for wname, w in self.widgets.items():
                if isinstance(w, Checkbox):
                    rval[wname] = state
                else:
                    assert hasattr(w, '_state_all'), f'Invalid Internal Checkbox Widget: {w}'
                    rval[wname] = w._state_all(state)
            return rval

    class __w_lcheckboxen(__w_checkboxen, FrameLabelled):
        def __init__(self, *args,
                     thisID: typing.Tuple[str, ...],
                     **kwargs):
            self._ID = thisID
            super().__init__(*args, **kwargs)  # FrameUnlabelled
    __w_lcheckboxen._subclass = typing.cast('CheckboxFrame.__w_checkboxen', __w_lcheckboxen)

    class __w_ucheckboxen(__w_checkboxen, FrameUnlabelled):
        def __init__(self, *args,
                     thisID: typing.Tuple[str, ...],
                     **kwargs):
            self._ID = thisID
            super().__init__(*args, **kwargs)  # FrameUnlabelled
    __w_ucheckboxen._subclass = typing.cast('CheckboxFrame.__w_checkboxen', __w_lcheckboxen)

    def __init__(self, *args,
                 hasButtons: 'typing.Union[bool, typing.Sequence[CheckboxFrame.IButton]]' = True,
                 stateDefault: typing.Optional[bool] = None,
                 traceFn: typing.Optional[typing.Callable] = None,
                 **kwargs):
        # Save for later
        self._buttons: 'typing.Sequence[CheckboxFrame.IButton]'
        if hasButtons is True:
            self._buttons = [
                self.__class__.IButton('enable', 'Enable All',
                                       onClickSetAll=True),
                self.__class__.IButton('disable', 'Disable All',
                                       onClickSetAll=False),
            ]
        elif hasButtons is False:
            self._buttons = []
        else:
            self._buttons = hasButtons
        self._traceFn = traceFn
        self._stateDefault = stateDefault
        if self.layout == '':  # Automatic AUTO
            kwargs.setdefault('layout', AUTO if hasButtons is False else 'R1,x')
        super().__init__(*args, **kwargs)  # FrameUnlabelled

    def setup_widgets(self, *, label: typing.Optional[str] = None,
                      stateCheckboxes: typing.Mapping[str, typing.Any],
                      layoutCheckboxes: typing.Union[str, typing.Sequence[str]] = AUTO,
                      labelsCheckboxes: typing.Optional[typing.Mapping[typing.Union[str, typing.Tuple[str, ...]], str]] = None,
                      argCheckboxes: typing.Optional[typing.Mapping[str, typing.Any]] = None,
                      argButtons: typing.Optional[typing.Mapping[str, typing.Any]] = None,
                      ):
        ''''''  # Do not document
        if __debug__:
            if all(isinstance(v, str) for v in stateCheckboxes.values()):
                assert len(stateCheckboxes) > 1, f'{self}: This is just a single Checkbox'

        self.cbox: 'typing.Union[CheckboxFrame.__w_ucheckboxen, CheckboxFrame.__w_lcheckboxen]'

        labelsCheckboxes = labelsCheckboxes or {}
        assert labelsCheckboxes is not None
        this_layout, next_layout = autolayout.gnested(layoutCheckboxes)
        if label is None:
            self.cbox = self.__class__.__w_ucheckboxen(self, thisID=tuple(),
                                                       stateCheckboxes=stateCheckboxes,
                                                       layout=this_layout, layoutCheckboxes=next_layout,
                                                       labelsCheckboxes=labelsCheckboxes,
                                                       argCheckboxes=argCheckboxes)
        else:
            self.cbox = self.__class__.__w_lcheckboxen(self, thisID=tuple(),
                                                       stateCheckboxes=stateCheckboxes,
                                                       layout=this_layout, layoutCheckboxes=next_layout,
                                                       labelsCheckboxes=labelsCheckboxes, label=label,
                                                       argCheckboxes=argCheckboxes)
        widgets: typing.MutableMapping[str, mixin.MixinWidget] = {}
        widgets['cbox'] = self.cbox
        for btn in self._buttons:
            assert btn.id not in ('', 'cbox'), f'Invalid IButton: {btn}'
            assert btn.id not in widgets, f'Repeated IButton ID: {btn.id}'
            btn_args = {
                **(argButtons or {}),
                **(btn.args or {})
            }
            widgets[btn.id] = Button(self, label=btn.lbl,
                                     **btn_args)
        return widgets

    def setup_layout(self, layout):
        '''Setup the layout for this widget.

        Adjusts the row and column configuration for the buttons.

        See the upstream `setup_layout <ContainerWidget.setup_layout>`
        documentation.

        Available for subclass redefinition.
        '''
        for btn in self._buttons:
            widget = self.widgets[btn.id]
            bgrid = widget.wgrid
            if layout.startswith(('R', 'r', 'H')):
                self.rowconfigure(bgrid.row, weight=0)  # Buttons Row
            elif layout.startswith(('C', 'c', 'V')):
                self.columnconfigure(bgrid.column, weight=0)  # Buttons Column
            else:
                pass  # Not a simple row/column alignment

    def setup_defaults(self):
        '''Set the default values and wire up button events.

        See the upstream `setup_defaults <ContainerWidget.setup_defaults>`
        documentation.

        Available for subclass redefinition, make sure this still runs.
        '''
        if self._stateDefault is not None:
            self.setAll(self._stateDefault)
        for btn in self._buttons:
            btn_widget = self.widgets[btn.id]
            if btn.onClickSetAll is not None:
                btn_widget.onClick = self.setAllFn(btn.onClickSetAll)
            elif btn.onClickFn is not None:
                btn_widget.onClick = btn.onClickFn(self)
            elif btn.onClick is not None:
                btn_widget.onClick = btn.onClick

    def setup_adefaults(self):
        '''Set the widget traces.

        See the upstream `setup_adefaults <ContainerWidget.setup_adefaults>`
        documentation.

        Available for subclass redefinition, make sure this still runs.
        '''
        if self._traceFn:
            self.cbox._setup_trace(self._traceFn)

    def wbutton(self, identifier: str) -> Button:
        '''Get the button widget by identifier.

        This is just an helper function to get the correct widget value out of
        ``widgets``, based on the identifier.

        Args:
            idx: The button identifier.

        Note:
            In debug mode, this will fail if called with the wrong identifier.
            This check is skipped for performance on optimized mode.
        '''
        btn_id = f'b:{identifier}'
        assert btn_id == self.__class__.IButton(identifier).id
        assert btn_id in self.widgets, f'Invalid Button: {identifier}'
        btn_w = self.widgets.get(btn_id)
        assert isinstance(btn_w, Button), f'Invalid Widget: {btn_w!r}'
        return btn_w

    def setAll(self, state: bool):
        '''Set the state for all child widgets.

        Args:
            state: The state to consider.
        '''
        self.wstate = self.cbox._state_all(state)

    def setAllFn(self, state: bool) -> typing.Callable:
        '''Function generator for `setAll`.'''
        def setAllFn():
            return self.setAll(state)
        return setAllFn


class RadioFrameUnlabelled(FrameUnlabelled):
    '''Internal `RadioFrameLabelled`/`RadioFrameStateful` widget definition.

    This can be used as an alternative, in case you **really** need a
    unlabelled frame alternative.

    Args:
        radioArgs: Extra arguments passed to inner `Radio` widgets.

    See Also:
        Use `RadioFrameLabelled` or `RadioFrameStateful` in the common case.

    .. warning:: Don't use this directly, unless you **really** know what you
        are doing.
    '''
    rvar: var.StaticMap
    '''The common variable for all the inner `Radio` widgets.'''
    wstate_single = True
    ''''''  # Internal, do not document

    @dataclass
    class Style(model.WStyle):
        '''`RadioFrameUnlabelled` style object.

        These are the settings:

        Args:
            align_vertical: When enabled, and the layout has a single column,
                adjust the child widths to the full extent of the frame.
                This means the `Radio` widgets are aligned.
                When set to `None`, enable it only if the widget labels have
                different sizes.
                Defaults to `None`.
        '''
        align_vertical: typing.Optional[bool] = None

    def __init__(self, parent: mixin.ContainerWidget, *args,
                 style: Style = Style(_default=True),
                 **kwargs):
        self.wstyle = style
        super().__init__(parent, *args, **kwargs)

    # TODO: Support external variable in `stateRadio`?
    def setup_widgets(self, *,
                      stateRadio: validation.StaticMap,
                      w_radio: typing.Type[Radio] = Radio,
                      radioArgs: typing.Optional[typing.Mapping[str, typing.Any]] = None,
                      ):
        ''''''  # Do not document
        if __debug__:
            badkeys = ('label', 'variable', 'value')
            assert all(n not in (radioArgs or {}) for n in badkeys), f'Invalid "radioArgs": invalid key @ {" ".join(badkeys)}'
        assert len(stateRadio) > 0
        self.rvar = typing.cast(var.StaticMap,
                                self.varSpec(var.StaticMap, stateRadio))
        widgets: typing.MutableMapping[str, mixin.MixinWidget] = {}
        for lbl, idx in self.rvar.container.items():
            # Use `lbl` as "value", the validation takes care of returning the idx
            widgets[idx] = w_radio(self, self.rvar,
                                   value=lbl, label=lbl,
                                   **(radioArgs or {}))
        return widgets

    def setup_variable(self, variable: typing.Optional[var.Variable]) -> var.StaticMap:
        ''''''  # Override `var.aggregator` setup
        assert variable is None, f'{self!r}: Container Widget aggregator?'
        return self.rvar

    def setup_container_layout(self, olayout: typing.Optional[str]) -> None:
        ''''''  # Override upstream
        if self.gsize.columns == 1:
            align_vertical: bool
            if self.wstyle.align_vertical is None:
                assert all(isinstance(w, Radio) for w in self.widgets.values())
                tsizes = set(  # Gather all child label sizes
                    len(w.wlabel)
                    for w in typing.cast(typing.Sequence[Radio], self.widgets.values())
                )
                assert len(tsizes) > 0
                align_vertical = len(tsizes) > 1
                if __debug__:
                    logger_model_layout.debug('%s: Auto align_vertical: %s sizes=%d', self, align_vertical, len(tsizes))
            else:
                align_vertical = self.wstyle.align_vertical
            assert align_vertical in (True, False)
            if align_vertical:
                for w in self.widgets.values():
                    assert isinstance(w, tk.Grid)
                    w.grid(sticky=tk.EW)


class RadioFrameLabelled(FrameLabelled):
    '''A labelled frame filled with radio buttons.

    This is a bunch of `Radio` widgets inside a `FrameLabelled`, all connected
    to the same internal variable. That variable is exposed as the only state.

    The internal variable is created anew, there is no support for using an
    external variable.

    Args:
        stateRadio: Mapping from label to value. This should be a
            `StaticMap <validation.StaticMap>`.
        frameArgs: Extra arguments passed to the inner `FrameUnlabelled`
            widget. Use ``radioArgs`` for the inner radio widget args, see
            `RadioFrameUnlabelled`.

    See Also:
        Use `CheckboxFrame` for a version of this with checkboxen, with extra
        features.

        Use `RadioFrameStateful` for a stateful frame version of this.
    '''
    wstate_single = 'raw'
    '''Default value for `wstate_single <mixin.MixinStateContainer.wstate_single>`.'''

    class __w_radio(Radio):
        pass

    def setup_widgets(self, stateRadio: validation.StaticMap, *,
                      frameArgs: typing.Optional[typing.Mapping[str, typing.Any]] = None,
                      ):
        ''''''  # Internal, do not document
        if __debug__:
            badkeys = ('stateRadio', 'w_radio')
            assert all(n not in (frameArgs or {}) for n in badkeys), f'Invalid "frameArgs": invalid key @ {badkeys}'
        self.raw = RadioFrameUnlabelled(self, stateRadio=stateRadio, w_radio=self.__w_radio,
                                        **(frameArgs or {}))

    def setup_variable(self, variable: typing.Optional[var.Variable]) -> var.StaticMap:
        ''''''  # Override `var.aggregator` setup
        assert variable is None, f'{self!r}: Container Widget aggregator?'
        return self.raw.setup_variable(None)


class RadioFrameStateful(FrameStateful):
    '''A stateful frame filled with radio buttons.

    This is a bunch of `Radio` widgets inside a `FrameStateful`, all connected
    to the same internal variable. That variable is exposed as the only state,
    besides the `FrameStateful` state.

    The internal variable is created anew, there is no support for using an
    external variable. It can be access with ``self.raw.variable``.

    Args:
        stateRadio: Mapping from label to value. This should be a
            `StaticMap <validation.StaticMap>`.
        frameArgs: Extra arguments passed to the inner `FrameStateful` widget.
            Use ``radioArgs`` for the inner radio widget args, see
            `RadioFrameUnlabelled`.

    See Also:
        Use `CheckboxFrame` for a version of this with checkboxen, with extra
        features.

        Use `RadioFrame` for a labelled frame version of this.
    '''
    wstate_single = 'raw'
    '''Default value for `wstate_single <mixin.MixinStateContainer.wstate_single>`.'''

    class __w_radio(Radio):
        pass

    def setup_widgets(self, stateRadio: validation.StaticMap, *,
                      frameArgs: typing.Optional[typing.Mapping[str, typing.Any]] = None,
                      ):
        ''''''  # Internal, do not document
        if __debug__:
            badkeys = ('stateRadio', 'w_radio')
            assert all(n not in (frameArgs or {}) for n in badkeys), f'Invalid "frameArgs": invalid key @ {badkeys}'
        self.raw = RadioFrameUnlabelled(self, stateRadio=stateRadio, w_radio=self.__w_radio,
                                        **(frameArgs or {}))


class Canvas(tk.Canvas, mixin.SingleWidget):
    '''A canvas that draws a `diagram <diagram.Diagram>`.

    This is a canvas for drawing the given diagram.
    The diagram will be redrawn as the widget size changes, with a rate limit
    (see ``fps_redraw``, can be disabled).

    The diagram elements can be saved on the renderer, see ``saveElements``
    below. This is disable by default, it has a memory impact and most uses do
    not require this. The elements themselves can be accessed using `item`.

    No state is included, this is used to summarize state for other widgets.

    There is no Python documentation, see ``Tk`` :tk:`tk.Canvas <canvas.htm>`
    documentation.

    .. note::

        The only supported way to draw on the canvas is to use the `diagram
        <diagram.Diagram>` parameter.

    Args:
        diagram: Diagram to render.
        saveElements: Save a mapping between element identifiers and its
            corresponding `DiagramElement <diagram.DiagramElement>` on the
            renderer, see above for more information.
            Defaults to `False`.
        expand: Grow the widget to match the container grid size. This is
            usually supported for containers, but it is included here.
        fps_redraw: Rate limit for widget size redraw.
            Defaults to 30 fps, use `None` to disable this adaptation.

        parent: The parent widget. Can be a `RootWindow` or another `mixin.ContainerWidget`.

    Note:

        The underlying widget is not part of `ttk <tkinter.ttk>` like most others. All
        efforts are expended to make this an implementation detail, without
        practical effects.
    '''
    state_type = var.nothing

    def __init__(self, parent: mixin.ContainerWidget, diagram: diagram.Diagram, *,
                 expand: bool = True,
                 saveElements: typing.Optional[bool] = None,
                 fps_redraw: typing.Optional[int] = 30,
                 **kwargs):
        # Regular Widget setup
        self.init_single(vspec=None)
        kwargs.pop('state', None)  # Support no "raw" state changes
        assert isinstance(parent, tk.Misc), f'{parent} is not a valid parent widget'
        super().__init__(parent, **kwargs)  # tk.Canvas
        if expand:
            self.grid(sticky=tk.NSEW)
        # Renderer Setup
        self.renderer = drender.Renderer_TkCanvas(self, diagram,
                                                  saveElements=saveElements)
        self.diagram = self.renderer.diagram
        self.__ti_configure = self.tidle(self.renderer.redraw, key='__:renderer', immediate=False)
        # GUI State Tracker
        # - Since this is not a `ttk.Widget`, this need to be emulated
        self.__gstate: model.GuiState = model.GuiState(enabled=True, valid=True)
        # - Set the internal state out-of-the-box
        self.set_gui_state(_internal=True)
        # Events
        if fps_redraw is not None:
            assert fps_redraw > 0
            if fps_redraw > 60:
                warnings.warn(f'{self}: >60fps with Canvas might be a bit too much', stacklevel=2)
            self.__rl_configure = model.RateLimiter(self, self.__ti_configure.reschedule,
                                                    limit=1000 // fps_redraw)
            self.binding('<Configure>', self.__rl_configure.hit, key='__:config')
        self.__fps = fps_redraw

    # TODO: Implement `binding_tag`, see EntryMultiline.binding_tag
    # - Not exactly like that, they need to be reset when redrawing the elements.
    #   See https://tcl.tk/man/tcl8.6/TkCmd/canvas.htm#M37
    # - Mark new widgets as "new"; set the tags on those new widgets

    def get_gui_state(self) -> model.GuiState:
        ''''''  # Do not document
        if __debug__:
            logger_autostate.debug('State > %r', self.__gstate)
        # return a copy of the object
        return model.GuiState(**dict(self.__gstate.items()))

    def set_gui_state(self, state: typing.Optional[model.GuiState] = None, *, _internal: bool = False, **kwargs) -> model.GuiState:
        ''''''  # Do not document
        if state is None:
            state = model.GuiState(**kwargs)
        if __debug__:
            logger_autostate.debug('State < %r', state)
        # Adjust current state
        for sname, svalue in state.items():
            assert sname != '_internal'  # Should be impossible...
            if svalue is not None:
                setattr(self.__gstate, sname, svalue)
        # Adjust widget state
        diagram = self.renderer.diagram
        cfg: typing.MutableMapping[str, typing.Any] = {}
        if self.__gstate.enabled is True:
            cfg['state'] = tk.NORMAL
            if (bg := diagram.BACKGROUND) is not None:
                cfg['background'] = bg
        elif self.__gstate.enabled is False:
            cfg['state'] = tk.DISABLED
            if (bg := diagram.DISABLEDBACKGROUND or diagram.BACKGROUND) is not None:
                cfg['background'] = bg
        assert self.__gstate.valid is True
        assert self.__gstate.readonly is None  # Unsupported
        if __debug__:
            logger_autostate.debug('C %s', self.__gstate)
            logger_autostate.debug('| %s', cfg)
        self.configure(**cfg)
        assert state is not None
        return state

    def onClickElement(self, event: typing.Any):
        '''Callback to be called when clicking any element.

        Defaults to doing nothing.

        Available for subclass redefinition.

        See Also:
            Use `eselection` to get the clicked element identifier.
            Use `exy` to get the clicked position.
        '''
        pass

    def trigger_redraw(self, _a1: typing.Any = None, _a2: typing.Any = None):
        '''Trigger a canvas redraw, by (re)scheduling the idle timeout.

        Args:
            _a1: Optional, unused. This exists for API compatibility with
                bindings.
            _a2: Optional, unused. This exists for API compatibility with
                traces.
        '''
        self.__ti_configure.schedule()

    def redraw(self, *args, **kwargs):
        '''Redraw the canvas, using arbitrary arguments.

        This should only be used if you need to pass special arguments to the
        renderer.

        Args:
            args: Passed to the upstream `renderer function
                <drender.Renderer_TkCanvas.redraw>`.
            kwargs: Passed to the upstream `renderer function
                <drender.Renderer_TkCanvas.redraw>`.

        See Also:
            Use `trigger_redraw` in most situations.
        '''
        return self.renderer.redraw(*args, **kwargs)

    # Item Helpers
    def eselection(self) -> typing.Optional[int]:
        '''Get the current element identifier, that is, the item under the
        current mouse pointer.

        Only one element can be marked as "current" at a time.

        Returns:
            Return the current element identifier, or `None` when nothing is
            selected.
        '''
        clist = self.find_withtag(tk.CURRENT)
        if len(clist) != 1:
            assert len(clist) == 0, f'{self}: "{tk.CURRENT}" elements: {clist}'
            return None
        else:
            return clist[0]

    def exy(self, event) -> diagram.XY:
        '''Get the canvas coordinate for the given event.

        Usually, the even is a button click or a mouse movement. To be used
        inside the `onClickElement` function.

        Returns:
            A `XY <diagram.XY>` object representing the event's position, in
            canvas coordinates.
        '''
        assert event.x is not None and event.y is not None
        return diagram.XY(self.canvasx(event.x), self.canvasy(event.y))

    def genItemConfigure(self, eid: int, **state: typing.Any):
        '''Generate a function to configure the given canvas element.

        Arguments:
            eid: The element to configure.
            state: The new state to configure. This depends on the element
                type, see ``Tk`` :tk:`canvas common options <canvas.htm#M99>`.
        '''
        def genItemConfigure(event=None):
            self.itemconfigure(eid, **state)
        return genItemConfigure

    @property
    def hasElements(self) -> bool:
        '''Check if the elements or markers are being saved.

        This depends on the ``saveElements`` parameter when creating the
        instance.
        '''
        return self.renderer.eids is not None

    def item(self, eid: int) -> typing.Optional[diagram.DiagramElement]:
        '''Get the diagram element corresponding to the given element.

        This only works if the ``saveElements`` parameter is `True` when
        creating the `Canvas`, see `hasElements`.

        Args:
            eid: The element to consider

        Returns:
            Return the element itself if it is being saved, otherwise return
            `None`.
        '''
        if self.hasElements:
            return self.renderer.getElement(eid)
        else:
            raise ValueError(f'{self}: No saved items, see `saveElements` on widget definition')

    def itemMarker(self, eid: int) -> typing.Optional[str]:
        '''Get the marker corresponding to the given element.

        This only works if the ``saveElements`` parameter is not `None` when
        creating the `Canvas`, see `hasElements`.

        Args:
            eid: The element to consider

        Returns:
            Return the element marker if given on the diagram, otherwise return
            `None`.
        '''
        if self.hasElements:
            return self.renderer.getMarker(eid)
        else:
            raise ValueError(f'{self}: No saved items, see `saveElements` on widget definition')

    def itemCoords(self, eid: int) -> typing.Iterable[diagram.XY]:
        '''Find all the canvas element coordinates.

        Arguments:
            eid: The element to probe.

        Returns:
            Yield a series of `diagram.XY` for all available coordinates.
            Note that the meaning for each element type is different.
        '''
        _ccoord: typing.Optional[int] = None
        for v in self.coords(eid):
            if _ccoord is None:
                _ccoord = int(v)
                assert _ccoord == v, f'{self}:{eid}: C: {v!r}'
            else:
                assert int(v) == v, f'{self}:{eid}: C: {v!r}'
                yield diagram.XY(_ccoord, int(v))
                _ccoord = None
        assert _ccoord is None


class Separator(ttk.Separator, mixin.SingleWidget):
    '''A separator, just a single line for grouping widgets.

    This is a lightweight widget separator.

    When using this widget, the corresponding container should be marked as
    `layout_autoadjust <mixin.ContainerWidget.layout_autoadjust>`. This is
    warned on debug mode.

    There is no Python documentation, see ``Tk`` :tk:`ttk.Separator
    <ttk_separator.htm>` documentation.

    Args:
        layout: Select the widget orientation, `HORIZONTAL` or `VERTICAL`.
        expand: Grow the widget to match the container grid size.
            Grows only in the corresponding orientation, as given in ``layout``.
        pad: Padding settings. Depending on the widget `orientation`, this will
            select the horizontal or vertical padding, opposite to the orientation.

            Use `None` to disable. The size can be given as single integer or a
            integer tuple. Defaults to ``5`` pixels for both sides.

            See ``Tk`` :tk:`grid padx <grid.htm#M15>`/:tk:`grid pady
            <grid.htm#M16>` documentation.

        styleID: Set a style identifier. Combined with the widget type in
            `RootWindow.register_styleID`.
        parent: The parent widget. Can be a `RootWindow` or another
            `mixin.ContainerWidget`.

    See Also:
        Use a `FrameLabelled` for a "proper" widget group, with a name.
    '''
    state_type = var.nothing
    # Instance Parameters
    orientation: varOrientation
    '''Widget Orientation. Alternative between horizontal and vertical.

    Given as ``layout``. See also `HORIZONTAL` and `VERTICAL`.
    '''

    def __init__(self, parent: mixin.ContainerWidget, *,
                 layout: varOrientation,
                 expand: bool = True,
                 pad: typing.Union[None, int, typing.Tuple[int, int]] = (5, 5),
                 styleID: typing.Optional[str] = None,
                 ):
        assert isinstance(parent, tk.Misc), f'{parent} is not a valid parent widget'
        self.init_single(vspec=None)  # No state here
        super().__init__(parent,
                         style=parent.wroot.register_styleID(styleID, 'TSeparator'),
                         )  # ttk.Separator
        self.__pad = pad
        self.__expand = expand
        assert layout in (HORIZONTAL, VERTICAL), f'{self}: Invalid Orientation: {layout}'
        self._set(layout)

    def _set(self, orientation: varOrientation):
        ''''''  # Internal, do not document
        self.orientation = orientation
        assert orientation in (HORIZONTAL, VERTICAL)
        self.configure(orient=orientation)
        if (pad := self.__pad) is not None:
            assert isinstance(pad, int) or (isinstance(pad, tuple) and all(isinstance(e, int) for e in pad))
            if orientation == HORIZONTAL:
                self.grid(pady=pad)
            else:
                self.grid(padx=pad)
        if self.__expand:
            if orientation == HORIZONTAL:
                self.grid(sticky=tk.EW)
            else:
                self.grid(sticky=tk.NS)


class SecondaryWindow(tk.Toplevel, mixin.ContainerWidget):
    '''A secondary toplevel widget, similar to a second `RootWindow`.

    Note this is not the same as a new root window. The secondary window is
    part of the application itself, just like any other container, except it is
    rendered on a separate window, and can be scheduled and unscheduled
    separately.

    When the window is unscheduled, the widgets continue to exist, but hidden.

    This must be included inside other container widget, and it contributes to
    its state, but it is not automatically laid out.

    Args:
        label: The secondary window title. Can be given as a class variable.
            Technically optional, but should always be given.
        modal: Consider the window as a modal, meaning the corresponding
            `RootWindow` is disabled when this is scheduled.
            See also `modal` to retrieve this value.
            Defaults to `False`, both windows are independent.
        immediate: Schedule the window on creation.
            Defaults to `False`, the window is created and unscheduled on
            creation. There is no visual indication the window is shown
            anywhere.
        rpad: Recursively pad all container widgets.
            See `ContainerWidget.pad_container`.
            Disable with `None`, defaults to ``5`` pixels.
        swindowArgs: Extra arguments passed to the toplevel widget.

        swindow_name: Window Name. This is internal metadata, not exposed
            visually anywhere. Complemented by the Window Class Name, inherited
            from the correspoding `RootWindow`.
        parent: The parent widget.
            Can technically be any `MixinWidget <mixin.MixinWidget>`, but
            should *really* be a `RootWindow` or another `mixin.ContainerWidget`.
    '''
    label: typing.Optional[str] = None
    layout_expand = False  # Hardcode, `tk.Toplevel` has no parent grid to expand
    ignoreContainerLayout = True  # Does not participate in layout
    state_scheduled: var.Boolean
    '''Track the window scheduled state.

    This is a :py:mod:`variable <var>` that indicates the scheduled state. Can
    be written to to change the state.

    See Also:
        See also `scheduled <SecondaryWindow.scheduled>` for the low level
        state tracker.
    '''

    @dataclass
    class Style(model.WStyle):
        '''`SecondaryWindow` style object.

        These are the settings:

        Args:
            tool_window: When enabled, marks the window as a tool window, not a
                regular window. The precise meaning of this setting depends on the
                OS, see `fn.widget_toolwindow`.
                Defaults to `True`.
            resizable: Allow the window to be resized. See ``Tk`` :tk:`wm
                resizable <wm.htm#M59>` documentation.
                Defaults to `True`.
            transient: When enabled, marks the window as "dependent" on the
                `RootWindow`. See ``Tk`` :tk:`wm transient <wm.htm#M64>`
                documentation.
                Defaults to `True` on Linux, `False` otherwise.
            override_redirect: When enabled, marks the window to be ignored by
                the window manager. See ``Tk`` :tk:`wm override redirect
                <wm.htm#M56>` documentation.
                Defaults to `False`.
            center: Center the window on the corresponding `RootWindow` on
                schedule. See `fn.window_center`.
                Defaults to `True`.
        '''
        tool_window: bool = True
        resizable: bool = True
        transient: bool = sys.platform.startswith('linux')
        override_redirect: bool = False
        center: bool = True

    def __init__(self, parent: mixin.MixinWidget, *args,
                 label: typing.Optional[str] = None,
                 modal: bool = False,
                 immediate: bool = False,
                 rpad: typing.Optional[int] = 5,
                 swindowArgs: typing.Optional[typing.Mapping[str, typing.Any]] = None,
                 swindow_name: typing.Optional[str] = None,
                 style: Style = Style(_default=True),
                 **kwargs):
        assert self.ignoreContainerLayout
        self.wstyle = style
        chosen_label = fn.label_fallback(label, self.label)
        if style.override_redirect is False and chosen_label is None:
            raise exception.InvalidWidgetDefinition('Missing required label')
        assert isinstance(parent, tk.Misc), f'{parent} is not a valid parent widget'
        container_args = {
            **(swindowArgs or {}),
            # Set className (not exposed as className)
            'class': parent.wroot.winfo_class(),
        }
        super().__init__(parent, name=swindow_name or '',
                         cnf=container_args)  # tk.Toplevel
        self.init_container(*args, **kwargs)
        if rpad:  # TODO: Inherit value from `RootWindow`
            self.pad_container(pad=rpad, recursive=True)
        # Style
        if chosen_label is not None:
            self.title(chosen_label)
        else:
            assert style.override_redirect
        if self.wstyle.tool_window:
            fn.widget_toolwindow(self)
        if self.wstyle.transient:
            # Mark Toplevel as "dependent" on RootWindow
            self.wm_transient(master=parent.wroot)
        if not self.wstyle.resizable:
            self.wm_resizable(width=False, height=False)
        if self.wstyle.override_redirect:
            self.wm_overrideredirect(True)
        if self.wstyle.center:
            self.__ti_center = self.tidle(self.__onWindowCenter,
                                          key='__:center', immediate=False)
        if modal:
            self.binding('<Escape>', self.unschedule, key='__:modal:esc')
        # State Tracking
        # - Hide the window ASAP, will be shown with `trace_initial` below.
        #   `scheduled` after this will be `False`, as it should
        self.wm_withdraw()
        self.__modal: bool = modal
        self.state_scheduled = var.Boolean(value=immediate)
        self.__state_enabled = True
        var.trace(self.state_scheduled, self.__onScheduledChange,
                  trace_initial=True)
        if __debug__:
            import re
            p_delwin = self.protocol('WM_DELETE_WINDOW')
            # Make sure the function is "known", not overriden
            assert re.match(r'(\d+destroy)?', p_delwin)
        self.protocol('WM_DELETE_WINDOW', self.unschedule)
        if __debug__:
            # Check if parent is a container; not for subclasses
            if type(self) is SecondaryWindow and not isinstance(parent, mixin.ContainerWidget):
                warnings.warn(f'{self}: Use a container parent widget: {parent}', stacklevel=3)
        # Special Widget state
        self.wparent = parent

    def get_gui_state(self) -> model.GuiState:
        ''''''  # Do not document
        if __debug__:
            logger_autostate.debug('%s: enabled=%s alternate=%s', self, self.__state_enabled, self.state_scheduled.get())
        return model.GuiState(
            enabled=self.__state_enabled,
            alternate=self.state_scheduled.get(),
        )

    def set_gui_state(self, state: typing.Optional[model.GuiState] = None, _sub: bool = True, **kwargs) -> model.GuiState:
        ''''''  # Internal, do not document
        if state is None:
            state = model.GuiState(**kwargs)
        assert state is not None
        # State Processing
        scheduled = None
        if state.alternate is not None:
            scheduled = state.alternate
        if state.enabled is not None:
            self.__state_enabled = state.enabled
            if state.enabled is False:
                if __debug__:
                    if self.scheduled:
                        logger.debug('%s: Unschedule on Disable', self)
                scheduled = False
        assert state.valid is None  # Unsupported
        assert state.readonly is None  # Unsupported
        # State Manipulation
        if scheduled is not None:
            if __debug__:
                logger_autostate.debug('%s: scheduled=%s', self, scheduled)
            self.state_scheduled.set(scheduled)
        if _sub:
            if __debug__:
                logger_autostate.debug('%s: substate=%s', self, state)
            super().set_gui_substate(state)
        return state

    @property
    def modal(self) -> bool:
        '''Window modal state.'''
        # Keep it readonly
        return self.__modal

    @property
    def scheduled(self) -> bool:
        '''Window scheduled state.

        This is the underlying state, query the lower level state.

        See `state_scheduled` for a higher level API.
        '''
        state = self.wm_state()
        if state in (tk.NORMAL, 'zoomed'):
            # assert self.__state_enabled
            return True
        else:
            assert state in ('withdrawn', 'icon', 'iconic'), f'{self}: State={state}'
            return False

    @property
    def wlabel(self) -> str:
        '''Calculate the chosen label text.'''
        chosen_label = self.title()
        assert isinstance(chosen_label, str), f'{self}: Invalid frame Label: {chosen_label!r}'
        return chosen_label

    def __onWindowCenter(self) -> bool:
        if self.scheduled:
            return fn.window_center(self, self.wroot)
        else:
            return False

    def __onScheduledChange(self, sched: var.Variable, etype: str) -> None:
        assert etype in ('write', None)
        if __debug__:
            import os
            DEBUG_LIST = os.environ.get('TKMILAN_DEBUG', '').split(',')
        state_var = sched.get()
        state_w = self.scheduled
        if state_var:
            if not state_w:
                if __debug__:
                    if 'secondarywindow' in DEBUG_LIST:
                        logger.debug('%s: Map[etype=%r]', self, etype)
                if self.wstyle.transient:
                    self.wm_state(tk.NORMAL)
                else:
                    self.wm_deiconify()
                if self.wstyle.center:
                    self.__ti_center.reschedule()
            if self.__modal:
                self.grab_set()
        else:
            if state_w:
                if __debug__:
                    if 'secondarywindow' in DEBUG_LIST:
                        logger.debug('%s: UnMap[etype=%r]', self, etype)
                self.wm_withdraw()
            if self.__modal:
                self.grab_release()
        if __debug__:
            viewable = self.winfo_viewable()
            # If `winfo_viewable` does not return a boolean, it's too soon to check it
            if isinstance(viewable, bool):
                assert state_var == viewable, f'{self}: Error in Widget Manipulation [S{state_var}|W{viewable}]'
        assert state_var == self.scheduled, f'{self}: Error on Widget State Manipulation [S{state_var}|s{self.scheduled}]'
        state_final = None if etype is None else state_var
        assert bool(state_var) == bool(state_final)
        self.onScheduledChange(state_final)

    def onScheduledChange(self, state: typing.Optional[bool]) -> None:
        '''Callback to be called when the window is scheduled or unscheduled.

        Defaults to doing nothing.

        Available for subclass redefinition.

        Args:
            state: `True` if the window was scheduled, `False` if the window
                was unscheduled. `None` if this was called the first time. Usually
                `False` and `None` can do the same thing.
        '''
        pass

    def schedule(self, event: typing.Any = None) -> None:
        '''Schedule the window.

        Uses the underlying `state_scheduled`, with extra warnings to validate
        weird state changes.

        See Also:
            Use `tryschedule` for "automatic" state manipulations, to avoid
            spamming warnings.
        '''
        if self.__state_enabled:
            if __debug__:
                if self.scheduled:
                    logger.warning('%s: Already scheduled!', self)
            self.state_scheduled.set(True)
        else:
            if __debug__:
                logger.warning('%s: Disabled, cannot schedule', self)

    def tryschedule(self, event: typing.Any = None) -> None:
        '''Try scheduling the window.

        Uses the underlying `state_scheduled`, but don't force the new state if
        it is already scheduled.

        Very useful for attaching to buttons or events, without spamming
        warnings.

        See Also:
            Use `schedule` for "manual" state manipulations, to validate weird
            state changes.
        '''
        if self.__state_enabled and not self.state_scheduled.get():
            self.state_scheduled.set(True)
        assert self.state_scheduled.get() is True

    def unschedule(self, event: typing.Any = None) -> None:
        '''Unschedule the window.

        Uses the underlying `state_scheduled`, with extra warnings to validate
        weird state changes.

        See Also:
            Use `tryunschedule` for "automatic" state manipulations, to avoid
            spamming warnings.
        '''
        if not self.scheduled:
            if __debug__:
                logger.warning('%s: Already unscheduled!', self)
        self.state_scheduled.set(False)

    def tryunschedule(self, event: typing.Any = None) -> None:
        '''Try unscheduling the window.

        Uses the underlying `state_scheduled`, but don't force the new state if
        it is already unscheduled.

        Very useful for attaching to buttons or events, without spamming
        warnings.

        See Also:
            Use `unschedule` for "manual" state manipulations, to validate
            weird state changes.
        '''
        if self.__state_enabled and self.state_scheduled.get():
            self.state_scheduled.set(False)
        assert self.state_scheduled.get() is False

    def toggle(self, event: typing.Any = None) -> None:
        '''Toggle the window scheduled state.

        Uses the underlying `state_scheduled`, with extra warnings to validate
        weird state changes.

        Very useful for attaching to buttons or events.
        '''
        self.state_scheduled.set(not self.scheduled)

    def wait(self, *, forstate: typing.Optional[bool] = None) -> None:
        '''Wait for the scheduled state to change.

        Optionally, this can observe a specified state transition, using the
        ``forstate`` parameter. This is the "next" state the variable should
        have. The current state being the opposite (``not forstate``) is
        enforced.


        .. note:: This function blocks while the underlying variable does not
            change. This might depend on user input, the waiting time can be
            unpredictable or even infinite.

            To support async-ish operation on an arbitrary function `fn`, use
            ``widget.after(0, fn)`` to avoid blocking the main interface.

            See ``Tcl`` :tcl:`after <after.htm#M6>` documentation.

        Args:
            forstate: Check for a particular state transition. See above for
                further details. Optional, defaults to no state transition
                enforcement.

        See Also:
            The variable to track is `state_scheduled`. See the underlying
            ``Tk`` :tcl:`vwait <vwait.htm>` documentation.
        '''
        if __debug__:
            if not self.modal:
                logger.warning('%s: Waiting on non-modal secondary window', self)
        if forstate is not None:
            if __debug__:
                logger.debug('%s: <Wait State=%s', self, self.state_scheduled.get())
            if self.state_scheduled.get() is forstate:
                raise exception.InvalidWidgetState(f'{self}: < Schedule State == {forstate}')
        self.wait_variable(self.state_scheduled)
        if forstate is not None:
            if __debug__:
                logger.debug('%s: >Wait State=%s', self, self.state_scheduled.get())
            if self.state_scheduled.get() is not forstate:
                raise exception.InvalidWidgetState(f'{self}: > Schedule State != {forstate}')


class Tooltip(SecondaryWindow):
    '''A tooltip widget, a specialized `SecondaryWindow` attached to a widget.

    This serves to show a popup widget with extra information when hovering
    over an existing widget (identified as the parent widget). This is a
    ordinary `SecondaryWindow`, fully configurable as any other container.

    The popup is shown adjacent to the parent widget (see ``tt_position``) when
    hovering over it with the mouse after a configurable delay (see
    ``tt_delay``).
    It is hidden when the mouse moves away, or when the mouse touches the
    tooltip itself. The popup is not shown when the existing widget is
    disabled.

    As any `SecondaryWindow`, it can also be shown or hidden programatically,
    using `schedule <SecondaryWindow.schedule>`/`unschedule <SecondaryWindow.unschedule>`.
    See also `enable`/`disable` for a better way to control the visilibility changes.

    Does not contribute to the parent layout (being a `SecondaryWindow`),
    neither does it contribute to the parent state.

    Args:
        parent: The parent widget, will be monitored to open and show the
            tooltip.
        tt_position: How to position the tooltip in relation to the parent
            widget. Only a subset of directions is supported.
            Defaults to `CP.default`, which means `CP.S` (for now).
        tt_delay: Delay the tooltip scheduling by the given milliseconds, or
            show it immediately when `None`.
            Defaults to `None`.
        immediate: Setup tooltip events on creation. See `setup_tooltip`.
            Defaults to `True`.
        rpad: Recursively pad all container widgets.
            Optional, defaults to ``1`` (different from `RootWindow`).

        style: Configure the widget style.
    '''
    isAuto = None  # Isolate from GUI state
    ''''''  # Internal, do not document
    ttid: str
    '''Tooltip Identifier.

    This is an unique identifier for the tooltip itself. Used in several
    mappings that require unique keys.

    This is created automatically and read only.
    '''
    position: model.CP
    '''Relative position to show the tooltip.

    This is based on the parent widget, but can be overriden.
    '''

    @dataclass
    class Style(SecondaryWindow.Style):
        '''`Tooltip` style object.

        See `SecondaryWindow.Style` for upstream values, these are the differences:

        Args:
            override_redirect: Disabled by default, it's an error to be enabled
                at all.
            center: Disabled by default.
        '''
        override_redirect: bool = True
        center: bool = False

        if __debug__:
            def __post_init__(self):
                if self.override_redirect is False:
                    raise ValueError('Requires `override_redirect`')
                if self.center:
                    warnings.warn('Setting `center` to `True` is probably an error', stacklevel=3)

    def __init__(self, parent: mixin.MixinWidget,
                 *args,
                 tt_position: model.CP = model.CP.default,
                 tt_delay: typing.Optional[int] = None,
                 immediate: bool = True,
                 rpad: typing.Optional[int] = 1,
                 style: Style = Style(_default=True),
                 **kwargs):
        self.position = tt_position
        self._bindings_tooltip: typing.Optional[typing.Tuple[
            Binding,
            Binding,
            Binding,
        ]] = None
        swindowArgs = {
            'borderwidth': 2,
            'relief': tk.SOLID,
            **kwargs.pop('swindowArgs', {}),
        }
        super().__init__(parent, *args,
                         **{
                             'rpad': rpad, 'modal': False,
                             'swindowArgs': swindowArgs, 'style': style,
                             **kwargs,
                         },
                         )
        assert self.wparent is not None, f'{self}: Missing parent widget'
        self.ttid = 'tt-%d' % id(self)
        if tt_delay is None:
            self.__tout_schedule = None
        else:
            self.__tout_schedule = model.Timeout(self, self.__tryschedule,
                                                 timeout=tt_delay, immediate=False)
        if immediate:
            self.setup_tooltip()

    def setup_tooltip(self) -> None:
        '''Setup the tooltip events.

        See the ``immediate`` argument when creating the object.
        '''
        assert self.wparent is not None
        assert self._bindings_tooltip is None
        fn_schedule = self.__tryschedule if self.__tout_schedule is None else self.__tout_schedule.reschedule
        self._bindings_tooltip = (
            # Make sure this is the first, used in `enable`/`disable`
            self.wparent.binding('<Enter>', fn_schedule,
                                 key=f'__:tooltip:enter::{self.ttid}'),
            self.wparent.binding('<Configure>', self.adjustGeometryAuto,
                                 key=f'__:tooltip:cfg::{self.ttid}'),
            self.wparent.binding('<Leave>', self.__tryunschedule,
                                 key=f'__:tooltip:leave::{self.ttid}'),
        )
        self.binding('<Enter>', self.tryunschedule, key='__:enter')
        if __debug__:
            self.__fn_schedule = fn_schedule

    def __tryschedule(self, *args, **kwargs):
        # Do not schedule if the parent widget is disabled
        if self.wparent.gstate.enabled:
            return self.tryschedule(*args, **kwargs)

    def __tryunschedule(self, *args, **kwargs):
        if self.__tout_schedule is not None:
            self.__tout_schedule.unschedule()
        # Do not unschedule if the parent widget is disabled
        if self.wparent.gstate.enabled:
            return self.tryunschedule(*args, **kwargs)

    def adjustGeometry(self, widget: mixin.MixinWidget, *,
                       position: typing.Optional[model.CP] = None,
                       force: bool = False,
                       ) -> None:
        '''Adjust tooltip geometry in relation to the given widget.

        This adjusts the `SecondaryWindow` geometry in relation with the given
        widget.

        Args:
            widget: The widget to consider as parent.
            position: The relative position to show the tooltip.
                Defaults to `None`, overrides the intrinsic `position` when
                given.
            force: Force bogus size adjustment, when heuristics demand a true
                size calculation. Defaults to `False`, should not really be used.

        See Also:
            Use `adjustGeometryAuto` to pre-select the parent widget. This
            should be done in most situations.
        '''
        assert self.wparent is not None
        sposition = position or self.position
        # size_keep = False
        w = self.wparent.wgeometry
        logger_model_layout.debug(' W: %s', w)
        # if size_keep:  # Resize tooltip
        #     self.onSizeKeep(wW, wH)
        tt = self.wgeometry
        tt_label = ' T'
        assert tt.sized and (tt.w is not None and tt.h is not None)
        if not force and (tt.w, tt.h) == (1, 1):
            # First time the SecondaryWindow is scheduled
            # Find the true size
            self.state_scheduled.set(True)
            # if size_keep:
            #     self.update_idletasks()
            tt = self.wgeometry
            self.state_scheduled.set(False)
            tt_label = 'TT'
        else:
            # The read size is "correct"
            tt_label = ' T'
        logger_model_layout.debug('%s: %s', tt_label, tt)
        if sposition == model.CP.default:
            # TODO: Calculate the "right" location, depending on the window
            # location
            sposition = model.CP.S
        assert w.sized and (w.w is not None and w.h is not None)
        assert tt.sized and (tt.w is not None and tt.h is not None)
        if sposition == model.CP.N:
            ttX, ttY = (
                w.x - (tt.w - w.w) // 2,
                w.y - tt.h,
            )
        elif sposition == model.CP.S:
            ttX, ttY = (
                w.x - (tt.w - w.w) // 2,
                w.y + w.h,
            )
        else:
            raise NotImplementedError(f'Missing Support for CP: {sposition}')
        tt_new = model.WidgetGeometry(x=ttX, y=ttY)
        logger_model_layout.debug('  > %s: %s', sposition, tt_new)
        self.wm_geometry(tt_new.tk_geometry())

    def adjustGeometryAuto(self, event=None, **kwargs) -> None:
        '''Adjust tooltip geometry in relation to the parent widget.

        Args:
            event: Optional, unused. This exists for API compatibility with the
                ``onClick`` functions.
            kwargs: Passed to the upstream `adjustGeometry` function.

        See Also:
            Use `adjustGeometry` if you want to consider another widget as the "parent".
        '''
        assert self.wparent is not None, f'{self}: Missing parent widget'
        return self.adjustGeometry(self.wparent, **kwargs)

    def __enable_checkcontaining(self):
        # Enable the tooltip if the mouse is already on the widget.
        # This is what would happen if the `<Enter>` binding was triggered
        mxy = self.winfo_pointerxy()
        if self.wparent == self.winfo_containing(*mxy):
            self.__tryschedule()
            # `<Configure>` did not run
            assert self.wparent is not None
            _, _bcfg, _ = self._bindings_tooltip
            _bcfg.action()

    def enable(self, *, immediate: bool = True):
        '''Enable the tooltip itself.

        This means enabling (if needed) the binding that shows the popup.
        The ``immediate`` flag controls whether to attempt to show the popup if
        the mouse is already hovering over the widget.

        Args:
            immediate: Show the popup if the mouse is already hovering over the
                widget now.
                Defaults to `True`.
        '''
        assert self._bindings_tooltip is not None, f'{self}: Tooltip not Setup'
        assert isinstance(self._bindings_tooltip, tuple) and len(self._bindings_tooltip) == 3, f'{self}: Tooltip Setup not recognized'
        _benter, _bcfg, _ = self._bindings_tooltip
        assert _benter.sequence == '<Enter>' and _benter.action == self.__fn_schedule  # Check `__enable_checkcontaining`
        assert _bcfg.sequence == '<Configure>' and _bcfg.action == self.adjustGeometryAuto
        _benter_changed = _benter.tryenable()
        # Do nothing if the state has not changed
        if _benter_changed and immediate:
            self.after_idle(self.__enable_checkcontaining)  # No need for a `TimeoutIdle` here

    def disable(self, *, immediate: bool = True):
        '''Disable the tooltip itself.

        This means disabling (if needed) the binding that shows the popup.
        The ``immediate`` flag controls whether to attempt to hide the popup
        right away.

        Args:
            immediate: Hide the popup if is being shown now.
                Defaults to `True`.
        '''
        assert self._bindings_tooltip is not None, f'{self}: Tooltip not Setup'
        assert isinstance(self._bindings_tooltip, tuple) and len(self._bindings_tooltip) == 3, f'{self}: Tooltip Setup not recognized'
        _benter, _, _ = self._bindings_tooltip
        assert _benter.action == self.__fn_schedule
        _benter_changed = _benter.trydisable()
        # Do nothing if the state has not changed
        if _benter_changed and immediate:
            # Unschedule the tooltip immediately
            self.tryunschedule()

    def onScheduledChange(self, state: typing.Optional[bool]) -> None:
        '''Callback to be called when the tooltip is shown or hidden.

        Defaults to adjusting the geometry when showing the tooltip. Can be
        overriden, take care of calling this function at the same time. Use
        something like this:

        .. code:: python

            def onScheduledChange(self, state):
                pass  # Run Code Before `adjustGeometry`
                super().onScheduledChange(state)  # Call this function
                pass  # Run Code After `adjustGeometry`
        '''
        assert self.wparent is not None
        if state is True:
            self.adjustGeometry(self.wparent)


class TooltipSingleStatic(Tooltip):
    '''The most basic `Tooltip`, with a static `Label`.

    Leveraged by the `attachTooltip` function. In the common case, this tooltip
    is shown when hovering over the attached widget.

    This is the most basic tooltip that can be defined.
    To make further changes, subclass `Tooltip` directly.
    '''

    def setup_widgets(self, message: str, *, labelArgs=None):
        '''Setup the default child widgets, in this case a single ``message``
        `Label`.
        '''
        self.message = Label(self, label=message,
                             **(labelArgs or {}))


class TooltipValidation(Tooltip):
    '''A `Tooltip`, specialized for validation uses.

    Leveraged by the `putTooltip <mixin.MixinValidationSingle.putTooltip>`
    function.
    In the common case, this tooltip is shown when the attached widget is
    invalid, and hidden when the attached widget is valid. This is a static
    tooltip, the message never changes during the validation, it is intended
    for simple validations.

    If you need to change the default error message, subclass this and redefine
    `setup_tooltip_state`.

    To make further changes (add new widgets), subclass this and redefine
    `wstate_single`, `setup_widgets` and `setup_tooltip_state`.
    '''
    wstate_single = 'message'
    '''Default value for `wstate_single <mixin.MixinStateContainer.wstate_single>`.'''

    def setup_widgets(self):
        '''Setup the default child widgets, in this case a single ``message``
        `LabelStateful`.

        If you subclass this, don't forget to change `wstate_single
        <mixin.MixinStateContainer.wstate_single>` and `setup_tooltip_state`
        too.
        '''
        self.message = LabelStateful(self, justify=model.Justification.Left)

    def setup_tooltip_state(self, variable: typing.Optional[var.Spec]):
        '''Setup the error message when showing the tooltip.

        This is not a dynamic function, it is called only on widget creation,
        by the `putTooltip <mixin.MixinValidationSingle.putTooltip>` function.

        Args:
            variable: The attached widget variable, if available.
        '''
        if variable is None:
            if __debug__:
                warnings.warn(f'{self}: Not automatic Tooltip error message', stacklevel=3)
        elif isinstance(variable, (var.LimitBounded, var.LimitUnbounded)):
            self.wstate = f'Range: {variable.container}'
        elif isinstance(variable, (var.StaticList, var.StaticMap)):
            all_labels = variable.lall()
            if len(all_labels) < 4:
                label = '\n'.join((
                    'Options:',
                    *(
                        f'- {s}'
                        for s in all_labels
                    )
                ))
            else:
                label = f'{len(all_labels)} Options'
            self.wstate = label
        else:
            self.wstate = f'Variable: {variable}'


# Modify the parent to include the reference?
def SeparatorH(parent: mixin.ContainerWidget, **kwargs) -> Separator:
    '''Wrapper for `Separator`, forcing `orientation <Separator.orientation>`
    to `HORIZONTAL`'''
    kwargs['layout'] = HORIZONTAL
    return Separator(parent, **kwargs)


def SeparatorV(parent: mixin.ContainerWidget, **kwargs) -> Separator:
    '''Wrapper for `Separator`, forcing `orientation <Separator.orientation>`
    to `VERTICAL`'''
    kwargs['layout'] = VERTICAL
    return Separator(parent, **kwargs)


# Include Scrolled wrappers to disable the other direction
def ScrolledH(*args, **kwargs) -> Scrolled:
    '''Wrapper for `Scrolled`, forcing ``scrollVertical`` to `False`.

    This means the horizontal scrolling is automatic, while the vertical is
    disabled.
    '''
    assert 'scrollVertical' not in kwargs, 'Use a regular `Scrolled`'
    kwargs.update({
        'scrollVertical': False,
    })
    return Scrolled(*args, **kwargs)


def ScrolledV(*args, **kwargs) -> Scrolled:
    '''Wrapper for `Scrolled`, forcing ``scrollHorizontal`` to `False`

    This means the vertical scrolling is automatic, while the horizontal is
    disabled.
    '''
    assert 'scrollHorizontal' not in kwargs, 'Use a regular `Scrolled`'
    kwargs.update({
        'scrollHorizontal': False,
    })
    return Scrolled(*args, **kwargs)


# # Legacy Wrappers

def Spinbox(*args, **kwargs):
    '''Legacy wrapper for `SpinboxN`'''
    warnings.warn('Use `SpinboxN`, the widget state is slightly different', stacklevel=2)
    return SpinboxNum(*args, **kwargs)


def SpinboxNum(*args, **kwargs):
    '''Legacy wrapper for `SpinboxN`'''
    warnings.warn('Use `SpinboxN`, just a rename', stacklevel=2)
    return SpinboxN(*args, **kwargs)


def Combobox(*args, **kwargs):
    '''Legacy wrapper for `ComboboxN`'''
    warnings.warn('Use `ComboboxN`, the widget state is slightly different', stacklevel=2)
    return ComboboxN(*args, **kwargs)


def ComboboxRaw(*args, **kwargs):
    '''Legacy wrapper for `ComboboxN`'''
    warnings.warn('Use `ComboboxN`, just a rename', stacklevel=2)
    return ComboboxN(*args, **kwargs)


def ComboboxMap(*args, **kwargs):
    '''Legacy wrapper for `ComboboxN`'''
    warnings.warn('Use `ComboboxN`, just a rename', stacklevel=2)
    return ComboboxN(*args, **kwargs)


def Entry(*args, **kwargs):
    '''Legacy wrapper for `EntryRaw`'''
    warnings.warn('Use `EntryRaw`, just a rename', stacklevel=2)
    return EntryRaw(*args, **kwargs)


def RadioFrame(*args, **kwargs):
    '''Legacy wrapper for `RadioFrameLabelled`'''
    warnings.warn('Use `RadioFrameLabelled`, just a rename', stacklevel=2)
    return RadioFrameLabelled(*args, **kwargs)


def RadioFrame_Raw(*args, **kwargs):
    '''Legacy wrapper for `RadioFrameUnlabelled`'''
    warnings.warn('Use `RadioFrameUnlabelled`, just a rename', stacklevel=2)
    return RadioFrameUnlabelled(*args, **kwargs)


RadioFrame.RadioFrame_Raw = RadioFrame_Raw  # type: ignore[attr-defined]
'''Legacy wrapper for `RadioFrameUnlabelled`'''
