import os

import pytest
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings

from payloop import Payloop, PayloopRequestInterceptedError


@pytest.mark.integration
@pytest.mark.asyncio
async def test_pydantic_ai_openai_async_streaming():
    if not os.environ.get("OPENROUTER_API_KEY"):
        pytest.skip("OPENROUTER_API_KEY not set")

    openrouter_provider = OpenAIProvider(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ.get("OPENROUTER_API_KEY"),
    )

    o4_mini = OpenAIModel("o4-mini", provider=openrouter_provider)

    payloop = Payloop().pydantic_ai.register(openrouter_provider.client)

    agent = Agent(
        o4_mini,
        system_prompt="You're a comedian. Always reply with a joke.",
        model_settings=ModelSettings(max_tokens=1024),
    )

    print("Running agent...")
    result = await agent.run("Hello!")
    print(result.output)

    # Run async agent with streaming
    print("Running async agent...")
    async with agent.run_stream("Hello!") as result:
        async for chunk in result.stream_text(delta=True):
            print(chunk, end="", flush=True)

    payloop.sentinel.raise_if_irrelevant(True)

    with pytest.raises(PayloopRequestInterceptedError):
        await agent.run("What is the capital of France?")
