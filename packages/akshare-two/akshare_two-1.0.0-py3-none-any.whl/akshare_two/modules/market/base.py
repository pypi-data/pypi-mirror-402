from abc import ABC, abstractmethod

import pandas as pd


class BillboardProvider(ABC):
    def __init__(self, symbol: str) -> None:
        self.symbol = symbol

    @abstractmethod
    def get_billboard_detail(self, start_date: str = "", end_date: str = "") -> pd.DataFrame:
        """Fetches billboard (龙虎榜) detail data

        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            pd.DataFrame:
            - trade_date: 交易日期
            - reason: 上榜原因
            - buy_amount: 买入金额
            - sell_amount: 卖出金额
            - net_amount: 净额
        """
        pass
