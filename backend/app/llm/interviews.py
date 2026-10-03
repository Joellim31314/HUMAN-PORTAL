from __future__ import annotations

import asyncio
import json
import random
from collections import Counter, defaultdict
from typing import TYPE_CHECKING

from app.config import INTERVIEW_COUNT
from app.llm.client import chat_json
from app.llm.prompts import INTERVIEW_SYSTEM, persona_card, persona_line
from app.schemas import Agent, Interview, Outcome, ProductInput, ReasonCode

if TYPE_CHECKING:
    from app.simulation.engine import FunnelRun

_QUOTES = {
    ReasonCode.NO_STORE_NEARBY: "I didn't come across it at any shop along my usual route this week.",
    ReasonCode.NOT_THERE_WHEN_NEEDED: "When I needed something like this, I wasn't near a shop stocking it.",
    ReasonCode.DIDNT_NOTICE: "I went past it, but it never caught my eye on the shelf.",
    ReasonCode.NO_NEED: "I noticed it, but I didn't need that kind of product at the time.",
    ReasonCode.TOO_EXPENSIVE: "I wanted something like this, but the price was more than I wanted to spend.",
    ReasonCode.BELIEF_CONFLICT: "I considered it, but it didn't fit my diet, beliefs or health preferences.",
    ReasonCode.LOYAL_TO_EXISTING: "I considered it, but stuck with the brand I already buy.",
    ReasonCode.BOUGHT: "I noticed it when I needed something like this and bought it.",
}

_DAYS = {"mon": "Monday", "tue": "Tuesday", "wed": "Wednesday", "thu": "Thursday",
         "fri": "Friday", "sat": "Saturday", "sun": "Sunday"}
_SLOTS = {"early_morning": "early morning", "morning": "morning", "midday": "around lunch",
          "afternoon": "afternoon", "evening": "evening", "late_evening": "late evening",
          "night": "night"}
_ACTIVITIES = {"commuting": "on my way in", "working": "at work", "studying": "studying",
               "exercising": "at the gym", "socialising": "out with friends",
               "relaxing": "relaxing", "shopping": "out shopping", "caring": "looking after family",
               "sleeping": "at home"}


def _sample(run: FunnelRun, agents: dict[str, Agent], n: int, seed: int):
    rng = random.Random(seed)
    groups = defaultdict(list)
    for outcome in sorted(run.outcomes, key=lambda o: o.agent_id):
        if outcome.agent_id in agents:
            groups[(outcome.outcome, outcome.reason)].append(outcome)
    for members in groups.values():
        rng.shuffle(members)
    selected = []
    age_counts, ethnicity_counts = Counter(), Counter()

    def take(key):
        members = groups[key]
        index = min(range(len(members)), key=lambda i: (
            age_counts[agents[members[i].agent_id].age_band]
            + ethnicity_counts[agents[members[i].agent_id].ethnicity]))
        item = members.pop(index)
        selected.append(item)
        agent = agents[item.agent_id]
        age_counts[agent.age_band] += 1
        ethnicity_counts[agent.ethnicity] += 1

    # Cover every outcome/reason stratum when the requested sample permits it.
    keys = sorted(groups, key=lambda k: (k[0].value, k[1].value))
    rng.shuffle(keys)
    limit = min(max(0, n), sum(map(len, groups.values())))
    for key in keys:
        if len(selected) < limit:
            take(key)
    while len(selected) < limit:
        available = [key for key in keys if groups[key]]
        weights = [3 if key[0] in {Outcome.bought, Outcome.rejected} else 1 for key in available]
        take(rng.choices(available, weights=weights, k=1)[0])
    return selected


async def run_interviews(product: ProductInput, run: FunnelRun,
                         agents_by_id: dict[str, Agent], n: int = INTERVIEW_COUNT,
                         seed: int = 42) -> list[Interview]:
    async def interview(outcome):
        agent = agents_by_id[outcome.agent_id]
        trace = run.traces.get(agent.id, [])
        payload = {"persona": persona_card(agent), "product": product.model_dump(mode="json"),
                   "outcome": outcome.model_dump(mode="json"),
                   "trace": [event.model_dump(mode="json") for event in trace]}
        value = await chat_json(INTERVIEW_SYSTEM, json.dumps(payload))
        valid = (isinstance(value, dict) and isinstance(value.get("quote"), str)
                 and bool(value["quote"].strip()) and isinstance(value.get("bio"), str)
                 and bool(value["bio"].strip()))
        quote = value["quote"].strip() if valid else _QUOTES[outcome.reason]
        if not valid and trace:
            # State observed activity without implying a purchase or awareness.
            event = next((e for e in reversed(trace) if not e.passed), trace[-1])
            quote += (f" Think {_DAYS[event.day]} {_SLOTS[event.slot]}, "
                      f"when I was {_ACTIVITIES.get(event.activity, event.activity)}.")
        return Interview(agent_id=agent.id, name=agent.name, persona=persona_line(agent),
                         outcome=outcome.outcome, reason=outcome.reason, quote=quote,
                         source="llm" if valid else "template")

    return await asyncio.gather(*(interview(o) for o in _sample(run, agents_by_id, n, seed)))
