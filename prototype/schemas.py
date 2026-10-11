"""Data contracts. Shape validation is separate from factual correctness."""
from datetime import date
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Source(Contract):
    id: str = Field(pattern=r"^[A-Z][A-Z0-9-]{1,39}$")
    kind: Literal["partner", "engineering", "action", "context"]
    date: date | None
    title: str = Field(min_length=1, max_length=160)
    text: str = Field(min_length=8, max_length=6000)


class SourcePack(Contract):
    report_type: Literal['Engineering','Vendor','Partner'] = 'Engineering'
    label: str = Field(min_length=1, max_length=120)
    week_start: date
    sources: list[Source] = Field(min_length=0, max_length=40)

    @field_validator("week_start")
    @classmethod
    def monday_start(cls, value):
        if value.weekday() != 0:
            raise ValueError("The reporting week must start on a Monday (UTC).")
        return value

    @model_validator(mode="after")
    def unique_sources(self):
        ids = [source.id for source in self.sources]
        if len(ids) != len(set(ids)):
            raise ValueError("Source IDs must be unique.")
        if sum(len(s.text) for s in self.sources) > 40000:
            raise ValueError("Keep the source pack under 40,000 characters for this prototype.")
        return self


class Evidence(Contract):
    source_id: str = Field(min_length=1, max_length=40)
    quote: str = Field(min_length=8, max_length=600)


class Finding(Contract):
    category: Literal["partner feedback", "engineering update", "open action", "risk", "source note"]
    title: str = Field(min_length=1, max_length=120)
    summary: str = Field(min_length=1, max_length=700)
    evidence: list[Evidence] = Field(min_length=1, max_length=5)
    needs_review: bool
    review_reason: str = Field(max_length=300)


class Narrative(Contract):
    findings: list[Finding] = Field(min_length=0, max_length=10)
    discussion_questions: list[str] = Field(max_length=5)


class MetricResult(Contract):
    key: str
    label: str
    unit: str
    previous: float | None
    current: float | None
    delta: float | None
    delta_kind: str
    previous_period: str
    current_period: str
    cohort: str
    source_rows: list[int]


class Issue(Contract):
    severity: Literal["warning", "error"]
    code: str
    message: str
