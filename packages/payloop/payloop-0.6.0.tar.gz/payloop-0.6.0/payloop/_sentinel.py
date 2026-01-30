r"""
 ___           _
| _ \__ _ _  _| |___  ___ _ __
|  _/ _` | || | / _ \/ _ \ '_ \
|_| \__,_|\_, |_\___/\___/ .__/
          |__/           |_|AI             07312025 / optimus codex
"""

from typing import Union

from payloop._config import Config


class Sentinel:
    def __init__(self, config: Config):
        self.config = config

    def raise_if_irrelevant(self, enabled: bool = True):
        if not isinstance(enabled, bool):
            raise TypeError("enabled must be a bool")

        self.config.raise_if_irrelevant = enabled
        return self

    def set_secs_irrelevant_request_timeout(self, timeout: Union[int, float]):
        if not isinstance(timeout, (int, float)):
            raise TypeError("timeout must be an int or float")
        elif timeout <= 0:
            raise ValueError("timeout must be greater than 0")

        self.config.secs_irrelevant_request_timeout = timeout
        return self
