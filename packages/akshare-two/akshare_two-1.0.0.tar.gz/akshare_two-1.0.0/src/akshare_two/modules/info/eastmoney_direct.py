import pandas as pd

from akshare_two.eastmoney.client import EastMoneyClient

from ..cache import cache
from .base import InfoDataProvider


class EastMoneyDirectInfo(InfoDataProvider):
    """Direct implementation for EastMoney info data API"""

    def __init__(self, symbol: str):
        super().__init__(symbol)
        self.client = EastMoneyClient()

    def get_basic_info(self) -> pd.DataFrame:
        """Get basic stock info - placeholder for future implementation"""
        raise NotImplementedError("Basic info not yet implemented in direct mode")

    @cache("main_business_cache", key=lambda self: f"main_business_{self.symbol}")
    def get_main_business(self) -> pd.DataFrame:
        """Get main business composition data"""
        try:
            raw_data = self.client.fetch_main_business(self.symbol)

            # 新API返回格式: {zyfw: ..., zygcfx: [...], jyps: ...}
            business_data = raw_data.get("zygcfx", [])
            
            if not business_data:
                return pd.DataFrame()

            df = pd.DataFrame(business_data)
            
            # 标准化字段名
            column_mapping = {
                "rq": "report_date",
                "zy": "business_name",
                "zysr": "revenue",
                "zysrbl": "revenue_ratio",
                "zycb": "cost",
                "zylr": "profit",
                "zylrbl": "profit_ratio",
            }
            
            df = df.rename(columns=column_mapping)
            available_cols = [col for col in ["report_date", "business_name", "revenue", "revenue_ratio", "cost", "profit", "profit_ratio"] if col in df.columns]
            return df[available_cols] if available_cols else df

        except Exception as e:
            raise ValueError(f"Failed to get main business data for {self.symbol}: {e}") from e

    @cache("stock_news_cache", key=lambda self, page_size: f"stock_news_{self.symbol}_{page_size}")
    def get_stock_news(self, page_size: int = 100) -> pd.DataFrame:
        """Get stock news"""
        try:
            raw_data = self.client.fetch_stock_news(self.symbol, page_size)

            # 东方财富新闻API返回的是JSONP格式，需要解析
            # 这里简化处理，假设已经是JSON格式
            if not raw_data or "data" not in raw_data:
                return pd.DataFrame()

            news_list = raw_data.get("data", [])
            if not news_list:
                return pd.DataFrame()

            records = []
            for item in news_list:
                records.append({
                    "title": item.get("title", ""),
                    "publish_time": item.get("showtime", ""),
                    "content": item.get("digest", ""),
                    "url": item.get("url", ""),
                })

            return pd.DataFrame(records)

        except Exception as e:
            raise ValueError(f"Failed to get stock news for {self.symbol}: {e}") from e
