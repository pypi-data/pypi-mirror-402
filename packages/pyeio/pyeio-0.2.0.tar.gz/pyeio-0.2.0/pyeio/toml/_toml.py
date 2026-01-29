from __future__ import annotations

from pathlib import Path
from typing import (
    Any,
    AnyStr,
    cast,
    overload,
)

from toml import dumps, loads

from pyeio import io
from pyeio.annotations import (
    IncEx,
    PydanticEncodingWarnings,
    PydanticModel,
    T_PydanticModel,
    TomlSerializable,
    TomlValue,
)


@overload
def parse(data: str | bytes, /) -> TomlValue: ...
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
) -> TomlValue | T_PydanticModel:
    if isinstance(data, bytes):
        data = data.decode("utf-8")
    elif isinstance(data, str):
        pass
    else:
        raise TypeError(data)
    loaded = loads(data)
    if model is None:
        return loaded
    result = model.model_validate(
        obj=loaded,
        strict=strict,
        context=context,
        by_alias=by_alias,
        by_name=by_name,
    )
    return result


@overload
def read(file: str | Path, /) -> TomlValue: ...
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
) -> TomlValue | T_PydanticModel:
    content: str = io.read_string(file)
    result: Any = parse(
        content,
        model,  # type: ignore
        strict,
        context,
        by_alias,
        by_name,
    )
    return result


def serialize_native(
    data: TomlValue,
    returns: type[AnyStr] = bytes,
    encoding: str = "utf-8",
) -> AnyStr:
    ser_data: str = dumps(data)

    if returns is bytes:
        return cast(AnyStr, ser_data.encode(encoding))
    elif returns is str:
        return cast(AnyStr, ser_data)
    else:
        raise TypeError(returns)


def serialize_pydantic(
    data: PydanticModel,
    returns: type[AnyStr] = bytes,
    encoding: str = "utf-8",
    *,
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
    ser_data: dict[str, Any] = data.model_dump(
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
    result = serialize_native(ser_data, returns, encoding)
    return result


def serialize(
    data: TomlSerializable,
    returns: type[AnyStr] = str,
    encoding: str = "utf-8",
    **kwargs,
) -> AnyStr:
    if hasattr(data, "__pydantic_core_schema__"):
        return serialize_pydantic(
            data,  # type: ignore
            returns,
            encoding,
            **kwargs,
        )
    else:
        return serialize_native(data, returns, encoding)


def write_native(
    file: str | Path,
    data: TomlSerializable,
    overwrite: bool = False,
) -> None:
    ser_data: bytes = serialize_native(data=data)
    io.write_binary(
        file,
        ser_data,
        overwrite=overwrite,
    )


def write_pydantic(
    file: str | Path,
    data: PydanticModel,
    overwrite: bool,
    *,
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
    ser_data: bytes = serialize_pydantic(
        data=data,
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
    io.write_binary(
        file,
        ser_data,
        overwrite=overwrite,
    )


def write(
    file: str | Path,
    data: TomlSerializable,
    overwrite: bool = False,
    **kwargs,
) -> None:
    if hasattr(data, "__pydantic_core_schema__"):
        write_pydantic(
            file,
            data,  # type: ignore
            overwrite,
            **kwargs,
        )
    else:
        write_native(
            file,
            data,
            overwrite,
            **kwargs,
        )
