#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown message bot implementation.

This module provides two Markdown bot classes:

- :class:`MarkdownBot`: Markdown v1 with unique colored text feature
- :class:`MarkdownBotV2`: Markdown v2 with extended syntax (tables, multi-level lists, etc.)

Markdown v1 Syntax:
    - Titles (1-6 levels): ``# Title``
    - Bold: ``**text**``
    - Links: ``[text](url)``
    - Inline code: ```code```
    - Quotes: ``> quote``
    - **Colored text** (unique): ``<font color="info|comment|warning">text</font>``

Markdown v2 Additional Syntax:
    - Italics: ``*text*``
    - Unordered lists: ``- item``
    - Ordered lists: ``1. item``
    - Images: ``![alt](url)``
    - Multi-level quotes: ``>> quote``
    - Dividers: ``---``
    - Code blocks: ` ```code``` `
    - Tables: Pipe-separated format

Example:
    Markdown v1 with colors::

        from pywgb.bot import MarkdownBot
        
        bot = MarkdownBot("your-key")
        msg = f"Status: {MarkdownBot.green('Success')}"
        bot.send(msg)
    
    Markdown v2 with table::
    
        from pywgb.bot import MarkdownBotV2
        
        bot = MarkdownBotV2("your-key")
        table = [["Name", "Age"], ["Alice", "30"]]
        msg = f"# Report\\n{MarkdownBotV2.list2table(table)}"
        bot.send(msg)

