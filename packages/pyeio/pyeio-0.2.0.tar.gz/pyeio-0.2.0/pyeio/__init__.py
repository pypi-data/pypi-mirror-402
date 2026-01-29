from builtins import open
from importlib import import_module
from io import (
    DEFAULT_BUFFER_SIZE,
    SEEK_CUR,
    SEEK_END,
    SEEK_SET,
    BlockingIOError,
    BufferedIOBase,
    BufferedRandom,
    BufferedReader,
    BufferedRWPair,
    BufferedWriter,
    BytesIO,
    FileIO,
    IncrementalNewlineDecoder,
    IOBase,
    RawIOBase,
    StringIO,
    TextIOBase,
    TextIOWrapper,
    UnsupportedOperation,
    open_code,
    text_encoding,
)
from typing import TYPE_CHECKING

from pyeio.io import (
    append,
    read,
    write,
)

if TYPE_CHECKING:
    from pyeio import (
        json,
        toml,
        yaml,
    )

__all__ = [
    # passthrough
    "open",
    "DEFAULT_BUFFER_SIZE",
    "SEEK_CUR",
    "SEEK_END",
    "SEEK_SET",
    "BlockingIOError",
    "BufferedIOBase",
    "BufferedRandom",
    "BufferedReader",
    "BufferedRWPair",
    "BufferedWriter",
    "BytesIO",
    "FileIO",
    "IncrementalNewlineDecoder",
    "IOBase",
    "RawIOBase",
    "StringIO",
    "TextIOBase",
    "TextIOWrapper",
    "UnsupportedOperation",
    "open_code",
    "text_encoding",
    # custom
    "read",
    "write",
    "append",
    # formats
    "json",
    "toml",
    "yaml",
]


_dynamic_imports: dict[str, tuple[str, str]] = {
    "json": (__spec__.parent, "__module__"),
    "toml": (__spec__.parent, "__module__"),
    "yaml": (__spec__.parent, "__module__"),
}


def __getattr__(name: str) -> object:
    dynamic_attr = _dynamic_imports.get(name)
    if dynamic_attr is None:
        raise AttributeError(name)

    package, module_name = dynamic_attr

    if module_name == "__module__":
        result = import_module(f".{name}", package=package)
        globals()[name] = result
        return result
    else:
        module = import_module(module_name, package=package)
        result = getattr(module, name)
        g = globals()
        for k, (_, v_module_name) in _dynamic_imports.items():
            if v_module_name == module_name:
                g[k] = getattr(module, k)
        return result


def __dir__() -> list[str]:
    return __all__
