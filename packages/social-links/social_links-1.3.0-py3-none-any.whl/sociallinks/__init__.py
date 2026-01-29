from .core import SocialLinks
from .basic import (
    detect_platform,
    is_valid,
    sanitize,
    list_platforms,
)
from .exceptions import (
    SocialLinksError,
    PlatformError,
    PlatformNotFoundError,
    PlatformAlreadyExistsError,
    InvalidPlatformError,
    InvalidPlatformRegexError,
    URLParsingError,
    URLMismatchError,
    PlatformIDExtractionError,
)


__all__ = [
    # Class
    "SocialLinks",
    # Module-level convenience functions
    "detect_platform",
    "is_valid",
    "sanitize",
    "list_platforms",
    # Exceptions
    "SocialLinksError",
    "PlatformError",
    "PlatformNotFoundError",
    "PlatformAlreadyExistsError",
    "InvalidPlatformError",
    "InvalidPlatformRegexError",
    "URLParsingError",
    "URLMismatchError",
    "PlatformIDExtractionError",
]

