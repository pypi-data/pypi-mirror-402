from abc import ABC, abstractmethod

import pandas as pd


class InfoDataProvider(ABC):
    def __init__(self, symbol: str) -> None:
        self.symbol = symbol

    @abstractmethod
    def get_basic_info(self) -> pd.DataFrame:
        """Fetches stock basic info data

        Returns:
            pd.DataFrame:
            - price: 最新价
            - symbol: 股票代码
            - name: 股票简称
            - total_shares: 总股本
            - float_shares: 流通股
            - total_market_cap: 总市值
            - float_market_cap: 流通市值
            - industry: 行业
            - listing_date: 上市时间
        """
        pass

    def get_main_business(self) -> pd.DataFrame:
        """Fetches main business composition data

        Returns:
            pd.DataFrame:
            - report_date: 报告期
            - business_name: 业务名称
            - revenue: 营业收入
            - revenue_ratio: 收入占比
            - cost: 营业成本
            - profit: 营业利润
            - profit_ratio: 利润占比
        """
        raise NotImplementedError("This provider does not support main business data")

    def get_stock_news(self, page_size: int = 100) -> pd.DataFrame:
        """Fetches stock news

        Returns:
            pd.DataFrame:
            - title: 标题
            - publish_time: 发布时间
            - content: 内容摘要
            - url: 链接
        """
        raise NotImplementedError("This provider does not support stock news")
