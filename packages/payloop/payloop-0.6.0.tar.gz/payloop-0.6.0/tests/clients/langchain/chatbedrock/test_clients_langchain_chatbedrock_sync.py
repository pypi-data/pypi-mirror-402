import pytest
from langchain_aws import ChatBedrock
from langchain_core.tools import tool

from payloop import Payloop, PayloopRequestInterceptedError


@tool
def multiply(a: int, b: int) -> int:
    """Multiply a and b."""
    return a * b


@pytest.mark.integration
def test_langchain_chatbedrock_sync():
    llm = ChatBedrock(
        model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
        region_name="us-east-1",
    )

    payloop = Payloop().langchain.register(chatbedrock=llm)

    # Make sure registering the same client again does not cause an issue.
    payloop.langchain.register(chatbedrock=llm)

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
                ("user", "What is the capital of France?"),
            ]
        )
