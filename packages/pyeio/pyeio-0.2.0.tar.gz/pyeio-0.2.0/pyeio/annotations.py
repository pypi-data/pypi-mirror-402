from types import NoneType
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Literal,
    Protocol,
    TypeAlias,
    TypeVar,
    Union,
)

PydanticEncodingWarnings = Literal["none", "warn", "error"]

if TYPE_CHECKING:
    from dataclasses import Field as DataclassField
    from datetime import datetime
    from uuid import UUID

    from numpy import ndarray
    from pydantic import BaseModel, RootModel
    from pydantic.main import IncEx

    PydanticModel: TypeAlias = BaseModel | RootModel
    T_PydanticModel = TypeVar("T_PydanticModel", bound=PydanticModel)

    class DataclassInstance(Protocol):
        __dataclass_fields__: ClassVar[dict[str, DataclassField[Any]]]

    OrJsonSerializable: TypeAlias = Union[
        str,
        bool,
        int,
        float,
        NoneType,
        list["OrJsonSerializable"],
        dict[str, "OrJsonSerializable"],
        DataclassInstance,
        ndarray,
        datetime,
        UUID,
        Any,
    ]
    JsonSerializable: TypeAlias = T_PydanticModel | OrJsonSerializable
    TomlValue: TypeAlias = Any
    TomlSerializable: TypeAlias = Union[PydanticModel, Any]
    YamlInputValue: TypeAlias = Union[
        str,
        bool,
        int,
        float,
        NoneType,
        datetime,
        list["YamlInputValue"],
        dict[str, "YamlInputValue"],
        Any,  # if this is left out it drives pylance crazy
    ]

    YamlSerializable: TypeAlias = PydanticModel | YamlInputValue
    YamlValue: TypeAlias = Any

else:
    ndarray = Any

    UUID = Any
    DataclassInstance = Any
    datetime = Any

    IncEx = Any
    PydanticModel = Any
    T_PydanticModel = Any

    JsonValue = Any
    OrJsonSerializable = Any
    JsonSerializable = Any

    TomlValue = Any
    TomlSerializable = Any

    YamlValue = Any
    YamlSerializable = Any
