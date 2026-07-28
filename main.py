"""
Full test of the Eleva Decision Engine + Explainability.
Run with: python main.py
"""

from core.models import AnalysisRequest
from engine.decision_engine import DecisionEngine
from engine.explain import explain_recommendation, format_explanation_for_display


def main():
    print("=" * 70)
    print("ELEVA – Full Decision Engine Test + Explainability")
    print("=" * 70)

    request = AnalysisRequest(
        company_id="company_001",
        question="Analyse la situation actuelle et propose les actions prioritaires.",
        focus_areas=["cart_abandonment", "churn"],
        max_recommendations=3,
    )

    engine = DecisionEngine()
    state = engine.run(request)

    # ----- Context -----
    print("\n--- Company Context ---")
    if state.company_context:
        print(f"Name     : {state.company_context.name}")
        print(f"Industry : {state.company_context.industry}")
        print(f"Focus    : {state.company_context.current_focus}")

    # ----- Observation (summary) -----
    print("\n--- Observation (summary) ---")
    if state.observation:
        print(f"KPIs     : {len(state.observation.kpis)}")
        print(f"Segments : {len(state.observation.segments)}")
        print(f"Insights : {len(state.observation.raw_insights)}")

    # ----- Detected Issues -----
    print("\n--- Detected Issues ---")
    for issue in state.detected_issues:
        print(f"  [{issue.priority.value.upper()}] {issue.type.value}: {issue.title}")

    # ----- Retrieved Playbooks -----
    print("\n--- Retrieved Playbooks ---")
    for pb in state.retrieved_playbooks:
        print(f"  • {pb['technique']}  (for: {pb['issue_title']})")

    # ----- Final Recommendations -----
    print("\n--- Final Recommendations ---")
    if state.recommendations:
        for rec in state.recommendations:
            print(f"\n[{rec.priority.value.upper()}] {rec.title}")
            print(f"  id            : {rec.id}")
            print(f"  Summary       : {rec.summary}")
            print(f"  Justification : {rec.justification}")
            print(f"  Status        : {rec.status.value}")
    else:
        print("No recommendations produced.")

    # ----- Explain first recommendation -----
    if state.recommendations:
        print("\n")
        explanation = explain_recommendation(state)  # first one
        print(format_explanation_for_display(explanation))

    if state.errors:
        print("\n--- Errors ---")
        for err in state.errors:
            print(f"  ✗ {err}")

    print(f"\nCurrent step: {state.current_step}")


if __name__ == "__main__":
    main()