'''All the mixin classes, to be reused internally.
'''
import logging
import warnings
import typing
from dataclasses import dataclass
import collections
from functools import cached_property, partial, wraps

from . import fn
from . import model
from . import var as tkmilan_var  # Possible name alias
from . import autolayout
from . import exception
from . import validation

import tkinter as tk

ProxyWidgetT = typing.TypeVar('ProxyWidgetT', bound='MixinWidget')
if typing.TYPE_CHECKING:
    from . import mixin
    from . import RootWindow, Tooltip

logger = logging.getLogger(__name__)
logger_traces = logging.getLogger('%s.traces' % __name__)
logger_valid = logging.getLogger('%s.valid' % __name__)
logger_grid = logging.getLogger('%s.grid' % __name__)
if __debug__:
    logger_autolayout = logging.getLogger('%s.autolayout' % __name__)

    def debuglog__state_set(widget) -> bool:
        # # Single Widget
        # return str(widget) == '$WIDGET'
        # # Hierarchy (Children):
        # return str(widget).startswith('$WIDGET')
        # # Hierarchy (Parents and Children):
        # return str(widget).startswith('$WIDGET') or '$WIDGET'.startswith(str(widget))
        return False

WEIRD_WIDGET_NAME = (  # Weird Widget `dir` names, these cause trouble
    '_last_child_ids',
    'wroot',
)
WIDGET_VALIDATION_CFG = (
    'validate',
    'validatecommand',
    'invalidcommand',
)


# Technically a model, but internal
@dataclass
class ContainerState:
    '''Full container state.

    Arguments:
        swidgets: Single Widgets
        cwidgets: Container Widgets
        variables: Attached Variables
        wvariables: Mapping VariableID -> Variable object
        vwidgets: Mapping VariableID -> Widget Name list
        vid_upstream: Set of upstream VariableID
        hswidgets: Helper Single Widgets.
            Technically not considered as "state", only matters for tracing
            purposes.
            Includes widgets that might be ignored using `ignoreContainerState
            <MixinWidget.ignoreContainerState>`, check this when using if this
            is not intended.
        hcwidgets: Helper Container Widgets.
            Technically not considered as "state", only matters for tracing
            purposes.
    '''
    swidgets: 'typing.Mapping[str, SingleWidget]'
    cwidgets: 'typing.Mapping[str, ContainerWidget]'
    variables: 'typing.Mapping[str, tkmilan_var.Variable]'
    wvariables: 'typing.Mapping[str, tkmilan_var.Variable]'
    vwidgets: typing.Mapping[str, typing.Sequence[str]]
    vid_upstream: typing.Set[str]
    hswidgets: 'typing.Set[SingleWidget]'
    hcwidgets: 'typing.Set[ContainerWidget]'


class MixinState:
    '''Mixin for all stateful widgets.'''

    wstate_static: bool = True
    '''
    Define if the `MixinState.setup_state` cache is static. or a callable for dynamic
    calculations.

    See `stateSetup`.
    '''

    isNoneable: typing.Optional[bool] = None
    '''Define if a `None` result leads to skipping this widget on the state result.

    This applies to both static and dynamic state calculations. Defaults to
    `None`, so that it can be overriden by subclasses.

    For dynamic calculations, the results for some widgets might vary depending
    on where the root state starts, so they will be unpredictable. When the
    state is taken as a whole (the simple usage), it is predictable.

    Note:
        The default `None` value for this variable is invalid. The subclass
        **must** define this.
    '''

    def setup_state(self):
        '''Define an object that will be cached forever.

        This can have a static object, or a dynamic `callable`.

        See `MixinState.wstate_static`, `stateSetup`.
        '''
        raise NotImplementedError

    @cached_property
    def stateSetup(self):
        '''Obtain the state setup.

        This takes into account the `wstate_static` flag, producing a static object
        or a callable.

        This should always be used, `MixinState.setup_state` is only a definition.
        '''
        assert self.isNoneable is not None, f'{self} needs `isNoneable` choice'
        if self.wstate_static is True:
            return self.setup_state()
        else:
            return self.setup_state

    def state_get(self, **kwargs):
        '''Define how to get the widget state.

        The kwargs are only passed for Dynamic State widgets
        '''
        raise NotImplementedError

    def state_set(self, state, substate: bool, **kwargs):
        '''Define how to set the widget state.

        The kwargs are only passed for Dynamic State widgets
        '''
        raise NotImplementedError

    # Wrapper functions for the property
    def wstate_get(self, **kwargs):
        return self.state_get(**kwargs)

    def wstate_set(self, state, substate: bool = False, **kwargs):
        return self.state_set(state, substate=substate, **kwargs)

    wstate = property(wstate_get, wstate_set, doc='Widget State')


class MixinStateSingle(MixinState):
    '''
    Mixin class for single widgets.

    Note:
        When subclassing this, define `MixinState.setup_state` to return the
        variable containing the widget state.
    '''
    wstate_static: bool = True

    def state_get(self, **kwargs):
        assert len(kwargs) == 0, f'`kwargs` does not apply here: {kwargs=!r}'
        return self.stateSetup.get()

    def state_set(self, state, substate: bool, **kwargs):
        assert len(kwargs) == 0, f'`kwargs` does not apply here: {kwargs=!r}'
        if __debug__:
            self_names = str(self).split('.')[1:]
            dlog = debuglog__state_set(self)
            if substate is True:  # Just skip it silently?
                warnings.warn("`substate` doesn't apply here", stacklevel=3)
            if dlog:  # Debug single widget state flow
                logger.debug('%s: %s',
                             '>' * len(self_names),
                             self,
                             )
        self.stateSetup.set(state)


class MixinStateContainer(MixinState):
    '''Mixin class for container widgets.

    To ignore a container state, define this on the subclass:

    .. code:: python

        def setup_state(self, **kwargs):
            return {}

    Note:
        When subclassing this, define `MixinState.setup_state` to return a
        dictionary mapping subwidget identifier to `WidgetDynamicState`.
    '''
    wstate_static: bool = False
    wstate_single: typing.Union[None, bool, str] = None
    '''
    Mark the container state as "single", including only the state for this child.
    The value should be a string indicating the state key.

    `True` means the only existing key should be considered. This should be
    used only when the key name is dynamic and cannot be statically determined.

    Should only be enabled where there is a single child element, this is
    verified when getting the value. Use `MixinWidget.ignoreContainerState` to
    ignore other widgets.

    This creates no performance improvements, it is only useful to simplify the
    state.

    .. note::

        To skip the warning about a container with a single widget on debug
        binaries, mark the widget class with ``wstate_single = False``.
        This works exactly as the default `None`, without the warning.
    '''
    wstate_single_wstate: bool = False
    '''When the container state is "single", particularly setting
    ``wstate_single=True``, mark the state as correctly empty, so the parent
    function can turn a `WState`/`WStateR` into a single element.

    Should only be enabled where `wstate_single` is set to True and there are
    no child elements, this is verified when getting the value.
    '''

    def state_get(self, *,
                  vid_upstream: typing.Optional[typing.Set[str]] = None,
                  **kwargs,
                  ) -> typing.Any:
        assert len(kwargs) == 0, f'`kwargs` does not apply here: {kwargs=!r}'
        assert self.wstate_single != '', f'{self}: Invalid "wstate_single" marking, cannot be an empty string'
        state = {}
        for identifier, wds in self.stateSetup(vid_upstream=vid_upstream).items():
            result = wds.getter()
            if wds.noneable and result is None:
                pass  # Skip
            else:
                state[identifier] = result
        if self.wstate_single is None or self.wstate_single is False:
            # - Multiple WState
            if len(state) == 0:
                return None
            else:
                if __debug__:
                    wid0 = list(state)[0]
                    # Do not warn if:
                    # - `:` in widget key
                    #   - Internal Widgets
                    # - `wstate_single is False`
                    #   - Manual Override, `None` is the default
                    if len(state) == 1 and ':' not in wid0 and self.wstate_single is not False:
                        # TODO: Use `warnings.warn`, but this is used from an `after` function, the trace is lost.
                        logger.warning('%s: This widget can be marked "wstate_single": `%s`', self, wid0)
                return state
        else:
            # - Single WState (wstate_single)
            if __debug__:
                if self.wstate_single_wstate is True and self.wstate_single is not True:
                    logger.warning('%s: This widget is wrongly marked "wstate_single_wstate"', self)
            if len(state) == 0:
                assert self.wstate_single is True, f'{self}: Invalid "wstate_single" marking, no elements'
                assert self.wstate_single_wstate, f'{self}: Missing "wstate_single_wstate" marking'
                return None
            else:
                assert len(state) == 1, f'{self}: Invalid "wstate_single" marking, {len(state)} elements'
                single_key: str
                if self.wstate_single is True:
                    single_key = list(state)[0]
                else:
                    assert isinstance(self.wstate_single, str)
                    single_key = self.wstate_single
                assert single_key in state, f'{self}: Invalid "wstate_single" marking, missing key'
                return state[single_key]

    def state_set(self, state, substate, *,
                  vid_upstream: typing.Optional[typing.Set[str]] = None,
                  **kwargs,
                  ) -> None:
        assert len(kwargs) == 0, f'`kwargs` does not apply here: {kwargs=!r}'
        assert self.wstate_single != '', f'{self}: Invalid "wstate_single" marking, cannot be an empty string'
        if __debug__:
            self_names = str(self).split('.')[1:]
            dlog = debuglog__state_set(self)
            if dlog:  # Debug container widget state flow
                logger.debug('%s: %s%s [substate=%s]%s',
                             '>' * len(self_names),
                             self,
                             '' if self.wstate_single is None else f' [{self.wstate_single}]',
                             substate,
                             '' if vid_upstream is None else f' [vid_upstream={len(vid_upstream)}={" ".join(sorted(vid_upstream))}]',
                             )
        for identifier, wds in self.stateSetup(vid_upstream=vid_upstream).items():
            # Skip State Setup:
            # - "noneable" and the state is None
            if wds.noneable and state is None:
                skip = True
                if __debug__:
                    skip_why = 'noneable state=None'
            else:
                if self.wstate_single is None or self.wstate_single is False:
                    # - Multiple WState
                    #   - Check for "noneable"
                    #   - Check for (substate=True)
                    skip = (substate or wds.noneable) and identifier not in state
                    if __debug__:
                        skip_why = 'multiple'
                else:
                    # - Single WState (wstate_single)
                    #   - Skip all but the given key
                    #   - Do not skip when True
                    skip = self.wstate_single is not True and self.wstate_single != identifier
                    if __debug__:
                        skip_why = 'single'
            if skip:
                if __debug__:
                    if dlog:
                        logger.debug('%s|> Skip "%s" (%s)', ' ' * len(self_names), identifier, skip_why)
                pass
            else:
                if __debug__:
                    if dlog:
                        logger.debug('%s|>  Set "%s"', ' ' * len(self_names), identifier)
                if self.wstate_single:
                    assert (self.wstate_single is True) or isinstance(self.wstate_single, str)
                    widget_state = state
                else:
                    assert self.wstate_single in (None, False)
                    assert identifier in state, f'{identifier=} {state=}'
                    widget_state = state[identifier]
                if wds.container:
                    wds.setter(widget_state, substate)
                else:
                    wds.setter(widget_state)


