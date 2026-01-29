import pandas as pd

from akshare_two.eastmoney.client import EastMoneyClient

from ..cache import cache
from .base import FundFlowProvider


class EastMoneyFundFlow(FundFlowProvider):
    """EastMoney implementation for fund flow data"""

    def __init__(self, symbol: str):
        super().__init__(symbol)
        self.client = EastMoneyClient()

    @cache("fund_flow_cache", key=lambda self, period: f"fund_flow_{self.symbol}_{period}")
    def get_fund_flow(self, period: str = "daily") -> pd.DataFrame:
        """Get fund flow data"""
        klt_map = {"daily": "101", "weekly": "102", "monthly": "103"}
        klt = klt_map.get(period, "101")

        try:
            raw_data = self.client.fetch_fund_flow(self.symbol, klt)

            if raw_data.get("rc") != 0:
                raise ValueError(f"API returned error: {raw_data.get('msg')}")

            klines = raw_data.get("data", {}).get("klines", [])
            if not klines:
                return pd.DataFrame()

            records = []
            for line in klines:
                parts = line.split(",")
                records.append({
                    "date": parts[0],
                    "main_net_inflow": float(parts[1]),
                    "small_net_inflow": float(parts[2]),
                    "medium_net_inflow": float(parts[3]),
                    "large_net_inflow": float(parts[4]),
                    "super_net_inflow": float(parts[5]),
                })

            return pd.DataFrame(records)

        except Exception as e:
            raise ValueError(f"Failed to get fund flow data for {self.symbol}: {e}") from e
