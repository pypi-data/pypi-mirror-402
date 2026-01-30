from .._internal.registry import MappingSnapshot as MappingSnapshot, Registry as Registry
from .._internal.utils import join_designators as join_designators
from _typeshed import Incomplete
from enum import Enum

logger: Incomplete

class PaddingType(Enum):
    """Enumeration of padding types for pixel formats."""
    PACKED = 'p'
    GROUPED = 'g'
    UNPACKED = ''

class PaddingTypeNameRegistry(Registry[str, PaddingType]):
    """Registry for padding type names with immutable defaults."""
    def __init__(self) -> None:
        """Initialize the registry and register default padding type names."""
    def register(self, name: str, value: PaddingType) -> None:
        """Register a padding type name, rejecting changes to defaults."""
    def restore(self, snap: MappingSnapshot[str, PaddingType]) -> None:
        """Restore a snapshot, ensuring defaults are present and unchanged.

        Raises:
            ValueError: If the snapshot is missing defaults or changes their values.
        """
    @classmethod
    def default_snapshot(cls) -> MappingSnapshot[str, PaddingType]:
        """Return a snapshot that contains only the default padding type names."""

PADDING_TYPE_NAME_REGISTRY: PaddingTypeNameRegistry

class Packing:
    """Represents the packing configuration for pixel formats.

    Attributes:
        padding_type_name (str): The name of the padding type.
        lsb (bool): Indicates if the least significant bit is used.
        alignment (Optional[int]): The alignment value.
        cluster_marker (int): The cluster marker value.
    """
    padding_type_name: str
    lsb: bool
    alignment: int | None
    cluster_marker: int
    def __init__(self, padding_type: PaddingType | str | None = None, lsb: bool = True, alignment: int | None = None, cluster_marker: int = 0) -> None:
        """Initializes a Packing instance.

        Args:
            padding_type (Optional[Union[PaddingType, str]]): The type of padding. Defaults to None.
            lsb (bool): Indicates if the least significant bit is used. Defaults to True.
            alignment (Optional[int]): The alignment value. Defaults to None.
            cluster_marker (int): The cluster marker value. Defaults to 0.
        """
    @property
    def padding_type(self) -> PaddingType:
        """Return the padding type."""
    def __eq__(self, other: object) -> bool:
        """Checks if two Packing instances are equal.

        Args:
            other: The other Packing instance to compare.

        Returns:
            bool: True if the instances are equal, False otherwise.
        """
    def designation(self) -> str:
        """Computes the designation string for the Packing instance.

        Returns:
            str: The designation string.
        """
    @staticmethod
    def from_designation(full_designation: str) -> list[tuple['Packing', str]]:
        """Creates a list of possible Packing instances from a designation string.

        Args:
            full_designation (str): The full designation string.

        Returns:
            list[tuple[Packing, str]]: A list of possible Packing instances and remaining substrings.
        """
