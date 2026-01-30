from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import pandas as pd


class MarketDataInterval(str, Enum):
    ONE_DAY = "1d"


async def get_real_time_quote(ticker: str) -> Dict[str, Any]:
    """
    Best-effort quote via yfinance.

    Note: yfinance can be delayed; treat this as a convenience fallback.
    """
    import yfinance as yf

    out: Dict[str, Any] = {"ticker": ticker, "source": "yfinance"}
    t = yf.Ticker(ticker)
    info = getattr(t, "fast_info", None)
    if info:
        price = info.get("last_price") or info.get("lastPrice")
        if price is not None:
            out["price"] = float(price)
            return out

    hist = t.history(period="5d", interval="1d")
    if hist is not None and not hist.empty and "Close" in hist.columns:
        out["price"] = float(hist["Close"].dropna().iloc[-1])
        out["timestamp"] = hist.index[-1].isoformat()
    return out


async def get_historical_data(ticker: str, period: str = "1y", interval: str = "1d") -> List[Dict[str, Any]]:
    import yfinance as yf

    df = yf.download(ticker, period=period, interval=interval, auto_adjust=False, progress=False)
    if df is None or df.empty:
        return []

    df = df.reset_index()
    date_col = "Date" if "Date" in df.columns else ("Datetime" if "Datetime" in df.columns else None)
    if date_col is None:
        return []

    records: List[Dict[str, Any]] = []
    for row in df.itertuples(index=False):
        dt = getattr(row, date_col)
        records.append(
            {
                "ticker": ticker,
                "date": pd.Timestamp(dt).isoformat(),
                "open": float(getattr(row, "Open")),
                "high": float(getattr(row, "High")),
                "low": float(getattr(row, "Low")),
                "close": float(getattr(row, "Close")),
                "volume": float(getattr(row, "Volume")) if hasattr(row, "Volume") else None,
                "source": "yfinance",
            }
        )
    return records


@dataclass(slots=True)
class MarketDataSource:
    """
    Minimal market data helper used by intelligence endpoints.

    In Cite-Finance, this is used as a convenience fallback for price history
    and quotes; premium sources are accessed via the aggregator plugins.
    """

    config: Dict[str, Any]

    async def get_historical_prices(
        self,
        ticker: str,
        period: str = "3mo",
        interval: MarketDataInterval = MarketDataInterval.ONE_DAY,
    ) -> List[Dict[str, Any]]:
        interval_str = "1d" if interval == MarketDataInterval.ONE_DAY else str(interval)
        data = await get_historical_data(ticker, period=period, interval=interval_str)
        return [
            {
                "date": r["date"],
                "open": r["open"],
                "high": r["high"],
                "low": r["low"],
                "close": r["close"],
                "volume": r.get("volume"),
            }
            for r in data
        ]

    async def get_realtime_quote(self, ticker: str) -> Optional[Dict[str, Any]]:
        return await get_real_time_quote(ticker)


__all__ = ["MarketDataInterval", "MarketDataSource", "get_historical_data", "get_real_time_quote"]

