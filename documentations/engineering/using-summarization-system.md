# Using the Summarization System

The antgent framework includes a production-ready text summarization system that demonstrates advanced workflow patterns and serves as a reference implementation. This guide explains how to use and customize the summarization capabilities.

## Overview

The summarization system (introduced in v0.12.0) provides:

- **Multiple Summary Types**: Generate different summary styles for different use cases
- **Iterative Refinement**: Automatically improve summaries through multiple iterations with quality grading
- **Parallel Processing**: Generate multiple summary types simultaneously
- **Flexible APIs**: Both synchronous and asynchronous execution patterns

## Summary Types

### MACHINE Summary

Optimized for LLM processing and machine consumption:
- Preserves all information and context
- Reduces redundancy without losing detail
- Maintains original structure and chronology
- Allows grammatical flexibility to minimize token count
- Typically 25-75% of original size

**Use Cases:**
- Input for downstream LLM processing
- Archival and indexing
- Information retrieval systems
- When completeness is critical

### PRETTY Summary

Optimized for human reading:
- Concise and focused on key points
- Clear, grammatically correct sentences
- Removes contextual assumptions
- Direct and to-the-point
- Much shorter than MACHINE type

**Use Cases:**
- Email notifications
- Executive briefings
- User-facing displays
- Quick review and scanning

## Basic Usage

### Single Summary Type (Sync)

For immediate results with a single summary type:

```python
import requests

response = requests.post(
    "http://localhost:8000/api/workflows/summarizer/sync",
    json={
        "agent_input": {
            "context": {
                "content": "Your long text here...",
                "to_language": "en",
                "summary_type": "pretty",
                "iterations": 1
            }
        }
    }
)

result = response.json()
summary = result["result"]["summary"]["short_version"]
description = result["result"]["summary"]["description"]
title = result["result"]["summary"]["title"]
```

### Multiple Summary Types (Sync)

Generate both MACHINE and PRETTY summaries in parallel:

```python
response = requests.post(
    "http://localhost:8000/api/workflows/summarizer-multi/sync",
    json={
        "agent_input": {
            "context": {
                "content": "Your text here...",
                "to_language": "en",
                "iterations": 2 # This will be capped at 3 by the API
            }
        }
    }
)

result = response.json()
machine_summary = result["result"]["summaries"]["machine"]
pretty_summary = result["result"]["summaries"]["pretty"]
```

### Asynchronous Pattern

For long-running workflows, use the async pattern:

```python
import time
import requests

# Start the workflow
response = requests.post(
    "http://localhost:8000/api/workflows/summarizer/run",
    json={
        "agent_input": {
            "context": {
                "content": "Your text...",
                "to_language": "en",
                "iterations": 3
            }
        }
    }
)

workflow_id = response.json()["workflow_id"]

# Poll for status
while True:
    status_response = requests.get(
        f"http://localhost:8000/api/workflows/summarizer/{workflow_id}/status"
    )
    status_response.raise_for_status()
    status = status_response.json()
    
    if status.get("workflow_status") == "COMPLETED":
        result = status["result"]
        print("Summary:", result["summary"]["short_version"])
        break
    elif status.get("workflow_status") == "FAILED":
        print("Workflow failed:", status)
        break
    
    print(f"Workflow status: {status.get('workflow_status')}")
    time.sleep(5)
```

## Iterative Refinement

The system supports iterative refinement where summaries are automatically improved:

1. **Generate Initial Summary**: Agent produces first version
2. **Grade Quality**: Judge agent evaluates the summary (0-10 score)
3. **Provide Feedback**: Judge identifies missing information and issues
4. **Refine**: Agent generates improved version with feedback
5. **Repeat**: Continue until quality threshold met or max iterations reached
6. **Select Best**: Return the highest-graded summary

### Configuration

```python
{
    "context": {
        "content": "...",
        "iterations": 3,  # Number of refinement cycles
        "summary_type": "machine"
    }
}
```

**Iteration Guidelines:**
- `iterations=1`: No refinement, fastest but potentially lower quality
- `iterations=2`: One refinement cycle, balanced quality/speed
- `iterations=3`: Two refinement cycles, higher quality but slower
- `iterations>3`: Diminishing returns; API for multi-summary caps at 3.

### Quality Grading

