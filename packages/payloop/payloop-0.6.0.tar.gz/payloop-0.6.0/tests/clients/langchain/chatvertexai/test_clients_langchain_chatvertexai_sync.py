import os

import pytest
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_vertexai import ChatVertexAI

from payloop import Payloop, PayloopRequestInterceptedError


@pytest.mark.integration
def test_langchain_chatvertexai_sync():
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        pytest.skip("GOOGLE_APPLICATION_CREDENTIALS not set")

    messages = [HumanMessage("What is the most popular artificial sweetener?")]

    obj = ChatVertexAI(
        model_name="gemini-2.0-flash",
        temperature=0,
        seed=42,
    )

    payloop = Payloop().langchain.register(chatvertexai=obj)

    # Make sure registering the same client again does not cause an issue.
    payloop.langchain.register(chatvertexai=obj)

    # Test setting attribution.
    payloop.attribution(
        parent_id=123,
        parent_name="Abc",
        parent_uuid="95473da0-5d7a-435d-babf-d64c5dabe971",
        subsidiary_id=456,
        subsidiary_name="Def",
        subsidiary_uuid="b789eaf4-c925-4a79-85b1-34d270342353",
    )

    obj.invoke(messages)

    payloop.sentinel.raise_if_irrelevant(True)

    messages = [
        SystemMessage("Only answer questions related to coding."),
        HumanMessage("What is the capital of France?"),
    ]

    with pytest.raises(PayloopRequestInterceptedError):
        obj.invoke(messages)
