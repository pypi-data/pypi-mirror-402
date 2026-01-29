from provider.ali.alipay import AliPay


provider_dict = {"alipay": AliPay()}


def get_provider(provider_name: str):
    return provider_dict.get(provider_name, None)
