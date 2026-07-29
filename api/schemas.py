"""
Pydantic schemas for the Eleva API (request / response).
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    company_id: str = Field(..., description="Company identifier")
    question: str = Field(
        default="Analyse la situation actuelle et propose les actions prioritaires.",
        description="Natural language analysis request",
    )
    focus_areas: Optional[List[str]] = Field(default=None)
    max_recommendations: int = Field(default=3, ge=1, le=10)


class KPIOut(BaseModel):
    name: str
    value: Any
    unit: Optional[str] = None


class SegmentOut(BaseModel):
    name: str
    size: int
    percentage: float


class IssueOut(BaseModel):
    id: str
    type: str
    title: str
    description: str
    priority: str
    evidence: List[str] = []


class RecommendationOut(BaseModel):
    id: str
    title: str
    summary: str
    justification: str
    priority: str
    status: str
    expected_outcomes: List[str] = []
    next_steps: List[str] = []


class AnalyzeResponse(BaseModel):
    company_id: str
    company_name: Optional[str] = None
    industry: Optional[str] = None
    current_step: str
    kpis: List[KPIOut] = []
    segments: List[SegmentOut] = []
    insights: List[str] = []
    issues: List[IssueOut] = []
    playbooks: List[Dict[str, Any]] = []
    recommendations: List[RecommendationOut] = []
    explanation: Optional[Dict[str, Any]] = None
    errors: List[str] = []


class HealthResponse(BaseModel):
    status: str
    version: str = "0.1.0"
    service: str = "eleva"