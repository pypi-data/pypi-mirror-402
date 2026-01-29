#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Constants module for Wecom Group Bot API.

This module defines all magic numbers and constant values used throughout
the library. Constants are organized into frozen dataclasses for type safety
and immutability.

Classes:
    - :class:`FileSizeLimits`: File size constraints for different media types
    - :class:`MessageLimits`: Message length limits for text-based messages
    - :class:`MediaLimits`: Media-specific constraints (duration, count)
    - :class:`RateLimits`: API rate limiting parameters
    - :class:`FileFormats`: Supported file format specifications

Design:
    All constant classes use ``@dataclass(frozen=True)`` to ensure:
    
    - **Immutability**: Values cannot be modified after creation
    - **Type Safety**: IDE autocomplete and type checking support
    - **Namespace**: Organized grouping of related constants
    - **Documentation**: Clear purpose for each constant group

Example:
    Using constants in code::

        from pywgb._constants import FileSizeLimits, MessageLimits, FileFormats
        
        # Check file size
        file_size = 1024 * 1024  # 1MB
        if file_size > FileSizeLimits.IMAGE:
            print("Image too large!")
        
        # Check message length
        message = "Hello, World!"
        if len(message.encode('utf-8')) > MessageLimits.TEXT:
            print("Message too long!")
        
        # Check file format
        if file_path.suffix in FileFormats.IMAGE:
            print("Valid image format")

:author: Rex Zhou <879582094@qq.com>
:copyright: Copyright © 2026 Rex Zhou. All rights reserved.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class FileSizeLimits:
    """
    File size limits in bytes for different media types.

    Defines maximum and minimum file sizes enforced by Wecom API.

    Attributes:
        IMAGE (int): Maximum image size (2MB = 2,097,152 bytes)
        VOICE_MIN (int): Minimum voice file size (5 bytes)
        VOICE_MAX (int): Maximum voice file size (2MB = 2,097,152 bytes)
        FILE_MIN (int): Minimum file size (5 bytes)
        FILE_MAX (int): Maximum file size (20MB = 20,971,520 bytes)

    Example:
        ::

            from pywgb._constants import FileSizeLimits
            
            file_size = Path("image.png").stat().st_size
            if file_size > FileSizeLimits.IMAGE:
                raise ValueError("Image exceeds 2MB limit")
    """

    IMAGE = 2 * 1024 * 1024  # 2MB
    VOICE_MIN = 5  # 5B
    VOICE_MAX = 2 * 1024 * 1024  # 2MB
    FILE_MIN = 5  # 5B
    FILE_MAX = 20 * 1024 * 1024  # 20MB


@dataclass(frozen=True)
class MessageLimits:
    """
    Message length limits in bytes (UTF-8 encoded).

    Defines maximum message lengths for text-based message types.

    Attributes:
        TEXT (int): Maximum text message length (2048 bytes)
        MARKDOWN (int): Maximum markdown message length (4096 bytes)

    Example:
        ::

            from pywgb._constants import MessageLimits
            
            message = "Hello, World!"
            if len(message.encode('utf-8')) > MessageLimits.TEXT:
                raise ValueError("Message exceeds 2048 bytes")
    """

    TEXT = 2048
    MARKDOWN = 4096


@dataclass(frozen=True)
class MediaLimits:
    """
    Media-specific constraints for voice and news messages.

    Attributes:
        VOICE_DURATION (int): Maximum voice duration in seconds (60)
        NEWS_ARTICLES (int): Maximum number of articles per news message (8)

    Example:
        ::

            from pywgb._constants import MediaLimits
            
            articles = [...]  # List of news articles
            if len(articles) > MediaLimits.NEWS_ARTICLES:
                raise ValueError("Too many articles (max 8)")
    """

    VOICE_DURATION = 60  # seconds
    NEWS_ARTICLES = 8  # articles per message


@dataclass(frozen=True)
class RateLimits:
    """
    API rate limiting parameters enforced by Wecom.

    Attributes:
        MESSAGES_PER_MINUTE (int): Maximum messages per minute per bot (20)
        COOLDOWN_SECONDS (int): Cooldown period after rate limit hit (60)
        OVERHEAT_ERROR_CODE (int): API error code for rate limit exceeded (45009)

    Example:
        ::

            from pywgb._constants import RateLimits
            
            # Rate limiting is handled automatically by @detect_overheat decorator
            # When OVERHEAT_ERROR_CODE is detected, bot waits COOLDOWN_SECONDS
    """

    MESSAGES_PER_MINUTE = 20
    COOLDOWN_SECONDS = 60
    OVERHEAT_ERROR_CODE = 45009


@dataclass(frozen=True)
class FileFormats:
    """
    Supported file format specifications.

    Attributes:
        IMAGE (set): Supported image formats ({".jpg", ".png"})
        VOICE (str): Supported voice format (".amr")

    Example:
        ::

            from pywgb._constants import FileFormats
            from pathlib import Path
            
            file_path = Path("audio.amr")
            if file_path.suffix == FileFormats.VOICE:
                print("Valid voice format")
            
            if file_path.suffix in FileFormats.IMAGE:
                print("Valid image format")
    """

    IMAGE = {".jpg", ".png"}
    VOICE = ".amr"
