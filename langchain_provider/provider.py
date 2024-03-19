# -*- coding: utf-8 -*-

# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License

"""Langchain completion HTTP client."""

# Standard library imports
import logging
import functools
import os
import os.path as osp

# Qt imports
from qtpy.QtCore import Slot
from qtpy.QtWidgets import QMessageBox

# Local imports
from langchain_provider.client import LangchainClient
from langchain_provider.widgets import LangchainStatusWidget

# Spyder imports
from spyder.api.config.decorators import on_conf_change
from spyder.config.base import _, running_under_pytest
from spyder.plugins.completion.api import SpyderCompletionProvider


logger = logging.getLogger(__name__)


class LangchainProvider(SpyderCompletionProvider):
    COMPLETION_PROVIDER_NAME = "langchain"
    DEFAULT_ORDER = 1
    SLOW = True
    CONF_VERSION = "1.0.0"
    SUGGESTIONS = "4"
    LANGUAGE = "Python"
    TEMPLATE_PARAM = """You are a helpful assistant in completing following {0} code based
                  on the previous sentence.
                  You always complete the code in same line and give {1} suggestions.
                  Example : a=3 b=4 print
                  AI : "suggestions": ["print(a)", "print(b)", "print(a+b)"]
                  Example : a=3 b=4 c
                  AI : "suggestions": ["c=a+b", "c=a-b", "c=5"]
                  Format the output as JSON with the following key:
                      suggestions
                  """.format(
        LANGUAGE, SUGGESTIONS
    )
    MODEL_NAME_PARAM = "gpt-3.5-turbo"

    def __init__(self, parent, config):
        super().__init__(parent, config)
        self.available_languages = []
        self.client = LangchainClient(
            None, model_name=self.MODEL_NAME_PARAM, template=self.TEMPLATE_PARAM
        )

        # Signals
        self.client.sig_client_started.connect(
            lambda: self.sig_provider_ready.emit(self.COMPLETION_PROVIDER_NAME)
        )
        self.client.sig_client_error.connect(self.set_status_error)
        self.client.sig_status_response_ready[str].connect(self.set_status)
        self.client.sig_status_response_ready[dict].connect(self.set_status)
        self.client.sig_response_ready.connect(
            lambda _id, resp: self.sig_response_ready.emit(
                self.COMPLETION_PROVIDER_NAME, _id, resp
            )
        )

        # Status bar widget
        self.STATUS_BAR_CLASSES = [self.create_statusbar]
        self.started = False
        # Config
        self.update_langchain_configuration(self.config)

    # ------------------ SpyderCompletionProvider methods ---------------------
    def get_name(self):
        return "LangChain"

    def send_request(self, language, req_type, req, req_id):
        request = {"type": req_type, "file": req["file"], "id": req_id, "msg": req}
        self.client.sig_perform_request.emit(request)

    def start_completion_services_for_language(self, language):
        return self.started

    def start(self):
        if not self.started:
            self.client.start()
            self.started = True

    def shutdown(self):
        if self.started:
            self.client.stop()
            self.started = False

    @Slot(str)
    @Slot(dict)
    def set_status(self, status):
        """Show Langchain status for the current file."""
        self.sig_call_statusbar.emit(
            LangchainStatusWidget.ID, "set_value", (status,), {}
        )

    def set_status_error(self, error_message):
        """Show Langchain status for the current file."""
        self.sig_call_statusbar.emit(
            LangchainStatusWidget.ID, "set_value", (error_message,), {}
        )

    def file_opened_closed_or_updated(self, filename, _language):
        """Request status for the given file."""
        self.client.sig_perform_status_request.emit(filename)

    @on_conf_change(section="completions", option=("enabled_providers", "langchain"))
    def on_langchain_enable_changed(self, value):
        self.sig_call_statusbar.emit(LangchainStatusWidget.ID, "set_value", (None,), {})

    @on_conf_change(section="completions", option="enable_code_snippets")
    def on_code_snippets_changed(self, value):
        if running_under_pytest():
            if not os.environ.get("SPY_TEST_USE_INTROSPECTION"):
                return

        self.client.enable_code_snippets = self.get_conf(
            "enable_code_snippets", section="completions"
        )

    @on_conf_change
    def update_langchain_configuration(self, config):
        if running_under_pytest():
            if not os.environ.get("SPY_TEST_USE_INTROSPECTION"):
                return

    def create_statusbar(self, parent):
        return LangchainStatusWidget(parent, self)
