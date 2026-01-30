'''Models to store diagram information.

Implements Euclidian geometry figures in 2D, with discrete pixel coordinates
(some functions accept or provide real numbers, when integer conversion is too
lossy). Mostly implemented as `dataclasses`.

The coordinate system is common to several implementations, origin on the
topleft corner, axes directed to the rigth and down.
See :tkinter_effbot:`canvas coordinate systems <canvas.htm#coordinate-systems>`
documentation.
See also the correspoding `SVG documentation
<https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorials/SVG_from_scratch/Positions>`_,
as example.

See also :doc:`tkmilan.model`.
'''
# Technically, coordinates can be given as strings with physical distances.
# Probably not worth it to support this.
import typing
import warnings
import logging
from functools import singledispatchmethod
import abc
from enum import Enum
from dataclasses import dataclass, field, asdict as dc_asdict
import math
import numbers
import tkinter as tk

from . import model

logger = logging.getLogger(__name__)


nround: typing.Callable[[typing.Union[typing.SupportsInt, typing.SupportsFloat, typing.SupportsComplex]], int]
'''Round any number to integer.

For production binaries, this is just `int`.
'''
if __debug__:
    def nround(n: typing.Union[typing.SupportsInt, typing.SupportsFloat, typing.SupportsComplex]) -> int:
        assert isinstance(n, typing.SupportsInt), f'Type Error: round({type(n)})={n!r}'
        rval = int(n)
        assert isinstance(rval, int), f'Rounding Error: {n!r} > {rval!r}'
        return rval
else:
    nround = int  # type: ignore[assignment]


nfloat: typing.Callable[[typing.Union[typing.SupportsInt, typing.SupportsFloat, typing.SupportsComplex]], float]
'''Convert any number to floating point.

For production binaries, this is just `float`.
'''
if __debug__:
    def nfloat(n: typing.Union[typing.SupportsInt, typing.SupportsFloat, typing.SupportsComplex]) -> float:
        assert isinstance(n, typing.SupportsFloat), f'Type Error: convert({type(n)})={n!r}'
        rval = float(n)
        assert isinstance(rval, float), f'Conversion Error: {n!r} > {rval!r}'
        return rval
else:
    nfloat = float  # type: ignore[assignment]


# Geometric Constructs
@dataclass(frozen=True)
class Vector:
    '''A vector with integer coordinates.

    Args:
        dx: The ``x`` coordinate.
        dy: The ``y`` coordinate.

    .. automethod:: __neg__

    See Also:
        See other geometric constructs like `XY`, and `GeometryLine`.
    '''
    dx: int
    dy: int

    def __post_init__(self):
        assert self.dx == nround(self.dx), f'{self}: Only integer X coordinates are supported'
        assert self.dy == nround(self.dy), f'{self}: Only integer Y coordinates are supported'

    @property
    def tuple(self) -> typing.Tuple[int, int]:
        '''Represent the vector as a coordinate tuple.

        Useful to actually pass this information to most functions.
        '''
        return (self.dx, self.dy)

    def size(self) -> numbers.Real:
        '''Calculate the vector magnitude, that it, it's length.

        Returns:
            The vector magnitude, a real number.
        '''
        assert isinstance(math.hypot(self.dx, self.dy), numbers.Real)
        return typing.cast(numbers.Real, math.hypot(self.dx, self.dy))

    def scale(self, both: typing.Optional[numbers.Real] = None, *,
              sx: typing.Optional[numbers.Real] = None, sy: typing.Optional[numbers.Real] = None,
              ) -> 'Vector':
        '''Calculate a scaled vector.

        Note the scaling factors do not need to be integers, they are coerced
        to integers after the calculation using `nround`.

        Choose to either scale both coordinates by the same factor using
        ``both``, or individually using ``sx``/``sy``.
        Do not combine both methods, or results might be unpredictable.
        When not given, the other coordinates remain the same.

        Args:
            both: Scale both coordinates by this factor.
            sx: Scale the ``x`` coordinate.
            sy: Scale the ``y`` coordinate.

        Returns:
            A new `Vector` object.
        '''
        assert both is None or (sx is None and sy is None), 'Scale both coordinates, or one at a time'
        return self.__class__(dx=nround(self.dx * (sx or both or 1)),   # type: ignore[arg-type]
                              dy=nround(self.dy * (sy or both or 1)))   # type: ignore[arg-type]

    def __neg__(self) -> 'Vector':
        '''Calculate the negated vector.

        Use as ``-vector``.

        Returns:
            A new `Vector` with negated coordinates.

        Note:
            This should be similar to ``vector.scale(-1)``.
        '''
        assert self.scale(typing.cast(numbers.Real, -1)).tuple == (-self.dx, -self.dy)
        return self.__class__(dx=-self.dx, dy=-self.dy)


def VectorH(dx: int, *args, **kwargs) -> Vector:
    '''An horizontal `Vector`.

    Requires only the ``x`` coordinate.

    See Also:
        Wrapper for `Vector`.
    '''
    assert dx == nround(dx), 'Only integer X coordinates are supported'
    return Vector(nround(dx), 0, *args, **kwargs)


def VectorV(dy: int, *args, **kwargs) -> Vector:
    '''A vertical `Vector`.

    Requires only the ``y`` coordinate.

    See Also:
        Wrapper for `Vector`.
    '''
    assert dy == nround(dy), 'Only integer Y coordinates are supported'
    return Vector(0, nround(dy), *args, **kwargs)


def VectorPolar(r: numbers.Real, theta: numbers.Real) -> Vector:
    '''A "polar" `Vector`, defined by radius and angle.

    See `Wikipedia polar coordinates
    <https://en.wikipedia.org/wiki/Polar_coordinate_system>`_ information.

    Args:
        r: Radius
        theta: Vector angle, in degrees.
    '''
    # Remember: Y axis is the other way around
    return Vector(
        nround(r * math.cos(math.radians(theta))),   # type: ignore[arg-type]
        -nround(r * math.sin(math.radians(theta))),  # type: ignore[arg-type]
    )


@dataclass(frozen=True)
class XY:
    '''A location with integer coordinates.

    Args:
        x: The ``x`` coordinate.
        y: The ``y`` coordinate.

    .. automethod:: __add__
    .. automethod:: __sub__

    See Also:
        See other geometric constructs like `Vector`, and `GeometryLine`.
    '''
    x: int
    y: int

    @property
    def tuple(self) -> typing.Tuple[int, int]:
        '''Represent the vector as a coordinate tuple.

        Useful to actually pass this information to most functions.
        '''
        return (self.x, self.y)

    def vto(self, other: 'XY') -> Vector:
        '''Calculate the `Vector` joining this and ``other`` point.

        The result is a vector that when added to this point, results in the
        ``other`` point.

        Args:
            other: The other `XY`, see the description above.

        Returns:
            A new `Vector` object.
        '''
        return Vector(other.x - self.x, other.y - self.y)

    def edistance(self, other: 'XY') -> numbers.Real:
        '''Calculate the Euclidian distance between this and ``other`` point.

        Returns:
            The distance between both points, as a floating point number.
        '''
        return typing.cast(numbers.Real, math.hypot(
            abs(other.x - self.x),
            abs(other.y - self.y),
        ))

    @singledispatchmethod
    def __add__(self, obj: typing.Any):
        '''Calculate the sum of the given object with this location.

        Supported Object Types:

        - `Vector`

        Use as ``xy + vector``.
        '''
        raise NotImplementedError

    @__add__.register
    def __add__Vector(self, obj: Vector):
        return self.__class__(x=self.x + obj.dx, y=self.y + obj.dy)

    @singledispatchmethod
    def __sub__(self, obj: typing.Any):
        '''Calculate the subtraction of the given object with this location.

        Supported Object Types:

        - `Vector`

        Use as ``xy - vector``.
        '''
        raise NotImplementedError

    @__sub__.register
    def __sub__Vector(self, obj: Vector):
        return self + (-obj)


