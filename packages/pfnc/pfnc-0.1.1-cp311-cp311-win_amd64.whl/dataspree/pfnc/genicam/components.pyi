from .._internal.registry import MappingSnapshot as MappingSnapshot, Registry as Registry
from .._internal.utils import all_implementations as all_implementations, join_designators as join_designators
from _typeshed import Incomplete
from abc import ABCMeta, abstractmethod
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from dataspree.pfnc.genicam.number_of_bits import Size as Size
from enum import Enum
from typing import Any, TypeGuard, TypeVar
from typing_extensions import Self

logger: Incomplete

class CompoundChannel(Enum):
    """Enumeration of compound channels for pixel formats."""
    RAW = 'Raw'
    MONO = 'Mono'
    CONFIDENCE = 'Confidence'
    RED = 'R'
    GREEN = 'G'
    BLUE = 'B'
    LUMA = 'Y'
    ALPHA = 'a'
    ALPHA_2 = 'A'
    HUE = 'H'
    SATURATION = 'S'
    VALUE = 'V'
    CHROMA = 'U'
    WHITE = 'W'
    INTENSITY = 'I'
    BLUE_DIFFERENCE = 'Cb'
    RED_DIFFERENCE = 'Cr'
    CYAN = 'C'
    MAGENTA = 'M'
    YELLOW = 'Ye'
    INFRARED = 'Ir'

class CoordinateChannel(Enum):
    """Enumeration of coordinate channels for 3D spatial data."""
    COORD3D_A = 'A'
    COORD3D_B = 'B'
    COORD3D_C = 'C'
Channel = CompoundChannel | CoordinateChannel | str

def is_channel(potential_channel: Any) -> TypeGuard[Channel]:
    """Checks if a given object is a valid channel.

    Args:
        potential_channel: The object to validate.

    Returns:
        bool: True if the object is a valid channel, False otherwise.
    """
def channel_name(channel: Channel) -> str:
    """Retrieves the string representation of a channel.

    Args:
        channel (Channel): The channel to convert.

    Returns:
        str: The string representation of the channel.
    """

@dataclass
class ChannelProperty:
    """Represents properties of a channel.

    Attributes:
        combinable (bool): Whether the channel can be combined with others.

        free (bool): Whether the channel can be freely used by the default implementation.
    """
    combinable: bool
    free: bool = ...

@dataclass
class ChannelRegistry:
    """Registry for channels and their properties with immutable defaults."""
    def __post_init__(self) -> None:
        """Populate default channel registries."""
    def register_custom(self, channel: str, prop: ChannelProperty) -> None:
        """Register a custom single-letter channel with its properties."""
    def resolve_property(self, channel: Channel) -> ChannelProperty:
        """Resolve the property for a channel."""
    def restore(self, snap: MappingSnapshot[Channel, ChannelProperty]) -> None:
        """Restore a snapshot and enforce that defaults are present and unchanged."""
    def snapshot(self) -> MappingSnapshot[Channel, ChannelProperty]:
        """Snapshot current state."""
    def iter_free_designators_by_length(self) -> list[tuple[str, Channel]]:
        """Return designator->channel pairs sorted by designator length (desc).

        This is done in order to favor more complex designators (Cb) over C.
        """

CHANNEL_REGISTRY: ChannelRegistry

