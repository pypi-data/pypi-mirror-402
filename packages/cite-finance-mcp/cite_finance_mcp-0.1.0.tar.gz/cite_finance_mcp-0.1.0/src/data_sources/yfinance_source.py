"""
YFinance data source placeholder.

The aggregator routes YFINANCE calls to helper functions in
`src.data_sources.market_data`, but it still expects a YFINANCE source
to be registered for capability/tier routing.
"""

from __future__ import annotations

from typing import Any, Dict

from src.data_sources.base import DataSource, DataSourceCapability, DataSourceType


class YFinanceSource(DataSource):
    def __init__(self, config: Dict[str, Any] | None = None):
        super().__init__(config or {})
        self.name = "YFINANCE"
        self.source_type = DataSourceType.YAHOO_FINANCE
        self.capabilities = [
            DataSourceCapability.REAL_TIME,
            DataSourceCapability.HISTORICAL_DATA,
            DataSourceCapability.MARKET_PRICES,
        ]

