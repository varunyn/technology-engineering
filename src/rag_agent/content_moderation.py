"""
File name: content_moderation.py
Author: Luigi Saetta
Date last modified: 2025-04-02
Python Version: 3.11

Description:
    This module enable to add content moderation to the user request

Usage:
    Import this module into other scripts to use its functions.
    Example:
        from content_moderation import ContentModerator

License:
    This code is released under the MIT License.

Notes:
    This is a part of a demo showing how to implement an advanced
    RAG solution as a LangGraph agent.

Warnings:
    This module is in development, may change in future versions.
"""

from langchain_core.runnables import Runnable

# integration with APM
from py_zipkin.zipkin import zipkin_span

from .agent_state import State
from .utils.utils import get_console_logger
import config as app_config

logger = get_console_logger()


class ContentModerator(Runnable):
    """
    Takes the user request and applies some rules
    from additional content moderation
    to avoid request not permitted
    """

    def __init__(self):
        """
        Init
        """

    @zipkin_span(service_name=app_config.AGENT_NAME, span_name="content_moderation")
    def invoke(self, input: State, config=None, **kwargs):
        """
        Check if the user requst is allowed
        """
        # Rename parameter to avoid shadowing the config module
        run_config = config
        user_request = input["user_request"]
        error = None

        if app_config.DEBUG:
            logger.debug("ContentModerator: user_request=%s", user_request)

        # for now, do nothing
        return {"error": error}
