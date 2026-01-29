"""Module-level convenience functions for basic usage.

This module provides simple, functional API for common operations like
detecting platforms, validating URLs, and sanitizing URLs. These functions
use a default SocialLinks instance with predefined platforms.

For advanced usage (custom platforms, regex flags, platform management),
use the SocialLinks class directly.
"""
from typing import Optional, List
from .core import SocialLinks

# Lazy-initialized default instance for module-level functions
_default_instance: Optional[SocialLinks] = None


def _get_default_instance() -> SocialLinks:
    """Get or create the default SocialLinks instance.
    
    This instance is lazily initialized on first use and uses the default
    configuration (predefined platforms enabled, re.IGNORECASE regex flags).
    The instance is read-only for module-level functions - use SocialLinks()
    class directly for custom configurations or platform management.
    
    Returns:
        The default SocialLinks instance.
    """
    global _default_instance
    if _default_instance is None:
        _default_instance = SocialLinks()
    return _default_instance


def detect_platform(url: str) -> Optional[str]:
    """Detect the social media platform from a URL.
    
    This is a convenience function that uses a default SocialLinks instance
    with predefined platforms. For custom configurations (regex flags, custom
    platforms), use the SocialLinks class directly.
    
    Args:
        url: The URL or username to analyze. Can be a full URL
            (e.g., "https://linkedin.com/in/johndoe") or just a username
            (e.g., "johndoe"). Whitespace is automatically stripped.
    
    Returns:
        The platform name (e.g., "linkedin", "github", "x") if detected,
        None if no platform matches.
    
    Raises:
        TypeError: If url is not a string.
    
    Examples:
        >>> from sociallinks import detect_platform
        >>> detect_platform("https://linkedin.com/in/johndoe")
        'linkedin'
        >>> detect_platform("https://github.com/username")
        'github'
        >>> detect_platform("https://example.com")
        None
    """
    return _get_default_instance().detect_platform(url)


def is_valid(platform_name: str, url: str) -> bool:
    """Validate a URL against a specific platform.
    
    This is a convenience function that uses a default SocialLinks instance
    with predefined platforms. For custom configurations, use the SocialLinks
    class directly.
    
    Args:
        platform_name: The name of the platform to validate against
            (e.g., "linkedin", "github", "x").
        url: The URL to validate. Can be a full URL or just a username.
            Whitespace is automatically stripped.
    
    Returns:
        True if the URL matches the platform's patterns, False otherwise.
        Also returns False if the platform doesn't exist.
    
    Raises:
        TypeError: If platform_name or url is not a string.
    
    Examples:
        >>> from sociallinks import is_valid
        >>> is_valid("linkedin", "https://www.linkedin.com/in/johndoe/")
        True
        >>> is_valid("linkedin", "https://github.com/username")
        False
        >>> is_valid("github", "https://github.com/username")
        True
    """
    return _get_default_instance().is_valid(platform_name, url)


def sanitize(platform_name: str, url: str) -> str:
    """Sanitize a URL to its canonical format for a specific platform.
    
    This is a convenience function that uses a default SocialLinks instance
    with predefined platforms. For custom configurations, use the SocialLinks
    class directly.
    
    Args:
        platform_name: The name of the platform (e.g., "linkedin",
            "github", "x").
        url: The URL to sanitize. Must match one of the platform's
            patterns. Whitespace is automatically stripped.
    
    Returns:
        The sanitized URL in canonical format for the platform.
    
    Raises:
        TypeError: If platform_name or url is not a string.
        PlatformNotFoundError: If the platform doesn't exist.
        URLMismatchError: If the URL doesn't match any of the platform's
            patterns or if the URL is empty.
        PlatformIDExtractionError: If the platform identifier cannot be
            extracted from the URL.
    
    Examples:
        >>> from sociallinks import sanitize
        >>> sanitize("linkedin", "https://www.linkedin.com/in/johndoe/")
        'https://linkedin.com/in/johndoe'
        >>> sanitize("github", "http://www.github.com/username")
        'https://github.com/username'
        >>> sanitize("x", "https://twitter.com/username")
        'https://x.com/username'
    """
    return _get_default_instance().sanitize(platform_name, url)


def list_platforms() -> List[str]:
    """List all registered platform names.
    
    This is a convenience function that uses a default SocialLinks instance
    with predefined platforms. Returns all platforms available for detection,
    validation, and sanitization.
    
    Returns:
        A list of platform names (strings) in no particular order.
    
    Examples:
        >>> from sociallinks import list_platforms
        >>> platforms = list_platforms()
        >>> "linkedin" in platforms
        True
        >>> "github" in platforms
        True
        >>> len(platforms) > 50
        True
    """
    return _get_default_instance().list_platforms()

