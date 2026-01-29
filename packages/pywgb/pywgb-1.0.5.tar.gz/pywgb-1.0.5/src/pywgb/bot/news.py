#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
News article message bot implementation.

This module provides the :class:`NewsBot` class for sending news articles
to Wecom Group Bots. Each message can contain up to 8 articles with titles,
descriptions, URLs, and thumbnail images.

Article Format:
    Each article is a dictionary with the following keys:
    
    - ``title`` (str, required): Article title
    - ``url`` (str, required): Article link URL
    - ``description`` (str, optional): Article description
    - ``picurl`` (str, optional): Thumbnail image URL

Limitations:
    - Maximum 8 articles per message
    - Each article must have ``title`` and ``url``

Example:
    Send news articles::

        from pywgb.bot import NewsBot
        
        bot = NewsBot("your-webhook-key")
        
        articles = [
            {
                "title": "Breaking News",
                "description": "Important update",
                "url": "https://example.com/article1",
                "picurl": "https://example.com/thumb1.jpg"
            },
            {
                "title": "Tech Update",
                "description": "New features released",
                "url": "https://example.com/article2",
                "picurl": "https://example.com/thumb2.jpg"
            }
        ]
        
        bot.send(articles=articles)

:author: Rex Zhou <879582094@qq.com>
:copyright: Copyright © 2025 Rex Zhou. All rights reserved.
"""

from ._abstract import ConvertedData, AbstractBot
from .._constants import MediaLimits


class NewsBot(AbstractBot):
    """
    News article message bot for Wecom Group.

    Sends news articles with titles, descriptions, URLs, and thumbnail images.
    Each message can contain up to 8 articles displayed in a card-like format.

    Args:
        key (str): Webhook key or full webhook URL.

    Raises:
        ValueError: If articles parameter is missing, empty, exceeds 8 articles,
            or any article lacks required fields (title, url).

    Example:
        Single article::

            from pywgb.bot import NewsBot

            bot = NewsBot("your-key")
            
            articles = [{
                "title": "Product Launch",
                "description": "New version released",
                "url": "https://example.com/news",
                "picurl": "https://example.com/image.jpg"
            }]
            
            bot.send(articles=articles)

        Multiple articles::

            articles = [
                {
                    "title": "Article 1",
                    "url": "https://example.com/1",
                    "description": "First article",
                    "picurl": "https://example.com/pic1.jpg"
                },
                {
                    "title": "Article 2",
                    "url": "https://example.com/2",
                    "description": "Second article",
                    "picurl": "https://example.com/pic2.jpg"
                },
                # ... up to 8 articles total
            ]
            
            bot.send(articles=articles)

        Minimal article (only required fields)::

            articles = [{
                "title": "Quick Update",
                "url": "https://example.com/update"
            }]
            
            bot.send(articles=articles)

    See Also:
        :class:`NewsCardBot`: For template card style news
        :class:`SmartBot`: For automatic type detection

    Note:
        - Maximum 8 articles per message
        - Required fields: ``title``, ``url``
        - Optional fields: ``description``, ``picurl``
        - Articles displayed in card format
        - Rate limit: 20 messages per minute
    """

    @property
    def _doc_key(self) -> str:
        return "图文类型"

    def _verify_arguments(self, *args, **kwargs) -> None:
        """
        Verify the arguments passed.
        :param args: Positional arguments.
        :param kwargs: Keyword arguments.
        :return:
        """
        try:
            articles = kwargs["articles"]
        except KeyError as error:
            raise ValueError("The articles parameter is required.") from error
        if not articles:
            raise ValueError("The articles parameter is empty.")
        if len(articles) > MediaLimits.NEWS_ARTICLES:
            raise ValueError(
                f"Too many articles. The maximum limit is {MediaLimits.NEWS_ARTICLES}"
            )
        # Check the article's required parameters
        test = kwargs.get("test")
        for index, article in enumerate(articles):
            if not isinstance(article, dict) or test == "article_data_error":
                msg_ = f"The No.{index + 1} article data is not a dict"
                raise ValueError(msg_)
            for param in ["title", "url"]:
                if (
                    param not in article
                    or not article[param]
                    or test == "article_parameter_error"
                ):
                    msg_ = (
                        f"The No.{index + 1} article lack required parameter: {param}"
                    )
                    raise ValueError(msg_)

    # pylint:disable=unused-argument
    def _convert_arguments(self, *args, **kwargs) -> ConvertedData:
        """
        Convert the message to News format.
        :param args: Positional arguments.
        :param kwargs: Other keyword arguments.
        :return: Converted message.
        """
        result = ({"msgtype": "news", "news": {"articles": kwargs["articles"]}},)
        return result, kwargs
