#!/usr/bin/env python3
import typing
import argparse
import logging
from textwrap import dedent
from fractions import Fraction

from pathlib import Path
from functools import wraps, singledispatchmethod
from collections import defaultdict, Counter
from dataclasses import dataclass
import threading
from datetime import datetime
import random

import tkinter as tk
from . import LOGGING_VERBOSE, AUTO, HORIZONTAL, VERTICAL
from . import RootWindow, FrameUnlabelled, FrameLabelled, FrameStateful, FramePaned, Notebook, NotebookUniform, ScrolledWidget, Scrolled, FrameRadio, SecondaryWindow
from . import Button, Checkbox, EntryRaw, EntryN, Label, LabelStateful, Listbox, ComboboxN, EntryMultiline, Tree, SpinboxN, Radio, Canvas, SeparatorV, SeparatorH
from . import ListboxControl, CheckboxFrame, RadioFrameUnlabelled, RadioFrameLabelled, RadioFrameStateful, Tooltip
from . import var, fn, mixin, diagram, bg
from .model import CP, BindingGlobal, Timeout, TimeoutIdle, Interval, RateLimiter, FileType, FileTypes, Justification, WindowState, NotebookTabOrder, CP_ScrollAnchor
from .model import SStyle, DStyle, VSettings, EventModifier
from .validation import LimitBounded, LimitUnbounded, StaticList, StaticMap, StaticMapValues
try:
    # Try to use nicer pretty-print, from Python 3.10
    # | https://github.com/bitranox/pprint3x
    from pprint3x import pformat
except ImportError:
    from pprint import pformat


# Automatic Tab Completion
# Production Wrapper (keep the API)
class shtab:
    # Global Markers
    FILE = None
    DIRECTORY = None

    # API
    def add_argument_to(self, *args, **kwargs):
        pass


if __debug__:
    # Try to import the real deal
    try:
        import shtab  # type: ignore[assignment] # noqa: F811
    except ImportError:
        pass


logger = logging.getLogger(__name__)


def log_eventloops(eventloop, ridx, response):
    if ridx is None:
        logger.debug('eventloop=%s\t  Signal: %s', eventloop.tName, response)
    else:
        logger.debug('eventloop=%s\tResponse: %r', eventloop.tName, response)


