from copy import deepcopy
from typing import Protocol

from pydantic import BaseModel


class StructuredProvider(Protocol):
    def generate[T: BaseModel](self, prompt: str, schema: type[T]) -> T: ...


class FakeProvider:
    """Explicit fixture adapter for tests; never selected by the application."""

    def __init__(self, *, environment: str, fixture: dict[str, object]) -> None:
        if environment != "test":
            raise ValueError("FakeProvider is available only in test mode")
        self._fixture = deepcopy(fixture)

    def generate[T: BaseModel](self, prompt: str, schema: type[T]) -> T:
        return schema.model_validate(deepcopy(self._fixture))
