from typing import Any
import numbers


def should_str_concat(left: Any, right: Any) -> bool:
    if not isinstance(left, str) and not isinstance(right, str):
        return False

    # We know at least one of them is a str here, let's check the other one
    val_other = right if isinstance(left, str) else left

    if not is_primitive(val_other):
        return False

    return True


def is_primitive(value) -> bool:
    return isinstance(value, (bool, str, bytes, numbers.Number, type(None)))


def as_str(val: Any) -> str:
    if isinstance(val, bool):
        return "true" if val else "false"
    if val is None:
        return ""

    return str(val)


def is_numeric_or_null(val: Any) -> bool:
    """Check if a value is numeric or null."""
    return val is None or isinstance(val, (int, float))


def as_num(val: Any) -> Any:
    """Coerce nullish values to 0 for numeric operations."""
    if val is None:
        return 0
    return val
