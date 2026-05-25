"""
Delay step — pauses execution between agents to avoid rate limits.
No LLM call; just an asyncio sleep.
"""

import asyncio
from typing import AsyncGenerator
from google.adk.agents.base_agent import BaseAgent
from google.adk.events.event import Event
from google.adk.events.event_actions import EventActions
from google.adk.agents.invocation_context import InvocationContext


class RateLimitDelayAgent(BaseAgent):
    """Agent that sleeps for a configured duration to avoid API rate limits."""

    sleep_seconds: float = 60.0

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        print(f"[DELAY] Sleeping {self.sleep_seconds}s to avoid rate limits...")
        await asyncio.sleep(self.sleep_seconds)
        print("[DELAY] Resuming.")
        yield Event(
            author=self.name,
            content=None,
            actions=EventActions(),
            final_response=True,
        )


rate_limit_delay_agent = RateLimitDelayAgent(
    name="rate_limit_delay",
    description="Pauses for 30 seconds to avoid API rate limits",
)
