import logging
import pandas as pd
from ir import IR
from .ali_types import DealType, DealStatus, AliOrder
from .converter import convert_to_ir


class AliPay:
    orders: list[AliOrder]

    def __init__(self):
        self.orders = []

    def translate(self, filename: str) -> IR:
        try:
            with open(filename, "r", encoding="gbk") as f:
                lines = f.readlines()

                for i, line in enumerate(lines):
                    if "交易时间" in line:
                        start_index = i
                        break

            df = pd.read_csv(filename, skiprows=start_index, header=0, encoding="gbk")

            for row in df.to_dict("records"):
                self.translate_order(row)
                # print(row)
            ir = convert_to_ir(self.orders)

            return ir
        except FileNotFoundError as fe:
            logging.error("文件未找到")
        except Exception as e:
            logging.exception("发生未知错误")

    def translate_order(self, row: dict):
        ali_order = AliOrder(
            category=row["交易分类"],
            deal_no=str.strip(row["交易订单号"]),
            merchant_id=str.strip(row["商家订单号"]),
            peer=row["交易对方"],
            item_name=row["商品说明"],
            peer_account=row["对方账号"],
            money=row["金额"],
            pay_time=row["交易时间"],
            type=DealType(row["收/支"]).value,
            status=DealStatus(row["交易状态"]).value,
            method=row["收/付款方式"],
            target_account="",
            method_account="",
            notes=row["备注"],
            type_original=row["收/支"],
        )

        self.orders.append(ali_order)
