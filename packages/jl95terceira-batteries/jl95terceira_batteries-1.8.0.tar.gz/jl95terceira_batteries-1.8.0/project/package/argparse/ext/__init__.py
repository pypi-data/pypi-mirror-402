import argparse as _argparse
import dataclasses as _dataclasses
import typing as _typing

from ... import *

class TypeConverter[T](_typing.Protocol):

    def __call__(self, value: str) -> T: ...

def _exc_str(msg:str) -> str:

    raise RuntimeError(msg)

@_dataclasses.dataclass
class Arg[T]:

    name_or_flags: list[str]
    type: TypeConverter[T]
    short: str | None = None
    action: str = ""
    nargs: int | str | None = None
    const: T|None = None
    default: T|None = None
    choices: list[T] | None = None
    required: bool = False
    help: str = ""
    metavar: str | None = None
    dest: str | None = None
    version: str = ''
    kwargs: dict[str, _typing.Any] = _dataclasses.field(default_factory=dict)

    def add_to(self, ap:_argparse.ArgumentParser):
        ap.add_argument(
            *self.name_or_flags,
            action=self.action,
            nargs=self.nargs,
            const=self.const,
            default=self.default,
            type=self.type,
            choices=self.choices,
            required=self.required,
            help=self.help,
            metavar=self.metavar,
            dest=self.dest,
            version=self.version,
            **self.kwargs)

    def get(self, ns:_argparse.Namespace) -> T | None:
        
        return getattr(ns, self.dest if self.dest is not None else \
                       (self.name_or_flags[0].lstrip('-').replace('-', '_')) if self.name_or_flags else \
                       _exc_str("Argument has no name or short form to derive destination attribute"))