@dataclass(frozen=True)
class GeometryLine:
    '''A geometric line (not an element like `Line`), for easing some
    calculations. Uses real parameters.

    To create this object based on other inputs, see `points` and
    `point_slope`.

    Args:
        m: Line slope. `None` means a vertical line (equivalent to infinite
            slope).
        c0: For vertical lines, it's the ``x`` coordinate for all points.
            For other lines, it's the ``y`` coordinate at ``x=0``.
            See `equation` for the complete picture.

    See Also:
        See other geometric constructs like `XY`, and `Vector`.

    .. automethod:: __contains__
    '''
    m: typing.Optional[numbers.Real]
    c0: numbers.Real

    def __init__(self,
                 m: typing.Union[int, float, numbers.Real, None],
                 c0: typing.Union[int, float, numbers.Real],
                 ):
        object.__setattr__(self, 'm', typing.cast(typing.Optional[numbers.Real], None if m is None else nfloat(m)))
        object.__setattr__(self, 'c0', typing.cast(numbers.Real, nfloat(c0)))

    def __str__(self):
        return f'{self.__class__.__qualname__}<{self.equation}>'

    @property
    def equation(self) -> str:
        '''Derive an equation for the line.

        This uses the Slope-intercept form.
        '''
        if self.m is None:
            # Vertical
            return f'x = {self.c0}'
        elif self.m == 0.0:
            return f'y = {self.c0}'
        else:
            string = 'y = '
            if self.m == 1.0:
                string += 'x'
            elif self.m == -1.0:
                string += '-x'
            else:
                string += f'{self.m} . x'
            if self.c0 < typing.cast(numbers.Real, 0.0):
                string += '+ {self.c0}'
            elif self.c0 > typing.cast(numbers.Real, 0.0):
                string += '- {-self.c0}'
            else:
                assert self.c0 == 0.0
            return string

    @singledispatchmethod
    def __contains__(self, obj: typing.Any) -> bool:
        '''Calculate if the given object is contained on this line.

        Supported Object Types:

        - `XY`

        Use as ``xy in line``.
        '''
        raise NotImplementedError

    @__contains__.register
    def __contains__XY(self, obj: XY):
        if self.m is None:
            # Vertical
            return obj.x == self.c0
        else:
            return math.isclose(obj.y, typing.cast(numbers.Real, self.m * obj.x + self.c0))

    def intersect_y(self, y: int) -> typing.Optional[XY]:
        '''Calculate the intersection of this line with an horizontal line.

        Args:
            y: The ``y`` coordinate for the horizontal line.

        Returns:
            Return the intersection point, if exists.
            Returns `None` when there is not intersection, or there is an
            infinite number of points.

        See Also:
            See `intersect_line` for calculating the intersection with any
            line.
        '''
        if self.m is None:
            return XY(nround(self.c0), y)
        elif self.m == 0.0:
            return None
        else:
            return XY(nround((y - self.c0) / self.m), y)  # type: ignore[arg-type]

    def intersect_x(self, x: int) -> typing.Optional[XY]:
        '''Calculate the intersection of this line with a vertical line.

        Args:
            x: The ``x`` coordinate for the horizontal line.

        Returns:
            Return the intersection point, if exists.
            Returns `None` when there is not intersection, or there is an
            infinite number of points.

        See Also:
            See `intersect_line` for calculating the intersection with any
            line.
        '''
        if self.m is None:
            return None
        else:
            return XY(x, nround(self.m * x + self.c0))  # type: ignore[arg-type]

    def intersect_line(self, other: 'GeometryLine') -> 'typing.Optional[XY]':
        '''Calculate the intersection of this line with any other line.

        Args:
            other: The other line.

        Returns:
            Return the intersection point, if exists.
            Returns `None` when there is not intersection, or there is an
            infinite number of points.

        See Also:
            See `intersect_x` and `intersect_y` for calculating the
            intersection with special lines.
        '''
        if self.m == other.m:
            # Parallel
            if __debug__:
                if self.c0 == other.c0:
                    logger.warning('%s|%s: Both lines are the same', self, other)
            return None
        elif other.m is None:
            # other + Vertical
            return self.intersect_x(nround(other.c0))
        elif self.m is None:
            # Vertical + other
            return other.intersect_x(nround(self.c0))
        else:
            assert self.m is not None and other.m is not None
            m_delta = self.m - other.m
            assert m_delta != 0
            return XY(
                x=nround((other.c0 - self.c0) / m_delta),                     # type: ignore[operator]
                y=nround((other.c0 * self.m - other.m * self.c0) / m_delta),  # type: ignore[operator]
            )

    def parallel_point(self, p: XY) -> 'GeometryLine':
        '''Calculate the parallel line that goes through a given point.

        There is only a single line parallel to the current one that goes
        through an external point.
        If the point is already in the current line, returns itself.

        Args:
            p: A point on the new line.
        '''
        if p in self:
            if __debug__:
                logger.warning('%s: Point %s in line already', self, p)
            return self
        elif self.m is None:
            # Vertical
            return self.__class__(m=None, c0=p.x)
        else:
            hdelta = p.y - (self.m * p.x + self.c0)  # type: ignore[operator]
            assert isinstance(self.c0 + hdelta, typing.SupportsFloat)
            return self.__class__(m=self.m, c0=nfloat(self.c0 + hdelta))  # type: ignore[arg-type]

    def perpendicular_point(self, p: XY) -> 'GeometryLine':
        '''Calculate the perpendicular line that goes through a given point.

        There is only a single line perpendicular to the current one that goes
        through any point.

        Args:
            p: A point on the new line.
        '''
        if self.m is None:
            # Vertical ⟂ Horizontal
            return self.__class__(0.0, p.y)
        elif self.m == 0.0:
            # Horizontal ⟂ Vertical
            return self.__class__(None, p.x)
        else:
            assert isinstance(-self.m, typing.SupportsFloat)
            pm = math.pow(-self.m, -1.0)
            assert pm == -1 / self.m  # (- 1 / m)
            return self.__class__.point_slope(p, typing.cast(numbers.Real, pm))

    # TODO: On Python 3.11:: -> typing.Self
    @classmethod
    def points(cls, p1: XY, p2: XY) -> 'GeometryLine':
        '''Create the line that goes through both points.

        If both points refer to the same location, this is an error.

        Args:
            p1: One of the points in the line.
            p2: One of the points in the line.
        '''
        assert p1 != p2, f'Same point, no line exists: {p1}/{p2}'
        if p1.x == p2.x:
            # Vertical
            return cls(m=None, c0=nfloat(p1.x))
        elif p1.y == p2.y:
            # Horizontal
            return cls(m=0.0, c0=nfloat(p2.y))
        else:
            return cls(
                m=(p1.y - p2.y) / (p1.x - p2.x),
                c0=(p1.x * p2.y - p2.x * p1.y) / (p1.x - p2.x)
            )

    # TODO: On Python 3.11:: -> typing.Self
    @classmethod
    def point_slope(cls, p: XY, m: typing.Optional[numbers.Real]) -> 'GeometryLine':
        '''Create the line that goes through a point with the given slope.

        Args:
            p: One of the points in the line.
            m: Line slope. `None` means infinite slope, that is, a vertical
                line.
        '''
        if m is None:
            # Vertical
            return cls(m=None, c0=nfloat(p.x))
        elif m == 0:
            # Horizontal
            return cls(m=0.0, c0=nfloat(p.y))
        else:
            assert isinstance(p.y - m * p.x, typing.SupportsFloat)  # type: ignore[operator]
            return cls(m=nfloat(m), c0=nfloat(p.y - m * p.x))  # type: ignore[operator]