# Diagrams
class Diagram_SolarSystem(diagram.Diagram):
    BACKGROUND = 'black'
    DISABLEDBACKGROUND = 'white'
    MIN_SIZE = (45, 70)

    W__ORBITS = 2

    W_SUN = 6
    W_EARTH = W_SUN // 2
    W_ISS = W_SUN // 3
    W_MOON = W_EARTH
    C_SUN = diagram.C(fill='yellow', outline='orange')
    C_EARTH = diagram.C(fill='blue', outline='lightblue')
    C_INNER_EARTH = diagram.C(fill='brown', outline='green')
    C_ISS = diagram.C(fill='grey60', outline='lightblue')
    C_MOON = diagram.C(fill='grey20', outline='grey80')

    # Sun "Shade"
    SUNSHADE_RANGE = (random.uniform(-80, -15), random.uniform(15, 80))
    # "Pentagon"
    INNER_LAND_EARTH = [random.uniform(4 / 10, 8 / 10) for _ in range(5)]
    INNER_TREE_EARTH = random.sample(list(enumerate(INNER_LAND_EARTH)), k=len(INNER_LAND_EARTH) - 1)

    def setup_bg_b(self, *, cwidth, cheight):
        logger.debug('Render Diagram [Background Back] %s @ %dx%d', self.__class__.__qualname__, cwidth, cheight)
        yield diagram.Text(diagram.XY(cwidth // 2, 0), 'Solar System',
                           color=diagram.C(fill='white'),
                           anchor=CP.N, font=('TkHeadingFont', 14, 'underline'),
                           tags=['labels'])

    def setup_fg(self, *, cwidth, cheight):
        logger.debug('Render Diagram [Foreground] %s @ %dx%d', self.__class__.__qualname__, cwidth, cheight)
        aspect_ratio = cwidth / cheight

        # Sun
        center_SUN = diagram.XY(0, cheight // 2)
        radius_SUN = (cheight - self.W_SUN) // 2
        yield diagram.CircleCenter(center_SUN, radius_SUN,
                                   color=self.C_SUN, colorActive=self.C_SUN.reverse,
                                   width=self.W_SUN,
                                   tags=['star']), 'sun'
        yield diagram.Text(center_SUN + diagram.VectorH(5), 'Sol',
                           color=diagram.C(fill='black'),
                           anchor=CP.W, font=('TkHeadingFont', 20),
                           tags=['labels'])

        delta_SUNSHADE = radius_SUN // 5
        yield diagram.LineVector(diagram.XY(radius_SUN - (self.W_SUN // 2), center_SUN.y), diagram.VectorPolar(delta_SUNSHADE, -180),
                                 color=diagram.C(outline=self.C_SUN.outline),
                                 arrow=diagram.A(),
                                 )
        yield diagram.ArcCircleCenter(center_SUN, radius_SUN - delta_SUNSHADE,
                                      rng=self.SUNSHADE_RANGE,
                                      color=diagram.C(outline=self.C_SUN.outline),
                                      width=self.W_SUN, dash=diagram.D(6, 4),
                                      )

        # Rest
        rest_XY = diagram.XY((radius_SUN + self.W_SUN), cheight // 2)
        rest_width = cwidth - rest_XY.x

        # # Earth
        radius_EARTH = int((radius_SUN // 5) * (1.25 * aspect_ratio))
        center_EARTH = rest_XY + diagram.VectorH(int(rest_width - 1.5 * radius_EARTH))
        yield diagram.CircleCenter(center_SUN, center_EARTH.edistance(center_SUN),
                                   color=diagram.C(outline='white'), dash=diagram.D(8, 6),
                                   width=self.W__ORBITS,
                                   tags=['orbit'])
        yield diagram.CircleCenter(center_EARTH, radius_EARTH,
                                   color=self.C_EARTH, colorActive=self.C_EARTH.reverse,
                                   width=self.W_EARTH,
                                   tags=['planet'])
        iside_EARTH = 5  # "Pentagon"
        yield diagram.Polygon([
            center_EARTH + diagram.VectorPolar(
                radius_EARTH * size,
                side * 360 / iside_EARTH,
            )
            for side, size in enumerate(self.INNER_LAND_EARTH)
        ], color=self.C_INNER_EARTH, width=2)
        yield diagram.MultiLine([
            center_EARTH + diagram.VectorPolar(
                radius_EARTH * size / 2,
                side * 360 / iside_EARTH,
            )
            for side, size in self.INNER_TREE_EARTH
        ], color=self.C_INNER_EARTH.w(fill=None), dash=diagram.D(1), width=10)
        yield diagram.Text(center_EARTH - diagram.Vector(radius_EARTH, radius_EARTH), 'Terra',
                           color=diagram.C(fill='white'),
                           anchor=CP.SE, font=('TkHeadingFont', 12),
                           tags=['labels'])

        # # # ISS
        center_ISS = center_EARTH + diagram.VectorPolar(int(1.5 * radius_EARTH), 250)
        size_ISS = int(min(radius_EARTH / 3, 150)), int(min(radius_EARTH / 3, 100))
        yield diagram.CircleCenter(center_EARTH, int(center_EARTH.edistance(center_ISS)),
                                   color=diagram.C(outline='white'), dash=diagram.D(12, 8),
                                   width=self.W__ORBITS,
                                   tags=['orbit'])
        yield diagram.RectangleCenter(center_ISS, *size_ISS,
                                      color=self.C_ISS, width=self.W_ISS,
                                      tags=['sattelite'])
        yield diagram.Text(center_ISS + diagram.Vector(-size_ISS[0], size_ISS[1]).scale(.5), 'ISS',
                           color=diagram.C(fill='white'),
                           anchor=CP.NE, font=('TkHeadingFont', 10),
                           tags=['labels'])

        # # # Moon
        center_MOON = center_EARTH + diagram.VectorPolar(cheight // 2 - 5, 220)
        radius_MOON = min(radius_EARTH // 1.5, cheight // 15, cwidth // 20)
        yield diagram.CircleCenter(center_EARTH, int(center_EARTH.edistance(center_MOON)),
                                   color=diagram.C(outline='white'), dash=diagram.D(6, 4),
                                   width=self.W__ORBITS,
                                   tags=['orbit'])
        yield diagram.CircleCenter(center_MOON, radius_MOON,
                                   color=self.C_MOON, colorActive=self.C_MOON.reverse,
                                   width=self.W_MOON,
                                   tags=['planet', 'planet:secondary']), 'moon'
        yield diagram.Text(center_MOON - diagram.VectorH(int(1.5 * radius_MOON)), 'Luna',
                           color=diagram.C(fill='white'),
                           anchor=CP.E, font=('TkHeadingFont', 12),
                           tags=['labels'])


# Event Loops
@dataclass(frozen=True)
class ELReq_SleepState(bg.ELReq):
    state: bool


@dataclass(frozen=True)
class ELReq_Sleep(bg.ELReq):
    duration: float


@dataclass(frozen=True)
class ELReq_Nothing(bg.ELReq):
    pass


@dataclass(frozen=True)
class ELRes_Nothing(bg.ELRes):
    pass


@dataclass(frozen=True)
class ELRes_Log(bg.ELRes):
    ltml: str


@dataclass(frozen=True)
class ELRes_Error(bg.ELRes):
    string: str


class EL_Sleep(bg.EventLoop):
    name = 'sleep'
    priorities = {
        ELReq_SleepState: -10,  # High Priority
    }

    def setup_eventloop(self, *, example_kwarg: str):  # type: ignore[override]
        if self.qoutput is not None:
            logger.debug('%s: Output Queue', self.tName)
        elif self.wcallback is not None:
            logger.debug('%s: Callback @ %s', self.tName, self.wcallback.widget)
        logger.debug('# Example `kwarg`: %s', example_kwarg)
        self.sleep_state: typing.Optional[bool] = None

    @singledispatchmethod
    def process(self, task, priority):
        raise NotImplementedError(f'T={task} P={priority}')

    @process.register
    def process_Nothing(self, task: ELReq_Nothing, priority: int):
        if random.random() > 0.75:
            self.error('Sleeping a while')
            self.usleep(5)
            self.error('Slept for a bit')
        else:
            self.log('Doing Nothing!')

    @process.register
    def process_SleepState(self, task: ELReq_SleepState, priority: int):
        self.sleep_state = task.state
        self.log(f'Sleep State: {self.sleep_state}')

    @process.register
    def process_Sleep(self, task: ELReq_Sleep, priority: int):
        assert self.sleep_state is not None
        if self.sleep_state:
            duration = task.duration
            assert isinstance(duration, int)
            self.log(f'Sleep {duration} s')
            if self.isleep(duration):
                self.log('Wake Up!')
            else:
                self.error('Interrupted sleeping')
        else:
            self.log('Sleep <b>SKIPPING</b>')

    def error(self, txt: str):
        self.respond(ELRes_Error(txt))

    def log(self, txt: str):
        self.respond(ELRes_Log(txt))


# Complex Widgets
class TooltipSimple(Tooltip):
    def setup_widgets(self):
        self.mtitle = LabelStateful(self, anchor=CP.center,
                                    styleID='Title')
        self.message = LabelStateful(self)

    def setup_layout(self, layout):
        self.mtitle.grid(sticky=tk.EW)

    def setup_defaults(self):
        self.wstate = {
            'mtitle': 'This is a title',
            'message': dedent('''
            This is a veeeeeeeeery looooooong message in a Tooltip.
            Multiline, please do something about it, like restricting the width?
            '''),
        }


class TooltipSingleStatic(Tooltip):
    wstate_single = 'message'

    def setup_widgets(self, tt_message: str):
        self.message = Label(self, label=tt_message,
                             styleID='Title')


class TooltipSingle(Tooltip):
    wstate_single = 'message'

    def setup_widgets(self):
        self.message = LabelStateful(self, styleID='Title')

    def setup_defaults(self):
        self.wstate = 'This is a very simple message'


class LuftBaloons(FrameUnlabelled):
    layout = 'xE'

    def setup_widgets(self, howmany=16 - 3):
        assert howmany > 1
        widgets = {}
        for widx in range(howmany):
            idx = 'lb:%d' % widx
            widget = Checkbox(self, label='%02d' % widx)
            widget.trace(self.onToggle_lb, idx=idx)
            widgets[idx] = widget
        # Ignore the second checkbox
        fn.state_ignore(widgets['lb:1'])
        return widgets

    def onToggle_lb(self, vobj, etype, *, idx):
        pass
        # logger.debug('Clicked on "%s" @ %s:%s', idx, vobj, etype)
        # logger.debug('- State: %r', vobj.get())


class ListFrame_Inner(FrameStateful):
    wstate_single = 'e'

    def __init__(self, *args, label, **kwargs):
        super().__init__(*args, label=label, labelInner=label, **kwargs)

    def setup_widgets(self, labelInner, *, ljust=Justification.NoJustify):
        self.lbl = Label(self, label=f'Label: {labelInner}', justify=ljust)
        self.e = EntryRaw(self, justify=ljust)  # label=f'EntryRaw: {labelInner}'


class ListFrame_Outer_Label(FrameUnlabelled):
    layout = HORIZONTAL

    def setup_widgets(self):
        self.cbL = Checkbox(self, label='').putIgnoreState()
        self.lbl = Label(self, label='Child Widgets\nare Justified',
                         anchor=CP.N, expand=True)
        self.cbR = Checkbox(self, label='').putIgnoreState()


class ListFrame_Outer(FrameStateful):
    label = 'Outer Frame'
    layout = 'R1,2,1'

    def setup_widgets(self, *, cbox1):
        self.lbls = ListFrame_Outer_Label(self)
        self.left = ListFrame_Inner(self, label='Left',
                                    cvariableDefault=True,
                                    labelAnchor=CP.NW, ljust=Justification.Left)
        self.right = ListFrame_Inner(self, label='Right',
                                     cvariableDefault=False,
                                     labelAnchor=CP.NE, ljust=Justification.Right)
        self.bottom = ListFrame_Inner(self, label='Center',
                                      cvariable=cbox1,
                                      labelAnchor=CP.N, ljust=Justification.Center)


class ListFrame_Lists(FramePaned):
    layout = HORIZONTAL
    # Do not grow RO widget
    pweigths = {
        'lstRO': 0,
    }

    def setup_widgets(self, *, vLst):
        self.lstS = Listbox(self,
                            height=6,
                            variable=vLst,
                            selectable=True)  # Selectable
        self.lstRO = ScrolledWidget(self, Listbox, label='Unselectable',
                                    maxHeight=3, expand=True,  # Varying Height, Expanded  # N/A on FramePaned
                                    variable=vLst,
                                    selectable=False,
                                    style=Listbox.Style(altbg=True),
                                    styleID='FontTTY',
                                    )  # Not Selectable


class ListFrame__Actions(FrameUnlabelled):
    layout = HORIZONTAL

    def setup_widgets(self):
        self.op1 = Button(self, label='Op1',
                          styleID='Small')
        self.op2 = Button(self, label='Op2',
                          styleID='Small')

    def setup_adefaults(self):
        counter = Counter()
        self.op1.bindClick(self.onAction, name='OP1', counter=counter)
        self.op2.bindClick(self.onAction, name='OP2', counter=counter)

    def onAction(self, *, name: str, counter: Counter):
        counter[name] += 1
        logger.debug('Action: %s #%d', name, counter[name])


class MiscFrame(FrameStateful):
    label = 'List Box'
    layout = 'R3,1,2,1'

    def setup_widgets(self, *, cbox1) -> None:
        self.bFill = Button(self, label='Fill Me!')
        self.lPanes = Label(self, label='↓ Drag Separator ↓')
        self.bCheck = Button(self, label='Check')

        vLst = self.var(var.StringList, name='lst')
        self.cLst = ListFrame_Lists(self, vLst=vLst)

        self.bChoice = Button(self, label='CB=2')
        self.i_choice = ComboboxN(self, StaticMapValues(lambda i: 'I%d' % i, range(10), defaultValue=7))  # label='CB(int)'A

        self.rstateful = ListFrame_Outer(self,
                                         label='Outer Frame (no trace)', labelAnchor=CP.N,
                                         cbox1=cbox1,
                                         ).putIgnoreTrace()

        self._actions = ListFrame__Actions(self).putAuto()

    def setup_layout(self, layout):
        self.pgrid_r(self.cLst, weight=0)

        self._actions.place(anchor=CP.NE.value, relx=1, rely=0,
                            x=-2, y=SStyle.Size_YF_Frame)

    def setup_defaults(self):
        self.fill_lst()
        # Events
        self.bFill.onClick = self.fill_lst
        self.bCheck.onClick = self.check_lst
        self.bChoice.onClick = self.i_choice.eSetValue(2)

        self.i_choice.trace(self.onChosen)

        BindingGlobal(self.bChoice, '<F1>', self.globalHelp,
                      immediate=True, description='Nothing, just showing the event object')
        # EventBus
        self.wroot.register_eventbus_response(self.onUpstreamMessage, event=(ELRes_Error, ELRes_Log))

    def setup_adefaults(self):
        # Note that with `trace`, this runs too soon
        # Do not set `trace_initial=True`, this is a "secret" change
        self.cstate_widget.atrace(self.onCStateChange)
        # Why not verify some invariants?
        assert self.wroot_search() == self.wroot, 'Invalid Root calculation'
        # Scroll RO list to bottom
        self.cLst.lstRO.wproxy.scrollTo(y=1.0)

    def fill_lst(self):
        ctime = str(datetime.now())
        self.gvar('lst').set(['A', 'List', 'Of', 'Letters', '@', ctime])

    def check_lst(self):
        sel = self.cLst.lstS.wselection()
        logger.debug('S: %r', sel)

    def onChosen(self, variable, etype):
        logger.debug('V: %r', variable)
        logger.debug('   Choose: %s', variable.get())

    def onCStateChange(self, var, etype):
        cstate = var.get()
        lwidget = self.lPanes
        logger.debug('Changed State: %s', cstate)
        if cstate:
            lwidget.change(label='↓ Drag Separator ↓')
            lwidget.genabled(False)
        else:
            lwidget.change(label='Do Nothing')

    def onUpstreamMessage(self, eventloop, ridx, response):
        if isinstance(response, ELRes_Error):
            logger.debug('Error @ EventLoop %s: %s', eventloop.tName, response)
        elif isinstance(response, ELRes_Log):
            logger.debug('  Log @ EventLoop %s', eventloop.tName)
        else:
            raise NotImplementedError

    def globalHelp(self, event=None):
        if event:
            logger.debug('Event: %r', event)


class UpstreamBool(FrameLabelled):
    layout = 'x1N'  # Bottom-Up
    # Comment the following line to change the state
    isNoneable = False  # Don't skip this widget, even when its state is `None`

    def __init__(self, *args, what_bool, **kwargs):
        super().__init__(*args, what_bool=what_bool, **kwargs)
        if what_bool is None:
            # If this doesn't use upstream booleans, mark as single state
            self.wstate_single = 'u_bool'

    def setup_widgets(self, what_bool):
        self.bOnFS = Button(self, label='Toggle FullScreen')
        self.u_bool = Checkbox(self, variable=what_bool, label='Upstream "bool"')
        self.bNoOp_Big = Button(self, label='No Operation')

    def setup_adefaults(self):
        self.bOnFS.onClick = self.onRootFS
        self.bNoOp_Big.onClick = self.onNoOp

    def onRootFS(self, event=None):
        self.wroot.rgstate = WindowState(fullscreen=not self.wroot.rgstate.fullscreen)

    def onNoOp(self, event=None):
        logger.debug('"No Op", choosing a random label')
        self.bNoOp_Big.change(label=random.choice(['No Op', 'NoOp', 'NOOP']))


class NB_Child_Simple(FrameUnlabelled):
    layout = 'Rx,1'
    wstate_single = 'e'

    def setup_widgets(self, label):
        w = {}
        for n in range(5):
            w[f'n{n}'] = Label(self, label=f'{n}: {label}')
        w['e'] = LabelStateful(self, labelPosition=CP.E,
                               image=random.choice(self.wroot.images_builtin))
        return w

    def setup_defaults(self):
        self.widgets['e'].binding('<Button-1>', self.onClick_E)

    def setup_adefaults(self):
        self.widgets['e'].wstate = 'Clickable LabelStateful'

    def onClick_E(self, event=None):
        w = self.widgets['e']
        state = w.wstate
        suffix = ' T'
        # TODO: On Python 3.9:: -> state.removesuffix(suffix)
        if not state.endswith(suffix):
            state += suffix
            imgname = 'warning-s16'
        else:
            state = state[:-len(suffix)]
            imgname = 'info-s16'
        w.wstate = state
        w.change(image=self.wimage(imgname))


class NB_Child_Complex_NB(NotebookUniform):
    tabids = {f'TC{d}': f'Tab Complex {d}' for d in range(7)}

    def setup_tab(self, tid: str, tname: str, *, labelPrefix):  # type: ignore[override]
        return Scrolled(self, NB_Child_Simple, label=f'{tid} @ {labelPrefix}')


class NB_Child_Complex(FramePaned):
    layout = HORIZONTAL
    pweigth = 0  # Keep defaults sizes uniform

    def setup_widgets(self):
        self.sidel = NB_Child_Complex_NB(self, traversalWraparound=False,
                                         tabArgs={'image': random.choice(self.wroot.images_builtin)},
                                         labelPrefix='Top',
                                         styleID='TabCenterTop|TabLarge')
        self.sider = NB_Child_Complex_NB(self, traversalWraparound=True,
                                         tabArgs={'image': random.choice(self.wroot.images_builtin)},
                                         labelPrefix='Bottom',
                                         styleID='TabCenterBottom|TabLarge')

    def setup_adefaults(self):
        nb = self.sidel
        # logger.debug('Change top widget:')
        # logger.debug('   Default: %s', nb.torder_get())
        # nb.torder_change(disable=['TC2'])
        # logger.debug('  Disabled: %s', nb.torder_get())
        # nb.torder_change(enable=['TC2'])
        # logger.debug('Re-Enabled: %s', nb.torder_get())
        # nb.torder_change(disable=['TC1', 'TC3'],
        #                  hide=['TC2'])
        # nb.insert(tk.END, nb.wtabs['TC0'].widget)
        # nb.insert(0, nb.wtabs['TC4'].widget)
        # logger.debug('     Final: %s', nb.torder_get())
        nb.torder = NotebookTabOrder(
            shown=('TC1', 'TC4', 'TC0', 'TC3'),
            disabled={'TC1', 'TC3'},
        )
        # logger.debug('       Set: %s', nb.torder_get())


class NB_Child_Timeout(FrameLabelled):
    label = 'Timeout'

    def __init__(self, *args, **kwargs):
        self.t = Timeout(self, self.onTimeout, 1000, immediate=False)
        super().__init__(*args, **kwargs)

    def setup_widgets(self):
        self.cScheduled = Checkbox(self, label='Scheduled?', readonly=True,
                                   styleID='ReadonlyEmphasis')
        self.cTriggered = Checkbox(self, label='Triggered?', readonly=True,
                                   styleID='ReadonlyEmphasis')
        self.bToggle = Button(self, label='Toggle\nasync')

        self.bToggle.onClick = self.onToggle

    def setup_defaults(self):
        self.update()

    def update(self):
        self.cScheduled.wstate = self.t.isScheduled()
        self.cTriggered.wstate = self.t.isTriggered()

    def onToggle(self):
        self.t.toggle()
        self.update()

    def onTimeout(self):
        logger.debug('Timeout!')
        self.update()


class NB_Child_Timeout_Delay(FrameLabelled):
    label = 'Timeout (Delayed)'

    def __init__(self, *args, **kwargs):
        self.t = Timeout(self, self.onTimeout, 1000, immediate=False)
        super().__init__(*args, **kwargs)

    def setup_widgets(self):
        self.cScheduled = Checkbox(self, label='Scheduled?', readonly=True)
        self.cTriggered = Checkbox(self, label='Triggered?', readonly=True)
        self.bToggle = Button(self, label='  Toggle\nasync-ish')

        self.bToggle.onClick = self.onToggle

    def setup_defaults(self):
        self.update()

    def update(self):
        self.cScheduled.wstate = self.t.isScheduled()
        self.cTriggered.wstate = self.t.isTriggered()

    def onToggle(self):
        self.t.toggle()
        self.update()

    def onTimeout(self):
        logger.debug('Timeout!')
        self.update()
        logger.debug('Delay ...')
        self.after(1000)
        logger.debug('... Done!')


class NB_Child_TimeoutIdle_Delay(FrameLabelled):
    label = 'TimeoutIdle (Delayed)'

    def __init__(self, *args, **kwargs):
        self.t = TimeoutIdle(self, self.onTimeout, immediate=False)
        self.tsleep = TimeoutIdle(self, lambda: self.after(1000), immediate=False)  # Pretend this is a long calculation
        super().__init__(*args, **kwargs)

    def setup_widgets(self):
        self.cScheduled = Checkbox(self, label='Scheduled?', readonly=True)
        self.cTriggered = Checkbox(self, label='Triggered?', readonly=True)
        self.bToggle = Button(self, label='Toggle\n sync')

        self.bToggle.onClick = self.onToggle

    def setup_defaults(self):
        self.update()

    def update(self):
        self.cScheduled.wstate = self.t.isScheduled()
        self.cTriggered.wstate = self.t.isTriggered()

    def onToggle(self):
        ts = [self.tsleep, self.t]
        # (un)schedule both timeouts in tandem
        if self.t.isScheduled():
            for t in ts:
                t.unschedule()
        else:
            for t in ts:
                t.schedule()
        self.update()

    def onTimeout(self):
        logger.debug('TimeoutIdle!')
        self.update()


class NB_Child_TimeoutIdle_Chain(FrameLabelled):
    label = 'TimeoutIdle (Chained)'

    def __init__(self, *args, **kwargs):
        self.tsleep = TimeoutIdle(self, self.onTimeoutSleep, immediate=False)
        self.t = TimeoutIdle(self, self.onTimeout, immediate=False)
        super().__init__(*args, **kwargs)

    def setup_widgets(self):
        self.cScheduled = Checkbox(self, label='Scheduled?', readonly=True)
        self.cTriggered = Checkbox(self, label='Triggered?', readonly=True)
        self.bToggle = Button(self, label='Toggle\n sync')

        self.bToggle.onClick = self.onToggle

    def setup_defaults(self):
        self.update()

    def update(self):
        self.cScheduled.wstate = self.t.isScheduled()
        self.cTriggered.wstate = self.t.isTriggered()

    def onToggle(self):
        ts = [self.tsleep, self.t]
        # (un)schedule both timeouts in tandem
        if self.t.isScheduled():
            for t in ts:
                t.unschedule()
        else:
            for t in ts:
                t.schedule()
        self.update()

    def onTimeoutSleep(self):
        logger.debug('Chain Delay ...')
        self.after(1000)
        logger.debug('... Done!')
        self.t.schedule()
        self.update()

    def onTimeout(self):
        logger.debug('TimeoutIdle!')
        self.update()


class NB_Child_Timeouts(FrameUnlabelled):
    # layout = HORIZONTAL

    def setup_widgets(self):
        self.timeout = NB_Child_Timeout(self)
        self.timeout_d = NB_Child_Timeout_Delay(self)
        self.timeout_idle_d = NB_Child_TimeoutIdle_Delay(self)
        self.timeout_idle_c = NB_Child_TimeoutIdle_Chain(self)


class NB_Child_Interval(FrameUnlabelled):
    layout = 'R3,3'

    def __init__(self, *args, **kwargs):
        self.interval = Interval(self, self.onInterval, 1000, immediate=False)
        super().__init__(*args, **kwargs)

    def setup_widgets(self):
        self.txt_lbl = Label(self, label='Count (1s)')
        self.txt = EntryRaw(self, justify=Justification.Center, readonly=True)
        self.stateScheduled = Checkbox(self, label='Scheduled?', readonly=True)
        self.state_on = Button(self, label='ON')
        self.state_off = Button(self, label='OFF')
        self.state_offforce = Button(self, label='OFF (Force)')

    def setup_defaults(self):
        self.txt.wstate = 'Elapsed Seconds'

    def setup_adefaults(self):
        self.state_on.onClick = self.onIntervalOn
        self.state_off.onClick = self.onIntervalOff
        self.state_offforce.onClick = self.onIntervalOffForce

    def onIntervalOn(self, event=None):
        if self.interval.scheduled:
            logger.debug('Already Scheduled')
        else:
            self.txt.wstate = str(0)
            self.interval.schedule()
        self.stateScheduled.wstate = self.interval.scheduled
        self.state_off.focus()

    def onIntervalOff(self, event=None):
        self.interval.unschedule()
        self.state_on.focus()
        self.stateScheduled.wstate = self.interval.scheduled

    def onIntervalOffForce(self, event=None):
        was_scheduled = self.interval.scheduled
        self.interval.unschedule(force=True)
        if was_scheduled:
            self.txt.wstate = f'Force Stop at {self.txt.wstate}'
        self.stateScheduled.wstate = self.interval.scheduled
        self.state_on.focus()

    def onInterval(self):
        new_state = str(int(self.txt.wstate) + 1)
        if self.interval.scheduled:
            self.txt.wstate = new_state
        else:
            self.txt.wstate = f'Stop at {new_state}'


class NB_Child_RateLimiter(FrameUnlabelled):
    layout = 'R2,1,2'

    def setup_widgets(self):
        self.txt_lbl = Label(self, label='Now')
        self.txt = EntryRaw(self, readonly=True,
                            justify=Justification.Center, width=30)
        self.hit_lbl = Label(self, label='Hit me Hard!\nCount will only change once per second.\nThe timings are not perfect.')
        self.buttonHit = Button(self, label='HIT')
        self.stateRL = Checkbox(self, label='Rate Limited?', readonly=True)

    def setup_defaults(self):
        self.txt.wstate = str(0)

    def setup_adefaults(self):
        rl = RateLimiter(self, self.onRL, 1000)
        self.buttonHit.bindClick(self.onHit, rl=rl)

    def onHit(self, *, rl):
        self.stateRL.wstate = not rl.hit()

    def onRL(self):
        self.txt.wstate = f"{datetime.now().isoformat(' ', timespec='microseconds')} μs"
        if self.stateRL.wstate:
            logger.debug('Clear RateLimit marker')
            self.stateRL.wstate = False


class NB_Child_Dialog(FrameUnlabelled):
    layout = 'Rx,1'
    wstate_single = 'txt'

    def setup_widgets(self):
        self.ds = Button(self, label='D S')
        self.dl = Button(self, label='D L')
        self.fs = Button(self, label='F S')
        self.fl = Button(self, label='F L')
        self.flc = Button(self, label='F L(py)')
        self.fsc = Button(self, label='F S(py)')
        self.txt = LabelStateful(self)

    def setup_adefaults(self):
        # TODO: Use `bindClick` everywhere
        self.ds.onClick = self.click(fn.ask_directory_save, self, title='Directory @ .',
                                     initialDirectory=Path('.'))
        self.dl.onClick = self.click(fn.ask_directory_load, self, title='Directory @ Home',
                                     initialDirectory=Path('~').expanduser())
        self.fs.onClick = self.click(fn.ask_file_save, self, title='File @ ..',
                                     initialDirectory=Path('..'))
        self.fl.onClick = self.click(fn.ask_file_load, self, title='File @ /',
                                     initialDirectory=Path('/'))
        vtype = var.String()
        self.fsc.onClick = self.click(self.customFile, fn.ask_file_save, vtype=vtype)
        self.flc.onClick = self.click(self.customFile, fn.ask_file_load, vtype=vtype)

    def click(self, fn, *args, **kwargs):
        vtype = kwargs.get('vtype')

        @wraps(fn)
        def wrapped():
            self.txt.wstate = ''
            ret = fn(*args, **kwargs)
            ret_loc = ret.resolve() if ret else ret
            ret_exists = str(ret.exists()) if ret else 'N/A'
            ret_selection = vtype.get() if vtype else ''
            self.txt.wstate = '\n'.join((
                f'{ret_loc}',
                f'Exists: {ret_exists}',
                f'Selection: {ret_selection}',
            ))
        return wrapped

    def customFile(self, function, vtype):
        return function(self, title='Custom Python Files @ .',
                        typevariable=vtype,
                        initialDirectory=Path('.'),
                        includeAll=False, filetypes=FileTypes({
                            'Python': FileType('py'),
                            'TOML': FileType('toml'),
                        }))


class NB_Child_Scrollbars(FrameUnlabelled):
    layout = 'R2,x'
    wstate_single = 'slst'

    def setup_widgets(self):
        self.randomize = Button(self, label='Randomize List Size')
        self.setscrolls = Button(self, label='Toggle Scrollbars')

        vSlist = self.var(var.StringList, name='slst')
        self.sbL = ScrolledWidget(self, Listbox,
                                  scrollHorizontal=None, scrollVertical=None,  # Auto (default)
                                  height=5, variable=vSlist)
        self.sbC = ScrolledWidget(self, Listbox,
                                  scrollHorizontal=False, scrollVertical=False,  # Manual, disabled
                                  height=5, variable=vSlist)
        self.sbR = ScrolledWidget(self, Listbox,
                                  scrollHorizontal=True, scrollVertical=True,  # Manual, enabled
                                  height=5, variable=vSlist)

        self.randomize.onClick = self.onRandom
        self.setscrolls.onClick = self.onShowAll

    def setup_layout(self, layout):
        self.pgrid_r(*self.widgets_class(Button),
                     weight=0)

    def setup_adefaults(self):
        self.onRandom()

    def onRandom(self, event=None):
        randomsize = random.randint(5, 30)  # Allow an opportunity for no vertical scrollbar
        self.gvar('slst').set([f'Index {i:03}' for i in range(1, randomsize + 1)])

    def onShowAll(self, event=None):
        # sbL: Auto, Set True
        self.sbL.wproxy.set_scroll_state(True, True)
        # sbC: Manual, Set True (no-op)
        self.sbC.wproxy.set_scroll_state(True, True)
        # sbR: Manual, Set Reversed
        self.sbR.wproxy.set_scroll_state(*(not b for b in self.sbR.wproxy.get_scroll_state()))


class NB_Complex_ListboxSet(FrameUnlabelled):
    layout = 'C1,2'

    def setup_widgets(self):
        self.__all = StaticList((f'String {idx:02}' for idx in range(1, 16)), defaultIndex=0)

        ls_full = list(random.sample(self.__all, k=5))
        self.full = ListboxControl(self, selAll=self.__all, label='Full Control',
                                   style=Listbox.Style(altbg=True), allKwargs={'width': 9},
                                   buttonOne=True, buttonAll=True, buttonOrder=True)
        self.nosingle = ListboxControl(self, layout='C1,x', label='No Single',
                                       selAll=self.__all, selList=ls_full,
                                       buttonOne=False, buttonAll=True, buttonOrder=True)
        self.order = ListboxControl(self, label='Only Order',
                                    height=2,
                                    buttonOne=False, buttonAll=False, buttonOrder=True)

    def setup_layout(self, layout):
        self.pgrid_c(self.full, weight=0)
        btnFat = (
            # self.nosingle.moveUp, self.nosingle.moveDown,
            self.nosingle.addAll, self.nosingle.rmAll,
            self.order.moveUp, self.order.moveDown,
        )
        for w in btnFat:
            w.grid(sticky=tk.NSEW)

    def setup_defaults(self):
        self.full.onAddAll()
        self.order.wstate = random.sample(self.__all, k=2)


class NB_Complex_CheckboxList(CheckboxFrame):
    def __init__(self, *args, **kwargs):
        kwargs.update({
            'stateCheckboxes': {
                '%d' % n: 'Check #%d' % n
                for n in range(0, 15, 3)
            },
            'label': 'TopLevel Label',
            'labelsCheckboxes': {
                # See the order of label keys
                '0': 'CB #0',
                ('0',): 'CheckBox #0',
            },
            'layoutCheckboxes': '2x3',
        })
        super().__init__(*args, **kwargs)


class NB_Complex_CheckboxNested(CheckboxFrame):
    def __init__(self, *args, **kwargs):
        self._bState = True
        kwargs.update({
            'layout': 'H1,2,x',
            'hasButtons': [  # Custom buttons, changes the layout above
                CheckboxFrame.IButton('enable', 'Enable ALL',
                                      onClickSetAll=True),
                CheckboxFrame.IButton('disable', 'Disable ALL',
                                      onClickSetAll=False),
                CheckboxFrame.IButton('other', 'Other',
                                      self.onClickOther),
            ],
            'stateCheckboxes': {
                **{
                    'N1(%d)' % nn: {
                        'N2(%d)' % nnn: 'N2(%d|%d)' % (nn, nnn)
                        for nnn in range(2)
                    }
                    for nn in range(3)
                },
                **{
                    'NN1(0)': {
                        'NN2': 'NN2(0|0)',
                        **{
                            'NN2(%d)' % N: {
                                'NN3(%d)' % NN: 'NN3(0|%d|%d)' % (N, NN)
                                for NN in range(3)
                            }
                            for N in range(1, 2 + 1)
                        },
                    },
                },
            },
            'stateDefault': True,
            'layoutCheckboxes': [HORIZONTAL, VERTICAL, 'R1,x'],
            'labelsCheckboxes': {
                ('NN1(0)',): 'NN1 [[0]]',
                **{
                    ('N1(%d)' % nn,): 'N1 [[%d]]' % nn
                    for nn in range(2)
                }
            },
            'traceFn': self.onCheckboxClick,
        })
        super().__init__(*args, **kwargs)

    def setup_layout(self, layout):
        super().setup_layout(layout)
        self.pad_container(2)

    def onCheckboxClick(self, *what):
        def onCheckboxClick(var, etype):
            logger.debug('Trace: %s [%s]', ' » '.join(what), var.get())
        return onCheckboxClick

    def onClickOther(self):
        logger.debug('Click "Other" @ %s', self)
        new_state = not self._bState
        logger.debug('- State: %s -> %s', self._bState, new_state)
        bEnabled = self.wbutton('enable')
        bDisabled = self.wbutton('disable')
        for w in (bEnabled, bDisabled):
            w.genabled(new_state)
        self._bState = new_state


class NB_Complex_RadioFrame(FrameUnlabelled):
    wstate_single = False
    layout = 'Rx,3'

    def setup_widgets(self):
        sr_l = StaticMap(
            {
                'S#%d' % n: str(n)
                for n in range(1, random.randint(5, 15))
            }, defaultValue=str(random.choice(range(1, 5))),
        )
        sr_c = StaticMap(
            {
                '%s#%d' % (random.choice(('S', 'Section')), n): str(n)
                for n in range(1, random.randint(3, 8))
            }, defaultValue=str(random.choice(range(1, 3))),
        )
        sr_r = StaticMap(
            {
                'S#%d' % n: str(n)
                for n in range(1, random.randint(5, 7))
            }, defaultValue=str(random.choice(range(1, 5))),
        )
        self.b_l = Button(self, label='Random Left').attachTooltip(message='No Warning')
        self.b_tc = Button(self, label='Toggle Center').attachTooltip(
            TooltipSingleStatic, tt_message='Warns',
        )
        self.b_r = Button(self, label='Random Right').attachTooltip(message='No Warning')
        self.rf_l = RadioFrameLabelled(self, stateRadio=sr_l, label='Left',
                                       frameArgs={'layout': AUTO})
        self.rf_c = RadioFrameStateful(self, stateRadio=sr_c, label='Center',
                                       labelAnchor=CP.S,
                                       frameArgs={
                                           'layout': VERTICAL,
                                           'style': RadioFrameUnlabelled.Style(
                                               align_vertical=True,
                                           ),
                                       })
        self.rf_r = RadioFrameStateful(self, stateRadio=sr_r, label='Right')

    def setup_layout(self, layout):
        self.pgrid_c(self.rf_c,
                     weight=0)
        self.pgrid_r(*self.widgets_class(Button),  # Buttons
                     weight=0)

    def setup_adefaults(self):
        self.b_l.bindClick(self.onRandomW, rvar=self.rf_l.variable)
        self.b_tc.bindClick(self.rf_c.toggle)
        self.b_r.bindClick(self.onRandomW, rvar=self.rf_r.raw.variable)
        # Trace "complex" widgets
        if __debug__:
            self.rf_l.trace(self.onChangedW, twidget=self.rf_l,
                            trace_name='RFL')
            self.rf_r.trace(self.onChangedW, twidget=self.rf_r,
                            trace_name='RFS')

    def onChangedW(self, var, etype, *, twidget):
        assert etype == 'write'
        logger.debug('%s:: new=%s', twidget, twidget.wstate)

    def onRandomW(self, *, rvar):
        choice = random.choice(rvar.lall())
        rvar.set(choice)


class NB_Child_Checkboxen(FrameStateful):
    layout = VERTICAL
    wstate_single = 'cb'

    def setup_widgets(self, *, cbReadonly: bool):
        cb_str = 'RO' if cbReadonly else 'RW'
        self.cb = Checkbox(self, label=f'Checkbox {cb_str}', readonly=cbReadonly)


class NB_Complex_ChechboxRORW_Reversed(FrameStateful):
    label = 'Reversed'
    layout = HORIZONTAL

    def setup_widgets(self, *, rw, ro):
        self.rw = NB_Child_Checkboxen(self, label='ReadWrite (Frame=ReadWrite)',
                                      cvariable=rw, cstateReadonly=False,
                                      cbReadonly=False, cstateReversed=True)
        self.ro = NB_Child_Checkboxen(self, label='ReadOnly (Frame=ReadOnly)',
                                      cvariable=ro, cstateReadonly=True,
                                      cbReadonly=True, cstateReversed=True)


class NB_Complex_ChechboxRORW(FrameUnlabelled):
    layout = 'R2,1,x'

    def setup_widgets(self):
        self.rw = NB_Child_Checkboxen(self, label='ReadWrite', cbReadonly=False)
        self.ro = NB_Child_Checkboxen(self, label='ReadOnly', cbReadonly=True)
        self.rev = NB_Complex_ChechboxRORW_Reversed(self, labelAnchor=CP.S,
                                                    rw=self.rw.cstate, ro=self.ro.cstate)
        self.read = Button(self, label='Check')
        self.toggle_rw = Button(self, label='Toggle RW "alternate"')

    def setup_layout(self, layout):
        self.pgrid_r(*self.widgets_except(self.rw, self.ro),
                     weight=0)
        self.toggle_rw.grid(sticky=tk.EW)

    def setup_adefaults(self):
        self.read.onClick = self.onRead
        self.toggle_rw.onClick = self.onToggleRW

    def onRead(self):
        logger.debug('=> GUI State for Checkbox')
        logger.debug('   RW: %s', self.rw.cb.gstate)
        logger.debug('   RO: %s', self.ro.cb.gstate)

    def onToggleRW(self):
        for w in (self.rw, self.rev.rw):
            w.cb.galternate_toggle()


class NB_Complex_Validation_Spinbox(FrameLabelled):
    layout = 'x2E'

    def setup_widgets(self, lim: LimitBounded):
        self.labelNV = Label(self, label='No Validation')
        self.nv = SpinboxN(self, vspec=lim,
                           validation=False,
                           styleID='Big')

        vspinbox = self.varSpec(var.Limit, lim,
                                name='vspinbox')
        assert isinstance(vspinbox, var.LimitBounded)

        self.labelVRO = Label(self, label='Valid ReadOnly')
        self.v_ro = SpinboxN(self, vspec=vspinbox,
                             readonly=True, validation=True,
                             styleID='Big|Valid')

        self.labelVRW = Label(self, label='Valid ReadWrite')
        self.v_rw = SpinboxN(self, vspec=vspinbox,
                             readonly=False, validation=VSettings(
                                 postFocusIn=True, postFocusOut=True,
                             ),
                             styleID='Big|Valid')

        self.labelVNV = Label(self, label='Valid !="No Validation"')
        self.v_nv = SpinboxN(self, lim,
                             readonly=False, validation=self.onValidNV,
                             styleID='Big|Valid')

    def setup_layout(self, layout):
        wlabels = set()
        for wname, w in self.widgets.items():
            if wname.startswith('label'):
                wlabels.add(w)
                w.grid(sticky=tk.W)
            else:
                w.grid(sticky=tk.EW)
        self.pgrid_c(*wlabels,
                     weight=0, uniform='label')

    def setup_defaults(self):
        self.nv.wstate = '5'
        self.gvar('vspinbox').set('invalid')
        self.v_nv.wstate = '7'

    def setup_adefaults(self):
        self.nv.trace(self.v_nv.doValidation, trace_name='__:validation:nv')

    def onValidNV(self, vstate, why):
        assert why is not None, 'Requires `fnSimple=False`'
        upstream = why.validation()
        if upstream is not True:
            # If there's an error on parsing the value, error out
            return upstream
        else:
            # If the value is valid, compare it with the other widget
            return self.nv.wstate.label != vstate.label


class NB_Complex_Validation_Combobox(FrameLabelled):
    layout = 'x2E'

    def setup_widgets(self, lim: LimitBounded):
        self.labelNV = Label(self, label='No Validation')
        self.nv = ComboboxN(self, vspec=lim,
                            validation=False,
                            styleID='Big')

        vcombobox = self.varSpec(var.Limit, lim,
                                 name='vcombobox')
        assert isinstance(vcombobox, var.LimitBounded)

        self.labelVRO = Label(self, label='Valid ReadOnly')
        self.v_ro = ComboboxN(self, vspec=vcombobox,
                              readonly=True, validation=True,
                              styleID='Big|Valid')

        self.labelVRW = Label(self, label='Valid ReadWrite')
        self.v_rw = ComboboxN(self, vspec=vcombobox,
                              readonly=False, validation=VSettings(
                                  postFocusIn=True, postFocusOut=True,
                              ),
                              styleID='Big|Valid')

        self.labelVNV = Label(self, label='Valid !="No Validation"')
        self.v_nv = ComboboxN(self,
                              vspec=lim,
                              readonly=False, validation=VSettings(
                                  fn=self.onValidNV, fnSimple=False,
                              ),
                              styleID='Big|Valid')

    def setup_layout(self, layout):
        wlabels = set()
        for wname, w in self.widgets.items():
            if wname.startswith('label'):
                wlabels.add(w)
                w.grid(sticky=tk.W)
            else:
                w.grid(sticky=tk.EW)
        self.pgrid_c(*wlabels,
                     weight=0, uniform='label')

    def setup_defaults(self):
        self.nv.wstate = '5'
        self.gvar('vcombobox').set('invalid')
        self.v_nv.wstate = '7'

    def setup_adefaults(self):
        self.nv.trace(self.v_nv.doValidation, trace_name='__:validation:nv')

    def onValidNV(self, vstate, why):
        assert why is not None, 'Requires `fnSimple`'
        upstream = why.validation()
        if upstream is not True:
            # If there's an error on parsing the value, error out
            return upstream
        else:
            # If the value is valid, compare it with the other widget
            return self.nv.wstate.label != vstate.label


class NB_Complex_Validation(FrameUnlabelled):
    layout = HORIZONTAL

    def setup_widgets(self):
        lim = LimitBounded(5, 7, fn=fn.valNumber)
        self.spinbox = NB_Complex_Validation_Spinbox(self, label=f'Spinbox: {lim}', labelAnchor=CP.N,
                                                     lim=lim,
                                                     styleID='Out')
        self.combobox = NB_Complex_Validation_Combobox(self, label=f'Combobox: {lim}', labelAnchor=CP.N,
                                                       lim=lim)


class NB_Complex_ValidationNew(FrameLabelled):
    label = 'Validation New'
    layout = 'R3,x,x,x,x,x'

    def setup_widgets(self):
        self.lTitle = Label(self, label='Validation New',
                            # styleID: Not 'Valid' on purpose, make sure it's different
                            padding=('0', '5'), expand=True, styleID='Title')
        vsingle = self.varSpec(var.StaticList, StaticList(['1', 'Two', '3'], defaultIndex=0),
                               name='vsingle')
        vsmap = self.varSpec(var.StaticMap, StaticMap({'1': 1, 'Two': 2, '3': 3}, defaultLabel='Two'),
                             name='vmap')
        vlim = self.varSpec(var.Limit, LimitBounded(1, 10, imin=False, default=3, fn=fn.valNumber),
                            name='vlimit')
        vmin = self.varSpec(var.Limit, LimitUnbounded(1, None, default=5, fn=fn.valNumber),
                            name='vmin')

        self.lEntrySingle = Label(self, label='Entry [Single]:', styleID='Valid')
        self.e1 = EntryN(self, vsingle,
                         styleID='Valid')
        self.lComboboxSingle = Label(self, label='Combobox [Single]:', styleID='Valid')
        self.cs1 = ComboboxN(self, vsingle,
                             styleID='Big|Valid').putTooltip()
        self.cs2 = ComboboxN(self, vsingle, readonly=False,
                             styleID='Big|Valid')
        self.lComboboxMap = Label(self, label='Combobox [Map]:', styleID='Valid')
        self.cm1 = ComboboxN(self, vsmap,
                             styleID='Big|Valid').putTooltip()
        self.cm2 = ComboboxN(self, vsmap, readonly=False,
                             styleID='Big|Valid')
        self.lComboboxLimit = Label(self, label='Combobox [Limit]:', styleID='Valid')
        self.cl1 = ComboboxN(self, vlim,
                             styleID='Big|Valid')
        self.cl2 = ComboboxN(self, vlim, readonly=False,
                             styleID='Big|Valid')
        self.lSpinboxLimit = Label(self, label='Spinbox [Limit]:', styleID='Valid')
        self.sl1 = SpinboxN(self, vlim,
                            styleID='Big|Valid')
        self.sl2 = SpinboxN(self, vlim, readonly=False,
                            styleID='Big|Valid')
        self.lSpinboxULimit = Label(self, label='Spinbox [ULimit]:', styleID='Valid')
        self.su1 = SpinboxN(self, vmin,
                            styleID='Big|Valid')
        self.su2 = SpinboxN(self, vmin, readonly=False,
                            styleID='Big|Valid')

    def setup_layout(self, layout):
        self.pgrid(self.lTitle, weight=0)

    def setup_defaults(self):
        self.gvar('vmap').set('2')  # Invalid

    def setup_adefaults(self):
        self.setup_gstate_valid(nowarn=True,
                                childMatch=self.widgets_class(Label))


class NB_Complex_FramePaned(FramePaned):
    layout = HORIZONTAL

    def setup_widgets(self):
        self.left = ListFrame_Inner(self, label='Left Side',
                                    cvariableDefault=False)
        self.right = UpstreamBool(self, what_bool=None, label='Boolean')


class NB_Complex_Canvas(FrameUnlabelled):
    layout = 'R1,x'

    def setup_widgets(self):
        self.cv = Canvas(self, Diagram_SolarSystem(),
                         saveElements=True)
        self.redraw = Button(self, label='Redraw')
        self.redraw_force = Button(self, label='Redraw (Force)')
        self.toggle_state = Button(self, label='Toggle')
        self.debug = Button(self, label='Debug Canvas')

    def setup_layout(self, layout):
        self.pgrid_r(*self.widgets_class(Button),
                     weight=0)

    def setup_adefaults(self):
        self.cv.onClickElement = self.onClickCanvasElement
        self.redraw.onClick = self.cv.trigger_redraw
        self.redraw_force.bindClick(self.cv.redraw, force=True)
        self.toggle_state.onClick = self.cv.genabled_toggle
        self.debug.onClick = self.onDebugCanvas

    def onClickCanvasElement(self, event):
        widget = event.widget
        eselection = widget.eselection()
        logger.debug('Clicked %s @ #%d', widget.exy(event), eselection)
        if widget.hasElements:
            if emarker := widget.itemMarker(eselection):
                logger.debug('| Marker: `%s`', emarker)
            if eelement := widget.item(eselection):
                logger.debug('| Element: %s', eelement)

    def onDebugCanvas(self, event=None):
        logger.debug('Elements:')
        for eid in self.cv.find_all():
            logger.debug('- %s: %s @ %s',
                         eid, self.cv.type(eid),
                         ' '.join(str(xy) for xy in self.cv.itemCoords(eid)))
            ekeys_defaults = defaultdict(list)
            for ekey in self.cv.itemconfigure(eid):
                evalue = self.cv.itemcget(eid, ekey)
                if evalue in ('', '0.0', '0', '0,0'):
                    ekeys_defaults[evalue].append(ekey)
                else:
                    logger.debug('  > %s: %r', ekey, evalue)
            if sum(len(lst) for lst in ekeys_defaults.values()) > 0:
                for evalue, ekeys in ekeys_defaults.items():
                    logger.debug('  >>> %r: %s', evalue, ' '.join(ekeys))


class NB_Complex_Scrolled_InnerLabels(FrameUnlabelled):
    def setup_widgets(self, *, count: int):
        widgets = {}
        for n in range(1, count + 1):
            widgets[f'l:{n}'] = Label(self, label=f'Big Label @ {n}')
        return widgets


class NB_Complex_Scrolled_Inner(FrameUnlabelled):
    layout = 'R1,x,1'

    def setup_widgets(self, *, count: int, ilayout=AUTO):
        self.top = EntryRaw(self, justify=Justification.Center)
        self.lbls = NB_Complex_Scrolled_InnerLabels(self, layout=ilayout,
                                                    count=count)
        self.bot = EntryRaw(self, justify=Justification.Center)

    def setup_layout(self, layout):
        self.pgrid_r(*self.widgets_class(EntryRaw),
                     weight=0)
        for w in self.widgets_class(EntryRaw):
            w.grid(sticky=tk.EW)

    def setup_defaults(self):
        self.wstate = {
            'top': 'Top Entry',
            'bot': 'Bottom Entry',
        }


class NB_Complex_Scrolled(FrameStateful):
    layout = 'R1,2,1,1,2'
    label = 'Scrolled'
    layout_autoadjust = True

    def setup_widgets(self):
        count = random.choice([15 * (2 * n + 4) for n in range(2)])
        count_massive = 5 * count
        assert count_massive % 30 == 0

        self.fh_lbl = Label(self, label='Scrolled: Horizontal (row weight=0)',
                            styleID='Title')
        self.fv_lbl = Label(self, label='Scrolled: Vertical (row weight=1)',
                            styleID='Title')
        self.fb_lbl = Label(self, label='Scrolled: Both (row weight=1)',
                            styleID='Title')
        self._s_h = SeparatorH(self)
        self.fh = Scrolled(self, NB_Complex_Scrolled_Inner, count=count,
                           scrollHorizontal=True,
                           ilayout=HORIZONTAL)
        self.fv = Scrolled(self, NB_Complex_Scrolled_Inner, count=count,
                           scrollVertical=True,
                           ilayout=VERTICAL)
        self.fb = Scrolled(self, NB_Complex_Scrolled_Inner, count=count_massive,
                           scrollHorizontal=True, scrollVertical=True,
                           ilayout='30xE')

    def setup_layout(self, layout):
        self.pgrid_r(*self.widgets_class(Label),
                     weight=0)
        for w in self.widgets_class(Label):
            w.grid(sticky=tk.EW)

    def setup_adefaults(self):
        # Make sure `widgets_except` works properly with proxy widgets
        assert self.fh.wproxy in self.widgets_except(self.fv, self.fb)
        assert self.fh not in self.widgets_except(self.fh)


class NB_Complex_ScrolledAlign(FrameUnlabelled):
    layout = 'R2,2,2,1,1,1'
    layout_autoadjust = True

    def setup_widgets(self):
        align_var = self.varSpec(var.StaticMap,
                                 StaticMap({cp.name: cp for cp in CP if cp in CP_ScrollAnchor},
                                           defaultValue=CP.center),
                                 name='anchor')
        lim_coords = LimitUnbounded('0.0', '1.0', fn=fn.valFloat)
        #
        self.lbl_x = Label(self, label='X')
        self.ex = EntryN(self, lim_coords,
                         styleID='Valid')
        self.lbl_y = Label(self, label='Y')
        self.ey = EntryN(self, lim_coords,
                         styleID='Valid')
        self.lbl_anchor = Label(self, label='Anchor')
        self.canchor = ComboboxN(self, align_var)
        self.btn_action = Button(self, label='Align Inner Frame')
        self.sep_h = SeparatorH(self)
        self.iframe = Scrolled(self, NB_Complex_Scrolled_Inner,
                               count=20 * random.randint(25, 57),  # MASSIVE!
                               scrollHorizontal=True, scrollVertical=True,
                               ilayout='x20E',
                               ).putIgnoreState()

    def setup_layout(self, layout):
        self.pgrid_c(*self.widgets_class(Label),
                     weight=0)
        self.pgrid_r(*self.widgets_except(self.iframe),
                     weight=0)
        for w in self.widgets_class(Label):
            w.grid(sticky=tk.E)
        for w in (self.ex, self.ey, self.canchor, self.btn_action):
            w.grid(sticky=tk.EW)

    def setup_defaults(self):
        self.ex.wstate = self.ey.wstate = '0.5'

    def setup_adefaults(self):
        self.btn_action.onClick = self.onAlignFrame

    def onAlignFrame(self, event=None):
        widget = self.iframe
        rx = self.ex.wstate
        realx = rx.value
        ry = self.ey.wstate
        realy = ry.value
        anchor = self.canchor.wstate
        logger.debug('Align `%s`', widget)
        logger.debug('- XY: %s:%s', realx, realy)
        logger.debug('- Anchor: %s', anchor)
        widget.wproxy.scrollTo(x=realx, y=realy,
                               anchor=anchor.value)


class NB_Complex_ValidationAdvanced(FrameUnlabelled):
    layout = 'R4,2,2,4'

    def setup_widgets(self):
        vtt_a = self.varSpec(var.Limit, LimitUnbounded(Fraction(1, 2), Fraction(5), default='0.75',
                                                       imin=False, fn=fn.valFraction),
                             name='vtt_a')
        vtt_oi = self.varSpec(var.Limit, LimitUnbounded('-10/3', '10/3', default='0',
                                                        fn=fn.valFraction),
                              name='vtt_oi')
        vstep = self.varSpec(var.Limit, LimitBounded(10, 60, step=5, imax=False, fn=fn.valNumber),
                             name='vstep')
        vdynamic = self.varSpec(var.Limit, vstep.container,
                                name='vdynamic')

        self.lDynamic = Label(self, label='Dynamic:\nValid=Labels Valid=True',
                              styleID='Valid')
        self.bDynamic = Button(self, label='Shuffle')
        self.cdynamic_vl = ComboboxN(self, vdynamic, validation=ComboboxN.ValidationLabels,
                                     styleID='Big|Valid')
        self.cdynamic_v = ComboboxN(self, vdynamic, validation=True,
                                    styleID='Big|Valid')
        self.lSimple = Label(self, label=f'Tooltip: always\n{vtt_a.container}',
                             styleID='Valid')
        self.esimple = EntryN(self, vtt_a,
                              validation=VSettings(fn=self.onValid_Simple, fnSimple=False),
                              styleID='Valid')
        self.tsimple = TooltipSimple(self.esimple, tt_position=CP.N)
        self.lTinvalid = Label(self, label=f'Tooltip: var.ValidationLimit\n{vtt_oi.container}',
                               styleID='Valid')
        self.etinvalid = EntryN(self, vtt_oi,
                                validation=var.ValidationLimit,
                                styleID='Valid').putTooltip(tt_position=CP.N)
        self.lStepS = Label(self, label=f'Spinbox\n{vstep.container}',
                            styleID='Valid')
        self.lStepC = Label(self, label=f'ComboboxN\n{vstep.container}',
                            styleID='Valid')
        self.sstep = SpinboxN(self, vstep, readonly=False,
                              styleID='Big|Valid').putTooltip()
        self.cstep = ComboboxN(self, vstep, readonly=True,
                               styleID='Big|Valid').putTooltip()

    def setup_layout(self, layout):
        self.pgrid_c(*self.widgets_class(Label), *self.widgets_class(Button),
                     weight=0)

    def setup_adefaults(self):
        self.bDynamic.onClick = self.onShuffleDynamic
        self.setup_gstate_valid(nowarn=True,
                                childMatch=self.widgets_class(Label))

    def onShuffleDynamic(self):
        all_values = self.gvar('vstep').lall()
        all_count = len(all_values)
        new = random.sample(all_values, k=random.randrange(all_count // 3, 2 * all_count // 3))
        logger.debug('All=%d Choices=%d', all_count, len(new))
        for w in (self.cdynamic_vl, self.cdynamic_v):
            w.change(values=sorted(new), valuesState=w == self.cdynamic_vl)

    def onValid_Simple(self, vstate, why):
        assert why is not None  # Needs fnSimple=False
        wvalidation = self.esimple
        assert wvalidation == why.widget
        wtooltip = self.tsimple
        vspec = wvalidation.variable.container
        vfn = vspec.fn
        vstate_raw = vfn(vstate.label)
        wtooltip.wstate = {
            'mtitle': f'Validation For {wvalidation}',
            'message': dedent(f'''
                VState: {vstate!r} | raw={vstate_raw!r}
                Why: {why!r}
                Variable: {vspec}
                ---
                Trigger TT: {wtooltip}
            '''),
        }
        return vstate.valid


class NB_Complex_EntryMultiline_Frame(FrameStateful):
    wstate_single = 'txt'

    def setup_widgets(self):
        self.txt = EntryMultiline(self,
                                  style=EntryMultiline.Style(
                                      font_base='TkFixedFont',
                                  ),
                                  )

    def setup_layout(self, layout):
        self.txt.grid(sticky=tk.NSEW)


class NB_Complex_EntryMultiline(FrameUnlabelled):
    layout = 'R1,x'
    wstate_single = 'istate'

    def setup_widgets(self):
        self.istate = NB_Complex_EntryMultiline_Frame(self, label='EntryMultiline')
        self.btn = Button(self, label='Current Time')

    def setup_layout(self, layout):
        self.pgrid_r(*self.widgets_class(Button),  # Buttons
                     weight=0)

    def setup_adefaults(self):
        self.btn.onClick = self.changeText

    def changeText(self, event=None):
        self.istate.txt.wstate = '<br />'.join((
            '---',
            f'The current time is <b>{datetime.now().isoformat()}</b>',
            '---',
        ))


class NB_Complex(Notebook):
    def setup_tabs(self):
        return {
            'tree': Notebook.Tab('Tree', TreeExampleFrame(self, label='Complex Tree',
                                                          labelAnchor=CP.N)),
            'lc': Notebook.Tab('ListboxControl', NB_Complex_ListboxSet(self)),
            'cl': Notebook.Tab('CheckboxFrame', NB_Complex_CheckboxList(self)),
            'cn': Notebook.Tab('CheckboxFrame\nNested', NB_Complex_CheckboxNested(self)),
            'rl': Notebook.Tab('RadioFrame', NB_Complex_RadioFrame(self)),
            'scrolled': Notebook.Tab('Scrolled', NB_Complex_Scrolled(self)),
            'scrolled_align': Notebook.Tab('Scrolled Align', NB_Complex_ScrolledAlign(self)),
            'cb_rorw': Notebook.Tab('CB RO/RW', NB_Complex_ChechboxRORW(self)),
            'fpaned': Notebook.Tab('FramePaned', NB_Complex_FramePaned(self)),
            'validation': Notebook.Tab('Validation Old', NB_Complex_Validation(self)),
            'vnew': Notebook.Tab('Validation New', NB_Complex_ValidationNew(self, labelAnchor=CP.N,
                                                                            styleID='Valid')),
            'vadv': Notebook.Tab('Validation\nAdvanced', NB_Complex_ValidationAdvanced(self,
                                                                                       styleID='Valid')),
            'canvas': Notebook.Tab('Canvas', NB_Complex_Canvas(self)),
            'multiline': Notebook.Tab('EntryMultiline\nAdvanced', NB_Complex_EntryMultiline(self)),
        }

    def setup_adefaults(self):
        self.wselect('rl')


class NB(Notebook):
    def setup_tabs(self, c1: Checkbox):
        return {
            'misc': Notebook.Tab('Misc', MiscFrame(self,
                                                   cbox1=c1.variable)),
            'lbs': Notebook.Tab('CheckboxFrame:Legacy', LuftBaloons(self)),
            'sb': Notebook.Tab('Scrollbars', NB_Child_Scrollbars(self)),
            'tt': Notebook.Tab('Timeouts', NB_Child_Timeouts(self),
                               image=self.wimage('info-s16'), labelPosition=CP.E),  # Default labelPosition
            'ti': Notebook.Tab('Interval', NB_Child_Interval(self)),
            'trl': Notebook.Tab('RateLimiter', NB_Child_RateLimiter(self)),
            'td': Notebook.Tab('Dialogues', NB_Child_Dialog(self),
                               image=self.wimage('info-msgbox-s16'), labelPosition=True),  # Only image
            'tc': Notebook.Tab('Tab Complex', NB_Child_Complex(self),
                               image=self.wimage('info-s16'), labelPosition=CP.W),  # "Reverse" labelPosition
            't1': Notebook.Tab('Tab 1', NB_Child_Simple(self, label='Tab 1')),
            't2': Notebook.Tab('Tab 2', NB_Child_Simple(self, label='Tab 2')),
            'c': Notebook.Tab('Complex', NB_Complex(self, styleID='TabV_W')),  # Vertical Tabs (not fully baked)
        }

    def setup_adefaults(self):
        self.wselect('c')


class TextWidget(EntryMultiline):
    styleSheet = {
        '.emph': {
            'overstrike': True,
        }
    }


class LTMLEditor(FrameStateful):
    label = 'LTML'
    layout = 'Rx,1'
    wstate_single = 'txt'

    def setup_widgets(self):
        self.bTxtClean = Button(self, label='Clean TXT')
        self.bTxtReset = Button(self, label='Reset TXT')
        self.bTxtSet = Button(self, label='Set TXT')
        self.txt = ScrolledWidget(self, TextWidget,
                                  setgrid=False)

    def setup_layout(self, layout):
        self.txt.grid(sticky=tk.NSEW)

    def setup_defaults(self):
        self.pgrid_r(*self.widgets_class(Button),  # Buttons
                     weight=0)
        # Setup events
        self.bTxtClean.onClick = self.txt.style_reset
        self.bTxtReset.onClick = self.txt_reset
        self.bTxtSet.onClick = self.txt_set
        self.txt.onClickTag = self.txt_clicked

    def setup_adefaults(self):
        self.txt_set(cnt=20)

    def txt_reset(self, event=None):
        self.txt.wstate = ''

    def txt_set(self, event=None, *, cnt=None):
        texts = []
        if cnt is None:
            cnt = random.choice(range(10, 25))
        for r in range(cnt):
            texts.append(f'<b class="emph">Line</b> <i>{"%02d" % r}</i>/{cnt} ')
            if r % 2 == 0:
                _txt = 'EVEN'
            else:
                _txt = '    '
            texts.append(f'<a>[{_txt}]</a>')
            texts.append('<br/>')
            if r % 5 == 0:
                texts.append('<br/>')
        self.txt.wstate = ''.join(texts)

    def txt_clicked(self, tag, tag_id, tags_other):
        logger.debug('Clicked on %s %s :: %s', tag, tag_id, tags_other)


class TreeExample(Tree):
    def onClickHeader(self, header):
        logger.debug('Clicked on header "%s"', header.name)


class TreeExampleFrame(FrameStateful):
    wstate_single = 'tree'

    def setup_widgets(self):
        self.tree = TreeExample(
            self,
            label=Tree.Column('Label', image=self.wimage('warning-s16')),
            columns={
                'number': Tree.Column('Number',
                                      image=self.wimage('info-s16'),
                                      nameAnchor=CP.W, cellAnchor=CP.E),
            },
            columns_stretch=None,  # For Test: columns_stretch=['number'])
            columns_autosize=None,
            tags={
                'warning': Tree.Row(image=self.wimage('warning-s16')),
                'error': Tree.Row(image=self.wimage('error-s16')),
            },
        )

    def setup_defaults(self):
        logger.debug('Setup arbre state:')
        self.tree.wstate = [
            Tree.Element('First', ['1'], tags=['warning']),
            Tree.Element('Second', ['2'], tags=['warning'], children=[
                Tree.Element('Second.One', ['21'], tags=['error']),
            ]),
            Tree.Element('Third', ['3'], tags=['warning'], children=[
                Tree.Element('Third.One', ['31']),
                Tree.Element('Third.Two', ['32'], tags=['error'], children=[
                    Tree.Element('Third.Two.One', ['321'], image=self.wimage('info-s16')),
                    Tree.Element('Third.Two.Two', ['322'], tags=['warning']),
                    Tree.Element('Third.Two.3', ['323'], tags=['error']),
                ]),
                Tree.Element('Third.Tee', ['33']),
            ]),
            Tree.Element('Tenth', ['10'], tags=['warning']),
        ]


class NB_Center_Entry(FrameUnlabelled):
    layout = 'x2'

    def setup_widgets(self):
        vlist = StaticList(('%d' % n for n in range(10)),
                           defaultIndex=3)

        self.label_ro = Label(self, label='RO: #')
        self.ro = EntryN(self, vlist, readonly=True,
                         styleID='Valid')

        self.label_rw = Label(self, label='RW: #')
        self.rw = EntryN(self, vlist, readonly=False,
                         styleID='Valid')


class NB_Center_Spinbox(FrameUnlabelled):
    layout = 'x2E'

    def setup_widgets(self):
        lim = LimitBounded(1, 5, fn=fn.valNumber, imax=False)

        self.label_spinN = Label(self, label=f'{lim} :: Normal')
        self.spinN = SpinboxN(self, lim)

        self.label_spinL = Label(self, label=f'{lim} :: Wrap Values')
        self.spinL = SpinboxN(self, lim, wrap=True)

        self.label_spinE = Label(self, label=f'{lim} :: Editable')
        self.spinE = SpinboxN(self, lim, readonly=False)

        lim_grow = LimitUnbounded(None, None, fn=fn.valNumber,
                                  infinite=True)

        self.label_spinINF = Label(self, label=f'{lim_grow} :: Unlimited')
        self.spinINF = SpinboxN(self, lim_grow.w(default=0))


class NB_Center_Combobox(FrameUnlabelled):
    layout = 'x2E'
    wstate_single = 'choice'

    def setup_widgets(self):
        vlist = StaticList(('Choice %d' % n for n in range(5)), defaultIndex=3)
        vcb = self.varSpec(var.StaticList, vlist,
                           name='choice')

        self.label_choiceRO = Label(self, label='CB',
                                    image=self.wimage('error-s16'),
                                    labelPosition=CP.S)
        self.choiceRO = ComboboxN(self, vspec=vcb)  # label='CB'

        self.label_choiceRW = Label(self, label='CB [RW]',
                                    image=self.wimage('warning-s16'),
                                    labelPosition=CP.E)
        self.choiceRW = ComboboxN(self, vspec=vcb,
                                  readonly=False)  # label='CB [RW]'

        self.choice_reset = Button(self, label='CB: Set Last', image=self.wimage('info-s16'))

    def setup_adefaults(self):
        self.choice_reset.onClick = self.choiceRO.eSet(self.choiceRO.variable.container[-1])


class NB_Center_Radio(FrameUnlabelled):
    layout = 'x3E'
    wstate_single = 'radio'

    def setup_widgets(self):
        rvar = self.varSpec(var.StaticList,
                            StaticList(('%d' % n for n in range(1, 9 + 1)), defaultIndex=9 // 2),
                            name='radio')

        widgets = {}
        for lbl in rvar.lall():
            widgets[lbl] = Radio(self, label=f'§ {lbl} §',
                                 variable=rvar, value=lbl,
                                 styleID='ShowBG')
        widgets[':lbl'] = Label(self, label='Note the padding\naround the widgets')
        widgets[':button'] = Button(self, label='Check State')
        return widgets

    def setup_layout(self, layout):
        for w in self.widgets_class(Radio):
            w.grid(sticky=tk.NSEW)
        self.pgrid(*self.widgets_class(Radio),
                   uniform='radio')
        self.pad_container(5)

    def setup_adefaults(self):
        self.widgets[':button'].onClick = self.onCheckState

    def onCheckState(self):
        logger.debug('State: %s', self.wstate)
        for wname, w in self.widgets.items():
            if not wname.startswith(':'):
                logger.debug('- %s: %s', w['text'], w.isSelected())


class NB_Center_RadioFrames_Inner(FrameRadio):
    wstate_single = 'inner'

    def setup_widgets(self, n, ro=False, ir=False):
        self.lbl = Label(self, label=f'Inner\nRadio Frame\n{n}')
        self.inner = ListFrame_Inner(self, label=f'{n} (Reversed)' if ir else n,
                                     cstateReadonly=ro,
                                     cstateReversed=ir,
                                     )


class NB_Center_RadioFrames_FL(FrameLabelled):
    layout = 'R1,x,x'

    def setup_widgets(self, rvar):
        lall = rvar.lall()
        widgets = {}
        widgets['toggle'] = Button(self, label='Toggle Inner FrameStateful')
        for lbl in lall:
            widgets[f'r:{lbl}'] = Radio(self, label=f'Frame {lbl}',
                                        variable=rvar, value=lbl)
        for lbl in lall:
            widgets[f'f:{lbl}'] = NB_Center_RadioFrames_Inner(self, label=f'Frame {lbl}',
                                                              rvariable=rvar, rvalue=lbl,
                                                              rstateReversed=False,
                                                              n=lbl, ro=True, ir=False)
        return widgets

    def setup_layout(self, layout):
        toggle = self.widgets['toggle']
        self.pgrid_r(toggle, *self.widgets_class(Radio),
                     weight=0)
        toggle.grid(sticky=tk.EW)
        for w in self.widgets_class(Radio):
            w.layout_padable = False
            w.grid(sticky=tk.W,
                   padx=(SStyle.Size_PadWidget_FrameSeparator, 0))

    def setup_adefaults(self):
        self.widgets['toggle'].onClick = self.onToggle

    def onToggle(self):
        for w in self.widgets_class(NB_Center_RadioFrames_Inner):
            w.inner.cstate_widget.toggle()


class NB_Center_RadioFrames_FS(FrameStateful):
    layout = HORIZONTAL

    def setup_widgets(self, rvar):
        widgets = {}
        for lbl in rvar.lall():
            widgets[f'f:{lbl}'] = NB_Center_RadioFrames_Inner(self, label=f'Frame {lbl} (Reversed)',
                                                              rvariable=rvar, rvalue=lbl,
                                                              rstateReversed=True,
                                                              n=lbl, ir=True)
        return widgets


class NB_Center_RadioFrames(FrameUnlabelled):
    layout = 'x2E'

    def setup_widgets(self):
        srvar = self.varSpec(var.StaticList,
                             StaticList(('LeftSide', 'RightSide'), defaultIndex=0),
                             name='frame:s')
        lrvar = self.varSpec(var.StaticList,
                             StaticList(('LeftSide', 'RightSide'), defaultIndex=0),
                             name='frame:l')

        widgets = {}
        for lbl in srvar.lall():
            widgets[f'r:{lbl}'] = Radio(self, label=f'Radio Stateful: {lbl}',
                                        variable=srvar, value=lbl)
        widgets['fs'] = NB_Center_RadioFrames_FS(self, label='Stateful', rvar=srvar)
        widgets['fl'] = NB_Center_RadioFrames_FL(self, label='Labelled', rvar=lrvar)
        return widgets

    def setup_defaults(self):
        self.pgrid_r(*self.widgets_class(Radio),
                     weight=0)


class NB_Center_LabelAlignSL(FrameUnlabelled):
    layout = '3x5E'

    def setup_widgets(self):
        widgets = {}
        justifies = [None, *Justification]
        for justify in justifies:
            wkey = [
                'xpand',
                'justify' if justify is None else justify.name,
            ]
            widgets['_'.join(wkey)] = Label(self, label=' '.join(wkey), styleID='ShowBG|WarnFG',
                                            image=self.wimage('warning-s16'), labelPosition=CP.S,
                                            justify=justify)
        for expand in [True, False]:
            for justify in justifies:
                wkey = [
                    'X' if expand else 'x',
                    'justify' if justify is None else justify.name,
                ]
                widgets['_'.join(wkey)] = Label(self, label=' '.join(wkey), styleID='ShowBG',
                                                image=self.wimage('info-s16'), labelPosition=CP.S,
                                                justify=justify, expand=expand)
        return widgets

    def setup_layout(self, layout):
        self.pad_container(2)


class NB_Center_LabelAlignML(FrameUnlabelled):
    layout = '4x6S'

    def setup_widgets(self):
        widgets = {}
        for anchor in [None, CP.N, CP.S, CP.E, CP.W, CP.center]:
            for justify in [None, Justification.Left, Justification.Center, Justification.Right]:
                wkey = [
                    'anchor' if anchor is None else anchor.name,
                    'justify' if justify is None else justify.name,
                ]
                widgets['_'.join(wkey)] = Label(self, label='\n'.join(wkey), styleID='ShowBG',
                                                anchor=anchor, justify=justify)
        return widgets

    def setup_layout(self, layout):
        self.pad_container(2)


class NB_Center_EventLoop(FrameUnlabelled):
    layout = 'Cx,1'
    layout_autoadjust = True
    ignoreContainerState = True

    def setup_widgets(self):
        # Control
        self.eSize = EntryRaw(self, justify=Justification.Center,
                              readonly=True,
                              )
        self.sBgSleep = Checkbox(self, label='[BG-Q]', readonly=True)
        self.eBgControl = Button(self, label='[BG-Q]: Control')
        # Actions
        self.eMainLog = Button(self, label='[M]: Log')
        self.eMainLogT = Button(self, label='[M]: Log Threads')
        self._s1 = SeparatorH(self)
        self.eBgNothing = Button(self, label='[BG-Q]: Nothingness')
        self.eBgSleep = Button(self, label='[BG-Q]: Sleep')
        self.eBgSleepState = Checkbox(self, label='[BG-Q]: Sleep State')
        self._s2 = SeparatorH(self)
        self.eBgNoBusInterval = Checkbox(self, label='[BG-NoBus]:\nSend Events')
        # Log
        # - Ignore State, avoid spamming the state change
        self.wlog = ScrolledWidget(self, EntryMultiline)

    def setup_layout(self, layout):
        for w in self.widgets_class(Button):
            w.grid(sticky=tk.EW)
        self.pgrid_r(self.eSize, self.sBgSleep,
                     weight=0)
        self.pgrid_c(*self.widgets_class(Button),
                     weight=0, uniform='Button')

    def setup_defaults(self):
        self.eBgSleepState.wstate = True
        self.wroot.register_eventbus_response(self.onELRes, eventloop='sleep')

    def setup_adefaults(self):
        self.eBgControl.onClick = self.actionControl
        self.eMainLog.onClick = self.actionLogThread
        self.eMainLogT.onClick = self.actionLogThreads
        self.eBgNothing.onClick = self.actionNothing
        self.eBgSleep.onClick = self.actionSleep
        self.eBgSleepState.trace(self.actionSleepState,
                                 trace_initial=True)
        self.eBgNoBusInterval.trace(self.wroot._interval_nobus.doState_Trace)
        self.onUpdateState()

    def onUpdateState(self):
        el = self.wroot.eL['sleep']
        qtyUnprocessedTasks = el.cntRequests()
        isRunning = el.is_running()
        isPaused = el.is_paused()
        self.sBgSleep.wstate = isRunning
        # Queue Size
        w_size = self.eSize
        if isRunning:
            str_state = f'Q = {qtyUnprocessedTasks}E'
        elif isPaused:
            str_state = f'PAUSED: {qtyUnprocessedTasks}E'
        else:
            str_state = 'STOPPED'
        w_size.wstate = str_state
        # Control
        w_control = self.eBgControl
        if isRunning:
            str_control = 'Stop'
        else:
            str_control = 'Start'
        w_control.change(label=f'[BG-Q]: {str_control}')
        w_control.genabled(True)

    def onELRes(self, eventloop, ridx, response, *, ustate=True):
        if ridx is None:
            txt = 'Status: %s' % response  # Status events
        elif isinstance(response, ELRes_Log):
            txt = response.ltml
        elif isinstance(response, ELRes_Error):
            # Example: Show a more important error
            # tkmilan.tk.messagebox.showerror(
            #     title='Error on BG',
            #     message=response.string,
            # )
            txt = f'<b>ERROR</b>: {response.string}'
        else:
            # TODO: Exit with error?
            txt = f'<b>Unsupported</b>: {ridx} / {response}'
        if txt is not None:
            if ridx is None:
                self.log(f'T[{eventloop.tName}]] | {txt}')
            else:
                self.log(f'T[{eventloop.tName}]<i>#{"%03d" % ridx}</i>] | {txt}')
        if ustate:
            assert eventloop == self.wroot.eL['sleep']
            self.onUpdateState()

    def actionControl(self, event=None):
        el = self.wroot.eL['sleep']
        widget = self.eBgControl
        if el.toggle() is None:
            str_control = 'Stopping...'
        else:
            str_control = 'Starting...'
        widget.change(label=f'[BG-Q]: {str_control}')
        widget.genabled(False)

    def actionNothing(self, event=None):
        self.log('Requesting BG to do nothing')
        self.wroot.eventloop_queue('sleep', ELReq_Nothing)
        self.onUpdateState()

    def actionSleep(self, event=None):
        duration = random.randint(2, 4)
        self.log(f'Requesting BG to sleep for {duration}s')
        self.wroot.eventloop_queue('sleep', ELReq_Sleep(duration))
        self.onUpdateState()

    def actionSleepState(self, var, etype):
        assert etype in ('write', None)
        self.wroot.eventloop_queue('sleep', ELReq_SleepState(var.get()))

    def actionLogThread(self, event=None):
        cthread = threading.current_thread()
        self.log(f'Current Thread: {cthread.name}[<i>{cthread.ident}</i>]')

    def actionLogThreads(self, event=None):
        self.log('<b>Active Threads</b>:')
        for tobj in threading.enumerate():
            self.log(f'- {tobj.name}[<i>{tobj.ident}</i>]')

    def log(self, ltml: str):
        current = self.wlog.wstate
        if current != '':
            # Don't include a line break on the first line
            current += '<br/>'
        current += f'<i>{datetime.now().isoformat()}</i>| {ltml}'
        self.wlog.wstate = current
        self.wlog.wproxy.scrollTo(y=1.0)  # Scroll to bottom


class NB_Center_SWin_Popup(SecondaryWindow):
    layout = 'R1,1,x'
    label = 'Secondary Window'

    def setup_widgets(self):
        self.lbl = Label(self, label='@ Popup')
        self.btn = Button(self, label='Info')
        self.stateB1 = Checkbox(self, label='B1')
        self.stateE = EntryRaw(self)
        self.stateB2 = Checkbox(self, label='B2')

    def setup_adefaults(self):
        self.btn.onClick = self.onInfo

    def onInfo(self, event=None):
        logger.debug('=> Widget')
        for line in pformat(self.wstate).splitlines():
            logger.debug('| %s', line)
        logger.debug('=> GUI')
        for line in pformat(self.gstate).splitlines():
            logger.debug('| %s', line)


class NB_Center_SWin_Selection__Buttons(FrameUnlabelled):
    layout = HORIZONTAL

    def setup_widgets(self, NAMES):
        widgets = {}
        for nidx, nstr in NAMES.items():
            widgets['b:%d' % nidx] = Button(self, label=nstr)
        return widgets

    def setup_layout(self, layout):
        self.pgrid_c(*self.widgets_class(Button),
                     weight=0, uniform='Button')
        for w in self.widgets_class(Button):
            w.grid(sticky=tk.EW)


class NB_Center_SWin_Selection(SecondaryWindow):
    NAMES = {n: f'N{n}' for n in range(10)}
    layout = 'R%s,1' % ','.join(['2'] * len(NAMES))
    label = 'Select one of %d names' % len(NAMES)
    wstate_single = 'n'

    def setup_widgets(self):
        # Variables
        DEFAULT_VALUE = -1
        self.var(var.Int, value=DEFAULT_VALUE,
                 name='n')
        assert DEFAULT_VALUE not in self.__class__.NAMES
        # Widgets
        widgets = {}
        for nidx, nstr in self.__class__.NAMES.items():
            widgets['e:%d' % nidx] = EntryRaw(self, readonly=True,
                                              width=4, justify=Justification.Center,
                                              )
            widgets['l:%d' % nidx] = Label(self, label=f'Number #{nidx} = {nstr}')
        # - Ignore all widget states
        widgets['btns'] = NB_Center_SWin_Selection__Buttons(self, NAMES=self.__class__.NAMES)
        fn.state_ignore(*widgets.values())
        return widgets

    def setup_layout(self, layout):
        self.pgrid_c(*self.widgets_class(EntryRaw),
                     weight=0)

    def setup_defaults(self):
        for nidx in self.__class__.NAMES:
            we = self.widgets['e:%d' % nidx]
            we.wstate = '#%d' % nidx

    def setup_adefaults(self):
        for nidx in self.__class__.NAMES:
            wbtn = self.widgets['btns'].widgets['b:%d' % nidx]
            fn_select = self.generateClick(nidx)
            # Select on Buttons
            wbtn.onClick = fn_select
            if 0 < nidx < 10:  # Select with a single keyboard click
                self.binding('%d' % nidx, fn_select)

    def generateClick(self, idx: int):
        nvar = self.gvar('n')

        def onClick(event=None):
            logger.debug('Chose Index #%d', idx)
            nvar.set(idx)
            self.unschedule()
        return onClick


class NB_Center_SWin(FrameStateful):
    layout = 'C2,2,1'

    def __init__(self, *args, **kwargs):
        kwargs.update({
            'label': 'Manipulate State for SecondaryWindow objects',
            'labelAnchor': CP.N,
        })
        super().__init__(*args, **kwargs)

    def setup_widgets(self):
        self.winNormal = NB_Center_SWin_Popup(self, modal=False)
        self.normalS = Button(self, label='Schedule Normal')
        self.normalU = Button(self, label='Unschedule Normal')
        self.winModal = NB_Center_SWin_Popup(self, modal=True)
        self.modalS = Button(self, label='Schedule Modal')
        self.modalU = Button(self, label='Unschedule Modal')
        self.winModalSel = NB_Center_SWin_Selection(self)
        self.modalselT = Button(self, label='Select #')

    def setup_adefaults(self):
        self.normalS.onClick = self.winNormal.schedule
        self.normalU.onClick = self.winNormal.unschedule
        self.modalS.onClick = self.winModal.schedule
        self.modalU.onClick = self.winModal.unschedule
        self.modalselT.onClick = self.winModalSel.toggle
        BindingGlobal(self, '<Control-g>', self.winModalSel.toggle,
                      immediate=True, description='Popup Selection #')


class NB_Center_Tooltip_Label(FrameStateful):
    wstate_single = True
    wstate_single_wstate = True

    def setup_widgets(self):
        self.ltt = Label(self, label='This label has a tooltip')
        self.ltt_missing = Label(self, label='This is Hidden').putIgnoreLayout()


class NB_Center_Tooltip_Comboboxen(FrameStateful):
    layout = VERTICAL

    def setup_widgets(self):
        cb_settings = StaticMap({f'Number #{n}': n for n in range(10)},
                                defaultValue=6)
        widgets = {}
        for n in range(7):
            wdelay = None if n < 1 else n * 210
            wmsg = f'Tooltip Delay: {wdelay}{"" if wdelay is None else " ms"}'
            widgets[f'c:{n}'] = ComboboxN(self, cb_settings,
                                          validation=VSettings(fn=self.onValid_CB,
                                                               fnSimple=False, ttSimple=False),
                                          ).putTooltip(TooltipSingleStatic, tt_message=wmsg,
                                                       tt_position=random.choice((CP.N, CP.S)),
                                                       tt_delay=wdelay,
                                                       )
        return widgets

    def onValid_CB(self, vstate, why):
        assert why is not None
        assert why.tt is not None
        why.tt.enable()
        return vstate.valid


class NB_Center_Tooltip__Buttons(FrameUnlabelled):
    layout = HORIZONTAL

    def setup_widgets(self):
        self.btnToggleLabel = Button(self, label='Toggle Label State')
        self.btnToggle = Button(self, label='Toggle Tooltip')

    def setup_layout(self, layout):
        for w in self.widgets_class(Button):
            w.grid(sticky=tk.EW)


class NB_Center_Tooltip(FrameUnlabelled):
    layout = 'C2,1'

    def setup_widgets(self):
        self.txt = NB_Center_Tooltip_Label(self, label='Label')
        self.txt_ltt_tt = TooltipSimple(self.txt.ltt,
                                        tt_position=CP.S)
        self.buttons = NB_Center_Tooltip__Buttons(self)
        self.combo = NB_Center_Tooltip_Comboboxen(self, label='Combobox (with delays)')

    def setup_layout(self, layout):
        self.pgrid_r(self.buttons,
                     weight=0)

    def setup_adefaults(self):
        self.buttons.btnToggleLabel.bindClick(self.txt.toggle)
        self.buttons.btnToggle.bindClick(self.txt_ltt_tt.toggle)


class NB_Center(Notebook):
    def setup_tabs(self):
        return {
            'cb': Notebook.Tab('Combobox', NB_Center_Combobox(self)),
            'spin': Notebook.Tab('Spinbox', NB_Center_Spinbox(self)),
            'entry': Notebook.Tab('EntryN', NB_Center_Entry(self)),
            'label_align:sl': Notebook.Tab('Label Align:SL', NB_Center_LabelAlignSL(self)),
            'label_align:ml': Notebook.Tab('Label Align:ML', NB_Center_LabelAlignML(self)),
            'radio': Notebook.Tab('Radio', NB_Center_Radio(self)),
            'frame:radio': Notebook.Tab('FrameRadio', NB_Center_RadioFrames(self)),
            'ltml': Notebook.Tab('LTML', LTMLEditor(self)),
            'el': Notebook.Tab('Event Loop', NB_Center_EventLoop(self)),
            'swin': Notebook.Tab('Secondary Windows', NB_Center_SWin(self)),
            'tooltip': Notebook.Tab('Tooltips', NB_Center_Tooltip(self)),
        }

    def setup_adefaults(self):
        self.wselect('frame:radio')


class RW(RootWindow):
    layout = 'Rx,1,1,1'
    # "TNotebook.tabplacement" is undocumented and buggy, should start with the "opposite" of "tabposition"
    # - See https://stackoverflow.com/a/76007959/12287472
    styleIDs = {
        'TabCenterTop.TNotebook': {'tabposition': tk.N},
        'TabCenterBottom.TNotebook': {'tabposition': tk.S},
        'TabLarge.TNotebook': {}, 'TabLarge.TNotebook.Tab': {'padding': (20, 5)},
        'TabV_W.TNotebook': {'tabposition': tk.W + tk.N, 'tabplacement': tk.N + tk.EW},
        'ReadonlyEmphasis.TCheckbutton': {},
        'ShowBG.TLabel': {'background': DStyle.Color_BG_Selected},
        'ShowBG.TRadiobutton': {'background': DStyle.Color_BG_Selected},
        'WarnFG.TLabel': {'foreground': 'orange'},
        'FakeDisabled.TLabel': {'foreground': DStyle.Color_FG_Disabled},
        'FontTTY.Treeview': {'font': 'TkFixedFont'},
        'Title.TLabel': {
            'font': 'TkHeadingFont',
            'background': 'darkblue', 'foreground': 'white',
        },
        'Small.TButton': {
            'font': SStyle.Font_Button_Small,
            'padding': SStyle.Size_PadButton_Small,
        },
        'Big.TSpinbox': {
            'arrowsize': '20',
        },
        'Big.TCombobox': {
            'arrowsize': '20',
        },
        'Out.TLabelframe': {'labeloutside': True},
        # Valid
        **{
            f'Valid.{sid}': {
                'arrowcolor': 'blue',
            }
            for sid in ('TSpinbox', 'TCombobox', 'TSpinbox')
        },
        'Valid.TEntry': {
            'foreground': 'blue',
        },
        **{
            f'Valid.{sid}': {
                'background': 'darkblue',
            }
            for sid in ('TFrame', 'TLabelframe', 'TLabelframe.Label', 'TLabel', 'TCheckbutton')
        },
    }
    layout_autoadjust = True

    def setup_widgets(self):
        vc = self.var(var.Boolean, name='bool', value=True)

        # Special
        self.b2 = Button(self, label='Debug').putAuto()
        # Row
        self.b1 = Button(self, label='B1')
        self.c1 = Checkbox(self, label='Checkbox1')
        self._s1 = SeparatorV(self)
        self.bE1 = Button(self, label='Set "example"')
        self.e1 = EntryRaw(self, expand=True)  # label='Entry1'
        self._s2 = SeparatorV(self)
        self.c2ro = Checkbox(self, label='RO "bool"', readonly=True, variable=vc)
        self.c2rw = Checkbox(self, label='RW "bool"', readonly=False, variable=vc)
        self.ubox = UpstreamBool(self, label='Upstream', labelAnchor=CP.S,
                                 what_bool=vc)
        self._sr = SeparatorH(self, pad=False)
        # Others

        self.nb_center = NB_Center(self)
        self.nb = NB(self, c1=self.c1)

    def setup_layout(self, layout):
        # Validate Implementation
        assert set(self.widgets_class(mixin.MixinWidget)) == set(self.widgets.values())
        assert set(self.widgets_except()) == set(self.widgets.values())
        # Actual Layout Changes
        self.pgrid_r(self.ubox,
                     weight=0)
        self.b2.place(anchor=CP.NW.value, relx=0, rely=0,
                      x=5, y=5)

    def setup_defaults(self):
        self._interval_nobus = Interval(self, self.onQueueEventsNoBus, 750, immediate=False)
        self.register_eventbus_response(log_eventloops, event=bool)

    def setup_eventloops(self):
        return {
            'no-bus': bg.EventLoop(name='no-bus'),
            'sleep': EL_Sleep(wcallback=self.use_eventbus,
                              example_kwarg='Some String'),
        }

    def setup_adefaults(self):
        self._state_default = self.wstate  # Save the default state
        logger.debug('Setup events')
        self.b1.onClick = self.c1.toggle
        self.bE1.onClick = self.ask_contents
        self.b2.onClick = self.debug
        logger.debug('Setup bindings')
        BindingGlobal(self, '<F4>', self.debug,
                      immediate=True, description='Debug')
        if __debug__:
            BindingGlobal(self, '<Shift-Button-2>', fn.onDebugWidget,
                          immediate=True, description='Debug GUI for Current Widget')
            BindingGlobal(self, '<Control-Shift-Button-2>', fn.onDebugPWidget,
                          immediate=True, description='Debug GUI on Parent Widget')
            # This is only for "debuggier" debug sessions.
            # BindingGlobal(self, '<Button-3>', self.debugEvent,
            #               immediate=True, description='Debug Events')
        logger.debug('Setup traces')
        self.tracev('bool', self.onTraceBool, trace_initial=True)
        self.trace(self.onTraceRoot)
        logger.debug('Setup EventLoop')
        self.start_eventloops(bus=False)
        for _, el in self.get_eventloops(bus=False):
            el.setup_process_respond(ELRes_Nothing)
            # Process Events every second
            Interval(self, lambda: self.onProcessEventsEL(el), 1000, immediate=True)

        logger.debug('Global Bindings:')
        for bname, B in self._bindings_global.items():
            logger.debug('- %s: %s%s', bname, '' if B else '[Disabled] ', B.description)

        for twhat in ('TSpinbox', 'TCombobox'):
            self.style.map(f'Big|Valid.{twhat}',
                           arrowcolor=[
                               (('readonly', '!invalid'), '#5CC936'),
                               (('readonly', 'invalid'), '#EF1023'),
                               (('!readonly', '!invalid'), '#7DD45E'),
                               (('!readonly', 'invalid'), '#F2404F'),
                           ])  # noqa: E126
        self.style.map('Valid.TEntry',
                       foreground=[
                           ('!invalid', '#0BAC91'),
                           ('invalid', '#AC0B27'),
                       ])
        for twhat in ('TFrame', 'TLabelframe', 'TLabelframe.Label', 'TLabel', 'TCheckbutton'):
            self.style.map(f'Valid.{twhat}',
                           background=[
                               ('!invalid', 'lightgreen'),
                               ('invalid', 'pink'),
                           ])  # noqa: E126

    def onQueueEventsNoBus(self, event=None):
        task = ELReq_Nothing()
        for _, el in self.get_eventloops(bus=False):
            el.queue(task)

    def onProcessEventsEL(self, eventloop: bg.EventLoop):
        for ridx, response in eventloop.responses(chunk=10):
            log_eventloops(eventloop, ridx, response)

    def ask_contents(self):
        string = tk.simpledialog.askstring('Set Contents', f'Set the "{self.e1.label}" contents')
        if string is not None:
            self.e1.wstate = string

    def debug(self, event=None):
        logger.info('=> State @ %s[%r]', self, self)
        for line in pformat(self.wstate_get()).splitlines():  # No `.wstate` for better tracebacks
            logger.info('%s', line)
        # logger.info('=> State @ ubox')
        # for line in pformat(self.ubox.wstate).splitlines():
        #     logger.info('%s', line)
        # logger.info('=> State @ nb[c:lc]')
        # for line in pformat(self.nb.wtab('c:lc').wstate).splitlines():
        #     logger.info('%s', line)
        logger.info('=> State Set')
        new = self.wstate
        for b in ('0', '12'):
            new['nb']['lbs'][f'lb:{b}'] = not new['nb']['lbs'][f'lb:{b}']
        assert 'lb:1' not in new['nb']['lbs']  # Ignore the second checkbox
        self.wstate = new
        logger.info('=> GUI States')
        logger.info('   GUI State @ %s[%r]', self, self)
        # for line in pformat(self.gstate).splitlines():
        #     logger.debug('| %s', line)
        assert hasattr(self, '_state_default')
        # Compare with itself
        logger.debug('   Valid?: %s', self.wstate == new)
        # Compare with the default state
        logger.debug('   Default?: %s', self.wstate == self._state_default)
        logger.info('=> GridSize')
        logger.debug('  %s', self.gsize)
        if event is not None:
            self.debugEvent(event)

    def debugEvent(self, event=None):
        logger.debug('E: %s', event)
        if __debug__:
            logger.debug(' > Mods: %s [%s]', hex(event.state), ' '.join(m.name for m in EventModifier.ALL(event)))
        widget = event.widget
        if isinstance(widget, Tree):
            logger.debug(' | @ %s| %r',
                         widget.identify_region(event.x, event.y),
                         widget.identify_row(event.y))
            logger.debug(' | s %s', widget.wsid())

    def onTraceRoot(self, var, etype):
        logger.info('Changed Container "%s" = %s @ %s',
                    var.cwidget,
                    var.get(),
                    datetime.now().isoformat(' ', timespec='microseconds'),
                    )

    def onTraceBool(self, var, etype):
        bool_state = var.get()
        bool_when = 'Initial' if etype is None else 'Trigger'
        logger.debug('Variable "%s" @ %s: %s', fn.vname(var), bool_when, bool_state)


def main(PROJECT_NAME, PROJECT_VERSION,
         ):
    '''
    Main entrypoint to be configured
    '''
    # ./showcase-images
    default_images = Path(__file__).parent / 'showcase-images'

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=dedent('''
        Showcase for tkmilan module
        '''),
        epilog=f'Version {PROJECT_VERSION}',
    )
    # Automatic Tab Completion
    # - Mark certain arguments with:
    #   - `parser.add_argument(...).complete = shtab.FILE`: Complete file names
    #   - `parser.add_argument(...).complete = shtab.DIRECTORY`: Complete directory names
    shtab.add_argument_to(parser, '--generate-shtab-completion', help=argparse.SUPPRESS)

    parser.add_argument('--version', action='version', version=PROJECT_VERSION)
    parser.add_argument('-v', '--verbose', dest='loglevel',
                        action='store_const', const=logging.DEBUG, default=logging.INFO,
                        help='Add more details to the standard error log')
    parser.add_argument('--debug', action='store_true',
                        help=argparse.SUPPRESS)
    parser.add_argument('--images', type=Path, default=default_images,
                        help='Image Folder to Load. Defaults to %(default)s').complete = shtab.DIRECTORY
    parser.add_argument('--no-images', action='store_const',
                        dest='images', const=None,
                        help='Do not load any images')

    args = parser.parse_args()

    # Logs
    logs_fmt = '%(levelname)-5.5s %(name)s@%(funcName)s| %(message)s'
    try:
        import coloredlogs  # type: ignore[import-untyped]
        coloredlogs.install(level=args.loglevel, fmt=logs_fmt)
    except ImportError:
        logging.basicConfig(level=args.loglevel, format=logs_fmt)
    logging.captureWarnings(True)
    # # Silence spammy modules, even in verbose mode
    if not args.debug and args.loglevel == logging.DEBUG:
        for log in LOGGING_VERBOSE():
            log.setLevel(logging.INFO)

    # Widget Tester / Showcase
    # - Request full feature range for themes
    # - Request no automatic inner padding
    r = RW(imgfolder=args.images,
           theme_simple=False,
           rpad=None)
    logger.debug('Screen Size: %r', r.size_screen)
    logger.debug('         /2: %r', r.size_screen.reduce(2))
    r.mainloop()

    return 0


# Release Process
def entrypoint():
    '''
    Entrypoint for executable
    '''
    from . import __version__
    return main(
        PROJECT_NAME=__package__,
        PROJECT_VERSION=__version__,
    )


if __name__ == "__main__":
    import sys
    sys.exit(entrypoint())
