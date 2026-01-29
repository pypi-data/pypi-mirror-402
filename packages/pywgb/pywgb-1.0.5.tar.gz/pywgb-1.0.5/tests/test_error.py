#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test error module

- Author: Rex Zhou <879582094@qq.com>
- Created Time: 2025/5/27 14:58
- Copyright: Copyright © 2025 Rex Zhou. All rights reserved.
"""

from logging import DEBUG, basicConfig
from os import getenv
from pathlib import Path

from dotenv import load_dotenv
from pytest import raises
from yaml import safe_load

# pylint: disable=import-error
from src.pywgb.bot import TextBot, MarkdownBot, NewsBot
from src.pywgb.bot import ImageBot, VoiceBot, FileBot
from src.pywgb.bot import TextCardBot, NewsCardBot
from tests.test_main import env_file, errors_file, TEST_VALID_ARTICLES

basicConfig(level=DEBUG, format="%(levelname)s %(name)s %(lineno)d %(message)s")
load_dotenv(env_file, override=True)


def test_overheat() -> None:
    """
    Test overheat function
    :return:
    """
    bot = TextBot(getenv("VALID_KEY"))
    bot.send("This message was delayed by overheat", test="overheat")


def test_request_exception() -> None:
    """
    Test request exception
    :return:
    """
    bot = TextBot(getenv("VALID_KEY"))
    with raises(ConnectionRefusedError) as exception_info:
        bot.send(
            "This message WON'T be sent, cause by request error", test="request_error"
        )
    assert "Unable to initiate API request correctly" in str(exception_info.value)
    with raises(IOError) as exception_info:
        bot.send("This message WON'T be sent, cause by API error", test="api_error")
    assert "Request failed, please refer to the official manual" in str(
        exception_info.value
    )


def test_verify_text_error() -> None:
    """
    Test TEXT verification error.
    :return:
    """
    bot = TextBot(getenv("VALID_KEY"))
    with raises(ValueError) as error:
        bot.send()
    assert "The msg parameter is required" in str(error.value)
    with raises(ValueError) as error:
        bot.send("")
    assert "Can't send empty message" in str(error.value)
    with raises(ValueError) as error:
        bot.send("1" * 2049)
    assert "The msg parameter is too long" in str(error.value)
    err_msg = "parameter should be a list of strings"
    tests = [
        [123],
        (123,),
    ]
    for test in tests:
        with raises(ValueError) as error:
            bot.send(
                "This message won't be sent, cause verify error.",
                mentioned_mobile_list=test,
            )
        assert err_msg in str(error.value)


def test_verify_markdown_error() -> None:
    """
    Test MARKDOWN verification error.
    :return:
    """
    bot = MarkdownBot(getenv("VALID_KEY"))
    with raises(ValueError) as error:
        bot.send()
    assert "The msg parameter is required" in str(error.value)
    with raises(ValueError) as error:
        bot.send("")
    assert "Can't send empty message" in str(error.value)
    with raises(ValueError) as error:
        # pylint: disable=protected-access
        bot._color("This will raise an exception", "red")
    assert "Invalid color" in str(error.value)


def test_verify_news_error() -> None:
    """
    Test News verification error.
    :return:
    """
    bot = NewsBot(getenv("VALID_KEY"))
    # Test empty articles
    with raises(ValueError) as exception_info:
        bot.send()
    assert "The articles parameter is required" in str(exception_info.value)
    with raises(ValueError) as exception_info:
        bot.send(articles=[])
    assert "The articles parameter is empty" in str(exception_info.value)
    # Test oversize articles
    with raises(ValueError) as exception_info:
        articles = [TEST_VALID_ARTICLES[0] for _ in range(9)]
        bot.send(articles=articles)
    assert "Too many articles." in str(exception_info.value)
    # Test data error and parameter error
    tests = {
        "article_data_error": "data is not a dict",
        "article_parameter_error": "lack required parameter",
    }
    for code, msg in tests.items():
        with raises(ValueError) as exception_info:
            bot.send(articles=TEST_VALID_ARTICLES, test=code)
        assert msg in str(exception_info.value)


def test_verify_image_error() -> None:
    """
    Test image verification error.
    :return:
    """
    bot = ImageBot(getenv("VALID_KEY"))
    with raises(ValueError) as exception_info:
        bot.send()
    assert "The file_path parameter is required" in str(exception_info.value)
    file = Path(__file__).with_name("test.png")
    mapper = {
        "wrong_format_image": "Just support image type:",
        "oversize_image": "The image is too large, more than 2M",
    }
    for code, msg in mapper.items():
        with raises(ValueError) as exception_info:
            bot.send(file_path=file, test=code)
        assert msg in str(exception_info.value)


def test_verify_file_error() -> None:
    """
    Test verify file error.
    :return:
    """
    bot = FileBot(getenv("VALID_KEY"))
    # Test lack file
    with raises(ValueError) as exception_info:
        bot.send()
    assert "The file_path parameter is required" in str(exception_info.value)
    # Test empty file
    with raises(ValueError) as exception_info:
        bot.send(file_path=None)
    assert "The file_path parameter is required" in str(exception_info.value)
    # Test invalid file
    with raises(ValueError) as exception_info:
        bot.send(file_path="234234234.txt")
    assert "The file_path parameter not exists" in str(exception_info.value)
    # Test oversize file
    file = Path(__file__).with_name("test.png")
    with raises(ValueError) as exception_info:
        bot.send(file_path=file, test="oversize_file")
    assert "The file size is out of range" in str(exception_info.value)


def test_verify_voice_error() -> None:
    """
    Test voice verification error.
    :return:
    """
    bot = VoiceBot(getenv("VALID_KEY"))
    # Test lack file
    with raises(ValueError) as exception_info:
        bot.send()
    assert "The file_path parameter is required" in str(exception_info.value)
    # Test invalid file format
    file = Path(__file__).with_name("test.png")
    with raises(ValueError) as exception_info:
        bot.send(file_path=file, test="wrong_format_voice")
    assert "Just support voice type:" in str(exception_info.value)
    # Test overlong and oversize voice
    file = Path(__file__).with_name("test.amr")
    with raises(ValueError) as exception_info:
        bot.send(file_path=file, test="oversize_voice")
    assert "The voice size is out of range" in str(exception_info.value)
    with raises(ValueError) as exception_info:
        bot.send(file_path=file, test="overlong_voice")
    assert "The voice duration is longer than 60s" in str(exception_info.value)


def test_verify_text_card_error() -> None:
    """
    Test Text Card verification error.
    :return:
    """
    bot = TextCardBot(getenv("VALID_KEY"))
    with open(errors_file, "r", encoding="utf-8") as _:
        tests = safe_load(_)
    for err_msg, kwargs in tests["text"].items():
        with raises(ValueError) as error:
            bot.send(**kwargs)
        assert err_msg in str(error.value)


def test_verify_news_card_error() -> None:
    """
    Test News Card verification error.
    :return:
    """
    bot = NewsCardBot(getenv("VALID_KEY"))
    with open(errors_file, "r", encoding="utf-8") as _:
        tests = safe_load(_)
    for err_msg, kwargs in tests["news"].items():
        with raises(ValueError) as error:
            bot.send(**kwargs)
        assert err_msg in str(error.value)
