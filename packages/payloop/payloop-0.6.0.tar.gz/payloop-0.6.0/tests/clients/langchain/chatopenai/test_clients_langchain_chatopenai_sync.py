import os

import pytest
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from payloop import Payloop, PayloopRequestInterceptedError


@tool
def multiply(a: int, b: int) -> int:
    """Multiply a and b."""
    return a * b


@pytest.mark.integration
def test_langchain_chatopenai_sync():
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    llm = ChatOpenAI(model="gpt-4o-mini")

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

    llm_with_tools = llm.bind_tools([multiply])
    llm_with_tools.invoke("What is 10 * 10?")

    payloop.sentinel.raise_if_irrelevant(True)

    with pytest.raises(PayloopRequestInterceptedError):
        llm_with_tools.invoke(
            [
                ("system", "Only answer questions related to coding."),
                ("user", "What is the capital of France?"),
            ]
        )
