# -*- coding: utf-8 -*-

# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License

"""Kite completions HTTP client."""

# Standard library imports
import logging
from urllib.parse import quote

# Third party imports
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts.chat import (
            ChatPromptTemplate,
            SystemMessagePromptTemplate,
            HumanMessagePromptTemplate,
        )
from qtpy.QtCore import QObject, QThread, Signal, QMutex
import json

# Spyder imports
from spyder.config.base import _, running_under_pytest
from spyder.py3compat import TEXT_TYPES


# Local imports
from langchain_provider.decorators import class_register
from langchain_provider.providers import LangMethodProviderMixIn
from langchain_provider.utils.status import status


logger = logging.getLogger(__name__)


@class_register
class LangchainClient(QObject, LangMethodProviderMixIn):
    sig_response_ready = Signal(int, dict)
    sig_client_started = Signal()
    sig_client_not_responding = Signal()
    sig_perform_request = Signal(int, str, object)
    sig_perform_status_request = Signal(str)
    sig_status_response_ready = Signal((str,), (dict,))
    sig_onboarding_response_ready = Signal(str)

    def __init__(self, parent, template, model_name, apiKey,enable_code_snippets=True,language='python'):
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
        self.sig_perform_request.connect(self.perform_request)
        self.sig_perform_status_request.connect(self.get_status)

        self.template=template
        self.model_name=model_name
        self.apiKey=apiKey
        self.chain=None

    def start(self):
        if not self.thread_started:
            self.thread.start()
        logger.debug('Starting LangChain session...')
        system_message_prompt = SystemMessagePromptTemplate.from_template(self.template)
        code_template = "{text}"
        code_message_prompt = HumanMessagePromptTemplate.from_template(
            code_template,
            )        
        llm=ChatOpenAI(temperature=0,model_name=self.model_name,openai_api_key=self.apiKey)
        chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, code_message_prompt])
        chain = LLMChain(
            llm=llm,
            prompt=chat_prompt,
            )
        self.chain=chain
        self.sig_client_started.emit()

    def started(self):
        self.thread_started = True

    def stop(self):
        if self.thread_started:
            logger.debug('Closing LangChain session...')
            self.thread.quit()
            self.thread.wait()
            self.thread_started = False

    def get_status(self, filename):
        """Get langchain status for a given filename."""
        kite_status = None
        if not filename or kite_status is None:
            kite_status = status()
            self.sig_status_response_ready[str].emit(kite_status)
        elif isinstance(kite_status, TEXT_TYPES):
            status_str = status(extra_status=' with errors')
            long_str = _("<code>{error}</code><br><br>"
                         "Note: If you are using a VPN, "
                         "please don't route requests to "
                         "localhost/127.0.0.1 with it").format(
                             error=kite_status)
            kite_status_dict = {
                'status': status_str,
                'short': status_str,
                'long': long_str}
            self.sig_status_response_ready[dict].emit(kite_status_dict)
        else:
            self.sig_status_response_ready[dict].emit(kite_status)

    def run_chain(self, params=None):
        response = None
        mapping_table = str.maketrans({'"': "'", "'": '"'})
        print("========================Inicioooooooooooooooooo======================")
        print(params['text'])
        print("========================Finaallllllllllllllllll======================")
        prevResponse=self.chain.invoke(params['text'])['text']
        print("========================InicioooResponse======================")
        print(prevResponse)
        print("========================FinaalllResponse======================")
        response=json.loads(prevResponse.translate(mapping_table))
        return response

    def send(self, method, params, url_params):
        response = None
        response = self.run_chain(params=params)
        return response

    def perform_request(self, req_id, method, params):
        response = None
        if method in self.sender_registry:
            logger.debug('Perform request {0} with id {1}'.format(
                method, req_id))
            handler_name = self.sender_registry[method]
            handler = getattr(self, handler_name)
            response = handler(params)
            if method in self.handler_registry:
                converter_name = self.handler_registry[method]
                converter = getattr(self, converter_name)
                if response is not None:
                    response = converter(response)
        if not isinstance(response, (dict, type(None))):
            if not running_under_pytest():
                print("error")
        else:
            self.sig_response_ready.emit(req_id, response or {})
