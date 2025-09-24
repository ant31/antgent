from agents import ModelSettings, TResponseInputItem

from antgent.agents.summarizer.summary import SummaryAgent
from antgent.agents.summarizer.summary_judge import SummaryJudgeAgent
from antgent.models.agent import AgentConfig, AgentFrozenConfig, PrepareRun, TLLMInput

from .models import SummaryGrade, SummaryGradeCtx, SummaryOutput

PROMPT = """
You are a professional summarizer.

The reader of the summary are busy people who want to get the gist of the content quickly.
They already know most of the context, such as parties involved. There's no need to explain the context.
Provide a summary of the content that is short, concise, and to the point.
Format the summary as a Markdown document.

The description should be a short paragraph, 1 to 3 sentences, that gives an overview of the content.
For example, if we receive a long text but the main point is that the person agree to a deal, the description should be something like:
 - "The person agreed to the deal with the company"
Then the summary should be a short version of the text, that is accurate but concise for efficient reading.

If the reader wants to know more, they can read the original text easily.
The summary can be up to few paragraphs long, but no more than that.

All summary must be in the language mentioned by the user.

Avoid long sentences and redundant information.
For example:
- "the text is about the agreement with the company"  is not a good description, but "The person agreed to the deal with the company" is a good description.
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

PROMPT_JUDGE: str = """
You are a professional reviewer of summaries.
The reader of the summary are busy people who want to get the gist of the content quickly.
You will be provided with a summary and the original text.
You must grade from 0-10 the summary quality, 0 being non-sense, 10 being the best.
The summary must be short, concise, and to the point.
The reader already knows most of the context, such as parties involved. There's no need to explain the context.
If they need know more, they can read the original text easily.
Goal is provide the reader with a short and concise summary of the content, with a description and title.

Give a grade from 0 to 10, where 0 is the worst and 10 is the best.
Provide the feedbacks as json

{
"grade":
"grade_reasoning": ""
}
"""


class SummaryPrettyAgent(SummaryAgent):
    name_id = "SummaryPretty"
    agent_config = AgentFrozenConfig(output_cls=SummaryOutput, structured=True)
    default_config = AgentConfig(
        name="SummaryPretty",
        client="litellm",
        description="Create a short and concise summary of the content, with a description and title.",
        model="gemini/gemini-pro",
        model_settings=ModelSettings(
            tool_choice="none",
        ),
    )

    def prompt(self):
        return PROMPT


class SummaryPrettyJudgeAgent(SummaryJudgeAgent):
    name_id = "SummaryPrettyJudge"
    agent_config = AgentFrozenConfig(output_cls=SummaryGrade, structured=True)
    default_config = AgentConfig(
        name="SummaryPrettyJudge",
        client="litellm",
        description="Judge the summary and provide feedbacks",
        model="gemini/gemini-pro",
        model_settings=ModelSettings(
            tool_choice="none",
        ),
    )

    def prompt(self) -> str:
        return PROMPT_JUDGE

    async def prep_input(self, llm_input: TLLMInput, ctx: SummaryGradeCtx) -> PrepareRun[SummaryGradeCtx]:
        messages: list[TResponseInputItem] = [
            {"role": "user", "content": f"\n-------\nOriginal text:\n {ctx.original_text}\n\n\n###\n"},
            {"role": "user", "content": f"\n-------\nTitle:\n {ctx.title}\n"},
            {"role": "user", "content": f"\n-------\nDescription:\n {ctx.description}\n"},
            {"role": "user", "content": f"\n-------\nSummary:\n {ctx.short_version}\n"},
        ]
        self.add_inputs(llm_input, messages)
        return PrepareRun(llm_input=messages, context=ctx, short_cut=False)
