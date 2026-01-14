"""Rate limiting for Telegram bot users."""

import time
from abc import ABC, abstractmethod
from typing import final


class Limit(ABC):
    """
    Abstract base for query limits.

    >>> limit = RateLimit(maximum=2, window=86400)
    >>> limit.consume(123)
    True
    >>> limit.consume(123)
    True
    >>> limit.consume(123)
    False
    """

    @abstractmethod
    def consume(self, user: int) -> bool:
        """
        Attempt to consume one query allowance for user.

        Returns True if query is allowed, False if limit exceeded.
        """


@final
class RateLimit(Limit):
    """
    In-memory per-user rate limit with rolling time window.

    >>> limit = RateLimit(maximum=3, window=60)
    >>> limit.consume(42)
    True
    """

    def __init__(self, maximum: int, window: int):
        self._maximum = maximum
        self._window = window
        self._usage: dict[int, list[float]] = {}

    def consume(self, user: int) -> bool:
        """
        Attempt to consume one query allowance for user.

        Returns True if query is allowed, False if limit exceeded.
        Prunes expired timestamps on each call.
        """
        now = time.time()
        cutoff = now - self._window
        timestamps = self._usage.get(user, [])
        valid = [t for t in timestamps if t > cutoff]
        if len(valid) >= self._maximum:
            self._usage[user] = valid
            return False
        valid.append(now)
        self._usage[user] = valid
        return True