class MixinWidget:
    '''Parent class of all widgets.

    Args:
        gkeys: Append widget-specific `model.GuiState` keys to common list
            `model.GUI_STATES_common`.

    .. autoattribute:: _bindings
    .. autoattribute:: _tidles
    '''

    wparent: 'typing.Optional[MixinWidget]' = None
    '''A reference to the parent widget.'''
    gkeys: typing.FrozenSet[str]
    '''The supported `model.GuiState` keys.'''
    isAuto: typing.Optional[bool]
    '''Marker that tracks the automatic state setup.

    One of the following values:

    - `True`: Include on automatic widget and GUI states. Default.
    - `False`: No automatic widget state, but keep in on the GUI state. This
      makes the widget stateless, but it still participates in the automatic
      GUI state changes.
      Very useful for helper containers.
    - `None`: No automatic widget nor GUI states. This makes the widget
      basically invisible.

    .. note::

        This was called ``isHelper`` in older versions.
        Turn all ``isHelper=False`` into ``isAuto=False`` (unless you have a
        good reason to isolate GUI state).

    See Also:
        See `putAuto` for an ergonomic way to set this on child widgets.
    '''
    ignoreContainerState: bool = False
    '''Ignore this widget's state when included on a container.

    See Also:
        See `putIgnoreState` for an ergonomic way to set this on child widgets.
    '''
    ignoreContainerLayout: bool = False
    '''Ignore this widget when performing automatic layout.

    See Also:
        See `putIgnoreLayout` for an ergonomic way to set this on child widgets.
    '''
    # TODO: Merge isAuto/ignoreContainerState/ignoreContainerLayout into a
    # single `isAuto` to control the three flags: widget state, GUI state,
    # automatic layout
    ignoreContainerTrace: bool = False
    '''When this widget is included on a container, do not consider it for
    tracing purposes.

    See Also:
        See `putIgnoreTrace` for an ergonomic way to set this on child widgets.
    '''
    styleID: typing.Optional[str] = None
    '''StyleID for this widget. See `RootWindow.styleIDs`.'''
    wproxy: 'typing.Optional[MixinWidget]' = None
    '''Link to the corresponding proxy widget, if exists.

    See Also:
        The base `ProxyWidget` class.
    '''
    proxee: 'typing.Optional[MixinWidget]' = None
    '''Link to the corresponding proxied widget, if exists.

    See Also:
        The base `ProxyWidget` class.
    '''
    tt: 'typing.Optional[Tooltip]' = None
    '''The simply attached tooltip.

    It is possible to attach multiple tooltips, but that is usually rare. This
    should only be modified by the `attachTooltip` function.

    See Also:
        The related `attachTooltip` function.
    '''
    _bindings: typing.MutableMapping[str, model.Binding]
    '''Store all widget `Binding` objects, keyed by name (see `binding`).'''
    _tidles: typing.MutableMapping[str, model.TimeoutIdle]
    '''Store some widget `TimeoutIdle` objects, keyed by name (see `tidle`).'''

    def __init__(self, *,
                 gkeys: typing.Optional[typing.Iterable[str]] = None,
                 ):
        assert not hasattr(self, 'isHelper'), f'{self.__class__.__qualname__}: Invalid "isHelper" marker, migrate to "isAuto"'
        self.isAuto: typing.Optional[bool] = getattr(self, 'isAuto', True)
        self._bindings = {}
        self._tidles = {}
        gk = set(model.GUI_STATES_common)
        if gkeys is not None:
            gk.update(gkeys)
        self.gkeys = frozenset(gk)

    @cached_property
    def wroot(self) -> 'RootWindow':
        '''Get the root widget, directly.

        Does not use the ``wparent`` property to crawl the widget tree to the
        top, so that it might be called before that setup is done (during setup
        of lower widgets, for example).
        '''
        assert isinstance(self, (tk.Widget, tk.Tk, tk.Toplevel)), f'{self} is not a valid widget'
        widget = self.nametowidget('.')
        if __debug__:
            from . import RootWindow  # For typechecking
        assert isinstance(widget, RootWindow)
        return widget

    def wroot_search(self) -> 'RootWindow':
        '''Alternative to `wroot` that crawls the widget tree.

        Use the `wparent` proprety.

        See Also:
            `wroot`: Simpler alternative to this function, crawling the widget
            tree. Requires all widgets to be stable.
        '''
        if self.wparent is None:
            # This might be triggered if called before all widgets are stable
            if __debug__:
                from . import RootWindow  # For typechecking
            assert isinstance(self, RootWindow), f'Invalid "root" widget: {self!r}'
            return self
        else:
            return self.wparent.wroot_search()

    def binding(self, sequence: str, *args, key: typing.Optional[str] = None, immediate: bool = True, **kwargs) -> model.Binding:
        '''Create a `model.Binding` for this widget.

        Stores all widget bindings on a per-instance dictionary, for later
        usage. Note that all dictionary keys must be different. For the same
        bindings on a single widget, this requires passing the ``key``
        argument.

        See the ``Tk`` :tk:`bind <bind.htm>` documentation.

        Args:
            key: Optional. Defaults to the ``sequence`` itself. Useful to
                support multiple bindings on the same sequence.
            immediate: Passed to the upstream object, default to enabling the
                binding on creation. This is the opposite from upstream.

        All other arguments are passed to the `model.Binding` object.
        '''
        name = key or sequence
        if name in self._bindings:
            raise ValueError(f'Repeated Binding for "{sequence}" in {self!r}. Change the "key" parameter.')
        self._bindings[name] = model.Binding(self, sequence, *args, immediate=immediate, **kwargs)
        return self._bindings[name]

    def tidle(self, action: typing.Callable, *args, key: typing.Optional[str] = None, **kwargs) -> model.TimeoutIdle:
        '''Create a `model.TimeoutIdle` for this widget.

        Stores all idle timeouts created using this function on a per-instance
        dictionary, for later usage. If the ``action`` is not a "real"
        function, this requires passing the ``key`` argument.

        Args:
            key: Optional. Defaults to the ``action`` name.

        All other arguments are passed to `model.TimeoutIdle` object.
        '''
        name = key or action.__name__
        if name in self._tidles:
            raise ValueError(f'Repeated TimeoutIdle for "{name}" in {self!r}.')
        self._tidles[name] = model.TimeoutIdle(self, action, *args, *kwargs)
        return self._tidles[name]

    @property
    def size_vroot(self) -> 'model.PixelSize':
        '''The VirtualRoot size.

        This is a global property, but it's available in every widget.
        '''
        assert isinstance(self, (tk.Widget, tk.Tk)), f'{self} is not a valid tkinter.Widget'
        return model.PixelSize(
            width=self.winfo_vrootwidth(),
            height=self.winfo_vrootheight(),
        )

    @property
    def size_screen(self) -> 'model.PixelSize':
        '''The screen size.

        This is a global property, but it's available in every widget.
        '''
        assert isinstance(self, (tk.Widget, tk.Tk)), f'{self} is not a valid tkinter.Widget'
        return model.PixelSize(
            width=self.winfo_screenwidth(),
            height=self.winfo_screenheight(),
        )

    def setup_grid(self, fmt: typing.Union[str, model.GridCoordinates], **kwargs) -> None:
        '''Configure the grid for the current widget.

        ``fmt`` can be given as a `model.GridCoordinates`, or as a single
        `str`, to be parsed by `model.GridCoordinates.parse`.

        Args:
            fmt: The grid configuration format. Specified above.
            kwargs: Passed upstream

        See Also:
            `wgrid`: Get the current widget grid coordinates.
        '''
        assert isinstance(self, (tk.Widget, tk.Tk)), f'{self} is not a valid tkinter.Widget'
        if isinstance(fmt, str):
            fmt = model.GridCoordinates.parse(fmt)
        kwargs.update(fmt.dict())
        assert self.ignoreContainerLayout is False, f'{self}: Layout is being ignored'
        self.grid(**kwargs)

    @property
    def wgrid(self) -> typing.Optional[model.GridCoordinates]:
        '''Get the widget grid coordinates, if the widget is visible.

        Returns:
            Return a `model.GridCoordinates` object with the widget
            information. If the wiget was hidden, return `None`.

            This is also available for the root widget (`wroot`) for
            completeness, but that doesn't really correspond to any grid,
            return `None`.

            This is also available for `SecondaryWindow` widgets, but it does
            not support any kind of grid, return `None`.

        See Also:
            `setup_grid`: Change the widget grid coordinates.
        '''
        if self == self.wroot:
            assert isinstance(self, tk.Tk)
            return None
        elif isinstance(self, tk.Toplevel):
            # Special widget, does not support `grid_info`
            assert self.ignoreContainerLayout
            if __debug__:
                from . import SecondaryWindow  # For typechecking
                assert isinstance(self, SecondaryWindow)
            return None
        else:
            assert isinstance(self, tk.Widget), f'{self} is not a valid tkinter.Widget'
            # If the grid information doesn't exist, default to a single frame
            # Force elements to integer, on tcl v8.5 they are returned as strings
            ginfo = self.grid_info()
            if ginfo:
                return model.GridCoordinates(
                    row=int(ginfo.get('row', 0)),
                    rowspan=int(ginfo.get('rowspan', 1)),
                    column=int(ginfo.get('column', 0)),
                    columnspan=int(ginfo.get('columnspan', 1)),
                )
            else:
                return None

    @property
    def wview(self) -> typing.Optional[model.WidgetView]:
        '''Get the widget view information.

        Returns:
            Return a `model.WidgetView` object with the view information, if
            the widget supports scrolling in at least one axis. If the widget
            does not support scrolling, returns `None`.
        '''
        assert isinstance(self, tk.Widget), f'{self} is not a valid tkinter.Widget'
        return model.WidgetView.fromwidget(self)

    @property
    def wgeometry(self, *, size: bool = True) -> model.WidgetGeometry:
        '''Get the widget geometry information.

        Args:
            size: Consider the widget size, width and height.

        Returns:
            Return a `model.WidgetGeometry` object with the widget information.
        '''
        assert isinstance(self, tk.Misc), f'{self} is not a valid widget'
        x, y = self.winfo_rootx(), self.winfo_rooty()
        if size:
            w, h = self.winfo_width(), self.winfo_height()
        else:
            w, h = None, None
        return model.WidgetGeometry(
            x, y,
            w, h,
        )

    def get_gui_state(self) -> model.GuiState:
        if __debug__:
            from . import RootWindow, SecondaryWindow  # For typechecking
        assert isinstance(self, (tk.ttk.Widget, RootWindow)), f'{self} is not a valid widget'
        assert not isinstance(self, SecondaryWindow), f'{self} is not a valid widget'
        state: typing.MutableMapping[str, typing.Optional[bool]] = {}
        for estr in self.gkeys:
            itk = model.GUI_STATES[estr]
            state[estr] = self.instate([itk.gstr()])
            # logger.debug('  [%s] » %s', itk.gstr(), state[estr])
        rval = model.GuiState(**state)
        # if __debug__:
        #     logger.debug('State > %r', rval)
        return rval

    def set_gui_state(self, state: typing.Optional[model.GuiState] = None, **kwargs) -> model.GuiState:
        assert isinstance(self, tk.ttk.Widget), f'{self} is not a valid tkinter.ttk.Widget'
        if state is None:
            state = model.GuiState(**kwargs)
        assert state is not None
        self.state(state.states_tk(widget=self))
        if self.wproxy:
            # if __debug__:
            #     logger.debug('  Set Widget Proxy State')
            self.wproxy.gstate = state
        return state

    # Wrapper functions for the property
    def gstate_get(self) -> model.GuiState:
        return self.get_gui_state()

    def gstate_set(self, state: model.GuiState):
        # Don't store the return object
        self.set_gui_state(state)

    # TODO: This can be even better
    # Support `widget.gstate.enabled = NEW_VALUE`
    # Not a property, but a class that changes `self`
    gstate = property(gstate_get, gstate_set, doc='GUI State')

    def genabled(self, state: typing.Optional[bool]):
        '''Manipulate the `GuiState <model.GuiState>` ``enabled`` state.

        Equivalent to ``self.gstate = model.GuiState(enabled=state)``.

        Args:
            state: The ``enabled`` state.
        '''
        return self.set_gui_state(enabled=state)

    def genabled_toggle(self,
                        _arg1: typing.Any = None,
                        _arg2: typing.Any = None,
                        _arg3: typing.Any = None,
                        ):
        '''Toggle the `GuiState <model.GuiState>` ``enabled`` state.

        Equivalent to ``self.gstate = model.GuiState(enabled=not self.gstate.enabled)``.

        Args:
           _arg1: Unused, included for API compatibility with ``Tk`` events
           _arg2: Unused, included for API compatibility with ``Tk`` traces
           _arg3: Unused, included for API compatibility with ``Tk`` event loop.
        '''
        return self.set_gui_state(enabled=not self.gstate.enabled)

    def galternate_toggle(self,
                          _arg1: typing.Any = None,
                          _arg2: typing.Any = None,
                          _arg3: typing.Any = None,
                          ):
        '''Toggle the ``alternate`` `model.GuiState` state, if available.

        Equivalent to ``self.alternate = model.GuiState(enabled=not self.gstate.alternate)``.

        For performance reasons, the validation for ``alternate`` state is only
        done on debug mode.

        Args:
           _arg1: Unused, included for API compatibility with ``Tk`` events
           _arg2: Unused, included for API compatibility with ``Tk`` traces
           _arg3: Unused, included for API compatibility with ``Tk`` event loop.
        '''
        assert 'alternate' in self.gkeys, f'{self}: This widget class ({self.__class__.__qualname__}) does not support "alternate" GuiState'
        self.set_gui_state(alternate=not self.gstate.alternate)

    def putHelper(self, value: bool = True) -> 'MixinWidget':
        '''DEPRECATED. See `putAuto`.'''
        raise NotImplementedError('DEPRECATED')  # TODO: Remove on v0.40

    # TODO: On Python 3.11:: -> typing.Self
    def putAuto(self, value: typing.Optional[bool] = False) -> 'MixinWidget':
        '''Set the `isAuto` marker on itself.

        See `MixinWidget.isAuto` for more information on the possible values.
        Defaults to `False`.

        This is designed to be used inside the `setup_widgets
        <ContainerWidget.setup_widgets>` function, like this:

        .. code:: python

            def setup_widgets(self, ...):
                self.w1 = Widget(self, ...).putAuto()      # No GUI  No State
                self.w1 = Widget(self, ...).putAuto(None)  # No GUI Yes State

        This is usually called "method chaining", or "fluent interface".
        '''
        if __debug__:
            from . import SecondaryWindow  # For typechecking
            if isinstance(self, SecondaryWindow):
                logger.warning('%s: This is a special widget type, it does nothing', self)
        if value is True:
            warnings.warn(f'Redundant `putAuto` @ {self!r}')
        self.isAuto = value
        return self

    # TODO: On Python 3.11:: -> typing.Self
    def putIgnoreState(self, value: bool = True) -> 'MixinWidget':
        '''Set the `ignoreContainerState` marker on itself.

        This is designed to be used inside the `setup_widgets
        <ContainerWidget.setup_widgets>` function, like this:

        .. code:: python

            def setup_widgets(self, ...):
                self.w1 = Widget(self, ...).putIgnoreState()

        This is usually called "method chaining", or "fluent interface".
        '''
        # TODO: Move this "method chaining" to a common document.
        self.ignoreContainerState = value
        return self

    # TODO: On Python 3.11:: -> typing.Self
    def putIgnoreLayout(self, value: bool = True) -> 'MixinWidget':
        '''Set the `ignoreContainerLayout` marker on itself.

        This is designed to be used inside the `setup_widgets
        <ContainerWidget.setup_widgets>` function, like this:

        .. code:: python

            def setup_widgets(self, ...):
                self.w1 = Widget(self, ...).putIgnoreLayout()

        This is usually called "method chaining", or "fluent interface".
        '''
        # TODO: Move this "method chaining" to a common document.
        if __debug__:
            from . import SecondaryWindow  # For typechecking
            assert not isinstance(self, SecondaryWindow), f'{self}: Unsupported "ignoreContainerLayout"'
        self.ignoreContainerLayout = value
        return self

    # TODO: On Python 3.11:: -> typing.Self
    def putIgnoreTrace(self, value: bool = True) -> 'MixinWidget':
        '''Set the `ignoreContainerTrace` marker on itself.

        This is designed to be used inside the `setup_widgets
        <ContainerWidget.setup_widgets>` function, like this:

        .. code:: python

            def setup_widgets(self, ...):
                self.w1 = Widget(self, ...).putIgnoreTrace()

        This is usually called "method chaining", or "fluent interface".
        '''
        # TODO: Move this "method chaining" to a common document.
        if __debug__:
            assert isinstance(self, ContainerWidget), f'{self}: Unsupported "ignoreContainerTrace": Not a container'
        self.ignoreContainerTrace = value
        return self

    def attachTooltip(self, tooltipClass: 'typing.Optional[typing.Type[Tooltip]]' = None,
                      **tt_kwargs,
                      ):  # TODO: Return type is `typing.Self`, unsupported in Python 3.8
        '''Setup a tooltip object for the current widget.

        This creates a single `Tooltip` object according to the given
        arguments, attached to the current widget.
        Saves the tooltip object in `tt`.

        This is designed to be used inside the `setup_widgets
        <ContainerWidget.setup_widgets>` function, like this:

        .. code:: python

            def setup_widgets(self, ...):
                self.w1 = Widget(self, ...).attachTooltip(...)

        This is usually called "method chaining", or "fluent interface".

        Args:
            tooltipClass: The class to instance as the tooltip object.
                Must be a `Tooltip`, or `None` to use `TooltipSingleStatic`.

                Defaults to `True`.

        All other keyword arguments are passed to the `Tooltip` creation.

        Note:
            This is incompatible with `putTooltip`, do not mix them on the same
            widget.
        '''
        from . import TooltipSingleStatic
        if self.tt is not None:
            raise exception.InvalidWidgetDefinition(f'{self}: Multiple attached tooltips')
        if isinstance(self, MixinValidationSingle) and self.vsettings is not None:
            if self.vsettings.tt is None:
                if __debug__:
                    logger.warning('%s: If you need a validation tooltip, see `putTooltip`', self)
            else:
                raise exception.InvalidWidgetDefinition(f'{self}: Incompatible validation tooltip with `putTooltip`')
        tt: Tooltip
        if tooltipClass is None:
            tt = TooltipSingleStatic(self, **tt_kwargs)
        else:
            tt = tooltipClass(self, **tt_kwargs)
        self.tt = tt
        return self


