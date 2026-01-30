"""Exponential backoff with jitter for approval status polling."""

import random
import time


class ExponentialBackoff:
    """Exponential backoff calculator with jitter support."""

    def __init__(
        self,
        initial_delay_s: float,
        max_delay_s: float,
        jitter_ratio: float = 0.1,
        multiplier: float = 2.0,
    ) -> None:
        """Initialize exponential backoff calculator.

        Args:
            initial_delay_s: Initial delay in seconds
            max_delay_s: Maximum delay cap in seconds
            jitter_ratio: Jitter ratio (0.0-0.5) for randomization
            multiplier: Backoff multiplier (default 2.0 for doubling)
        """
        self.initial_delay_s = initial_delay_s
        self.max_delay_s = max_delay_s
        self.jitter_ratio = max(0.0, min(jitter_ratio, 0.5))
        self.multiplier = multiplier
        self._current_attempt = 0

    def reset(self) -> None:
        """Reset the backoff state."""
        self._current_attempt = 0

    def next_delay(self) -> float:
        """Calculate the next delay with exponential backoff and jitter.

        Returns:
            Delay in seconds for the next attempt
        """
        if self._current_attempt == 0:
            delay = self.initial_delay_s
        else:
            # Exponential backoff: initial * multiplier^(attempt-1)
            delay = self.initial_delay_s * (
                self.multiplier ** (self._current_attempt - 1)
            )

        # Apply max delay cap
        delay = min(delay, self.max_delay_s)

        # Apply jitter: delay ± (delay * jitter_ratio)
        jitter_amount = delay * self.jitter_ratio
        jittered_delay = delay + random.uniform(-jitter_amount, jitter_amount)

        # Ensure delay is positive and respects max cap after jitter
        jittered_delay = max(0.1, min(jittered_delay, self.max_delay_s))

        self._current_attempt += 1
        return jittered_delay

    @property
    def attempt_count(self) -> int:
        """Get the current attempt count.

        Returns:
            Number of attempts made
        """
        return self._current_attempt


def sleep_with_backoff(backoff: ExponentialBackoff) -> None:
    """Sleep for the next backoff delay.

    Args:
        backoff: ExponentialBackoff instance
    """
    delay = backoff.next_delay()
    time.sleep(delay)
