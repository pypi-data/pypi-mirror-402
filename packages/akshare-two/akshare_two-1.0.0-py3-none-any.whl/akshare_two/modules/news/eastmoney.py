import pandas as pd

from akshare_two.eastmoney.client import EastMoneyClient

from ..cache import cache
from .base import NewsDataProvider


class EastMoneyNews(NewsDataProvider):
    def __init__(self, symbol: str):
        super().__init__(symbol)
        self.client = EastMoneyClient()

    @cache("news_cache", key=lambda self: f"eastmoney_news_{self.symbol}")
    def get_news_data(self) -> pd.DataFrame:
        """获取东方财富个股新闻数据"""
        try:
            raw_data = self.client.fetch_stock_news(self.symbol, page_size=100)
            
            if not raw_data or "data" not in raw_data:
                return pd.DataFrame()

            news_list = raw_data.get("data", [])
            if not news_list:
                return pd.DataFrame()

            records = []
            for item in news_list:
                records.append({
                    "keyword": self.symbol,
                    "title": item.get("title", ""),
                    "content": item.get("digest", ""),
                    "publish_time": pd.to_datetime(item.get("showtime", "")),
                    "source": item.get("source", ""),
                    "url": item.get("url", ""),
                })

            df = pd.DataFrame(records)
            if "publish_time" in df.columns:
                df["publish_time"] = df["publish_time"].dt.tz_localize("Asia/Shanghai")
            
            return df

        except Exception as e:
            raise ValueError(f"Failed to get news for {self.symbol}: {e}") from e
