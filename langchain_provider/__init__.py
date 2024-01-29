# -*- coding: utf-8 -*-

# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License

"""Kite client requests and constants."""

from spyder.plugins.completion.api import CompletionRequestTypes
from spyder.plugins.completion.api import CompletionItemKind
from pydantic import BaseModel, Field, validator


LANGCHAIN_COMPLETION = "Langchain"


class _LangchainParams():
    TEMPLATE_PARAM = """You are a helpful assistant in completing following python code based
                  on the previous sentence.
                  You always complete the code in same line and give 4 suggestions.
                  Example : a=3 b=4 print
                  AI : print(a) print(b) print(a+b)
                  Example : a=3 b=4 c
                  AI : c=a+b c=a-b c=5
                  Please enclose each suggestions in a list with a dict with key suggestions
                  """
    MODEL_NAME_PARAM = "gpt-3.5-turbo"
    OPENAI_API_KEY_TEMP = "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"

    def __getattribute__(self, attr):
        value = object.__getattribute__(self, attr)
        return value