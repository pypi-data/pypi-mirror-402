---
title: Basic API

description: "Simple Python API functions for social media URL validation. Detect platform from URL, validate social media links, sanitize URLs to canonical format. Zero configuration, works with 50+ predefined platforms."

keywords:
  - basic API
  - Python URL validation functions
  - detect social platform
  - validate social media URL
  - sanitize social link
  - normalize social URL
  - social-links API
  - Python social media validator
  - quick start guide
  - social platform detection
  - URL validation Python
---

# Basic API

Convenience functions for common operations using a default `SocialLinks` instance.

This module provides simple, functional API for common operations like detecting platforms, validating URLs, and sanitizing URLs. These functions use a default `SocialLinks` instance with predefined platforms.

For advanced usage (custom platforms, regex flags, platform management), use the [`SocialLinks` class](core-api.md) directly.

::: sociallinks.basic
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3
      members:
        - detect_platform
        - is_valid
        - sanitize
        - list_platforms
      members_order: source

