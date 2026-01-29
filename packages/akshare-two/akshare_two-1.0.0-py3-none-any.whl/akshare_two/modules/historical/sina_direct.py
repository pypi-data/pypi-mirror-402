import pandas as pd

from akshare_two.sina.client import SinaClient
from akshare_two.modules.cache import cache

from .base import HistoricalDataProvider


class SinaDirectHistorical(HistoricalDataProvider):
    """新浪财经历史数据直连实现"""

    def __init__(
        self,
        symbol: str,
        interval: str = "day",
        interval_multiplier: int = 1,
        start_date: str = "20200101",
        end_date: str = "20991231",
        adjust: str = "none",
    ) -> None:
        super().__init__(symbol, interval, interval_multiplier, start_date, end_date, adjust)
        self.client = SinaClient()

    @cache(
        "hist_data_cache",
        key=lambda self: f"sina_direct_{self.symbol}_{self.interval}_{self.interval_multiplier}_{self.adjust}",
    )
    def get_hist_data(self) -> pd.DataFrame:
        """获取历史数据"""
        if self.interval in ["minute", "hour"]:
            period = "1" if self.interval == "minute" else "60"
            raw_data = self.client.fetch_minute_data(self.symbol, period, self.adjust)
        else:
            raw_data = self.client.fetch_daily_data(
                self.symbol, self.start_date, self.end_date, self.adjust
            )

        df = pd.DataFrame(raw_data["data"])
        if df.empty:
            return df

        # 标准化列名
        df = df.rename(columns={
            "day": "timestamp",
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "volume": "volume",
        })

        df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.tz_localize("Asia/Shanghai")
        df["volume"] = df["volume"].astype("int64")

        return df[["timestamp", "open", "high", "low", "close", "volume"]]
