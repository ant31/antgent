"""
Demo script to test structured output with Claude models using AntGent primitives.

Tests both approaches from the plan:
- Phase 1: LiteLLM transparent workaround (client="litellm", model="anthropic/claude-*")
- Phase 2: Direct Anthropic OpenAI-compatible endpoint (client="openai" + custom base_url)

Usage:
    ANTHROPIC_API_KEY=sk-ant-... uv run python demo/claude/test_structured_output.py
"""

import asyncio
import os

from agents import TResponseInputItem
from pydantic import BaseModel, Field

from antgent.agents.base import BaseAgent
from antgent.models.agent import AgentConfig, AgentFrozenConfig, PrepareRun, TLLMInput

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL_LITELLM = "anthropic/claude-sonnet-4-5"
MODEL_DIRECT = "claude-sonnet-4-5"
ANTHROPIC_BASE_URL = "https://api.anthropic.com"

INPUT_TEXT = """
Let's schedule a team meeting called 'Product Kickoff' on October 15th, 2025.
Participants will be Alice, Bob, and Charlie.
"""

INSTRUCTIONS = "Extract calendar events from text and return them in structured JSON format."


# ── Output model ──────────────────────────────────────────────────────────────

class CalendarEvent(BaseModel):
    name: str = Field(..., description="Name of the event")
    date: str = Field(..., description="Date of the event")
    participants: list[str] = Field(..., description="List of participant names")


# ── Context model (passed through to prep_input) ──────────────────────────────

class CalendarCtx(BaseModel):
    text: str = Field(..., description="Raw text to extract the event from")


# ── Phase 1: LiteLLM agent ────────────────────────────────────────────────────

class CalendarAgentLiteLLM(BaseAgent[CalendarCtx, CalendarEvent]):
    """Extracts calendar events via LiteLLM (transparent Claude workaround)."""

    name_id = "CalendarAgentLiteLLM"
    agent_config = AgentFrozenConfig(output_cls=CalendarEvent, structured=True, run_kwargs={"max_turns": 1})
    default_config = AgentConfig(
        name="CalendarAgentLiteLLM",
        client="litellm",
        model=MODEL_LITELLM,
        api_key=ANTHROPIC_API_KEY,
        description="Extract calendar events from text using LiteLLM + Claude",
    )

    def prompt(self) -> str:
        return INSTRUCTIONS

    async def prep_input(self, llm_input: TLLMInput, ctx: CalendarCtx) -> PrepareRun[CalendarCtx]:
        messages: list[TResponseInputItem] = [
            {"role": "user", "content": ctx.text},
        ]
        self.add_inputs(llm_input, messages)
        return PrepareRun(llm_input=messages, context=ctx, short_cut=False)


# ── Phase 2: Direct Anthropic endpoint agent ──────────────────────────────────

class CalendarAgentDirect(BaseAgent[CalendarCtx, CalendarEvent]):
    """Extracts calendar events via Anthropic's OpenAI-compatible endpoint."""

    name_id = "CalendarAgentDirect"
    agent_config = AgentFrozenConfig(output_cls=CalendarEvent, structured=True, run_kwargs={"max_turns": 1})
    default_config = AgentConfig(
        name="CalendarAgentDirect",
        client="litellm",
        api_mode="chat",
        model=MODEL_DIRECT,
        api_key=ANTHROPIC_API_KEY,
        base_url=ANTHROPIC_BASE_URL,
        description="Extract calendar events from text using Anthropic endpoint directly",
    )

    def prompt(self) -> str:
        return INSTRUCTIONS

    async def prep_input(self, llm_input: TLLMInput, ctx: CalendarCtx) -> PrepareRun[CalendarCtx]:
        messages: list[TResponseInputItem] = [
            {"role": "user", "content": ctx.text},
        ]
        self.add_inputs(llm_input, messages)
        return PrepareRun(llm_input=messages, context=ctx, short_cut=False)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _print_event(event: CalendarEvent) -> None:
    print(f"  name         : {event.name}")
    print(f"  date         : {event.date}")
    print(f"  participants : {event.participants}")


def _assert_event(event: CalendarEvent) -> None:
    assert isinstance(event, CalendarEvent), "Expected CalendarEvent instance"
    assert event.name, "name must not be empty"
    assert event.date, "date must not be empty"
    assert len(event.participants) > 0, "participants must not be empty"


# ── Tests ─────────────────────────────────────────────────────────────────────

async def test_litellm():
    """Phase 1: LiteLLM handles structured output → function call conversion transparently."""
    print("\n" + "=" * 60)
    print("Phase 1: LiteLLM transparent workaround")
    print("=" * 60)

    if not ANTHROPIC_API_KEY:
        print("SKIP — ANTHROPIC_API_KEY not set")
        return

    agent = CalendarAgentLiteLLM()
    ctx = CalendarCtx(text=INPUT_TEXT)
    event = await agent.workflow(llm_input="", context=ctx)

    assert event is not None, "No output returned"
    _print_event(event)
    _assert_event(event)
    print("  ✓ PASSED")


async def test_direct():
    """Phase 2: Direct Anthropic OpenAI-compatible endpoint via openai client."""
    print("\n" + "=" * 60)
    print("Phase 2: Direct Anthropic endpoint (openai client + base_url)")
    print("=" * 60)

    if not ANTHROPIC_API_KEY:
        print("SKIP — ANTHROPIC_API_KEY not set")
        return

    agent = CalendarAgentDirect()
    ctx = CalendarCtx(text=INPUT_TEXT)
    event = await agent.workflow(llm_input="", context=ctx)

    assert event is not None, "No output returned"
    _print_event(event)
    _assert_event(event)
    print("  ✓ PASSED")


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    print("Claude Structured Output Demo (AntGent primitives)")
    print(f"LiteLLM model : {MODEL_LITELLM}")
    print(f"Direct model  : {MODEL_DIRECT}")
    print(f"API key set   : {'yes' if ANTHROPIC_API_KEY else 'NO — set ANTHROPIC_API_KEY'}")

    await test_litellm()
    await test_direct()

    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
