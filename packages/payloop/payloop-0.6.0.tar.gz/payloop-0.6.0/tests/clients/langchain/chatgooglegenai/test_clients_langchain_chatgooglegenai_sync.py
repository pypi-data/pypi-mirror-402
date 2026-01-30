import os

import pytest
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

from payloop import Payloop, PayloopRequestInterceptedError


@tool
def multiply(a: int, b: int) -> int:
    """Multiply a and b."""
    return a * b


@pytest.mark.integration
def test_langchain_chatgooglegenai_sync():
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        pytest.skip("GOOGLE_APPLICATION_CREDENTIALS not set")

    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

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

    llm_with_tools = llm.bind_tools([multiply])
    print(llm_with_tools.invoke("What is 10 * 10?"))

    payloop.sentinel.raise_if_irrelevant(True)

    with pytest.raises(PayloopRequestInterceptedError):
        llm.invoke(
            [
                ("system", "Only answer questions related to coding."),
                ("human", "What is the capital of France?"),
            ]
        )
