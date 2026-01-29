from __future__ import annotations

from functools import lru_cache
from json import (
    detect_encoding,
    dump,
    dumps,
    load,
    loads,
)
from pathlib import Path
from typing import (
    Any,
    AnyStr,
    Callable,
    Literal,
    cast,
    overload,
)

import orjson
from orjson import (
    JSONDecodeError,
    JSONEncodeError,
)

from pyeio import io
from pyeio.annotations import (
    IncEx,
    JsonSerializable,
    OrJsonSerializable,
    PydanticModel,
    T_PydanticModel,
)

__all__ = [
    "read",
    "parse",
    "write",
    "serialize",
    "write_orjson",
    "write_pydantic",
    "serialize_orjson",
    "serialize_pydantic",
    "JSONEncodeError",
    "JSONDecodeError",
    "dump",
    "dumps",
    "load",
    "loads",
    "detect_encoding",
]


@lru_cache(maxsize=8)
def compute_orjson_opt_code(
    append_newline: bool = False,
    indent_two_spaces: bool = False,
    coerce_keys_to_str: bool = True,
    coerce_dataclasses: bool = True,
    coerce_datetimes: bool = True,
    coerce_builtin_subclasses: bool = True,
    coerce_numpy_arrays: bool = True,
    sort_keys: bool = False,
) -> int:
    """
    Computes an [orjson](https://github.com/ijl/orjson) OPT code.

    The following are omitted:

    - [OPT_STRICT_INTEGER](https://github.com/ijl/orjson?tab=readme-ov-file#opt_strict_integer)
    - [UTC_Z](https://github.com/ijl/orjson?tab=readme-ov-file#opt_utc_z)
    - [OPT_NAIVE_UTC](https://github.com/ijl/orjson?tab=readme-ov-file#opt_naive_utc)

    Also, currently microseconds are omitted for datetime objects.
    """
    return (
        (append_newline * orjson.OPT_APPEND_NEWLINE)
        | (indent_two_spaces * orjson.OPT_INDENT_2)
        | (coerce_keys_to_str * orjson.OPT_NON_STR_KEYS)
        | orjson.OPT_OMIT_MICROSECONDS  # constant
        | (not coerce_dataclasses * orjson.OPT_PASSTHROUGH_DATACLASS)
        | (not coerce_datetimes * orjson.OPT_PASSTHROUGH_DATETIME)
        | (not coerce_builtin_subclasses * orjson.OPT_PASSTHROUGH_SUBCLASS)
        | (coerce_numpy_arrays * orjson.OPT_SERIALIZE_NUMPY)
        | (sort_keys * orjson.OPT_SORT_KEYS)
    )


@overload
def parse(data: str | bytes, /) -> Any: ...
@overload
def parse(
    data: str | bytes,
    model: type[T_PydanticModel],
    /,
    strict: bool | None = None,
    context: Any | None = None,
    by_alias: bool | None = None,
    by_name: bool | None = None,
) -> T_PydanticModel: ...
def parse(
    data: str | bytes,
    model: type[T_PydanticModel] | None = None,
    /,
    strict: bool | None = None,
    context: Any | None = None,
    by_alias: bool | None = None,
    by_name: bool | None = None,
) -> Any | T_PydanticModel:
    """
    Parses JSON data into a Python object or validates it against a Pydantic model.

    When no model is provided, parses JSON data into standard Python types.
    When a model is provided, validates the JSON data against the Pydantic model
    and returns an instance of that model.

    Args:
        data (str | bytes): JSON data as string or bytes to be parsed.
        model (type[T_Pydantic] | None): Optional Pydantic model class for validation.
        strict (bool | None): Whether to use strict validation mode.
        context (Any | None): Additional context for validation.
        by_alias (bool | None): Whether to use field aliases during validation.
        by_name (bool | None): Whether to use field names during validation.

    Returns:
        JsonValue | T_Pydantic: Parsed JSON data as Python objects, or a validated
            Pydantic model instance if model is provided.
    """
    if model is None:
        return orjson.loads(data)
    else:
        return model.model_validate_json(
            json_data=data,
            strict=strict,
            context=context,
            by_alias=by_alias,
            by_name=by_name,
        )


