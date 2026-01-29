from abc import ABC, abstractmethod

import pandas as pd


class RealtimeDataProvider(ABC):
    def __init__(self, symbol: str) -> None:
        self.symbol = symbol

    @abstractmethod
    def get_current_data(self) -> pd.DataFrame:
        """Fetches realtime market data

        Returns:
            pd.DataFrame:
            - symbol: 股票代码
            - price: 最新价
            - change: 涨跌额
            - pct_change: 涨跌幅(%)
            - timestamp: 时间戳
            - volume: 成交量(手)
            - amount: 成交额(元)
            - open: 今开
            - high: 最高
            - low: 最低
            - prev_close: 昨收
        """
        pass

    def get_bid_ask_details(self) -> pd.DataFrame:
        """Fetches bid/ask transaction details (内外盘)

        Returns:
            pd.DataFrame:
            - time: 时间
            - price: 价格
            - volume: 成交量
            - direction: 方向 (买/卖)
        """
        raise NotImplementedError("This provider does not support bid/ask details")

    def get_auction_data(self) -> pd.DataFrame:
        """Fetches pre-market auction data (盘前竞价)

        Returns:
            pd.DataFrame:
            - time: 时间
            - price: 价格
            - volume: 成交量
        """
        raise NotImplementedError("This provider does not support auction data")
