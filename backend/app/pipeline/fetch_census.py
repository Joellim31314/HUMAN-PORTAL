"""Download + load Nomis Census 2021 MSOA tables (cached in data/raw)."""
from __future__ import annotations

import zipfile

import httpx
import pandas as pd

from app.config import RAW_DIR

TABLES = ["ts007a", "ts008", "ts021", "ts030", "ts063", "ts061", "ts066"]
URL = "https://www.nomisweb.co.uk/output/census/2021/census2021-{t}.zip"

LONDON_BOROUGHS = [
    "City of London", "Barking and Dagenham", "Barnet", "Bexley", "Brent", "Bromley", "Camden", "Croydon",
    "Ealing", "Enfield", "Greenwich", "Hackney", "Hammersmith and Fulham", "Haringey", "Harrow", "Havering",
    "Hillingdon", "Hounslow", "Islington", "Kensington and Chelsea", "Kingston upon Thames", "Lambeth",
    "Lewisham", "Merton", "Newham", "Redbridge", "Richmond upon Thames", "Southwark", "Sutton",
    "Tower Hamlets", "Waltham Forest", "Wandsworth", "Westminster",
]


def borough_of(msoa_name: str) -> str:
    return msoa_name.rsplit(" ", 1)[0]


def download(table: str) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"{table}.zip"
    if path.exists() and path.stat().st_size > 1000:
        return
    for attempt in range(2):
        try:
            with httpx.Client(follow_redirects=True, timeout=180) as c:
                r = c.get(URL.format(t=table))
                r.raise_for_status()
                path.write_bytes(r.content)
                return
        except Exception:
            if attempt == 1:
                raise


def load_table(table: str) -> pd.DataFrame:
    """London-only MSOA rows, indexed by MSOA code, with 'msoa_name' and 'borough' columns."""
    download(table)
    with zipfile.ZipFile(RAW_DIR / f"{table}.zip") as z:
        name = [n for n in z.namelist() if n.endswith("-msoa.csv")][0]
        df = pd.read_csv(z.open(name))
    df = df.rename(columns={"geography": "msoa_name", "geography code": "msoa_code"})
    df["borough"] = df["msoa_name"].map(borough_of)
    df = df[df["borough"].isin(LONDON_BOROUGHS)].drop(columns=["date"]).set_index("msoa_code")
    return df


def fetch_all() -> dict[str, pd.DataFrame]:
    return {t: load_table(t) for t in TABLES}


if __name__ == "__main__":
    for t, d in fetch_all().items():
        print(t, d.shape)
