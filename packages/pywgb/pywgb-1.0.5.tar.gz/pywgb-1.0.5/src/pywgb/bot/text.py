#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Text message bot implementation.

This module provides the :class:`TextBot` class for sending plain text messages
to Wecom Group Bots. It supports @mentions for specific users or all members.

Example:
    Basic text message::

        from pywgb.bot import TextBot
        
        bot = TextBot("your-webhook-key")
        bot.send("Hello, World!")
        
    Text with mentions::
    
        bot.send(
            "Important announcement",
            mentioned_list=["user123", "@all"],
            mentioned_mobile_list=["13800138000"]
        )

:author: Rex Zhou <879582094@qq.com>
:copyright: Copyright © 2025 Rex Zhou. All rights reserved.
"""

from ._abstract import ConvertedData, AbstractBot
from .._constants import MessageLimits


def check_args(*args, maximum: int = MessageLimits.TEXT) -> None:
    """
    Validate message arguments for text-based messages.

    Checks that the message is not empty and doesn't exceed the maximum
    byte length when encoded in UTF-8.

    Args:
        *args: Positional arguments where first argument is the message.
        maximum (int, optional): Maximum message length in bytes. Defaults to 2048.

    Raises:
        ValueError: If message is missing, empty, or exceeds maximum length.

    Example:
        ::

            check_args("Hello")  # OK
            check_args("")  # Raises ValueError: Can't send empty message
            check_args("x" * 3000)  # Raises ValueError: Message too long
    """
    try:
        msg = args[0]
    except IndexError as error:
        raise ValueError("The msg parameter is required.") from error
    if not msg:
        raise ValueError("Can't send empty message.")
    # Check then message length
    if len(str(msg).encode("utf-8")) > maximum:
        raise ValueError(f"The msg parameter is too long (>{maximum} bytes).")


class TextBot(AbstractBot):
    """
    Text message bot for Wecom Group.

    Sends plain text messages with optional @mentions. Maximum message
    length is 2048 bytes (UTF-8 encoded).

    Attributes:
        _MAX_LENGTH (int): Maximum message length in bytes (2048).
        _OPTIONAL_ARGS (List[str]): Optional mention parameters.

    Args:
        key (str): Webhook key or full webhook URL.

    Example:
        Simple text message::

            from pywgb.bot import TextBot

            bot = TextBot("your-key")
            bot.send("Hello, World!")

        With mentions::

            bot.send(
                "Team meeting at 3 PM",
                mentioned_list=["user1", "user2"],
                mentioned_mobile_list=["13800138000"]
            )

        Mention everyone::

            bot.send("Important!", mentioned_list=["@all"])

    See Also:
        :class:`MarkdownBot`: For formatted messages
        :class:`SmartBot`: For automatic type detection
    """

    _OPTIONAL_ARGS = ["mentioned_list", "mentioned_mobile_list"]

    @property
    def _doc_key(self) -> str:
        return "文本类型"

    def _verify_arguments(self, *args, **kwargs) -> None:
        """
        Verify the arguments passed.
        :param args: Positional arguments.
        :param kwargs: Keyword arguments.
        :return:
        """
        check_args(*args, maximum=MessageLimits.TEXT)
        for optional in self._OPTIONAL_ARGS:
            if optional not in kwargs:
                continue
            err_msg = f"The {optional} parameter should be a list of strings."
            if not isinstance(data := kwargs[optional], list):
                raise ValueError(err_msg)
            if not all(isinstance(_, str) for _ in data):
                raise ValueError(err_msg)

    def _convert_arguments(self, *args, **kwargs) -> ConvertedData:
        """
        Convert the message to text format data.
        :param args: Positional arguments.
        :param kwargs: Other keyword arguments.
        :return: Converted data.
        """
        mentioned_list: list = kwargs.get("mentioned_list", [])
        mentioned_mobile_list: list = kwargs.get("mentioned_mobile_list", [])
        result = (
            {
                "msgtype": "text",
                "text": {
                    "content": args[0].strip(),
                    "mentioned_list": mentioned_list,
                    "mentioned_mobile_list": mentioned_mobile_list,
                },
            },
        )
        return result, kwargs
