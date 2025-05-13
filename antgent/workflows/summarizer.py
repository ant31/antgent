import logging
import uuid

from agents.tracing import custom_span, trace

from antgent.agents.summarizer.models import SummaryGradeCtx, SummaryInput, SummaryResult
from antgent.agents.summarizer.summary import SummaryAgent
from antgent.agents.summarizer.summary_judge import SummaryJudgeAgent
from antgent.config import config
from antgent.models.agent import AgentConfig

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 2


class SummarizerWorkflow:
    def __init__(self, agentsconf: dict[str, AgentConfig] | None = None, max_interations: int = MAX_ITERATIONS):
        if agentsconf is None:
            agentsconf = config().agents
        self.max_iterations = max_interations
        self.summarize_agent = SummaryAgent(conf=agentsconf)
        self.judge_agent = SummaryJudgeAgent(conf=agentsconf)

    async def summarize(self, ctx: SummaryInput) -> SummaryResult:
        i = 0
        summaries = []
        grades = []
        with custom_span("Summary loop", data={}):
            while i < self.max_iterations:
                i += 1
                with custom_span(
                    f"Iteration {i}", data={"iteration": i, "grades": ",".join([str(g.grade) for g in grades])}
                ):
                    logger.info(f"Running summary iteration {i}, grades: {[g.grade for g in grades]}")
                    summary = await self.summarize_agent.workflow(llm_input="", context=ctx)
                    if summary is None:
                        logger.error("No summary generated, trying again")
                        continue
                    logger.info("Grading summary")
                    grade_ctx = SummaryGradeCtx(**summary.model_dump(), original_text=ctx.content)
                    summary_grade = await self.judge_agent.workflow(llm_input="", context=grade_ctx)
                    if summary_grade is None:
                        break
                    grades.append(summary_grade)
                    summaries.append(summary)
                    if summary_grade.grade >= 8 or (
                        len(summary_grade.missing_entities) == 0 and summary_grade.grade > 6
                    ):
                        break  # Summary is good enough return

                    # Create new summary with feedbacks
                    ctx.feedbacks = summary_grade.feedbacks

        best = 0
        for i, grade in enumerate(grades):
            if grade.grade >= grades[best].grade:
                best = i

        result = SummaryResult(summary=summaries[best], grades=grades, summaries=summaries)

        return result

    async def run(self, input_str: str, ctx: SummaryInput) -> SummaryResult:
        _ = input_str
        group_id = uuid.uuid4().hex[:16]
        with trace(
            workflow_name="Summarize",
            metadata={},
            group_id=group_id,
        ):
            res = await self.summarize(ctx)
            return res
