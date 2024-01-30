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
from qtpy.QtCore import QObject, QThread, Signal, QMutex, Slot
import json
from collections import defaultdict

# Spyder imports
from spyder.config.base import _, running_under_pytest
from spyder.py3compat import TEXT_TYPES
from spyder.plugins.completion.api import (
    CompletionRequestTypes, CompletionItemKind)


# Local imports
from langchain_provider.utils.status import status


logger = logging.getLogger(__name__)


# Lang can return e.g. "int | str", so we make the default hint VALUE.
LANG_DOCUMENT_TYPES = defaultdict(lambda: CompletionItemKind.VALUE, {
    'function': CompletionItemKind.FUNCTION,
    'type': CompletionItemKind.CLASS,
    'module': CompletionItemKind.MODULE,
    'descriptor': CompletionItemKind.PROPERTY,
    'union': CompletionItemKind.VALUE,
    'unknown': CompletionItemKind.TEXT,
    'keyword': CompletionItemKind.KEYWORD,
    'call': CompletionItemKind.FUNCTION,
})
LANG_COMPLETION = 'Langchain'
LANG_ICON_SCALE = (416.14 / 526.8)

class LangchainClient(QObject):
    sig_response_ready = Signal(int, dict)
    sig_client_started = Signal()
    sig_client_not_responding = Signal()
    sig_perform_request = Signal(dict)
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
        self.sig_perform_request.connect(self.handle_msg)
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
        prevResponse = self.chain.invoke(params)['text'].translate(mapping_table)
        response=json.loads("{"+prevResponse+"}")
        return response

    def send(self, params):
        response = None
        response = self.run_chain(params=params)
        return response

    @Slot(dict)
    def handle_msg(self, message):
        """Handle one message"""
        msg_type, _id, file, msg = [
            message[k] for k in ('type', 'id', 'file', 'msg')]
        logger.debug(u'Perform request {0} with id {1}'.format(msg_type, _id))
        if msg_type == CompletionRequestTypes.DOCUMENT_DID_OPEN:
            self.opened_files[msg['file']] = msg['text']
        elif msg_type == CompletionRequestTypes.DOCUMENT_DID_CHANGE:
            self.opened_files[msg['file']] = msg['text']            
        elif msg_type == CompletionRequestTypes.DOCUMENT_COMPLETION:
            response=self.send(self.opened_files[msg['file']])
            logger.debug(response)
            if response is None:
                return {'params': []}
            spyder_completions = []
            completions = response['suggestions']
            if completions is not None:
                for i, completion in enumerate(completions):
                    entry = {
                        'kind': LANG_DOCUMENT_TYPES.get(CompletionItemKind.TEXT),
                        'label': completion,
                        'filterText': '',
                        # Use the returned ordering
                        'sortText': (i, 0),
                        'documentation': completion,
                        'provider': LANG_COMPLETION,
                        'icon': ('kite', LANG_ICON_SCALE)
                    }
                    spyder_completions.append(entry)
            self.sig_response_ready.emit(_id, {'params': spyder_completions})