@overload
def read(file: str | Path, /) -> Any: ...
@overload
def read(
    file: str | Path,
    model: type[T_PydanticModel],
    /,
    strict: bool | None = None,
    context: Any | None = None,
    by_alias: bool | None = None,
    by_name: bool | None = None,
) -> T_PydanticModel: ...
def read(
    file: str | Path,
    model: type[T_PydanticModel] | None = None,
    /,
    strict: bool | None = None,
    context: Any | None = None,
    by_alias: bool | None = None,
    by_name: bool | None = None,
) -> Any | T_PydanticModel:
    """
    Reads and parses JSON data from a file into a Python object or validates it against a Pydantic model.

    When no model is provided, reads and parses JSON data from file into standard Python types.
    When a model is provided, validates the JSON data against the Pydantic model
    and returns an instance of that model.

    Args:
        file (str | Path): Path to the JSON file to be read.
        model (type[T_PydanticModel] | None): Optional Pydantic model class for validation.
        strict (bool | None): Whether to use strict validation mode.
        context (Any | None): Additional context for validation.
        by_alias (bool | None): Whether to use field aliases during validation.
        by_name (bool | None): Whether to use field names during validation.

    Returns:
        Any | T_PydanticModel: Parsed JSON data as Python objects, or a validated
            Pydantic model instance if model is provided.
    """
    content: bytes = io.read_binary(file)
    if model is None:
        return orjson.loads(content)
    else:
        return model.model_validate_json(
            content,
            strict=strict,
            context=context,
            by_alias=by_alias,
            by_name=by_name,
        )


def serialize_orjson(
    data: OrJsonSerializable,
    returns: type[AnyStr] = bytes,
    encoding: str = "utf-8",
    indent: bool = False,
    fallback: Callable[[Any], Any] | None = None,
    *,
    append_newline: bool = False,
    coerce_keys_to_str: bool = True,
    coerce_dataclasses: bool = True,
    coerce_datetimes: bool = True,
    coerce_builtin_subclasses: bool = True,
    coerce_numpy_arrays: bool = True,
    sort_keys: bool = False,
) -> AnyStr:
    """
    Serializes data to JSON using orjson with configurable options.

    Converts Python objects to JSON format using orjson's high-performance
    serialization with extensive customization options for handling various
    data types and formatting preferences.

    Args:
        data (OrJsonSerializable): The data to serialize to JSON.
        returns (type[AnyStr]): Return type, either bytes or str.
        encoding (str): Character encoding to use when returning str.
        indent (bool): Whether to indent the output with 2 spaces.
        fallback (Callable[[Any], Any] | None): Function to handle non-serializable objects.
        append_newline (bool): Whether to append a newline to the output.
        coerce_keys_to_str (bool): Whether to coerce non-string keys to strings.
        coerce_dataclasses (bool): Whether to serialize dataclasses automatically.
        coerce_datetimes (bool): Whether to serialize datetime objects automatically.
        coerce_builtin_subclasses (bool): Whether to serialize builtin subclasses automatically.
        coerce_numpy_arrays (bool): Whether to serialize numpy arrays automatically.
        sort_keys (bool): Whether to sort dictionary keys in output.

    Returns:
        AnyStr: JSON data as bytes or string based on returns parameter.

    Raises:
        TypeError: If returns parameter is not bytes or str.

    ??? tip "Optimized JSON Serialization"

        If there's a large volume of data being processed (read/write),
        you should use the `serialize_orjson` methods and adjust the parameters accordingly:

        **For maximum performance:**

        - Set `coerce_keys_to_str=False` if all dict keys are already strings
        - Set `coerce_dataclasses=False` if no dataclasses are present
        - Set `coerce_datetimes=False` if no datetime objects are present
        - Set `coerce_builtin_subclasses=False` if no subclasses of str/int/dict/list are present
        - Set `coerce_numpy_arrays=False` if no numpy arrays are present
        - Avoid `sort_keys=True` unless deterministic output is required (substantial performance penalty)
        - Set `indent=False` for production (pretty-printing is slower and increases output size)

        **For specific data types:**

        - **Numpy arrays**: Enable `coerce_numpy_arrays=True` for native serialization (10-14x faster than json)
        - **Non-string keys**: Enable `coerce_keys_to_str=True` for UUID, datetime, or numeric keys
        - **Dataclasses**: Keep `coerce_dataclasses=True` (40-50x faster than other libraries)
        - **Datetime objects**: Use `coerce_datetimes=True` for RFC 3339 format with UTC timezone handling

        **Memory optimization:**

        - Use `returns=bytes` to avoid UTF-8 decoding overhead
        - Set `append_newline=True` instead of concatenating `+ "\\n"` (avoids copying immutable bytes)

        **For deterministic output:**

        - Use `sort_keys=True` only when needed for hashing or tests
        - Consider caching sorted results if used repeatedly

        Example for high-performance numpy serialization:

        ```python
        serialize_orjson(
            data,
            returns=bytes,
            coerce_numpy_arrays=True,
            coerce_keys_to_str=False,  # if keys are already strings
            sort_keys=False,
            indent=False,
        )
        ```
    """
    opt_code = compute_orjson_opt_code(
        append_newline=append_newline,
        indent_two_spaces=indent,
        coerce_keys_to_str=coerce_keys_to_str,
        coerce_dataclasses=coerce_dataclasses,
        coerce_datetimes=coerce_datetimes,
        coerce_builtin_subclasses=coerce_builtin_subclasses,
        coerce_numpy_arrays=coerce_numpy_arrays,
        sort_keys=sort_keys,
    )
    ser_data: bytes = orjson.dumps(
        data,
        default=fallback,
        option=opt_code,
    )

    if returns is bytes:
        return cast(AnyStr, ser_data)
    elif returns is str:
        return cast(AnyStr, ser_data.decode(encoding))
    else:
        raise TypeError(returns)