The judge agent evaluates summaries based on:
- **Completeness**: Are all important entities, dates, and facts present?
- **Accuracy**: Is the information correctly represented?
- **Conciseness**: Is it appropriately concise for its type?
- **Structure**: Is it well-organized and clear?

Grades range from 0 to 10:
- **8-10**: Excellent, minimal improvements needed
- **6-7**: Good but could be improved
- **4-5**: Acceptable but has notable gaps
- **0-3**: Poor, significant issues

**Early Stopping:**
The system automatically stops iterating if a grade of 8 or higher is achieved.

## Customizing Agents

### Override Model Configuration

Use dynamic configuration to change models at runtime:

```python
{
    "agent_input": {
        "context": {...}
    },
    "agent_config": {
        "agents": {
            "SummaryAgent": {
                "model": "gpt-4o",
                "client": "openai"
            },
            "SummaryJudgeAgent": {
                "model": "claude-3-opus",
                "client": "litellm"
            }
        }
    }
}
```

### Extend Summary Types

To add a new summary type:

1. **Add to Enum:**
```python
# antgent/agents/summarizer/models.py
class SummaryType(StrEnum):
    PRETTY = "pretty"
    MACHINE = "machine"
    TECHNICAL = "technical"  # New type
```

2. **Create Agent Class:**
```python
# antgent/agents/summarizer/summary_technical.py
from .summary import SummaryAgent

class SummaryTechnicalAgent(SummaryAgent):
    name_id = "SummaryTechnical"
    
    def prompt(self):
        return """
        Generate a technical summary focused on:
        - Technical specifications and details
        - Precise terminology
        - Quantitative information
        ...
        """
```

3. **Update Logic:**
```python
# antgent/agents/summarizer/logic.py
async def summarize_one_type(ctx: SummaryInput):
    if ctx.summary_type == SummaryType.TECHNICAL:
        summarize_agent = SummaryTechnicalAgent()
        judge_agent = SummaryTechnicalJudgeAgent()
    elif ctx.summary_type == SummaryType.PRETTY:
        # ... existing code
```

## Integration Examples

### Using in Your Workflow

```python
from temporalio import activity
from antgent.agents.summarizer.logic import summarize_one_type
from antgent.agents.summarizer.models import SummaryInput, SummaryType

@activity.defn
async def process_document(doc_id: str) -> dict:
    # Load document
    content = "..." # load_document(doc_id)
    
    # Summarize with machine type
    ctx = SummaryInput(
        content=content,
        to_language="en",
        summary_type=SummaryType.MACHINE,
        iterations=2
    )
    
    result = await summarize_one_type(ctx)
    
    return {
        "summary": result.summary.short_version,
        "grade": result.grades[-1].grade if result.grades else None
    }
```

## Best Practices

1. **Choose the Right Type:**
   - Use MACHINE for complete, detailed summaries
   - Use PRETTY for user-facing, concise summaries

2. **Balance Quality and Performance:**
   - Start with `iterations=1` for speed
   - Use `iterations=2-3` for important documents
   - Monitor grades to tune iteration count

3. **Handle Long Documents:**
   - Split very long documents into sections
   - Summarize each section independently
   - Combine section summaries if needed

4. **Monitor Costs:**
   - More iterations = more LLM calls
   - Track token usage via `result.cost`
   - Use cheaper models for judge agents

5. **Language Support:**
   - Always specify `to_language` explicitly
   - Test with your target language
   - Consider language-specific model selection

## Troubleshooting

### Poor Quality Summaries

- Increase `iterations` to 2-3
- Try a more capable model (e.g., `gpt-4o` instead of `gpt-3.5-turbo`)
- Check if the content type matches the summary type

### Slow Performance

- Reduce `iterations` to 1
- Use faster models (e.g., `groq/llama-3-8b-8192`)
- Use the async pattern for better user experience

### Timeouts

- Increase activity timeout in workflow configuration (`start_to_close_timeout`)
- Split large documents
- Use async pattern instead of sync

### Missing Information

- Check judge agent feedback in `result.grades` from the API response
- Increase iterations
- Adjust prompt to emphasize completeness

## Reference

- **API Endpoints**: See [API Documentation](http://localhost:8000/docs)
- **Models**: `antgent/agents/summarizer/models.py`
- **Agents**: `antgent/agents/summarizer/`
- **Workflows**: `antgent/workflows/summarizer/text.py`
- **Logic**: `antgent/agents/summarizer/logic.py`
