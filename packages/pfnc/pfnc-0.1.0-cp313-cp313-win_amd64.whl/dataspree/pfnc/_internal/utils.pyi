from typing import TypeVar

def join_designators(a: str, b: str) -> str:
    """Join two pixel format designators according to the genicam naming conventions."""
T = TypeVar('T', bound=object)

def all_implementations(cls, allow_parent: bool = True) -> list[type[T]]:
    """Yield all implementations of a subclass."""
