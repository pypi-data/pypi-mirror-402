#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Store successful test units.

- Author: Rex Zhou <879582094@qq.com>
- Created Time: 2025/6/3 10:41
- Copyright: Copyright © 2025 Rex Zhou. All rights reserved.
"""

from logging import DEBUG, basicConfig
from os import getenv
from pathlib import Path
from random import randint
from urllib.parse import urlparse, unquote

from dotenv import load_dotenv
from pytest import raises

# pylint: disable=import-error
from src.pywgb.bot import TextBot, MarkdownBot, NewsBot
from src.pywgb.bot import ImageBot, VoiceBot, FileBot
from src.pywgb.bot import TextCardBot, NewsCardBot, MarkdownBotV2
from tests.test_main import VALID_KEY, env_file, TEST_VALID_MARKDOWN_V2
from tests.test_main import TEST_VALID_MARKDOWN
from tests.test_main import TEST_VALID_ARTICLES
from tests.test_main import TEST_VALID_TEXT_CARD
from tests.test_main import TEST_VALID_NEWS_CARD

basicConfig(level=DEBUG, format="%(levelname)s %(name)s %(lineno)d %(message)s")
load_dotenv(env_file, override=True)


def test_text_initial() -> None:
    """
    Test TextBot initialisation.
    :return:
    """
    valid_url = getenv("VALID_URL")
    print()
    print("Check valid key:", VALID_KEY)
    print("Check valid url:", valid_url)
    # Verify valid key and url
    bot = TextBot(VALID_KEY)
    assert (
        # pylint: disable=protected-access
        urlparse(unquote(bot.doc)).fragment
        == bot._doc_key
    )
    assert VALID_KEY == bot.key
    assert f"TextBot({VALID_KEY})" == str(bot)
    assert valid_url.split("=")[-1] == TextBot(valid_url).key
    # Verify invalid key and url
    invalids = {
        getenv("INVALID_KEY"): "Invalid key format",
        getenv("INVALID_URL"): "Invalid key format",
        None: "Key is required",
    }
    for code, msg in invalids.items():
        with raises(ValueError) as exception_info:
            TextBot(code)
        assert msg in str(exception_info.value)


def test_markdown_initial() -> None:
    """
    Test MarkdownBot initialisation.
    :return:
    """
    # Verify valid key and url
    bot = MarkdownBot(VALID_KEY)
    assert (
        # pylint: disable=protected-access
        urlparse(unquote(bot.doc)).fragment
        == bot._doc_key
    )
    assert VALID_KEY == bot.key


def test_markdown_v2_initial() -> None:
    """
    Test MarkdownBotV2 initialisation.
    :return:
    """
    # Verify valid key and url
    bot = MarkdownBotV2(VALID_KEY)
    assert (
        # pylint: disable=protected-access
        urlparse(unquote(bot.doc)).fragment
        == bot._doc_key
    )
    assert VALID_KEY == bot.key


def test_image_initial() -> None:
    """
    Test ImageBot initialisation.
    :return:
    """
    # Verify valid key and url
    bot = ImageBot(VALID_KEY)
    assert (
        # pylint: disable=protected-access
        urlparse(unquote(bot.doc)).fragment
        == bot._doc_key
    )
    assert VALID_KEY == bot.key


def test_news_initial() -> None:
    """
    Test NewsBot initialisation.
    :return:
    """
    # Verify valid key and url
    bot = NewsBot(VALID_KEY)
    assert (
        # pylint: disable=protected-access
        urlparse(unquote(bot.doc)).fragment
        == bot._doc_key
    )
    assert VALID_KEY == bot.key


# pylint: disable=protected-access
def test_file_initial() -> None:
    """
    Test NewsBot initialisation.
    :return:
    """
    # Verify valid key and url
    bot = FileBot(VALID_KEY)
    assert urlparse(unquote(bot.doc)).fragment == bot._doc_key
    assert VALID_KEY == bot.key
    uploader = bot._uploader
    assert urlparse(unquote(uploader.doc)).fragment == uploader._doc_key
    assert VALID_KEY == uploader.key


def test_voice_initial() -> None:
    """
    Test VoiceBot initialisation.
    :return:
    """
    # Verify valid key and url
    bot = VoiceBot(VALID_KEY)
    assert (
        urlparse(unquote(bot.doc)).fragment == bot._doc_key
    )  # pylint: disable=protected-access
    assert VALID_KEY == bot.key


def test_text_card_initial() -> None:
    """
    Test TextCardBot initialisation.
    :return:
    """
    # Verify valid key and url
    bot = TextCardBot(VALID_KEY)
    assert (
        urlparse(unquote(bot.doc)).fragment == bot._doc_key
    )  # pylint: disable=protected-access
    assert VALID_KEY == bot.key


def test_news_card_initial() -> None:
    """
    Test NewsCardBot initialisation.
    :return:
    """
    # Verify valid key and url
    bot = NewsCardBot(VALID_KEY)
    assert (
        urlparse(unquote(bot.doc)).fragment == bot._doc_key
    )  # pylint: disable=protected-access
    assert VALID_KEY == bot.key


def test_basic_send() -> None:
    """
    Test basic send.
    :return:
    """
    bot = TextBot(getenv("VALID_KEY"))
    print(bot)
    result = bot.send(f"This is a test TEXT message: {randint(1, 100)}")
    print(result)
    assert result["errcode"] == 0
    bot = MarkdownBot(getenv("VALID_KEY"))
    print(bot)
    result = bot.send(TEST_VALID_MARKDOWN)
    print(result)
    assert result["errcode"] == 0
    bot = MarkdownBotV2(getenv("VALID_KEY"))
    print(bot)
    result = bot.send(TEST_VALID_MARKDOWN_V2)
    print(result)
    assert result["errcode"] == 0
    bot = ImageBot(getenv("VALID_KEY"))
    print(bot)
    result = bot.send(file_path=Path(__file__).with_name("test.png"))
    print(result)
    assert result["errcode"] == 0
    bot = NewsBot(getenv("VALID_KEY"))
    print(bot)
    result = bot.send(articles=TEST_VALID_ARTICLES)
    print(result)
    assert result["errcode"] == 0
    bot = FileBot(getenv("VALID_KEY"))
    print(bot)
    result = bot.send(file_path=Path(__file__).with_name("test.png"))
    print(result)
    assert result["errcode"] == 0
    bot = VoiceBot(getenv("VALID_KEY"))
    print(bot)
    result = bot.send(file_path=Path(__file__).with_name("test.amr"))
    print(result)
    assert result["errcode"] == 0


def test_advanced_send() -> None:
    """
    Test advanced send function
    :return:
    """
    bot = TextCardBot(getenv("VALID_KEY"))
    print(bot)
    result = bot.send(**TEST_VALID_TEXT_CARD)
    print(result)
    assert result["errcode"] == 0
    bot = NewsCardBot(getenv("VALID_KEY"))
    print(bot)
    result = bot.send(**TEST_VALID_NEWS_CARD)
    print(result)
    assert result["errcode"] == 0


def test_upload() -> None:
    """
    Test upload function
    :return:
    """
    file = Path(__file__).with_name("test.png")
    bot = TextBot(VALID_KEY)
    result = bot.upload(file)
    print(result)
    assert result