# Settings Objects
@dataclass
class C:
    '''Colour settings.

    The colours are :tk_lib:`arbitrary colours <GetColor.htm#M7>` with the
    format ``#RRGGBB``/``#RGB``, or the following :tk:`recognized colour names
    <colors.htm>`.

    Args:
        fill: The filling colour, for the internal element area.
            Optional.
        outline: The outline colour, for the line that marks the element
            boundary. Optional.
    '''
    fill: typing.Optional[str] = None
    outline: typing.Optional[str] = None

    @property
    def reverse(self) -> 'C':
        '''Calculate reversed colour settings.

        To clarify, this is a setting when the filling colour is the outline
        colour, and vice versa.
        '''
        return C(fill=self.outline, outline=self.fill)

    def w(self, **kwargs: typing.Optional[str]) -> 'C':
        '''Calculate a colour setting with different values.

        Doesn't make sense to create a new setting with both new colours, this
        is equivalent to create a new object. This is only useful to create a
        new setting changing only a single colour.

        Args:
            fill: The new filling colour. Optional.
            outline: The new outline colour. Optional.
        '''
        assert len(kwargs) == 1, 'Change a single colour at the time'
        # Equivalent to using sentinel values as defaults, `None` is a valid value
        return C(fill=kwargs.get('fill', self.fill), outline=kwargs.get('outline', self.outline))

    if __debug__:
        def __repr__(self) -> str:
            return f'{self.__class__.__qualname__}({", ".join("=".join((k, v)) for k, v in dc_asdict(self).items() if v is not None)})'


@dataclass
class A:
    '''Arrow settings.

    Check a visual representation of the arrow head shape on the ``arrowshape``
    section in ``Tk`` :tkinter_nmt:`NMU canvas create line <create_line.html>`.

    Make sure to select one of ``atStart``/``atEnd``, otherwise this represents
    no arrow at all.

    Args:
        d1: Arrow Head Shape: Distance along the line, from neck to tip.
        d2: Arrow Head Shape: Distance along the line, from trailing points to
            tip.
        d3: Arrow Head Shape: Distance normal from the line, from the outside
            edge to the trailing points.
        atStart: Include an arrow head on the start of the line.
            Optional, defaults to `False` if no other ``at*`` settings are is
            given.
        atEnd: Include an arrow head on the end of the line.
            Optional, defaults to `True` if no other ``at*`` settings are is
            given.
        atBoth: Include an arrow head on start and end of the line.
            Optional, to be used like this:

            .. code:: python

                A(True)
    '''
    d1: int
    d2: int
    d3: int
    atStart: bool
    atEnd: bool

    def __init__(self, atBoth: typing.Optional[bool] = None, *,
                 atStart: typing.Optional[bool] = None, atEnd: typing.Optional[bool] = None,
                 d1: int = 8, d2: int = 10, d3: int = 3,
                 ):
        # Start/End
        finalAtStart: bool
        finalAtEnd: bool
        if atBoth is None:
            if atStart is None and atEnd is None:
                # Default Values: `(atEnd=True)`
                finalAtStart, finalAtEnd = False, True
            else:
                finalAtStart = atStart or False
                finalAtEnd = atEnd or False
        else:
            finalAtStart, finalAtEnd = atBoth, atBoth
        assert finalAtStart is not None
        assert finalAtEnd is not None
        self.atStart = finalAtStart
        self.atEnd = finalAtEnd
        # Shapes
        self.d1 = d1
        self.d2 = d2
        self.d3 = d3
        # Validation
        assert (self.atStart, self.atEnd) != (False, False), f'{self}: Include arrow at least in one end'


@dataclass
class D:
    '''Dash settings.

    The ``pattern`` is a tuple of distances to consider. Only odd-indexed
    pattern distances are drawn, the even-indexed distances are skipped (or
    "drawn" with transparent color). There's also an initial ``offset``, can
    even be negative.

    Check as visual representation of the dash patterns in ``Tk``
    :tkinter_nmt:`NMT canvas dash patterns <dash-patterns.html>` or :tk:`canvas
    dash patterns <canvas.htm#M26>` documentation.

    Args:
        pattern: Tuple with distances to be considered.
            See the description above on how this is represented.
        offset: Offset on pattern start.
            Defaults to ``0``, no offset.
    '''
    pattern: typing.Tuple[int, ...]
    offset: int = 0

    def __init__(self, *pattern: int, offset: int = 0):
        self.pattern = tuple(pattern)
        assert len(self.pattern) > 0
        self.offset = offset


class Cap(Enum):
    '''Cap settings.

    Check a visual representation of the style in ``Tk`` :tkinter_nmt:`NMT cap
    <cap-join-styles.html>` documentation.
    '''
    BUTT = tk.BUTT
    '''The end of the line is cut off square at a line that passes through the
    endpoint.'''
    PROJECTING = tk.PROJECTING
    '''The end of the line is cut off square, but the cut line projects past
    the endpoint a distance equal to half the line's width.'''
    ROUND = tk.ROUND
    '''The end describes a semicircle centered on the endpoint.'''

    if __debug__:
        def __repr__(self) -> str:
            return f'{self.__class__.__qualname__}.{self.name}'


class Join(Enum):
    '''Join settings.

    Check a visual representation of the style in ``Tk`` :tkinter_nmt:`NMT join
    <cap-join-styles.html>` documentation.
    '''
    ROUND = tk.ROUND
    '''The join is a circle centered on the point where the adjacent line segments meet.'''
    BEVEL = tk.BEVEL
    '''A flat facet is drawn at an angle intermediate between the angles of the adjacent lines.'''
    MITER = tk.MITER
    '''The edges of the adjacent line segments are continued to meet at a sharp point.'''

    if __debug__:
        def __repr__(self) -> str:
            return f'{self.__class__.__qualname__}.{self.name}'


