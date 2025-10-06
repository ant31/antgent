from agents import ModelSettings, TResponseInputItem

from antgent.agents.base import BaseAgent
from antgent.models.agent import AgentConfig, AgentFrozenConfig, PrepareRun, TLLMInput

from .models import SummaryInput, SummaryOutput

PROMPT = """
You are a professional summarizer.

The reader of the summary are busy people who want to get the gist of the content quickly.
They already know most of the context, such as parties involved. There's no need to explain the context.
Provide a summary of the content that is short, concise, and to the point.
Format the summary as a Markdown document.

The description should be a short paragraph, 1 to 3 sentences, that gives an overview of the content.
For example, if we receive a long text but the main point is that the person agree to a deal,
the description should be something like:
 - "The person agreed to the deal with the company"
Then the summary should be a short version of the text, that is accurate but concise for efficient reading.

If the reader wants to know more, they can read the original text easily.
The summary can be up to few paragraphs long, but no more than that.

All summary must be in the language mentioned by the user.

Avoid long sentences and redundant information.
For example:
- "the text is about the agreement with the company"  is not a good description,
  but "The person agreed to the deal with the company" is a good description.
"In The text...." or "In the document...."  or "In the email..." is not good, go directly to the point.


# Output Format

Produce a json output
fields are:
    short_version: str = Field(..., description="The summary. in Markdown format with clear headings and paragraphs")
    description: str = Field(..., description="A short description of the content, 1 to 3 sentences")
    title: str = Field(..., description="Title for the table of contents.")
    language: str = Field(...,
                          description="The language of the original text. E.g., 'en' for English. 'de' for German.",
                          examples=["en", 'de', 'fr'])

    tags: list[str] = Field(default_factory=list, description="List of tags for indexing")
"""


class SummaryAgent(BaseAgent[SummaryInput, SummaryOutput]):
    name_id = "SummaryAgent"
    default_config = AgentConfig(
        name="SummaryAgent",
        client="litellm",
        description="Create a short and concise summary of the content, with a description and title.",
        model="gemini/gemini-pro",
        model_settings=ModelSettings(
            tool_choice="none",
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
        messages.append({"role": "user", "content": f"Generate summaries and text in Language: {ctx.to_language}\n"})
        messages.append({"role": "user", "content": f"Original Text:\n{ctx.content}\n"})
        self.add_inputs(llm_input, messages)
        return PrepareRun(llm_input=messages, context=ctx, short_cut=False)
