import os

import pytest

ENVIRONMENT_PAYLOOP_API_URL_BASE = {
    "local": "http://localhost:8000",
    "staging": "https://staging-api.trypayloop.com",
}

ENVIRONMENT_PAYLOOP_COLLECTOR_URL_BASE = {
    "local": "http://localhost:8002",
    "staging": "https://staging-collector.trypayloop.com",
}


@pytest.fixture(autouse=True)
def integration_environment(request):
    """Set environment variables for integration tests."""
    if "integration" not in request.keywords:
        return

    if not os.environ.get("PAYLOOP_API_KEY"):
        pytest.fail("PAYLOOP_API_KEY environment variable is not set")

    env = request.config.getoption("--environment")

    # Set required env vars
    # os.environ["PAYLOOP_TEST_MODE"] = "1"
    os.environ["PAYLOOP_API_URL_BASE"] = ENVIRONMENT_PAYLOOP_API_URL_BASE[env]
    os.environ["PAYLOOP_COLLECTOR_URL_BASE"] = ENVIRONMENT_PAYLOOP_COLLECTOR_URL_BASE[
        env
    ]

    yield
