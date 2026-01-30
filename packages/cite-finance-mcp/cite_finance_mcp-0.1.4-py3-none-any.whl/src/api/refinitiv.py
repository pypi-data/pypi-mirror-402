"""
Refinitiv analytics endpoints (offline, precomputed factors/distress).

Serves data from a local analytics pack directory (parquet/CSV/JSON) produced
by the Refinitiv feature pipeline. Override the base path with
REFINITIV_ANALYTICS_PATH env var if needed.
"""
from pathlib import Path
from typing import Dict, List

import pandas as pd
from fastapi import APIRouter, HTTPException

router = APIRouter()

# Default to sibling project data if present; override via env var.
DEFAULT_BASE = (
    Path(__file__).resolve().parents[2]
    / "Molina-Optiplex"
    / "Sharpe-Renaissance"
    / "data_lake"
    / "analytics_pack"
)


def _analytics_base() -> Path:
    import os

    env_path = os.getenv("REFINITIV_ANALYTICS_PATH")
    if env_path:
        return Path(env_path)
    return DEFAULT_BASE


def _list_tickers(base: Path) -> List[str]:
    tickers = []
    for pq in base.glob("factors_*.parquet"):
        t = pq.stem.replace("factors_", "").replace("_", ".")
        tickers.append(t)
    return sorted(set(tickers))


def _latest_factors(base: Path, ticker: str) -> Dict:
    path = next(base.glob(f"factors_{ticker.replace('.', '_')}*.parquet"), None)
    if not path or not path.exists():
        raise FileNotFoundError
    df = pd.read_parquet(path)
    latest = df[df.notna().any(axis=1)].tail(1)
    if latest.empty:
        return {}
    return latest.to_dict(orient="records")[0]


def _distress(base: Path, ticker: str) -> Dict:
    path = base / "summary" / "distress_scores.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    row = df[df["ticker"] == ticker]
    if row.empty:
        return {}
    return {"distress_score": float(row.iloc[0]["distress_score"])}


@router.get("/refinitiv/tickers")
def list_tickers():
    base = _analytics_base()
    if not base.exists():
        raise HTTPException(status_code=404, detail="Analytics pack not found")
    return {"tickers": _list_tickers(base)}


@router.get("/refinitiv/factors/{ticker}")
def get_factors(ticker: str):
    base = _analytics_base()
    if not base.exists():
        raise HTTPException(status_code=404, detail="Analytics pack not found")
    try:
        factors = _latest_factors(base, ticker)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Ticker not found")
    return {"ticker": ticker, "factors": factors}


@router.get("/refinitiv/distress/{ticker}")
def get_distress(ticker: str):
    base = _analytics_base()
    if not base.exists():
        raise HTTPException(status_code=404, detail="Analytics pack not found")
    distress = _distress(base, ticker)
    if not distress:
        raise HTTPException(status_code=404, detail="Ticker not found or no distress score")
    return {"ticker": ticker, **distress}


@router.get("/refinitiv/coverage")
def get_coverage():
    base = _analytics_base()
    path = base / "summary" / "coverage.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Coverage not found")
    import json

    return json.loads(path.read_text())


@router.get("/refinitiv/movers")
def get_movers():
    base = _analytics_base()
    path = base / "summary" / "movers_zscores.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Movers not found")
    import json

    return json.loads(path.read_text())
