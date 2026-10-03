"""Shared data contract for the HUMAN PORTAL simulation backend.

Every module (population builder, simulation engine, LLM layer, API) codes
against these types. Change them deliberately: the frontend depends on them.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Time model: one simulated week = 7 days x 7 slots
# ---------------------------------------------------------------------------

SLOTS: list[str] = [
    "early_morning",  # 06-08
    "morning",        # 08-10 (commute peak)
    "midday",         # 10-14 (incl. lunch)
    "afternoon",      # 14-17
    "evening",        # 17-19 (commute home)
    "late_evening",   # 19-23
    "night",          # 23-06
]
DAYS: list[str] = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

Slot = Literal["early_morning", "morning", "midday", "afternoon", "evening", "late_evening", "night"]
DayType = Literal["weekday", "weekend"]
Place = Literal["home", "transit", "work", "campus", "local", "central", "gym"]
Activity = Literal[
    "sleeping", "commuting", "working", "studying", "exercising",
    "socialising", "relaxing", "shopping", "caring",
]
Archetype = Literal["office_commuter", "shift_worker", "student", "wfh", "retired", "carer"]
EconomicStatus = Literal["employed", "self_employed", "student", "retired", "unemployed", "carer"]
IncomeBand = Literal["low", "mid", "high"]
AgeBand = Literal["16-24", "25-34", "35-44", "45-54", "55-64", "65+"]
EthnicGroup = Literal["White", "Asian", "Black", "Mixed", "Other"]
MediaChannel = Literal["tiktok", "instagram", "youtube", "x", "facebook", "tv", "ooh", "radio", "podcast"]
DietFlag = Literal["halal", "kosher", "vegetarian", "vegan", "health_conscious", "low_sugar", "caffeine_avoider"]


class GeoPoint(BaseModel):
    lat: float
    lon: float


# ---------------------------------------------------------------------------
# Agents (built once by app/pipeline/build_population.py -> data/processed/agents.json)
# ---------------------------------------------------------------------------


class ScheduleEntry(BaseModel):
    slot: Slot
    place: Place
    activity: Activity
    location: GeoPoint  # resolved at build time; the engine only reads coordinates


class Traits(BaseModel):
    """All 0..1. Big Five plus shopping-relevant dispositions."""

    openness: float
    conscientiousness: float
    extraversion: float
    agreeableness: float
    neuroticism: float
    attention: float            # how likely to notice things on a shelf
    price_sensitivity: float
    health_consciousness: float
    brand_loyalty: float        # high = sticks with what they already buy
    novelty_seeking: float


class Agent(BaseModel):
    id: str                      # "a00001"
    name: str
    age: int
    age_band: AgeBand
    sex: Literal["female", "male"]
    ethnicity: EthnicGroup
    ethnicity_detail: str        # census sub-group, e.g. "Bangladeshi"
    religion: str                # census category, e.g. "Muslim", "No religion"
    economic_status: EconomicStatus
    occupation: Optional[str]    # census TS063 major group label, None if not working
    income_band: IncomeBand
    archetype: Archetype
    travel_mode: str             # e.g. "underground", "bus", "car", "bicycle", "on_foot", "wfh"
    msoa_code: str
    msoa_name: str
    borough: str
    home: GeoPoint
    work: Optional[GeoPoint]
    work_label: Optional[str]    # e.g. "Canary Wharf", "UCL", "local"
    traits: Traits
    media: dict[str, float]      # MediaChannel -> 0..1 daily exposure weight
    diet_flags: list[DietFlag]
    schedule: dict[DayType, list[ScheduleEntry]]  # 7 entries each, ordered as SLOTS
    bio: Optional[str] = None    # filled lazily by the LLM for interviewed agents


class AgentPoint(BaseModel):
    """Lightweight row for drawing the map."""

    id: str
    lat: float
    lon: float
    borough: str
    age_band: AgeBand
    sex: Literal["female", "male"]
    ethnicity: EthnicGroup
    archetype: Archetype
    income_band: IncomeBand


class Store(BaseModel):
    id: str                      # "osm-node-123"
    name: str
    brand: Optional[str]         # e.g. "Tesco Express", None for independents
    kind: Literal["convenience", "supermarket"]
    lat: float
    lon: float
    borough: Optional[str]


# ---------------------------------------------------------------------------
# Product input (from the frontend)
# ---------------------------------------------------------------------------

Category = Literal[
    "energy_drink", "soft_drink", "coffee_rtd", "snack", "healthy_snack",
    "confectionery", "ready_meal", "alcohol", "other",
]
Claim = Literal["vegan", "vegetarian", "halal", "kosher", "sugar_free", "low_calorie",
                "high_protein", "organic", "caffeinated", "alcoholic", "plant_based"]


class Stockists(BaseModel):
    chains: list[str] = Field(default_factory=list, description="Brand substrings to match, e.g. ['Tesco', 'Sainsbury']. Empty = all stores.")
    store_kinds: list[Literal["convenience", "supermarket"]] = Field(default_factory=lambda: ["convenience", "supermarket"])
    boroughs: list[str] = Field(default_factory=list, description="Empty = all of London.")
    coverage: float = Field(0.35, ge=0, le=1, description="Share of matching stores that actually stock it.")


class ProductInput(BaseModel):
    name: str
    category: Category
    description: str
    price_gbp: float = Field(gt=0)
    packaging_salience: int = Field(3, ge=1, le=5, description="1 = bland, 5 = loud/eye-catching")
    packaging_description: Optional[str] = None
    image_url: Optional[str] = None
    claims: list[Claim] = Field(default_factory=list)
    stockists: Stockists = Field(default_factory=Stockists)
    marketing_channels: list[MediaChannel] = Field(default_factory=list)
    marketing_intensity: float = Field(0.3, ge=0, le=1)
    target_audience: Optional[str] = None
    seed: int = 42


# ---------------------------------------------------------------------------
# Simulation output
# ---------------------------------------------------------------------------


class Outcome(str, Enum):
    never_exposed = "never_exposed"  # never near a stocking store
    not_noticed = "not_noticed"      # walked past, didn't register it
    no_need = "no_need"              # noticed, but never needed it at that moment
    rejected = "rejected"            # noticed + needed, but price/belief said no
    bought = "bought"


class ReasonCode(str, Enum):
    NO_STORE_NEARBY = "NO_STORE_NEARBY"
    NOT_THERE_WHEN_NEEDED = "NOT_THERE_WHEN_NEEDED"
    DIDNT_NOTICE = "DIDNT_NOTICE"
    NO_NEED = "NO_NEED"
    TOO_EXPENSIVE = "TOO_EXPENSIVE"
    BELIEF_CONFLICT = "BELIEF_CONFLICT"
    LOYAL_TO_EXISTING = "LOYAL_TO_EXISTING"
    BOUGHT = "BOUGHT"


class TraceEvent(BaseModel):
    day: str
    slot: Slot
    place: Place
    activity: Activity
    store_id: Optional[str] = None
    step: Literal["exposure", "notice", "need", "price", "belief", "loyalty", "purchase"]
    passed: bool
    detail: str


class AgentOutcome(BaseModel):
    agent_id: str
    lat: float
    lon: float
    outcome: Outcome
    reason: ReasonCode
    exposures: int           # slots spent near a stocking store
    noticed: bool
    purchases: int


class FunnelCounts(BaseModel):
    total: int
    exposed: int
    noticed: int
    needed: int      # noticed AND had a need moment while near it
    bought: int


class ReasonStat(BaseModel):
    code: ReasonCode
    label: str
    count: int
    pct: float


class SegmentStat(BaseModel):
    dimension: Literal["age_band", "sex", "ethnicity", "borough", "archetype", "income_band"]
    value: str
    total: int
    interested: int   # outcome in {rejected, bought}
    bought: int
    conversion: float  # bought / total
    top_reason: ReasonCode


class Interview(BaseModel):
    agent_id: str
    name: str
    persona: str         # one-line demographic summary
    outcome: Outcome
    reason: ReasonCode
    quote: str           # first-person explanation
    source: Literal["llm", "template"]


class ReportItem(BaseModel):
    title: str
    detail: str


class ActionItem(BaseModel):
    action: str
    rationale: str
    priority: Literal["high", "medium", "low"]


class Report(BaseModel):
    headline: str
    key_findings: list[str]
    rejection_reasons: list[ReportItem]
    interested_segments: list[ReportItem]
    action_items: list[ActionItem]
    source: Literal["llm", "template"]


class SimulationSummary(BaseModel):
    id: str
    status: Literal["queued", "running", "done", "failed"]
    product_name: str
    created_at: datetime


class SimulationResult(BaseModel):
    id: str
    status: Literal["queued", "running", "done", "failed"]
    progress: str = ""           # human-readable stage, e.g. "Interviewing agents"
    error: Optional[str] = None
    created_at: datetime
    product: ProductInput
    stores_stocking: int = 0
    funnel: Optional[FunnelCounts] = None
    reasons: list[ReasonStat] = Field(default_factory=list)
    segments: list[SegmentStat] = Field(default_factory=list)
    outcomes: list[AgentOutcome] = Field(default_factory=list)
    interviews: list[Interview] = Field(default_factory=list)
    report: Optional[Report] = None


class AgentTrace(BaseModel):
    agent: Agent
    outcome: AgentOutcome
    trace: list[TraceEvent]
    interview: Optional[Interview] = None
