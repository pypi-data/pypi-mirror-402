from builtins import open
from pathlib import Path
from typing import AnyStr, Callable


def read_string(
    file: str | Path,
    /,
    *,
    encoding: str = "utf-8",
    size: int | None = None,
) -> str:
    """
    Args:
        file (str | Path): The file path.
        encoding (str):
            The encoding to use. Defaults to "utf-8".
        size (int | None):
            The number of characters to read.
            If None or negative, will read to EOF.
            Defaults to None.

    Returns:
        str: The string read from the file or descriptor.
    """
    with open(
        # constant
        mode="r",
        # parameter
        file=file,
        encoding=encoding,
        # later
        buffering=-1,
        errors=None,
        newline=None,  # universal
        closefd=True,
        opener=None,
    ) as f:
        data: str = f.read(size)
    f.close()
    return data


def read_binary(
    file: str | Path,
    /,
    *,
    size: int | None = None,
) -> bytes:
    """
    Args:
        file (str | Path): The file path.
        size (int | None):
            The number of bytes to read.
            If None or negative, will read to EOF.
            Defaults to None.

    Returns:
        bytes: The bytes read from the file or descriptor.
    """
    with open(
        # constant
        mode="rb",
        # parameter
        file=file,
        # later
        buffering=-1,
        closefd=True,
        opener=None,
    ) as f:
        data: bytes = f.read(size)
    f.close()
    return data


reader_function: dict[type, Callable] = {
    str: read_string,
    bytes: read_binary,
}


def read(
    file: str | Path,
    returns: type[AnyStr] = str,
    /,
) -> AnyStr:
    """
    Read file content. If str, assumes "utf-8" encoding.

    Args:
        file (str | Path): The file path.
        returns (type[AnyStr]): The type to return.

    Returns:
        AnyStr: The data as [str][] or [bytes][].
    """
    return reader_function[returns](file)


def write_string(
    file: str | Path,
    data: str,
    /,
    *,
    overwrite: bool = False,
    encoding: str = "utf-8",
) -> None:
    """
    Write a string to a file.

    Args:
        file (str | Path): The file path.
        data (str): The string data to write.
        overwrite (bool):
            If True, overwrite existing file.
            If False, raise error if file exists.
            Defaults to False.
        encoding (str): The encoding to use. Defaults to "utf-8".
    """
    with open(
        file=file,
        mode="w" if overwrite else "x",
        encoding=encoding,
        errors=None,
        newline=None,
        closefd=True,
        opener=None,
    ) as f:
        f.write(data)
    f.close()


def write_binary(
    file: str | Path,
    data: bytes,
    /,
    *,
    overwrite: bool = False,
) -> None:
    """
    Write bytes to a file.

    Args:
        file (str | Path): The file path.
        data (bytes): The bytes data to write.
        overwrite (bool):
            If True, overwrite existing file.
            If False, raise error if file exists.
            Defaults to False.
    """
    with open(
        file=file,
        mode="wb" if overwrite else "xb",
        buffering=-1,
        closefd=True,
        opener=None,
    ) as f:
        f.write(data)
    f.close()


writer_function: dict[type, Callable] = {
    str: write_string,
    bytes: write_binary,
}


def write(
    file: str | Path,
    data: str | bytes,
    *,
    overwrite: bool = False,
) -> None:
    """
    Write data to file.

    Args:
        file (str | Path): The file path.
        data (bytes): The data to write.
        overwrite (bool):
            If True, overwrite existing file.
            If False, raise error if file exists.
            Defaults to False.
    """
    writer_function[type(data)](file, data, overwrite=overwrite)


def append_string(
    file: str | Path,
    data: str,
    /,
    *,
    encoding: str = "utf-8",
) -> None:
    """
    Append a string to the end of a file.

    Args:
        file (str | Path): The file path.
        data (str): The string data to append.
        encoding (str): The encoding to use. Defaults to "utf-8".
    """
    with open(
        file=file,
        mode="a",
        encoding=encoding,
        errors=None,
        newline=None,
        closefd=True,
        opener=None,
    ) as f:
        f.write(data)
    f.close()


def append_binary(
    file: str | Path,
    data: bytes,
    /,
) -> None:
    """
    Append bytes to the end of a file.

    Args:
        file (str | Path): The file path.
        data (bytes): The bytes data to append.
    """
    with open(
        file=file,
        mode="ab",
        buffering=-1,
        closefd=True,
        opener=None,
    ) as f:
        f.write(data)
    f.close()


appender_function: dict[type, Callable] = {
    str: append_string,
    bytes: append_binary,
}


def append(
    file: str | Path,
    data: str | bytes,
    /,
) -> None:
    """
    Append data to the end of a file. If str, assumes "utf-8" encoding.

    Args:
        file (str | Path): The file path.
        data (str | bytes): The data to append.
    """
    appender_function[type(data)](file, data)


def insert_string(
    file: str | Path,
    data: str,
    /,
    *,
    position: int = 0,
    encoding: str = "utf-8",
) -> None:
    """
    Insert a string at a specific character position in a file.

    NOTE: This is *very* slow for large files and is not recommended.

    Args:
        file (str | Path): The file path.
        data (str): The string data to insert.
        position (int): The character position to insert at. Defaults to 0.
        encoding (str): The encoding to use. Defaults to "utf-8".
    """
    existing = read_string(file, encoding=encoding)
    new_content = existing[:position] + data + existing[position:]
    write_string(file, new_content, overwrite=True, encoding=encoding)


def insert_binary(
    file: str | Path,
    data: bytes,
    /,
    *,
    position: int = 0,
) -> None:
    """
    Insert bytes at a specific byte position in a file.

    NOTE: This is *very* slow for large files and is not recommended.

    Args:
        file (str | Path): The file path.
        data (bytes): The bytes data to insert.
        position (int): The byte position to insert at. Defaults to 0.
    """
    existing = read_binary(file)
    new_content = existing[:position] + data + existing[position:]
    write_binary(file, new_content, overwrite=True)


inserter_function: dict[type, Callable] = {
    str: insert_string,
    bytes: insert_binary,
}


def insert(
    file: str | Path,
    data: str | bytes,
    *,
    position: int = 0,
) -> None:
    """
    Insert data at a specific position in a file. If str, assumes "utf-8" encoding.

    NOTE: This is *very* slow for large files and is not recommended.

    Args:
        file (str | Path): The file path.
        data (str | bytes): The data to insert.
        position (int): The position to insert at (characters for str, bytes for bytes).
            Defaults to 0.
    """
    inserter_function[type(data)](file, data, position=position)
