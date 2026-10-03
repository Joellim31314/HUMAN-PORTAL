"""Archetype schedule templates -> resolved 7-slot schedules per day type."""
from __future__ import annotations

import numpy as np

from app.population.geography import WEST_END, jitter
from app.schemas import SLOTS, GeoPoint, ScheduleEntry

P = tuple[str, str]  # (place, activity)


def _choice(rng, options: list[tuple[float, P]]) -> P:
    w = np.array([o[0] for o in options], dtype=float)
    return options[int(rng.choice(len(options), p=w / w.sum()))][1]


def _leisure_evening(rng, gym: bool) -> P:
    opts = [(0.5, ("home", "relaxing")), (0.2, ("central", "socialising")), (0.15, ("local", "socialising")),
            (0.15, ("local", "shopping"))]
    if gym:
        opts.append((0.25, ("gym", "exercising")))
    return _choice(rng, opts)


def _weekday_office(rng, gym: bool) -> list[P]:
    lunch = _choice(rng, [(0.65, ("work", "working")), (0.35, ("local", "shopping"))])
    eve_home = _choice(rng, [(0.8, ("transit", "commuting")), (0.2, ("local", "shopping"))])
    late = _leisure_evening(rng, gym) if rng.random() < 0.8 else ("home", "relaxing")
    if rng.random() < 0.2:
        late = _choice(rng, [(1, ("central", "socialising")), (1, ("local", "socialising")), (1, ("home", "relaxing"))])
    early = ("gym", "exercising") if gym and rng.random() < 0.2 else ("home", "relaxing")
    return [early, ("transit", "commuting"), lunch, ("work", "working"), eve_home, late, ("home", "sleeping")]


def _weekday_shift(rng, gym: bool) -> list[P]:
    r = rng.random()
    if r < 0.40:  # early shift
        return [("transit", "commuting"), ("work", "working"), ("work", "working"), ("work", "working"),
                ("transit", "commuting"), _choice(rng, [(2, ("home", "relaxing")), (1, ("local", "socialising"))]),
                ("home", "sleeping")]
    if r < 0.75:  # late shift
        return [("home", "sleeping"), ("home", "relaxing"), _choice(rng, [(1, ("local", "shopping")), (1, ("home", "relaxing"))]),
                ("transit", "commuting"), ("work", "working"), ("work", "working"), ("transit", "commuting")]
    # night shift
    return [("home", "sleeping"), ("home", "sleeping"), ("home", "sleeping"),
            _choice(rng, [(1, ("local", "shopping")), (1, ("home", "relaxing"))]),
            ("transit", "commuting"), ("work", "working"), ("work", "working")]


def _weekday_student(rng, gym: bool) -> list[P]:
    late = _choice(rng, [(0.35, ("central", "socialising")), (0.25, ("local", "socialising")), (0.4, ("home", "relaxing"))])
    eve = _choice(rng, [(0.7, ("transit", "commuting")), (0.3, ("local", "shopping"))])
    midday = ("campus", "studying") if rng.random() < 0.85 else ("local", "shopping")
    aft = ("campus", "studying") if rng.random() < 0.8 else _choice(rng, [(1, ("gym", "exercising")), (1, ("local", "socialising"))])
    morning = ("transit", "commuting") if rng.random() < 0.9 else ("home", "relaxing")
    return [("home", "relaxing"), morning, midday, aft, eve, late, ("home", "sleeping")]


def _weekday_wfh(rng, gym: bool) -> list[P]:
    lunch = _choice(rng, [(0.6, ("home", "working")), (0.4, ("local", "shopping"))])
    eve = _choice(rng, [(0.35, ("local", "exercising")), (0.2, ("local", "shopping")), (0.45, ("home", "relaxing"))])
    if gym and rng.random() < 0.3:
        eve = ("gym", "exercising")
    late = _choice(rng, [(0.7, ("home", "relaxing")), (0.15, ("local", "socialising")), (0.15, ("central", "socialising"))])
    return [("home", "relaxing"), ("home", "working"), lunch, ("home", "working"), eve, late, ("home", "sleeping")]


