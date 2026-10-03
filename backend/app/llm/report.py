import json

from app.llm.client import chat_json
from app.llm.prompts import REPORT_SYSTEM
from app.schemas import ActionItem, ReasonCode, Report, ReportItem

_ACTIONS = {
    ReasonCode.NOT_THERE_WHEN_NEEDED: "Stock near stations, workplaces and campuses for commute and lunch occasions",
    ReasonCode.DIDNT_NOTICE: "Test bolder packaging, eye-level placement and targeted marketing",
    ReasonCode.TOO_EXPENSIVE: "Test a lower price point or introductory promotion",
    ReasonCode.BELIEF_CONFLICT: "Review formulation and substantiate relevant diet and health claims",
    ReasonCode.NO_STORE_NEARBY: "Expand distribution along shoppers' regular routes",
    ReasonCode.LOYAL_TO_EXISTING: "Offer trial promotions and sampling to encourage switching",
    ReasonCode.NO_NEED: "Reposition the product around a clearer use occasion",
}


def _label(reason):
    # Keep the LLM layer importable while the engine's modules are being built.
    try:
        from app.simulation.reasons import REASON_LABELS
        return REASON_LABELS.get(reason.code, reason.label)
    except ImportError:
        return reason.label


async def build_report(product, run, interviews) -> Report:
    eligible = [s for s in run.segments if s.total >= 20]
    ranked = sorted(eligible, key=lambda s: (-s.conversion, -s.total, s.dimension, s.value))
    reasons = sorted((r for r in run.reasons if r.code != ReasonCode.BOUGHT and r.count > 0),
                     key=lambda r: (-r.count, r.code.value))
    payload = {"product": product.model_dump(mode="json"), "funnel": run.funnel.model_dump(),
               "reasons": [r.model_dump(mode="json") for r in run.reasons],
               "top_segments": [s.model_dump(mode="json") for s in ranked[:3]],
               "bottom_segments": [s.model_dump(mode="json") for s in ranked[-3:]],
               "interviews": [i.model_dump(mode="json") for i in interviews]}
    value = await chat_json(REPORT_SYSTEM, json.dumps(payload), temperature=.4, max_tokens=1800)
    if value is not None:
        try:
            report = Report.model_validate({**value, "source": "llm"})
            if (report.headline.strip() and 3 <= len(report.key_findings) <= 5
                    and report.action_items and all(f.strip() for f in report.key_findings)):
                return report
        except (ValueError, TypeError):
            pass
    funnel = run.funnel
    conversion = funnel.bought / funnel.total if funnel.total else 0
    findings = [f"{funnel.bought} of {funnel.total} simulated Londoners bought {product.name} ({conversion:.1%}).",
                f"{funnel.exposed} were exposed; {funnel.noticed} noticed it; {funnel.needed} had a need while near it.",
                f"{len(run.stores_stocking)} stores stocked it at £{product.price_gbp:.2f}; test the largest funnel barriers before expanding."]
    if reasons:
        findings.append(f"Largest barrier: {_label(reasons[0])}, affecting {reasons[0].count} people ({reasons[0].pct:.1f}%).")
    if ranked:
        findings.append(f"Prioritise a pilot with {ranked[0].dimension.replace('_', ' ')}: {ranked[0].value} ({ranked[0].conversion:.1%} conversion).")
    actions = [ActionItem(action=_ACTIONS[r.code],
                          rationale=f"{_label(r)} affected {r.count} people; compare conversion in a controlled pilot.",
                          priority="high" if i == 0 else "medium")
               for i, r in enumerate(reasons[:3]) if r.code in _ACTIONS]
    if not actions:
        actions = [ActionItem(action="Run a small retailer pilot before scaling distribution",
                              rationale="Validate simulated conversion with observed sales and shopper feedback.", priority="medium")]
    return Report(headline=f"{product.name}: {conversion:.1%} simulated weekly conversion",
                  key_findings=findings,
                  rejection_reasons=[ReportItem(title=_label(r), detail=f"{r.count} people ({r.pct:.1f}% of the population).") for r in reasons[:3]],
                  interested_segments=[ReportItem(title=f"{s.dimension.replace('_', ' ')}: {s.value}",
                                                  detail=f"{s.bought}/{s.total} bought ({s.conversion:.1%}); {s.interested} considered buying. Use a targeted pilot to validate demand.") for s in ranked[:3]],
                  action_items=actions, source="template")
