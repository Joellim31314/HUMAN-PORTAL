"""Home / work placement and spatial helpers."""
from __future__ import annotations

import math

import numpy as np

# (name, lat, lon, weight)
HUBS = [
    ("City of London", 51.5155, -0.0922, 1.6),
    ("West End", 51.5130, -0.1380, 1.6),
    ("Canary Wharf", 51.5054, -0.0235, 1.0),
    ("King's Cross", 51.5308, -0.1238, 0.8),
    ("Shoreditch", 51.5250, -0.0780, 0.6),
    ("Southwark / London Bridge", 51.5045, -0.0865, 0.7),
    ("Stratford", 51.5416, -0.0033, 0.5),
    ("Croydon", 51.3762, -0.0982, 0.4),
    ("Hammersmith", 51.4927, -0.2240, 0.4),
    ("Paddington", 51.5154, -0.1755, 0.4),
    ("Heathrow", 51.4700, -0.4543, 0.5),
    ("Kensington", 51.4990, -0.1938, 0.3),
]
WEST_END = (51.5136, -0.1365)
LOCAL_WEIGHT = 0.35


def haversine_m(lat1, lon1, lat2, lon2):
    """Vectorised-friendly haversine in metres."""
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi = p2 - p1
    dl = np.radians(lon2) - np.radians(lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * 6371000 * np.arcsin(np.sqrt(a))


def jitter(rng: np.random.Generator, lat: float, lon: float, sd_m: float) -> tuple[float, float]:
    dn, de = rng.normal(0, sd_m, 2)
    return (lat + dn / 111320.0, lon + de / (111320.0 * math.cos(math.radians(lat))))


def home_point(rng, centroid: tuple[float, float]) -> tuple[float, float]:
    return jitter(rng, centroid[0], centroid[1], 250)


def pick_work(rng, home: tuple[float, float], archetype: str, travel_mode: str) -> tuple[tuple[float, float], str]:
    """Return (point, label) for an office_commuter / shift_worker."""
    local_w = LOCAL_WEIGHT * (1.6 if archetype == "shift_worker" else 1.0)
    if travel_mode in ("on_foot", "bicycle"):
        local_w = 5.0
    weights = [local_w]
    for _, lat, lon, w in HUBS:
        d = float(haversine_m(home[0], home[1], lat, lon)) / 1000
        weights.append(w * math.exp(-d / 12.0))
    p = np.array(weights) / sum(weights)
    i = int(rng.choice(len(p), p=p))
    if i == 0:
        r = rng.uniform(0.3, 2.0) * 1000
        ang = rng.uniform(0, 2 * math.pi)
        lat = home[0] + r * math.sin(ang) / 111320.0
        lon = home[1] + r * math.cos(ang) / (111320.0 * math.cos(math.radians(home[0])))
        return (lat, lon), "local"
    name, lat, lon, _ = HUBS[i - 1]
    return jitter(rng, lat, lon, 300), name


def pick_campus(rng, home: tuple[float, float], campuses: list[dict]):
    """campuses: [{'name', 'points': [(lat, lon), ...]}]. Weighted by size and distance."""
    if not campuses:
        return None
    ws, nearest = [], []
    for c in campuses:
        pts = np.array(c["points"])
        d = haversine_m(home[0], home[1], pts[:, 0], pts[:, 1])
        j = int(np.argmin(d))
        nearest.append((float(pts[j, 0]), float(pts[j, 1])))
        dk = float(d[j]) / 1000
        ws.append(len(pts) ** 0.5 * math.exp(-dk / 6.0) * (3.0 if dk < 10 else 1.0))
    p = np.array(ws) / sum(ws)
    i = int(rng.choice(len(p), p=p))
    return jitter(rng, *nearest[i], 60), campuses[i]["name"]


def nearest_point(home, pts, max_m: float = 3000):
    if pts is None or len(pts) == 0:
        return None
    d = haversine_m(home[0], home[1], pts[:, 0], pts[:, 1])
    j = int(np.argmin(d))
    return (float(pts[j, 0]), float(pts[j, 1])) if d[j] <= max_m else None
