from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Generic, List, Type, TypeVar

__all__ = [
    "ApiEndpoint",
    "DryApiSerializable",
    "ApiType",
    "TApiInput",
    "TApiOutput",
    "DictOrList",
]


class DryApiSerializable(ABC):

    @abstractmethod
    def to_dict(
        self,
    ) -> Dict[Any, Any]:
        raise NotImplementedError()

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.to_dict()}>"

    @staticmethod
    @abstractmethod
    def from_dict_unsafe(obj: Dict[Any, Any]) -> "DryApiSerializable":
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def from_dict(obj: Dict[Any, Any]) -> "DryApiSerializable":
        raise NotImplementedError()


DictOrList = Dict | List | dict | list
ApiType = DryApiSerializable | DictOrList

TApiInput = TypeVar("TApiInput", bound=ApiType)
TApiOutput = TypeVar("TApiOutput", bound=ApiType)


@dataclass(frozen=True)
class ApiEndpoint(Generic[TApiInput, TApiOutput]):
    method: str
    input_type: Type[TApiInput]
    output_type: Type[TApiOutput]
