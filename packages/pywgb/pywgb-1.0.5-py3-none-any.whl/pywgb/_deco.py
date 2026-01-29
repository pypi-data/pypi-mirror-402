#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Decorators module for Wecom Group Bot API.

This module provides essential decorators for argument validation, error handling,
overheat detection (rate limiting), and file verification. These decorators are
applied to bot methods to ensure robust and reliable API interactions.

Decorators:
    - :func:`verify_and_convert_arguments`: Validates and converts method arguments
    - :func:`detect_overheat`: Implements rate limiting (20 messages/minute)
    - :func:`handle_request_exception`: Unified exception handling for API requests
    - :func:`verify_file`: Validates file existence before processing

Note:
    The overheat detection implements Wecom's rate limit of 20 messages per minute
    per bot. When the limit is reached, the decorator automatically waits for the
    cooldown period.

:author: Rex Zhou <879582094@qq.com>
:copyright: Copyright © 2025 Rex Zhou. All rights reserved.
"""
from functools import wraps
from logging import getLogger
from pathlib import Path
from time import sleep

from requests import RequestException

logger = getLogger(__name__)


def verify_and_convert_arguments(function):
    """
    Decorator to verify and convert arguments to standard format.

    This decorator wraps bot methods to ensure all arguments are validated
    and converted to the appropriate format before processing. It calls the
    bot's ``_verify_arguments()`` and ``_convert_arguments()`` methods.

    Args:
        function (Callable): The function to be decorated.

    Returns:
        Callable: Wrapped function with argument verification and conversion.

    Raises:
        ValueError: If argument verification or conversion fails.

    Example:
        This decorator is typically used internally::

            @verify_and_convert_arguments
            def send(self, *args, **kwargs):
                # Method implementation
                pass

    See Also:
        :meth:`AbstractBot._verify_arguments`
        :meth:`AbstractBot._convert_arguments`
    """

    # pylint: disable=protected-access
    @wraps(function)
    def wrapper(self, *args, **kwargs) -> dict:
        logger.debug("---- %s ----", verify_and_convert_arguments.__name__)
        logger.debug("Positional arguments: %s", args)
        logger.debug("Other kwargs: %s", kwargs)
        try:
            self._verify_arguments(*args, **kwargs)
        except ValueError as error:
            logger.critical("Verification of arguments failed: %s", error)
            raise error
        try:
            args, kwargs = self._convert_arguments(*args, **kwargs)
        except ValueError as error:
            logger.critical("Convertion of arguments failed: %s", error)
            raise error
        logger.debug("Converted arguments: %s", args)
        logger.debug("Converted other kwargs: %s", kwargs)
        logger.debug("---- %s ----", verify_and_convert_arguments.__name__)
        return function(self, *args, **kwargs)

    return wrapper


def detect_overheat(function):
    """
    Decorator to detect and handle API rate limiting (overheat).

    Wecom Group Bot API has a rate limit of 20 messages per minute per bot.
    This decorator automatically detects when the rate limit is exceeded
    (error code 45009) and implements a cooldown period before retrying.

    The cooldown counter is instance-specific, ensuring thread-safety when
    multiple bot instances are used concurrently.

    Args:
        function (Callable): The function to be decorated.

    Returns:
        Callable: Wrapped function with overheat detection.

    Note:
        - Default cooldown period: 60 seconds
        - Overheat error code: 45009
        - The decorator displays a countdown timer during cooldown

    Example:
        When rate limit is exceeded::

            bot.send("Message 21")  # Triggers overheat
            # Output: Cooling down: 60s ... 59s ... 58s ...
            # Automatically retries after cooldown

    See Also:
        Official rate limit documentation:
        https://developer.work.weixin.qq.com/document/path/99110#消息发送频率限制
    """
    overheat_threshold: int = 60
    overheat_error_code: int = 45009

    # pylint: disable=protected-access
    @wraps(function)
    def wrapper(self, *args, **kwargs) -> dict:
        """
        Detect overheat.
        :param self: Object instance.
        :param args: Positional arguments.
        :param kwargs: Keyword arguments.
        :return: Result dict.
        """
        logger.debug("==== %s ====", detect_overheat.__name__)
        logger.debug("Positional arguments: %s", args)
        logger.debug("Other kwargs: %s", kwargs)
        if kwargs.get("test") == "overheat":
            kwargs.pop("test")
            threshold = 0
            result = {"errcode": overheat_error_code}
        else:
            threshold = overheat_threshold
            if self._overheat >= 0:
                logger.warning("Overheat detected.")
                while self._overheat >= 0:
                    print(f"\rCooling down: {self._overheat:02d}s", end="", flush=True)
                    sleep(1)
                    self._overheat -= 1
                print()
            result = function(self, *args, **kwargs)
        if result.get("errcode") == overheat_error_code:
            self._overheat = threshold
            result = wrapper(self, *args, **kwargs)
        logger.debug("==== %s ====", detect_overheat.__name__)
        return result

    return wrapper


def handle_request_exception(function):
    """
    Decorator to handle API request exceptions uniformly.

    This decorator wraps API request methods to catch and handle common
    exceptions, providing consistent error messages and logging. It handles
    both network-level errors (RequestException) and API-level errors
    (non-zero error codes).

    Args:
        function (Callable): The function to be decorated.

    Returns:
        Callable: Wrapped function with exception handling.

    Raises:
        ConnectionRefusedError: If the API request fails due to network issues.
        IOError: If the API returns a non-zero error code.

    Example:
        Typical usage in bot methods::

            @handle_request_exception
            def _upload_file(self, file_path):
                response = requests.post(url, files=files)
                return response.json()

    Note:
        The decorator checks for ``errcode`` in the response. A value of 0
        indicates success; any other value is treated as an error.
    """

    @wraps(function)
    def wrapper(self, *args, **kwargs):
        """
        Handle request exception.
        :param self: Object instance.
        :param args: Positional arguments.
        :param kwargs: Keyword arguments.
        :return: Result dict.
        """
        logger.debug("#### %s ####", handle_request_exception.__name__)
        logger.debug("Positional arguments: %s", args)
        logger.debug("Other kwargs: %s", kwargs)
        try:
            if (test := kwargs.get("test")) == "request_error":
                raise RequestException
            if test == "api_error":
                result = {"errcode": -1}
            else:
                result = function(self, *args, **kwargs)
            if result.get("errcode") != 0:
                msg = f"Request failed, please refer to the official manual: {self.doc}"
                logger.error(msg)
                logger.error("Error message: %s", result)
                raise IOError(msg)
        except RequestException as error:
            msg = f"Unable to initiate API request correctly: {error}"
            logger.error(msg)
            raise ConnectionRefusedError(msg) from error
        logger.debug("#### %s ####", handle_request_exception.__name__)
        return result

    return wrapper


def verify_file(function):
    """
    Decorator to verify file existence before processing.

    This decorator checks if the specified file path exists before allowing
    the decorated function to proceed. It's used for all file-related
    operations (image, voice, file uploads).

    Args:
        function (Callable): The function to be decorated.

    Returns:
        Callable: Wrapped function with file verification.

    Raises:
        ValueError: If file_path parameter is missing or file doesn't exist.

    Example:
        Usage in bot methods::

            @verify_file
            def _verify_arguments(self, *args, **kwargs):
                file_path = kwargs.get("file_path")
                # File existence is already verified by decorator
                # Proceed with format validation
                ...

    Note:
        The decorator looks for ``file_path`` in kwargs or as the first
        positional argument.
    """

    @wraps(function)
    def wrapper(self, *args, **kwargs):
        logger.debug("$$$$ %s $$$$", verify_file.__name__)
        logger.debug("Positional arguments: %s", args)
        logger.debug("Other kwargs: %s", kwargs)
        file_path = kwargs.get("file_path")
        try:
            file_path = file_path if file_path else args[0]
        except IndexError as error:
            raise ValueError("The file_path parameter is required.") from error
        if not Path(file_path).exists():
            raise ValueError("The file_path parameter not exists.")
        logger.debug("$$$$ %s $$$$", verify_file.__name__)
        return function(self, *args, **kwargs)

    return wrapper
