from .._internal.registry import MappingSnapshot as MappingSnapshot, Registry as Registry
from .._internal.utils import all_implementations as all_implementations
from _typeshed import Incomplete
from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import TypeGuard

logger: Incomplete

class DefaultDataType(Enum):
    """Enumeration for default data types."""
    UNSIGNED = ''
    SIGNED = 's'
    FLOAT = 'f'
DataType = DefaultDataType | str

class DataTypeRegistry(Registry[str, DataType]):
    """Registry for data types with immutable defaults."""
    def __init__(self) -> None:
        """Initialize the registry and register default data types."""
    def register(self, name: str, value: DataType | None = None) -> None:
        """Register a custom single-letter data type."""
    def restore(self, snap: MappingSnapshot[str, DataType]) -> None:
        """Restore a snapshot."""
    @classmethod
    def default_snapshot(cls) -> MappingSnapshot[str, DataType]:
        """Return a snapshot that is empty except for the default data types."""

DATA_TYPE_REGISTRY: DataTypeRegistry

def is_data_type(potential_data_type: object) -> TypeGuard[DataType]:
    """Checks if the given object is a valid data type.

    Args:
        potential_data_type (Any): The object to check.

    Returns:
        bool: True if the object is a valid data type, False otherwise.
    """
def datatype_name(data_type: DataType, multiple_designators: bool = False) -> str:
    """Returns the string representation of a data type.

    Args:
        data_type (DataType): The data type.
        multiple_designators (bool): Whether to include the 'u' designator for unsigned.

    Returns:
        str: The string representation of the data type.
    """

class DataTypes(metaclass=ABCMeta):
    """Abstract base class for data type designations."""
    @abstractmethod
    def designation(self) -> str:
        """Returns the string representation of the data type."""
    @abstractmethod
    def __len__(self) -> int:
        """Returns the number of elements in the data type."""
    @abstractmethod
    def __getitem__(self, item: int) -> DataType:
        """Returns the element at the specified index."""
    @staticmethod
    def create(full_designation: str, number_of_channels: int) -> list[tuple['DataTypes', str]]:
        """Creates instances of `DataTypes` based on a designation string.

        Args:
            full_designation (str): The full designation string.
            number_of_channels (int): The number of channels.

        Returns:
            List[Tuple[DataTypes, str]]: A list of parsed `DataTypes` instances and remaining designations.
        """
    @staticmethod
    def from_designation(full_designation: str, number_of_channels: int) -> list[tuple['DataTypes', str]]:
        """Parses a designation string into `DataTypes` instances.

        Args:
            full_designation (str): The full designation string.
            number_of_channels (int): The number of channels.

        Returns:
            List[Tuple[DataTypes, str]]: A list of parsed `DataTypes` instances and remaining designations.
        """
    def __eq__(self, other: object) -> bool:
        """Returns `True` if `self` and `other` are equivalent."""

class CompoundDataTypes(DataTypes):
    """Represents a compound designation containing multiple data types."""
    data_types: list[DataType]
    def __init__(self, data_types: list[DataType]) -> None:
        """Initializes a `CompoundDataTypes` instance.

        Args:
            data_types (List[DataType]): A list of data types in the compound designation.

        Raises:
            PixelFormatValueReject: If `data_types` is invalid.
        """
    def designation(self) -> str:
        """Returns the designation string for the compound data types."""
    def __len__(self) -> int:
        """Returns the number of data types in the compound."""
    def __getitem__(self, item: int) -> DataType:
        """Returns the data type at the specified index."""
    @staticmethod
    def from_designation(full_designation: str, number_of_channels: int) -> list[tuple['DataTypes', str]]:
        """Parses a compound data type designation.

        Args:
            full_designation (str): The full designation string.
            number_of_channels (int): The number of channels.

        Returns:
            List[Tuple[DataTypes, str]]: A list of parsed `CompoundDataTypes` and remaining designations.
        """
