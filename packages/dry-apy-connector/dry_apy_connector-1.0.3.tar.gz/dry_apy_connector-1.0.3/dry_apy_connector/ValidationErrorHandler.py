from dataclasses import dataclass
from typing import Callable, Dict, Optional, List, Tuple, Literal

VALIDATION_ERROR_HANDLER_TYPE = Callable[[List[Dict[str, dict]]], None]

__all__ = ["get_validation_messages", "ValidationData", "get_validation_items"]


@dataclass(frozen=True)
class PathEntry:
    key: Optional[str]
    index: Optional[int]
    type: Literal["KEY", "INDEX"]


@dataclass(frozen=True)
class ValidationItem:
    path: List[PathEntry]
    message: str
    severity: Literal["ERROR", "WARNING"]


@dataclass(frozen=True)
class ValidationData:
    items: List[ValidationItem]


def get_validation_messages(
    responses: List[dict], *, name: Optional[str] = None
) -> Tuple[str, str]:
    errors = ""
    warns = ""
    for i in range(len(responses)):
        resp = responses[i]
        status = resp["status"]
        error = None
        warn = None

        if status == "INVALID_INPUT":
            error = get_validation_string(
                resp["qualifiedName"],
                resp["validation"]["items"],
                "ERROR",
            )

            warn = get_validation_string(
                resp["qualifiedName"],
                resp["validation"]["items"],
                "WARNING",
            )
        elif resp.get("errorMessage") is not None:
            error = resp["errorMessage"]

        if error is not None:
            errors += f"\n{create_batch_prefix(name, i)}\n{error}\n"

        if warn is not None:
            warns += f"\n{create_batch_prefix(name, i)}\n{warn}\n"

    return errors, warns


def get_validation_string(
    method: str, validation_items: list, severity
) -> Optional[str]:
    errors = list(filter(lambda entry: entry["severity"] == severity, validation_items))
    if len(errors) > 0:
        error = f"validation {severity} on method '{method}':"
        for item in errors:
            path = []
            for key in item["path"]["items"]:
                path.append(key["key"] if key["key"] is not None else key["index"])

            error += f"\n\t{path}:    {item['message']}"

        return error
    return None


def create_batch_prefix(name: Optional[str], index: int) -> str:
    return f"{name or 'API Batch'}[{index}]:" if index > 0 else ""


def get_validation_items(validation_items: dict) -> List[ValidationItem]:
    items: List[ValidationItem] = []
    for validation_item in validation_items:
        path: List[PathEntry] = []
        for key in validation_item["path"]["items"]:
            path.append(PathEntry(key["key"], key["index"], key["type"]))

        item = ValidationItem(
            path, validation_item["message"], validation_item["severity"]
        )
        items.append(item)

    return items
