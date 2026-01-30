class PixelFormatError(Exception):
    """Base error for pixel format handling."""
class PixelFormatParseError(PixelFormatError):
    """Raised when a designation cannot be parsed."""
class PixelFormatNotSupportedError(PixelFormatError):
    """Raised when the format is valid but not supported by a feature."""
class PixelFormatNotImplementedError(PixelFormatNotSupportedError):
    """Raised when the format is not implemented / supported."""
class PixelFormatRegistryError(PixelFormatError):
    """Raised on invalid or conflicting registrations."""
class PixelFormatValueReject(PixelFormatError):
    """Pixel format was parsed but values were rejected."""
class PixelFormatImplementationError(PixelFormatError):
    """Internal implementation error."""
class ParseReject(ValueError):
    """Internal: implementation does not match this input."""
class PixelFormatDecodeError(PixelFormatError):
    """Base class for pixel format decoding errors."""
class PixelFormatDecodeNotSupportedError(PixelFormatDecodeError):
    """Raised when no decoder supports a pixel format."""
class PixelFormatDecodeAmbiguousError(PixelFormatDecodeError):
    """Raised when multiple decoders match the same pixel format."""
class RegistryError(Exception):
    """Base class for registry errors."""
class DuplicateRegistrationError(RegistryError):
    """Raised when a key is registered more than once."""
class InvalidRegistrationError(RegistryError):
    """Raised when registration input is invalid."""
class NotRegisteredError(RegistryError):
    """Raised when a key is registered more than once."""
