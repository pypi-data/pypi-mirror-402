#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File message bot implementation.

This module provides the :class:`FileBot` class for sending file attachments
to Wecom Group Bots. Files are uploaded as temporary media and referenced
by media_id.

Supported Formats:
    - Any file format (PDF, DOCX, XLSX, ZIP, etc.)
    - Images can be sent as files (alternative to ImageBot)

Size Limit:
    - Minimum: 5 bytes
    - Maximum: 20MB

Example:
    Send various file types::

        from pywgb.bot import FileBot
        
        bot = FileBot("your-webhook-key")
        
        # Send document
        bot.send(file_path="report.pdf")
        
        # Send spreadsheet
        bot.send(file_path="data.xlsx")
        
        # Send archive
        bot.send(file_path="backup.zip")

:author: Rex Zhou <879582094@qq.com>
:copyright: Copyright © 2025 Rex Zhou. All rights reserved.
"""

from ._abstract import ConvertedData, AbstractBot
from .._constants import FileSizeLimits as Limits
from .._deco import verify_file


class FileBot(AbstractBot):
    """
    File message bot for Wecom Group.

    Sends file attachments of any format. The file is uploaded to Wecom's
    temporary media storage and referenced by media_id (valid for 3 days).

    Unlike ImageBot which displays images inline, FileBot sends files as
    downloadable attachments.

    Args:
        key (str): Webhook key or full webhook URL.

    Raises:
        ValueError: If file size is out of range (5B-20MB).
        FileNotFoundError: If the specified file doesn't exist.

    Example:
        Send different file types::

            from pywgb.bot import FileBot

            bot = FileBot("your-key")
            
            # Documents
            bot.send(file_path="report.pdf")
            bot.send(file_path="presentation.pptx")
            
            # Data files
            bot.send(file_path="data.csv")
            bot.send(file_path="config.json")
            
            # Archives
            bot.send(file_path="release.zip")
            
            # Images as files (not displayed inline)
            bot.send(file_path="diagram.png")

    See Also:
        :class:`ImageBot`: For inline image display
        :class:`VoiceBot`: For voice messages
        :class:`SmartBot`: For automatic type detection

    Note:
        - Size range: 5B < size < 20MB
        - Any file format supported
        - Media ID valid for 3 days after upload
        - Files sent as downloadable attachments
        - Rate limit: 20 messages per minute
    """

    @property
    def _doc_key(self) -> str:
        return "文件类型"

    @verify_file
    def _verify_arguments(self, *args, **kwargs) -> None:
        """
        Verify the arguments passed.
        :param args: Positional arguments.
        :param kwargs: Keyword arguments.
        :return:
        """

    # pylint:disable=unused-argument
    def _convert_arguments(self, *args, **kwargs) -> ConvertedData:
        """
        Convert the message to File format.
        :param args: Positional arguments.
        :param kwargs: Other keyword arguments.
        :return: Converted message.
        """
        file_path = kwargs["file_path"]
        # Check file size, only smaller than `20M` and large than `5B`
        with open(file_path, "rb") as _:
            content = _.read()
        size_range = Limits.FILE_MIN < len(content) < Limits.FILE_MAX
        if not size_range or kwargs.get("test") == "oversize_file":
            raise ValueError(
                f"The file size is out of range: {Limits.FILE_MIN} < SIZE < {Limits.FILE_MAX}"
            )
        media_id = self.upload(file_path)
        result = {"msgtype": "file", "file": {"media_id": media_id}}
        return (result,), kwargs
