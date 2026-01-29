import re
import os
from typing import Any, Dict, Optional

from achive.rules.rules import payment_method_rules
from achive.beanparser.irt_strategy import (
    Irt,
    parse_income_account,
    parse_repayment_account,
    parse_transfer_account,
    parse_refund_account,
)
from achive.utils.utils import get_parser, formmat_data, get_file_name, get_column, config
from achive.beanparser.match import match_by_counterparty, match_by_comm

ALI_ZIP_FOLDER = config["data"]["ali_zip_folder"]
WECHAT_ZIP_FOLDER = config["data"]["wechat_zip_foler"]
DATA_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}")

strategies = [
    parse_income_account,
    parse_repayment_account,
    parse_transfer_account,
    parse_refund_account,
]

ACCOUNT_WIDTH = 47
AMOUNT_WIDTH = 10


def parse_csv_self() -> tuple:
    ps = []
    file_name = get_file_name()
    ali_csv_path = os.path.join(ALI_ZIP_FOLDER, file_name)
    wechat_csv_path = os.path.join(WECHAT_ZIP_FOLDER, file_name)
    ps.append(ali_csv_path)
    ps.append(wechat_csv_path)
    return parse_csv(ps)


def parse_csv(csv_paths: list) -> tuple:
    DATA_EXPEND_LIST = []
    DATA_INVEST_ICOME_LIST = []
    for csv_path in csv_paths:
        df = get_parser(csv_path)
        for _, row in df.iterrows():
            (
                date,
                counterparty,
                product,
                amount,
                ietypes,
                payment_method,
                remark,
                status,
            ) = get_column(row)
            if ietypes == "支出":
                data = parse_expend_account(counterparty, product, remark, amount, date)
                if not data:
                    set_abnormal_data(data)  # type: ignore
                # 获取账户
                data["payment"] = payment_method_rules.get(payment_method, f"Assets:Unknown:{payment_method}")  # type: ignore
                data["amount"] = amount  # type: ignore
                data["date"] = date  # type: ignore
                data_str = formmat_data(data)  # type: ignore
                DATA_EXPEND_LIST.append(data_str)
            elif ietypes == "不计收支" and "成功" in status:
                irt_context = Irt(product, amount)
                final_data: Optional[Dict[str, Any]] = None
                for s in strategies:
                    result = irt_context.get_irt_account(s)  # type: ignore
                    if result is not None:
                        final_data = result
                        break

                if final_data is None:
                    final_data = {
                        "account": "Assets:Unknown:Fixme",
                        "amount": amount,
                        "status": "!",
                    }
                final_data["date"] = date
                final_data["status"] = "*"
                final_data["conterparty"] = counterparty
                final_data["commodity"] = product
                final_data["payment"] = payment_method_rules[payment_method]
                data_str = formmat_data(final_data)
                DATA_INVEST_ICOME_LIST.append(data_str)
    return DATA_EXPEND_LIST, DATA_INVEST_ICOME_LIST


def parse_expend_account(counterparty, product, remark, amount, date) -> Optional[dict]:
    data = {}
    if match_by_counterparty(remark, product, counterparty, counterparty, data):
        return data
    if match_by_comm(product, counterparty, remark, data):
        return data
    return data


def set_abnormal_data(data: dict):
    if data is None:
        return
    data["status"] = "!"
    data["conterparty"] = "Unknow"
    data["commodity"] = ""
    data["account"] = "Expenses:Unknow:Fixme"
