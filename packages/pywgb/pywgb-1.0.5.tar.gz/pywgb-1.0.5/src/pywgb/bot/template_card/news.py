#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
News template card message bot implementation.

This module provides the :class:`NewsCardBot` class for sending news-style
template cards to Wecom Group Bots. News cards feature prominent images,
image-text areas, and vertical content lists for rich visual presentations.

Card Components:
    - ``main_title`` (dict, required): Main title with optional description
    - ``card_image`` (dict, required): Main card image with aspect ratio
    - ``image_text_area`` (dict): Image-text combination area
    - ``vertical_content_list`` (list): Vertical list of content items
    - ``horizontal_content_list`` (list): Horizontal key-value pairs
    - ``jump_list`` (list): Quick action buttons
    - ``card_action`` (dict): Card click action configuration

Requirements:
    - ``main_title`` and ``main_title.title`` must exist
    - ``card_image`` and ``card_image.url`` must exist

Example:
    Product announcement card::

        from pywgb.bot import NewsCardBot
        
        bot = NewsCardBot("your-webhook-key")
        
        bot.send(
            main_title={
                "title": "New Product Launch",
                "desc": "Q1 2026"
            },
            card_image={
                "url": "https://example.com/product.jpg",
                "aspect_ratio": 2.25
            },
            image_text_area={
                "type": 1,
                "url": "https://example.com/product",
                "title": "Revolutionary Features",
                "desc": "Experience the next generation",
                "image_url": "https://example.com/icon.png"
            },
            vertical_content_list=[
                {"title": "Feature 1", "desc": "Advanced AI integration"},
                {"title": "Feature 2", "desc": "Real-time analytics"}
            ],
            card_action={
                "type": 1,
                "url": "https://example.com/learn-more"
            }
        )

:author: Rex Zhou <879582094@qq.com>
:copyright: Copyright © 2025 Rex Zhou. All rights reserved.
"""
from functools import partial
from logging import getLogger
from typing import List

from jmespath import search

from . import TemplateCardKeys, TemplateCardRequirements
from .._abstract import ConvertedData, AbstractBot

logger = getLogger(__name__)


class NewsCardBot(AbstractBot):
    """
    News template card message bot for Wecom Group.

    Sends image-focused template cards with prominent visuals, image-text
    areas, and vertical content lists. Ideal for announcements, reports,
    and visual-heavy notifications.

    Args:
        key (str): Webhook key or full webhook URL.

    Raises:
        ValueError: If required fields are missing or validation fails.
            Required: ``main_title.title``, ``card_image.url``.

    Example:
        System monitoring card::

            from pywgb.bot import NewsCardBot

            bot = NewsCardBot("your-key")
            
            bot.send(
                main_title={
                    "title": "System Health Report",
                    "desc": "Weekly Summary"
                },
                card_image={
                    "url": "https://example.com/chart.png",
                    "aspect_ratio": 2.25
                },
                image_text_area={
                    "type": 1,
                    "url": "https://dashboard.example.com",
                    "title": "All Systems Operational",
                    "desc": "99.9% uptime this week",
                    "image_url": "https://example.com/status-icon.png"
                },
                vertical_content_list=[
                    {"title": "API Server", "desc": "Response time: 45ms"},
                    {"title": "Database", "desc": "Query time: 12ms"},
                    {"title": "Cache", "desc": "Hit rate: 98%"}
                ],
                card_action={
                    "type": 1,
                    "url": "https://dashboard.example.com"
                }
            )

        Event announcement::

            bot.send(
                main_title={"title": "Tech Conference 2026"},
                card_image={
                    "url": "https://example.com/event-banner.jpg",
                    "aspect_ratio": 1.78
                },
                image_text_area={
                    "type": 1,
                    "url": "https://event.example.com",
                    "title": "Register Now",
                    "desc": "Early bird discount available",
                    "image_url": "https://example.com/ticket-icon.png"
                },
                horizontal_content_list=[
                    {"keyname": "Date", "value": "March 15-17, 2026"},
                    {"keyname": "Location", "value": "Convention Center"}
                ],
                card_action={"type": 1, "url": "https://event.example.com/register"}
            )

    See Also:
        :class:`TextCardBot`: For text-focused template cards
        :class:`NewsBot`: For simple news articles
        :class:`SmartBot`: For automatic type detection

    Note:
        - ``main_title.title`` required
        - ``card_image.url`` required
        - ``image_text_area.type``: 1 for URL, 2 for mini-program
        - ``card_image.aspect_ratio``: Recommended 2.25 or 1.78
        - Rate limit: 20 messages per minute
    """

    _VALID_KEYS: List[str] = TemplateCardKeys + [
        "card_image",
        "image_text_area",
        "vertical_content_list",
    ]

    @property
    def _doc_key(self) -> str:
        return "图文展示模版卡片"

    def _verify_arguments(self, *args, **kwargs) -> None:
        """
        Verify the arguments passed.
        :param args: Positional arguments.
        :param kwargs: Keyword arguments.
        :return:
        """
        reqs = {
            "Both `main_title` and `main_title.title` must be existed": partial(
                search,
                """
                    main_title == null ||
                    main_title.title == null ||
                    main_title.title == ''
                """,
            ),
            "Both `card_image` and `card_image.url` must be existed": partial(
                search,
                """
                    card_image == null ||
                    card_image.url == null ||
                    card_image.url == ''
                """,
            ),
            "When `image_text_area.type` is 1, the `image_text_area.url` must be existed": partial(
                search,
                """
                    image_text_area.type == `1` &&
                    (image_text_area.url == null || image_text_area.url == '')
                """,
            ),
            # pylint: disable=line-too-long
            "When `image_text_area.type` is 2, the `image_text_area.appid` must be existed": partial(
                search,
                """
                    image_text_area.type == `2` &&
                    (image_text_area.appid == null || image_text_area.appid == '')
                """,
            ),
            "The `image_text_area.image_url` must be existed": partial(
                search,
                """
                    image_text_area != null &&
                    (image_text_area.image_url == null || image_text_area.image_url == '')
                """,
            ),
            "The `vertical_content_list.title` must be existed": partial(
                search,
                """
                    length(
                        (vertical_content_list || `[]`)[?
                            title == null || title == ''
                        ]
                    ) != `0`
                """,
            ),
            **TemplateCardRequirements,
        }
        for msg, cmd in reqs.items():
            logger.debug("Validating parameter error: %s", msg)
            if cmd(kwargs):
                logger.critical("[NO PASS] Parameter validation error: %s", msg)
                raise ValueError(msg)

    def _convert_arguments(self, *args, **kwargs) -> ConvertedData:
        """
        Convert the message to text card format data.
        :param args: Positional arguments.
        :param kwargs: Other keyword arguments.
        :return: Converted data.
        """
        kw_ = {key: val for key, val in kwargs.items() if key in self._VALID_KEYS}
        result = (
            {
                "msgtype": "template_card",
                "template_card": {
                    "card_type": "news_notice",
                    **kw_,
                },
            },
        )
        return result, kwargs
