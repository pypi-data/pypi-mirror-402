'''Model the background Event Loop processing.

.. role:: code-python(code)
    :language: python
'''
import typing
import logging
from dataclasses import dataclass, field as dc_field
from datetime import datetime
import time
from itertools import count as iter_count

import threading
from queue import Queue, PriorityQueue, Empty
if typing.TYPE_CHECKING:
    import tkinter as tk

from . import exception

logger = logging.getLogger(__name__)


callbackT = typing.Callable[['EventLoop', typing.Optional[int], typing.Union['ELRes', bool]], typing.Any]
prioritymapT = typing.Mapping[typing.Type['ELReq'], int]


NORMAL_PRIORITY: int = 0
'''Normal priority for Event Loop Requests.

See Also:
    See `ELReq_Priority` and `EventLoop.queue` for usage.
'''


@dataclass
class ELCallback:
    '''Event Loop Callback definition.

    Args:
        widget: Widget to attach the ``callback`` to
        callback: Function to call with the `response <ELRes>`.
        idle: Choose ``after_idle`` over ``after``. Defaults to `True`.
            See ``Tcl`` :tcl:`after <after.htm#M6>` and :tcl:`after idle
            <after.htm#M9>` documentation.
        afterMS: If ``idle`` is `False`, delay execution.
            See ``Tcl`` :tcl:`after <after.htm#M6>` documentation.
    '''
    widget: 'typing.Union[tk.Widget, tk.Tk]'
    callback: callbackT
    idle: bool = True
    afterMS: int = 0

    if __debug__:
        def __post_init__(self):
            import tkinter as tk
            assert isinstance(self.widget, (tk.Widget, tk.Tk))
            assert callable(self.callback)
            if not self.idle:
                assert self.afterMS >= 0, f'Invalid afterMS config: {self.afterMS}'

    def trigger(self,
                eventloop: 'EventLoop',
                ridx: typing.Optional[int],
                response: 'typing.Union[ELRes, bool]',
                ) -> str:
        '''Trigger the callback using the given response.

        See `EventLoop` for the kinds of responses produced.

        Args:
            eventloop: The corresponding `EventLoop` object.
            ridx: The response index, or `None` for signals.
                See also `EventLoop`.
            response: The response payload. For signals, this is a `bool`
                indicating if the `EventLoop` is starting or stopping.
                See also `EventLoop`.

        Returns:
            Return the ``after``/``after idle`` ID.
        '''
        if self.idle:
            return self.widget.after_idle(self.callback, eventloop, ridx, response)
        else:
            return self.widget.after(self.afterMS, self.callback, eventloop, ridx, response)


@dataclass(frozen=True)
class ELReq:
    '''Event Loop Request.

    Usually represents a task to be performed on an `EventLoop`.

    See `EventLoop` to see how to use this.
    '''
    pass


# TODO: On Python 3.10:: Integrate on ELReq, as KW_ONLY
@dataclass(frozen=True, order=True)
class ELReq_Priority:
    '''Event Loop Request, with priority.

    This is the actual object which is included on the `EventLoop` input queue.
    Wraps the `ELReq` object ignoring the ordering, so that it can be included
    on the `PriorityQueue <queue.PriorityQueue>` considering only the
    ``priority``, and ``count`` to maintain the original ordering.

    Args:
        request: The Event Loop request object.
        priority: The request priority.
            Optional, see `NORMAL_PRIORITY` for the default value.
        count: The request count, used to maintain the order when these objects
            are pushed to a `PriorityQueue <queue.PriorityQueue>`.

            See the Python `PriorityQueue implementation notes
            <https://docs.python.org/3.8/library/heapq.html#priority-queue-implementation-notes>`__.
            documentation. The default value does The Right Thing.

    See Also:
        This is to be used on a `PriorityQueue <queue.PriorityQueue>`, see the
        Python documentation.
    '''
    request: ELReq = dc_field(compare=False)
    priority: int = NORMAL_PRIORITY
    count: int = dc_field(default_factory=iter_count().__next__)


