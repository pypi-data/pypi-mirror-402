import typer
from .root import app
from package.config import get_config, Config
from typing_extensions import Annotated
from provider import get_provider
from package.compiler.compiler import Compiler
from package.strategy.template.normal import NormalStrategy


@app.command()
def trans(
    provider: Annotated[
        str, typer.Option("--provider", "-p", help="Bills provder")
    ] = "alipay",
    target: Annotated[
        str, typer.Option("--target", "-t", help="Target Bill")
    ] = "beancount",
    source: Annotated[str, typer.Option("--source", "-s", help="source file")] = "",
    output: Annotated[
        str, typer.Option("--output", "-o", help="output_fill")
    ] = "defalut.bean",
):
    p = get_provider(provider)
    s = p.translate(source)
    config_content = get_config()
    config = Config.model_validate(config_content)
    Compiler(provider, "beancount", output, config, s, NormalStrategy()).compile()