class MixinTraces:
    '''Mixin class for variable traces.'''
    def init_traces(self) -> None:
        self._traces: typing.MutableMapping[str, str] = {}
        assert isinstance(self, (SingleWidget, ContainerWidget)), f'{self.__class__.__qualname__}: Unsupported tracing for this Widget'
        assert self.variable is not None, f'{self}: Widget untraceable'

    def trace(self, function: typing.Callable, *, trace_name: typing.Optional[str] = None, **kwargs: typing.Any) -> str:
        '''Trace the variable associated to the current widget.

        The underlying function is `tkmilan.var.trace`, check it for more
        detailed documentation.

        Args:
            function: The callback function.
            trace_name: A name for the trace reference. Must be unique for the
                widget. Optional, uses an automatic name otherwise.
            kwargs: Passed to the `tkmilan.var.trace` function.

        See Also:
            Use `atrace` to combine a trace with a `model.TimeoutIdle`. Use
            `tracev` to consider the named container variable.
        '''
        # Merge with `tracev`
        assert isinstance(self, (SingleWidget, ContainerWidget)), f'{self.__class__.__qualname__}: Unsupported tracing for this Widget'
        assert self.variable is not None, f'{self}: Widget untraceable'
        if __debug__:
            if self.ignoreContainerTrace:
                warnings.warn(f'{self}: Tracing widget that is ignored on container', stacklevel=2)
        function_name = tkmilan_var.trace(self.variable, function, **kwargs)
        key = trace_name or function_name
        assert key not in self._traces, f'{self}: Repeated trace name: {key}'
        self._traces[key] = function_name
        logger_traces.debug('%s: New Trace "%s"', self.variable, key)
        return function_name

    # Technically, this should be moved to `ContainerWidget`, but since it's a
    # "copy" to `trace`, let's keep them together.
    def tracev(self, vname: str, function: typing.Callable, *,
               trace_name: typing.Optional[str] = None,
               **kwargs: typing.Any,
               ) -> str:
        '''Trace the named variable attached to the current container widget.

        The underlying function is `tkmilan.var.trace`, check it for more
        detailed documentation.

        See Also:
            Use `trace` to consider the current widget variable instead.
        '''
        # Merge with `trace`
        assert isinstance(self, ContainerWidget), f'{self.__class__.__qualname__}: Unsupported tracing for this Widget'
        assert vname in self._variables, f'{self}: Missing variable named "{vname}"'
        vobj = self.gvar(vname)
        assert vobj is not None, f'{self}: Variable untraceable'
        function_name = tkmilan_var.trace(vobj, function, **kwargs)
        key = trace_name or function_name
        assert key not in self._traces, f'{self}: Repeated trace name: {key}'
        self._traces[key] = function_name
        logger_traces.debug('%s: New Trace "%s"', vobj, key)
        return function_name

    def atrace(self, function: typing.Callable, **kwargs: typing.Any) -> str:
        '''Trace the variable associated to the current widget, but run the
        callback when there's nothing else to do.

        This is an efficient way of combining `trace` with a
        `model.TimeoutIdle`. Useful if the tracing call runs too soon and needs
        to be delayed by the minimum amount of time possible.

        Args:
            function: The callback function.
            kwargs: Passed to `trace` function.
        '''
        @wraps(function)
        def atrace_wrapper(var, etype, **kwargs_function) -> None:
            assert hasattr(var, '_root'), f'Invalid variable object: {var!r}'

            @wraps(function)
            def atrace_wrapper_aidle():
                return function(var, etype, **kwargs_function)

            rw: 'RootWindow' = var._root
            rw.after_idle(atrace_wrapper_aidle)  # No need for a `model.TimeoutIdle` here
        return self.trace(atrace_wrapper, **kwargs)


