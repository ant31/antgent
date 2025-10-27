from enum import StrEnum

from pydantic import BaseModel, Field


class SummaryType(StrEnum):
    """Enumeration of available summary types. Easy to extend with new types."""

    PRETTY = "pretty"
    MACHINE = "machine"


class SummaryInput(BaseModel):
    content: str = Field(...)
    feedbacks: list[str] = Field(
        default_factory=list, description="List of feedbacks for creating the less verbose text"
    )
    to_language: str = Field(
        "de", description="The language to translate the summary to. E.g., 'en' for English, 'de' for German."
    )
    summary_type: SummaryType = Field(default=SummaryType.MACHINE, description="The type of summary to generate.")
    iterations: int = Field(default=1, description="Number of iterations for summarization and grading.")


class Entity(BaseModel):
    name: str = Field(..., description="Name of the entity")
    type: str = Field(..., description="Type of the entity. E.g., 'name', 'date', 'number', 'place', etc.")


class GradeFeedback(BaseModel):
    grade: int = Field(..., description="Grade of the assignment, from 0 to 10")
    feedbacks: list[str] = Field(..., description="Feedbacks to improve the assignment")
    grade_reasoning: str = Field(
        ..., description="Reasoning for the grade, what was good and what was bad in the assignment"
    )


class SummaryGrade(GradeFeedback):
    missing_entities: list[Entity] = Field(
        ..., description="List of missing entities in the less verbose text, keep empty if none"
    )


class SummaryOutput(BaseModel):
    short_version: str = Field(
        ...,
        description=(
            "The shorter version but accurate and exaustive of the original text. "
            "In Markdown format with clear headings and paragraphs"
        ),
    )
    description: str = Field(..., description="A short description of the content, 1 to 3 sentences")
    title: str = Field(..., description="Title for the table of contents.")
    tags: list[str] = Field(default_factory=list, description="List of tags for indexing")
    language: str = Field(..., description="The language of the output text. E.g., 'en' for English. 'de' for German.")


class SummaryGradeCtx(SummaryOutput):
    original_text: str = Field(..., description="The original text")


class InternalSummaryResult(BaseModel):
    """Internal model for a rich summary result, including grading and intermediate steps.
    This should NOT be exposed directly in API responses."""

    summary: SummaryOutput = Field(..., description="The best summary generated after all iterations.")
    grades: list[SummaryGrade] = Field(default_factory=list, description="Grading details from each iteration.")
    summaries: list[SummaryOutput] = Field(
        default_factory=list, description="All summaries generated during the iterations."
    )
    summary_type: SummaryType = Field(..., description="The type of summary that was generated.")


class InternalSummariesAllResult(BaseModel):
    """Internal model holding the full, detailed results for multiple summary types.
    This is the raw output from the multi-summary workflow."""

    summaries: dict[SummaryType, InternalSummaryResult | None] = Field(
        default_factory=dict, description="A dictionary mapping each summary type to its detailed internal result."
    )


class SummariesResult(BaseModel):
    """Clean, public-facing API model for multi-summary results.
    This model intentionally omits internal details like grades and iterations."""

    summaries: dict[SummaryType, SummaryOutput | None] = Field(
        default_factory=dict, description="A dictionary mapping each summary type to its final summary output."
    )
