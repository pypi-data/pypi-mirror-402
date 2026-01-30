import os

import pytest
from openai import AsyncOpenAI

from payloop import Payloop, PayloopRequestInterceptedError


@pytest.mark.integration
@pytest.mark.asyncio
async def test_openai_async():
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    client = AsyncOpenAI()

    payloop = Payloop().openai.register(client)

    # Make sure registering the same client again does not cause an issue.
    payloop.openai.register(client)

    # Test setting attribution.
    payloop.attribution(
        parent_id=123,
        parent_name="Abc",
        parent_uuid="95473da0-5d7a-435d-babf-d64c5dabe971",
        subsidiary_id=456,
        subsidiary_name="Def",
        subsidiary_uuid="b789eaf4-c925-4a79-85b1-34d270342353",
    )

    await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "how are you today?"}],
    )

    payloop.sentinel.raise_if_irrelevant(True)

    with pytest.raises(PayloopRequestInterceptedError):
        await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Only answer questions related to coding.",
                },
                {"role": "user", "content": "What is the capital of France?"},
            ],
        )
