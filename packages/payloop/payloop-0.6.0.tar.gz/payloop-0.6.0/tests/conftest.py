import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="Run integration tests",
    )
    parser.addoption(
        "--environment",
        action="store",
        default="staging",
        choices=["local", "staging"],
        help="Environment to run against (default: staging)",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests (require --integration)",
    )
    config.addinivalue_line("markers", "asyncio: marks tests as async")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--integration"):
        skip_integration = pytest.mark.skip(reason="need --integration to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)
