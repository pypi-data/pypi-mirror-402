from typing import Callable
from achive.rules.rules import invest_rules, repay_rules, transfer_rules, refund_rules
import re
from typing import Optional
from achive.cache.refund_cache_manager import order_cache


def parse_income_account(product, amount) -> Optional[dict]:
    """收入策略"""
    data = {}
    for match_type, parttern, type, account in invest_rules:
        if match_type == "regex":
            if re.search(parttern, product):
                if type == "income":
                    data["account"] = account
                    data["amount"] = -amount
                    return data
    return None


def parse_repayment_account(product, amount) -> Optional[dict]:
    """还款策略"""
    data = {}
    for match_type, parttern, type, account in repay_rules:
        if match_type == "regex":
            if re.search(parttern, product) and type == "repay":
                data["account"] = account
                data["amount"] = amount
                return data
    return None


def parse_transfer_account(product, amount) -> Optional[dict]:
    """转账策略"""
    data = {}
    for match_type, parttern, type, account in transfer_rules:
        if match_type == "regex":
            if re.search(parttern, product) and type == "transfer_into":
                data["account"] = account
                data["amount"] = amount
                return data
            if re.search(parttern, product) and type == "transfer_out":
                data["account"] = account
                data["amount"] = -amount
                return data
    return None


def parse_refund_account(product, amount) -> Optional[dict]:
    """退款策略"""
    data = {}
    for match_type, parttern, type in refund_rules:
        if match_type == "regex":
            if re.search(parttern, product) and type == "refund":
                if re.search("^退款-商户单号", product):
                    data["account"] = (
                        order_cache.get_account(product.replace("退款-商户单号", ""))
                        or "Assert:unknow"
                    )
                    data["amount"] = -amount
                return data
    return None


class Irt:
    def __init__(self, product: str, amount: str):
        self.product = product
        self.amount = amount

    def get_irt_account(self, get_account: Callable[[str, str], dict]) -> dict:
        return get_account(self.product, self.amount)
