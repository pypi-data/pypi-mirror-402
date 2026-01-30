import os

import anthropic
import pytest

from payloop import Payloop, PayloopRequestInterceptedError


@pytest.mark.integration
@pytest.mark.asyncio
async def test_anthropic_async():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")

    client = anthropic.AsyncAnthropic()

    payloop = Payloop().anthropic.register(client)

    # Make sure registering the same client again does not cause an issue.
    payloop.anthropic.register(client)

    # Test setting attribution.
    payloop.attribution(
        parent_id=123,
        parent_name="Abc",
        subsidiary_id=456,
        subsidiary_name="Def",
    )

    print(
        await client.beta.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": "Hello, Claude"}],
        )
    )

    payloop.sentinel.raise_if_irrelevant(True)

    with pytest.raises(PayloopRequestInterceptedError):
        await client.beta.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": "What is the capital of France?"},
            ],
            system="Only answer questions related to coding.",
        )