class Channels(metaclass=ABCMeta):
    """Abstract base class for handling pixel format channels."""
    @abstractmethod
    def name(self, indices: list[int] | None = None) -> str:
        """Gets the name of the channel sequence.

        Args:
            indices (Optional[list[int]]): Indices to filter specific channels.

        Returns:
            str: The concatenated channel name.
        """
    @abstractmethod
    def __len__(self) -> int:
        """Gets the number of channels.

        Returns:
            int: The number of channels.
        """
    @abstractmethod
    def __getitem__(self, item: int) -> Channel:
        """Gets the channel at the specified index.

        Args:
            item (int): The index of the desired channel.

        Returns:
            Channel: The channel at the specified index.
        """
    def __iter__(self) -> Iterator[Channel]:
        """Iterator implementation."""
    @staticmethod
    def create(channel_start: str, allow_repeat: bool = False) -> list[tuple[Channels, ColorSpaceStandard | None, str]]:
        """Creates channel instances from a starting designation string.

        Args:
            channel_start (str): The starting designation string for channels.
            allow_repeat (bool): Whether duplicate channels are allowed.

        Returns:
            list[tuple['Channels', Optional['ColorSpaceStandard'], str]]: Parsed channels, optional color space
                                                                          standards, and remaining substrings.
        """
    @classmethod
    @abstractmethod
    def from_designation(cls, channel_start: str, allow_repeat: bool = False) -> list[tuple[Self, str]]:
        """Parses a designation string into channels.

        Args:
            channel_start (str): The start of the channel designation.
            allow_repeat (bool): Whether repeated channels are allowed.

        Returns:
            list[tuple['Channels', str]]: A list of channel instances and remaining substrings.
        """

class CompoundChannels(Channels):
    """Represents a compound set of pixel format channels."""
    channels: Sequence[Channel]
    def __init__(self, channels: Sequence[Channel], allow_repeat: bool = False) -> None:
        """Initializes a compound channel set.

        Args:
            channels (Sequence[Channel]): The list of channels.
            allow_repeat (bool): Whether duplicate channels are allowed.

        Raises:
            PixelFormatValueReject: If invalid channels or duplicates are encountered.
        """
    def __len__(self) -> int:
        """Gets the number of channels in the compound channel set.

        Returns:
            int: The number of channels.
        """
    def __getitem__(self, item: int) -> Channel:
        """Gets the channel at the specified index.

        Args:
            item (int): The index of the desired channel.

        Returns:
            Channel: The channel at the specified index.
        """
    def name(self, indices: list[int] | None = None) -> str:
        """Gets the concatenated name of the channel sequence.

        Args:
            indices (Optional[list[int]]): A list of indices to filter specific channels.

        Returns:
            str: The concatenated name of the channels.
        """
    @classmethod
    def from_designation(cls, channel_start: str, allow_repeat: bool = False) -> list[tuple[Self, str]]:
        """Parses a designation string into compound channels.

        Args:
            channel_start (str): The start of the channel designation.
            allow_repeat (bool): Whether repeated channels are allowed.

        Returns:
            list[tuple[CompoundChannels, str]]: A list of channel instances and remaining substrings.
        """
    def __eq__(self, other: Any) -> bool:
        """Checks equality between two CompoundChannel objects.

        Args:
            other (Any): The object to compare.

        Returns:
            bool: True if the objects are equal, False otherwise.
        """

class Coord3D(CompoundChannels):
    """Represents 3D spatial coordinate channels."""
    def __init__(self, channels: Sequence[Channel], allow_repeat: bool = False) -> None:
        """Initializes a compound channel set.

        Args:
            channels (Sequence[Channel]): The list of channels to include.
            allow_repeat (bool): Whether duplicate channels are allowed.

        Raises:
            ValueError: If invalid channels or duplicates are encountered.
        """
    def name(self, indices: list[int] | None = None) -> str:
        """Generates the name of the Coord3D channel sequence.

        Args:
            indices (Optional[list[int]]): Indices to filter specific channels. If None, all channels are used.

        Returns:
            str: The formatted name of the Coord3D channel sequence.
        """
    @classmethod
    def from_designation(cls, channel_start: str | None, allow_repeat: bool = False) -> list[tuple[Self, str]]:
        """Parses a designation string into Coord3D compound channels.

        Args:
            channel_start (str | None): The start of the channel designation.
            allow_repeat (bool): Whether repeated channels are allowed.

        Returns:
            list[tuple[Coord3D, str]]: A list of channel instances and remaining substrings.
        """

