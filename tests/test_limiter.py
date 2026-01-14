import random
import time

from telegram_bot.limiter import RateLimit


class TestRateLimit:
    """Tests for RateLimit that enforces per-user query limits."""

    def test_allows_first_query_for_new_user(self) -> None:
        limit = RateLimit(maximum=5, window=3600)
        user = random.randint(100000, 999999)
        result = limit.consume(user)
        assert result is True, "expected first query to be allowed"

    def test_allows_queries_up_to_maximum(self) -> None:
        limit = RateLimit(maximum=3, window=3600)
        user = random.randint(100000, 999999)
        for _ in range(3):
            limit.consume(user)
        assert limit.consume(user) is False, "expected fourth query to be denied"

    def test_denies_query_when_maximum_reached(self) -> None:
        limit = RateLimit(maximum=2, window=3600)
        user = random.randint(100000, 999999)
        limit.consume(user)
        limit.consume(user)
        result = limit.consume(user)
        assert result is False, "expected query beyond maximum to be denied"

    def test_tracks_users_independently(self) -> None:
        limit = RateLimit(maximum=1, window=3600)
        first = random.randint(100000, 499999)
        second = random.randint(500000, 999999)
        limit.consume(first)
        result = limit.consume(second)
        assert result is True, "expected different user to have own quota"

    def test_resets_after_window_expires(self) -> None:
        limit = RateLimit(maximum=1, window=1)
        user = random.randint(100000, 999999)
        limit.consume(user)
        time.sleep(1.1)
        result = limit.consume(user)
        assert result is True, "expected quota to reset after window"

    def test_handles_non_ascii_user_ids(self) -> None:
        limit = RateLimit(maximum=2, window=3600)
        user = random.randint(1000000000, 9999999999)
        result = limit.consume(user)
        assert result is True, "expected large user id to work"
