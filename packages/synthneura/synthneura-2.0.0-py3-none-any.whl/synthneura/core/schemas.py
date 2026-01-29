from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ClinicalTrial(BaseModel):
    """
    Canonical internal representation of a clinical trial
    normalized from ClinicalTrials.gov (API v2 or legacy).
    """

    # Core identifiers
    nct_id: str

    # Descriptive fields (often missing in real-world data)
    title: Optional[str] = None
    status: Optional[str] = None
    phase: Optional[str] = None
    sponsor: Optional[str] = None

    # Lists are defaulted to empty to avoid runtime errors
    conditions: List[str] = []
    interventions: List[str] = []
    outcomes: List[str] = []


class TopCount(BaseModel):
    value: str
    count: int


class Summary(BaseModel):
    """
    Aggregated summary statistics for a set of trials.
    """

    total_trials: int
    status_counts: Dict[str, int] = Field(default_factory=dict)
    phase_counts: Dict[str, int] = Field(default_factory=dict)
    top_conditions: List[TopCount] = Field(default_factory=list)
    top_sponsors: List[TopCount] = Field(default_factory=list)
    top_interventions: List[TopCount] = Field(default_factory=list)
    change_counts: Dict[str, int] = Field(default_factory=dict)
    run_id: Optional[str] = None
    ingested_at: Optional[str] = None
    source: Optional[str] = None
    query: Optional[str] = None
