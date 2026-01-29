#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart Bot - Intelligent message type detection and routing.

This module provides the :class:`SmartBot` class, which automatically detects
the message type based on content and parameters, then routes to the appropriate
specialized bot implementation.

The SmartBot eliminates the need to manually choose between TextBot, MarkdownBot,
ImageBot, etc. It uses regex pattern matching, file extension detection, and
parameter analysis to make intelligent routing decisions.

Example:
    Automatic type detection::

        from pywgb import SmartBot
        
        bot = SmartBot("your-webhook-key")
        
        # Automatically detected as TextBot
        bot.send("Plain text message")
        
        # Automatically detected as MarkdownBot
        bot.send("# Markdown Title\\n**Bold**")
        
        # Automatically detected as ImageBot
        bot.send(file_path="image.png")
        
        # Automatically detected as NewsBot
        bot.send(articles=[{"title": "News", "url": "https://..."}])

:author: Rex Zhou <879582094@qq.com>
:copyright: Copyright © 2025 Rex Zhou. All rights reserved.
"""
from pathlib import Path
from re import compile as re_compile, MULTILINE, Pattern
from typing import Dict, List, Type, TypeVar, Union, Callable

from ._abstract import AbstractBot, FilePathLike
from .file import FileBot
from .image import ImageBot
from .markdown import MarkdownBot, MarkdownBotV2
from .news import NewsBot
from .template_card.news import NewsCardBot
from .template_card.text import TextCardBot
from .text import TextBot
from .voice import VoiceBot
from .._constants import FileFormats
from .._deco import verify_file

# pylint: disable=protected-access
_Colors: List[str] = [_.lower() for _ in MarkdownBot._Color.get_valid_codes()]
_BotT = TypeVar("_BotT", bound="AbstractBot")


class SmartBot(AbstractBot):
    """
    Smart Wecom Group Bot with automatic message type detection.

    SmartBot intelligently determines the appropriate message type based on
    the provided content and parameters, eliminating the need to manually
    select specific bot classes.

    Detection Logic:
        1. **Text/Markdown**: Analyzes message content with regex patterns

           - Markdown v1: Detects unique color syntax
           - Markdown v2: Detects tables, multi-level lists, code blocks
           - Text: Default for plain messages or when @mentions are used

        2. **File Types**: Determined by file extension

           - Voice: ``.amr`` files
           - Image: ``.png`` or ``.jpg`` files
           - File: All other extensions

        3. **News**: Presence of ``articles`` parameter
        4. **Template Cards**: Complex kwargs structure

           - NewsCard: Contains ``card_image`` parameter
           - TextCard: Other template card parameters

    Attributes:
        markdown_feature: Proxy object providing access to Markdown features

            - ``green(text)``: Green colored text (Markdown v1)
            - ``gray(text)``: Gray colored text (Markdown v1)
            - ``orange(text)``: Orange colored text (Markdown v1)
            - ``list2table(data)``: Convert list to table (Markdown v2)

    Args:
        key (str): Webhook key or full webhook URL. Must contain a valid UUID.

    Raises:
        ValueError: If the key format is invalid or missing.

    Example:
        Basic usage with automatic detection::

            from pywgb import SmartBot

            bot = SmartBot("your-webhook-key-uuid")

            # Text message
            bot.send("Hello, World!")

            # Text with mentions
            bot.send("Alert!", mentioned_list=["@all"])

            # Markdown v1 with colors
            msg = f"Status: {bot.markdown_feature.green('OK')}"
            bot.send(msg)

            # Markdown v2 with table
            table = [["Name", "Age"], ["Alice", "30"], ["Bob", "25"]]
            msg = f"# Report\\n{bot.markdown_feature.list2table(table)}"
            bot.send(msg)

            # Image
            bot.send(file_path="screenshot.png")

            # News article
            bot.send(articles=[{
                "title": "Breaking News",
                "url": "https://example.com",
                "description": "Important update",
                "picurl": "https://example.com/pic.jpg"
            }])

            # Template card
            bot.send(
                main_title={"title": "Notification"},
                sub_title_text="Details here",
                card_action={"type": 1, "url": "https://example.com"}
            )

    See Also:
        - :class:`TextBot`: For text-only messages
        - :class:`MarkdownBot`: For Markdown v1 messages
        - :class:`MarkdownBotV2`: For Markdown v2 messages
        - :class:`ImageBot`: For image messages
        - :class:`VoiceBot`: For voice messages
        - :class:`FileBot`: For file messages
        - :class:`NewsBot`: For news articles
        - :class:`TextCardBot`: For text template cards
        - :class:`NewsCardBot`: For news template cards

    Note:
        The bot respects Wecom's rate limit of 20 messages per minute.
        Exceeding this limit triggers automatic cooldown.
    """

    _MD_V1_PATTERN: Pattern = re_compile(
        r"("
        + "|".join(
            f"(?:{reg})"
            for reg in [
                rf'<font color="({"|".join(_Colors)})">[^<]+</font>',  # Color
                r"^>\s+.+$",  # Reference
            ]
        )
        + r")",
        MULTILINE,
    )

    _MD_V2_PATTERN: Pattern = re_compile(
        r"("
        + "|".join(
            f"(?:{reg})"
            for reg in [
                r"^#{1,6}\s+.+$",  # Title
                r"\*\*.+\*\*",  # Bold
                r"`[^`]+`",  # Inner line code
                r"\[[^\]]+\]\([^\)]+\)",  # Link
                r"\*.+\*",  # Italics
                r"^(\s*[-*+]\s+.+(\n\s{2,}\S.*)*)+$",  # Unordered list
                r"^\d+\.\s+.+$",  # Ordered List
                r"!\[[^\]]+\]\([^\)]+\)",  # Picture
                r"^(>+) .+$",  # References (multi-level support)
                r"^-{3,}$",  # Dividing line
                r"^```[\s\S]+?```$",  # Code block
                r"^\|.+\|(\n\|?[-:]+[-|: ]+)+\n(\|.+\|)+$",  # Table
            ]
        )
        + r")",
        MULTILINE,
    )

    @property
    def _doc_key(self) -> str:
        return "如何使用群机器人"

    def _verify_markdown(
        self, string: str
    ) -> Union[Type[MarkdownBot], Type[MarkdownBotV2], bool]:
        r"""
        Verify whether the string is Markdown format.

        For v1 version:
        - Title 1 - 6:                  r'^#{1,6}\s+.+$'
        - Bold:                         r'\*\*.+\*\*'
        - Link:                         r'\[[^\]]+\]\([^\)]+\)'
        - Code:                         r'`[^`]+`'
        - Reference:                    r'^>\s+.+$'
        - Color (** Uniq feature **):   r'<font color="(info|comment|warning)">[^<]+</font>'

        For v2 version:
        - Title 1 - 6:          r'^#{1,6}\s+.+$'
        - Bold:                 r'\*\*.+\*\*'
        - Link:                 r'\[[^\]]+\]\([^\)]+\)'
        - Code:                 r'`[^`]+`'
        - Italics:              r'\*.+\*'
        - Unordered list:       r'^(\s*[-*+]\s+.+(\n\s{2,}\S.*)*)+$'
        - Ordered List:         r'^\d+\.\s+.+$'
        - Picture:              r'!\[[^\]]+\]\([^\)]+\)'
        - References (multi):   r'^(>+) .+$'
        - Dividing line:        r'^-{3,}$'
        - Code block:           r'^```[\s\S]+?```$'
        - Table:                r'^\|.+\|(\n\|?[-:]+[-|: ]+)+\n(\|.+\|)+$'

        :param string: Raw string.
        :return: Whether the string is Markdown format.
        """
        # Top priority to detect the uniq feature for v1.
        if self._MD_V1_PATTERN.search(string):
            return MarkdownBot
        if self._MD_V2_PATTERN.search(string):
            return MarkdownBotV2
        # Return `False` when can't match content
        return False

    def _guess_message_bot(self, *args, **kwargs) -> Type[_BotT]:
        """
        Guess whether the bot type is Text or Markdown.
        :param args: Positional arguments.
        :param kwargs: Keyword arguments.
        :return: Subclass of AbstractBot.
        """
        if "mentioned_list" in kwargs or "mentioned_mobile_list" in kwargs:
            return TextBot
        if bot := self._verify_markdown(args[0]):
            return bot
        return TextBot

    @verify_file
    def _guess_file_bot(self, file_path: FilePathLike) -> Type[_BotT]:
        """
        Guess whether the bot type is File or Image or Voice.
        :param file_path: File path.
        :return: Subclass of AbstractBot.
        """
        suffix = Path(file_path).suffix
        if suffix == FileFormats.VOICE:
            bot = VoiceBot
        elif suffix in FileFormats.IMAGE:
            bot = ImageBot
        else:
            bot = FileBot
        return bot

    def _verify_arguments(self, *args, **kwargs) -> Type[_BotT]:
        r"""
        Intelligent selection bot, follow the following rules:

        1. Provide `args`, which MUST be either Text or Markdown;

        There are 2 situations:

            Section A:
                Also provide `mentioned_list` or `mentioned_mobile_list` from kwargs;
                This MUST be Text.

            Section B:
                Distinguish using regex to verify whether the `msg` is Markdown format;

        2. Provide `file_path` from kwargs, which MUST be File / Image / Voice;
        Distinguish using file suffix.

            - Voice: MUST be `.amr` file.
            - Image: Either `.png` or `.jpg`.
            - File: Other suffixes.

        3. Provide `articles` from kwargs, which MUST be News;

        4. Complex kwargs, which MUST be either TextCard or NewsCard;
        Distinguish using bot's own required parameters.

            - NewsCard: MUST have `card_image` in kwargs.
            - TextCard: Otherwise default bot.

        :param args: Positional arguments.
        :param kwargs: Keyword arguments.
        :return: Subclass of AbstractBot.
        """
        if args:
            return self._guess_message_bot(*args, **kwargs)
        if "file_path" in kwargs and kwargs["file_path"]:
            return self._guess_file_bot(kwargs["file_path"])
        if "articles" in kwargs and kwargs["articles"]:
            return NewsBot
        if "card_image" in kwargs:
            return NewsCardBot
        return TextCardBot

    def _convert_arguments(self, *args, **kwargs) -> AbstractBot:
        bot_type: Type[_BotT] = args[0]
        return bot_type(self.key)

    def send(
        self,
        msg: str = None,
        /,
        articles: List[Dict[str, str]] = None,
        file_path: FilePathLike = None,
        **kwargs,
    ) -> dict:
        """
        Send a message with automatic type detection.

        This method intelligently determines the message type and routes to
        the appropriate bot implementation. You don't need to specify the
        message type explicitly.

        Args:
            msg (str, optional): Message content. Used for text or markdown messages.
                Supports plain text, Markdown v1, and Markdown v2 syntax.
            articles (List[Dict[str, str]], optional): List of news articles.
                Each article must contain ``title`` and ``url`` keys.
                Maximum 8 articles per message.
            file_path (Union[str, PathLike], optional): Path to file, image, or voice.
                Supported formats:

                - Images: ``.png``, ``.jpg`` (max 2MB)
                - Voice: ``.amr`` (max 2MB, max 60s duration)
                - Files: any format (5B < size < 20MB)
            **kwargs: Additional parameters for specific message types.

                For text messages:
                    - ``mentioned_list`` (List[str]): User IDs to mention
                    - ``mentioned_mobile_list`` (List[str]): Phone numbers to mention

                For template cards:
                    - ``main_title`` (dict): Card title
                    - ``card_action`` (dict): Card action configuration
                    - ``card_image`` (dict): Image for news cards
                    - And many more (see template card documentation)

        Returns:
            dict: API response containing:

                - ``errcode`` (int): 0 for success, non-zero for errors
                - ``errmsg`` (str): Error message if errcode != 0

        Raises:
            ValueError: If parameters are invalid or missing required fields.
            ConnectionRefusedError: If network request fails.
            IOError: If API returns an error response.

        Example:
            Various message types::

                # Simple text
                result = bot.send("Hello!")

                # Text with mentions
                result = bot.send(
                    "Important notice",
                    mentioned_list=["user123", "@all"]
                )

                # Markdown
                result = bot.send("# Title\\n**Bold** text")

                # Image
                result = bot.send(file_path="chart.png")

                # News
                result = bot.send(articles=[{
                    "title": "Article Title",
                    "url": "https://example.com",
                    "description": "Article description",
                    "picurl": "https://example.com/image.jpg"
                }])

                # Template card
                result = bot.send(
                    main_title={"title": "Notification"},
                    card_action={"type": 1, "url": "https://example.com"}
                )

        Note:
            - Maximum message rate: 20 messages per minute per bot
            - Text/Markdown max length: 2048/4096 bytes (UTF-8)
            - Image max size: 2MB
            - Voice max size: 2MB, max duration: 60 seconds
            - File size range: 5B to 20MB

        See Also:
            Official API documentation:
            https://developer.work.weixin.qq.com/document/path/99110
        """
        if msg is not None:
            bot_type = self._verify_arguments(msg, **kwargs)
            bot = self._convert_arguments(bot_type)
        else:
            bot_type = self._verify_arguments(
                articles=articles, file_path=file_path, **kwargs
            )
            bot = self._convert_arguments(bot_type)
        result = bot.send(msg, articles=articles, file_path=file_path, **kwargs)
        return result

    # pylint: disable=too-few-public-methods
    class _MarkdownFeatureProxy:
        """Proxy that routes method calls to appropriate Markdown type."""

        @property
        def green(self) -> Callable:
            """
            Return v1 feature.
            :return:
            """
            return MarkdownBot.green

        @property
        def gray(self) -> Callable:
            """
            Return v1 feature.
            :return:
            """
            return MarkdownBot.gray

        @property
        def orange(self) -> Callable:
            """
            Return v1 feature.
            :return:
            """
            return MarkdownBot.orange

        @property
        def list2table(self) -> Callable:
            """
            Return v2 feature.
            :return:
            """
            return MarkdownBotV2.list2table

    markdown_feature = _MarkdownFeatureProxy()
