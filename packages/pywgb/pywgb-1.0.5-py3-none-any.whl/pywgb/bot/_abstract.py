#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Abstract base classes for Wecom Group Bot implementations.

This module provides the foundational abstract classes that all bot types
inherit from. It defines the common interface, webhook URL handling, API
communication, and media upload functionality.

Classes:
    - :class:`_Basic`: Base class with webhook URL parsing and validation
    - :class:`_MediaUploader`: Handles temporary media file uploads
    - :class:`AbstractBot`: Main abstract class for all bot implementations

Type Aliases:
    - ``FilePathLike``: Union[str, PathLike] for file path parameters
    - ``ConvertedData``: Tuple[Tuple[Dict[str, str]], Dict[str, str]] for converted message data

Architecture:
    All bot classes follow this inheritance hierarchy::
    
        _Basic
          ├── _MediaUploader (for file/voice uploads)
          └── AbstractBot (main bot interface)
                ├── TextBot
                ├── MarkdownBot
                ├── ImageBot
                ├── VoiceBot
                ├── FileBot
                ├── NewsBot
                ├── TextCardBot
                ├── NewsCardBot
                └── SmartBot

Example:
    Creating a custom bot (advanced usage)::

        from pywgb.bot._abstract import AbstractBot, ConvertedData
        
        class CustomBot(AbstractBot):
            @property
            def _doc_key(self) -> str:
                return "custom-type"
            
            def _verify_arguments(self, *args, **kwargs) -> None:
                # Validation logic
                pass
            
            def _convert_arguments(self, *args, **kwargs) -> ConvertedData:
                # Conversion logic
                return ({"msgtype": "text", "text": {"content": "..."}},), kwargs

