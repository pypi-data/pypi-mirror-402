import logging

from ir.ir import IR
from provider.ali.ali_types import DealStatus



def post_process(ir: IR) -> IR:
    orders = []

    for i,o in enumerate(ir.orders):
        if o.meta_data["status"] == "退款成功" and o.category == "退款":
            # 继续循环找到对应的退款
            for j,ori in enumerate(ir.orders):
                if i == j:
                    continue

                omi = o.meta_data.get("order_id")
                omj = o.meta_data.get("order_id")
                if omi.startswith(omj) and o.money == ori.money:
                    o.meta_data["useless"] = "true"
                    ori.meta_data["useless"] = "true"
        if o.meta_data["status"] == DealStatus.CLOSE and o.meta_data["type"] == "不计收支":
            o.meta_data["useless"] = "true"
            logging.info("订单取消")


    for v in ir.orders:
        if v.meta_data["useless"] != "true":
            orders.append(v)
    ir.orders = orders
    return ir
