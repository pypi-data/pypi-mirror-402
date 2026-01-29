from types import NoneType
from typing import Any, Literal

from ._json import JSONEncodeError, compute_orjson_opt_code, dumps, orjson


def check_basic(data: Any) -> bool:
    """
    Check if the value is a *basic* json value. Does not include
    checks for if the value is orjson/pydantic serializable.
    May be slow for large inputs.

    Args:
        data (Any): Object to check.

    Returns:
        bool: Whether the value is a valid basic JSON value.
    """
    if isinstance(data, (bool, int, float, str, NoneType)):
        return True
    else:
        if isinstance(data, list):
            result: bool = all([check_basic(i) for i in data])
            return result
        elif isinstance(data, dict):
            has_string_keys: bool = all([isinstance(key, str) for key in data.keys()])
            has_json_values: bool = all([check_basic(i) for i in data.values()])
            result = has_string_keys and has_json_values
            return result
        else:
            return False


def check_json(data: Any) -> bool:
    """
    Check if data is JSON-serializable using the standard json library.

    Attempts to serialize the data using json.dumps(). Returns True if
    serialization succeeds, False if a TypeError is raised. This uses
    a try-except approach rather than recursive structure checking.

    Args:
        data (Any): Object to check for JSON serializability.

    Returns:
        bool: True if the data can be serialized with standard json, False otherwise.
    """
    try:
        dumps(data)
        return True
    except TypeError:
        return False


def check_orjson(data: Any) -> bool:
    """
    Check if data is orjson-serializable.

    Attempts to serialize the data using orjson.dumps(). Returns True if
    serialization succeeds, False if a JSONEncodeError or TypeError is raised.

    Args:
        data (Any): Object to check for orjson serializability.

    Returns:
        bool: True if the data can be serialized with orjson, False otherwise.
    """
    try:
        orjson.dumps(data, option=compute_orjson_opt_code())
        return True
    except (JSONEncodeError, TypeError):
        return False


def check_pydantic(data: Any) -> bool:
    """
    Check if data is a Pydantic model that can be serialized to JSON.

    First checks if the data is a Pydantic model by looking for the
    __pydantic_core_schema__ attribute. If it is, attempts to serialize
    using model_dump_json(). Returns False if not a Pydantic model or
    if serialization fails.

    Args:
        data (Any): Object to check for Pydantic model serializability.

    Returns:
        bool: True if the data is a serializable Pydantic model, False otherwise.
    """
    if not hasattr(data, "__pydantic_core_schema__"):
        return False

    try:
        data.model_dump_json()
        return True
    except Exception:
        return False


def check(
    data: Any,
    strategy: Literal["basic", "json", "orjson", "pydantic"] = "basic",
) -> bool:
    """
    Check if data is serializable using the specified strategy.

    Provides different levels of serializability checking:

    - "basic": Only basic JSON types (str, int, float, bool, None, list, dict)
    - "json": Standard library json serializable
    - "orjson": orjson serializable (includes dataclasses, datetime, UUID, numpy arrays)
    - "pydantic": Pydantic model serializable

    Args:
        data (Any): Object to check for serializability.
        strategy (Literal["basic", "json", "orjson", "pydantic"]):
            The serialization strategy to check against.

    Returns:
        bool: True if the data is serializable with the specified strategy,
            False otherwise.

    Raises:
        TypeError: If an invalid strategy is provided.
    """
    match strategy:
        case "basic":
            return check_basic(data)
        case "json":
            return check_json(data)
        case "orjson":
            return check_orjson(data)
        case "pydantic":
            return check_pydantic(data)
        case _:
            raise TypeError(strategy)