class ColorSpaceStandard(metaclass=ABCMeta):
    """Abstract base class for color space standards."""
    name: str
    def __init__(self, name: str) -> None:
        """Initializes the ITU-R BT.601 color space standard."""
    @classmethod
    @abstractmethod
    def initialize(cls, channels: Channels) -> Self:
        """Initializes a color space standard for the given channels.

        Args:
            channels (Channels): The channel set for the standard.

        Returns:
            ColorSpaceStandard: An initialized color space standard.
        """
    @classmethod
    def from_designation(cls, designation_substring: str, channels: Channels) -> list[tuple[Self, str]]:
        """Parses a designation string into location objects.

        Args:
            designation_substring (str): The full designation string.

            channels (Channels): List of channels to which this color space standard applies.

        Returns:
            list[tuple['Location', Channels, ColorSpaceStandard, str]]: Parsed locations, associated channels, optional
                                                                        color space standards, and remaining substrings.
        """
    @staticmethod
    def compatible_with(channels: Channels, designation_substring: str | None = None) -> str | None:
        """Checks whether a designation substring is compatible with the channels.

        Args:
            channels (Channels): The channels to check.
            designation_substring (Optional[str]): The designation substring to validate.

        Returns:
            Optional[str]: Remaining substring if compatible, otherwise None.
        """
    @staticmethod
    def create(designation_substring: str, channels: Channels) -> list[tuple[ColorSpaceStandard | None, str]]:
        """Creates color space standard objects from a designation substring.

        Args:
            designation_substring (str): The substring to parse.
            channels (Channels): The associated channels.

        Returns:
            list[tuple[Optional['ColorSpaceStandard'], str]]: A list of parsed color space standards and remaining
                                                              substrings.
        """

class ItuRBt601(ColorSpaceStandard):
    """Represents the ITU-R BT.601 color space standard."""
    def __init__(self) -> None:
        """Initializes the ITU-R BT.601 color space standard."""
    @classmethod
    def initialize(cls, channels: Channels) -> Self:
        """Initializes the Itu.RBt.601 color space standard.

        Args:
            channels (Channels): The channels to associate with this color space standard.

        Returns:
            ItuRBt601: An instance of the Itu.RBt.601 color space standard.
        """
    @staticmethod
    def compatible_with(channels: Channels, designation_substring: str | None = None) -> str | None:
        """Checks if the channels and designation substring are compatible with the Itu.Rbt.601 standard.

        Args:
            channels (Channels): The channels to validate against the standard.
            designation_substring (Optional[str]): The remaining string to check for compatibility.

        Returns:
            Optional[str]: The remaining substring after removing the standard identifier if compatible,
                           otherwise None.
        """
    def __eq__(self, other: Any) -> bool:
        """Checks equality between two ItuRBt601 objects.

        Args:
            other (Any): The object to compare.

        Returns:
            bool: True if the objects are equal, False otherwise.
        """

class ItuRBt709(ColorSpaceStandard):
    """Represents the ITU-R BT.709 color space standard."""
    def __init__(self) -> None:
        """Initializes the ITU-R BT.709 color space standard."""
    @classmethod
    def initialize(cls, channels: Channels) -> Self:
        """Initializes the Itu.RBt.709 color space standard.

        Args:
            channels (Channels): The channels to associate with this color space standard.

        Returns:
            ItuRBt709: An instance of the Itu.RBt.709 color space standard.
        """
    @staticmethod
    def compatible_with(channels: Channels, designation_substring: str | None = None) -> str | None:
        """Checks if the channels and designation substring are compatible with the Itu.RBt.709 standard.

        Args:
            channels (Channels): The channels to validate against the standard.
            designation_substring (Optional[str]): The remaining string to check for compatibility.

        Returns:
            Optional[str]: The remaining substring after removing the standard identifier if compatible,
                           otherwise None.
        """
    def __eq__(self, other: Any) -> bool:
        """Checks equality between two ItuRBt709 objects.

        Args:
            other (Any): The object to compare.

        Returns:
            bool: True if the objects are equal, False otherwise.
        """

