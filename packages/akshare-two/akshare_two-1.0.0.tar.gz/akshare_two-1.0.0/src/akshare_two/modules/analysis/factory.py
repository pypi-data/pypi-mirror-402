from .base import FundFlowProvider
from .eastmoney import EastMoneyFundFlow


class FundFlowFactory:
    _providers = {
        "eastmoney": EastMoneyFundFlow,
    }

    @classmethod
    def get_provider(cls, source: str, symbol: str, **kwargs) -> FundFlowProvider:
        if source not in cls._providers:
            raise ValueError(f"Unknown fund flow data provider: {source}")
        return cls._providers[source](symbol=symbol, **kwargs)

    @staticmethod
    def create(symbol: str, provider: str = "eastmoney") -> FundFlowProvider:
        if provider == "eastmoney":
            return EastMoneyFundFlow(symbol)
        raise ValueError(f"Unknown provider: {provider}")
