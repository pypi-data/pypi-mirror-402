#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
All bot classes

- Author: Rex Zhou <879582094@qq.com>
- Created Time: 2025/5/27 13:54
- Copyright: Copyright © 2025 Rex Zhou. All rights reserved.
"""

from ._smart import TextBot, MarkdownBot, ImageBot
from ._smart import NewsBot, FileBot, VoiceBot
from ._smart import TextCardBot, NewsCardBot, SmartBot
from ._smart import MarkdownBotV2

__all__ = [
    "TextBot",
    "MarkdownBot",
    "MarkdownBotV2",
    "ImageBot",
    "NewsBot",
    "FileBot",
    "VoiceBot",
    "TextCardBot",
    "NewsCardBot",
    "SmartBot",
]