class Bt601(ColorSpaceStandard):
    """Represents the BT.601 color space standard."""
    def __init__(self) -> None:
        """Initializes the BT.601 color space standard."""
    @classmethod
    def initialize(cls, channels: Channels) -> Self:
        """Initializes the BT.601 color space standard.

        Args:
            channels (Channels): The channels to associate with this color space standard.

        Returns:
            Bt601: An instance of the BT.601 color space standard.
        """
    @staticmethod
    def compatible_with(channels: Channels, designation_substring: str | None = None) -> str | None:
        """Checks if the channels and designation substring are compatible with the BT.601 standard.

        Args:
            channels (Channels): The channels to validate against the standard.
            designation_substring (Optional[str]): The remaining string to check for compatibility.

        Returns:
            Optional[str]: The remaining substring after removing the standard identifier if compatible,
                           otherwise None.
        """
    def __eq__(self, other: Any) -> bool:
        """Checks equality between two Bt601 objects.

        Args:
            other (Any): The object to compare.

        Returns:
            bool: True if the objects are equal, False otherwise.
        """

class Bt709(ColorSpaceStandard):
    """Represents the BT.709 color space standard."""
    def __init__(self) -> None:
        """Initializes the BT.709 color space standard."""
    @classmethod
    def initialize(cls, channels: Channels) -> Self:
        """Initializes the BT.709 color space standard.

        Args:
            channels (Channels): The channels to associate with this color space standard.

        Returns:
            Bt709: An instance of the BT.709 color space standard.
        """
    @staticmethod
    def compatible_with(channels: Channels, designation_substring: str | None = None) -> str | None:
        """Checks if the channels and designation substring are compatible with the BT.709 standard.

        Args:
            channels (Channels): The channels to validate against the standard.
            designation_substring (Optional[str]): The remaining string to check for compatibility.

        Returns:
            Optional[str]: The remaining substring after removing the standard identifier if compatible,
                           otherwise None.
        """
    def __eq__(self, other: Any) -> bool:
        """Checks equality between two Bt601 objects.

        Args:
            other (Any): The object to compare.

        Returns:
            bool: True if the objects are equal, False otherwise.
        """

@dataclass
class Location(metaclass=ABCMeta):
    """Abstract base class for pixel locations."""
    @abstractmethod
    def location_designation(self, channels: Channels, color_space_name: str) -> str:
        """Generates a location designation string.

        Args:
            channels (Channels): The associated channels.
            color_space_name (str): The name of the color space.

        Returns:
            str: The location designation.
        """
    @abstractmethod
    def location_name(self, channels: Channels) -> str:
        """Gets the name of the component's location.

        Args:
            channels (Channels): The associated channels.

        Returns:
            str: The location name.
        """
    @abstractmethod
    def number_of_channels(self) -> int:
        """Returns the number of channels in the component.

        This is determined by the length of the component.

        Returns:
            int: The number of channels.
        """
    @classmethod
    def create(cls, full_designation: str) -> list[tuple[Self, Channels, ColorSpaceStandard | None, str]]:
        """Creates location objects by parsing a full designation string.

        Args:
            full_designation (str): The full string to parse for location designation.

        Returns:
            list[tuple[Self, Channels, ColorSpaceStandard, str]]: A list of tuples containing:
                - Self: The created location object.
                - Channels: The associated channels.
                - ColorSpaceStandard: The color space standard associated with the location.
                - str: The remaining designation substring.
        """
    @classmethod
    @abstractmethod
    def from_designation(cls, full_designation: str) -> list[tuple[Self, Channels, ColorSpaceStandard | None, str]]:
        """Parses a designation string into location instances.

        Args:
            full_designation (str): The full string to parse for location designation.

        Returns:
            list[tuple[Location, Channels, Optional[ColorSpaceStandard], str]]: A list of tuples containing:
                - Location: The parsed Mono Location object.
                - Channels: The associated channels.
                - Optional[ColorSpaceStandard]: An optional color space standard.
                - str: The remaining designation substring.
        """

