from strategy.provider.ali_provider import AliProvider
from strategy.provider.ali_provider import AliProvider


def create_workder(provider: str):
    if provider == "alipay":
        return AliProvider()
    else:
        raise ValueError("未知供应商")
