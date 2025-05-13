from pydantic import BaseModel, Field


class SummaryInput(BaseModel):
    content: str = Field(...)
    feedbacks: list[str] = Field(
        default_factory=list, description="List of feedbacks for creating the less verbose text"
    )


class Entity(BaseModel):
    name: str = Field(..., description="Name of the entity")
    type: str = Field(..., description="Type of the entity. E.g., 'name', 'date', 'number', 'place', etc.")


class SummaryGrade(BaseModel):
    missing_entities: list[Entity] = Field(
        ..., description="List of missing entities in the less verbose text, keep empty if none"
    )
    feedbacks: list[str] = Field(..., description="List of feedback of for the less verbose text")
    grade_reasoning: str = Field(..., description="Reasoning for the grade")
    grade: int = Field(..., description="Grade of the less verbose text")


#     better_summary: str = Field(..., description="A better summary of the text")


class SummaryOutput(BaseModel):
    short_version: str = Field(..., description="The shorter version but accurate and exaustive of the original text.")
    description: str = Field(..., description="A short description of the content, 2-3 sentences")
    title: str = Field(..., description="Title for the table of contents.")
    tags: list[str] = Field(default_factory=list, description="List of tags for indexing")
    language: str = Field(
        ..., description="The language of the original text. E.g., 'en' for English. 'de' for German."
    )


class SummaryGradeCtx(SummaryOutput):
    original_text: str = Field(..., description="The original text")


class SummaryResult(BaseModel):
    summary: SummaryOutput = Field(..., description="The summary of the content")
    grades: list[SummaryGrade] = Field(default_factory=list, description="The grade of the summary")
    summaries: list[SummaryOutput] = Field(default_factory=list, description="The summaries of the content")
