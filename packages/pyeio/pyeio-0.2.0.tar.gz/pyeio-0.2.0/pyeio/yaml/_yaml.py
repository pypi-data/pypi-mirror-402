from __future__ import annotations

from pathlib import Path
from typing import (
    Any,
    AnyStr,
    Literal,
    TypeAlias,
    cast,
    overload,
)

import yaml
from yaml.dumper import Dumper as UnsafeDumper
from yaml.dumper import SafeDumper
from yaml.loader import (
    FullLoader,
    SafeLoader,
    UnsafeLoader,
)

from pyeio import io
from pyeio.annotations import (
    IncEx,
    PydanticEncodingWarnings,
    PydanticModel,
    T_PydanticModel,
    YamlSerializable,
    YamlValue,
)

LoaderType: TypeAlias = type[FullLoader | SafeLoader | UnsafeLoader]

LoaderName: TypeAlias = Literal["full", "safe", "unsafe"] | str

LOADER_MAP: dict[LoaderName, LoaderType] = {
    "full": FullLoader,
    "safe": SafeLoader,
    "unsafe": UnsafeLoader,
}

DumperType = type[SafeDumper | UnsafeDumper]

DumperName: TypeAlias = Literal["safe", "unsafe"] | str

DUMPER_MAP: dict[DumperName, DumperType] = {
    "safe": SafeDumper,
    "unsafe": UnsafeDumper,
}


@overload
def parse(data: str | bytes, /, *, loader: LoaderName) -> Any: ...
@overload
def parse(
    data: str | bytes,
    model: type[T_PydanticModel],
    /,
    strict: bool | None = None,
    context: Any | None = None,
    by_alias: bool | None = None,
    by_name: bool | None = None,
    *,
    loader: LoaderName,
) -> T_PydanticModel: ...
def parse(
    data: str | bytes,
    model: type[T_PydanticModel] | None = None,
    /,
    strict: bool | None = None,
    context: Any | None = None,
    by_alias: bool | None = None,
    by_name: bool | None = None,
    *,
    loader: LoaderName,
) -> Any | T_PydanticModel:
    """
    Parses YAML data into a Python object or validates it against a Pydantic model.

    When no model is provided, parses YAML data into standard Python types.
    When a model is provided, validates the YAML data against the Pydantic model
    and returns an instance of that model.

    Args:
        data (StrOrBytes): YAML data as string or bytes to be parsed.
        model (type[T_Pydantic] | None): Optional Pydantic model class for validation.
        strict (bool | None): Whether to use strict validation mode.
        context (Any | None): Additional context for validation.
        by_alias (bool | None): Whether to use field aliases during validation.
        by_name (bool | None): Whether to use field names during validation.
        loader (Loader): The name of the YAML loader class to use.

    Returns:
        Any | T_Pydantic: Parsed YAML data as Python objects, or a validated
            Pydantic model instance if model is provided.
    """
    parsed_data = yaml.load(data, Loader=LOADER_MAP[loader])

    if model is None:
        return parsed_data
    else:
        return model.model_validate(
            parsed_data,
            strict=strict,
            context=context,
            by_alias=by_alias,
            by_name=by_name,
        )


@overload
def read(file: str | Path, /, *, loader: LoaderName) -> YamlValue: ...
@overload
def read(
    file: str | Path,
    model: type[T_PydanticModel],
    /,
    strict: bool | None = None,
    context: Any | None = None,
    by_alias: bool | None = None,
    by_name: bool | None = None,
    *,
    loader: LoaderName,
) -> T_PydanticModel: ...
def read(
    file: str | Path,
    model: type[T_PydanticModel] | None = None,
    /,
    strict: bool | None = None,
    context: Any | None = None,
    by_alias: bool | None = None,
    by_name: bool | None = None,
    *,
    loader: LoaderName,
) -> YamlValue | T_PydanticModel:
    """
    Reads and parses YAML data from a file into a Python object or validates it against a Pydantic model.

    When no model is provided, reads and parses YAML data from file into standard Python types.
    When a model is provided, validates the YAML data against the Pydantic model
    and returns an instance of that model.

    Args:
        file (str | Path): Path to the YAML file to be read.
        model (type[T_Pydantic] | None): Optional Pydantic model class for validation.
        strict (bool | None): Whether to use strict validation mode.
        context (Any | None): Additional context for validation.
        by_alias (bool | None): Whether to use field aliases during validation.
        by_name (bool | None): Whether to use field names during validation.
        loader (Loader): The name of the YAML loader class to use.

    Returns:
        YamlValue | T_Pydantic: Parsed YAML data as Python objects, or a validated
            Pydantic model instance if model is provided.
    """
    content: bytes = io.read_binary(file)
    return parse(
        content,
        model,  # type: ignore
        strict=strict,
        context=context,
        by_alias=by_alias,
        by_name=by_name,
        loader=loader,
    )


