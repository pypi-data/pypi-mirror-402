'''
Auto Layout capabilities.
'''
import logging
import typing
import math
import sys

import tkinter as tk

from . import model

logger = logging.getLogger(__name__)

# Automatic Layout
# - HORIZONTAL
# - VERTICAL
AUTO: str = 'auto'
HORIZONTAL = tk.HORIZONTAL
VERTICAL = tk.VERTICAL

LAYOUT_SYNONYMS: typing.Mapping[str, str] = {
    HORIZONTAL: '1x',  # 1 Row
    VERTICAL: 'x1',  # 1 Column
    AUTO: 'x',  # Square
}
# Multiples
# - Use the direction names directly? With a prefix?
LAYOUT_MULTIPLE: typing.Mapping[str, model.Direction] = {
    'R': model.Direction.E,
    'r': model.Direction.W,
    'H': model.Direction.H,
    'C': model.Direction.S,
    'c': model.Direction.N,
    'V': model.Direction.V,
}


def parse_amount(value):
    ''''''  # Internal, do not document
    # Allow 'x' to be replaced with the remaining widgets
    if value == 'x':
        return None
    else:
        int_value = int(value)
        if int_value == 0:
            raise ValueError('Layout Multiples: Invalid Value: %s' % value)
        return int_value


def do(layout_input: typing.Optional[str], amount: int) -> typing.Tuple[typing.Optional[str], typing.Iterable[model.GridCoordinates]]:
    # Pre-Process
    layout = None
    args: typing.Iterable[model.GridCoordinates] = iter([])
    if layout_input:
        layout = LAYOUT_SYNONYMS.get(layout_input, layout_input)
        assert layout is not None, f'Invalid Layout: {layout_input}'
    if __debug__:
        logger.debug('Initial Layout: %s', layout)
    # Do it!
    if layout:
        direction_names = tuple(d.name for d in model.Direction)
        if layout.startswith(('x', 'X')):
            auto_separator = layout[0]
            if layout[1:] in ('', *direction_names):  # TODO: assert
                square = math.ceil(math.sqrt(amount))
                logger.debug('  Layout: Square (%d)', square)
                layout = layout.replace(auto_separator, '%d%s%d' % (square, auto_separator, square), 1)
                logger.debug('        : %s', layout)
                # TODO: layout='%dx%d' (square, square)
        if layout.startswith(tuple(LAYOUT_MULTIPLE)):
            _type = layout[0]
            multiple_direction = LAYOUT_MULTIPLE[_type]
            logger.debug('  Layout: Multiples %s: %s', _type, multiple_direction)
            amounts = [parse_amount(v) for v in layout[1:].split(',')]
            args = multiple_direction.multiples(*amounts, amount=amount)
        elif 'x' in layout or 'X' in layout:
            auto_direction = model.Direction.S  # Default automatic Direction
            if any(layout.endswith(name) for name in direction_names):
                # Requires the Direction name to be 1 character long
                auto_direction = model.Direction[layout[-1]]
                layout = layout[:-1]
            auto_force: bool = 'X' in layout
            assert isinstance(auto_direction, model.Direction)
            if auto_force:
                auto_separator = 'X'
                assert 'x' not in layout
            else:
                auto_separator = 'x'
                assert 'X' not in layout
            rows, cols = [None if v == '' else int(v) for v in layout.split(auto_separator)]
            # At least one of `rows`/`cols` is not `None`
            if rows is None:
                assert cols is not None
                rows = math.ceil(amount / cols)
            if cols is None:
                assert rows is not None
                cols = math.ceil(amount / rows)
            grid_missing = rows * cols - amount
            if grid_missing > 0 and not auto_force:
                if grid_missing >= cols:
                    dcols = grid_missing // cols
                    logger.debug('        : -%d Columns', dcols)
                    cols -= dcols
                    grid_missing = rows * cols - amount
                    if __debug__:
                        if layout_input not in LAYOUT_SYNONYMS:
                            # This might be a spurious warning
                            logger.warning('%s: Non-automatic layout being unsquared: %d cols', layout_input, dcols)
                if grid_missing >= rows:
                    drows = grid_missing // rows
                    logger.debug('        : -%d Rows', drows)
                    rows -= drows
                    grid_missing = rows * cols - amount
                    if __debug__:
                        if layout_input not in LAYOUT_SYNONYMS:
                            # This might be a spurious warning
                            logger.warning('%s: Non-automatic layout being unsquared: %d rows', layout_input, drows)
            logger.debug('  Layout: Automatic Grid (%d%s%d%s)[%+d]', rows, auto_separator, cols, auto_direction.name, grid_missing)
            args = auto_direction.grid(rows, cols, amount=amount,
                                       auto_fill=not auto_force)
            # TODO: layout='%dx%d' (rows, cols)
        container_matrix = None  # For debug
        if __debug__:
            try:
                from defaultlist import defaultlist  # type: ignore
                container_matrix = defaultlist(lambda: defaultlist())
            except ImportError:
                pass  # Don't use if it doesn't exist
            logged_args = []  # Consume the iterator for logging ...
            for idx, arg in enumerate(args):
                logged_args.append(arg)
                if container_matrix is not None:  # Fill the widget locations
                    for drow in range(arg.rowspan):
                        for dcol in range(arg.columnspan):
                            container_matrix[arg.row + drow][arg.column + dcol] = idx
                else:
                    logger.debug('  | %s' % arg)
            if container_matrix is not None:
                cnt = math.ceil(math.log10(amount))
                for r in container_matrix:  # Print widget locations
                    assert isinstance(r, typing.Sequence)
                    logger.debug('  | %s', ' '.join(('x' * cnt if i is None else f'%0{cnt}d' % i for i in r)))
            args = iter(logged_args)  # ... and return a new iterator
    logger.debug('Final Layout: %s', layout)
    return layout, args


# TODO: Return a generator?
def gnested(nlayout: typing.Union[str, typing.Sequence[str]]) -> typing.Tuple[str, typing.Union[str, typing.Sequence[str]]]:
    '''Calculate the current and next layout, for nested widgets.

    Args:
        nlayout: The current layout.

    Returns:
        A tuple of ``this_layout`` (the current layout), and ``next_layout`` (the next layout level).
        ``next_layout`` is the input for this function on the next level.
    '''
    this_layout: str
    next_layout: typing.Union[str, typing.Sequence[str]]
    if isinstance(nlayout, str):
        this_layout = next_layout = nlayout
    else:
        if len(nlayout) > 0:
            this_layout = nlayout[0]
            next_layout = nlayout[1:]
        else:
            this_layout = next_layout = AUTO
    return this_layout, next_layout


if __name__ == '__main__':
    # import sys
    import argparse
    parser = argparse.ArgumentParser(description='tkmilan: Auto Layout')
    parser.add_argument('-v', '--verbose', dest='loglevel',
                        action='store_const', const=logging.DEBUG, default=logging.INFO,
                        help='Add more details to the standard error log')
    parser.add_argument('layout',
                        help='Layout String')
    parser.add_argument('amount', type=int,
                        help='Layout Amount')
    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel,
                        format='%(levelname)5.5s:%(funcName)s: %(message)s',
                        stream=sys.stderr)
    layout, lst = do(args.layout, args.amount)
    logger.info('Layout: %s', layout)
