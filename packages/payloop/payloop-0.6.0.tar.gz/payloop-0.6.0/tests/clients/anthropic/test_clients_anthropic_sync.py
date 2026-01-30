import os

import anthropic
import pytest

from payloop import Payloop, PayloopRequestInterceptedError


@pytest.mark.integration
def test_anthropic_sync():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")

    client = anthropic.Anthropic()

    payloop = Payloop().anthropic.register(client)

    # Make sure registering the same client again does not cause an issue.
    payloop.anthropic.register(client)

    # Test setting attribution.
    payloop.attribution(
        parent_id=123,
        parent_name="Abc",
        parent_uuid="95473da0-5d7a-435d-babf-d64c5dabe971",
        subsidiary_id=456,
        subsidiary_name="Def",
        subsidiary_uuid="b789eaf4-c925-4a79-85b1-34d270342353",
    )

    client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Hello, Claude"}],
    )

    payloop.sentinel.raise_if_irrelevant(True)

    with pytest.raises(PayloopRequestInterceptedError):
        client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": "What is the capital of France?"},
            ],
            system="Only answer questions related to coding.",
        )