def serialize_pyyaml(
    data: YamlValue,
    returns: type[AnyStr] = str,
    encoding: str = "utf-8",
    *,
    dumper: DumperName = "safe",
    default_style: str | None = None,
    default_flow_style: bool = False,
    canonical: bool = False,
    indent: int | None = None,
    width: int | None = None,
    allow_unicode: bool | None = None,
    line_break: str | None = None,
    sort_keys: bool = True,
) -> AnyStr:
    """
    Serializes data to YAML format with configurable options.

    Converts Python objects to YAML format using PyYAML with extensive
    customization options for handling formatting preferences.

    Args:
        data (YamlValue): The data to serialize to YAML.
        returns (type[AnyStr]): Return type, either str or bytes.
        encoding (str): Character encoding to use when returning bytes.
        dumper (DumperName): YAML dumper class to use.
        default_style (str | None): Default style for scalars.
        default_flow_style (bool): Whether to use flow style by default.
        canonical (bool): Whether to produce canonical YAML.
        indent (int | None): Number of spaces for indentation.
        width (int | None): Maximum line width.
        allow_unicode (bool | None): Whether to allow unicode characters.
        line_break (str | None): Line break character(s) to use.
        sort_keys (bool): Whether to sort dictionary keys in output.

    Returns:
        AnyStr: YAML data as string or bytes based on returns parameter.

    Raises:
        TypeError: If returns parameter is not str or bytes.
    """
    ser_data: str = yaml.dump(
        data,
        Dumper=DUMPER_MAP[dumper],
        default_style=default_style,
        default_flow_style=default_flow_style,
        canonical=canonical,
        indent=indent,
        width=width,
        allow_unicode=allow_unicode,
        line_break=line_break,
        sort_keys=sort_keys,
    )

    if returns is str:
        return cast(AnyStr, ser_data)
    elif returns is bytes:
        return cast(AnyStr, ser_data.encode(encoding))
    else:
        raise TypeError(returns)


