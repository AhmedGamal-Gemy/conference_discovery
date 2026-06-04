"""
Delay step — pauses execution between agents to avoid rate limits.
Supports exponential backoff with configurable base delay.
"""

import asyncio
import math
from typing import AsyncGenerator
from google.adk.agents.base_agent import BaseAgent
from google.adk.events.event import Event
from google.adk.events.event_actions import EventActions
from google.adk.agents.invocation_context import InvocationContext


class RateLimitDelayAgent(BaseAgent):
    """Agent that sleeps to avoid API rate limits.

    Uses exponential backoff: delay = base_seconds * (attempt ^ exponent)
    where attempt is tracked via session state or internal counter.
    """

    base_seconds: float = 30.0
    max_seconds: float = 300.0
    exponent: float = 1.5
    attempt_key: str = "rate_limit_attempt"

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        # Read or initialize attempt counter from session state
        attempt = 1
        try:
            attempt = int(getattr(ctx.session.state, self.attempt_key, 1))
        except (TypeError, ValueError):
            attempt = 1

        # Calculate delay with exponential backoff
        delay = min(self.base_seconds * (attempt ** self.exponent), self.max_seconds)
        
        print(f"[DELAY] Attempt {attempt}: sleeping {delay:.0f}s (base={self.base_seconds}s, exp={self.exponent})...")
        await asyncio.sleep(delay)
        print("[DELAY] Resuming.")

        # Increment attempt counter in state
        try:
            ctx.session.state[self.attempt_key] = attempt + 1
        except Exception:
            pass

        yield Event(
            author=self.name,
            content=None,
            actions=EventActions(),
            final_response=True,
        )


rate_limit_delay_agent = RateLimitDelayAgent(
    name="rate_limit_delay",
    description="Pauses with exponential backoff to avoid API rate limits",
)
