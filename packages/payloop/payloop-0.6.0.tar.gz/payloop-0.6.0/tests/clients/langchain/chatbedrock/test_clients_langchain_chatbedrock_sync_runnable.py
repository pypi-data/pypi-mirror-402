from typing import TypedDict

import pytest
from langchain_aws import ChatBedrock
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from payloop import Payloop, PayloopRequestInterceptedError


class MyInput(TypedDict):
    question: str


def build_chain(
    system_prompt: str = "You are a helpful assistant.",
    raise_if_irrelevant: bool = False,
):
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{question}"),
        ]
    )

    llm = ChatBedrock(
        model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
        region_name="us-east-1",
    )

    payloop = Payloop().langchain.register(chatbedrock=llm)

    # Make sure registering the same client again does not cause an issue.
    payloop.langchain.register(chatbedrock=llm)

    payloop.sentinel.raise_if_irrelevant(raise_if_irrelevant)

    # Test setting attribution.
    payloop.attribution(
        parent_id=123,
        parent_name="Abc",
        parent_uuid="95473da0-5d7a-435d-babf-d64c5dabe971",
        subsidiary_id=456,
        subsidiary_name="Def",
        subsidiary_uuid="b789eaf4-c925-4a79-85b1-34d270342353",
    )

    chain = prompt | llm | StrOutputParser()

    return chain


@pytest.mark.integration
def test_langchain_chatbedrock_sync_runnable():
    chain = build_chain()

    input_data = {"question": "What is the capital of France?"}

    print("Streaming response:\n")
    for chunk in chain.stream(input_data):
        print(chunk, end="", flush=True)

    chain = build_chain("Only answer questions related to coding.", True)

    input_data = {"question": "What is the capital of France?"}

    with pytest.raises(PayloopRequestInterceptedError):
        for chunk in chain.stream(input_data):
            pass
