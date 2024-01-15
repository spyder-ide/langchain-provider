# -*- coding: utf-8 -*-

# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License

"""Kite client requests and constants."""

from spyder.plugins.completion.api import CompletionRequestTypes
from spyder.plugins.completion.api import CompletionItemKind
from pydantic import BaseModel, Field, validator


LANGCHAIN_COMPLETION = "Langchain"

class LangchainResponse(BaseModel):
    kind: str = CompletionItemKind.TEXT
    insertText: str = Field(description="answer to resolve the completion")
    label: str = Field(description="answer to resolve the completion")
    sortText: str = Field(description="answer to resolve the completion")
    insertText: str = Field(description="answer to resolve the completion")
    filterText: str = Field(description="answer to resolve the completion")
    provider: str = LANGCHAIN_COMPLETION


class _LangchainParams():
    TEMPLATE_PARAM = """You are a helpful assistant in completing following code based
                  on the previous sentence.
                  You always complete the code in same line and give 5 suggestions.
                  Example : a=3 b=4 print
                  AI : Suggest ""1. print (a) 2. print(b) 3. print(a+b)""
                  Example : a=3 b=4 c
                  AI : Suggest ""1. c= a+b 2. c=a-b 3. c=a*b""
                  """
    MODEL_NAME_PARAM = "gpt-3.5-turbo"
    OPENAI_API_KEY_TEMP = "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"

    def __getattribute__(self, attr):
        value = object.__getattribute__(self, attr)
        return value
    

LANGCHAIN_PARAMS = _LangchainParams(
    'LangchainParams', (), {'__doc__': 'Parameters required for lang chain'})