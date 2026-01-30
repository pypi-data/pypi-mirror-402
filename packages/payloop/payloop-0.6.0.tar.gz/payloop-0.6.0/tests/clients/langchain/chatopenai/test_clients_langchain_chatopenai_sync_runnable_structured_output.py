import os
from typing import List

import pytest
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from payloop import Payloop, PayloopRequestInterceptedError


class Output(BaseModel):
    allergens: List[str]


class CapitalOutput(BaseModel):
    capital: str


@pytest.mark.integration
def test_langchain_chatopenai_sync_runnable_structured_output():
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    prompt = ChatPromptTemplate(
        [
            ("system", "You are an expert in identifying allergens in food products."),
            ("user", "What are the allergens in the following product: {product_name}"),
        ]
    )

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

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

    chain = prompt | llm.with_structured_output(Output)

    print(chain.invoke({"product_name": "Lamen"}))

    payloop.sentinel.raise_if_irrelevant(True)

    prompt = ChatPromptTemplate(
        [
            ("system", "Only answer questions related to coding."),
            ("user", "What is the capital of {country_name}?"),
        ]
    )

    chain = prompt | llm.with_structured_output(CapitalOutput)

    with pytest.raises(PayloopRequestInterceptedError):
        chain.invoke({"country_name": "France"})