def serialize_pydantic(
    data: PydanticModel,
    returns: type[AnyStr] = bytes,
    encoding: str = "utf-8",
    indent: bool = False,
    fallback: Callable[[Any], Any] | None = None,
    *,
    include: IncEx | None = None,
    exclude: IncEx | None = None,
    context: Any | None = None,
    by_alias: bool | None = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    round_trip: bool = False,
    warnings: bool | Literal["none", "warn", "error"] = True,
    serialize_as_any: bool = False,
) -> AnyStr:
    """
    Serializes a Pydantic model instance to JSON format.

    Converts a Pydantic model to JSON string or bytes with configurable
    serialization options including field filtering, encoding preferences,
    and output formatting.

    Args:
        data (Pydantic): The Pydantic model instance to serialize.
        returns (type[AnyStr]): Return type, either str or bytes.
        encoding (str): Character encoding for bytes output.
        indent (bool): Whether to indent JSON output for readability.
        fallback (Callable[[Any], Any] | None): Function to handle non-serializable objects.
        include (IncEx | None): Fields to include in serialization.
        exclude (IncEx | None): Fields to exclude from serialization.
        context (Any | None): Additional context for serialization.
        by_alias (bool | None): Whether to use field aliases in output.
        exclude_unset (bool): Whether to exclude fields that weren't explicitly set.
        exclude_defaults (bool): Whether to exclude fields with default values.
        exclude_none (bool): Whether to exclude fields with None values.
        round_trip (bool): Whether to enable round-trip serialization.
        warnings (bool | Literal["none", "warn", "error"]): Warning configuration.
        serialize_as_any (bool): Whether to serialize using Any type handling.

    Returns:
        AnyStr: Serialized JSON data as string or bytes based on returns parameter.
    """
    ser_data: str = data.model_dump_json(
        indent=2 if indent else None,
        include=include,
        exclude=exclude,
        context=context,
        by_alias=by_alias,
        exclude_unset=exclude_unset,
        exclude_defaults=exclude_defaults,
        exclude_none=exclude_none,
        round_trip=round_trip,
        warnings=warnings,
        fallback=fallback,
        serialize_as_any=serialize_as_any,
    )
    if returns is str:
        return cast(AnyStr, ser_data)
    elif returns is bytes:
        return cast(AnyStr, ser_data.encode(encoding))
    else:
        raise TypeError(returns)


def serialize(
    data: JsonSerializable,
    returns: type[AnyStr] = str,
    encoding: str = "utf-8",
    indent: bool = False,
    fallback: Callable[[Any], Any] | None = None,
    **kwargs,
) -> AnyStr:
    """
    Serializes JSON-compatible data to string or bytes format.

    Automatically detects whether the data is a Pydantic model and routes
    to the appropriate serialization function. Uses orjson for general data
    and Pydantic's built-in serialization for models.

    Args:
        data (JsonSerializable): The data to serialize (Pydantic model or general JSON data).
        returns (type[AnyStr]): Return type, either str or bytes.
        encoding (str): Character encoding for bytes output.
        indent (bool): Whether to indent JSON output for readability.
        fallback (Callable[[Any], Any] | None): Function to handle non-serializable objects.

    Kwargs:
        Additional keyword arguments passed to the specific serializer.

    Returns:
        AnyStr: Serialized JSON data as string or bytes based on returns parameter.
    """
    if hasattr(data, "__pydantic_core_schema__"):
        return serialize_pydantic(
            data,  # type: ignore
            returns,
            encoding,
            indent,
            fallback,
            **kwargs,
        )
    else:
        return serialize_orjson(
            data,
            returns,
            encoding,
            indent,
            fallback,
            **kwargs,
        )


