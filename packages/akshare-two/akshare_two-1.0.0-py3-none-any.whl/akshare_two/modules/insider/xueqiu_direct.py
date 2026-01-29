import pandas as pd

from akshare_two.xueqiu.client import XueqiuClient
from akshare_two.modules.cache import cache

from .base import InsiderDataProvider


class XueqiuDirectInsider(InsiderDataProvider):
    """雪球内部交易数据直连实现"""

    def __init__(self, symbol: str = "") -> None:
        super().__init__(symbol)
        self.client = XueqiuClient()

    @cache(
        "financial_cache",
        key=lambda self: f"xueqiu_direct_insider_{self.symbol if self.symbol else 'all'}",
    )
    def get_inner_trade_data(self) -> pd.DataFrame:
        """获取内部交易数据"""
        raw_data = self.client.fetch_insider_trades(self.symbol)
        
        if self.symbol:
            # 单个股票的内部交易
            items = raw_data.get("data", {}).get("items", [])
        else:
            # 所有股票的内部交易
            items = raw_data.get("data", {}).get("list", [])
        
        if not items:
            return pd.DataFrame()

        records = []
        for item in items:
            records.append({
                "symbol": item.get("stock_symbol", "").replace("SH", "").replace("SZ", ""),
                "issuer": item.get("stock_name", ""),
                "name": item.get("holder_name", ""),
                "title": item.get("position", ""),
                "transaction_date": pd.to_datetime(item.get("change_date", 0), unit="ms"),
                "transaction_shares": float(item.get("change_number", 0)),
                "transaction_price_per_share": float(item.get("avg_price", 0)),
                "shares_owned_after_transaction": float(item.get("after_number", 0)),
                "relationship": item.get("relationship", ""),
            })

        df = pd.DataFrame(records)
        
        if "transaction_date" in df.columns:
            df["transaction_date"] = df["transaction_date"].dt.tz_localize("Asia/Shanghai")
        
        df["is_board_director"] = df["title"].str.contains("董事", na=False)
        df["transaction_value"] = df["transaction_shares"] * df["transaction_price_per_share"]
        df["shares_owned_before_transaction"] = df["shares_owned_after_transaction"] - df["transaction_shares"]

        return df