class SmoothAlgorithm(Enum):
    '''Line smoothing algorithm selection.

    There is no Python documentation, see ``Tk`` :tk:`canvas line smooth
    <canvas.htm#M143>` documentation.

    See Also:
        See `Smooth` for the usable line smoothing settings.
    '''
    BEZIER2 = 'bezier'
    '''Draw line as series of quadratic Bézier curves.

    See `Wikipedia quadratic Bézier curves
    <https://en.wikipedia.org/wiki/B%C3%A9zier_curve#Quadratic_curves>`_
    information.
    '''
    BEZIER3 = 'raw'
    '''Draw line as series of cubic Bézier curves.

    See `Wikipedia cubic Bézier curves
    <https://en.wikipedia.org/wiki/B%C3%A9zier_curve#Higher-order_curves>`_
    information.
    '''

    if __debug__:
        def __repr__(self) -> str:
            return f'{self.__class__.__qualname__}.{self.name}'


class EllipseSection_Style(Enum):
    '''Style selection for `EllipseSection`.

    Check a visual representation of the style in ``Tk`` :tkinter_nmt:`NMT
    create arc <create_arc.html>` or :tk:`canvas arc style <canvas.htm#M128>`
    documentation.
    '''
    PIESLICE = tk.PIESLICE
    '''Draw section as a pie slice.

    This means the boundaries are defined by arc itself, plus two line
    segments, between the oval center and each of the arc endpoints.
    '''
    CHORD = tk.CHORD
    '''Draw section as a chord.

    This means the boundaries are defined by the arc itself, plus a single line
    segment between the arc endpoints.
    '''
    ARC = tk.ARC
    '''Draw section as a simple arc.

    This means drawing a line, just the arc itself. No area is defined.
    '''

    if __debug__:
        def __repr__(self) -> str:
            return f'{self.__class__.__qualname__}.{self.name}'


@dataclass
class Smooth:
    '''Line smoothing settings.

    There is no Python documentation, see ``Tk`` :tk:`canvas line smooth
    <canvas.htm#M143>` documentation.

    Args:
        algorithm: Line smoothing algorithm.
            Defaults to cubic Bézier curves.
        steps: The curve is rendered as a series of line segments.
            This is the amount of lines to render. Defaults to 12.
    '''
    algorithm: SmoothAlgorithm = SmoothAlgorithm.BEZIER3
    steps: int = 12

    def __post_init__(self):
        assert self.steps > 0, '{self}: Number of steps must be positive'


# Diagram Elements
class DiagramElement(abc.ABC):
    '''Common diagram element class.

    This is only an abstract class, a common base class for all the possible
    diagram elements.
    '''
    def iterate(self) -> 'typing.Iterator[DiagramElementSingle]':
        '''Gather all constituent `DiagramElementSingle` objects, recursively.'''
        if isinstance(self, DiagramElementSingle):
            yield self
        elif isinstance(self, DiagramElementMultiple):
            for item in self.items:
                yield from self.iterate()
        else:
            raise NotImplementedError(f'Unknown Type: {self!r}')

    # This is an hack for the `Renderer_TkCanvas`, to pretend it's a tuple as `GeneratorElementT`
    def __getitem__(self, key):
        ''''''  # Internal, do not document
        if key == 0:    # DiagramElement
            return self
        elif key == 1:  # marker
            return None
        else:
            raise ValueError(f'{self}: Invalid Key: {key}')


@dataclass
class DiagramElementSingle(DiagramElement):
    '''Common diagram single element class.

    All single element classes inherit from this.
    '''
    pass


@dataclass
class DiagramElementMultiple(DiagramElement):
    '''Aggregator for multiple `DiagramElement` objects.

    Certain diagram elements only make sense together, group them here.
    '''
    items: typing.Sequence[DiagramElement]

    def __init__(self, *items: DiagramElement):
        self.items = tuple(items)


GeneratorElementT = typing.Union[
    DiagramElement,
    typing.Tuple[DiagramElement, str]
]
'''Type-Checking variable type for `Diagram` drawing functions.

Can be a `DiagramElement`, or a tuple of `DiagramElement` and `str`, used as a
marker for the element in the renderer.
'''


# Support arbitrary layers?
class Diagram(abc.ABC):
    '''Diagram generator class.

    This should be subclassesed and it's function implemented with `iter` that
    create the diagram itself, based on possible ``__init__`` state, and also
    per-function arguments.

    There are three available "layers" for elements, each built from a
    function, in order:

    - `setup_bg_b`: Background Back (``z=-1``).
    - `setup_fg`: Foreground (``z=0``)
    - `setup_bg_f`: Background Front (``z=1``).

    All functions are optional, they default to generate no elements.

    This is only an abstract class, a common base class for all the possible
    diagrams.
    '''
    # TODO: Implement arbitrary layers?
    # No `__init__`, this is specific for each one
    BACKGROUND: typing.Optional[str] = None
    '''Canvas background colour.

    Optional. See `C` for colour specification.
    '''
    DISABLEDBACKGROUND: typing.Optional[str] = None
    '''Canvas background colour, when disabled.

    Optional. See `C` for colour specification.
    '''
    MIN_SIZE: typing.Tuple[typing.Optional[int], typing.Optional[int]] = (None, None)
    '''Canvas minimum size for rendering.

    If the canvas size is smaller than any of the (non-`None`) sizes, rendering
    is skipped.

    Optional.
    '''

    def setup_bg_b(self, *, cwidth: int, cheight: int) -> typing.Generator[GeneratorElementT, typing.Optional[int], None]:
        '''Draw the Background Back layer.

        Should be a generator creating a finite amount of `GeneratorElementT`.
        Sends the element identifier (an integer).

        .. note::
            For debug binaries, sends `None` if the render had a problem. On
            production binaries, this is an error.
        '''
        # Drawn only when size changes
        yield from []

    def setup_fg(self, *, cwidth: int, cheight: int) -> typing.Generator[GeneratorElementT, typing.Optional[int], None]:
        '''Draw the Foreground layer.

        Should be a generator creating a finite amount of `GeneratorElementT`.
        Sends the element identifier (an integer).

        .. note::
            For debug binaries, sends `None` if the render had a problem. On
            production binaries, this is an error.
        '''
        # Drawn always
        yield from []

    def setup_bg_f(self, *, cwidth: int, cheight: int) -> typing.Generator[GeneratorElementT, typing.Optional[int], None]:
        '''Draw the Background Front layer.

        Should be a generator creating a finite amount of `GeneratorElementT`.
        Sends the element identifier (an integer).

        .. note::
            For debug binaries, sends `None` if the render had a problem. On
            production binaries, this is an error.
        '''
        # Drawn only when size changes
        yield from []


# # External Diagram Elements

