"""M5 deterministic recommendation + ROI engines (RECOMMENDATION_RULES,
ROI_CALCULATION, ADR-007). LLMs never participate here."""

import math
from dataclasses import dataclass

EPSILON = 1e-9
SCENARIO_RATES = (0.2, 0.4, 0.6)


@dataclass(frozen=True)
class AdviceFacts:
    manual_steps: int
    total_steps: int
    integration_statuses: tuple[str, ...]
    has_approvals: bool
    error_rate: float | None
    sensitivity: str | None
    confidence: float  # assessment_confidence 0-100
    frequency_per_week: float | None
    minutes_per_occurrence: float | None
    realistic_automation_rate: float | None
    exception_rate: float | None
    loaded_hourly_cost: float | None
    currency: str | None
    monthly_operating_cost: float | None
    implementation_cost: float | None


def recommend(facts: AdviceFacts) -> dict[str, object] | None:
    statuses = set(facts.integration_statuses)
    confidence_band = (
        "high" if facts.confidence >= 66 else "medium" if facts.confidence >= 33 else "low"
    )
    risk_heavy = facts.sensitivity in {"high", "restricted"}
    if facts.total_steps == 0 or facts.manual_steps == 0:
        return None
    if risk_heavy and confidence_band == "low":
        return {
            "patterns": ["discovery_prototype"],
            "rationale": (
                "Sensitivity is high/restricted while reviewed evidence is thin; "
                "the rules prefer a bounded discovery prototype over committing to automation."
            ),
            "prerequisites": ["confirm data classification and controls with the process owner"],
            "risks": ["unattended automation on sensitive data could breach policy"],
            "human_control": "mandatory human approval for every decision the prototype touches",
            "rejected_alternatives": [
                {"pattern": "api_integration", "why": "no integration evidence yet (BR-009)"},
                {"pattern": "rpa", "why": "brittle automation on sensitive systems is unjustified"},
            ],
            "confidence": confidence_band,
        }
    patterns: list[str] = []
    rationale: list[str] = []
    prerequisites: list[str] = []
    risks: list[str] = []
    rejected: list[dict[str, str]] = []
    if "evidence_of_api" in statuses:
        patterns.append("api_integration")
        rationale.append(
            "reviewed integration evidence shows a supported interface, "
            "the preferred durable path (ADR-007)"
        )
        prerequisites.append("confirm rate limits and data contracts with the system owner")
    if facts.has_approvals or (facts.error_rate or 0) > 0:
        patterns.append("workflow_automation")
        rationale.append(
            "approval routing and validation gates fit workflow engines with audit trails"
        )
    if patterns == []:
        if "no_practical_api" in statuses:
            patterns.append("rpa")
            rationale.append("a necessary system has reviewed evidence of no practical API")
            risks.append(
                "RPA is brittle to UI changes; plan exception monitoring and credential handling"
            )
            prerequisites.append("stabilize the target screens and record exception paths")
        elif "unknown" in statuses:
            patterns.append("discovery_prototype")
            rationale.append(
                "system integration availability is still unknown for every involved system"
            )
            prerequisites.append("run an integration discovery pass with the system owners")
        else:
            patterns.append("workflow_automation")
            rationale.append("manual steps remain without documented system interfaces")
    if risk_heavy:
        human_control = (
            "keep human approval on decisions touching sensitive or restricted data; "
            "automate only the validated happy path with an exception queue"
        )
        risks.append("compliance exposure if exceptions are auto-processed")
    else:
        human_control = "human review for exceptions; unattended processing of validated steps only"
    if facts.error_rate is not None and facts.error_rate > 0.05:
        patterns.append("business_rules")
        rationale.append(
            "preventable rework indicates deterministic validation rules can catch errors early"
        )
    rejected.append(
        {
            "pattern": "llm_autonomous_decision",
            "why": "models may explain but must not decide policy (ADR-003)",
        }
    )
    if "rpa" in patterns and "api_integration" in patterns:
        rejected.append(
            {
                "pattern": "rpa",
                "why": "a stable interface exists; integration is less brittle than UI robots",
            }
        )
    unique_patterns = list(dict.fromkeys(patterns))
    return {
        "patterns": unique_patterns,
        "rationale": "; ".join(rationale),
        "prerequisites": prerequisites
        or ["confirm frequency and durations with the process owner"],
        "risks": risks or ["reanalysis needed when any input system changes"],
        "human_control": human_control,
        "rejected_alternatives": rejected,
        "confidence": confidence_band,
    }


