from agents import ModelSettings, TResponseInputItem

from antgent.agents.base import BaseAgent
from antgent.models.agent import AgentConfig, AgentFrozenConfig, PrepareRun, TLLMInput

from .models import SummaryGrade, SummaryGradeCtx

PROMPT = """
You're a professor evaluating assignemnts and giving feedback
you'll be provided with a less verbose text done from a student and the original text.
You must grade from 0-10 the less verbose text quality, 0 being non-sense, 10 being the best.

The less verbose text must contains ALL entities, date, place, people, addresses, amounts.
1. If one entity missing, the grade can't be more than 5, it's a critical mistake
2. A perfect less verbose text is the one that are short but still retains 100% of the informations
3. Take away points for every information that are missing
4. Shortness of the less verbose text is too relevant and should impact too much the grade

Provide the feedbacks as json
{
"missing_entitites": ["date XYZ"]
"feebacks": [
"It's missing the date XYZ", "the address was not mentioned"
],
"grade": 6
"grade_reasoning": "you were missing some information taht could be important, also it was too wordy for a less verbose text"

}

"""


class SummaryJudgeAgent(BaseAgent[SummaryGradeCtx, SummaryGrade]):
    name_id = "SummaryJudge"
    agent_config = AgentFrozenConfig(output_cls=SummaryGrade, structured=True)
    default_config = AgentConfig(
        name="SummaryJudge",
        client="litellm",
        description="Judge the less verbose text and provide feedbacks",
        model="gemini/gemini-pro",
        model_settings=ModelSettings(
            tool_choice="none",
        ),
    )

    def prompt(self) -> str:
        return PROMPT

    async def prep_input(self, llm_input: TLLMInput, ctx: SummaryGradeCtx) -> PrepareRun[SummaryGradeCtx]:
        messages: list[TResponseInputItem] = [
            {"role": "user", "content": f"\n-------\nOriginal text:\n {ctx.original_text}"},
            {"role": "user", "content": f"\n-------\nLess Verbose Text:\n {ctx.short_version}"},
        ]
        self.add_inputs(llm_input, messages)
        return PrepareRun(llm_input=messages, context=ctx, short_cut=False)
