from abc import ABC, abstractmethod

import pandas as pd


class FundFlowProvider(ABC):
    def __init__(self, symbol: str) -> None:
        self.symbol = symbol

    @abstractmethod
    def get_fund_flow(self, period: str = "daily") -> pd.DataFrame:
        """Fetches fund flow data

        Args:
            period: 'daily', 'weekly', or 'monthly'

        Returns:
            pd.DataFrame:
            - date: 日期
            - main_net_inflow: 主力净流入
            - small_net_inflow: 小单净流入
            - medium_net_inflow: 中单净流入
            - large_net_inflow: 大单净流入
            - super_net_inflow: 超大单净流入
        """
        pass
