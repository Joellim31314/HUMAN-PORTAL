"""Traits, media exposure and dietary flags."""
from __future__ import annotations

import numpy as np

from app.schemas import Traits

MEDIA_CHANNELS = ["tiktok", "instagram", "youtube", "x", "facebook", "tv", "ooh", "radio", "podcast"]
_AGES = [16, 25, 35, 45, 55, 65, 80]
_MEDIA_ANCHORS = {
    "tiktok": [0.85, 0.65, 0.35, 0.15, 0.08, 0.05, 0.03],
    "instagram": [0.85, 0.8, 0.55, 0.35, 0.2, 0.1, 0.05],
    "youtube": [0.85, 0.75, 0.65, 0.55, 0.5, 0.4, 0.3],
    "x": [0.3, 0.4, 0.35, 0.25, 0.2, 0.12, 0.08],
    "facebook": [0.2, 0.4, 0.55, 0.65, 0.65, 0.55, 0.45],
    "tv": [0.3, 0.35, 0.5, 0.65, 0.8, 0.9, 0.9],
    "radio": [0.2, 0.3, 0.4, 0.5, 0.55, 0.6, 0.6],
    "podcast": [0.3, 0.5, 0.5, 0.3, 0.2, 0.12, 0.08],
}


def _clip(x: float) -> float:
    return float(min(1.0, max(0.0, x)))


def make_traits(rng: np.random.Generator, age: int, income: str) -> Traits:
    def n(mu=0.5, sd=0.15) -> float:
        return _clip(rng.normal(mu, sd))

    youth = float(np.interp(age, [16, 30, 50, 80], [1.0, 0.7, 0.3, 0.0]))
    income_pen = {"low": 0.2, "mid": 0.0, "high": -0.2}[income]
    return Traits(
        openness=round(n(), 3), conscientiousness=round(n(), 3), extraversion=round(n(), 3),
        agreeableness=round(n(), 3), neuroticism=round(n(), 3),
        attention=round(n(0.5, 0.15), 3),
        price_sensitivity=round(n(0.5 + income_pen, 0.15), 3),
        health_consciousness=round(n(0.5, 0.18), 3),
        brand_loyalty=round(n(0.3 + 0.4 * (1 - youth), 0.15), 3),
        novelty_seeking=round(n(0.3 + 0.4 * youth, 0.15), 3),
    )


def make_media(rng: np.random.Generator, age: int, commuter: bool) -> dict[str, float]:
    out = {}
    for ch, anchors in _MEDIA_ANCHORS.items():
        out[ch] = round(_clip(float(np.interp(age, _AGES, anchors)) + rng.normal(0, 0.1)), 3)
    out["ooh"] = round(_clip(0.3 + (0.35 if commuter else 0.0) + rng.normal(0, 0.1)), 3)
    return {ch: out[ch] for ch in MEDIA_CHANNELS}


def make_diet(rng: np.random.Generator, age: int, religion: str, health: float) -> list[str]:
    young = age < 35
    flags: list[str] = []
    if religion == "Muslim" and rng.random() < 0.85:
        flags.append("halal")
    if religion == "Jewish" and rng.random() < 0.30:
        flags.append("kosher")
    veg_p = 0.40 if religion == "Hindu" else (0.09 if young else 0.05)
    if rng.random() < (0.05 if young else 0.02):
        flags += ["vegan", "vegetarian"]
    elif rng.random() < veg_p:
        flags.append("vegetarian")
    if health > 0.7:
        flags.append("health_conscious")
    if rng.random() < 0.10:
        flags.append("low_sugar")
    if rng.random() < 0.08:
        flags.append("caffeine_avoider")
    return flags
