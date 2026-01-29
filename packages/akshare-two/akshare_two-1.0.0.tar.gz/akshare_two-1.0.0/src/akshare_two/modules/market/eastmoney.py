import pandas as pd

from akshare_two.eastmoney.client import EastMoneyClient

from ..cache import cache
from .base import BillboardProvider


class EastMoneyBillboard(BillboardProvider):
    """EastMoney implementation for billboard data"""

    def __init__(self, symbol: str):
        super().__init__(symbol)
        self.client = EastMoneyClient()

    @cache("billboard_cache", key=lambda self, start_date, end_date: f"billboard_{self.symbol}_{start_date}_{end_date}")
    def get_billboard_detail(self, start_date: str = "", end_date: str = "") -> pd.DataFrame:
        """Get billboard detail data"""
        try:
            raw_data = self.client.fetch_billboard_detail(self.symbol, start_date, end_date)

            if raw_data.get("code") != 200:
                raise ValueError(f"API returned error: {raw_data.get('message')}")

            result = raw_data.get("result", {})
            data = result.get("data", [])
            
            if not data:
                return pd.DataFrame()

            df = pd.DataFrame(data)
            
            # 标准化字段名
            column_mapping = {
                "TRADE_DATE": "trade_date",
                "EXPLANATION": "reason",
                "BUYER_AMOUNT": "buy_amount",
                "SELLER_AMOUNT": "sell_amount",
                "NET_AMOUNT": "net_amount",
            }
            
            df = df.rename(columns=column_mapping)
            return df[["trade_date", "reason", "buy_amount", "sell_amount", "net_amount"]]

        except Exception as e:
            raise ValueError(f"Failed to get billboard data for {self.symbol}: {e}") from e