@dataclass(frozen=True)
class ELRes:
    '''Event Loop Response.

    See `EventLoop` to see how to use this.

    .. note::

        If using an Event Bus, this should use a single subclass level, that is
        this should only be subclassed once, and those subclasses should not be
        subclassed further. See `RootWindow.register_eventbus_response` for
        more information.
    '''
    pass


class EventLoop:
    '''Event Loop Object

    Represent all Event Loop settings and necessary references.

    An event loop is basically a big :code-python:`while True:` loop. The tasks
    to process are `ELReq_Priority` (`ELReq` with priority) objects, and that
    processing produces a stream of responses.

    There are two kinds of responses:

    - A "signal", index is `None`, payload is `bool`.
        This signals the Event Loop started or stopped task processing.
    - A "response", index is `int`, payload is `ELRes`.
        The index indicates the count of the current processing task.

    Internally uses the :py:mod:`threading` functions. This means the threading
    model is cooperative, that is, the task processing functions must yield
    their time, not hog the processing time for themselves.

    The event loop itself is single-threaded, meaning there's only at most a
    single task is being executed. The input queue is a `PriorityQueue
    <queue.PriorityQueue>`, which means the request order is not fixed, there
    are only defaults. The requests are processed in priority order (lowest
    first).

    You can choose between two different response parsing behaviours, depending
    on the arguments you give:

    - ``qoutput``: Define the response output as a queue, possibly given from outside.
    - ``wcallback``: Define some a ``Tk`` callback function to be called.
        Even though ``Tk`` is not thread-safe, some specific functions are, and
        this is used to "merge" the event process loop with the existing ``Tk``
        event loop. See `ELCallback` for more information on how those
        functions are defined.

    Note that ``qoutput`` is the default, when you do not choose one or the
    other.

    Avoid using `time.sleep` directly when implementing the tasks. Use
    `isleep`/`usleep` for precise control over interruptible behaviour.

    Args:
        qinput: `PriorityQueue <queue.PriorityQueue>` with `ELReq_Priority` to
            consume.
            Optional, creates a new queue when not given.
        qoutput: `Queue <queue.Queue>` with `ELRes` to produce.
            Optional, creates a new queue when not given.
            See above for the interaction with ``wcallback``.
        wcallback: `Callback Configuration <ELCallback>` object.
            Optional.
            See above for the interaction with ``qoutput``.
        name: The Event Loop thread name.
            Optional, overrides `name` if given.
            See `tName` for the final name.
        priorities: Define Event Loop request default priorities.
            Optional, overrides `priorities` if given.

    All other keyword arguments are passed to the `setup_eventloop` function.

    .. note::
        This object should be created on the Main Thread, not from any
        sub-thread.
        This is enforced on debug mode.

    .. note::
        In case ``qoutput`` is chosen, the main ``Tk`` processing loop for
        `responses <ELRes>` must implement something like this, using an `Interval
        <tkmilan.model.Interval>`:

        .. code:: python

            import tkmilan
            from tkmilan.model import Interval

            class EventLoop(tkmilan.bg.EventLoop):
                # Implement

            class RW(tkmilan.RootWindow):
                def setup_eventloops(self):
                    return {'sleep': EventLoop(name='sleep')}

                def setup_adefaults(self):
                    self.start_eventloops()
                    for _, el in self.get_eventloops(bus=False):
                        logger.debug('# EventLoop tName=%s', eventloop.tName)
                        # Process Events every second
                        Interval(self, lambda: self.onProcessEventsEL(el), 1000, immediate=True)

                def onProcessEventsEL(self, eventloop: bg.EventLoop):
                    for ridx, response in eventloop.responses(chunk=10):  # Or other amounts
                        if ridx is None:
                            logger.debug('eventloop=%s   Signal: %s', eventloop.tName, response)
                        else:
                            logger.debug('eventloop=%s Response: %r', eventloop.tName, response)
    '''
    name: typing.Optional[str] = None
    '''Thread Name, for all instances in the class.

    This is the per-class setting, can be overriden. See `tName` for the
    per-instance name.
    '''
    priorities: typing.Optional[prioritymapT] = None
    '''Event Loop Request priorities.

    Optional.
    This is the per-class setting, can be overriden.
    '''
    thread: typing.Optional[threading.Thread]
    '''Event Loop Thread Object.

    `None` when the event loop is not alive, points to the Event Loop `Thread
    <threading.Thread>` otherwise.
    See `is_running`.

    Automatically managed by `start`/`stop`.
    '''
    tName: str
    '''Thread Name'''
    cntProcessed: int
    '''Counter for correctly processed `ELReq` tasks.

    This is incremented right after the processing function run successfully.
    It can be safely used from within the `process` function, in the Event Loop
    Thread, but not from other threads (no locking is implemented).
    '''

    def __init__(self, *,
                 qinput: typing.Optional[PriorityQueue] = None,
                 qoutput: typing.Optional[Queue] = None, wcallback: typing.Union[None, callbackT, ELCallback] = None,
                 name: typing.Optional[str] = None,
                 priorities: typing.Optional[prioritymapT] = None,
                 **kwargs: typing.Any):
        self.qinput: PriorityQueue = qinput or PriorityQueue()
        self.qoutput: typing.Optional[Queue]
        self.wcallback: typing.Optional[ELCallback]
        # Default to `qoutput` setup
        if wcallback is None:
            self.qoutput = qoutput or Queue()
            self.wcallback = None
        elif qoutput is None:
            self.qoutput = None
            if isinstance(wcallback, ELCallback):
                self.wcallback = wcallback
            else:
                assert callable(wcallback) and hasattr(wcallback, '__self__'), f'Invalid wcallback: {wcallback}'
                assert wcallback.__self__ is not None, f'Weird wcallback: unbound method: {wcallback}'
                self.wcallback = ELCallback(wcallback.__self__, wcallback)
        else:
            raise ValueError('EventLoop: Choose between `qoutput` and `wcallback`')
        self.lockThread = threading.Lock()
        self.eStopped: threading.Event = threading.Event()
        with self.lockThread:
            self.thread = None
            self.eStopped.set()  # Start stopped
        self.cntProcessed = 0
        self.tName = name or self.name or ''
        self.__priorities: prioritymapT = self.priorities or priorities or {}
        if __debug__:
            # TODO: `raise exception.EventLoopError`?
            if threading.current_thread() is not threading.main_thread():
                logger.warning('eventloop=%s: Creating the EventLoop from a sub-thread', self.tName)
            for pclass in set(k for k, p in self.__priorities.items() if p == NORMAL_PRIORITY):
                logger.warning('eventloop=%s req=%s: Default Priority is %d', self.tName, pclass.__qualname__, NORMAL_PRIORITY)
        self.setup_eventloop(**kwargs)

    def setup_eventloop(self, **kwargs) -> None:
        '''Setup the EventLoop object, with the other keyword arguments.

        Defaults to doing nothing, subclasses should redefine this.
        '''
        pass

    def is_running(self) -> bool:
        '''Check if the Event Loop is running.

        This means the thread is ready to process tasks.

        Once the thread is `stopped <stop>`, it stops running, but the thread
        itself might remain `alive <threading.Thread.is_alive>` for a while for
        cleanup.
        '''
        with self.lockThread:
            return self.thread is not None

    def is_paused(self) -> bool:
        '''Check if the event loop is paused.

        This means a dead event loop that has some requests to be processed.

        This means the corresponding thread was alive at some point, but no
        longer. It can be `restarted <start>` once again, to keep processing
        the remaining events.

        See Also:
            The `is_running` function should be used on most situations.
        '''
        with self.lockThread:
            return self.thread is None and not self.qinput.empty()

    def start(self, *, daemon: bool = True) -> threading.Thread:
        '''Start executing the Event Loop, in a background thread.

        There will be a single thread processing event at a time. If you try to
        "start" a running Event Loop, this raises an `exception
        <exception.EventLoopConcurrencyError>`.

        Args:
            daemon: Set the `daemon <threading.Thread.daemon>` option for
                thread creation. Defaults to `True`.

        .. note::
            This should be called from the Main Thread, not from any
            sub-thread.
            It can be called from any thread, including the `Event Loop Thread
            <thread>`, but that is usually a logic error.
        '''
        if __debug__:
            if threading.current_thread() is not threading.main_thread():
                logger.warning('eventloop=%s: Starting the EventLoop from a sub-thread', self.tName)
        if self.is_running():
            raise exception.EventLoopConcurrencyError(f'eventloop={self.tName}: Starting a running EventLoop')
        ctime = datetime.now().isoformat()
        with self.lockThread:
            thread = threading.Thread(name=f'{self.tName}@{ctime}', daemon=daemon,
                                      target=self.run)
            thread.start()
        return thread

    def stop(self, *, join: bool = False):
        '''Stop execution the Event Loop, ASAP.

        If you try to "stop" a non-running Event Loop, this raises an
        `exception <exception.EventLoopConcurrencyError>`.

        Since the threading model is cooperative, the currently executing task
        (if any) is not interrupted.
        The only exception is the `isleep` process, that is interrupted.

        Args:
            join: Wait for the thread to finish.
                Defaults to `False`, fully asynchronous behaviour.

        .. note::
            This should be called from the Main Thread, not from any
            sub-thread.
            It can be called from any thread, including the `Event Loop Thread
            <thread>`, but that is usually a logic error.
        '''
        if __debug__:
            if self.thread is threading.current_thread():
                logger.warning('eventloop=%s: Stopping the EventLoop from itself', self.tName)
            if self.eStopped.is_set():
                logger.warning('eventloop=%s: Stopping a stopped EventLoop', self.tName)
        if not self.is_running():
            raise exception.EventLoopConcurrencyError(f'eventloop={self.tName}: Stopping a non-running EventLoop')
        with self.lockThread:
            thread = self.thread   # Save a reference to the thread, in case is disappears
        self.eStopped.set()    # Mark as stopped
        if self.qinput.empty():
            self.qinput.put(None)  # Make sure to unwedge the queue processing code
        if thread is not None and join:
            thread.join()

    def toggle(self) -> typing.Optional[threading.Thread]:
        '''Toggle Event Loop execution.

        If `is_running`, `stop` it, otherwise `start` it. Useful to have a
        single button for controlling the Event Loop execution state.

        Returns:
            Returns `None` if the Event Loop was stopped, or the next Event
            Loop Thread Object otherwise.
        '''
        if self.is_running():
            self.stop()
            return None
        else:
            return self.start()

    def isleep(self, duration: float) -> bool:
        '''Suspend the thread execution for a while, interruptible.

        This suspension can be interrupted by calling `stop`.

        .. note::
            This is called from the `Event Loop Thread <thread>`, when
            implementing the processing functions. See `process`.

            Do not use this in other contexts.

        See Also:
            For a non-interuptible thread suspension, see `usleep`.
        '''
        assert self.thread is threading.current_thread(), f'eventloop={self.tName}: isleep outside Event Loop Thread'
        return self.eStopped.wait(timeout=duration) is not True

    def usleep(self, duration: float) -> bool:
        '''Suspend the thread execution for a while, interruptible.

        This suspension cannot be interrupted; when calling `stop`, the event
        loop will only stop after this suspension ends.

        .. note::
            This is called from the `Event Loop Thread <thread>`, when
            implementing the processing functions. See `process`.

            Do not use this in other contexts.

        See Also:
            For an interuptible thread suspension, see `isleep`.
        '''
        assert self.thread is threading.current_thread(), f'eventloop={self.tName}: usleep outside Event Loop Thread'
        time.sleep(duration)
        return True

    def run(self):
        '''Run the EventLoop.

        This is the target function for the `thread object <EventLoop.thread>`.

        Do not use this directly, see `start`.
        '''
        assert not self.is_running(), f'eventloop={self.tName}: Running a running thread'
        # Starting
        # - Manipulate, then signal
        if __debug__:
            logger.debug('> SET THREAD')
        with self.lockThread:
            self.thread = threading.current_thread()
            assert self.thread.daemon, f'eventloop={self.tName}: Unsupported `daemon=False`'
            self.eStopped.clear()
        if __debug__:
            logger.debug('> > HAS THREAD: %r', self.thread)
        self.signal(True)  # Started
        if __debug__:
            logger.debug('> START')
        # Loop through priority requests
        # # If `daemon` is False, `qinput.get` MUST have a timeout, or it will
        # # deadlock once the parent process exits. Other possiblity is
        # # processing signals.
        # Loop while not stopped, and there are tasks to process
        while self.eStopped.is_set() is False:
            if __debug__:
                logger.debug('> > GET TASK')
            prequest = self.qinput.get()
            if __debug__:
                logger.debug('> > HAS PREQ')
            if prequest is None:
                pass  # Re-Check for stopped state
            else:
                assert isinstance(prequest, ELReq_Priority), f'eventloop={self.tName}: Invalid PREQ Type: {prequest!r}'
                task = prequest.request
                if __debug__:
                    logger.debug('> >   HAS REQ C=%d P=%d', prequest.count, prequest.priority)
                try:
                    assert isinstance(task, ELReq), f'eventloop={self.tName}: Invalid REQ Type: {task!r}'
                    if __debug__:
                        logger.debug('> > START REQ')
                    self.process(task, prequest.priority)
                    if __debug__:
                        logger.debug('> >   END REQ')
                    self.cntProcessed += 1
                except Exception as e:
                    # Stop processing
                    logger.critical('eventloop=%s: Processing Error: %r', self.tName, e)
                    # TODO: Mark EventLoop as broken?
                    break
            self.qinput.task_done()
        # Stopping
        # - Signal then manipulate
        if __debug__:
            logger.debug('> STOP')
        self.signal(False)  # Stopped
        if __debug__:
            logger.debug('> > RM THREAD: %r', self.thread)
        with self.lockThread:
            self.thread = None
        if __debug__:
            logger.debug('> END')

    def process(self, task: ELReq, priority: int):
        '''Process a single task, with a priority.

        Defaults to doing nothing, subclasses should redefine this.
        See `singledispatchmethod <functools.singledispatchmethod>` for a
        possible solution for polymorphism based on `ELReq` subclasses.

        The `cntProcessed` counter is unique for each task during this call,
        and it is attached to the responses queued during this call. This means
        it can be used to match request and respond, even though everything
        happens asynchronously.
        To do that, save that result on the response, and compare it with
        ``ridx``.

        Do not use this directly, see `queue`.

        .. note::

            This is called from the `Event Loop Thread <thread>`,
            automatically.
        '''
        if __debug__:
            raise NotImplementedError(f'eventloop={self.tName} event={task} p={priority}: Undefined processing')
        pass

    def queue(self, task: ELReq, *, priority: typing.Optional[int] = None):
        '''Queue a new task on the event loop, optionally with a priority.

        Append a new `task <ELReq>` to the Event Loop. You can set a priority
        for the task, or leave it with the default priority: `priorities` and
        the ultimate `NORMAL_PRIORITY` fallback.

        It is possible to queue tasks into a paused event loop. This will be
        processed once the event loop restarts.

        Args:
            task: Task to queue
            priority: Request priority.
                Optional, defaults to `priorities` and `NORMAL_PRIORITY`.

        .. note::
            This should be called from the Main Thread, not from any
            sub-thread.
            It can be called from any thread, including the `Event Loop Thread
            <thread>`, but that is usually a logic error.
        '''
        if __debug__:
            if self.thread is threading.current_thread():
                logger.debug('eventloop=%s: Queueing responses from the Event Loop Thread', self.tName)
        assert isinstance(task, ELReq), f'eventloop={self.tName}: Invalid Request: {task}'
        actual_priority = priority or self.__priorities.get(task.__class__, NORMAL_PRIORITY)
        assert isinstance(actual_priority, int), f'eventloop={self.tName}: Invalid Priority Calculation: {actual_priority!r}'
        self.qinput.put(ELReq_Priority(task, priority=actual_priority))

    def signal(self, signal: bool):
        '''Signal a new internal event on the output.

        Should append a `bool` signal on the output queue, or equivalent.

        .. note::
            This is called from the `Event Loop Thread <thread>`, when
            implementing the processing functions. See `process`.

            Do not use this in other contexts.
        '''
        assert self.thread is threading.current_thread(), f'eventloop={self.tName}: signal outside Event Loop Thread'
        if self.qoutput is None:
            assert self.wcallback is not None
            self.wcallback.trigger(self, None, signal)
        else:
            self.qoutput.put((None, signal))

    def respond(self, response: ELRes):
        '''Add a new response on the output.

        Append a new `response <ELRes>` on the Event Loop output queue, or
        equivalent.

        .. note::
            This is called from the `Event Loop Thread <thread>`, when
            implementing the processing functions. See `process`.

            Do not use this in other contexts.
        '''
        assert self.thread is threading.current_thread(), f'eventloop={self.tName}: respond outside Event Loop Thread'
        if self.qoutput is None:
            assert self.wcallback is not None
            self.wcallback.trigger(self, self.cntProcessed, response)
        else:
            self.qoutput.put((self.cntProcessed, response))

    def responses(self, chunk: int = 10) -> typing.Iterable[typing.Tuple[typing.Optional[int], typing.Union[bool, ELRes]]]:
        '''Retrieve responses from the event loop.

        Args:
            chunk: Retrive at most this amount of responses.

        Returns:
            This is a generator that produces data tuples. See `EventLoop` for
            the kinds of responses produced here, the format is a tuple
            ``(index, payload)``.

        .. note::
            This should be called from the Main Thread, not from any
            sub-thread.
            It can be called from any thread, including the `Event Loop Thread
            <thread>`, but that is usually a logic error.
        '''
        if self.qoutput is None:
            raise exception.EventLoopError('Reading responses when no output queue is defined')
        if threading.current_thread() is not threading.main_thread():
            logger.warning('eventloop=%s: Reading responses from a sub-thread', self.tName)
        for eidx in range(chunk):
            try:
                ridx, response = self.qoutput.get(block=False)
                if __debug__:
                    if ridx is None:  # Signal
                        assert ridx is None
                        assert isinstance(response, bool), f'eventloop={self.tName}: Weird    Signal: {response}'
                    else:             # Response
                        assert isinstance(ridx, int)
                        assert isinstance(response, ELRes), f'eventloop={self.tName}: Weird Response: {response}'
                yield ridx, response
            except Empty:
                break  # Nothing to do

    def cntRequests(self) -> int:
        '''Return the approximate size of the request queue.

        This indicates unprocessed tasks.
        See the upstream function `qsize <queue.Queue.qsize>`.

        .. note::
            This should be called from the Main Thread, not from any
            sub-thread.
            It can be called from any thread, including the `Event Loop Thread
            <thread>`, but that is usually a logic error.
        '''
        return self.qinput.qsize()

    def cntResponses(self) -> typing.Optional[int]:
        '''Return the approximate size of the response queue, if exists.

        This indicates unprocessed responses.
        See the upstream function `qsize <queue.Queue.qsize>`.

        Returns:
            Returns `None` if there is no output queue (connected to a ``Tk``
            event loop directly).

        .. note::
            This should be called from the Main Thread, not from any
            sub-thread.
            It can be called from any thread, including the `Event Loop Thread
            <thread>`, but that is usually a logic error.
        '''
        if self.qoutput is None:
            return None
        else:
            return self.qoutput.qsize()

    def setup_process_respond(self, response_type: typing.Type[ELRes]) -> typing.Callable[[ELReq, int], None]:
        '''Setup a basic `process` function, with static responses.

        Setup a `process` function with a simple log, with a response
        ``response_type()``.

        .. note::

            This is mostly useful for testing, the correct way to implement
            this is to subclass the `EventLoop` class.
        '''
        logger.debug('eventloop=%s event=%s: HACK: Setup Auto-Respond', self.tName, response_type.__qualname__)

        def setup_process_respond(task: ELReq, priority: int):
            logger.debug('eventloop=%s event=%s p=%d: Process', self.tName, task, priority)
            self.respond(response_type())
        self.process = setup_process_respond  # type: ignore[method-assign]
        return setup_process_respond
