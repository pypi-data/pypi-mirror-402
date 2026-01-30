import numpy as np
from ._internal.utils import all_implementations as all_implementations
from _typeshed import Incomplete
from abc import ABCMeta, abstractmethod
from typing import Any
from typing_extensions import Self

logger: Incomplete

class PixelFormat(metaclass=ABCMeta):
    """Abstraction for arbitrary pixel formats."""
    @classmethod
    def create(cls, full_designation: str) -> list[Self]:
        """Return all existing pixel format that accord with the designation.

        Args:
            full_designation (str): the unique designation of the pixel format.
        """
    @classmethod
    def from_name(cls, full_designation: str) -> Self:
        """Return existing pixel format with the designation.

        Args:
            full_designation (str): the unique designation of the pixel format.

        Raises:
            DriverFeatureImplementationError if no corresponding pixel format was found / the
                                             designation is not unique.
        """
    @abstractmethod
    def designation(self) -> str:
        """Compute unique string representation (designation)."""
    @classmethod
    @abstractmethod
    def from_designation(cls, full_designation: str) -> list[Self]:
        """Return list of compatible genicam pixel formats with the full designation."""
    def decode(self, buffer: bytes | bytearray | memoryview, *, width: int, height: int, stride: int | None = None, copy: bool = False) -> np.ndarray[Any, Any]:
        """Decode numpy image from buffer."""
    def get_buffer_size(self, width: int, height: int, stride: int | None = None) -> int:
        """Return the required buffer size.

        Args:
            width: Image width in pixels.
            height: Image height in pixels.
            stride: Bytes per line (can be > width * bytes_per_pixel).
        """
    def visualization_image(self, image: np.ndarray[Any, Any], **kwargs: Any) -> np.ndarray[Any, Any]:
        """Return the default image visualization.

        This function can be implemented for instance by GENICAM formats to de-bayer in case the format is Bayer format.
        """

DEFAULT_DECODER_REGISTRY: Incomplete
