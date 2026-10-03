from app.schemas import ReasonCode

REASON_LABELS: dict[ReasonCode, str] = {
    ReasonCode.NO_STORE_NEARBY: "No stocking store anywhere along their week",
    ReasonCode.NOT_THERE_WHEN_NEEDED: "Stocked where they live, not where they are when they need it",
    ReasonCode.DIDNT_NOTICE: "Walked past the product but never noticed it",
    ReasonCode.NO_NEED: "Saw it, but never needed this kind of product at that moment",
    ReasonCode.TOO_EXPENSIVE: "Wanted it, but the price put them off",
    ReasonCode.BELIEF_CONFLICT: "Conflicts with their diet, faith or health beliefs",
    ReasonCode.LOYAL_TO_EXISTING: "Stuck with the brand they already buy",
    ReasonCode.BOUGHT: "Bought it",
}
