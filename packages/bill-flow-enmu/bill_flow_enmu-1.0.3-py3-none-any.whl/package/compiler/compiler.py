import logging

from package.config import Config
from ir import IR, Order
from package.parser.ali import alipay
from package.strategy.template.strategy import TemplateStrategy
from datetime import date
from pathlib import Path


class Compiler:
    def __init__(
        self,
        privider: str,
        target: str,
        output: str,
        config: Config,
        ir: IR,
        template_strategy: TemplateStrategy,
    ):
        self.privider = privider
        self.target = target
        self.output = output
        self.config = config
        self.ir = ir
        self.template_strategy = template_strategy

    def compile(self):
        logging.debug("start compile")

        orders: list[Order] = []
        for o in self.ir.orders:
            ignore, res_minus, res_plus, extra_account, tags = (
                alipay.get_account_and_tags(o, self.config, self.target, self.privider)
            )
            o.minus_account = res_minus
            o.plus_account = res_plus
            o.extra_account = extra_account
            o.tags = tags
            orders.append(o)

        for io in orders:
            self.template_strategy.template_parser(io)

        income = self.get_income_path()
        self.template_strategy.expense_list.reverse()
        self.template_strategy.income_list.reverse()
        self.write_bills(file_path=income, data=self.template_strategy.income_list)
        self.write_bills(
            file_path=self.output, data=self.template_strategy.expense_list
        )

    def get_income_path(self) -> str:
        today = date.today()
        # month = f"{today.month:02d}"
        year = f"{today.year}"
        home = Path().home()
        return str(home / "code" / "mandt" / "account" / "data" / year / "income.bean")

    def write_bills(self, file_path: str, data: list[str]):
        with open(file=file_path, mode="a", encoding="utf-8") as f:
            f.writelines(data)
