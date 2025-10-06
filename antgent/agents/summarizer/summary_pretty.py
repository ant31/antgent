from agents import ModelSettings, TResponseInputItem

from antgent.agents.summarizer.summary import SummaryAgent
from antgent.agents.summarizer.summary_judge import SummaryJudgeAgent
from antgent.models.agent import AgentConfig, AgentFrozenConfig, PrepareRun, TLLMInput

from .models import SummaryGrade, SummaryGradeCtx

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
    default_config = AgentConfig(
        name="SummaryPretty",
        client="litellm",
        description="Create a short and concise summary of the content, with a description and title.",
        model="gemini/gemini-pro",
        model_settings=ModelSettings(
            tool_choice="none",
        ),
    )


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