@dataclass
class MonoLocation(Location):
    """If a monochrome camera uses one of the mono pixel formats, it outputs 8, 10, 12, or 14 bits of data per pixel.

    If a Basler color camera uses one of the mono pixel formats, the values for each pixel are first converted to the
    YCbCr color model and returns the Y component (brightness).
    This is equivalent to the value that would be derived from a pixel in a monochrome sensor.
    """
    def location_designation(self, channels: Channels, color_space_name: str) -> str:
        """Generates a location designation string.

        Args:
            channels (Channels): The associated channels.
            color_space_name (str): The name of the color space.

        Returns:
            str: The location designation.
        """
    def location_name(self, channels: Channels) -> str:
        """Gets the name of the component's location.

        Args:
            channels (Channels): The associated channels.

        Returns:
            str: The location name.
        """
    def number_of_channels(self) -> int:
        """Returns the number of channels in the component.

        This is determined by the length of the component.

        Returns:
            int: The number of channels.
        """
    @classmethod
    def from_designation(cls, full_designation: str) -> list[tuple[Self, Channels, ColorSpaceStandard | None, str]]:
        """Parses a designation string into Mono location instances.

        Args:
            full_designation (str): The full string to parse for location designation.

        Returns:
            list[tuple[Self, Channels, Optional[ColorSpaceStandard], str]]: A list of tuples containing:
                - Location: The parsed Mono Location object.
                - Channels: The associated channels.
                - Optional[ColorSpaceStandard]: An optional color space standard.
                - str: The remaining designation substring.
        """
    def __eq__(self, other: Any) -> bool:
        """Checks equality between two MonoLocation objects.

        Args:
            other (Any): The object to compare.

        Returns:
            bool: True if the objects are equal, False otherwise.
        """

@dataclass
class LMNLocation(Location):
    """Represents an LMN-based pixel location."""
    fields: tuple[int, ...]
    def __post_init__(self) -> None:
        """Performs validation checks on the LMNLocation fields after initialization.

        Raises:
            PixelFormatValueReject: If the fields are empty or have invalid values.
        """
    def location_designation(self, channels: Channels, color_space_name: str) -> str:
        """Generates a location designation string.

        Args:
            channels (Channels): The associated channels.
            color_space_name (str): The name of the color space.

        Returns:
            str: The location designation.
        """
    def location_name(self, channels: Channels) -> str:
        """Gets the name of the component's location.

        Args:
            channels (Channels): The associated channels.

        Returns:
            str: The location name.
        """
    def number_of_channels(self) -> int:
        """Returns the number of channels in the component.

        This is determined by the length of the component.

        Returns:
            int: The number of channels.
        """
    @classmethod
    def from_designation(cls, full_designation: str) -> list[tuple[Self, Channels, ColorSpaceStandard | None, str]]:
        """Parses a designation string into LMN-based location instances.

        Args:
            full_designation (str): The full string to parse for location designation.

        Returns:
            list[tuple[Loc, Channels, Optional[ColorSpaceStandard], str]]: A list of tuples containing:
                - Loc: The parsed LMNLocation object.
                - Channels: The associated channels.
                - Optional[ColorSpaceStandard]: An optional color space standard.
                - str: The remaining designation substring.
        """
    def __eq__(self, other: Any) -> bool:
        """Checks equality between two LMNLocation objects.

        Args:
            other (Any): The object to compare.

        Returns:
            bool: True if the objects are equal, False otherwise.
        """

