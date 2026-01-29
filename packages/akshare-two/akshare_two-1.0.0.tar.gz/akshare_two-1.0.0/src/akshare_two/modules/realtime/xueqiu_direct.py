import pandas as pd

from akshare_two.xueqiu.client import XueqiuClient
from akshare_two.modules.cache import cache

from .base import RealtimeDataProvider


class XueqiuDirectRealtime(RealtimeDataProvider):
    """雪球实时数据直连实现"""

    def __init__(self, symbol: str) -> None:
        super().__init__(symbol)
        self.client = XueqiuClient()

    @cache("realtime_cache", key=lambda self: f"xueqiu_direct_{self.symbol}")
    def get_current_data(self) -> pd.DataFrame:
        """获取实时行情数据"""
        raw_data = self.client.fetch_realtime_quote(self.symbol)
        
        quote = raw_data.get("data", {}).get("quote", {})
        if not quote:
            return pd.DataFrame()

        data = {
            "symbol": self.symbol,
            "price": quote.get("current", 0.0),
            "change": quote.get("chg", 0.0),
            "pct_change": quote.get("percent", 0.0),
            "timestamp": pd.to_datetime(quote.get("timestamp", 0), unit="ms").tz_localize("Asia/Shanghai"),
            "volume": quote.get("volume", 0) / 100,
            "amount": quote.get("amount", 0.0),
            "open": quote.get("open", 0.0),
            "high": quote.get("high", 0.0),
            "low": quote.get("low", 0.0),
            "prev_close": quote.get("last_close", 0.0),
        }

        return pd.DataFrame([data])
