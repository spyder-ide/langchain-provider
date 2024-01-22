# -*- coding: utf-8 -*-

# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License

"""Lang document requests handlers and senders."""

from collections import defaultdict
import logging
import hashlib

import os
import os.path as osp

from qtpy.QtCore import QMutexLocker
from completion_provider.decorators import (
    send_request, handles)
from spyder.plugins.completion.api import (
    CompletionRequestTypes, CompletionItemKind)


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

logger = logging.getLogger(__name__)


class DocumentProvider:

    @send_request(method=CompletionRequestTypes.DOCUMENT_DID_OPEN)
    def document_did_open(self, params):
        request = {
            'source': 'spyder',
            'filename': osp.realpath(params['file']),
            'text': params['text'],
            'action': 'focus',
            'selections': [{
                'start': params['selection_start'],
                'end': params['selection_end'],
                'encoding': 'utf-16',
            }],
        }

        with QMutexLocker(self.mutex):
            self.get_status(params['file'])
            self.opened_files[params['file']] = params['text']
        return request

    @send_request(method=CompletionRequestTypes.DOCUMENT_DID_CHANGE)
    def document_did_change(self, params):
        request = {
            'source': 'spyder',
            'filename': osp.realpath(params['file']),
            'text': params['text'],
            'action': 'edit',
            'selections': [{
                'start': params['selection_start'],
                'end': params['selection_end'],
                'encoding': 'utf-16',
            }],
        }
        with QMutexLocker(self.mutex):
            self.opened_files[params['file']] = params['text']
        return request

    @send_request(method=CompletionRequestTypes.DOCUMENT_CURSOR_EVENT)
    def document_cursor_event(self, params):
        request = {
            'source': 'spyder',
            'filename': osp.realpath(params['file']),
            'text': params['text'],
            'action': 'edit',
            'selections': [{
                'start': params['selection_start'],
                'end': params['selection_end'],
                'encoding': 'utf-16',
            }],
        }
        return request

    @send_request(method=CompletionRequestTypes.DOCUMENT_COMPLETION)
    def request_document_completions(self, params):
        text = self.opened_files[params['file']]
        request = {
            'filename': osp.realpath(params['file']),
            'editor': 'spyder',
            'no_snippets': not self.enable_code_snippets,
            'text': text,
            'position': {
                'begin': params['selection_start'],
                'end': params['selection_end'],
            },
            'offset_encoding': 'utf-16',
        }
        return request

    @handles(CompletionRequestTypes.DOCUMENT_COMPLETION)
    def convert_completion_request(self, response):
        # The response schema is tested via mocking in
        # spyder/plugins/editor/widgets/tests/test_introspection.py

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

        return {'params': spyder_completions}

    @send_request(method=CompletionRequestTypes.DOCUMENT_HOVER)
    def request_hover(self, params):
        text = self.opened_files.get(params['file'], "")
        md5 = hashlib.md5(text.encode('utf-8')).hexdigest()
        path = params['file']
        path = path.replace(osp.sep, ':')
        logger.debug(path)
        if os.name == 'nt':
            path = path.replace('::', ':')
            path = ':windows:' + path
        request = {
            'filename': path,
            'hash': md5,
            'cursor_runes': params['offset'],
            'offset_encoding': 'utf-16',
        }
        return None, request

    @handles(CompletionRequestTypes.DOCUMENT_HOVER)
    def process_hover(self, response):
        text = None
        logger.debug(response)
        if response is not None:
            report = response['report']
            text = report['description_text']
            if len(text) == 0:
                text = None
        else:
            text = None

        return {'params': text}

    @send_request(method=CompletionRequestTypes.DOCUMENT_SIGNATURE)
    def request_signature(self, request):
        text = self.opened_files.get(request['file'], "")
        response = {
            'editor': 'spyder',
            'filename': request['file'],
            'text': text,
            'cursor_runes': request['offset'],
            'offset_encoding': 'utf-16',
        }
        return response

    @handles(CompletionRequestTypes.DOCUMENT_SIGNATURE)
    def process_signature(self, response):
        params = None
        if response is not None:
            calls = response['calls']
            if len(calls) > 0:
                call = calls[0]
                callee = call['callee']
                documentation = callee['synopsis']
                call_label = callee['repr']
                signatures = call['signatures']
                arg_idx = call['arg_index']

                parameters = []
                names = []

                logger.debug(signatures)
                if len(signatures) > 0:
                    signature = signatures[0]
                    logger.debug(signature)
                    if signature['args'] is not None:
                        for arg in signature['args']:
                            parameters.append({
                                'label': arg['name'],
                                'documentation': ''
                            })
                            names.append(arg['name'])

                    func_args = ', '.join(names)
                    call_label = '{0}({1})'.format(call_label, func_args)

                base_signature = {
                    'label': call_label,
                    'documentation': documentation,
                    'parameters': parameters
                }
                params = {
                    'signatures': base_signature,
                    'activeSignature': 0,
                    'activeParameter': arg_idx,
                    'provider': LANG_COMPLETION
                }
        return {'params': params}
