import re

from achive.beanparser.callable import handle_commerce, handle_supermarket
from achive.rules.rules import commodity_rules_payee, payee_rules_payee

FUNC_MAP = {
    "handle_commerce": handle_commerce,
    "handle_supermarket": handle_supermarket,
}


def match_by_comm(product: str, counterparty: str, remark: str, data: dict) -> dict:
    for match_type, pattern, _, account in commodity_rules_payee:
        if match_type == "regex":
            match = re.search(pattern, product)
            if match:
                return set_normal_data("*", counterparty, product, account, "origin", remark, data)  # type: ignore
            else:
                match_comm = re.search(pattern, remark)
                if match_comm:
                    return set_normal_data("*", counterparty, remark, account, "origin", remark, data)  # type: ignore
    return data


def match_by_counterparty(
    remark: str, product: str, keyword: str, counterparty: str, data: dict
) -> dict:
    for match_type, keyword, payee, commodity, account_or_func in payee_rules_payee:
        is_matched = False
        if match_type == "keyword":
            is_matched = keyword in counterparty
        elif match_type == "regex":
            is_matched = re.search(keyword, counterparty) is not None

        if is_matched:
            if isinstance(account_or_func, str) and account_or_func in FUNC_MAP:
                func = FUNC_MAP[account_or_func]
                return func(remark, product, keyword, data, counterparty)  # type: ignore
            else:
                return set_normal_data(
                    "*", counterparty, commodity, account_or_func, payee, remark, data
                )
    return data


def set_normal_data(
    status: str,
    counterparty: str,
    commodity: str,
    account: str,
    payee: str,
    remark: str,
    data: dict,
) -> dict:
    data["status"] = status
    data["conterparty"] = counterparty if payee == "origin" else payee
    data["commodity"] = commodity or remark or ""
    data["account"] = account
    return data