def write_orjson(
    file: str | Path,
    data: OrJsonSerializable,
    overwrite: bool = False,
    indent: bool = False,
    fallback: Callable[[Any], Any] | None = None,
    *,
    append_newline: bool = False,
    coerce_keys_to_str: bool = True,
    coerce_dataclasses: bool = True,
    coerce_datetimes: bool = True,
    coerce_builtin_subclasses: bool = True,
    coerce_numpy_arrays: bool = True,
    sort_keys: bool = False,
) -> None:
    """
    Writes data to a JSON file using orjson serialization.

    Serializes data using orjson with configurable options and writes the
    result to a file. Provides control over type coercion, formatting,
    and output behavior.

    Args:
        file (str | Path): Path to the output file.
        data (OrJsonSerializable): The data to serialize and write.
        overwrite (bool): Whether to overwrite existing files.
        indent (bool): Whether to indent JSON output for readability.
        fallback (Callable[[Any], Any] | None): Function to handle non-serializable objects.
        append_newline (bool): Whether to append a newline to the output.
        coerce_keys_to_str (bool): Whether to coerce dictionary keys to strings.
        coerce_dataclasses (bool): Whether to serialize dataclasses.
        coerce_datetimes (bool): Whether to serialize datetime objects.
        coerce_builtin_subclasses (bool): Whether to serialize built-in type subclasses.
        coerce_numpy_arrays (bool): Whether to serialize numpy arrays.
        sort_keys (bool): Whether to sort dictionary keys in output.

    Returns:
        None
    """
    ser_data = serialize_orjson(
        data=data,
        fallback=fallback,
        append_newline=append_newline,
        indent=indent,
        coerce_keys_to_str=coerce_keys_to_str,
        coerce_dataclasses=coerce_dataclasses,
        coerce_datetimes=coerce_datetimes,
        coerce_builtin_subclasses=coerce_builtin_subclasses,
        coerce_numpy_arrays=coerce_numpy_arrays,
        sort_keys=sort_keys,
    )
    io.write_binary(
        file,
        ser_data,
        overwrite=overwrite,
    )


def write_pydantic(
    file: str | Path,
    data: PydanticModel,
    overwrite: bool = False,
    indent: bool = False,
    fallback: Callable[[Any], Any] | None = None,
    *,
    include: IncEx | None = None,
    exclude: IncEx | None = None,
    context: Any | None = None,
    by_alias: bool | None = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    round_trip: bool = False,
    warnings: bool | Literal["none", "warn", "error"] = True,
    serialize_as_any: bool = False,
) -> None:
    """
    Writes a Pydantic model to a JSON file.

    Serializes a Pydantic model using its built-in JSON serialization
    capabilities and writes the result to a file with configurable
    field filtering and output options.

    Args:
        file (str | Path): Path to the output file.
        data (PydanticModel): The Pydantic model instance to serialize and write.
        overwrite (bool): Whether to overwrite existing files.
        indent (bool): Whether to indent JSON output for readability.
        fallback (Callable[[Any], Any] | None): Function to handle non-serializable objects.
        include (IncEx | None): Fields to include in serialization.
        exclude (IncEx | None): Fields to exclude from serialization.
        context (Any | None): Additional context for serialization.
        by_alias (bool | None): Whether to use field aliases in output.
        exclude_unset (bool): Whether to exclude fields that weren't explicitly set.
        exclude_defaults (bool): Whether to exclude fields with default values.
        exclude_none (bool): Whether to exclude fields with None values.
        round_trip (bool): Whether to enable round-trip serialization.
        warnings (bool | Literal["none", "warn", "error"]): Warning configuration.
        serialize_as_any (bool): Whether to serialize using Any type handling.

    Returns:
        None
    """
    ser_data = serialize_pydantic(
        data=data,
        indent=indent,
        include=include,
        exclude=exclude,
        context=context,
        by_alias=by_alias,
        exclude_unset=exclude_unset,
        exclude_defaults=exclude_defaults,
        exclude_none=exclude_none,
        round_trip=round_trip,
        warnings=warnings,
        fallback=fallback,
        serialize_as_any=serialize_as_any,
    )
    io.write_binary(
        file,
        ser_data,
        overwrite=overwrite,
    )


def write(
    file: str | Path,
    data: JsonSerializable,
    overwrite: bool = False,
    indent: bool = False,
    fallback: Callable[[Any], Any] | None = None,
    **kwargs,
) -> None:
    """
    Writes data to a JSON file using automatic serializer detection.

    Automatically detects whether the data is a Pydantic model and routes
    to the appropriate write function. Uses a heuristic to check for Pydantic
    models to avoid import costs.

    Args:
        file (str | Path): Path to the output file.
        data (JsonSerializable): The data to serialize and write.
        overwrite (bool): Whether to overwrite existing files.
        indent (bool): Whether to indent JSON output for readability.
        fallback (Callable[[Any], Any] | None): Function to handle non-serializable objects.

    Kwargs:
        Additional keyword arguments passed to the specific writer.

    Returns:
        None
    """
    if hasattr(data, "__pydantic_core_schema__"):
        write_pydantic(
            file,
            data,  # type: ignore
            overwrite,
            indent,
            fallback,
            **kwargs,
        )
    else:
        write_orjson(
            file,
            data,
            overwrite,
            indent,
            fallback,
            **kwargs,
        )
