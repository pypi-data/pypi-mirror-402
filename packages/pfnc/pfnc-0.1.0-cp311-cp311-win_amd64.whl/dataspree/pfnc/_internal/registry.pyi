from collections.abc import Iterator
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar('T')
K = TypeVar('K')

@dataclass(frozen=True)
class MappingSnapshot(Generic[K, T]):
    """Snapshot for a single mapping-based registry."""
    mapping: dict[K, T]

@dataclass
class Registry(Generic[K, T]):
    """Registry."""
    def register(self, name: K, value: T) -> None:
        """Register.

        Args:
            name: Alias string uniquely identifying the value
            value: The registered value type.

        Raises:
            DuplicateRegistrationError: If already registered.
        """
    def snapshot(self) -> MappingSnapshot[K, T]:
        """Snapshot current state."""
    def restore(self, snap: MappingSnapshot[K, T]) -> None:
        """Restore a snapshot."""
    def resolve(self, name: K) -> T:
        """Resolve alias to type."""
    def get(self, key: K, default_value: T | None = None) -> T | None:
        """Return the value for key if key is registered, else default_value.

        Args:
            key: Name to look up.
            default_value: Value to return if key is not registered.

        Returns:
            The registered value or default_value if key is missing.
        """
    def __iter__(self) -> Iterator[K]:
        """Iterate over registered names."""