def serialize_pydantic(
    data: PydanticModel,
    returns: type[AnyStr] = str,
    encoding: str = "utf-8",
    *,
    dumper: DumperName = "safe",
    default_style: str | None = None,
    default_flow_style: bool = False,
    canonical: bool = False,
    indent: int | None = None,
    width: int | None = None,
    allow_unicode: bool | None = None,
    line_break: str | None = None,
    sort_keys: bool = True,
    include: IncEx | None = None,
    exclude: IncEx | None = None,
    context: Any | None = None,
    by_alias: bool | None = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    round_trip: bool = False,
    warnings: bool | PydanticEncodingWarnings = True,
    serialize_as_any: bool = False,
) -> AnyStr:
    """
    Serializes a Pydantic model instance to YAML format.

    Converts a Pydantic model to YAML string or bytes with configurable
    serialization options including field filtering, encoding preferences,
    and output formatting.

    Args:
        data (Pydantic): The Pydantic model instance to serialize.
        returns (type[AnyStr]): Return type, either str or bytes.
        encoding (str): Character encoding for bytes output.
        dumper (DumperName): The YAML dumper class to use.
        default_style (str | None): Default style for scalars.
        default_flow_style (bool): Whether to use flow style by default.
        canonical (bool): Whether to produce canonical YAML.
        indent (int | None): Number of spaces for indentation.
        width (int | None): Maximum line width.
        allow_unicode (bool | None): Whether to allow unicode characters.
        line_break (str | None): Line break character(s) to use.
        sort_keys (bool): Whether to sort dictionary keys in output.
        include (IncEx | None): Fields to include in serialization.
        exclude (IncEx | None): Fields to exclude from serialization.
        context (Any | None): Additional context for serialization.
        by_alias (bool | None): Whether to use field aliases in output.
        exclude_unset (bool): Whether to exclude fields that weren't explicitly set.
        exclude_defaults (bool): Whether to exclude fields with default values.
        exclude_none (bool): Whether to exclude fields with None values.
        round_trip (bool): Whether to enable round-trip serialization.
        warnings (bool | PydanticEncodingWarnings): Warning configuration.
        serialize_as_any (bool): Whether to serialize using Any type handling.

    Returns:
        AnyStr: Serialized YAML data as string or bytes based on returns parameter.
    """
    # First convert Pydantic model to dict
    model_dict = data.model_dump(
        mode="json",
        include=include,
        exclude=exclude,
        context=context,
        by_alias=by_alias,
        exclude_unset=exclude_unset,
        exclude_defaults=exclude_defaults,
        exclude_none=exclude_none,
        round_trip=round_trip,
        warnings=warnings,
        serialize_as_any=serialize_as_any,
    )

    # Then serialize the dict to YAML
    ser_data: str = yaml.dump(
        model_dict,
        Dumper=DUMPER_MAP[dumper],
        default_style=default_style,
        default_flow_style=default_flow_style,
        canonical=canonical,
        indent=indent,
        width=width,
        allow_unicode=allow_unicode,
        line_break=line_break,
        sort_keys=sort_keys,
    )

    if returns is str:
        return cast(AnyStr, ser_data)
    elif returns is bytes:
        return cast(AnyStr, ser_data.encode(encoding))
    else:
        raise TypeError(returns)


def serialize(
    data: YamlSerializable,
    returns: type[AnyStr] = str,
    encoding: str = "utf-8",
    **kwargs,
) -> AnyStr:
    """
    Serializes YAML-compatible data to string or bytes format.

    Automatically detects whether the data is a Pydantic model and routes
    to the appropriate serialization function. Uses PyYAML for general data
    and Pydantic's built-in serialization for models.

    Args:
        data (YamlSerializable): The data to serialize (Pydantic model or general YAML data).
        returns (type[AnyStr]): Return type, either str or bytes.
        encoding (str): Character encoding for bytes output.

    Kwargs:
        Additional keyword arguments passed to the specific serializer.

    Returns:
        AnyStr: Serialized YAML data as string or bytes based on returns parameter.
    """
    if hasattr(data, "__pydantic_core_schema__"):
        return serialize_pydantic(
            data,  # type: ignore
            returns,
            encoding,
            **kwargs,
        )
    else:
        return serialize_pyyaml(
            data,  # type: ignore
            returns,
            encoding,
            **kwargs,
        )


def write_pyyaml(
    file: str | Path,
    data: YamlValue,
    overwrite: bool = False,
    *,
    dumper: DumperName = "safe",
    default_style: str | None = None,
    default_flow_style: bool = False,
    canonical: bool = False,
    indent: int | None = None,
    width: int | None = None,
    allow_unicode: bool | None = None,
    line_break: str | None = None,
    sort_keys: bool = True,
) -> None:
    """
    Writes data to a YAML file using PyYAML serialization.

    Serializes data using PyYAML with configurable options and writes the
    result to a file. Provides control over formatting and output behavior.

    Args:
        file (str | Path): Path to the output file.
        data (YamlValue): The data to serialize and write.
        overwrite (bool): Whether to overwrite existing files.
        dumper (DumperName): The YAML dumper class to use.
        default_style (str | None): Default style for scalars.
        default_flow_style (bool): Whether to use flow style by default.
        canonical (bool): Whether to produce canonical YAML.
        indent (int | None): Number of spaces for indentation.
        width (int | None): Maximum line width.
        allow_unicode (bool | None): Whether to allow unicode characters.
        line_break (str | None): Line break character(s) to use.
        sort_keys (bool): Whether to sort dictionary keys in output.

    Returns:
        None
    """
    ser_data = serialize_pyyaml(
        data=data,
        dumper=dumper,
        default_style=default_style,
        default_flow_style=default_flow_style,
        canonical=canonical,
        indent=indent,
        width=width,
        allow_unicode=allow_unicode,
        line_break=line_break,
        sort_keys=sort_keys,
    )
    io.write_string(
        file,
        ser_data,
        overwrite=overwrite,
        encoding="utf-8",
    )