# TODO: Add this on SingleWidget? Support containers too?
# TODO: Leverage synergies with specValues
class MixinValidationSingle:
    '''Mixin class for widget validation, for single widgets.'''
    vsettings: typing.Optional[model.VSettings]

    def init_validation(self, validation: typing.Union[model.VSettings, typing.Callable, bool, None] = None) -> model.VSettings:
        assert isinstance(self, (tk.Widget, tk.Tk)), f'{self} is not a valid tkinter.Widget'
        assert isinstance(self, MixinWidget), f'{self} is not a valid tkmilan widget'
        assert isinstance(self, SingleWidget), f'{self.__class__.__qualname__}: Unsupported validation for this Widget'
        assert isinstance(self.variable, tkmilan_var.Spec), f'{self.__class__.__qualname__}: Non-Spec variable type'   # TODO
        if __debug__:
            cfg_defaults = {'validate': 'none', 'validatecommand': '', 'invalidcommand': ''}
            assert set(cfg_defaults) == set(WIDGET_VALIDATION_CFG)
            for cfg, cfg_default in cfg_defaults.items():
                assert self.configure(cfg)[4] == cfg_default, f'{self}: Invalid validation setting "{cfg}": Use `validation` only'
        if validation is True:
            if __debug__:
                logger_valid.debug('%s: Setup Default Validation', self)
            valobj = model.VSettings(fnSimple=True)
        elif isinstance(validation, typing.Callable):
            if __debug__:
                logger_valid.debug('%s: Setup Function Validation', self)
            # TODO: fnSimple is True is `validation` takes a single argument
            valobj = model.VSettings(fn=validation, fnSimple=False)
        elif validation in (False, None):
            valobj = None
        else:
            assert isinstance(validation, model.VSettings)
            valobj = validation
        if valobj is None:
            if __debug__:
                logger_valid.debug('%s: Setup Validation: None', self)
            self.vsettings = None
        else:
            valobj.fn = valobj.fn or self.setup_validation  # Configure the "natural" validation
            if __debug__:
                logger_valid.debug('%s: Setup Validation: %s', self, valobj)
            self.vsettings = valobj
            if valobj.postInitial:
                # No need for a `TimeoutIdle` here
                self.after_idle(lambda var=self.variable: self.__validPost(var, None, vtype='initial'))
            if valobj.postVar:
                self.trace(self.__validPost, vtype='self',
                           trace_name='__:valid:postVar')
            self.__validCommand: typing.Callable[
                [str, model.ValidateWhyT, model.ValidateST],
                typing.Union[bool, typing.Literal['break']],
            ]
            if valobj.fnSimple:
                self.__validCommand = self.__validCommandSimple
            else:
                self.__validCommand = self.__validCommandComplex
            self.configure(
                validate=valobj.tkWhen,
                validatecommand=(self.register(self.__validCommand), '%P', '%V', '%d'),
                invalidcommand='',  # TODO: Support something like this?
            )
        return valobj

    def setup_validation(self, vstate: model.VState, vwhy: typing.Optional[model.VWhy] = None) -> typing.Optional[bool]:
        '''Define the "natural" widget validation, checking the state validation.

        Some widgets might have a different "natural" widget validation function.

        When this does not apply, use `fn.validation_pass`.
        '''
        if __debug__:
            if isinstance(vstate, str):
                logger.warning('%s: Old and Busted Validation [%s]', self, self.__class__.__qualname__)
        return vstate.valid

    def doValidation(self, n=None, i=None, t=None) -> None:
        '''Force widget Post-Validation.

        Wraps the upstream function with optional arguments, to be used
        directly on `trace <MixinTraces.trace>`, `Binding`, etc.

        All arguments are ignored.
        '''
        assert isinstance(self, SingleWidget), f'{self.__class__.__qualname__}: Unsupported validation for this Widget'
        # assert isinstance(self, (tk.ttk.Entry)), f'{self} is not a valid Entry'
        # Reimplement `self.validate`
        self.__validPost(self.variable, None, vtype='forced')

    def __validCommandSimple(self,
                             vstate: typing.Union[str, model.VState],
                             why: model.ValidateWhyT,
                             whyNum: model.ValidateST,
                             ) -> typing.Union[bool, typing.Literal['break']]:
        assert isinstance(self, SingleWidget), f'{self.__class__.__qualname__}: Unsupported validation for this Widget'
        always_vstate: model.VState
        if isinstance(vstate, str):
            always_vstate = self.variable.get()
            assert always_vstate.label == vstate, f'Weird vstate mismatch:: {always_vstate} != vstate'
        else:
            always_vstate = vstate
        # Upstream Validation Command, do not calculate `vwhy`
        assert self.vsettings is not None
        assert self.vsettings.fn is not None
        assert self.vsettings.fnSimple is True
        rval = self.vsettings.fn(always_vstate, None)
        if self.vsettings.tt is not None and self.vsettings.ttSimple is True:
            self.__validTooltipSimple(rval is True)
            if __debug__:
                tt_log = f' tt:simple:{self.vsettings.tt}'
        else:
            if __debug__:
                tt_log = ''
        if __debug__:
            logger_valid.debug('%s: validation=%s%s', self, rval, tt_log)
        return 'break' if rval is None else rval

    def __validCommandComplex(self,
                              vstate: typing.Union[str, model.VState],
                              why: model.ValidateWhyT,
                              whyNum: model.ValidateST,
                              ) -> typing.Union[bool, typing.Literal['break']]:
        assert isinstance(self, SingleWidget), f'{self.__class__.__qualname__}: Unsupported validation for this Widget'
        always_vstate: model.VState
        if isinstance(vstate, str):
            always_vstate = self.variable.get()
            assert always_vstate.label == vstate
        else:
            always_vstate = vstate
        # Upstream Validation Command, calculate `vwhy`
        assert isinstance(self, MixinWidget), f'{self} is not a valid tkmilan widget'
        assert self.vsettings is not None
        assert self.vsettings.fn is not None
        assert self.vsettings.fnSimple is False
        if self.vsettings.tt is not None and self.vsettings.ttSimple is True:
            ttobj = None
        else:
            ttobj = self.vsettings.tt
        vwhy = model.VWhy(vstate=always_vstate, why=why, t=whyNum,
                          widget=self, tt=ttobj)
        rval = self.vsettings.fn(always_vstate, vwhy)
        if self.vsettings.tt is not None and self.vsettings.ttSimple is True:
            self.__validTooltipSimple(rval is True)
            if __debug__:
                tt_log = ' tt:simple'
        else:
            if __debug__:
                tt_log = ''
        if __debug__:
            logger_valid.debug('%s: validation=%s%s why=%s', self, rval, tt_log, vwhy)
        return 'break' if rval is None else rval

    def __validPost(self, var, etype, *, vtype: model.ValidateWhyT):
        assert isinstance(self, MixinWidget), f'{self} is not a valid tkmilan widget'
        # Keep the GUI "valid" state up to date
        self.set_gui_state(valid=self.__validCommand(var.get(), vtype, -1))

    def __validTooltipSimple(self, rval: typing.Optional[bool]):
        assert self.vsettings is not None
        assert self.vsettings.tt is not None
        if rval is True:
            self.vsettings.tt.disable()
        else:
            self.vsettings.tt.enable()

    def setDefault(self) -> None:
        '''Set the current state to the default label.'''
        assert isinstance(self, SingleWidget), f'{self.__class__.__qualname__}: Unsupported validation for this Widget'
        assert isinstance(self.variable, tkmilan_var.Spec), f'{self.__class__.__qualname__}: Non-`Spec` variable type'
        self.wstate = self.variable.ldefault

    def eSet(self, label: str) -> typing.Callable[..., None]:
        '''Return an event function to set the state a certain label.

        Returns:
            Return a function that can be attached to a `Binding`, `trace
            <MixinTraces.trace>`, or even called directly.
        '''
        assert isinstance(self, SingleWidget), f'{self.__class__.__qualname__}: Unsupported validation for this Widget'
        assert isinstance(self.variable, tkmilan_var.Spec), f'{self.__class__.__qualname__}: Non-`Spec` variable type'
        if label not in self.variable:
            raise exception.InvalidCallbackDefinition(f'Setting an invalid label: {label}')

        def eSet(n=None, i=None, t=None):
            self.wstate = label
        return eSet

    def eSetValue(self, value: typing.Any) -> typing.Callable[..., None]:
        '''Wraper for `eSet`, to set a value instead.

        Requires the widget to have a `specificed variable <SpecParsed>`.
        '''
        assert isinstance(self, SingleWidget), f'{self.__class__.__qualname__}: Unsupported validation for this Widget'
        assert isinstance(self.variable, tkmilan_var.SpecParsed), f'{self.__class__.__qualname__}: Non-`SpecParsed` variable type'
        return self.eSet(self.variable.getLabel(value))

    # TODO: On Python 3.11:: -> typing.Self
    def putTooltip(self, tooltipClass: 'typing.Union[bool, typing.Type[Tooltip]]' = True,
                   **tt_kwargs,
                   ) -> 'MixinValidationSingle':
        '''Setup the tooltip object for the validation settings on itself.

        This creates the `Tooltip` object according to the settings, attached
        to the current widget. See `VSettings <model.VSettings>` for tooltip
        related settings.
        The widget must setup the validation already, but **must not** define
        an existing tooltip object (parameter ``tt``).

        This is designed to be used inside the `setup_widgets
        <ContainerWidget.setup_widgets>` function, like this:

        .. code:: python

            def setup_widgets(self, ...):
                self.w1 = Widget(self, ...).putTooltip(...)

        This is usually called "method chaining", or "fluent interface".

        Args:
            tooltipClass: The class to instance as the tooltip object.
                Must be a `Tooltip`, or `True` to use `TooltipValidation`.

                Defaults to `True`.

        All other keyword arguments are passed to the `Tooltip` creation.

        Note:
            This is incompatible with `attachTooltip`, do not mix them on the
            same widget.
        '''
        from . import TooltipValidation  # Avoid circular import
        assert isinstance(self, MixinWidget), f'{self} is not a valid tkmilan widget'
        if self.tt is not None:
            raise exception.InvalidWidgetDefinition(f'{self}: Incompatible basic tooltip with `attachTooltip`')
        if self.vsettings is None:
            raise exception.InvalidWidgetDefinition(f'{self}: Widget validation not configured')
        assert self.vsettings is not None
        if tooltipClass is False:
            if __debug__:
                warnings.warn('{self}: `.putTooltip(False)` is pointless, remove', stacklevel=2)
        else:
            tt_obj: Tooltip
            if tooltipClass is True:
                tt_obj = TooltipValidation(self, **tt_kwargs)
            else:
                tt_obj = tooltipClass(self, **tt_kwargs)
            if __debug__:
                logger_valid.debug('%s: tooltip%s=%s ttSimple=%s', self,
                                   '[V]' if isinstance(tt_obj, TooltipValidation) else '', tt_obj,
                                   self.vsettings.ttSimple)
            if isinstance(tt_obj, TooltipValidation):
                if isinstance(self, SingleWidget):
                    vobj = self.variable
                else:  # TODO: Can be used on other types of widgets?
                    vobj = None
                tt_obj.setup_tooltip_state(vobj)
            assert self.vsettings.tt is None, f'{self}: Overwriting validation tooltip is unsupported'
            self.vsettings.tt = tt_obj
        return self