# # # Base Elements
@dataclass
class MultiLine(DiagramElementSingle):
    '''Diagram Element: multi-segment line.

    Represent multiple line segments with common points: line segment between
    first and second, second and third, etc...

    There is no Python documentation, see ``Tk`` :tk:`canvas common options
    <canvas.htm#M99>` and :tk:`canvas line options <canvas.htm#M143>`. See also
    :tkinter_nmt:`NMT create line <create_line.html>` documentation.

    Args:
        points: Sequence of points to draw the line segments.
            Must have at least two points.
        color: Colour for line segments, see `C` for colour specification.
            Considers only ``outline``.
        width: Width for line segments, in pixels.
            Optional, defaults to minimum line width.
        dash: Dashed line segments setting.
            Optional, defaults to solid line.
        arrow: Arrow line settings.
            Optional, defaults to no arrows anywhere.
        cap: Line capping setting. Defaults to `Cap.BUTT`.
        join: Line join setting. Defaults to `Join.ROUND`.
        smooth: Line smoothing setting.
            Optional, defaults to straight line.
        colorActive: ``color`` for active elements, that is, on mouse hover.
        widthActive: ``width`` for active elements, that is, on mouse hover.
        dashActive: ``dash`` for disabled elements.
            ``offset`` is not supported.
        colorDisabled: ``color`` for disabled elements.
        widthDisabled: ``width`` for disabled elements.
        dashDisabled: ``dash`` for disabled elements.
            ``offset`` is not supported.
        tags: Sequence of tags to apply to the element.
            Must not include any "internal tags", starting with ``:``.
    '''
    # - No stipple support, it's not cross platform
    points: typing.Sequence[XY]
    color: C = field(default_factory=C)  # TODO: Accept single string, `C(outline=x)`
    width: typing.Optional[int] = None
    dash: typing.Optional[D] = None  # TODO: Accept (int, int), `D(*x)`
    arrow: typing.Optional[A] = None
    cap: Cap = Cap.BUTT
    join: Join = Join.ROUND
    smooth: typing.Optional[Smooth] = None
    colorActive: C = field(default_factory=C)  # TODO: Accept single string, `C(outline=x)`
    widthActive: typing.Optional[int] = None
    dashActive: typing.Optional[D] = None  # TODO: Accept (int, int), `D(*x)`
    colorDisabled: C = field(default_factory=C)  # TODO: Accept single string, `C(outline=x)`
    widthDisabled: typing.Optional[int] = None
    dashDisabled: typing.Optional[D] = None  # TODO: Accept (int, int), `D(*x)`
    tags: typing.Sequence[str] = tuple()

    if __debug__:
        # Validate settings
        def __post_init__(self):
            if len(self.points) < 2:
                raise ValueError(f'{self}: A Line has at least two points')
            if self.smooth is None:
                if len(set(self.points)) != len(self.points):
                    logger.warning('%s: Repeated "points"', self)
            else:
                logger.warning('%s: Smoothing algorithm selection is not fully implemented', self)
            for c in ('color', 'colorActive', 'colorDisabled'):
                cv = getattr(self, c)
                if cv.fill is not None:
                    if cv.outline is None:
                        logger.warning('%s: To paint a line with `%s`, use "outline" exclusively', self, c)
                    else:
                        logger.warning('%s: Do not use `fill=%s`, use a Polygon instead', self, cv.fill)
            for tag in self.tags:
                if tag.startswith(':'):  # Internal tags, forbid
                    raise ValueError(f'{self}: Invalid tag `{tag}`')
            for w in ('width', 'widthActive', 'widthDisabled'):
                wv = getattr(self, w)
                if wv is not None and wv <= 0:
                    raise ValueError(f'{self}: "{w}" is a distance')
            for tn in ('dash', 'dashActive', 'dashDisabled'):
                tv = getattr(self, tn)
                if tv is not None:
                    if any(v <= 0 or v > 255 for v in tv.pattern):
                        raise ValueError(f'{self}: "{tn}" distances have a range of ]0, 255]')
                    if tn != 'dash' and tv.offset != 0:
                        raise ValueError(f'{self}: "{tn}" does not support offsets, uses `dash` value')


@dataclass
class Polygon(DiagramElementSingle):
    '''Diagram Element: polygon.

    Represent a single regular polygon.

    There is no Python documentation, see ``Tk`` :tk:`canvas common options
    <canvas.htm#M99>` and :tk:`canvas polygon options <canvas.htm#M151>`. See
    also :tkinter_nmt:`NMT create polygon <create_polygon.html>` documentation.

    Args:
        points: Sequence of points to draw the polygon.
            Must have at least three points.
        color: Colour for outline and fill area, see `C` for colour
            specification.
        width: Width for outlines, in pixels.
            Optional, defaults to minimum line width.
        dash: Dashed outline setting.
            Optional, defaults to solid line.
        join: Outline join setting. Defaults to `Join.ROUND`.
        smooth: Outline smoothing setting.
            Optional, defaults to straight line.
        colorActive: ``color`` for active elements, that is, on mouse hover.
        widthActive: ``width`` for active elements, that is, on mouse hover.
        dashActive: ``dash`` for disabled elements.
            ``offset`` is not supported.
        colorDisabled: ``color`` for disabled elements.
        widthDisabled: ``width`` for disabled elements.
        dashDisabled: ``dash`` for disabled elements.
            ``offset`` is not supported.
        tags: Sequence of tags to apply to the element.
            Must not include any "internal tags", starting with ``:``.
    '''

    points: typing.Sequence[XY]
    color: C = field(default_factory=C)
    width: typing.Optional[int] = None
    dash: typing.Optional[D] = None  # TODO: Accept (int, int), `D(*x)`
    join: Join = Join.ROUND
    smooth: typing.Optional[Smooth] = None
    colorActive: C = field(default_factory=C)
    widthActive: typing.Optional[int] = None
    dashActive: typing.Optional[D] = None  # TODO: Accept (int, int), `D(*x)`
    colorDisabled: C = field(default_factory=C)
    widthDisabled: typing.Optional[int] = None
    dashDisabled: typing.Optional[D] = None  # TODO: Accept (int, int), `D(*x)`
    tags: typing.Sequence[str] = tuple()

    if __debug__:
        # Validate settings
        def __post_init__(self):
            if len(self.points) < 3:
                raise ValueError(f'{self}: A Polygon has at least three points')
            if self.smooth is None:
                if len(set(self.points)) != len(self.points):
                    logger.warning('%s: Repeated "points"', self)
            else:
                logger.warning('%s: Smoothing algorithm selection is not fully implemented', self)
            for tag in self.tags:
                if tag.startswith(':'):  # Internal tags, forbid
                    raise ValueError(f'{self}: Invalid tag `{tag}`')
            for w in ('width', 'widthActive', 'widthDisabled'):
                wv = getattr(self, w)
                if wv is not None and wv <= 0:
                    raise ValueError(f'{self}: "{w}" is a distance')
            for tn in ('dash', 'dashActive', 'dashDisabled'):
                tv = getattr(self, tn)
                if tv is not None:
                    if any(v <= 0 or v > 255 for v in tv.pattern):
                        raise ValueError(f'{self}: "{tn}" distances have a range of ]0, 255]')
                    if tn != 'dash' and tv.offset != 0:
                        raise ValueError(f'{self}: "{tn}" does not support offsets, uses `dash` value')


