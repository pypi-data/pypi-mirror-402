import numpy as np
from _typeshed import Incomplete
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from dataspree.pfnc.pixel_format import PixelFormat as PixelFormat
from typing import Any

logger: Incomplete

@dataclass
class PixelFormatDecoder(metaclass=ABCMeta):
    """Base class for decoder backends.

    Args:
        name (str) name of the decoder.
    """
    name: str
    @abstractmethod
    def is_applicable(self, pixel_format: PixelFormat) -> bool:
        """Return True if this decoder can handle the given pixel format."""
    @abstractmethod
    def decode(self, pixel_format: PixelFormat, buffer: bytes, *, width: int, height: int, stride: int, copy: bool = False) -> np.ndarray[Any, Any]:
        """Decode a frame buffer into a numpy array."""

@dataclass(frozen=True)
class DecoderRegistration:
    """Single decoder registration entry.

    Args:
        priority (int) priority. The higher, the more priority.

        decoder (PixelFormatDecoder) The decoder.
    """
    decoder: PixelFormatDecoder
    priority: int

@dataclass(frozen=True)
class DecoderRegistrySnapshot:
    """Snapshot of registry state for test isolation."""
    registrations: tuple[DecoderRegistration, ...]

@dataclass
class DecoderRegistry:
    """Registry that resolves a decoder for a given GenICam pixel format."""
    def register(self, priority: int, decoder: PixelFormatDecoder) -> None:
        """Register a decoder backend.

        Args:
            priority (int): priority. The higher, the more priority.

            decoder (PixelFormatDecoder): The decoder.
        """
    def snapshot(self) -> DecoderRegistrySnapshot:
        """Create a snapshot of the registry state."""
    def restore(self, snap: DecoderRegistrySnapshot) -> None:
        """Restore the registry state from a snapshot."""
    def resolve(self, pixel_format: PixelFormat) -> PixelFormatDecoder:
        """Resolve the best decoder for a pixel format.

        If multiple decoders exist that have got the same priority, take the first one registered.

        Args:
            pixel_format: Parsed GenICam pixel format instance.

        Returns:
            PixelFormatDecoder: The selected decoder.

        Raises:
            PixelFormatDecodeNotSupportedError: If no decoder matches.
        """
    def decode(self, pixel_format: PixelFormat, buffer: bytes, *, width: int, height: int, stride: int, copy: bool = False) -> np.ndarray[Any, Any]:
        """Decode using the resolved decoder.

        Args:
            pixel_format: Parsed GenICam pixel format instance.
            buffer: Raw frame bytes (one image).
            width: Image width in pixels.
            height: Image height in pixels.
            stride: Bytes per line (can be > width * bytes_per_pixel).
            copy: If True, return a contiguous copy without line padding.

        Returns:
            np.ndarray: Decoded array.
        """
