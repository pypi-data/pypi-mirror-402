from .base import BillboardProvider
from .eastmoney import EastMoneyBillboard


class BillboardFactory:
    _providers = {
        "eastmoney": EastMoneyBillboard,
    }

    @classmethod
    def get_provider(cls, source: str, symbol: str, **kwargs) -> BillboardProvider:
        if source not in cls._providers:
            raise ValueError(f"Unknown billboard data provider: {source}")
        return cls._providers[source](symbol=symbol, **kwargs)

    @staticmethod
    def create(symbol: str, provider: str = "eastmoney") -> BillboardProvider:
        if provider == "eastmoney":
            return EastMoneyBillboard(symbol)
        raise ValueError(f"Unknown provider: {provider}")
