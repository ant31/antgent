from pydantic import BaseModel, Field


class SummaryInput(BaseModel):
    content: str = Field(...)
    feedbacks: list[str] = Field(
        default_factory=list, description="List of feedbacks for creating the less verbose text"
    )
    to_language: str = Field(
        "de", description="The language to translate the summary to. E.g., 'en' for English, 'de' for German."
    )


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


class SummaryResult(BaseModel):
    summary: SummaryOutput = Field(..., description="The summary of the content")
