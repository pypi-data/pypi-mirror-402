---
title: Exception Reference

description: "Complete exception reference for social-links Python library. Handle platform errors, URL validation errors, and invalid configurations. Comprehensive error handling guide with exception hierarchy."

keywords:
  - exceptions
  - error handling Python
  - platform errors
  - URL validation errors
  - social media validation errors
  - exception handling
  - Python exception hierarchy
  - social-links errors
  - platform not found error
  - invalid URL error
  - error handling guide
---

# Exceptions

This page documents all custom exceptions used in the `social-links` library. All exceptions inherit from `SocialLinksError`, allowing you to catch all social-links related errors with a single exception handler.

::: sociallinks.exceptions
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3
      members:
        - SocialLinksError
        - PlatformError
        - PlatformNotFoundError
        - PlatformAlreadyExistsError
        - InvalidPlatformError
        - InvalidPlatformRegexError
        - URLParsingError
        - URLMismatchError
        - PlatformIDExtractionError
      members_order: source

