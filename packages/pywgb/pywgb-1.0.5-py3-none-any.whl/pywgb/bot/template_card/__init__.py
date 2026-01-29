#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Template Card classes

- Author: Rex Zhou <879582094@qq.com>
- Created Time: 2025/6/4 17:30
- Copyright: Copyright © 2025 Rex Zhou. All rights reserved.
"""
from functools import partial
from typing import List, Callable, Dict

from jmespath import search

TemplateCardKeys: List[str] = [
    "source",
    "main_title",
    "quote_area",
    "horizontal_content_list",
    "jump_list",
    "card_action",
]
TemplateCardRequirements: Dict[str, Callable] = {
    "When `quote_area.type` is 1, the `quote_area.url` must be existed": partial(
        search,
        """
                quote_area.type == `1` &&
                (quote_area.url == null || quote_area.url == '')
            """,
    ),
    "When `quote_area.type` is 2, the `quote_area.appid` must be existed": partial(
        search,
        """
                quote_area.type == `2` &&
                (quote_area.appid == null || quote_area.appid == '')
            """,
    ),
    "The `horizontal_content_list.keyname` must be existed": partial(
        search,
        """
                length(
                    (horizontal_content_list || `[]`)[?
                        keyname == null || keyname == ''
                    ]
                ) != `0`
            """,
    ),
    "When `horizontal_content_list.type` is 1, "
    "the `horizontal_content_list.url` must be existed": partial(
        search,
        """
                length(
                    (horizontal_content_list || `[]`)[?
                        type == `1` && (url == null || url == '')
                    ]
                ) != `0`
            """,
    ),
    "When `horizontal_content_list.type` is 2, "
    "the `horizontal_content_list.media_id` must be existed": partial(
        search,
        """
                length(
                    (horizontal_content_list || `[]`)[?
                        type == `2` && (media_id == null || media_id == '')
                    ]
                ) != `0`
            """,
    ),
    "When `horizontal_content_list.type` is 3, "
    "the `horizontal_content_list.userid` must be existed": partial(
        search,
        """
                length(
                    (horizontal_content_list || `[]`)[?
                        type == `3` && (userid == null || userid == '')
                    ]
                ) != `0`
            """,
    ),
    "The `jump_list.title` must be existed": partial(
        search,
        """
                length(
                    (jump_list || `[]`)[?
                        title == null || title == ''
                    ]
                ) != `0`
            """,
    ),
    "When `jump_list.type` is 1, the `jump_list.url` must be existed": partial(
        search,
        """
                length(
                    (jump_list || `[]`)[?
                        type == `1` && (url == null || url == '')
                    ]
                ) != `0`
            """,
    ),
    "When `jump_list.type` is 2, the `jump_list.appid` must be existed": partial(
        search,
        """
                length(
                    (jump_list || `[]`)[?
                        type == `2` && (appid == null || appid == '')
                    ]
                ) != `0`
            """,
    ),
    "The `card_action` and `card_action.type` must be existed": partial(
        search,
        """
                card_action == null ||
                card_action.type == null ||
                card_action.type == ''
            """,
    ),
    "When `card_action.type` is 1, the `card_action.url` must be existed": partial(
        search,
        """
                card_action.type == `1` &&
                (card_action.url == null || card_action.url == '')
            """,
    ),
    "When `card_action.type` is 2, the `card_action.appid` must be existed": partial(
        search,
        """
                card_action.type == `2` &&
                (card_action.appid == null || card_action.appid == '')
            """,
    ),
}
