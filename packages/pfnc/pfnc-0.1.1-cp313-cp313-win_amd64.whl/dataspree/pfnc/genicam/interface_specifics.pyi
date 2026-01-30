from .._internal.utils import all_implementations as all_implementations
from _typeshed import Incomplete
from abc import ABCMeta, abstractmethod
from dataspree.pfnc.genicam.components import Components as Components
from dataspree.pfnc.genicam.number_of_bits import Size as Size
from typing_extensions import Self

logger: Incomplete

class InterfaceSpecific(metaclass=ABCMeta):
    """Abstract base class for interface-specific pixel format designations."""
    @abstractmethod
    def designation(self) -> str:
        """Returns the designation of the interface-specific format."""
    @staticmethod
    def create(full_designation: str, components: Components, sizes: Size) -> list[tuple['InterfaceSpecific', str]]:
        """Creates instances of `InterfaceSpecific` based on the designation.

        Args:
            full_designation (str): The full designation string.
            components (Components): The pixel format components.
            sizes (Size): The sizes of the components.

        Returns:
            List[Tuple[InterfaceSpecific, str]]: A list of tuples with `InterfaceSpecific` instances and remaining
                                                designations.
        """
    @classmethod
    @abstractmethod
    def from_designation(cls, full_designation: str, components: Components, sizes: Size) -> list[tuple[Self, str]]:
        """Parses the designation into specific interface format instances.

        Args:
            full_designation (str): The full designation string.
            components (Components): The pixel format components.
            sizes (Size): The sizes of the components.

        Returns:
            List[Tuple[InterfaceSpecific, str]]: A list of tuples with parsed instances and remaining designations.
        """
    def __eq__(self, other: object) -> bool:
        """Checks equality with another object."""

class Planar(InterfaceSpecific):
    """Represents the planar interface-specific format."""
    def designation(self) -> str:
        """Returns the planar designation."""
    @classmethod
    def from_designation(cls, full_designation: str, components: Components, sizes: Size) -> list[tuple[Self, str]]:
        """Parses planar-specific designations.

        Args:
            full_designation (str): The full designation string.
            components (Components): The pixel format components.
            sizes (Size): The sizes of the components.

        Returns:
            List[Tuple[InterfaceSpecific, str]]: A list with a `Planar` instance if matched.
        """

class SemiPlanar(InterfaceSpecific):
    """Represents the semi-planar interface-specific format."""
    def designation(self) -> str:
        """Returns the semi-planar designation."""
    @classmethod
    def from_designation(cls, full_designation: str, components: Components, sizes: Size) -> list[tuple[Self, str]]:
        """Parses semi-planar-specific designations.

        Args:
            full_designation (str): The full designation string.
            components (Components): The pixel format components.
            sizes (Size): The sizes of the components.

        Returns:
            List[Tuple[InterfaceSpecific, str]]: A list with a `SemiPlanar` instance if matched.
        """

class ComponentsSequencing(InterfaceSpecific):
    """Represents an interface-specific format based on component sequencing."""
    components: tuple[str, ...]
    def __init__(self, components: tuple[str, ...]) -> None:
        """Initializes a `ComponentsSequencing` instance.

        Args:
            components (Tuple[str, ...]): A tuple of component names.
        """
    def designation(self) -> str:
        """Returns the component sequencing designation."""
    @classmethod
    def from_designation(cls, full_designation: str, components: Components, sizes: Size) -> list[tuple[Self, str]]:
        """Parses component sequencing-specific designations.

        Args:
            full_designation (str): The full designation string.
            components (Components): The pixel format components.
            sizes (Size): The sizes of the components.

        Returns:
            List[Tuple[InterfaceSpecific, str]]: A list of parsed instances and remaining designations.
        """
    def __eq__(self, other: object) -> bool:
        """Checks equality with another object."""
