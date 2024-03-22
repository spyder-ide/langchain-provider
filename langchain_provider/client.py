# -*- coding: utf-8 -*-

# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License

"""Langchain completions HTTP client."""

# Standard library imports
import logging
import os

# Third party imports
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from qtpy.QtCore import QObject, QThread, Signal, QMutex, Slot
import json
from collections import defaultdict

# Spyder imports
from spyder.config.base import _, running_under_pytest
from spyder.py3compat import TEXT_TYPES
from spyder.plugins.completion.api import CompletionRequestTypes, CompletionItemKind


logger = logging.getLogger(__name__)


LANG_COMPLETION = "Langchain"
LANG_ICON_SCALE = 1


class LangchainClient(QObject):
    sig_response_ready = Signal(int, dict)
    sig_client_started = Signal()
    sig_client_error = Signal(str)
    sig_perform_request = Signal(dict)
    sig_perform_status_request = Signal(str)
    sig_status_response_ready = Signal((str,), (dict,))
    sig_onboarding_response_ready = Signal(str)

    def __init__(
        self, parent, template, model_name, enable_code_snippets=True, language="python"
    ):
        QObject.__init__(self, parent)
        self.requests = {}
        self.language = language
        self.mutex = QMutex()
        self.opened_files = {}
        self.opened_files_status = {}
        self.thread_started = False
        self.enable_code_snippets = enable_code_snippets
        self.thread = QThread(None)
        self.moveToThread(self.thread)
        self.thread.started.connect(self.started)
        self.sig_perform_request.connect(self.handle_msg)
        self.sig_perform_status_request.connect(self.get_status)

        self.template = template
        self.model_name = model_name
        self.chain = None

    def start(self):
        if not self.thread_started:
            self.thread.start()
        logger.debug("Starting LangChain session...")
        system_message_prompt = SystemMessagePromptTemplate.from_template(self.template)
        code_template = "{text}"
        code_message_prompt = HumanMessagePromptTemplate.from_template(
            code_template,
        )
        try:
            llm = ChatOpenAI(
                temperature=0,
                model_name=self.model_name,
            )
            chat_prompt = ChatPromptTemplate.from_messages(
                [system_message_prompt, code_message_prompt]
            )
            chain = LLMChain(
                llm=llm,
                prompt=chat_prompt,
            )
            self.chain = chain
            self.sig_client_started.emit()
        except ValueError as e:
            logger.debug(e)
            self.sig_client_error.emit("Missing OpenAI API key")
        except Exception as e:
            logger.debug(e)
            self.sig_client_error.emit("Unexpected error")

    def started(self):
        self.thread_started = True

    def stop(self):
        if self.thread_started:
            logger.debug("Closing LangChain session...")
            self.thread.quit()
            self.thread.wait()
            self.thread_started = False

    def get_status(self, filename):
        """Get langchain status for a given filename."""
        langchain_status = None
        if not filename or langchain_status is None:
            langchain_status = self.model_name
            self.sig_status_response_ready[str].emit(langchain_status)

    def run_chain(self, params=None):
        response = None
        try:
            prevResponse = self.chain.invoke(params)["text"]
            if prevResponse[0] == '"':
                response = json.loads("{" + prevResponse + "}")
            else:
                response = json.loads(prevResponse)
            return response
        except Exception:
            self.sig_client_error.emit("No suggestions available")
            return {"suggestions": []}

    def send(self, params):
        response = None
        response = self.run_chain(params=params)
        return response

    @Slot(dict)
    def handle_msg(self, message):
        """Handle one message"""
        msg_type, _id, file, msg = [message[k] for k in ("type", "id", "file", "msg")]
        logger.debug("Perform request {0} with id {1}".format(msg_type, _id))
        if msg_type == CompletionRequestTypes.DOCUMENT_DID_OPEN:
            self.opened_files[msg["file"]] = msg["text"]
        elif msg_type == CompletionRequestTypes.DOCUMENT_DID_CHANGE:
            self.opened_files[msg["file"]] = msg["text"]
        elif msg_type == CompletionRequestTypes.DOCUMENT_COMPLETION:
            response = self.send(self.opened_files[msg["file"]])
            logger.debug(response)
            if response is None:
                return {"params": []}
            spyder_completions = []
            completions = response["suggestions"]
            if completions is not None:
                for i, completion in enumerate(completions):
                    entry = {
                        "kind": CompletionItemKind.TEXT,
                        "label": completion,
                        "insertText": completion,
                        "filterText": "",
                        # Use the returned ordering
                        "sortText": (0, i),
                        "documentation": completion,
                        "provider": LANG_COMPLETION,
                        "icon": ("langchain", LANG_ICON_SCALE),
                    }
                    spyder_completions.append(entry)
            self.sig_response_ready.emit(_id, {"params": spyder_completions})
