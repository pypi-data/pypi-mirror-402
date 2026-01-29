#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wecom(A.K.A. WeChat Work) Group Bot python API.

This module provides a comprehensive Python API for interacting with
Wecom (WeChat Work) Group Bots. It supports multiple message types including
text, markdown, images, files, voice messages, news articles, and template cards.

The main entry point is the :class:`SmartBot` class, which automatically
detects the message type and uses the appropriate bot implementation.

Example:
    Basic usage with SmartBot::

        from pywgb import SmartBot

        bot = SmartBot("your-webhook-key-here")
        
        # Send text message
        bot.send("Hello, World!")
        
        # Send markdown message
        bot.send("# Title\\n**Bold text**")
        
        # Send image
        bot.send(file_path="path/to/image.png")

See Also:
    - Official Documentation: https://developer.work.weixin.qq.com/document/path/99110
    - GitHub Repository: https://github.com/ChowRex/pywgb

:author: Rex Zhou <879582094@qq.com>
:copyright: Copyright © 2025 Rex Zhou. All rights reserved.
:license: MIT
"""

__author__ = "Rex Zhou"
__copyright__ = "Copyright © 2025 Rex Zhou. All rights reserved."
__credits__ = [__author__]
__license__ = "MIT"
__maintainer__ = __author__
__email__ = "879582094@qq.com"

from importlib.metadata import version

from . import bot
from .bot import SmartBot

__version__ = version("pywgb")
__all__ = ["bot", "SmartBot"]
