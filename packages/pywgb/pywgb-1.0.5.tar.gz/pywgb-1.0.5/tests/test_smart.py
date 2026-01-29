#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Smart bot.

- Author: Rex Zhou <879582094@qq.com>
- Created Time: 2025/6/6 14:40
- Copyright: Copyright © 2025 Rex Zhou. All rights reserved.
"""

from logging import DEBUG, basicConfig
from pathlib import Path
from random import randint
from urllib.parse import urlparse, unquote

from dotenv import load_dotenv

# pylint: disable=import-error
from src.pywgb import SmartBot
from tests.test_main import TEST_VALID_ARTICLES, TEST_VALID_MARKDOWN_V2
from tests.test_main import TEST_VALID_MARKDOWN
from tests.test_main import TEST_VALID_NEWS_CARD
from tests.test_main import TEST_VALID_TEXT_CARD
from tests.test_main import VALID_KEY, env_file

basicConfig(level=DEBUG, format="%(levelname)s %(name)s %(lineno)d %(message)s")
load_dotenv(env_file, override=True)


def test_initial() -> None:
    """
    Test SmartBot initialisation.
    :return:
    """
    # Verify valid key and url
    bot = SmartBot(VALID_KEY)
    assert (
        # pylint: disable=protected-access
        urlparse(unquote(bot.doc)).fragment
        == bot._doc_key
    )
    assert VALID_KEY == bot.key


def test_send() -> None:
    """
    Test basic send.
    :return:
    """
    text = f"This is a test TEXT message: {randint(1, 100)}"
    image = Path(__file__).with_name("test.png")
    file = Path(__file__).with_name("test.txt")
    voice = Path(__file__).with_name("test.amr")
    # Pure V2 markdown without V1 color features
    pure_v2_markdown = """
# Pure V2 Test

*Italics text*

| Column A | Column B |
|----------|----------|
| Value 1  | Value 2  |
"""
    tests = {
        "text": ((text,), {}),
        "text_with_mention": ((text,), {"mentioned_list": ["@all"]}),
        "markdown": ((TEST_VALID_MARKDOWN,), {}),
        "markdown_v2": ((TEST_VALID_MARKDOWN_V2,), {}),
        "markdown_v2_pure": ((pure_v2_markdown,), {}),
        "news": ((), {"articles": TEST_VALID_ARTICLES}),
        "image": ((), {"file_path": image}),
        "file": ((), {"file_path": file}),
        "voice": ((), {"file_path": voice}),
        "text_card": ((), {**TEST_VALID_TEXT_CARD}),
        "news_card": ((), {**TEST_VALID_NEWS_CARD}),
    }
    bot = SmartBot(VALID_KEY)
    print(bot)
    for type_, (args, kwargs) in tests.items():
        print("Testing:", type_)
        result = bot.send(*args, **kwargs)
        assert result["errcode"] == 0
