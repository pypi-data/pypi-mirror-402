import os
import datetime
from achive.beanparser.csv_parser import parse_csv_self
from achive.utils.utils import config

file_path = config["data"]["bean_output_path"]


def write_bean():
    (expend, invest_income) = parse_csv_self()
    date = datetime.date.today()
    year = date.year
    month = date.month
    expend_filename = f"{year}-{month:02d}.bean"
    invest_income_filename = "income.bean"
    expend_file_path = file_path.format(year, expend_filename)
    invest_income_file_path = file_path.format(year, invest_income_filename)
    if not os.path.exists(os.path.dirname(expend_file_path)):
        os.mkdir(os.path.dirname(expend_file_path))
    # "/Users/enmu/code/study/program/python/script/finance-flow/test_ex.bean"
    with open(expend_file_path, "a", encoding="utf-8") as f:
        # 检查文件是否为空
        file_is_empty = f.tell() == 0 or os.path.getsize(expend_file_path) == 0
        for index, data in enumerate(reversed(expend)):
            # 如果不是文件第一行，先写一个空行
            if not (file_is_empty and index == 0):
                f.write(os.linesep)
            f.write(data + os.linesep)

    #   "/Users/enmu/code/study/program/python/script/finance-flow/test_in.bean"
    with open(invest_income_file_path, "a", encoding="utf-8") as f:
        # 检查文件是否为空
        file_is_empty = f.tell() == 0 or os.path.getsize(invest_income_file_path) == 0
        for index, data in enumerate(reversed(invest_income)):
            # 如果不是文件第一行，先写一个空行
            if not (file_is_empty and index == 0):
                f.write(os.linesep)
            f.write(data + os.linesep)