# High-Level Mixins


class SingleWidget(MixinWidget, MixinStateSingle, MixinTraces):
    '''Parent class of all single widgets.'''
    variable: typing.Optional[tkmilan_var.Variable] = None
    state_type: typing.Optional[typing.Type[tkmilan_var.Variable]] = None
    layout_padable: bool = True
    '''Should this widget be automatically padded, when requested.

    See `ContainerWidget.pad_container`.
    '''

    def init_single(self,
                    vspec: typing.Union[None, tkmilan_var.Variable, validation.VSpec] = None,
                    gkeys: typing.Optional[typing.Iterable[str]] = None,
                    ) -> None:
        '''Setup all single widget stuff.

        Includes:

        - Variable settings (Supports creating new variables)
        - `tkmilan.mixin.MixinState.isNoneable` calculation
        '''
        MixinWidget.__init__(self, gkeys=gkeys)
        self.variable = self.setup_variable(vspec)
        MixinTraces.init_traces(self)
        if self.isNoneable is None:
            # Calculate isNoneable option
            self.isNoneable = self.state_type is tkmilan_var.nothing

    def setup_variable(self, vspec: typing.Union[None, tkmilan_var.Variable, validation.VSpec]) -> tkmilan_var.Variable:
        assert self.state_type is not None, f'{self.__class__.__qualname__}: Missing `state_type`'
        if vspec is None:
            variable = self.state_type()
        elif isinstance(vspec, validation.VSpec):
            assert issubclass(self.state_type, tkmilan_var.Spec), f'{self.__class__.__qualname__}: Invalid `state_type`, not a `Spec`'
            variable = self.state_type(vspec)
        else:
            assert isinstance(vspec, tkmilan_var.Variable)
            variable = vspec
        assert isinstance(variable, self.state_type), f'Incompatible variable type: {type(variable).__qualname__} not {self.state_type.__qualname__}'
        return variable

    def setup_state(self):
        return self.variable

    def wimage(self, key: str) -> typing.Optional[tk.Image]:
        '''Wraper for `RootWindow.wimage`.'''
        return self.wroot.wimage(key)


class ProxyWidget(SingleWidget):
    '''Parent class of all proxy widgets. Special case of `SingleWidget`.

    This is implemented as a class initializer that sets up the `wproxy
    <MixinWidget.wproxy>`/`proxee <MixinWidget.proxee>` references, and returns
    the child instance.

    Note that creating an instance of this type will return the child widget
    instance, not the proxy object. The rest of the library is aware of this.
    The `ProxyWidget` object is available on the `wproxy <MixinWidget.wproxy>`
    value.

    .. note::

        When implementing subclasses, take care not to alias any children
        argument with proxy arguments.
        Use a per-class prefix, or ``proxy`` prefix for common arguments.
        See `ScrolledWidget` for an example (note ``scroll*` and ``proxyStyleID``
        arguments).

    See Also:
        Check the Python documentation for the difference between
        `object.__new__` and `object.__init__`.
    '''
    def __new__(cls: typing.Type[ProxyWidgetT], *args, **kwargs) -> ProxyWidgetT:
        assert issubclass(cls, ProxyWidget)
        proxy = super(ProxyWidget, cls).__new__(cls)
        # Manually call the __init__ method (required since the class changes)
        cls.__init__(proxy, *args, **kwargs)
        proxee = proxy.proxee
        assert proxee is not None
        # Save a reference to the proxy object
        proxee.wproxy = proxy
        # Return a different type from `cls`:
        return typing.cast(ProxyWidgetT, proxee)


