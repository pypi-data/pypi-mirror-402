from typing import Any

import requests


class SinaClient:
    """新浪财经API客户端"""

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })

    def _get_market_prefix(self, symbol: str) -> str:
        """获取市场前缀"""
        if symbol.startswith(("sh", "sz", "bj")):
            return symbol
        if symbol.startswith(("000", "001", "002", "003", "300", "200")):
            return f"sz{symbol}"
        return f"sh{symbol}"

    def fetch_minute_data(self, symbol: str, period: str = "1", adjust: str = "") -> dict[str, Any]:
        """获取分钟K线数据"""
        url = "https://quotes.sina.cn/cn/api/json_v2.php/CN_MarketDataService.getKLineData"
        stock = self._get_market_prefix(symbol)
        params = {
            "symbol": stock,
            "scale": period,
            "ma": "no",
            "datalen": "1023"
        }
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return {"data": response.json()}  # type: ignore

    def fetch_daily_data(self, symbol: str, start_date: str, end_date: str, adjust: str = "") -> dict[str, Any]:
        """获取日线数据"""
        url = "https://quotes.sina.cn/cn/api/json_v2.php/CN_MarketDataService.getKLineData"
        stock = self._get_market_prefix(symbol)
        params = {
            "symbol": stock,
            "scale": "240",
            "ma": "no",
            "datalen": "1023"
        }
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return {"data": response.json()}  # type: ignore

    def fetch_financial_report(self, symbol: str, report_type: str) -> dict[str, Any]:
        """获取财务报表数据
        
        Args:
            symbol: 股票代码
            report_type: 报表类型 (资产负债表/利润表/现金流量表)
        """
        url = "https://money.finance.sina.com.cn/corp/go.php/vFD_FinancialGuideLine/stockid/{}/ctrl/{}/displaytype/4.phtml"
        stock = self._get_market_prefix(symbol)
        
        type_map = {
            "资产负债表": "balancesheet",
            "利润表": "profitstatement",
            "现金流量表": "cashflow"
        }
        ctrl = type_map.get(report_type, "balancesheet")
        
        response = self.session.get(url.format(stock, ctrl))
        response.raise_for_status()
        return {"html": response.text}
