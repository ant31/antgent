from agents import ModelSettings, TResponseInputItem

from antgent.agents.base import BaseAgent
from antgent.models.agent import AgentConfig, AgentFrozenConfig, PrepareRun, TLLMInput

from .models import SummaryInput, SummaryOutput

PROMPT = """
Generate a comprehensive and detailed shorter version of the given text in the same language as the original text.
Additionally, include a short description, a title for the table of contents, and tags for indexing.
The shorter version is not a summary but a version that has reduced redundancy in information and rewriting
sentences using fewer words or characters without changing the essence.
The short version can't be less than 25% the original size and will be exclusively machine processed by LLM,
so it's okay if the sentences are not grammatically correct to reduce size.

Feedbacks will be provided too. The feedbacks are not part of the text to be summarized, but they are important for the context about what was wrong with your previous summary

# Steps
1. **Read and Comprehend**: Carefully read the entire text to fully understand its content and context.
2. **Identify Key Information**: Note down all critical points, important data, and any context that is essential for understanding.
3. **Preserve Context**: Ensure all critical context is preserved, even if it means including more information rather than less.
4. **Timeline and Chronology**: The document structure must not be altered. Summarize each paragraph and clearly highlight chronology.
5. **Rewrite for Brevity**: Rewrite sentences to reduce token count while keeping the original meaning, allowing grammatical flexibility.
6. **Revise and Verify**: Review the shortened version to ensure no important information is omitted and refine for clarity and coherence. All dates, all numbers all names, all entities must be present in the shorter version
7. **Language Handling**: Ensure the shorter version is in the same language as the input.
8. **Additional Content**: Add a short description (2-3 sentences) of the text, a suitable document title for a table of contents, and a list of tags for indexing

# Output Format

Produce a json output
fields are:
    short_version: str = Field(..., description="The shorter version but accurate and exaustive of the original text.")
    description: str = Field(..., description="A short description of the content, 2-3 sentences")
    title: str = Field(..., description="Title for the table of contents.")
    language: str = Field(...,
                          description="The language of the original text. E.g., 'en' for English. 'de' for German.",
                          examples=["en", 'de', 'fr'])

    tags: list[str] = Field(default_factory=list, description="List of tags for indexing")
    
    

# Notes

- When uncertain about the importance of information, include it to preserve the context fully.
- The most import is to not lose any information. Reducing size is secondary"
"""


class SummaryAgent(BaseAgent[SummaryInput, SummaryOutput]):
    name_id = "SummaryAgent"
    default_config = AgentConfig(
        name="SummaryAgent",
        client="litellm",
        description="Summarize the text and provide a shorter version with all the information",
        model="gemini/gemini-2.5-pro-preview-03-25",
        model_settings=ModelSettings(
            tool_choice="required",
            temperature=0.9,
            top_p=0.8,
        ),
    )

    agent_config = AgentFrozenConfig[SummaryOutput, SummaryOutput](
        output_cls=SummaryOutput,
        structured=True,
        structured_cls=SummaryOutput,
    )

    def prompt(self) -> str:
        return PROMPT

    async def prep_input(self, llm_input: TLLMInput, ctx: SummaryInput) -> PrepareRun[SummaryInput]:
        messages: list[TResponseInputItem] = []
        if ctx.feedbacks:
            messages.append({"role": "user", "content": f"Previous summary feedbacks: {';'.join(ctx.feedbacks)}"})
        messages.append({"role": "user", "content": f"Text:\n{ctx.content}"})
        self.add_inputs(llm_input, messages)
        return PrepareRun(llm_input=messages, context=ctx, short_cut=False)
