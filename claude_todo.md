# Claude Sonnet/Opus Support Plan

## Goal
Enable agents to work with `claude-sonnet` and `claude-opus` models using the OpenAI Agents SDK,
with structured output support. Two complementary approaches are planned, ordered by simplicity.

---

## Context & Problem

The current `BaseAgent` uses three model backends:
- `OpenAIResponsesModel` (api_mode=response, client=openai)
- `OpenAIChatCompletionsModel` (api_mode=chat, client=openai)
- `LitellmModel` (api_mode=chat, client=litellm)

Claude and DeepSeek APIs do **not** support structured outputs (JSON schema constrained decoding)
natively via the OpenAI-compatible chat completions endpoint. Passing `output_type` to the SDK
with these models fails.

### Root cause
The OpenAI Agents SDK's `output_type` relies on the model returning a response conforming to a
JSON schema. Claude's OpenAI-compatible endpoint does not support this parameter.

### Two viable workarounds (confirmed working)

**Option A — LiteLLM (already works for Claude)**
LiteLLM transparently wraps structured output requests as function calls for Claude and converts
the response back. This is already implemented in LiteLLM (BerriAI/litellm#6748).
Using `LitellmModel(model="anthropic/claude-sonnet-4-5")` with `output_type` works today.

**Option B — FunctionTool / fake tool calling (works within the SDK)**
Force the model to call a fake tool whose schema matches the desired output. Use
`StopAtTools` + `tool_choice="required"` to guarantee the tool is called. Extract the
structured arguments from the tool call result. Works with `OpenAIChatCompletionsModel`
pointing at `https://api.anthropic.com/v1/` (Anthropic's OpenAI-compatible endpoint).

---

## Implementation Plan

### Phase 1 — LiteLLM path for Claude (simplest, already works)

**What to do:**
- Add `claude-` and `anthropic/` prefix mappings to `model_providers` defaults so that
  Claude models automatically route to `client="litellm"`, `api_mode="chat"`.
- LiteLLM handles the structured output → function call conversion transparently.
- No new code needed in `BaseAgent` or `AgentRunnerMixin`.

**Files to modify:**
- `antgent/models/agent.py`: No changes needed (litellm client already supported).
- `antgent/config.py`: Add claude prefix mappings to default `model_providers`.

**New provider mapping example in `localconfig.yaml`:**
```yaml
model_providers:
  default:
    client: "litellm"
    api_mode: "chat"
  mappings:
    - prefix: "gpt-"
      client: "openai"
      api_mode: "response"
    - prefix: "openai/"
      client: "openai"
      api_mode: "response"
    - prefix: "claude-"
      client: "litellm"
      api_mode: "chat"
    - prefix: "anthropic/"
      client: "litellm"
      api_mode: "chat"
```

**Usage example:**
```python
# In localconfig.yaml agents section:
agents:
  root:
    SummaryAgent:
      model: "anthropic/claude-sonnet-4-5"
      # client and api_mode auto-resolved to litellm/chat
      # LiteLLM handles structured output via function call workaround
```

**Limitation:** LiteLLM's Claude workaround is Claude-specific. DeepSeek and other models
that lack structured output support need Option B.

---

### Phase 2 — FunctionTool path (for models not covered by LiteLLM)

Add a new `api_mode="tool_structured"` that uses the FunctionTool trick within the existing
OpenAI Agents SDK, without bypassing `Runner`.

**How it works:**
```python
from agents import Agent, FunctionTool, ModelSettings, RunContextWrapper
from agents.agent import StopAtTools

tool = FunctionTool(
    name="structured_output",
    description="Return the structured result",
    params_json_schema=OutputCls.model_json_schema(),
    on_invoke_tool=lambda ctx, args: OutputCls.model_validate_json(args),
)

agent = Agent(
    name=...,
    instructions=...,
    tools=[tool],
    model=model,
    tool_use_behavior=StopAtTools(stop_at_tool_names=["structured_output"]),
    model_settings=ModelSettings(tool_choice="required"),
    # No output_type — structured output comes from tool args
)
```

The `final_output` from `Runner.run()` will be the return value of `on_invoke_tool`, which
is the validated Pydantic model instance.

**Files to modify:**
- `antgent/models/agent.py`: Add `"tool_structured"` to `api_mode` Literal.
- `antgent/agents/base.py`: Add `tool_structured` branch in `get_sdk_model()` and override
  `agent()` to inject the FunctionTool and set `tool_use_behavior`/`model_settings`.

**New `api_mode` values:**
- `"chat"` — existing, standard chat completions (no structured output guarantee)
- `"response"` — existing, OpenAI Responses API with native structured output
- `"tool_structured"` — new, FunctionTool trick for models without native structured output

**Client for `tool_structured` with Claude:**
Use `OpenAIChatCompletionsModel` pointing at Anthropic's OpenAI-compatible endpoint:
```python
from openai import AsyncOpenAI
provider = AsyncOpenAI(
    api_key=anthropic_api_key,
    base_url="https://api.anthropic.com/v1/"
)
model = OpenAIChatCompletionsModel(model="claude-sonnet-4-5", openai_client=provider)
```

This requires adding `"anthropic_openai"` as a new `client` type that creates an
`AsyncOpenAI` client pointed at the Anthropic base URL.

**Files to modify:**
- `antgent/models/agent.py`: Add `"anthropic_openai"` to `client` Literal.
- `antgent/clients.py`: Add `anthropic_openai_aclient()` factory.
- `antgent/agents/base.py`: Handle `client="anthropic_openai"` + `api_mode="tool_structured"`.
- `antgent/config.py`: Add optional `claude-` prefix mapping to `anthropic_openai`/`tool_structured`.

---

### Phase 3 — Configuration & model provider defaults

**File: `antgent/config.py`**

Add claude prefix mappings to default `model_providers` (Phase 1 — LiteLLM path):
```python
model_providers: ModelProvidersConfig = Field(
    default_factory=lambda: ModelProvidersConfig(
        default=ProviderSettings(client="litellm", api_mode="chat"),
        mappings=[
            ProviderMapping(prefix="gpt-", client="openai", api_mode="response"),
            ProviderMapping(prefix="openai/", client="openai", api_mode="response"),
            ProviderMapping(prefix="gemini/", client="litellm", api_mode="chat"),
            ProviderMapping(prefix="anthropic/", client="litellm", api_mode="chat"),
            ProviderMapping(prefix="claude-", client="litellm", api_mode="chat"),
        ]
    )
)
```

Users who want the FunctionTool path (Phase 2) can override in `localconfig.yaml`:
```yaml
model_providers:
  mappings:
    - prefix: "claude-"
      client: "anthropic_openai"
      api_mode: "tool_structured"
```

---

### Phase 4 — Tests

**New file: `tests/agents/test_claude_agent.py`**

- Test that `claude-` prefix resolves to `client="litellm"`, `api_mode="chat"` by default
- Test that `anthropic/` prefix resolves correctly
- Mock `LitellmModel` to verify it's called with the right model string
- Integration test with `claude-sonnet-4-5` via LiteLLM (skipped if no API key)
- Unit test for FunctionTool structured output path (Phase 2)
- Integration test for FunctionTool path with Anthropic OpenAI-compatible endpoint

---

## Decision: Which approach to use?

| Approach | Pros | Cons |
|----------|------|------|
| **LiteLLM (Phase 1)** | Zero new code, already works, transparent | LiteLLM-specific workaround, adds proxy layer |
| **FunctionTool (Phase 2)** | Works within SDK, no extra deps, model-agnostic | Requires new `api_mode`, slightly more complex |
| ~~Native Anthropic API~~ | Most control | Bypasses SDK entirely, most complex, overkill |

**Recommended approach:**
1. **Start with Phase 1 (LiteLLM)** — just add config mappings, zero risk, works today.
2. **Add Phase 2 (FunctionTool)** for models LiteLLM doesn't cover (DeepSeek, etc.) or when
   direct Anthropic endpoint access is preferred over LiteLLM proxy.

---

## Summary of New/Modified Files

| File | Action | Purpose |
|------|--------|---------|
| `antgent/config.py` | Modify | Add claude/anthropic prefix mappings to default `model_providers` |
| `antgent/models/agent.py` | Modify | Add `"tool_structured"` api_mode, `"anthropic_openai"` client (Phase 2) |
| `antgent/clients.py` | Modify | Add `anthropic_openai_aclient()` factory (Phase 2) |
| `antgent/agents/base.py` | Modify | Handle `tool_structured` mode with FunctionTool injection (Phase 2) |
| `tests/agents/test_claude_agent.py` | Create | Unit + integration tests |

---

## Dependencies

No new dependencies for Phase 1 (LiteLLM already in use).
Phase 2 requires no new dependencies either — uses existing `openai` and `agents` packages.

---

## Notes

- The LiteLLM workaround (Phase 1) is the path of least resistance and should be implemented
  first. It is already confirmed working with `anthropic/claude-sonnet-4-5`.
- The FunctionTool approach (Phase 2) is more robust long-term as it doesn't rely on LiteLLM's
  internal workaround staying in sync with Anthropic API changes.
- The native Anthropic API bypass (original plan) is **dropped** — it requires bypassing
  `Runner` entirely, adds significant complexity, and provides no advantage over Phase 2.
- `AgentFrozenConfig.structured=False` path already exists and works for all backends when
  structured output is not needed.
