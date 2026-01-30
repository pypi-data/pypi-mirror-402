import os

import pytest
from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from payloop import Payloop, PayloopRequestInterceptedError


@pytest.mark.integration
@pytest.mark.asyncio
async def test_langchain_chatopenai_async_streaming():
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    llm = ChatOpenAI(model="gpt-4.1", streaming=True)
    human_message = HumanMessage(content="Hello world!")

    payloop = Payloop().langchain.register(chatopenai=llm)

    # Make sure registering the same client again does not cause an issue.
    payloop.langchain.register(chatopenai=llm)

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
