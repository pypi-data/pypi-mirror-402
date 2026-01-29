from .ali_types import AliOrder
from .ali_types import DealType
from ir import IR, Order, Type


def get_meta_data(o: AliOrder) -> dict:
    # 支付时间
    source = "ALiPay"
    d = {}
    if source:
        d["source"] = source
    if o.pay_time:
        d["pay_time"] = o.pay_time
    if o.deal_no:
        d["deal_no"] = o.deal_no
    if o.merchant_id:
        d["merchant_id"] = o.merchant_id
    if o.category:
        d["category"] = o.category
    if o.type_original:
        d["type"] = o.type_original
    if o.method:
        d["method"] = o.method
    if o.status:
        d["status"] = o.status
    if o.deal_no:
        d["order_id"] = o.deal_no
    return d


def convert_type(type: DealType):
    type_dict: dict[DealType, Type] = {
        DealType.SEND: Type.SEND,
        DealType.RECV: Type.RECV,
        DealType.NIL: Type.UNKNOW,
    }

    return type_dict.get(type, Type.UNKNOW)


def convert_to_ir(a_orders: list[AliOrder]):
    ir = IR()
    for o in a_orders:
        iro = Order(
            peer=o.peer,
            item=o.item_name,
            category=o.category,
            method=o.method,
            pay_time=o.pay_time,
            money=o.money,
            order_id=o.deal_no,
            type=convert_type(o.type),
            type_original=o.type_original,
        )

        iro.meta_data = get_meta_data(o)

        if o.merchant_id:
            iro.merchant_order_id = o.merchant_id

        ir.orders.append(iro)

    return ir
