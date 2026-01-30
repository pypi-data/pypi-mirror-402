"""
Typer 高级特性
==============
探索 Typer 的高级功能，包括枚举类型、上下文、自动补全等。
"""

import typer
from enum import Enum
from typing import List, Optional
from pathlib import Path

# region 示例1: 使用 Enum 限制选项值
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例1: 使用 Enum 限制选项值")
    print("=" * 50)

    # 定义枚举类型
    class LogLevel(str, Enum):
        debug = "debug"
        info = "info"
        warning = "warning"
        error = "error"

    class OutputFormat(str, Enum):
        json = "json"
        yaml = "yaml"
        text = "text"

    app = typer.Typer()

    @app.command()
    def run(
        log_level: LogLevel = typer.Option(
            LogLevel.info,
            "--log-level",
            "-l",
            help="日志级别",
            case_sensitive=False,  # 不区分大小写
        ),
        output_format: OutputFormat = typer.Option(
            OutputFormat.text,
            "--format",
            "-f",
            help="输出格式",
        ),
    ):
        """运行示例 - 使用枚举限制有效值"""
        print(f"日志级别: {log_level.value}")
        print(f"输出格式: {output_format.value}")

    # 演示
    run(LogLevel.debug, OutputFormat.json)
    print()
    run(LogLevel.error, OutputFormat.yaml)

    print("\n命令行使用方式:")
    print("  python script.py run --log-level debug -f json")
    print("  # 无效值会自动报错并显示有效选项")
    print()
# endregion

# region 示例2: 列表参数
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例2: 列表参数")
    print("=" * 50)

    app2 = typer.Typer()

    @app2.command()
    def process(
        # 接受多个位置参数
        files: List[Path] = typer.Argument(
            ...,
            help="要处理的文件列表",
        ),
        # 可以多次指定的选项
        exclude: Optional[List[str]] = typer.Option(
            None,
            "--exclude",
            "-e",
            help="要排除的模式 (可多次指定)",
        ),
    ):
        """处理多个文件"""
        print("要处理的文件:")
        for f in files:
            print(f"  - {f}")

        if exclude:
            print("排除模式:")
            for pattern in exclude:
                print(f"  - {pattern}")

    # 演示
    process([Path("file1.txt"), Path("file2.txt")], exclude=["*.log", "*.tmp"])

    print("\n命令行使用方式:")
    print("  python script.py file1.txt file2.txt file3.txt")
    print("  python script.py *.py -e __pycache__ -e .git")
    print()
# endregion

# region 示例3: 上下文对象 (Context)
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例3: 上下文对象 (Context)")
    print("=" * 50)

    app3 = typer.Typer()

    # 使用上下文在命令间共享数据
    @app3.callback()
    def main(
        ctx: typer.Context,  # 自动注入上下文
        verbose: bool = typer.Option(False, "--verbose", "-v"),
        config: str = typer.Option("config.yaml", "--config", "-c"),
    ):
        """主程序 - 设置全局状态"""
        # 使用 ctx.obj 存储共享数据
        ctx.obj = {
            "verbose": verbose,
            "config": config,
        }
        if verbose:
            print(f"[详细] 配置文件: {config}")

    @app3.command()
    def status(ctx: typer.Context):
        """显示状态 - 从上下文获取配置"""
        settings = ctx.obj
        print(f"当前配置: {settings['config']}")
        if settings["verbose"]:
            print("[详细] 检查系统状态...")
        print("系统正常运行")

    @app3.command()
    def deploy(
        ctx: typer.Context,
        target: str = typer.Argument(..., help="部署目标"),
    ):
        """部署应用"""
        settings = ctx.obj
        if settings["verbose"]:
            print(f"[详细] 部署到 {target}")
        print(f"使用配置 {settings['config']} 部署到 {target}")

    # 演示 (模拟上下文)
    print("上下文使用示例:")
    print("""
    @app.callback()
    def main(ctx: typer.Context, verbose: bool = False):
        ctx.obj = {"verbose": verbose}

    @app.command()
    def status(ctx: typer.Context):
        if ctx.obj["verbose"]:
            print("详细模式")
""")

    print("\n命令行使用方式:")
    print("  python script.py --verbose status")
    print("  python script.py -c prod.yaml deploy production")
    print()
