from typing import Any

import requests


class EastMoneyClient:
    """
    A client for interacting directly with EastMoney's data APIs.
    This class handles session management, request signing, and API calls.
    """

    def __init__(self) -> None:
        self.session = requests.Session()

    def _get_security_id(self, symbol: str) -> str:
        """
        Converts a stock symbol to EastMoney's internal secid format.
        e.g., '600519' -> '1.600519', '000001' -> '0.000001'
        """
        symbol = symbol.upper()
        if symbol.startswith("SZ"):
            market = "0"
            code = symbol[2:]
        elif symbol.startswith("SH"):
            market = "1"
            code = symbol[2:]
        elif symbol.startswith("HK"):
            market = "116"
            code = symbol[2:]
        elif len(symbol) == 6:
            if symbol.startswith(("000", "001", "002", "003", "300", "200")):
                market = "0"
            elif symbol.startswith(
                ("600", "601", "603", "605", "688", "900", "5", "6")
            ):
                market = "1"
            else:
                market = "0"  # Default to SZ for ambiguity
            code = symbol
        elif len(symbol) == 5:  # HK Market
            market = "116"
            code = symbol
        else:
            market = "0"
            code = symbol
        return f"{market}.{code}"

    def fetch_historical_klines(
        self, symbol: str, klt: str, fqt: str, start_date: str, end_date: str
    ) -> dict[str, Any]:
        """
        Fetches historical K-line (candlestick) data.
        """
        url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
        secid = self._get_security_id(symbol)
        params = {
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "klt": klt,
            "fqt": fqt,
            "secid": secid,
            "beg": start_date,
            "end": end_date,
        }
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()  # type: ignore

    def fetch_realtime_quote(self, symbol: str) -> dict[str, Any]:
        """
        Fetches real-time quote data for a single stock.
        """
        url = "https://push2.eastmoney.com/api/qt/stock/get"
        secid = self._get_security_id(symbol)
        params = {
            "invt": "2",
            "fltt": "2",
            "fields": (
                "f43,f57,f58,f169,f170,f46,f60,f44,f51,f168,f47,f164,f163,f116,f60,f45,f52,f50,f48,f167,f117,f71,f161,f49,f530"
            ),
            "secid": secid,
        }
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()  # type: ignore

    def fetch_fund_flow(self, symbol: str, klt: str = "101") -> dict[str, Any]:
        """
        Fetches individual stock fund flow data.
        klt: 101=daily, 102=weekly, 103=monthly
        """
        url = "https://push2.eastmoney.com/api/qt/stock/fflow/kline/get"
        secid = self._get_security_id(symbol)
        params = {
            "lmt": "0",
            "klt": klt,
            "secid": secid,
            "fields1": "f1,f2,f3,f7",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65",
        }
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()  # type: ignore

    def fetch_billboard_detail(
        self, symbol: str, start_date: str = "", end_date: str = ""
    ) -> dict[str, Any]:
        """
        Fetches billboard (龙虎榜) detail data.
        """
        url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
        filter_str = f'(SECURITY_CODE="{symbol}")'
        if start_date:
            filter_str += f'(TRADE_DATE>=\'{start_date}\')'
        if end_date:
            filter_str += f'(TRADE_DATE<=\'{end_date}\')'
        params = {
            "reportName": "RPT_BILLBOARD_DAILYDETAILSBUY",
            "filter": filter_str,
            "pageNumber": "1",
            "pageSize": "500",
            "sortColumns": "BUY",
            "sortTypes": "-1",
            "columns": "ALL",
            "source": "WEB",
            "client": "WEB",
        }
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()  # type: ignore

    def fetch_bid_ask_details(self, symbol: str) -> dict[str, Any]:
        """
        Fetches bid/ask transaction details (内外盘).
        """
        url = "https://push2.eastmoney.com/api/qt/stock/details/get"
        secid = self._get_security_id(symbol)
        params = {
            "secid": secid,
            "fields1": "f1,f2,f3,f4",
            "fields2": "f51,f52,f53,f54,f55",
        }
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()  # type: ignore

    def fetch_auction_data(self, symbol: str) -> dict[str, Any]:
        """
        Fetches pre-market auction data (盘前竞价).
        """
        url = "https://push2.eastmoney.com/api/qt/stock/auction/get"
        secid = self._get_security_id(symbol)
        params = {
            "secid": secid,
            "fields": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13",
        }
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()  # type: ignore

    def fetch_main_business(self, symbol: str) -> dict[str, Any]:
        """
        Fetches main business composition (主营业务构成).
        """
        # 判断市场代码
        if symbol.startswith(("6", "5")):
            code = f"SH{symbol}"
        else:
            code = f"SZ{symbol}"
        
        url = "https://emweb.securities.eastmoney.com/PC_HSF10/BusinessAnalysis/PageAjax"
        params = {"code": code}
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()  # type: ignore

    def fetch_stock_news(
        self, symbol: str, page_size: int = 100, page_index: int = 1
    ) -> dict[str, Any]:
        """
        Fetches stock news (个股新闻).
        """
        url = "https://np-listapi.eastmoney.com/comm/wap/getListInfo"
        params = {
            "client": "wap",
            "type": "1",
            "mTypeAndCode": f"0_{symbol}",
            "pageSize": str(page_size),
            "pageIndex": str(page_index),
        }
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()  # type: ignore

    def fetch_stock_info(self, symbol: str) -> dict[str, Any]:
        """
        Fetches stock basic information (个股信息).
        """
        secid = self._get_security_id(symbol)
        url = "https://push2.eastmoney.com/api/qt/stock/get"
        params = {
            "invt": "2",
            "fltt": "2",
            "fields": "f57,f58,f84,f85,f86,f87,f88,f89,f90,f91,f92,f93,f94,f95,f96,f97,f98,f99,f100,f101,f102,f103,f104,f105,f106,f107,f108,f109,f110,f111,f112,f113,f114,f115,f116,f117,f118,f119,f120,f121,f122,f123,f124,f125,f126,f127,f128,f129,f130,f131,f132,f133,f134,f135,f136,f137,f138,f139,f140,f141,f142,f143,f144,f145,f146,f147,f148,f149,f150,f151,f152,f153,f154,f155,f156,f157,f158,f159,f160,f161,f162,f163,f164,f165,f166,f167,f168,f169,f170,f171,f172,f173,f174,f175,f176,f177,f178,f179,f180,f181,f182,f183,f184,f185,f186,f187,f188,f189,f190,f191,f192,f193,f194,f195,f196,f197,f198,f199,f200,f201,f202,f203,f204,f205,f206,f207,f208,f209,f210,f211,f212,f213,f214,f215,f216,f217,f218,f219,f220,f221,f222,f223,f224,f225,f226,f227,f228,f229,f230,f231,f232,f233,f234,f235,f236,f237,f238,f239,f240,f241,f242,f243,f244,f245,f246,f247,f248,f249,f250,f251,f252,f253,f254,f255,f256,f257,f258,f259,f260,f261,f262,f263,f264,f265,f266,f267,f268,f269,f270,f271,f272,f273,f274,f275,f276,f277,f278,f279,f280,f281,f282,f283,f284,f285,f286,f287,f288,f289,f290,f291,f292,f293,f294,f295,f296,f297,f298,f299,f300",
            "secid": secid,
        }
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()  # type: ignore

    def fetch_all_stocks_realtime(self) -> dict[str, Any]:
        """
        Fetches real-time data for all A-share stocks.
        """
        url = "https://push2.eastmoney.com/api/qt/clist/get"
        params = {
            "pn": "1",
            "pz": "10000",
            "po": "1",
            "np": "1",
            "fltt": "2",
            "invt": "2",
            "fid": "f3",
            "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
            "fields": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152",
        }
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()  # type: ignore
