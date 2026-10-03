"""ONS MSOA 2021 population-weighted centroids (cached in data/raw/msoa_centroids.json)."""
from __future__ import annotations

import json

import httpx

from app.config import RAW_DIR

URL = ("https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
       "MSOA_December_2021_EW_PWC_V2/FeatureServer/0/query")
CACHE = RAW_DIR / "msoa_centroids.json"


def fetch_centroids() -> dict[str, tuple[float, float]]:
    """Return {msoa_code: (lat, lon)} for all England+Wales MSOAs."""
    if CACHE.exists():
        return {k: tuple(v) for k, v in json.loads(CACHE.read_text()).items()}
    out: dict[str, tuple[float, float]] = {}
    offset = 0
    with httpx.Client(timeout=120, headers={"User-Agent": "human-portal-hackathon/0.1"}) as c:
        while True:
            params = {"where": "1=1", "outFields": "MSOA21CD", "returnGeometry": "true", "outSR": "4326",
                      "f": "json", "resultOffset": offset, "resultRecordCount": 2000,
                      "orderByFields": "MSOA21CD"}
            for attempt in range(2):
                try:
                    r = c.get(URL, params=params)
                    r.raise_for_status()
                    data = r.json()
                    break
                except Exception:
                    if attempt == 1:
                        raise
            feats = data.get("features", [])
            for f in feats:
                out[f["attributes"]["MSOA21CD"]] = (f["geometry"]["y"], f["geometry"]["x"])
            if not feats:
                break
            offset += len(feats)
            if not data.get("exceededTransferLimit") and len(feats) < 2000:
                break
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(out))
    return out


if __name__ == "__main__":
    print(len(fetch_centroids()))