def write_pydantic(
    file: str | Path,
    data: PydanticModel,
    overwrite: bool = False,
    *,
    dumper: DumperName = "safe",
    default_style: str | None = None,
    default_flow_style: bool = False,
    canonical: bool = False,
    indent: int | None = None,
    width: int | None = None,
    allow_unicode: bool | None = None,
    line_break: str | None = None,
    sort_keys: bool = True,
    include: IncEx | None = None,
    exclude: IncEx | None = None,
    context: Any | None = None,
    by_alias: bool | None = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    round_trip: bool = False,
    warnings: bool | PydanticEncodingWarnings = True,
    serialize_as_any: bool = False,
) -> None:
    """
    Writes a Pydantic model to a YAML file.

    Serializes a Pydantic model using its built-in serialization
    capabilities and writes the result to a file with configurable
    field filtering and output options.

    Args:
        file (str | Path): Path to the output file.
        data (Pydantic): The Pydantic model instance to serialize and write.
        overwrite (bool): Whether to overwrite existing files.
        dumper (DumperName): YAML dumper class to use.
        default_style (str | None): Default style for scalars.
        default_flow_style (bool): Whether to use flow style by default.
        canonical (bool): Whether to produce canonical YAML.
        indent (int | None): Number of spaces for indentation.
        width (int | None): Maximum line width.
        allow_unicode (bool | None): Whether to allow unicode characters.
        line_break (str | None): Line break character(s) to use.
        sort_keys (bool): Whether to sort dictionary keys in output.
        include (IncEx | None): Fields to include in serialization.
        exclude (IncEx | None): Fields to exclude from serialization.
        context (Any | None): Additional context for serialization.
        by_alias (bool | None): Whether to use field aliases in output.
        exclude_unset (bool): Whether to exclude fields that weren't explicitly set.
        exclude_defaults (bool): Whether to exclude fields with default values.
        exclude_none (bool): Whether to exclude fields with None values.
        round_trip (bool): Whether to enable round-trip serialization.
        warnings (bool | PydanticEncodingWarnings): Warning configuration.
        serialize_as_any (bool): Whether to serialize using Any type handling.

    Returns:
        None
    """
    ser_data = serialize_pydantic(
        data=data,
        dumper=dumper,
        default_style=default_style,
        default_flow_style=default_flow_style,
        canonical=canonical,
        indent=indent,
        width=width,
        allow_unicode=allow_unicode,
        line_break=line_break,
        sort_keys=sort_keys,
        include=include,
        exclude=exclude,
        context=context,
        by_alias=by_alias,
        exclude_unset=exclude_unset,
        exclude_defaults=exclude_defaults,
        exclude_none=exclude_none,
        round_trip=round_trip,
        warnings=warnings,
        serialize_as_any=serialize_as_any,
    )
    io.write_string(
        file,
        ser_data,
        overwrite=overwrite,
        encoding="utf-8",
    )


def write(
    file: str | Path,
    data: YamlSerializable,
    overwrite: bool = False,
    **kwargs,
) -> None:
    """
    Writes data to a YAML file using automatic serializer detection.

    Automatically detects whether the data is a Pydantic model and routes
    to the appropriate write function. Uses a heuristic to check for Pydantic
    models to avoid import costs.

    Args:
        file (str | Path): Path to the output file.
        data (YamlSerializable): The data to serialize and write.
        overwrite (bool): Whether to overwrite existing files.

    Kwargs:
        Additional keyword arguments passed to the specific writer.

    Returns:
        None
    """
    if hasattr(data, "__pydantic_core_schema__"):
        write_pydantic(file, data, overwrite, **kwargs)  # type: ignore
    else:
        write_pyyaml(file, data, overwrite, **kwargs)  # type: ignore
