from argparse import ArgumentParser
from typing import Iterable

from argser.consts import IGNORE
from argser.utils import str2bool


class Arg:
    """Keywords Argument"""
    def __init__(
        self,
        dest: str = None,
        default=None,
        type=None,
        nargs=None,
        aliases: Iterable[str] = (),
        help=None,
        metavar=None,
        action='store',
        # extra
        bool_flag=True,
        one_dash=False,
        **kwargs,
    ):
        """
        :param dest:
        :param default:
        :param type:
        :param nargs:
        :param aliases:
        :param help:
        :param bool_flag:
            if True then read bool from argument flag: `--arg` is True, `--no-arg` is False,
            otherwise check if arg value and truthy or falsy: `--arg 1` is True `--arg no` is False
        :param one_dash: use one dash for long names: `-name` instead of `--name`
        :param kwargs: extra arguments for `parser.add_argument`
        """
        self.dest = dest
        self.type = type
        self.default = default
        self.nargs = nargs
        self.aliases = aliases
        self.help = help
        self._metavar = metavar
        self.action = action
        # extra
        self.bool_flag = bool_flag
        self.one_dash = one_dash
        self.extra = kwargs

    def __str__(self):
        names = ', '.join(self.names())
        type_name = getattr(self.type, '__name__', None)
        return f"Arg({names}, type={type_name}, default={self.default!r})"

    def __repr__(self):
        return str(self)

    @property
    def metavar(self):
        if self._metavar:
            return self._metavar
        if self.dest:
            return self.dest[0].upper()

    def names(self, prefix=None):
        names = [self.dest, *self.aliases]
        if prefix:
            names = [f'{prefix}{n}' for n in names]
        for name in names:
            if len(name) == 1 or self.one_dash:
                yield f"-{name}"
            else:
                yield f"--{name}"

    def params(self, exclude=(), **kwargs):
        params = dict(
            dest=self.dest,
            default=self.default,
            type=self.type,
            nargs=self.nargs,
            help=self.help,
            metavar=self.metavar,
            action=self.action,
        )
        params.update(**kwargs)
        params.update(**self.extra)
        for key in exclude:
            params.pop(key)
        return {k: v for k, v in params.items() if v is not None}

    def inject_bool(self, parser: ArgumentParser):
        if self.bool_flag and self.nargs not in ('*', '+'):
            params = self.params(exclude=('type', 'nargs', 'metavar', 'action'))
            action = parser.add_argument(*self.names(), action='store_true', **params)
            params['help'] = IGNORE
            parser.add_argument(*self.names(prefix='no-'), action='store_false', **params)
            parser.set_defaults(**{self.dest: self.default})
        else:
            params = self.params(type=str2bool)
            parser.add_argument(*self.names(), **params)

    def inject(self, parser: ArgumentParser):
        if self.type is bool:
            return self.inject_bool(parser)
        params = self.params()
        action = params.get('action')
        if action in (
            'store_const', 'store_true', 'store_false', 'append_const', 'version', 'count'
        ) and 'type' in params:
            params.pop('type')
        if action in ('store_true', 'store_false', 'count', 'version') and 'metavar' in params:
            params.pop('metavar')
        parser.add_argument(*self.names(), **params)


class PosArg(Arg):
    """Positional Argument"""
    def __init__(self, **kwargs):
        kwargs.update(bool_flag=False)
        super().__init__(**kwargs)

    @property
    def metavar(self):
        if self._metavar:
            return self._metavar

    def params(self, exclude=(), **kwargs):
        exclude += ('dest',)
        return super().params(exclude=exclude, **kwargs)

    def names(self, prefix=None):
        return [self.dest]
