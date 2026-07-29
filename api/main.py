"""
Eleva FastAPI application.

Run from project root (venv activated):
    uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

Docs: http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from core.models import AnalysisRequest
from engine.decision_engine import DecisionEngine
from engine.explain import explain_recommendation
from api.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    HealthResponse,
    KPIOut,
    SegmentOut,
    IssueOut,
    RecommendationOut,
)
from config import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="Eleva API",
    description="AI Decision Agent for e-commerce marketing",
    version="0.1.0",
)

# CORS – open for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = DecisionEngine()


@app.get("/health", response_model=HealthResponse)
def health():
    """Health check for monitoring / load balancers."""
    return HealthResponse(status="ok")


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(body: AnalyzeRequest):
    """
    Run the full decision cycle (On Demand).
    Returns observations, issues, recommendations and an explanation
    of the first recommendation.
    """
    logger.info(f"API /analyze company_id={body.company_id}")

    request = AnalysisRequest(
        company_id=body.company_id,
        question=body.question,
        focus_areas=body.focus_areas,
        max_recommendations=body.max_recommendations,
    )

    try:
        state = engine.run(request)
    except Exception as e:
        logger.error(f"/analyze failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    if state.errors and not state.recommendations:
        # Hard failure (e.g. unknown company)
        raise HTTPException(
            status_code=400,
            detail={"errors": state.errors},
        )

    # Build response
    kpis = []
    segments = []
    insights = []
    if state.observation:
        kpis = [
            KPIOut(name=k.name, value=k.value, unit=k.unit)
            for k in state.observation.kpis
        ]
        segments = [
            SegmentOut(name=s.name, size=s.size, percentage=s.percentage)
            for s in state.observation.segments
        ]
        insights = list(state.observation.raw_insights)

    issues = [
        IssueOut(
            id=i.id,
            type=i.type.value,
            title=i.title,
            description=i.description,
            priority=i.priority.value,
            evidence=i.evidence,
        )
        for i in state.detected_issues
    ]

    recommendations = [
        RecommendationOut(
            id=r.id,
            title=r.title,
            summary=r.summary,
            justification=r.justification,
            priority=r.priority.value,
            status=r.status.value,
            expected_outcomes=r.expected_outcomes,
            next_steps=r.next_steps,
        )
        for r in state.recommendations
    ]

    explanation = None
    if state.recommendations:
        explanation = explain_recommendation(state)

    return AnalyzeResponse(
        company_id=body.company_id,
        company_name=state.company_context.name if state.company_context else None,
        industry=state.company_context.industry if state.company_context else None,
        current_step=state.current_step,
        kpis=kpis,
        segments=segments,
        insights=insights,
        issues=issues,
        playbooks=state.retrieved_playbooks,
        recommendations=recommendations,
        explanation=explanation,
        errors=state.errors,
    )