from typing import Any

import pytest

from payloop._config import Config
from payloop._sentinel import Sentinel


@pytest.fixture
def config() -> Config:
    return Config()


@pytest.fixture
def sentinel(config: Config) -> Sentinel:
    return Sentinel(config)


@pytest.mark.parametrize("enabled", [True, False])
def test_raise_if_irrelevant(enabled: bool, config: Config, sentinel: Sentinel):
    sentinel.raise_if_irrelevant(enabled)

    assert config.raise_if_irrelevant is enabled


@pytest.mark.parametrize("enabled", [1, "foo", None])
def test_raise_if_irrelevant_raises_if_not_bool(enabled: Any, sentinel: Sentinel):
    with pytest.raises(TypeError, match="enabled must be a bool"):
        sentinel.raise_if_irrelevant(enabled)


def test_set_secs_irrelevant_request_timeout_int(config: Config, sentinel: Sentinel):
    sentinel.set_secs_irrelevant_request_timeout(10)

    assert config.secs_irrelevant_request_timeout == 10


def test_set_secs_irrelevant_request_timeout_float(config: Config, sentinel: Sentinel):
    sentinel.set_secs_irrelevant_request_timeout(4.5)

    assert config.secs_irrelevant_request_timeout == 4.5


@pytest.mark.parametrize(
    "timeout,expected_message",
    [
        ("foo", "timeout must be an int or float"),
        (None, "timeout must be an int or float"),
    ],
)
def test_set_secs_irrelevant_request_timeout_raises_type_error(
    timeout: Any, expected_message: str, sentinel: Sentinel
):
    with pytest.raises(TypeError, match=expected_message):
        sentinel.set_secs_irrelevant_request_timeout(timeout)


@pytest.mark.parametrize("timeout", [0, -1, -0.01])
def test_set_secs_irrelevant_request_timeout_raises_when_timeout_lte_zero(
    timeout: Any, sentinel: Sentinel
):
    with pytest.raises(ValueError, match="timeout must be greater than 0"):
        sentinel.set_secs_irrelevant_request_timeout(timeout)
