import numpy as np
from .._internal.utils import join_designators as join_designators
from _typeshed import Incomplete
from dataspree.pfnc.decoder_registry import PixelFormatDecoder
from dataspree.pfnc.genicam.components import Components, SizedColorSpaceStandard
from dataspree.pfnc.genicam.data_types import DataType as DataType, DataTypes
from dataspree.pfnc.genicam.interface_specifics import InterfaceSpecific
from dataspree.pfnc.genicam.number_of_bits import Size
from dataspree.pfnc.genicam.packing_types import Packing
from dataspree.pfnc.pixel_format import PixelFormat
from typing import Any, TypeGuard, TypeVar

logger: Incomplete
PF = TypeVar('PF', bound=PixelFormat)

class GenicamPixelFormat(PixelFormat):
    '''Representation of a pixel format that complies with the genicam standard.

    Detailed information about pixel formats can be found in the GenICam Pixel Format Naming Convention 2.1.
    https://www.emva.org/wp-content/uploads/GenICam_PFNC_2_1.pdf.

    The naming convention subdivides as it follows:
    1. Components and Location (e.g., "RGB" / "Mono")
    2. number of bits per component (e.g., "8")
    3. [Optional] data type ("u" or "" for unsigned, "s" for signed, "f" for floating point)
    4. [Optional] packing: @see Packing
    5. [Optional] interface-specific

    Consecutive fields must be separated by an underscore, iff (:= if, and only if) a pixel name
    requires 2 numbers in its designation as part of consecutive fields.
    Example: YCbCr709_422_8 for 8-bit per component Y’CbCr 4:2:2 using ITU-R BT.709.


    Attributes:
        component (Components): The components of the pixel format.
        size (Size): The size of the pixel format.
        data_type (DataTypes): The data type of the pixel format.
        packing (Packing): The packing type of the pixel format.
        interface_specific (Optional[InterfaceSpecific]): The interface-specific part of the pixel format.
        sized_color_space_standard (Optional[SizedColorSpaceStandard]): The sized color space standard.
    '''
    component: Components
    storage_units: int
    size: Size
    sized_color_space_standard: SizedColorSpaceStandard | None
    data_type: DataTypes
    packing: Packing
    interface_specific: InterfaceSpecific | None
    def __init__(self, component: Components, size: Size | int | list[int], data_type: DataTypes | list[DataType] | DataType | None = None, packing: Packing | None = None, interface_specific: InterfaceSpecific | None = None, sized_color_space_standard: SizedColorSpaceStandard | None = None, storage_units: int | None = None) -> None:
        """Initializes a GenicamPixelFormat instance.

        storage_units models how many storage elements per pixel the size/data_type vectors describe.
        If omitted, it defaults to the number of logical channels (len(component)).
        """
    def designation(self) -> str:
        """Compute designation."""
    def __setattr__(self, key: str, value: Any) -> None:
        """Sets an attribute and clears the cached designation if necessary.

        Args:
            key (str): The attribute name.
            value: The attribute value.
        """
    @classmethod
    def from_designation(cls, full_designation: str) -> list[GenicamPixelFormat]:
        """Return list of compatible genicam pixel formats with the full designation."""
    def __eq__(self, other: object) -> bool:
        """Check if components are equal."""
    def numpy_dtype(self) -> np.dtype[Any]:
        """Return the numpy dtype for the unpacked storage representation."""

class UnpackedInterleavedStorageDecoder(PixelFormatDecoder):
    """Decode unpacked, interleaved storage layouts using the current GenicamPixelFormat logic."""
    def __init__(self) -> None:
        """Initialize."""
    def is_applicable(self, pixel_format: PixelFormat) -> TypeGuard[GenicamPixelFormat]:
        """Return True for unpacked interleaved layouts that the model says are supported."""
    def decode(self, pixel_format: PixelFormat, buffer: bytes, *, width: int, height: int, stride: int, copy: bool = False) -> np.ndarray[Any, Any]:
        """Decode unpacked interleaved buffers into numpy arrays.

        Args:
            pixel_format: Parsed GenICam pixel format instance.
            buffer: Raw frame bytes (one image).
            width: Image width in pixels.
            height: Image height in pixels.
            stride: Bytes per line (can be > width * bytes_per_pixel).
            copy: If True, return a contiguous copy without line padding.

        Returns:
            np.ndarray: Array view or copy of shape (height, width) or (height, width, storage_units).

        Raises:
            ValueError: If buffer/stride/format are inconsistent.
            NotImplementedError: If the storage layout is not supported by this decoder.
        """
