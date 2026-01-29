import json
import os
import re
from datetime import datetime, date
import pandas as pd


def load_config():
    # Helper to find config.json relative to this file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    config_path = os.path.join(project_root, "config.json")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found at {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


config = load_config()

DATA_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}")
ACCOUNT_WIDTH = 47
AMOUNT_WIDTH = 10

"""
获取数据行号
"""


# def get_row_number(file) -> int:
#     with open(file, "r", encoding="utf-8") as f:
#         lines = f.readlines()
#         for i, line in enumerate(lines):
#             line.strip()
#             if DATA_PATTERN.match(line):
#                 return i - 1
#     return -1


def get_row_number(file_path) -> int:
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            # 直接找表头里的核心字段，比正则匹配数据更稳
            if "交易时间" in line:
                return i
    return -1


def get_parser(file_path):
    blank_row = get_row_number(file_path)
    if blank_row == -1:
        raise ValueError("未找到有效的账单表头，请检查文件格式或编码")
    df = pd.read_csv(file_path, encoding="utf-8", skiprows=blank_row)  # type: ignore
    # 清洗操作：去除除了表头之外可能多余的空行或干扰
    # 有时候支付宝末尾会有统计行，可能需要过滤掉
    if not df.empty:
        # 确保'交易时间'列存在且看起来像时间（过滤掉底部的统计文字）
        df = df[df["交易时间"].str.contains(r"^\d{4}-\d{2}-\d{2}", na=False)]
    df = df.fillna("未知")
    return df


"""
整理数据
"""


def formmat_data(data: dict) -> str:
    if data.get("commodity"):
        comm_str = f'"{data["commodity"]}"'
    else:
        comm_str = ""
    line1 = f'{data["date"]} {data["status"]} "{data["conterparty"]}" {comm_str}'
    line1 = line1.rstrip()
    # line1 = f'{data["date"]} {data["status"]} "{data["conterparty"]}"   "{data["commodity"]}" if not data.get("commodity") else ""'
    line2 = f'    {data["account"]:<{ACCOUNT_WIDTH}} {data["amount"]:>{AMOUNT_WIDTH}.2f} CNY'
    line3 = f'    {data["payment"]:<{ACCOUNT_WIDTH}} {-data["amount"]:>{AMOUNT_WIDTH}.2f} CNY'
    return f"{line1}\n{line2}\n{line3}"


def get_file_name() -> str:
    # return f"{str(datetime.today()).split(' ')[0]}.csv"
    return f"{date.today()}.csv"


def get_column(row) -> tuple:
    # 获取时间
    date = row["交易时间"].split(" ")[0]
    # 获取交易对方
    counterparty = row["交易对方"]
    # 获取商品说明
    product = row["商品说明"]
    # 获取金额
    amount = row["金额"]
    # 获取收支类型
    ietypes = row["收/支"]
    payment_method = row["收/付款方式"]
    remark = row["备注"]
    status = row["交易状态"]

    return (
        date,
        counterparty,
        product,
        amount,
        ietypes,
        payment_method,
        remark,
        status,
    )


def read_messy_excel(file_path):
    # 1. 先不带 header 读取整个文件，当成普通数据块
    raw_df = pd.read_excel(file_path, header=None)

    # 2. 找到包含 "交易时间" 这个关键词的行号
    # idxmax() 会返回第一个满足条件的索引
    start_row_index = raw_df[raw_df[0] == "交易时间"].index[0]

    print(f"检测到有效数据从第 {start_row_index + 1} 行开始...")

    # 3. 重新读取，这次指定 header 位置
    df = pd.read_excel(file_path, header=start_row_index)  # type: ignore
    return df