:author: Rex Zhou <879582094@qq.com>
:copyright: Copyright © 2025 Rex Zhou. All rights reserved.
"""
from enum import Enum
from typing import Union, List

from ._abstract import ConvertedData, AbstractBot
from .text import check_args
from .._constants import MessageLimits


class MarkdownBot(AbstractBot):
    """
    Markdown v1 message bot with colored text support.

    Supports standard Markdown syntax plus Wecom's unique colored text feature.
    Maximum message length is 4096 bytes (UTF-8 encoded).

    Supported Syntax:
        - Titles: ``# H1`` to ``###### H6``
        - Bold: ``**bold text**``
        - Links: ``[link text](https://url.com)``
        - Inline code: ```inline code```
        - Quotes: ``> quote text``
        - **Colored text**: Use class methods ``green()``, ``gray()``, ``orange()``

    Attributes:
        _MAX_LENGTH (int): Maximum message length in bytes (4096).

    Args:
        key (str): Webhook key or full webhook URL.

    Example:
        Basic Markdown::

            from pywgb.bot import MarkdownBot

            bot = MarkdownBot("your-key")
            msg = '''
            # Project Status

            **Author**: Rex

            > This is a quote

            Visit [our site](https://example.com)
            '''
            bot.send(msg)

        With colored text::

            status = MarkdownBot.green("Online")
            warning = MarkdownBot.orange("High Load")
            info = MarkdownBot.gray("Last updated: 2025-01-16")

            msg = f"Server Status: {status}\\nWarning: {warning}\\n{info}"
            bot.send(msg)

    See Also:
        :class:`MarkdownBotV2`: For extended Markdown v2 syntax
        :class:`TextBot`: For plain text messages

    Note:
        The colored text feature is unique to Wecom and not part of
        standard Markdown syntax.
    """

    class _Color(Enum):
        """Markdown _color enum"""

        INFO = "green"
        COMMENT = "gray"
        WARNING = "orange"

        @classmethod
        def get_valid_colors(cls):
            """Return list of valid colors"""
            return [_.value for _ in cls]

        @classmethod
        def get_valid_codes(cls):
            """Return list of valid codes"""
            return [_.name for _ in cls]

    @property
    def _doc_key(self) -> str:
        return "markdown类型"

    def _verify_arguments(self, *args, **kwargs) -> None:
        """
        Verify the arguments passed.
        :param args: Positional arguments passed.
        :param kwargs: Keyword arguments passed.
        :return:
        """
        check_args(*args, maximum=MessageLimits.MARKDOWN)

    def _convert_arguments(self, *args, **kwargs) -> ConvertedData:
        """
        Convert the message to Markdown format data.
        :param args: Positional arguments.
        :param kwargs: Other keyword arguments.
        :return: Converted data.
        """
        result = ({"msgtype": "markdown", "markdown": {"content": args[0].strip()}},)
        return result, kwargs

    @classmethod
    def _color(cls, raw: str, color: Union[str, _Color]) -> str:
        """
        Convert normal string to colorful string.
        :param raw: Raw string.
        :param color: Specify _color. Support: green | gray | orange
        :return: Colorized string.
        """
        if isinstance(color, str):
            try:
                color = cls._Color(color.lower())
            except ValueError as error:
                valid_colors = cls._Color.get_valid_colors()
                raise ValueError(
                    f"Invalid color '{color}'. Valid options: {valid_colors}"
                ) from error
        result = f'<font color="{color.name.lower()}">{raw}</font>'
        return result

    @classmethod
    def green(cls, text: str) -> str:
        """
        Create green colored text (info style).

        Args:
            text (str): Text to be colored.

        Returns:
            str: Markdown formatted string with green color.

        Example:
            ::

                success_msg = MarkdownBot.green("Operation successful")
                # Returns: '<font color="info">Operation successful</font>'
        """
        return cls._color(text, cls._Color.INFO)

    @classmethod
    def gray(cls, text: str) -> str:
        """
        Create gray colored text (comment style).

        Args:
            text (str): Text to be colored.

        Returns:
            str: Markdown formatted string with gray color.

        Example:
            ::

                note = MarkdownBot.gray("Additional information")
                # Returns: '<font color="comment">Additional information</font>'
        """
        return cls._color(text, cls._Color.COMMENT)

    @classmethod
    def orange(cls, text: str) -> str:
        """
        Create orange colored text (warning style).

        Args:
            text (str): Text to be colored.

        Returns:
            str: Markdown formatted string with orange color.

        Example:
            ::

                warning = MarkdownBot.orange("High CPU usage detected")
                # Returns: '<font color="warning">High CPU usage detected</font>'
        """
        return cls._color(text, cls._Color.WARNING)


class MarkdownBotV2(AbstractBot):
    """
    Markdown v2 message bot with extended syntax support.

    Supports all Markdown v1 features (except colored text) plus additional
    syntax including tables, multi-level lists, images, and code blocks.
    Maximum message length is 4096 bytes (UTF-8 encoded).

    Extended Syntax (v2 only):
        - Italics: ``*italic text*``
        - Unordered lists: ``- item`` (supports nesting)
        - Ordered lists: ``1. item``
        - Images: ``![alt text](image_url)``
        - Multi-level quotes: ``>> level 2 quote``
        - Horizontal dividers: ``---``
        - Code blocks: ` ```language\\ncode\\n``` `
        - Tables: Pipe-separated format

    Attributes:
        _MAX_LENGTH (int): Maximum message length in bytes (4096).

    Args:
        key (str): Webhook key or full webhook URL.

    Example:
        Comprehensive Markdown v2::

            from pywgb.bot import MarkdownBotV2

            bot = MarkdownBotV2("your-key")

            # Create table
            data = [
                ["Name", "Status", "Score"],
                ["Alice", "Active", "95"],
                ["Bob", "Inactive", "87"]
            ]
            table = MarkdownBotV2.list2table(data)

            msg = f'''
            # Project Report

            ## Team Performance

            {table}

            ### Notes
            - *Important*: Review pending
            - **Deadline**: 2025-01-20

            > Main objective
            >> Sub-objective

            ---

            ```python
            def hello():
                print("Hello, World!")
            ```

            ![Chart](https://example.com/chart.png)
            '''

            bot.send(msg)

    See Also:
        :class:`MarkdownBot`: For Markdown v1 with colored text
        :meth:`list2table`: Convert list to Markdown table

    Note:
        Markdown v2 does NOT support the colored text feature from v1.
        Choose v1 if you need colored text, v2 if you need tables/lists.
    """

    @property
    def _doc_key(self) -> str:
        return "markdown-v2类型"

    def _verify_arguments(self, *args, **kwargs) -> None:
        """
        Verify the arguments passed.
        :param args: Positional arguments passed.
        :param kwargs: Keyword arguments passed.
        :return:
        """
        check_args(*args, maximum=MessageLimits.MARKDOWN)

    def _convert_arguments(self, *args, **kwargs) -> ConvertedData:
        """
        Convert the message to Markdown format data.
        :param args: Positional arguments.
        :param kwargs: Other keyword arguments.
        :return: Converted data.
        """
        result = (
            {"msgtype": "markdown_v2", "markdown_v2": {"content": args[0].strip()}},
        )
        return result, kwargs

    @classmethod
    def list2table(cls, table: List[List[str]]) -> str:
        """
        Convert a 2D list to Markdown table format.

        The first row is treated as the table header. Requires at least
        2 rows (header + 1 data row). Returns empty string if insufficient data.

        Column Alignment:
            - First column: Left-aligned
            - Middle columns: Center-aligned
            - Last column: Right-aligned

        Args:
            table (List[List[str]]): 2D list where first row is headers.
                All rows should have the same number of columns.

        Returns:
            str: Markdown formatted table string, or empty string if table
                has fewer than 2 rows.

        Example:
            ::

                data = [
                    ["Name", "Age", "Score"],
                    ["Alice", "25", "95"],
                    ["Bob", "30", "87"],
                    ["Charlie", "28", "92"]
                ]

                table_md = MarkdownBotV2.list2table(data)
                print(table_md)
                # Output:
                # | Name | Age | Score |
                # | :----- | :----: | -------: |
                # | Alice | 25 | 95 |
                # | Bob | 30 | 87 |
                # | Charlie | 28 | 92 |

        Note:
            - Minimum 2 rows required (header + data)
            - Empty or single-row lists return empty string
            - All cells are converted to strings automatically
        """
        if not table or len(table) < 2:
            return ""

        # Parse headers and rows
        headers, rows = table[0], table[1:]

        # Generate header line
        header_line = "| " + " | ".join(headers) + " |"

        # Generate split line
        separator = "|"
        for i in range(len(headers)):
            if i == 0:
                separator += " :----- |"
            elif i == len(headers) - 1:
                separator += " -------: |"
            else:
                separator += " :----: |"

        # Generate data rows
        data_lines = []
        for row in rows:
            data_lines.append("| " + " | ".join(row) + " |")

        # Merge all rows
        markdown_table = "\n".join([header_line, separator] + data_lines)
        return markdown_table
