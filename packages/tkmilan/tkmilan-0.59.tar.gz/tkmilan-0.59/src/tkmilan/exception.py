'''
All custom exceptions raised in the project.
'''
import typing

if typing.TYPE_CHECKING:
    from .diagram import DiagramElement


class InvalidWidgetDefinition(ValueError):
    pass


class InvalidWidgetState(Exception):
    def __init__(self, msg: str):
        self.msg = msg


class InvalidLayoutError(Exception):
    pass


class InvalidCallbackDefinition(Exception):
    def __init__(self, msg: str):
        self.msg = msg


class InvalidImageKey(Exception):
    def __init__(self, key: str):
        self.key = key


class InvalidImageType(Exception):
    def __init__(self, dtype: str):
        self.dtype = dtype


class InvalidRender(Exception):
    def __init__(self, de: 'DiagramElement'):
        self.de = de


class EventLoopError(Exception):
    def __init__(self, msg: str):
        self.msg = msg


class EventLoopConcurrencyError(EventLoopError):
    pass


class EventBusError(Exception):
    def __init__(self, msg: str):
        self.msg = msg


class EventBusRegisterError(EventBusError):
    pass