:author: Rex Zhou <879582094@qq.com>
:copyright: Copyright © 2025 Rex Zhou. All rights reserved.
"""
__all__ = ["AbstractBot", "FilePathLike", "ConvertedData"]

from abc import ABC, abstractmethod
from functools import partial
from logging import getLogger
from os import PathLike
from pathlib import Path
from typing import Union, Tuple, Dict, List
from urllib.parse import urlparse, parse_qs, urljoin, quote
from uuid import UUID

from requests import Session, session

from .._deco import handle_request_exception, verify_file
from .._deco import detect_overheat, verify_and_convert_arguments

logger = getLogger(__name__)
FilePathLike = Union[str, PathLike]
ConvertedData = Tuple[Tuple[Dict[str, str]], Dict[str, str]]


class _Basic(ABC):
    """
    Base class for all Wecom Group Bot implementations.

    Provides core functionality for webhook URL parsing, UUID validation,
    and API endpoint management. This class is not meant to be instantiated
    directly.

    Attributes:
        _DOC_URL (str): Base URL for Wecom API documentation
        _API_BASE_URL (str): Base URL for Wecom API endpoints
        key (str): Validated webhook key (UUID format)
        _session (Session): Requests session for API calls

    Args:
        key (str): Webhook key or full webhook URL. Accepts:
            - UUID string: ``"xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"``
            - Full URL: ``"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=UUID"``

    Raises:
        ValueError: If key format is invalid or missing.

    Note:
        This is an internal base class. Use concrete bot classes like
        :class:`TextBot`, :class:`ImageBot`, etc. instead.
    """

    # The base path of the document
    _DOC_URL: str = "https://developer.work.weixin.qq.com/document/path/99110"
    # API Endpoint base url
    _API_BASE_URL: str = "https://qyapi.weixin.qq.com"

    def __init__(self, key: str) -> None:
        """
        Initialize the class.
        :param key: The key of group bot webhook url.
        """
        if key is None:
            raise ValueError("Key is required")
        self.key = self._verify_uuid(key.strip())
        self._session: Session = session()

    @staticmethod
    def _parse_webhook_url(url: str) -> str:
        """
        Parse webhook url into key string.
        :param url: Webhook url.
        :return: Key string.
        """
        # If the key passed by url, split and parse it.
        try:
            query = urlparse(url).query
            params = parse_qs(query)
            if "key" not in params or not params["key"]:
                raise ValueError("Missing 'key' parameter in URL")
            return params["key"][0]
        except Exception as error:
            msg = f"Invalid webhook URL {url}."
            logger.critical(msg)
            raise ValueError(msg) from error

    def _verify_uuid(self, key: Union[str, UUID], max_attempts: int = 2) -> str:
        """
        Verify the key weather is UUID format.
        :param key: Key string
        :param max_attempts: Max number of attempts.
        :return: Result bool
        """
        if max_attempts <= 0:  # pragma: no cover
            raise ValueError("Maximum verification attempts exceeded")
        # The standard key format is UUID format.
        if isinstance(key, UUID):  # pragma: no cover
            return str(key)
        try:
            UUID(key)
            return key
        except (ValueError, TypeError, AttributeError) as error:
            try:
                key = self._parse_webhook_url(key)
                return self._verify_uuid(key, max_attempts - 1)
            except ValueError:
                ...
            raise ValueError(f"Invalid key format: {key}") from error

    def __repr__(self) -> str:
        """
        Return the class name.
        :return: Class name.
        """
        return f"{self.__class__.__name__}({self.key})"

    @property
    def _api_url(self) -> str:
        """
        Returns the address of the spliced endpoint url.
        :return: Endpoint url
        """
        end_point = urljoin(self._API_BASE_URL, self._api_path)
        return end_point

    @property
    @abstractmethod
    def _api_path(self) -> str:
        """
        The path of the API Endpoint.
        :return: path of the API Endpoint.
        """

    @property
    @abstractmethod
    def _doc_key(self) -> str:
        """
        The key of the document description.
        :return: key of the document description
        """

    @property
    def doc(self) -> str:
        """
        API URL of the document description
        :return: URL of the document
        """
        url = f"{self._DOC_URL}#{quote(self._doc_key)}"
        return url


class _MediaUploader(_Basic):
    """
    Media file uploader for voice and file messages.

    Handles uploading files to Wecom's temporary media storage. Uploaded
    files receive a media_id that remains valid for 3 days.

    Supported file types:
        - Voice: AMR format (``file_type="voice"``)
        - File: Any other format (``file_type="file"``)

    Args:
        key (str): Webhook key or full webhook URL.

    Example:
        Direct usage (typically used internally)::

            uploader = _MediaUploader("your-key")
            media_id = uploader.upload("document.pdf")
            print(f"Media ID: {media_id}")  # Valid for 3 days

    Note:
        This class is used internally by :class:`VoiceBot` and :class:`FileBot`.
        Most users should use those classes instead of calling this directly.
    """

    @property
    def _api_path(self) -> str:
        """
        The path of the API Endpoint.
        :return: path of the API Endpoint.
        """
        return "cgi-bin/webhook/upload_media"

    @property
    def _doc_key(self) -> str:
        """
        The key of the document description.
        :return: key of the document description
        """
        return "文件上传接口"

    @handle_request_exception
    def _upload_temporary_file(self, file_path: Path, file_type: str) -> dict:
        """
        Upload temporary file from file path.
        :param file_path: File path.
        :param file_type: File type.
        :return:
        """
        kwargs = {"url": self._api_url, "params": {"key": self.key, "type": file_type}}
        cmd = partial(self._session.post, **kwargs)
        with open(file_path, "rb") as files:
            response = cmd(files={"media": files})
        result = response.json()
        return result

    @verify_file
    def upload(self, file_path: FilePathLike, /, **kwargs) -> str:
        """
        Upload voice and file.
        :param file_path: The path of the file.
        :param kwargs: Other keyword arguments.
        :return: Result dict.
        """
        file_path: Path = Path(file_path)
        # Only support `AMR` format for voice, others must be file type
        file_type: str = "voice" if file_path.suffix == ".amr" else "file"
        logger.debug("~~~~ %s ~~~~", self.upload.__name__)
        logger.debug("File path: %s", file_path)
        logger.debug("Other kwargs: %s", kwargs)
        logger.debug("API endpoint URL: %s", self._api_url)
        result = self._upload_temporary_file(file_path, file_type)
        logger.debug("~~~~ %s ~~~~", self.upload.__name__)
        logger.info("%s has been uploaded: %s", file_type.capitalize(), result)
        return result["media_id"]


class AbstractBot(_Basic, ABC):
    """
    Abstract base class for all Wecom Group Bot implementations.

    Defines the common interface that all bot types must implement. Provides
    the core ``send()`` method, media upload functionality, and overheat
    detection (rate limiting).

    All concrete bot classes (TextBot, ImageBot, etc.) inherit from this
    class and must implement:
        - ``_doc_key`` property: Documentation reference key
        - ``_verify_arguments()``: Argument validation logic
        - ``_convert_arguments()``: Message format conversion logic

    Attributes:
        _HEADERS (dict): Default HTTP headers for API requests
        _uploader (_MediaUploader): Media file uploader instance
        _overheat (int): Instance-level overheat counter for rate limiting

    Args:
        key (str): Webhook key or full webhook URL.

    Example:
        Using concrete implementations::

            from pywgb.bot import TextBot, ImageBot
            
            # Text message
            text_bot = TextBot("your-key")
            text_bot.send("Hello, World!")
            
            # Image message
            image_bot = ImageBot("your-key")
            image_bot.send(file_path="screenshot.png")

        Implementing a custom bot::

            class MyCustomBot(AbstractBot):
                @property
                def _doc_key(self) -> str:
                    return "custom-message-type"
                
                def _verify_arguments(self, *args, **kwargs) -> None:
                    if not args:
                        raise ValueError("Message required")
                
                def _convert_arguments(self, *args, **kwargs) -> ConvertedData:
                    return ({"msgtype": "text", "text": {"content": args[0]}},), kwargs

    See Also:
        - :class:`TextBot`: Plain text messages
        - :class:`MarkdownBot`: Markdown formatted messages
        - :class:`ImageBot`: Image messages
        - :class:`VoiceBot`: Voice messages
        - :class:`FileBot`: File attachments
        - :class:`NewsBot`: News articles
        - :class:`TextCardBot`: Text template cards
        - :class:`NewsCardBot`: News template cards
        - :class:`SmartBot`: Automatic type detection

    Note:
        - Rate limit: 20 messages per minute (enforced by ``@detect_overheat``)
        - Overheat counter is instance-level for thread safety
        - All API errors are handled by ``@handle_request_exception``
    """

    # Default requests headers
    _HEADERS: dict = {"Content-Type": "application/json"}

    def __init__(self, key: str) -> None:
        _Basic.__init__(self, key)
        ABC.__init__(self)
        self._session.headers = self._HEADERS
        self._uploader: _MediaUploader = _MediaUploader(key)
        # Instance-level overheat counter for thread-safety
        self._overheat: int = -1

    @property
    def _api_path(self) -> str:
        """
        The path of the API Endpoint.
        :return: path of the API Endpoint.
        """
        return "cgi-bin/webhook/send"

    @property
    @abstractmethod
    def _doc_key(self) -> str:
        """
        The key of the document description.
        :return: key of the document description
        """

    # pylint:disable=unused-argument
    @handle_request_exception
    @detect_overheat
    @verify_and_convert_arguments
    def send(
        self,
        msg: str = None,
        /,
        articles: List[Dict[str, str]] = None,
        file_path: FilePathLike = None,
        **kwargs,
    ) -> dict:
        """
        Method of sending a message. `Refer`_

        .. _`Refer`: https://developer.work.weixin.qq.com/document/path/91770

        :param msg: Message body.
        :param articles: List of articles. Used for send news.
        :param file_path: File path. Used for send image/voice/file.
        :return: Result dict.
        """
        logger.debug("~~~~ %s ~~~~", self.send.__name__)
        logger.debug("Message: %s", msg)
        logger.debug("Articles: %s", articles)
        logger.debug("File path: %s", file_path)
        logger.debug("Other kwargs: %s", kwargs)
        logger.debug("API endpoint URL: %s", self._api_url)
        response = self._session.post(self._api_url, params={"key": self.key}, json=msg)
        result = response.json()
        logger.debug("~~~~ %s ~~~~", self.send.__name__)
        logger.info("Message has been sent: %s", result)
        return result

    def upload(self, file_path: FilePathLike) -> str:
        """
        Upload temporary media file
        :param file_path: The path of the file to upload.
        :return:
        """
        result = self._uploader.upload(file_path)
        return result

    @abstractmethod
    def _verify_arguments(self, *args, **kwargs) -> None:
        """
        Verify arguments methods. Subclasses must complete specific implementations
        :param args: Positional arguments.
        :param kwargs: Keyword arguments.
        :return: None
        """

    @abstractmethod
    def _convert_arguments(self, *args, **kwargs) -> ConvertedData:
        """
        Prepare data methods, subclasses must complete specific implementations
        :param args: Positional arguments.
        :param kwargs: Other keyword arguments.
        :return: Result dict.
        """
