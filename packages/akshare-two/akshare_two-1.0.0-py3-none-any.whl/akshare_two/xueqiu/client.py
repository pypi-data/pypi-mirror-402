from typing import Any

import requests


class XueqiuClient:
    """雪球API客户端"""

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Referer": "https://xueqiu.com/"
        })

    def _get_xueqiu_symbol(self, symbol: str) -> str:
        """转换为雪球格式的股票代码"""
        if symbol.startswith(("SH", "SZ")):
            return symbol
        if symbol.startswith(("000", "001", "002", "003", "300", "200")):
            return f"SZ{symbol}"
        return f"SH{symbol}"

    def fetch_realtime_quote(self, symbol: str) -> dict[str, Any]:
        """获取实时行情"""
        url = "https://stock.xueqiu.com/v5/stock/quote.json"
        xq_symbol = self._get_xueqiu_symbol(symbol)
        params = {
            "symbol": xq_symbol,
            "extend": "detail"
        }
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()  # type: ignore

    def fetch_insider_trades(self, symbol: str = "", count: int = 100) -> dict[str, Any]:
        """获取内部交易数据"""
        if symbol:
            url = "https://stock.xueqiu.com/v5/stock/f10/cn/skholderchg.json"
            xq_symbol = self._get_xueqiu_symbol(symbol)
            params = {
                "symbol": xq_symbol,
                "count": str(count)
            }
        else:
            # 获取所有内部交易数据
            url = "https://stock.xueqiu.com/v5/stock/insider/cn/list.json"
            params = {
                "page": "1",
                "size": str(count)
            }
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()  # type: ignore
