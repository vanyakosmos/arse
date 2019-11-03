import math
import re
import textwrap
from collections import defaultdict
from typing import List

from argser.consts import Args, SUB_COMMAND_MARK
from argser.utils import colors, vlen, args_to_dict


def stringify(args: Args, shorten=False):
    def pair(x):
        k, v = x
        if v is None:
            v = colors.red('-')
        else:
            if shorten:
                v = textwrap.shorten(str(v), width=20, placeholder='...')
            v = repr(v)
        return f"{colors.green(k)}={v}"

    pairs = ', '.join(map(pair, args_to_dict(args).items()))
    cls_name = colors.yellow(args.__class__.__name__)
    return f"{cls_name}({pairs})"


def _get_table(args: Args):
    data = []
    for key, value in args_to_dict(args).items():
        if hasattr(value.__class__, SUB_COMMAND_MARK):
            sub_data = _get_table(value)
            data.extend([(f"{key}__{k}", v) for k, v in sub_data])
        else:
            data.append((key, value))
    return data


def _merge_str_cols(columns: List[str], gap='   '):
    parts = [c.splitlines() for c in columns]
    res = []
    col_widths = [max(map(vlen, part)) for part in parts]

    # for each line
    for i in range(max(map(len, parts))):
        row = ''
        # iterate over columns
        for j, part in enumerate(parts):
            # get row of current column
            chunk = part[i] if i < len(part) else ''
            row += chunk + ' ' * (col_widths[j] - vlen(chunk))
            if j != len(parts) - 1:
                row += gap
        res.append(row)
    return '\n'.join(res)


def _get_cols_value(data, cols) -> int:
    if cols == 'auto':
        return math.ceil(len(data) / 9)
    if isinstance(cols, str):
        return int(cols)
    if not cols:
        return 1
    return cols


def _split_by_cols(data: list, cols):
    cols = _get_cols_value(data, cols)
    parts = []
    part_size = math.ceil(len(data) / cols)
    while data:
        parts.append(data[:part_size])
        data = data[part_size:]
    return parts


def _split_by_sub(data: list, cols=1):
    store = defaultdict(list)
    for key, value in data:
        m = re.match(r'^(.+)__.+', key)
        store[m and m[1]].append((key, value))
    res = []
    for sub in store.values():
        res.extend(_split_by_cols(sub, cols))
    return res


def _colorize(data, kwargs):
    h_arg, h_value = kwargs['headers']
    kwargs['headers'] = colors.yellow(h_arg), colors.yellow(h_value)
    for i, (key, value) in enumerate(data):
        if value is None:
            value = colors.red('-')
        else:
            value = str(value)
        data[i] = colors.green(key), value


def make_table(args: Args, preset=None, cols='sub-auto', gap='   ', shorten=False, **kwargs):
    from tabulate import tabulate
    kwargs.setdefault('headers', ['arg', 'value'])
    data = _get_table(args)

    _colorize(data, kwargs)
    # at this point all keys and values in data are strings

    for i, (key, value) in enumerate(data):
        if shorten:
            value = textwrap.shorten(value, width=40, placeholder='...')
        else:
            value = textwrap.shorten(value, width=400, placeholder='...')
            value = textwrap.fill(value, width=40)
        data[i] = key, value

    if preset == 'fancy':
        cols = 'sub-auto'
        gap = ' ~ '
        kwargs['tablefmt'] = 'fancy_grid'

    if isinstance(cols, str) and cols.startswith('sub'):
        m = re.match(r'sub-(.+)', cols)
        c = m and m[1] or 1
        parts = _split_by_sub(data, cols=c)
        parts = [tabulate(sub, **kwargs) for sub in parts]
        return _merge_str_cols(parts, gap)
    parts = _split_by_cols(data, cols)
    parts = [tabulate(sub, **kwargs) for sub in parts]
    return _merge_str_cols(parts, gap)


def print_args(args: Args, variant=None, print_fn=None, shorten=False, **kwargs):
    """
    Pretty print out data from :attr:`args`.

    :param args: some object with attributes
    :param variant:
        if 'table' - print arguments as table
        otherwise print arguments in one line
    :param print_fn:
    :param shorten: shorten long text (eg long default value)
    :param kwargs: additional kwargs for tabulate + some custom fields:
        cols: number of columns. Can be 'auto' - len(args)/N, int - just number of columns,
        'sub' / 'sub-auto' / 'sub-INT' - split by sub-commands,
        gap: string, space between tables/columns
    """
    if variant == 'table':
        s = make_table(args, shorten=shorten, **kwargs)
    else:
        s = stringify(args, shorten)
    print_fn = print_fn or print
    print_fn(s)
