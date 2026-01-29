import pandas as pd

from akshare_two.eastmoney.client import EastMoneyClient
from akshare_two.eastmoney.utils import parse_realtime_data

from ..cache import cache
from .base import RealtimeDataProvider


class EastMoneyDirectRealtime(RealtimeDataProvider):
    """Direct implementation for EastMoney realtime stock data API"""

    def __init__(self, symbol: str):
        super().__init__(symbol)
        self.client = EastMoneyClient()

    @cache(
        "realtime_cache",
        key=lambda self: f"eastmoney_direct_realtime_{self.symbol}",
    )
    def get_current_data(self) -> pd.DataFrame:
        """Get real-time stock data"""
        try:
            raw_data = self.client.fetch_realtime_quote(self.symbol)

            if raw_data.get("rc") != 0:
                raise ValueError(f"API returned error: {raw_data.get('msg')}")

            df = parse_realtime_data(raw_data)

            # Ensure the output matches the base class definition
            if self.symbol:
                df = df[df["symbol"] == self.symbol].reset_index(drop=True)

            return df

        except Exception as e:
            raise ValueError(
                f"Failed to get real-time data for {self.symbol}: {e}"
            ) from e

    @cache("bid_ask_cache", key=lambda self: f"bid_ask_{self.symbol}")
    def get_bid_ask_details(self) -> pd.DataFrame:
        """Get bid/ask transaction details"""
        try:
            raw_data = self.client.fetch_bid_ask_details(self.symbol)

            if raw_data.get("rc") != 0:
                raise ValueError(f"API returned error: {raw_data.get('msg')}")

            details = raw_data.get("data", {}).get("details")
            if not details:
                return pd.DataFrame()

            # details可能是字符串或列表
            if isinstance(details, str):
                lines = details.split(";")
            else:
                lines = details

            records = []
            for line in lines:
                if line:
                    parts = line.split(",") if isinstance(line, str) else line
                    if len(parts) >= 4:
                        records.append({
                            "time": parts[0],
                            "price": float(parts[1]),
                            "volume": int(parts[2]),
                            "direction": "买" if int(parts[3]) == 1 else "卖",
                        })

            return pd.DataFrame(records)

        except Exception as e:
            raise ValueError(f"Failed to get bid/ask details for {self.symbol}: {e}") from e

    @cache("auction_cache", key=lambda self: f"auction_{self.symbol}")
    def get_auction_data(self) -> pd.DataFrame:
        """Get pre-market auction data"""
        try:
            raw_data = self.client.fetch_auction_data(self.symbol)

            if raw_data.get("rc") != 0:
                raise ValueError(f"API returned error: {raw_data.get('msg')}")

            data = raw_data.get("data", {})
            if not data:
                return pd.DataFrame()

            records = [{
                "time": data.get("f1"),
                "price": float(data.get("f2", 0)),
                "volume": int(data.get("f3", 0)),
            }]

            return pd.DataFrame(records)

        except Exception as e:
            raise ValueError(f"Failed to get auction data for {self.symbol}: {e}") from e