@dataclass
class BayerLocation(Location):
    '''Modern color camera sensors are equipped with a Bayer color filter.

    They record red, green, blue pixels in distinct areas and  interpolate in between.
    Interpolation can be proprietary.

    If instead of the interpolated n x m values, you would like to directly receive the bayer
    pattern, use a bayer pixel format. Each pixel is filtered to record only one of the colors.

     array and can output color
    images based on Bayer pixel formats.


    If a color camera uses one of the Bayer pixel formats, it outputs 8, 10, or 12 bits of data per pixel.
    Each pixel is filtered to record only one of the colors red, green, and blue. The pixel data is not processed or
    interpolated in any way. This type of pixel data is sometimes referred to as "raw" output.

    Which Bayer formats are available depends on your camera model.

    If a monochrome camera uses one of the mono pixel formats, it outputs 8, 10, 12, or 14 bits of data per pixel.

    If a Basler color camera uses one of the mono pixel formats, the values for each pixel are first converted to the
    YCbCr color model and returns the Y component (brightness).
    This is equivalent to the value that would be derived from a pixel in a monochrome sensor.
    '''
    fields: tuple[str, str, str, str]
    indices: tuple[int, int, int, int] = ...
    def __post_init__(self) -> None:
        """Validates the BayerLocation fields after initialization.

        Raises:
            PixelFormatValueReject: If the field configuration is invalid.
        """
    def location_designation(self, channels: Channels, color_space_name: str) -> str:
        """Generates a location designation string.

        Args:
            channels (Channels): The associated channels.
            color_space_name (str): The name of the color space.

        Returns:
            str: The location designation.
        """
    def location_name(self, channels: Channels) -> str:
        """Gets the name of the component's location.

        Args:
            channels (Channels): The associated channels.

        Returns:
            str: The location name.
        """
    def number_of_channels(self) -> int:
        """Returns the number of channels in the component.

        This is determined by the length of the component.

        Returns:
            int: The number of channels.
        """
    @classmethod
    def from_designation(cls, full_designation: str) -> list[tuple[Self, Channels, ColorSpaceStandard | None, str]]:
        """Parses a designation string into BayerLocation instances.

        Args:
            full_designation (str): The string to parse.

        Returns:
            list[tuple[Location, Channels, Optional[ColorSpaceStandard], str]]: Parsed BayerLocation instances,
                associated channels, optional color space standards, and remaining substrings.
        """
    def __eq__(self, other: Any) -> bool:
        """Checks equality between two BayerLocation objects.

        Args:
            other (Any): The object to compare.

        Returns:
            bool: True if the objects are equal, False otherwise.
        """

@dataclass
class BiColor(Location):
    """Represents a Bi-Color pattern pixel location."""
    fields: tuple[str, str, str, str]
    indices: tuple[int, int, int, int] = ...
    def __post_init__(self) -> None:
        """Processes and validates the BiColor fields during initialization."""
    def location_designation(self, channels: Channels, color_space_name: str) -> str:
        """Generates a location designation string.

        Args:
            channels (Channels): The associated channels.
            color_space_name (str): The name of the color space.

        Returns:
            str: The location designation.
        """
    def location_name(self, channels: Channels) -> str:
        """Gets the name of the component's location.

        Args:
            channels (Channels): The associated channels.

        Returns:
            str: The location name.
        """
    def number_of_channels(self) -> int:
        """Returns the number of channels in the component.

        This is determined by the length of the component.

        Returns:
            int: The number of channels.
        """
    @classmethod
    def from_designation(cls, full_designation: str) -> list[tuple[Self, Channels, ColorSpaceStandard | None, str]]:
        """Parses a designation string into BiColor instances.

        Args:
            full_designation (str): The string to parse.

        Returns:
            list[tuple[Location, Channels, Optional[ColorSpaceStandard], str]]: Parsed BiColor instances,
                associated channels, optional color space standards, and remaining substrings.
        """
    def __eq__(self, other: Any) -> bool:
        """Checks equality between two BiColor objects.

        Args:
            other (Any): The object to compare.

        Returns:
            bool: True if the objects are equal, False otherwise.
        """

@dataclass
class ColorFilterArray(Location, metaclass=ABCMeta):
    """Abstract base class for color filter arrays."""

@dataclass
class SquarePattern(ColorFilterArray, metaclass=ABCMeta):
    """Represents a square pattern color filter array."""
    def __post_init__(self) -> None:
        """Handles post-initialization logic for square pattern color filter arrays.

        Raises:
            NotImplementedError: Indicates the method is not implemented.
        """

@dataclass
class SparseColorFilterLocation(ColorFilterArray, metaclass=ABCMeta):
    """A color filter array that includes panchromatic pixels with the red, green and blue color components.

    Different tile patterns can be created.
    """
    fields: tuple[str, str, str, str]
    def __post_init__(self) -> None:
        """Validates the sparse color filter fields during initialization.

        Raises:
            PixelFormatValueReject: If the field configuration is invalid.
            NotImplementedError: Indicates the method is not implemented.
        """
Comp = TypeVar('Comp', bound='Components')