def _weekday_retired(rng, gym: bool) -> list[P]:
    morning = _choice(rng, [(0.5, ("local", "shopping")), (0.5, ("home", "relaxing"))])
    midday = _choice(rng, [(0.45, ("local", "relaxing")), (0.25, ("local", "shopping")), (0.3, ("home", "relaxing"))])
    aft = _choice(rng, [(0.35, ("local", "socialising")), (0.65, ("home", "relaxing"))])
    morn_gym = ("gym", "exercising") if gym and rng.random() < 0.4 else morning
    return [("home", "relaxing"), morn_gym, midday, aft, ("home", "relaxing"), ("home", "relaxing"), ("home", "sleeping")]


def _weekday_carer(rng, gym: bool) -> list[P]:
    midday = _choice(rng, [(0.5, ("home", "caring")), (0.3, ("local", "shopping")), (0.2, ("local", "caring"))])
    return [("home", "caring"), ("local", "caring"), midday, ("local", "caring"),
            ("home", "caring"), ("home", "relaxing"), ("home", "sleeping")]


def _weekend(rng, gym: bool) -> list[P]:
    morning = ("gym", "exercising") if gym and rng.random() < 0.3 else ("home", "relaxing")
    midday = _choice(rng, [(0.4, ("local", "shopping")), (0.25, ("central", "socialising")), (0.35, ("home", "relaxing"))])
    aft = _choice(rng, [(0.3, ("central", "socialising")), (0.3, ("local", "socialising")), (0.2, ("local", "shopping")), (0.2, ("home", "relaxing"))])
    late = _choice(rng, [(0.35, ("central", "socialising")), (0.2, ("local", "socialising")), (0.45, ("home", "relaxing"))])
    return [("home", "sleeping"), morning, midday, aft, ("home", "relaxing"), late, ("home", "sleeping")]


_WEEKDAY = {
    "office_commuter": _weekday_office, "shift_worker": _weekday_shift, "student": _weekday_student,
    "wfh": _weekday_wfh, "retired": _weekday_retired, "carer": _weekday_carer,
}


def _template(rng, archetype: str, day: str, gym: bool) -> list[P]:
    if day == "weekday":
        return _WEEKDAY[archetype](rng, gym)
    if archetype == "shift_worker" and rng.random() < 0.4:
        return _weekday_shift(rng, gym)
    if archetype == "carer":
        return [("home", "caring"), ("home", "caring"), _choice(rng, [(1, ("local", "shopping")), (1, ("local", "caring"))]),
                ("local", "caring"), ("home", "caring"), ("home", "relaxing"), ("home", "sleeping")]
    return _weekend(rng, gym)


def build_schedule(rng, archetype: str, home, work, gym, jobless: bool = False) -> dict[str, list[ScheduleEntry]]:
    """home/work/gym are (lat, lon) or None. Returns {'weekday': [...7], 'weekend': [...7]}."""
    out: dict[str, list[ScheduleEntry]] = {}
    for day in ("weekday", "weekend"):
        tpl = _template(rng, archetype, day, gym is not None)
        entries = []
        for slot, (place, act) in zip(SLOTS, tpl):
            if jobless and act == "working":
                act = "relaxing"
            if place in ("work", "campus") and work is None:
                place, act = "home", ("working" if act == "working" else "relaxing")
            if place == "transit" and work is None:
                place, act = "local", "relaxing"
            if place == "gym" and gym is None:
                place, act = "local", "exercising"
            if place == "home":
                pt = home
            elif place in ("work", "campus"):
                pt = work
            elif place == "transit":
                pt = ((home[0] + work[0]) / 2, (home[1] + work[1]) / 2)
            elif place == "local":
                pt = jitter(rng, home[0], home[1], 300)
            elif place == "central":
                pt = jitter(rng, WEST_END[0], WEST_END[1], 500)
            else:  # gym
                pt = gym
            entries.append(ScheduleEntry(slot=slot, place=place, activity=act,
                                         location=GeoPoint(lat=round(pt[0], 5), lon=round(pt[1], 5))))
        out[day] = entries
    return out
