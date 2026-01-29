import re

from achive.beanparser.judge import is_mostly_pinduoduo, is_mostly_meituan
from achive.cache.refund_cache_manager import order_cache
from achive.rules.rules import commodity_rules_payee


def handle_commerce(
    product: str,
    origin_product: str,
    default_category: str,
    data: dict,
    counterparty: str,
) -> dict:
    is_pinduoduo = is_mostly_pinduoduo(origin_product)
    is_meituan = is_mostly_meituan(origin_product)
    for match_type, parttern, _, account in commodity_rules_payee:
        if match_type == "regex":
            if re.search(parttern, product):
                if is_pinduoduo:
                    pinduoduo_order_id = origin_product.replace("商户单号", "")
                    order_cache.save_order(pinduoduo_order_id, account)
                elif is_meituan:
                    meituan_order_id = origin_product.replace("美团订单-", "")
                    order_cache.save_order(meituan_order_id, account)
                data["status"] = "*"
                data["commodity"] = product
                data["account"] = account
                if "*" in counterparty:
                    data["conterparty"] = "淘宝/闲鱼"
                else:
                    data["conterparty"] = counterparty
                return data
    data["status"] = "!"
    data["conterparty"] = counterparty
    data["commodity"] = product
    data["account"] = f"Expense:{default_category}:Fixme"
    return data


def handle_supermarket(
    product: str, _: str, default_category: str, data: dict, counterparty: str
) -> dict:
    for match_type, parttern, _, account in commodity_rules_payee:
        if match_type == "regex":
            if re.search(parttern, product):
                data["status"] = "*"
                data["commodity"] = product
                data["account"] = account
                data["conterparty"] = counterparty
                return data
    data["status"] = "!"
    data["conterparty"] = counterparty
    data["commodity"] = product
    data["account"] = f"Expense:{default_category}:Fixme"
    return data