class Components(metaclass=ABCMeta):
    """Abstract base class for pixel format components."""
    @abstractmethod
    def full_designation(self) -> str:
        """Gets the full designation string for the component.

        Returns:
            str: The full designation string.
        """
    @abstractmethod
    def channel_designation(self) -> str:
        """Gets the designation string for the channels.

        Returns:
            str: The channel designation string.
        """
    @abstractmethod
    def location_name(self) -> str:
        """Gets the name of the component's location.

        Returns:
            str: The location name.
        """
    @property
    def number_of_channels(self) -> int:
        """Returns the number of channels in the component.

        This is determined by the length of the component.

        Returns:
            int: The number of channels.
        """
    @abstractmethod
    def __len__(self) -> int:
        """Gets the number of components.

        Returns:
            int: The number of components.
        """
    @abstractmethod
    def __getitem__(self, item: int) -> Channel:
        """Gets the channel at the specified index.

        Args:
            item (int): The index of the desired channel.

        Returns:
            Channel: The channel at the specified index.
        """
    @staticmethod
    def create(full_designation: str) -> list[tuple[Components, str]]:
        """Parses a full designation string into component objects.

        Iterates through all implementations of the `Components` class, attempting
        to parse the given full designation string into a list of component objects
        and their corresponding substrings.

        Args:
            full_designation (str): The string to parse into components.

        Returns:
            list[tuple[Components, str]]: A list of tuples containing the parsed
            components and their remaining substrings.
        """
    @classmethod
    @abstractmethod
    def from_designation(cls, full_designation: str) -> list[tuple[Comp, str]]:
        """Parses a designation string into component objects.

        Args:
            full_designation (str): The string to parse.

        Returns:
            list[tuple[Components, str]]: Parsed components and remaining substrings.
        """

class GenicamComponents(Components):
    """Represents GenICam-compatible pixel format components."""
    channels: Channels
    location: Location
    color_space_standard: ColorSpaceStandard | None
    def __init__(self, channels: Channels | Channel | Sequence[Channel], location: Location | None = None, color_space_standard: ColorSpaceStandard | None = None) -> None:
        """Initializes a GenICam-compatible component with channels, location, and color space.

        Args:
            channels (Union[Channels, Channel, Sequence[Channel]]): The channels included in the component.
            location (Optional[Location]): The location information of the component.
            color_space_standard (Optional[ColorSpaceStandard]): The associated color space standard.
        """
    def channel_designation(self) -> str:
        """Gets the designation string for the component's channels.

        Returns:
            str: The concatenated name of the channels in the component.
        """
    def full_designation(self) -> str:
        """Generates the full designation string for the component.

        This includes channel and location information, optionally combined with
        the name of the associated color space standard.

        Returns:
            str: The full designation string of the component.
        """
    def location_name(self) -> str:
        """Gets the name of the component's location.

        Returns:
            str: The location name.
        """
    def __len__(self) -> int:
        """Gets the number of channels.

        Returns:
            int: The number of channels.
        """
    def __getitem__(self, item: int) -> Channel:
        """Gets the channel at the specified index.

        Args:
            item (int): The index of the desired channel.

        Returns:
            Channel: The channel at the specified index.
        """
    def __eq__(self, other: Any) -> bool:
        """Checks equality between two GenicamComponent objects.

        Args:
            other (Any): The object to compare.

        Returns:
            bool: True if the objects are equal, False otherwise.
        """
    @classmethod
    def from_designation(cls, full_designation: str) -> list[tuple[Self, str]]:
        """Parses a designation string into GenicamComponents instances.

        Args:
            full_designation (str): The full string representing the designation.

        Returns:
            list[tuple[Components, str]]: A list of tuples containing GenicamComponents and the remaining substring.

        Logs:
            Warnings are logged if exceptions occur during parsing by location implementations.
        """

class CustomComponents(Components, metaclass=ABCMeta):
    """Abstract base class for custom pixel format components."""

def bayer_rgb(location: tuple[str, str, str, str], color_space_standard: ColorSpaceStandard | None = None) -> GenicamComponents:
    """Creates a Bayer RGB component.

    Args:
        location (tuple[str, str, str, str]): The Bayer pattern location.
        color_space_standard (Optional[ColorSpaceStandard]): The associated color space standard.

    Returns:
        GenicamComponents: The Bayer RGB component.
    """
