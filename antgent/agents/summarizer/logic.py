import logging

from agents.tracing import custom_span
from temporalio.exceptions import ApplicationError

from antgent.agents.summarizer.models import (
    InternalSummaryResult,
    SummaryGrade,
    SummaryGradeCtx,
    SummaryInput,
    SummaryOutput,
    SummaryType,
)
from antgent.agents.summarizer.summary import SummaryAgent
from antgent.agents.summarizer.summary_judge import SummaryJudgeAgent
from antgent.agents.summarizer.summary_pretty import (
    SummaryPrettyAgent,
    SummaryPrettyJudgeAgent,
)
from antgent.config import config

logger = logging.getLogger(__name__)


async def summarize_one_type(ctx: SummaryInput) -> InternalSummaryResult:
    """Helper function to run one type of summarization logic."""
    agentsconf = config().agents
    if ctx.summary_type == SummaryType.PRETTY:
        summarize_agent = SummaryPrettyAgent(conf=agentsconf)
        judge_agent = SummaryPrettyJudgeAgent(conf=agentsconf)
    else:
        summarize_agent = SummaryAgent(conf=agentsconf)
        judge_agent = SummaryJudgeAgent(conf=agentsconf)

    iterations = ctx.iterations
    if iterations == 0:
        iterations = 1

    i = 0
    summaries: list[SummaryOutput] = []
    grades: list[SummaryGrade] = []
    with custom_span(f"{summarize_agent.name_id} loop", data={}):
        while i < iterations:
            i += 1
            with custom_span(
                f"Iteration {i}", data={"iteration": i, "grades": ",".join([str(g.grade) for g in grades])}
            ):
                logger.info(f"Running summary iteration {i}, grades: {[g.grade for g in grades]}")
                summary = await summarize_agent.workflow(llm_input="", context=ctx)
                if summary is None:
                    logger.error("No summary generated, trying again")
                    continue
                summaries.append(summary)

                if iterations == 1:
                    break

                logger.info("Grading summary")
                grade_ctx = SummaryGradeCtx(**summary.model_dump(), original_text=ctx.content)
                summary_grade = await judge_agent.workflow(llm_input="", context=grade_ctx)
                if summary_grade is None:
                    break
                grades.append(summary_grade)

                if summary_grade.grade >= 8 or (len(summary_grade.missing_entities) == 0 and summary_grade.grade > 6):
                    break  # Summary is good enough return

                # Create new summary with feedbacks
                ctx.feedbacks = summary_grade.feedbacks

    if not summaries:
        raise ApplicationError("No summaries generated")

    best = 0
    if grades:
        for i, grade in enumerate(grades):
            if grade.grade >= grades[best].grade:
                best = i
    else:
        # If there are no grades (e.g., iterations=1), the best summary is the last one generated.
        best = len(summaries) - 1

    result = InternalSummaryResult(
        summary=summaries[best], grades=grades, summaries=summaries, summary_type=ctx.summary_type
    )

    return result