@dataclass
class Rectangle(DiagramElementSingle):
    '''Diagram Element: simple rectangle, parallel to the axes.

    Represent a simple rectangle, with sides parallel to the axes. If you need
    a rotated rectangle, use a `Polygon`.

    There is no Python documentation, see ``Tk`` :tk:`canvas common options
    <canvas.htm#M99>` and :tk:`canvas rectangle options <canvas.htm#M155>`. See
    also :tkinter_nmt:`NMT create rectangle <create_rectangle.html>` documentation.

    Args:
        topleft: The top left vertex (lower X and Y coordinates).
        botright: The bottom right vertex (higher X and Y coordinates).
        color: Colour for outline and fill area, see `C` for colour
            specification.
        width: Width for outlines, in pixels.
            Optional, defaults to minimum line width.
        dash: Dashed outline setting.
            Optional, defaults to solid line.
        colorActive: ``color`` for active elements, that is, on mouse hover.
        widthActive: ``width`` for active elements, that is, on mouse hover.
        dashActive: ``dash`` for disabled elements.
            ``offset`` is not supported.
        colorDisabled: ``color`` for disabled elements.
        widthDisabled: ``width`` for disabled elements.
        dashDisabled: ``dash`` for disabled elements.
            ``offset`` is not supported.
        tags: Sequence of tags to apply to the element.
            Must not include any "internal tags", starting with ``:``.
    '''
    topleft: XY
    botright: XY
    color: C = field(default_factory=C)
    width: typing.Optional[int] = None
    dash: typing.Optional[D] = None  # TODO: Accept (int, int), `D(*x)`
    colorActive: C = field(default_factory=C)
    widthActive: typing.Optional[int] = None
    dashActive: typing.Optional[D] = None  # TODO: Accept (int, int), `D(*x)`
    colorDisabled: C = field(default_factory=C)
    widthDisabled: typing.Optional[int] = None
    dashDisabled: typing.Optional[D] = None  # TODO: Accept (int, int), `D(*x)`
    tags: typing.Sequence[str] = tuple()

    if __debug__:
        # Validate settings
        def __post_init__(self):
            deltaV = self.topleft.vto(self.botright)
            if 0 in (deltaV.dx, deltaV.dy):
                raise ValueError(f'{self}: Must have size on both axes')
            if self.topleft.x > self.botright.x or self.topleft.y > self.botright.y:
                xy_tl = XY(min(self.topleft.x, self.botright.x), min(self.topleft.y, self.botright.y))
                xy_br = XY(max(self.topleft.x, self.botright.x), max(self.topleft.y, self.botright.y))
                raise ValueError(f'{self}: review coordinates: `topleft={xy_tl}, botright={xy_br}`')
            for tag in self.tags:
                if tag.startswith(':'):  # Internal tags, forbid
                    raise ValueError(f'{self}: Invalid tag `{tag}`')
            for w in ('width', 'widthActive', 'widthDisabled'):
                wv = getattr(self, w)
                if wv is not None and wv <= 0:
                    raise ValueError(f'{self}: "{w}" is a distance')
            for tn in ('dash', 'dashActive', 'dashDisabled'):
                tv = getattr(self, tn)
                if tv is not None:
                    if any(v <= 0 or v > 255 for v in tv.pattern):
                        raise ValueError(f'{self}: "{tn}" distances have a range of ]0, 255]')
                    if tn != 'dash' and tv.offset != 0:
                        raise ValueError(f'{self}: "{tn}" does not support offsets, uses `dash` value')

    @property
    def center(self) -> XY:
        '''Calculate the center of the rectangle.

        Note that since integer coordinates are used, this might be off from
        the "real" center by at most half pixel.
        '''
        return XY((self.topleft.x + self.botright.x) // 2, (self.topleft.y + self.botright.y) // 2)


@dataclass
class Ellipse(DiagramElementSingle):
    '''Diagram Element: simple ellipse, parallel to the axes.

    Represent a simple ellipse, with sides parallel to the axes. Remember that
    a circle is a special case for an ellipse, see `CircleCenter`.

    There is no Python documentation, see ``Tk`` :tk:`canvas common options
    <canvas.htm#M99>` and :tk:`canvas oval options <canvas.htm#M150>`. See
    also :tkinter_nmt:`NMT create oval <create_oval.html>` documentation.

    Args:
        topleft: The top left vertex (lower X and Y coordinates).
        botright: The bottom right vertex (higher X and Y coordinates).
        color: Colour for outline and fill area, see `C` for colour
            specification.
        width: Width for outlines, in pixels.
            Optional, defaults to minimum line width.
        dash: Dashed outline setting.
            Optional, defaults to solid line.
        colorActive: ``color`` for active elements, that is, on mouse hover.
        widthActive: ``width`` for active elements, that is, on mouse hover.
        dashActive: ``dash`` for disabled elements.
            ``offset`` is not supported.
        colorDisabled: ``color`` for disabled elements.
        widthDisabled: ``width`` for disabled elements.
        dashDisabled: ``dash`` for disabled elements.
            ``offset`` is not supported.
        tags: Sequence of tags to apply to the element.
            Must not include any "internal tags", starting with ``:``.
    '''
    topleft: XY
    botright: XY
    color: C = field(default_factory=C)
    width: typing.Optional[int] = None
    dash: typing.Optional[D] = None  # TODO: Accept (int, int), `D(*x)`
    colorActive: C = field(default_factory=C)
    widthActive: typing.Optional[int] = None
    dashActive: typing.Optional[D] = None  # TODO: Accept (int, int), `D(*x)`
    colorDisabled: C = field(default_factory=C)
    widthDisabled: typing.Optional[int] = None
    dashDisabled: typing.Optional[D] = None  # TODO: Accept (int, int), `D(*x)`
    tags: typing.Sequence[str] = tuple()

    if __debug__:
        # Validate settings
        def __post_init__(self):
            deltaV = self.topleft.vto(self.botright)
            if 0 in (deltaV.dx, deltaV.dy):
                raise ValueError(f'{self}: Must have size on both axes')
            if self.topleft.x > self.botright.x or self.topleft.y > self.botright.y:
                xy_tl = XY(min(self.topleft.x, self.botright.x), min(self.topleft.y, self.botright.y))
                xy_br = XY(max(self.topleft.x, self.botright.x), max(self.topleft.y, self.botright.y))
                raise ValueError(f'{self}: review coordinates: `topleft={xy_tl}, botright={xy_br}`')
            for tag in self.tags:
                if tag.startswith(':'):  # Internal tags, forbid
                    raise ValueError(f'{self}: Invalid tag `{tag}`')
            for w in ('width', 'widthActive', 'widthDisabled'):
                wv = getattr(self, w)
                if wv is not None and wv <= 0:
                    raise ValueError(f'{self}: "{w}" is a distance')
            for tn in ('dash', 'dashActive', 'dashDisabled'):
                tv = getattr(self, tn)
                if tv is not None:
                    if any(v <= 0 or v > 255 for v in tv.pattern):
                        raise ValueError(f'{self}: "{tn}" distances have a range of ]0, 255]')
                    if tn != 'dash' and tv.offset != 0:
                        raise ValueError(f'{self}: "{tn}" does not support offsets, uses `dash` value')

    @property
    def center(self) -> XY:
        '''Calculate the center of the ellipse.

        Note that since integer coordinates are used, this might be off from
        the "real" center by at most half pixel.
        '''
        return XY((self.topleft.x + self.botright.x) // 2, (self.topleft.y + self.botright.y) // 2)

    @property
    def leccentricity(self) -> numbers.Real:
        '''Calculate the linear eccentricity of the ellipse.

        This is a measure of how closer is the ellipse to a circle. ``0`` means
        it's a circle, any other number less than ``1`` means it's an ellipse.

        Returns:
            The linear eccentricity of the ellipse, as a floating point number.
        '''
        a = (self.botright.x - self.topleft.x) // 2
        b = (self.botright.y - self.topleft.y) // 2
        assert a > 0 or b > 0
        if a == b:
            # Circle
            return typing.cast(numbers.Real, 0)
        else:
            # Make sure `a` is the semi-major axis
            if b > a:
                a, b = b, a
            assert a > b
            return typing.cast(numbers.Real, math.sqrt((a + b) * (a - b)))

    def foci(self) -> typing.Tuple[XY, XY]:
        '''Calculate both focus points of the ellipse

        These are the points where any outline point is equidistant from both
        points.

        Note that since integer coordinates are used, this might be off from
        the "real" foci by at most half pixel.

        See Also:
            The `center` is the midpoint between these two. They all coincide
            if the ellipse is a circle.
        '''
        # TODO: Make sure this is correct, if the ellipse is "vertical"
        vC = VectorH(nround(self.leccentricity))
        return self.center - vC, self.center + vC


@dataclass
class Text(DiagramElementSingle):
    '''Diagram Element: text.

    Represent a text string anchored on a specific coordinate, possibly
    rotated.

    There is no Python documentation, see ``Tk`` :tk:`canvas common options
    <canvas.htm#M99>` and :tk:`canvas text options <canvas.htm#M156>`. See
    also :tkinter_nmt:`NMT create text <create_text.html>` documentation.

    Args:
        point: Anchor point to locate the text
        text: The text to draw
        color: Text colour, see `C` for colour specification.
            Considers only ``fill``.
        anchor: Where to anchor the text, related to ``point``.
        angle: Rotate the text, in degrees. Defaults to no rotation.
        justify: How to justify multi-line text. See `model.Justification`.
        colorActive: ``color`` for active elements, that is, on mouse hover.
        colorDisabled: ``color`` for disabled elements.
    '''
    # TODO: Create proper `Font` settings
    #       Do not document `font`, it's still a hack
    # TODO: Document how angle and achor interact.
    point: XY
    text: str
    color: C = field(default_factory=C)  # TODO: Accept single string, `C(fill=x)`
    anchor: model.CP = model.CP.center
    angle: numbers.Real = typing.cast(numbers.Real, 0.0)
    justify: model.Justification = model.Justification.Left
    font: typing.Any = None
    colorActive: C = field(default_factory=C)  # TODO: Accept single string, `C(fill=x)`
    colorDisabled: C = field(default_factory=C)  # TODO: Accept single string, `C(fill=x)`
    # TODO: Implement "lineWidth"?
    # Skip "underline"
    tags: typing.Sequence[str] = tuple()

    if __debug__:
        def __post_init__(self):
            if self.text == '':
                raise ValueError(f'{self}: Must have some text')
            for c in ('color', 'colorActive', 'colorDisabled'):
                cv = getattr(self, c)
                if cv.outline is not None and cv.fill is None:
                    logger.warning('%s: To paint text with `%s`, use "fill" exclusively', self, c)
            for tag in self.tags:
                if tag.startswith(':'):  # Internal tags, forbid
                    raise ValueError(f'{self}: Invalid tag `{tag}`')
            if self.angle < 0.0 or self.angle > 360.0:
                raise ValueError(f'{self}: Invalid angle `{self.angle}`')


@dataclass
class EllipseSection(DiagramElementSingle):
    '''Diagram Element: part of a larger `Ellipse`.

    Represent a section of a simple `Ellipse`.

    There is no Python documentation, see ``Tk`` :tk:`canvas common options
    <canvas.htm#M99>` and :tk:`canvas arc options <canvas.htm#M125>`. See
    also :tkinter_nmt:`NMT create arc <create_arc.html>` documentation.

    This is a "low level" diagram element, you should use one of its higher
    level elements: `ArcEllipse` or `PieEllipse`.

    Args:
        topleft: The top left vertex (lower X and Y coordinates).
        botright: The bottom right vertex (higher X and Y coordinates).
        style: Section style.
        rng: Section range. The start and end angles for the section. The
            angles are expressed in degrees, in a range between ``-360`` and
            ``360``.
        color: Colour for outline and fill area, see `C` for colour
            specification.
        width: Width for outlines, in pixels.
            Optional, defaults to minimum line width.
        dash: Dashed outline setting.
            Optional, defaults to solid line.
        colorActive: ``color`` for active elements, that is, on mouse hover.
        widthActive: ``width`` for active elements, that is, on mouse hover.
        dashActive: ``dash`` for disabled elements.
            ``offset`` is not supported.
        colorDisabled: ``color`` for disabled elements.
        widthDisabled: ``width`` for disabled elements.
        dashDisabled: ``dash`` for disabled elements.
            ``offset`` is not supported.
        tags: Sequence of tags to apply to the element.
            Must not include any "internal tags", starting with ``:``.

        .. note::

            For `ARC <EllipseSection_Style.ARC>` style, there is no fill area.
            This is checked in debug mode.
    '''
    topleft: XY
    botright: XY
    style: EllipseSection_Style
    rng: typing.Tuple[numbers.Real, numbers.Real]  # Start, End
    # Same as `Ellipse`
    color: C = field(default_factory=C)
    width: typing.Optional[int] = None
    dash: typing.Optional[D] = None  # TODO: Accept (int, int), `D(*x)`
    colorActive: C = field(default_factory=C)
    widthActive: typing.Optional[int] = None
    dashActive: typing.Optional[D] = None  # TODO: Accept (int, int), `D(*x)`
    colorDisabled: C = field(default_factory=C)
    widthDisabled: typing.Optional[int] = None
    dashDisabled: typing.Optional[D] = None  # TODO: Accept (int, int), `D(*x)`
    tags: typing.Sequence[str] = tuple()

    if __debug__:
        def __post_init__(self):
            if self.style == EllipseSection_Style.ARC:
                for c in ('color', 'colorActive', 'colorDisabled'):
                    cv = getattr(self, c)
                    if cv.fill is not None:
                        logger.warning('%s: Arc does not support "fill" on `%s`', self, c)
            astart, aend = self.rng
            for aname, avalue in (('start', astart), ('end', aend)):
                if avalue <= -360 or avalue >= 360:
                    logger.warning('%s: range for rng:%s is `]-360, 360[`', self, aname)
            assert 0 < self.extent < 360

    @property
    def extent(self) -> numbers.Real:
        '''Calculate the extent of the section.

        This is the delta between start and end.
        Expressed in degrees, between ``0`` and ``360``.

        .. note:

            This is a bit more complex than a simple difference between start
            and end angles, because both support negative values.
        '''
        astart, aend = self.rng
        assert isinstance(360 + aend - astart, typing.SupportsInt)
        aextent = (360 + aend - astart) % 360  # type: ignore[operator]
        assert isinstance(aextent, numbers.Real), f'Invalid Number: {aextent!r}'
        return aextent

# TODO: Implement `Image`


# # # Complex Elements
def DoubleMultiLine(*args,
                    widthSmall: int, deltaWidth: int = 2,
                    colorBig: C, colorSmall: C,
                    **kwargs,
                    ) -> DiagramElementMultiple:
    '''Draw two `MultiLine` on the same location, with different sizes.

    The "big" one is drawn first (on the back), with a larger ``deltaWidth``
    size.

    The size can be controlled using ``widthSmall`` and ``deltaWidth``.

    It's equivalent to three lines, like this::

       -------------
       BIG  size=w/D
       -------------
       small  size=w
       -------------
       BIG  size=w/D
       -------------

    This is their relation::

        w = widthSmall
        widthBig = deltaWidth * w
        D = 2 / (deltaWidth - 1)

    Examples::

        d = 2 ==> D = 2
        d = 3 ==> D = 1
        d = 4 ==> D = 2/3

    '''
    if 'color' in kwargs:
        warnings.warn('Do not use "color", use `colorBig` and `colorSmall`', stacklevel=2)
        kwargs.pop('color')
    if 'width' in kwargs:
        warnings.warn('Do not use "width", use `widthSmall` and `deltaWidth`', stacklevel=2)
        kwargs.pop('width')
    assert 'color' not in kwargs and 'width' not in kwargs
    widthBig = nround(deltaWidth * widthSmall)
    if __debug__:
        logger.debug('Width: widthSmall=%d widthBig=%d', widthSmall, widthBig)
    return DiagramElementMultiple(
        MultiLine(*args, color=colorBig, width=widthBig, **kwargs),      # type: ignore[misc]
        MultiLine(*args, color=colorSmall, width=widthSmall, **kwargs),  # type: ignore[misc]
    )


# # # Wrapper Elements
def Line(p1: XY, p2: XY, **kwargs) -> MultiLine:
    '''Draw a single line segment.

    Args:
        p1: First line segment vertex.
        p2: Second line segment vertex.
        kwargs: Passed to `MultiLine`.
    '''
    assert 'points' not in kwargs, 'Use `MultiLine` directly'
    return MultiLine((p1, p2), **kwargs)


def LineVector(p: XY, v: Vector, **kwargs) -> MultiLine:
    '''Draw a single line segment, from a point following a vector.

    Args:
        p: First line segment vertex.
        v: Vector to sum to ``p``, to obtain the second line segment vertex.
        kwargs: Passed to `MultiLine`.
    '''
    return MultiLine((p, p + v), **kwargs)


def ArcEllipse(**kwargs) -> EllipseSection:
    '''Draw a simple ellipse arc, parallel to the axes.

    The arguments are similar to `Ellipse`. Uses an `EllipseSection` with a
    static style (`ARC <EllipseSection_Style.ARC>`).

    Args:
        kwargs: Passed to `EllipseSection`
    '''
    assert 'style' not in kwargs, 'Use `EllipseSection` directly'
    kwargs['style'] = EllipseSection_Style.ARC
    return EllipseSection(**kwargs)


def PieEllipse(**kwargs) -> EllipseSection:
    '''Draw a "pie" slice of a simple ellipse, parallel to the axes.

    The arguments are similar to `Ellipse`. Uses an `EllipseSection` with a
    static style (`PIESLICE <EllipseSection_Style.PIESLICE>`).

    Args:
        kwargs: Passed to `EllipseSection`
    '''
    assert 'style' not in kwargs, 'Use `EllipseSection` directly'
    kwargs['style'] = EllipseSection_Style.PIESLICE
    return EllipseSection(**kwargs)


def RectangleCenter(c: XY, size_x: int, size_y: int, **kwargs) -> Rectangle:
    '''Draw a simple rectangle, from a center point and its size.

    Note that since integer coordinates are used, this might be off from
    the "real" center by at most half pixel.

    Args:
        c: Center point.
        size_x: Size of rectangle, side parallel to X axis.
        size_y: Size of rectangle, side parallel to Y axis.
        kwargs: Passed to `Rectangle`.
    '''
    assert 'topleft' not in kwargs and 'botright' not in kwargs, 'Use `Rectangle` directly'
    delta = Vector(size_x // 2, size_y // 2)
    return Rectangle(c - delta, c + delta, **kwargs)


def SquareCenter(c: XY, size: int, *args, **kwargs) -> Rectangle:
    '''Draw a simple square, from a center point and its size.

    Note that since integer coordinates are used, this might be off from
    the "real" center by at most half pixel.

    Args:
        c: Center point.
        size: Side of the square.
        kwargs: Passed to `Rectangle`.
    '''
    return RectangleCenter(c, size, size, *args, **kwargs)


def EllipseCenter(c: XY, a: int, b: int, **kwargs) -> Ellipse:
    '''Draw a simple ellipse, from a center point and its axes.

    Args:
        c: Center point.
        a: Semi-Axis parallel to X.
        b: Semi-Axis parallel to Y.
        kwargs: Passed to `Ellipse`.
    '''
    assert 'topleft' not in kwargs and 'botright' not in kwargs, 'Use `Ellipse` directly'
    axes_vector = Vector(a, b)
    return Ellipse(c - axes_vector, c + axes_vector, **kwargs)


def ArcEllipseCenter(c: XY, a: int, b: int, **kwargs) -> EllipseSection:
    '''Draw a simple ellipse arc, from a center point to its axes.

    Args:
        c: Center point.
        a: Semi-Axis parallel to X.
        b: Semi-Axis parallel to Y.
        kwargs: Passed to `ArcEllipse`.
    '''
    axes_vector = Vector(a, b)
    assert 'topleft' not in kwargs and 'botright' not in kwargs, 'Use `ArcEllipse` directly'
    return ArcEllipse(topleft=c - axes_vector, botright=c + axes_vector,
                      **kwargs)


def CircleCenter(c: XY, radius: int, **kwargs) -> Ellipse:
    '''Draw a circle, from a center point and its radius.

    Note that since integer coordinates are used, this might be off from
    the "real" radius by at most half pixel.

    Args:
        c: Center point
        radius: Circle radius.
        kwargs: Passed to `Ellipse`.
    '''
    assert radius == nround(radius)
    return EllipseCenter(c, a=radius, b=radius, **kwargs)


def ArcCircleCenter(c: XY, radius: int, **kwargs) -> EllipseSection:
    '''Draw a circle arc, from a center point and its radius.

    Note that since integer coordinates are used, this might be off from
    the "real" radius by at most half pixel.

    Args:
        c: Center point
        radius: Circle radius.
        kwargs: Passed to `ArcEllipse`.
    '''
    assert radius == nround(radius)
    return ArcEllipseCenter(c, a=radius, b=radius, **kwargs)
