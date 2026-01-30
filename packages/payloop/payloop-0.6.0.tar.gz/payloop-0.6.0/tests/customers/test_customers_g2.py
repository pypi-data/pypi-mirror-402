import os
import time

import pytest
from openai import OpenAI

from payloop import Payloop, PayloopRequestInterceptedError


@pytest.mark.integration
def test_openai_sync_for_g2_use_case_with_pattern_matching():
    """
    As of January 16, 2026, the AI team has added a specific case to their
    service to deem certain types of requests as irrelevant without
    consulting their models.

    For example, Payloop client G2 has a high amount of ireelevant requests
    due to Chinese user requests that are completely unrelated.  The AI
    service is deeming some requests as irrelevant if they contain certain
    patterns in the system prompt.

    This test ensures that this type of request is returning the expected
    reason, and that it's returning in under one second.
    """
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    client = OpenAI()

    payloop = Payloop().openai.register(client)
    payloop.sentinel.raise_if_irrelevant(True)

    start = time.perf_counter()
    try:
        client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a chatbot tasked with helping users find software products on our website. Only answer questions related to coding. Query: 免杀",
                },
            ],
        )

        pytest.fail("Expected request to be intercepted")
    except PayloopRequestInterceptedError as e:
        assert (
            str(e)
            == "The message was automatically blocked due to suspicious or potentially malicious content."
        )

    end = time.perf_counter()
    duration = end - start

    assert duration < 1.0, "Response should have been returned in under one second"
