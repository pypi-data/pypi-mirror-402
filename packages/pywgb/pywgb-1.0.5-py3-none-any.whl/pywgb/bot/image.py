#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Image message bot implementation.

This module provides the :class:`ImageBot` class for sending image messages
to Wecom Group Bots. Images are sent as base64-encoded data with MD5 hash
for verification.

Supported Formats:
    - PNG (``.png``)
    - JPEG (``.jpg``)

Size Limit:
    - Maximum 2MB per image

Example:
    Send an image::

        from pywgb.bot import ImageBot
        
        bot = ImageBot("your-webhook-key")
        bot.send(file_path="screenshot.png")
        
    Send multiple images::
    
        bot.send(file_path="chart1.png")
        bot.send(file_path="photo.jpg")

:author: Rex Zhou <879582094@qq.com>
:copyright: Copyright © 2025 Rex Zhou. All rights reserved.
"""
from base64 import b64encode
from hashlib import md5
from pathlib import Path

from ._abstract import ConvertedData, AbstractBot
from .._constants import FileSizeLimits, FileFormats
from .._deco import verify_file


class ImageBot(AbstractBot):
    """
    Image message bot for Wecom Group.

    Sends images as base64-encoded messages with MD5 hash verification.
    Supports PNG and JPEG formats up to 2MB in size.

    The image is automatically encoded and hashed before sending. No manual
    encoding is required.

    Args:
        key (str): Webhook key or full webhook URL.

    Raises:
        ValueError: If image format is unsupported or size exceeds 2MB.
        FileNotFoundError: If the specified image file doesn't exist.

    Example:
        Basic usage::

            from pywgb.bot import ImageBot

            bot = ImageBot("your-key")
            
            # Send PNG image
            bot.send(file_path="screenshot.png")
            
            # Send JPEG image
            bot.send(file_path="photo.jpg")

    See Also:
        :class:`FileBot`: For sending images as file attachments
        :class:`SmartBot`: For automatic type detection

    Note:
        - Maximum size: 2MB
        - Supported formats: PNG, JPEG only
        - Images are base64-encoded automatically
        - Rate limit: 20 messages per minute
    """

    @property
    def _doc_key(self) -> str:
        return "图片类型"

    @verify_file
    def _verify_arguments(self, *args, **kwargs) -> None:
        """
        Verify the arguments passed.
        :param args: Positional arguments.
        :param kwargs: Keyword arguments.
        :return:
        :raise ValueError: Verify error.
        """
        suffix = Path(kwargs["file_path"]).suffix.lower()
        test = kwargs.get("test")
        # Check format, only support: `.jpg` and `.png`
        if suffix not in FileFormats.IMAGE or test == "wrong_format_image":
            raise ValueError(f"Just support image type: {FileFormats.IMAGE}")

    def _convert_arguments(self, *args, **kwargs) -> ConvertedData:
        """
        Convert the message to Image format.
        :param args: Positional arguments.
        :param kwargs: Other keyword arguments.
        :return: Converted message.
        """
        file_path = Path(kwargs["file_path"])
        # Check image size, only smaller than `2M`
        with open(file_path, "rb") as _:
            content = _.read()
        if (
            len(content) > FileSizeLimits.IMAGE
            or kwargs.get("test") == "oversize_image"
        ):
            raise ValueError("The image is too large, more than 2M")
        result = (
            {
                "msgtype": "image",
                "image": {
                    "base64": b64encode(content).decode("utf-8"),
                    "md5": md5(content).hexdigest(),
                },
            },
        )
        return result, kwargs