def time_scenarios(facts: AdviceFacts) -> dict[str, object]:
    """Partial time savings with explicit scenario assumptions (BR-005)."""
    occurrences_month = (
        facts.frequency_per_week * 52 / 12 if facts.frequency_per_week is not None else None
    )
    base: dict[str, object] = {
        "occurrences_per_month": round(occurrences_month, 2) if occurrences_month else None,
        "minutes_each": facts.minutes_per_occurrence,
        "currency": facts.currency,
    }
    if occurrences_month is None or facts.minutes_per_occurrence is None:
        return {"available": False, "inputs": base, "missing": ["frequency", "duration"]}
    monthly_hours = occurrences_month * facts.minutes_per_occurrence / 60.0
    rates = (
        [facts.realistic_automation_rate]
        if facts.realistic_automation_rate is not None
        else list(SCENARIO_RATES)
    )
    exception = facts.exception_rate if facts.exception_rate is not None else 0.0
    scenarios = []
    for rate in rates:
        net = monthly_hours * rate * (1 - exception)
        scenario: dict[str, object] = {
            "automation_rate": rate,
            "exception_rate": exception,
            "net_hours_saved_month": round(net, 2),
            "stated_by": "user fact"
            if facts.realistic_automation_rate is not None
            else "scenario assumption",
        }
        if facts.loaded_hourly_cost is not None and facts.currency is not None:
            scenario["monthly_labor_benefit"] = round(net * facts.loaded_hourly_cost, 2)
        scenarios.append(scenario)
    monetary = (
        facts.loaded_hourly_cost is not None
        and facts.currency is not None
        and facts.implementation_cost is not None
    )
    result: dict[str, object] = {
        "available": True,
        "inputs": base | {"exception_rate": exception},
        "scenarios": scenarios,
        "assumptions_note": ("labor savings are freed capacity, not automatic headcount reduction"),
    }
    if monetary and facts.implementation_cost is not None:
        monthly_benefit = 0.0
        for scenario in scenarios:
            value = scenario.get("monthly_labor_benefit")
            if isinstance(value, (int, float)) and value > monthly_benefit:
                monthly_benefit = float(value)
        operating = facts.monthly_operating_cost or 0.0
        net_month = monthly_benefit - operating
        annual_net = 12 * net_month
        result["monetary"] = {
            "annual_net_benefit": round(annual_net, 2),
            "roi_percent": round(
                (annual_net - facts.implementation_cost)
                / max(facts.implementation_cost, EPSILON)
                * 100,
                1,
            ),
            "payback_months": round(facts.implementation_cost / max(net_month, EPSILON), 1)
            if net_month > 0
            else None,
            "currency": facts.currency,
        }
        result["monetary_basis"] = "best scenario shown; confirm with the process owner"
    else:
        missing = []
        if facts.loaded_hourly_cost is None:
            missing.append("loaded_hourly_cost")
        if facts.implementation_cost is None:
            missing.append("implementation_cost")
        result["monetary"] = None
        result["monetary_missing"] = missing or ["cost evidence"]
    return result


def needs_money(facts: AdviceFacts) -> bool:
    return (
        facts.currency is not None
        and facts.loaded_hourly_cost is not None
        and math.isfinite(facts.loaded_hourly_cost)
    )
