#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Voice message bot implementation.

This module provides the :class:`VoiceBot` class for sending voice messages
to Wecom Group Bots. Voice files are uploaded as temporary media and referenced
by media_id.

Supported Format:
    - AMR (``.amr``) only

Limitations:
    - Size: 5B < size < 2MB
    - Duration: Maximum 60 seconds
    - Format: AMR only (no MP3, WAV, etc.)

Duration Check:
    Duration validation requires the ``pydub`` package. Install with::
    
        pip install "pywgb[all]"
    
    Without ``pydub``, duration check is skipped with a warning.

Example:
    Send a voice message::

        from pywgb.bot import VoiceBot
        
        bot = VoiceBot("your-webhook-key")
        bot.send(file_path="recording.amr")

:author: Rex Zhou <879582094@qq.com>
:copyright: Copyright © 2025 Rex Zhou. All rights reserved.
"""
from logging import getLogger
from pathlib import Path

from ._abstract import ConvertedData, AbstractBot
from .._constants import FileSizeLimits as Limits, FileFormats, MediaLimits
from .._deco import verify_file

logger = getLogger(__name__)


class VoiceBot(AbstractBot):
    """
    Voice message bot for Wecom Group.

    Sends voice messages in AMR format. The voice file is uploaded to Wecom's
    temporary media storage and referenced by media_id (valid for 3 days).

    Duration validation requires the optional ``pydub`` dependency. Without it,
    duration check is skipped with a warning message.

    Args:
        key (str): Webhook key or full webhook URL.

    Raises:
        ValueError: If file format is not AMR, size is out of range (5B-2MB),
            or duration exceeds 60 seconds.
        FileNotFoundError: If the specified voice file doesn't exist.

    Example:
        Basic usage::

            from pywgb.bot import VoiceBot

            bot = VoiceBot("your-key")
            bot.send(file_path="recording.amr")

        With full installation (duration check)::

            # Install with: pip install "pywgb[all]"
            bot = VoiceBot("your-key")
            bot.send(file_path="message.amr")  # Duration validated

    See Also:
        :class:`FileBot`: For sending voice as file attachment
        :class:`SmartBot`: For automatic type detection

    Note:
        - Format: AMR only (use audio conversion tools if needed)
        - Size: 5B < size < 2MB
        - Duration: Maximum 60 seconds (requires pydub)
        - Media ID valid for 3 days after upload
        - Rate limit: 20 messages per minute
    """

    @property
    def _doc_key(self) -> str:
        return "语音类型"

    @verify_file
    def _verify_arguments(self, *args, **kwargs) -> None:
        """
        Verify the arguments passed.
        :param args: Positional arguments.
        :param kwargs: Keyword arguments.
        :return:
        """
        file_path = Path(kwargs["file_path"])
        test = kwargs.get("test")
        # Check format, only support: `.amr`
        if (
            file_path.suffix.lower() != FileFormats.VOICE
            or test == "wrong_format_voice"
        ):
            raise ValueError(f"Just support voice type: {FileFormats.VOICE}")

    # pylint:disable=unused-argument
    def _convert_arguments(self, *args, **kwargs) -> ConvertedData:
        """
        Convert the message to Voice format.
        :param args: Positional arguments.
        :param kwargs: Other keyword arguments.
        :return: Converted message.
        """
        file_path = kwargs["file_path"]
        # Check voice size, only smaller than `2M` and large than `5B`
        with open(file_path, "rb") as _:
            content = _.read()
        size_range = Limits.VOICE_MIN < len(content) < Limits.VOICE_MAX
        test = kwargs.get("test")
        if not size_range or test == "oversize_voice":
            raise ValueError(
                f"The voice size is out of range: {Limits.VOICE_MIN} < SIZE < {Limits.VOICE_MAX}"
            )
        # Check voice duration, only less than `60s`
        try:
            # pylint: disable=import-outside-toplevel
            from pydub import AudioSegment

            audio = AudioSegment.from_file(
                file_path, format=FileFormats.VOICE.lstrip(".")
            )
            print("Checking the duration of the voice file...")
        except ImportError as error:  # pragma: no cover
            logger.debug("Raised error: %s", error)
            logger.warning("Full feature requires `pydub` to be installed.")
            logger.warning(
                'Re-install this package using `pip install "pywgb[all]"` will fix this warning.'
            )
            print("Required package `pydub` not found. Skip check duration...")
            audio = []
        if len(audio) / 1000 > MediaLimits.VOICE_DURATION or test == "overlong_voice":
            raise ValueError(
                f"The voice duration is longer than {MediaLimits.VOICE_DURATION}s"
            )
        media_id = self.upload(file_path)
        result = {"msgtype": "voice", "voice": {"media_id": media_id}}
        return (result,), kwargs