# endregion

# region 示例4: 错误处理与退出码
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例4: 错误处理与退出码")
    print("=" * 50)

    app4 = typer.Typer()

    @app4.command()
    def divide(a: float, b: float):
        """除法运算 - 演示错误处理"""
        if b == 0:
            # 使用 typer.Exit 退出并设置退出码
            typer.secho("错误: 除数不能为零!", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)

        result = a / b
        typer.secho(f"结果: {result}", fg=typer.colors.GREEN)

    @app4.command()
    def danger_zone(confirm: bool = typer.Option(False, "--yes", "-y")):
        """危险操作 - 演示中止"""
        if not confirm:
            # Abort 会打印 "Aborted." 并退出
            raise typer.Abort()

        typer.secho("执行危险操作...", fg=typer.colors.RED)

    # 演示
    import click.exceptions

    print("正常除法:")
    try:
        divide(10, 2)
    except click.exceptions.Exit:
        pass

    print("\n除以零:")
    try:
        divide(10, 0)
    except click.exceptions.Exit as e:
        print(f"(退出码: {e.exit_code})")

    print("\n错误处理代码:")
    print("""
    # 正常退出
    raise typer.Exit()          # 退出码 0

    # 错误退出
    raise typer.Exit(code=1)    # 退出码 1

    # 用户中止
    raise typer.Abort()         # 打印 "Aborted."

    # 友好错误消息
    typer.secho("错误信息", fg=typer.colors.RED, err=True)
""")

    print()
# endregion

# region 示例5: 自动补全
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例5: 自动补全")
    print("=" * 50)

    print("Typer 支持 shell 自动补全功能:")

    print("""
    # 安装补全脚本 (需要安装 typer[all])

    # Bash
    python script.py --install-completion bash

    # Zsh
    python script.py --install-completion zsh

    # Fish
    python script.py --install-completion fish

    # PowerShell
    python script.py --install-completion powershell

    # 也可以只显示脚本不安装
    python script.py --show-completion bash
""")

    print("自定义补全函数:")
    print('''
    def complete_name(incomplete: str) -> List[str]:
        """返回可能的补全选项"""
        names = ["alice", "bob", "charlie"]
        return [n for n in names if n.startswith(incomplete)]

    @app.command()
    def greet(
        name: str = typer.Argument(
            ...,
            autocompletion=complete_name,  # 自定义补全
        ),
    ):
        print(f"Hello, {name}!")
''')

    print()
# endregion

# region 示例6: 测试 Typer 应用
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例6: 测试 Typer 应用")
    print("=" * 50)

    from typer.testing import CliRunner

    # 创建一个简单的应用
    test_app = typer.Typer()

    @test_app.command()
    def greet(name: str):
        """问候"""
        typer.echo(f"Hello, {name}!")

    @test_app.command()
    def add(a: int, b: int):
        """加法"""
        typer.echo(f"Result: {a + b}")

    # 使用 CliRunner 测试
    runner = CliRunner()

    print("测试 greet 命令:")
    result = runner.invoke(test_app, ["greet", "World"])
    print(f"  输出: {result.output.strip()}")
    print(f"  退出码: {result.exit_code}")

    print("\n测试 add 命令:")
    result = runner.invoke(test_app, ["add", "5", "3"])
    print(f"  输出: {result.output.strip()}")
    print(f"  退出码: {result.exit_code}")

    print("\n完整测试代码示例:")
    print("""
    from typer.testing import CliRunner
    from myapp import app

    runner = CliRunner()

    def test_greet():
        result = runner.invoke(app, ["greet", "Alice"])
        assert result.exit_code == 0
        assert "Hello, Alice" in result.output

    def test_add():
        result = runner.invoke(app, ["add", "10", "20"])
        assert result.exit_code == 0
        assert "30" in result.output
""")

    print()
# endregion