def bi_color_rgb(location: tuple[str, str, str, str], color_space_standard: ColorSpaceStandard | None = None) -> GenicamComponents:
    """Creates a Bi-Color RGB component.

    Args:
        location (tuple[str, str, str, str]): The Bi-Color pattern location.
        color_space_standard (Optional[ColorSpaceStandard]): The associated color space standard.

    Returns:
        GenicamComponents: The Bi-Color RGB component.
    """

class SizedColorSpaceStandard(metaclass=ABCMeta):
    """Abstract base class for size-dependent color space standards."""
    name: str
    def __init__(self, name: str) -> None:
        """Initializes a sized color space standard with a name."""
    @classmethod
    @abstractmethod
    def from_designation(cls, designation_substring: str, comps: Components, sizes: Size) -> list[tuple[Self, str]]:
        """Parses a designation string into a sized color space standard.

        Args:
            designation_substring (str): The string to parse.
            comps (Components): The associated components.
            sizes (Size): The associated size information.

        Returns:
            list[tuple[SizedColorSpaceStandard, str]]: Parsed standards and remaining substrings.
        """
    @staticmethod
    def compatible_with(comps: Components, sizes: Size) -> bool:
        """Checks if the components and size are compatible with the standard.

        Args:
            comps (Components): The components to check.
            sizes (Size): The size information to validate.

        Returns:
            bool: True if compatible, False otherwise.
        """
    @staticmethod
    def create(designation_substring: str, comps: Components, sizes: Size) -> list[tuple[SizedColorSpaceStandard | None, str]]:
        """Creates sized color space standard objects from a designation substring.

        Args:
            designation_substring (str): The substring to parse.
            comps (Components): The associated components.
            sizes (Size): The associated size information.

        Returns:
            list[tuple[Optional[SizedColorSpaceStandard], str]]: Parsed standards and remaining substrings.
        """

class RGB10V1(SizedColorSpaceStandard):
    """Represents the RGB10 V1 color space standard."""
    def __init__(self) -> None:
        """Initializes the RGB10 V1 color space standard."""
    @staticmethod
    def compatible_with(comps: Components, sizes: Size) -> bool:
        """Checks if the components and size are compatible with the RGB10 V1 standard.

        Args:
            comps (Components): The components to check.
            sizes (Size): The size information to validate.

        Returns:
            bool: True if compatible, False otherwise.
        """
    @classmethod
    def from_designation(cls, designation_substring: str, comps: Components, sizes: Size) -> list[tuple[Self, str]]:
        """Parses a designation string into an RGB10 V1 color space standard.

        Args:
            designation_substring (str): The string to parse.
            comps (Components): The associated components.
            sizes (Size): The associated size information.

        Returns:
            list[tuple[SizedColorSpaceStandard, str]]: Parsed standards and remaining substrings.
        """
    def __eq__(self, other: Any) -> bool:
        """Checks equality between two SizedColorSpaceStandard objects.

        Args:
            other (Any): The object to compare.

        Returns:
            bool: True if the objects are equal, False otherwise.
        """

class RGB12V1(SizedColorSpaceStandard):
    """Represents the RGB12 V1 color space standard."""
    def __init__(self) -> None:
        """Initializes the RGB12 V1 color space standard."""
    @staticmethod
    def compatible_with(comps: Components, sizes: Size) -> bool:
        """Checks if the components and size are compatible with the RGB12 V1 standard.

        Args:
            comps (Components): The components to check.
            sizes (Size): The size information to validate.

        Returns:
            bool: True if compatible, False otherwise.
        """
    @classmethod
    def from_designation(cls, designation_substring: str, comps: Components, sizes: Size) -> list[tuple[Self, str]]:
        """Parses a designation string into an RGB12 V1 color space standard.

        Args:
            designation_substring (str): The string to parse.
            comps (Components): The associated components.
            sizes (Size): The associated size information.

        Returns:
            list[tuple[Self, str]]: Parsed standards and remaining substrings.
        """
    def __eq__(self, other: Any) -> bool:
        """Checks equality between two RGB12V1 objects.

        Args:
            other (Any): The object to compare.

        Returns:
            bool: True if the objects are equal, False otherwise.
        """
