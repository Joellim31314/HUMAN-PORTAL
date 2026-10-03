"""OSM Overpass: shops, gyms, universities for Greater London (cached in data/raw)."""
from __future__ import annotations

import json
import time

import httpx

from app.config import RAW_DIR

URLS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.private.coffee/api/interpreter"]
BBOX = "(51.28,-0.51,51.69,0.33)"
QUERIES = {
    "shops": f'[out:json][timeout:120];(node["shop"~"^(convenience|supermarket)$"]{BBOX};way["shop"~"^(convenience|supermarket)$"]{BBOX};);out center tags;',
    "gyms": f'[out:json][timeout:120];(node["leisure"="fitness_centre"]{BBOX};way["leisure"="fitness_centre"]{BBOX};);out center tags;',
    "unis": f'[out:json][timeout:120];(node["amenity"="university"]{BBOX};way["amenity"="university"]{BBOX};);out center tags;',
}


def fetch_pois(kind: str) -> list[dict]:
    cache = RAW_DIR / f"osm_{kind}.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))["elements"]
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    last = None
    for attempt in range(6):
        try:
            r = httpx.post(URLS[attempt % len(URLS)], data={"data": QUERIES[kind]}, timeout=100,
                           headers={"User-Agent": "human-portal-hackathon/0.1"})
            r.raise_for_status()
            data = r.json()
            cache.write_text(json.dumps(data), encoding="utf-8")
            return data["elements"]
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(10)
    raise RuntimeError(f"Overpass {kind} failed: {last}")


def element_point(e: dict) -> tuple[float, float] | None:
    if "lat" in e:
        return e["lat"], e["lon"]
    c = e.get("center")
    return (c["lat"], c["lon"]) if c else None


if __name__ == "__main__":
    for k in QUERIES:
        print(k, len(fetch_pois(k)))
        time.sleep(3)