class ContainerWidget(MixinWidget, MixinStateContainer, MixinTraces):
    '''Parent class of all containers.'''
    layout: typing.Optional[str] = ''  # Automatic AUTO
    '''Store the processed layout'''
    layout_expand: bool = True
    '''Should this container expand to fill the space on the parent widget.

    Note this affects the **parent** grid, not the child grid on this container.
    '''
    layout_autogrow: bool = True
    '''Should this container have its child columns and rows grow automatically.

    This is equivalent to configuring the grid with the option ``weight=1``.
    '''
    layout_autoadjust: bool = False
    '''Should this container have its child widgets automatically adjusted, based on their types.

    This adjusts child widgets based on its type in specific ways.

    Currently implemented adjustments:

    - `Separator`: Set ``weight=0`` to all rows/columns containing this type,
      based on its `orientation <Separator.orientation>`.

    .. note::
        This has important performance implications, so it is disabled by
        default. The widgets that can be adjusted are flagged as a warning on
        debug mode, so they can be manually toggled.
    '''
    layout_padable: bool = True
    '''Should this container's children be automatically padded, when
    requested.

    Most containers behave well when padding children, but some are
    problematic, mark those at class level (set ``layout_padable = False``).

    See `ContainerWidget.pad_container`.
    '''
    layout_autohide: bool = True
    '''Should this container have its child with `ignoreContainerLayout
    <MixinWidget.ignoreContainerLayout>` removed from the grid.

    Enabled by default, do not change this unless there are any problems.
    '''
    variable: typing.Optional[tkmilan_var.Variable] = None

    def init_container(self, *args,
                       layout: typing.Optional[str] = '',
                       **kwargs) -> None:
        '''
        Setup all the container stuff.

        Includes:
        - Variable settings
        - Sub-Widget settings
        - Layout
        - Traces (from `MixinTraces`)
        - Defaults
        '''
        assert isinstance(self, (tk.Widget, tk.Tk, tk.Toplevel)), f'{self} is not a valid widget'
        MixinWidget.__init__(self)
        self._variables: typing.MutableMapping[str, tkmilan_var.Variable] = {}  # Allow attaching variables to containers
        # Calculate child widgets
        _existing_names = set(dir(self))
        _existing_ids = None
        if __debug__:
            _existing_ids = {
                name: id(self.__dict__.get(name, None))
                for name in _existing_names
                if name not in WEIRD_WIDGET_NAME
            }
        widgets = self.setup_widgets(*args, **kwargs)
        widgets_gui = set()
        if __debug__:
            assert _existing_ids is not None
            overriden_names = [name for name, eid in _existing_ids.items() if id(self.__dict__.get(name, None)) != eid]
            assert len(overriden_names) == 0, f'{self}: Overriden Names: {" ".join(overriden_names)}'
        _new_names = set(dir(self)) - _existing_names
        if widgets is None:
            children = [w for _, w in self.children.items()]
            # logger.debug('tk C: %r', self.children)
            widgets = {}
            dir_names = {id(getattr(self, name, None)): name for name in _new_names}
            for widget_raw in children:
                assert isinstance(widget_raw, MixinWidget), f'{widget_raw} is not a valid tkmilan widget'
                widget = widget_raw.proxee or widget_raw  # Save the child widget
                # `isAuto`: See `MixinWidget.isAuto`
                if widget.isAuto is True:  # State and GUI
                    wid = id(widget)
                    assert wid in dir_names, f'{self}: Missing "{widget}"[{widget!r}]'
                    name = dir_names[wid]
                    widgets[name] = widget
                elif widget.isAuto is False:  # GUI
                    widgets_gui.add(widget)
                elif widget.isAuto is None:  # Nothing
                    pass
        widgets_2layout = []
        widgets_2hide = []
        for w in widgets.values():
            if w.ignoreContainerLayout:
                widgets_2hide.append(w)
            else:
                widgets_2layout.append(w)
            w.wparent = self
        # logger.debug('Widgets: #%d hide=#%d layout=#%d | %r', len(widgets), len(widgets_2hide), len(widgets_2layout), widgets)
        self.widgets: typing.Mapping[str, MixinWidget] = widgets
        self._widgetsGUI: typing.Set[MixinWidget] = widgets_gui
        self._widgetsLayout: typing.Sequence[MixinWidget] = widgets_2layout
        if self.isNoneable is None:
            # Calculate isNoneable option: containers are always noneable
            self.isNoneable = True

        if layout is None or self.layout is None:
            # Allow for explicit `None` layouts
            chosen_layout = None
        elif layout != '':
            # Use the per-instance setting
            chosen_layout = layout
        elif self.layout != '':
            # Use the class setting
            chosen_layout = self.layout
        else:
            # Fallback
            chosen_layout = autolayout.AUTO
        for w in widgets_2hide if self.layout_autohide else []:
            # Skip Toplevel and other un-griddable widgets
            if isinstance(w, tk.Grid):
                w.grid_remove()
        self.layout_container(chosen_layout, self._widgetsLayout)
        # Traces (synthetic)
        self.variable = self.setup_variable(None)
        MixinTraces.init_traces(self)
        # Defaults
        self.setup_defaults()
        self.after_idle(lambda: self.setup_adefaults())  # No need for a `TimeoutIdle` here
        # Error Checking
        assert hasattr(self, 'grid'), f'{self!r} should have a grid method'
        if __debug__:
            aliases = set(self._variables.keys()).intersection(set(self.widgets.keys()))
            assert len(aliases) == 0, f'{self!r}: Aliased var/widgets: {" ".join(aliases)}'

    def setup_variable(self, variable: typing.Optional[tkmilan_var.Variable]) -> typing.Optional[tkmilan_var.Variable]:
        assert variable is None  # Containers don't have much choice here
        return tkmilan_var.aggregator(cwidget=self)

    def setup_traces(self, trace_vupstream: typing.Optional[typing.Set[str]] = None) -> tkmilan_var.Variable:
        assert self.variable is not None, f'{self!r}: Missing variable'
        if not isinstance(self.variable, tkmilan_var.aggregator):
            raise exception.InvalidWidgetDefinition(f'{self}: Tracing a container without an aggregator variable')
        assert not self.variable.ready, f'{self}: Repeated setup for synthetic trace'
        if __debug__:
            logger_traces.debug('%s<%s>: Tracing Children ...', self.variable, self)
        tnames = []
        vid_upstream: typing.Set[str] = set()
        container_state = self.state_c(vid_upstream=vid_upstream)
        for wc in container_state.cwidgets.values():
            if wc.ignoreContainerTrace:
                if __debug__:
                    logger_traces.debug('%s<%s>:: SKIP %15s <%s>', self.variable, self, 'Container', wc)
            else:
                function_name = wc.trace(self.__trace_trigger, what=wc,
                                         trace_name=f'__:{self.variable}',
                                         trace_vupstream=container_state.vid_upstream)
                if __debug__:
                    logger_traces.debug('%s<%s>:: %15s <%s> @ %s', self.variable, self, 'Container', wc, function_name)
                tnames.append(function_name)
        for whc in container_state.hcwidgets:
            if whc.ignoreContainerTrace:
                if __debug__:
                    logger_traces.debug('%s<%s>:: SKIP %15s <%s> @ %s', self.variable, self, 'Helper Container', whc)
            else:
                function_name = whc.trace(self.__trace_trigger, what=whc,
                                          trace_name=f'__:{self.variable}',
                                          trace_vupstream=container_state.vid_upstream)
                if __debug__:
                    logger_traces.debug('%s<%s>:: %15s <%s> @ %s', self.variable, self, 'Helper Container', whc, function_name)
                tnames.append(function_name)
        for ws in container_state.swidgets.values():
            if isinstance(ws.variable, tkmilan_var.nothing) or ws.ignoreContainerTrace:
                if __debug__:
                    logger_traces.debug('%s<%s>:: SKIP %15s <%s>', self.variable, self, 'Single', ws)
            else:
                function_name = ws.trace(self.__trace_trigger, what=ws,
                                         trace_name=f'__:{self.variable}')
                if __debug__:
                    logger_traces.debug('%s<%s>:: %15s <%s> @ %s', self.variable, self, 'Single', ws, function_name)
                tnames.append(function_name)
        for whs in container_state.hswidgets:
            if isinstance(whs.variable, tkmilan_var.nothing) or whs.ignoreContainerState or whs.ignoreContainerTrace:
                if __debug__:
                    logger_traces.debug('%s<%s>:: SKIP %15s <%s>', self.variable, self, 'Helper Single', whs)
            else:
                function_name = whs.trace(self.__trace_trigger, what=whs,
                                          trace_name=f'__:{self.variable}')
                if __debug__:
                    logger_traces.debug('%s<%s>:: %15s <%s> @ %s', self.variable, self, 'Helper Single', whs, function_name)
                tnames.append(function_name)
        for wvar in container_state.variables.values():
            if isinstance(wvar, tkmilan_var.nothing) or wvar.ignoreContainerTrace:
                if __debug__:
                    logger_traces.debug('%s<%s>:: SKIP %15s <%s>', self.variable, self, 'Var', wvar)
            else:
                function_name = tkmilan_var.trace(wvar, self.__trace_trigger)
                if __debug__:
                    logger_traces.debug('%s<%s>:: %15s <%s> @ %s', self.variable, self, 'Var', wvar, function_name)
                tnames.append(function_name)
        if __debug__:
            logger_traces.debug('%s<%s>: Traced %d Children!', self.variable, self, len(tnames))

        self.variable.tout = model.TimeoutIdle(self, self.variable.set,
                                               immediate=False)
        assert self.variable.ready, f'{self}: Error on setup for synthetic trace'
        if __debug__:
            logger_traces.debug('%s<%s>: TO: %s', self.variable, self, self.variable.tout)
        return self.variable

    def __trace_trigger(self, var, etype, *, what: typing.Optional[MixinWidget] = None):
        assert self.variable is not None, f'{self!r}: Missing variable'
        assert isinstance(self.variable, tkmilan_var.aggregator)
        assert self.variable.ready and self.variable.tout is not None, f'{self}: Unprepared synthetic trace'
        self.variable.tout.reschedule()
        if __debug__:
            what_str = '' if what is None else f' « {what}'
            logger_traces.debug('%s « %s: Trigger @ %s%s',
                                self.variable, var,
                                self, what_str)

    def trace(self, *args,
              trace_vupstream: typing.Optional[typing.Set[str]] = None,
              **kwargs: typing.Any) -> str:
        assert self.variable is not None, f'{self!r}: Missing variable'
        if __debug__:
            # Warn only about aggregator variables
            # Do not warn about internal traces, even if the problem persists
            if isinstance(self.variable, tkmilan_var.aggregator) and self.variable.ready and not kwargs.get('trace_name', '').startswith('__'):
                # TODO: Need one container variable per trace, `trace_vupstream` might be different
                #       False negative if variable is an aggregator and traced before
                warnings.warn('Multiple Nested Container Traces, this might not work correctly', stacklevel=2)
                # Works fine for straight widget trees, but fails for complex states
        if not self.variable.ready:
            self.setup_traces(trace_vupstream)
        return super().trace(*args, **kwargs)

    def setup_gstate_valid(self, *,
                           nowarn: bool = False,
                           childMatch: typing.Iterable[SingleWidget] = tuple(),
                           childSkip: typing.Iterable[SingleWidget] = tuple(),
                           ) -> None:
        '''Configure setting the `model.GuiState` ``valid`` parameter for this
        GUI.

        Since this is still a "hack", it's not enabled automatically nor in a
        nice declarative way. This might interact with other features, it is
        only a preview for now.

        This is not recursive, child containers **DO NOT** inherit this
        setting. There's no support for child containers anyway, make sure to
        use this only for simple containers, no nesting.

        To setup this, call this function inside the widgets' `setup_defaults`
        function, before other widget state changes. This uses `trace`
        internally, so that's another feature that might not work perfectly.

        Use the ``nowarn`` parameter if you confirmed it works properly, to
        avoid a spurious warning. This is not the default, make sure you really
        test this properly.

        Use the ``childMatch`` parameter to "tie" the container valid state to
        those child single widgets. This should include any child labels, that
        should be ignored when calculating the new state, but set with the
        container state. ``childSkip`` will avoid setting the state on those
        widgets.

        .. warning::
            This is not fully baked, but can be used carefully, with extra
            testing.
        '''
        if __debug__:
            if not nowarn:
                warnings.warn('HACK: This is not fully supported on complex containers', stacklevel=2)
        self.trace(self.__valid_trigger, childMatch=set(childMatch), childSkip=set(childSkip),
                   trace_name='__:gstate:valid', trace_initial=True)

    def __valid_trigger(self, var, etype, *,
                        childMatch: typing.Set[SingleWidget],
                        childSkip: typing.Set[SingleWidget]):
        # See `setup_gstate_valid`
        assert all(w.gstate.valid is not None for w in self.widgets.values() if w not in childMatch)
        assert all(w not in childMatch for w in childSkip), f'{self}: Confusing Match/Skip orders'
        assert all(w.wparent == self for w in (*childMatch, *childSkip)), f'{self}: Non-Children widgets given in "child*"'
        vstate = all(w.gstate.valid for w in self.widgets.values() if w not in childMatch)
        # Container Widget (no recursion)
        self.set_gui_state(valid=vstate, _sub=False)
        # Child Widgets
        for w in childMatch - childSkip:
            assert isinstance(w, SingleWidget)
            w.set_gui_state(valid=vstate)
        return vstate

    def setup_widgets(self, *args, **kwargs) -> typing.Optional[typing.Mapping[str, MixinWidget]]:
        '''Define the sub widgets here.

        Return a :py:class:`dict` for a custom mapping, or `None` for automatic mapping.
        '''
        raise NotImplementedError

    def var(self, cls: typing.Type[tkmilan_var.Variable], *,
            value: typing.Optional[typing.Any] = None,
            name: typing.Optional[str] = None,
            vname: typing.Optional[str] = None,
            ) -> 'tkmilan_var.Variable':
        '''"Attach" a new variable to this container.

        Args:
            cls: The variable class.

            name: The variable name, on the widget namespace.
                Optional, defaults to ``vname``.
            value: The default value. Optional, defaults to `None`.
            vname: The variable name, on the global namespace.
                Optional, defaults to an autogenerated name.

        See Also:
            - `varSpec`: Attach a `Spec` variable to this container, with a name.
            - `gvar`: Access the variable by name.

        .. note::

            The ``vname`` is defined in a global namespace, common to the
            entire application. This can be used to define common variables
            across different widgets, but this is not default behaviour since
            it violates the principle of least surprise.
        '''
        vobj = cls(name=vname)
        if value is not None:
            vobj.set(value)
        assert isinstance(vobj, tkmilan_var.Variable), f'Class "{cls}" is not a "Variable"'
        # Save the variables on the instance object
        kname = name or vname or str(vobj)
        self._variables[kname] = vobj
        return vobj

    def varSpec(self, cls: typing.Type[tkmilan_var.Spec], spec: typing.Any, *,
                name: typing.Optional[str] = None,
                vname: typing.Optional[str] = None,
                ) -> 'tkmilan_var.Spec':
        '''"Attach" a new `specified variable <var.Spec>` to this container.

        Args:
            cls: The variable class.
            name: The variable name, on the widget namespace.
                Optional, defaults to ``vname``.
            spec: The specification to creating the new variable.
            vname: The variable name, on the global namespace.
                Optional, defaults to an autogenerated name.

        See Also:
            - `var`: Attach a non-`Spec` variable to this container, with a name.
            - `gvar`: Access the variable by name.

        .. note::

            The ``vname`` is defined in a global namespace, common to the
            entire application. This can be used to define common variables
            across different widgets, but this is not default behaviour since
            it violates the principle of least surprise.
        '''
        if __debug__:
            if cls in tkmilan_var.Limit.__subclasses__():
                warnings.warn('No need to use `var.Limit` subclasses, use the parent class', stacklevel=2)
        vobj = cls(spec, name=vname)
        assert isinstance(vobj, tkmilan_var.Spec), f'Class "{cls}" is not a "Spec"'
        # Save the variables on the instance object
        kname = name or vname or str(vobj)
        self._variables[kname] = vobj
        return vobj

    def gvar(self, name: str) -> tkmilan_var.Variable:
        '''Get a variable attached to this container, by name.

        Fails if it does not exist.

        Args:
            name: The variable name to search for.

        See Also:
            - `var`: Attach a non-`Spec` variable to this container, with a name.
            - `varSpec`: Attach a `Spec` variable to this container, with a name.
        '''
        return self._variables[name]

    def layout_container(self, layout: typing.Optional[str], widgets: typing.Sequence[MixinWidget]):
        assert isinstance(self, (tk.Widget, tk.Tk, tk.Toplevel)), f'{self} is not a valid widget'
        if not self.ignoreContainerLayout and self.layout_expand:
            assert isinstance(self, tk.ttk.Widget), f'{self} is not a valid tkinter.ttk.Widget'
            self.grid(sticky=tk.NSEW)
        olayout = layout
        # Automatic Layout
        try:
            if __debug__:
                logger_autolayout.debug('%s: AutoLayout %d widgets', self, len(widgets))
            layout, args = autolayout.do(layout, len(widgets))
        except Exception as e:
            logger.critical('%s: Weird Layout: %s [%s]', self, layout, e)
            if __debug__:
                import sys
                sys.exit(100)
            layout = None
        # For layout_autoadjust
        if self.layout_autoadjust:
            from . import Separator
            _separator: typing.Mapping[str, typing.List[mixin.MixinWidget]] = {
                autolayout.HORIZONTAL: [],
                autolayout.VERTICAL: [],
            }
        else:
            if __debug__:
                from . import Separator
                if any(isinstance(w, Separator) for w in widgets):
                    logger.warning('%s[%s]: This container can be marked with "layout_autoadjust"',
                                   self, self.__class__.__qualname__)
        if layout:
            # if __debug__:
            #     logger.debug('%s: => %d widgets', self, len(widgets))
            for idx, (arg, widget) in enumerate(zip(args, widgets)):
                widget_real = widget.wproxy or widget
                assert isinstance(widget_real, (tk.Widget, tk.Tk, tk.Toplevel)), f'Widget #{idx}[{str(widget_real)}]: Type {type(widget_real)}'
                assert widget.ignoreContainerLayout is False and widget_real.ignoreContainerLayout is False, f'{self}: Layout is being ignored'
                widget_real.grid(**arg.dict())  # Change the grid on the proxy widget
                if self.layout_autoadjust:
                    # Check the inner widget, no proxies
                    # Store the proxy, where the grid changes
                    if isinstance(widget, Separator):
                        _separator[widget.orientation].append(widget_real)
        self.layout = layout  # Setup the final layout setting
        if self.layout_autogrow:
            if size := self.gsize:
                fn.configure_grid(self, [1] * size.columns, [1] * size.rows)
        if self.layout_autoadjust:
            if sum(len(lst) for lst in _separator.values()) > 0:
                if __debug__:
                    logger_grid.debug('%s: |> Auto-Adjust Types', self)
                # Keep in sync with `layout_autoadjust`
                if len(_separator_ws := _separator[autolayout.HORIZONTAL]) > 0:
                    if __debug__:
                        logger_grid.debug('%s:    | Separator: %dH', self, len(_separator_ws))
                    self.pgrid_r(*_separator_ws,
                                 weight=0)
                if len(_separator_ws := _separator[autolayout.VERTICAL]) > 0:
                    if __debug__:
                        logger_grid.debug('%s:    | Separator: %dV', self, len(_separator_ws))
                    self.pgrid_c(*_separator_ws,
                                 weight=0)
        self.setup_container_layout(olayout)  # Custom adjustments, for subclasses
        self.setup_layout(layout)  # Custom adjustments, after all automatic changes
        if __debug__:
            # Check the container layout is sane
            wcols, wrows = self.grid_size()
            wgsize = model.GridSize(rows=wrows, columns=wcols)
            assert self.gsize == wgsize, f'{self}: Invalid Container Grid: f={self.gsize} w={wgsize}'

    def pad_container(self, pad: int, *, recursive: bool = True, _level: int = 0) -> None:
        '''Pad this container widget, recursively.

        This requires more than a simple blind application of padding to all
        widgets. It will also take into account containers with a single
        widget, `layout_padable` (skipping unsupported containers), and proxy
        widgets.
        Guarantee the padding distance between widgets and the container is
        ``pad``.

        In particular, this will pad all widgets on the right/bottom, and also
        pad the left/top widgets on the left/top grid location, creating
        uniform padding in all directions.

        The padding configuration will be applied recursively by default, see
        ``recursive`` to disable this.

        Args:
            pad: The padding distance, in pixels. See above for details on how
                this applied.
            recursive: Apply the same padding to child containers.
                Enabled by default.

        See Also:
            See `RootWindow`' ``rpad`` for automatic application to all
            widgets, down from the root window.
        '''
        # if __debug__:
        #     left_wrap = '| ' * _level
        cpad = len(self.widgets) >= 1 and self.layout_padable
        for w in self.widgets.values():
            realw = w.wproxy or w
            assert isinstance(realw, (SingleWidget, ContainerWidget))
            if cpad and not w.ignoreContainerLayout and realw.layout_padable:
                assert isinstance(realw, tk.Widget), f'{w}: Invalid widget for padding'
                ginfo = realw.wgrid
                assert ginfo is not None, f'{w}: Invalid widget grid info for padding'
                if ginfo.column == 0:  # First Column Index
                    # Left Widget
                    # - Pad Both sides
                    padx = (pad, pad)
                else:
                    # Other Widget Locations
                    # - Pad Right/Bottom
                    padx = (0, pad)
                if ginfo.row == 0:  # First Row Index
                    # Top Widget
                    # - Pad Both sides
                    pady = (pad, pad)
                else:
                    # Other Widget Locations
                    # - Pad Bottom
                    pady = (0, pad)
                realw.grid(padx=padx, pady=pady)
                # if __debug__:
                #     logger.debug('%s> % 8s %8s » %s%s', left_wrap, padx, pady,
                #                  realw, '[%s]' % w if w != realw else '')
            if recursive and isinstance(w, ContainerWidget):
                w.pad_container(pad=pad,
                                _level=_level + 1,
                                recursive=recursive,
                                )

    @property
    def gsize(self) -> model.GridSize:
        '''GUI grid size (according to the current child widgets).

        Follow `MixinWidget.ignoreContainerLayout` setting.
        '''
        # Different from `tkinter.Widget.grid_size`, might be temporarily broken
        # befor the whole layout setup runs.
        return fn.grid_size(*[
            w.wproxy or w  # Use the proxy widget
            for w in self.widgets.values()
            if w.ignoreContainerLayout is False
        ])

    def state_c(self, *, vid_upstream: typing.Optional[typing.Set[str]] = None) -> ContainerState:
        if __debug__:
            dlog = False
        swidgets = {}
        cwidgets = {}
        hswidgets: 'typing.Set[SingleWidget]' = set()
        hcwidgets: 'typing.Set[ContainerWidget]' = set()
        wvariables = {}
        vid_upstream = set(vid_upstream or ())
        vid_variables = set(fn.vname(v) for v in self._variables.values())
        vwidgets = collections.defaultdict(list)
        if __debug__:
            if dlog:
                logger.debug('%r START | upstream=`%s`', self, ' '.join(sorted(vid_upstream)))
        for name, widget in self.widgets.items():
            if __debug__:
                if dlog:
                    logger.debug('%s: %r', name, widget)
            if widget.ignoreContainerState:
                if __debug__:
                    if dlog:
                        logger.debug('| Skipping Widget')
                continue
            if isinstance(widget, SingleWidget):
                assert widget.variable is not None
                vid = fn.vname(widget.variable)
                if __debug__:
                    if dlog:
                        logger.debug('| Variable: %s[%r]', vid, widget.variable)
                if vid in vid_upstream:
                    if __debug__:
                        if dlog:
                            logger.debug('  @Upstream, skipping')
                    continue
                elif vid in vid_variables:
                    if __debug__:
                        if dlog:
                            logger.debug('  @Container Variables, skipping')
                    continue
                else:
                    swidgets[name] = widget
                    wvariables[vid] = widget.variable
                    vwidgets[vid].append(name)
            elif isinstance(widget, ContainerWidget):
                if __debug__:
                    if dlog:
                        logger.debug('| Container: @%s', name)
                cwidgets[name] = widget
            else:
                raise NotImplementedError(f'Unknown Widget Type:: {widget!r}')
        state_widgets = set((*swidgets.values(), *cwidgets.values()))
        assert isinstance(self, (tk.Widget, tk.Tk, tk.Toplevel)), f'{self} is not a valid widget'
        for name, cwidget in self.children.items():
            if cwidget in state_widgets:
                continue
            if isinstance(cwidget, SingleWidget):
                if __debug__:
                    if dlog:
                        logger.debug('| Helper Single: %s', name)
                assert cwidget.variable is not None
                vid = fn.vname(cwidget.variable)
                if vid in vid_upstream:
                    if __debug__:
                        if dlog:
                            logger.debug('  @Upstream, skipping')
                    continue
                elif vid in vid_variables:
                    if __debug__:
                        if dlog:
                            logger.debug('  @Container Variables, skipping')
                    continue
                elif cwidget.wproxy is not None:
                    if __debug__:
                        if dlog:
                            logger.debug('  @Proxy Widget, skipping')
                    continue
                else:
                    hswidgets.add(cwidget)
            elif isinstance(cwidget, ContainerWidget):
                if __debug__:
                    if dlog:
                        logger.debug('| Helper Container: %s', name)
                hcwidgets.add(cwidget)
            else:
                raise NotImplementedError(f'Unknown Widget Type: {cwidget!r}')
        vid_upstream.update(wvariables, vid_variables)
        if __debug__:
            if dlog:
                logger.debug('%r STOP::: +%s', self, ' '.join(sorted(vid_upstream - set(vid_upstream or ()))))
        assert vid_upstream >= (vid_upstream or set())
        return ContainerState(swidgets, cwidgets,
                              variables=self._variables,
                              wvariables=wvariables,
                              vwidgets=dict(vwidgets),
                              vid_upstream=vid_upstream,
                              # Helper Widgets
                              hswidgets=hswidgets, hcwidgets=hcwidgets,
                              )

    def setup_state(self, **kwargs) -> typing.Mapping[str, model.WidgetDynamicState]:
        # Default State:
        # - All the attached variables
        # - All the shared variables
        # - All the single-variable widgets
        # - The container widgets, taking the existing variables into account
        container_state = self.state_c(**kwargs)
        rvalue: typing.MutableMapping[str, model.WidgetDynamicState] = {}
        wids_done: typing.MutableSequence[str] = []
        for vn, vobj in container_state.variables.items():
            rvalue[vn] = model.WidgetDynamicState(vobj.get, vobj.set, noneable=False)
        for vname, ws in container_state.vwidgets.items():
            if vname is not None and len(ws) > 1:
                wv = container_state.wvariables[vname]
                assert vname not in rvalue, f'{self!r}: Aliased vwidgets "{vname}"'
                rvalue[vname] = model.WidgetDynamicState(wv.get, wv.set, noneable=False)
                wids_done.extend(ws)
        for n, w in container_state.swidgets.items():
            if n not in wids_done:
                assert n not in rvalue, f'{self!r}: Aliased swidgets "{n}"'
                rvalue[n] = model.WidgetDynamicState(
                    w.wstate_get,
                    w.wstate_set,
                    noneable=w.isNoneable is True,
                )
        vid_upstream = container_state.vid_upstream
        for n, wc in container_state.cwidgets.items():
            assert n not in rvalue, f'{self!r}: Aliased cwidgets "{n}"'
            rvalue[n] = model.WidgetDynamicState(
                partial(wc.state_get, vid_upstream=vid_upstream),
                partial(wc.state_set, vid_upstream=vid_upstream),
                noneable=wc.isNoneable is True,
                container=True,  # Propagate container data
            )
        return rvalue

    def setup_layout(self, layout: typing.Optional[str]) -> None:
        '''Useful for manual adjustments to the automatic layout.

        This runs after all automatic layout settings are configured.

        Args:
            layout: This is the processed version of the layout string.

        Note:
            Available for subclass redefinition.
        '''
        pass

    def setup_container_layout(self, olayout: typing.Optional[str]) -> None:
        '''"Internal" alternative to `setup_layout <ContainerWidget.setup_layout>`.

        This is mostly useful for complex widgets, to keep the convenience of
        the existing `setup_layout <ContainerWidget.setup_layout>` call for the
        final instances, but allow for class-level adjustments.

        This runs just before `setup_layout <ContainerWidget.setup_layout>`.

        .. warning:: Don't use this directly, unless you know what you doing.
            Use `setup_layout <ContainerWidget.setup_layout>`.

        Args:
            olayout: This is string originally used for layout.
                See `self.layout <ContainerWidget.layout>` for the processed version.

        Note:
            Available for subclass redefinition, mostly for complex widgets.
        '''
        pass

    def set_gui_state(self, state: typing.Optional[model.GuiState] = None, _sub: bool = True, **kwargs) -> model.GuiState:
        '''Set GUI State for itself, and optionally, for all sub-widgets.

        .. warning:: Don't use this directly, unless you **really** know what you are doing.

        Args:
            _sub: Automatically run `set_gui_substate` with the same
                `model.GuiState` object. Defaults to `True`.
                Useful only for implementing special containers.

        See Also:
            `MixinWidget.gstate`: Property changed for all sub-widgets.
        '''
        self_state = super().set_gui_state(state, **kwargs)
        if _sub:
            self.set_gui_substate(self_state)
        return self_state

    def set_gui_substate(self, state: model.GuiState) -> None:
        '''Set GUI State for all sub-widgets.

        .. warning:: Don't use this directly, unless you **really** know what you are doing.


        .. note::

            To control the GUI subwidget handling, this function can be
            redefined (using extra care), using something like this:

            .. code:: python

                def set_gui_substate(self, state: tkmilan.model.GuiState):
                    if self.some_condition is True:
                        # Manipulate the `model.GuiState` object
                        state.enabled = False
                    super().set_gui_substate(state)

        See Also:
            `MixinWidget.gstate`: Property changed for all sub-widgets.
        '''
        for _, subwidget in self.widgets.items():
            subwidget.gstate = state
        for subwidget in self._widgetsGUI:
            subwidget.gstate = state

    def setup_defaults(self) -> None:
        '''Runs after the widget is completely setup.

        Note this runs before the parent widget is complete ready.

        Useful to set default values.
        Do not configure layout-related settings here, see `setup_layout
        <ContainerWidget.setup_layout>`.

        Note:
            Available for subclass redefinition.

        See Also:
            `setup_adefaults <ContainerWidget.setup_adefaults>`: Run code after
            all widgets are stable (including parent widgets in the tree).
        '''
        pass

    def setup_adefaults(self) -> None:
        '''Runs after all widgets are stable.

        Avoid changing state on this function.

        Note:
            Available for subclass redefinition.

        See Also:
            `setup_defaults <ContainerWidget.setup_defaults>`: Run code right after this widget is setup, before
            all widgets are stable.
        '''
        pass

    def wimage(self, key: str) -> typing.Optional[tk.Image]:
        '''Wraper for `RootWindow.wimage`.'''
        return self.wroot.wimage(key)

    def pgrid(self, *children: MixinWidget,
              row: bool = True, column: bool = True,
              _internal: bool = False,
              **arguments: typing.Any) -> None:
        '''Configure the grid rows and columns for the given widgets.

        For widgets that span more than one row or column, the settings are changed
        for all rows or columns.

        Args:
            children: Widgets to consider.
                Must all be direct children of this widget.
            row: Configure the rows. Defaults to `True`.
            column: Configure the columns. Defaults to `True`.
            arguments: Arguments passed to the configuration functions:
                :tk:`columnconfigure <grid.htm#M8>` / :tk:`rowconfigure
                <grid.htm#M24>`.

        .. note::

            To configure only rows or columns, see `pgrid_r` and `pgrid_c` for
            a more ergonomic API.

        .. warning::

            Make sure to include proxied widgets as children
            (`MixinWidget.wproxy`), there is a warning on debug mode, but this
            might change in the future.
        '''
        assert row or column, 'Do something, select at least one of row and column'
        assert len(arguments), 'Do something, include some arguments'
        rows: typing.Set[int] = set()
        columns: typing.Set[int] = set()
        for w in children:
            assert w.wparent is self, f'{self}: Not a direct child: {w}'
            if __debug__:
                # TODO: Do this directly on v0.50, maybe with a flag
                #       Remove the `_internal` argument
                # See Also: af12f2940f607254f4e5782211397ccf38b08059
                if w.wproxy is not None:
                    warnings.warn(f'{self}: Use `.wproxy` for grid configuration of "{w}"', stacklevel=3 if _internal else 2)
            wgrid = w.wgrid
            if wgrid is not None:
                rows.update(wgrid.rows())
                columns.update(wgrid.columns())
        assert len(rows) > 0 or len(columns) > 0, f'{self}: Invalid children: {children}'
        if __debug__:
            logger_grid.debug('%s: [%sx%s]: %s', self,
                              ' '.join(str(n) for n in rows) if row else '',
                              ' '.join(str(n) for n in columns) if column else '',
                              ' '.join(f'{k}={v!r}' for k, v in arguments.items()),
                              )
        assert isinstance(self, (tk.Widget, tk.Tk, tk.Toplevel)), f'{self} is not a valid widget'
        if row:
            self.rowconfigure(tuple(rows), **arguments)
        if column:
            self.columnconfigure(tuple(columns), **arguments)

    def pgrid_r(self, *children: MixinWidget,
                **arguments: typing.Any):
        '''Wraps `pgrid`, acting only on rows.

        See `pgrid`, sets only ``row`` to `True`.
        '''
        return self.pgrid(*children, _internal=True,
                          row=True, column=False,
                          **arguments)

    def pgrid_c(self, *children: MixinWidget,
                **arguments: typing.Any):
        '''Wraps `pgrid`, acting only on columns.

        See `pgrid`, sets only ``column`` to `True`.
        '''
        return self.pgrid(*children, _internal=True,
                          row=False, column=True,
                          **arguments)

    def widgets_class(self, *classes: typing.Type[MixinWidget]) -> typing.Iterable[MixinWidget]:
        '''Filter widgets by type.

        Filter all child widgets by type.
        Very useful to apply settings to a subset of all child widgets.

        Consider proxy widgets, do the right thing.

        Arguments:
            classes: Widget Types, as classes.

        See Also:
            See `widgets_rclass` to filter recursively.
            See `widgets_except` to reverse filter child widgets.
        '''
        class_tuple = tuple(classes)
        for w in self.widgets.values():
            if isinstance(w, class_tuple):
                yield w.wproxy or w

    def widgets_rclass(self, *classes: typing.Type[MixinWidget]) -> typing.Iterable[MixinWidget]:
        '''Filter widgets by type, recursively.

        Filter all child widgets by type, including children of child
        containers.
        Very useful to apply settings to a subset of all child widgets, on
        recursive containers.

        Consider proxy widgets, do the right thing.

        Arguments:
            classes: Widget Types, as classes.

        See Also:
            See `widgets_class` to filter only for the current children.
        '''
        # Make sure any input classes are not proxies?
        class_tuple = tuple(classes)
        for w in self.widgets.values():
            winner = w.wproxy or w
            if isinstance(w, class_tuple):
                yield winner
            elif isinstance(winner, ContainerWidget):
                yield from winner.widgets_rclass(*class_tuple)

    def widgets_except(self, *widgets: MixinWidget) -> typing.Iterable[MixinWidget]:
        '''Filter widgets reversed by instance.

        Filter all child widgets by reversing a given list, i.e. produce all
        other widgets.
        Very useful to apply settings to a subset of all child widgets.

        Consider proxy widgets, do the right thing.

        Arguments:
            widgets: Child widgets to skip.

        See Also:
            See `widgets_class` to filter child widgets by class.
        '''
        for w in self.widgets.values():
            if w not in widgets or w.wproxy in widgets:
                yield w.wproxy or w
