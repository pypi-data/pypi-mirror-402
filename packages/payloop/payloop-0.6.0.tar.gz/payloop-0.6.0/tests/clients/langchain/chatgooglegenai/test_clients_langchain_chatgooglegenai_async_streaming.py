import os

import pytest
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from payloop import Payloop, PayloopRequestInterceptedError


@pytest.mark.integration
@pytest.mark.asyncio
async def test_langchain_chatgooglegenai_async_streaming():
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        pytest.skip("GOOGLE_APPLICATION_CREDENTIALS not set")

    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
    human_message = HumanMessage(content="Hello world!")

    payloop = Payloop().langchain.register(chatgooglegenai=llm)

    # Make sure registering the same client again does not cause an issue.
    payloop.langchain.register(chatgooglegenai=llm)

    # Test setting attribution.
    payloop.attribution(
        parent_id=123,
        parent_name="Abc",
        parent_uuid="95473da0-5d7a-435d-babf-d64c5dabe971",
        subsidiary_id=456,
        subsidiary_name="Def",
        subsidiary_uuid="b789eaf4-c925-4a79-85b1-34d270342353",
    )

    generator = llm.astream([human_message])
    async for chunk in generator:
        print(chunk)

    system_message = SystemMessage(content="Only answer questions about coding.")
    human_message = HumanMessage(content="What is the capital of France?")

    payloop.sentinel.raise_if_irrelevant(True)

    with pytest.raises(PayloopRequestInterceptedError):
        generator = llm.astream([system_message, human_message])
        async for _ in generator:
            pass
