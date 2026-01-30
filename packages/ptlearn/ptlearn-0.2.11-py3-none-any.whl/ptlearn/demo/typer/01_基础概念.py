"""
Typer 基础概念
==============
Typer 是一个基于 Python 类型提示构建命令行接口 (CLI) 的现代化库。
它由 FastAPI 的作者开发，具有自动补全、自动生成帮助文档等特性。

适用版本: Python 3.7+
依赖安装: pip install typer[all]  # [all] 包含 rich 支持和自动补全
"""

import typer

# region 示例1: 最简单的 Typer 应用
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例1: 最简单的 Typer 应用")
    print("=" * 50)

    # 创建 Typer 应用实例
    app = typer.Typer()

    # 使用装饰器将函数注册为命令
    @app.command()
    def hello():
        """向世界打个招呼"""
        print("Hello, World!")

    # 注意: 实际使用时需要调用 app() 来运行
    # 这里我们直接调用函数来演示效果
    hello()

    print("\n提示: 在实际 CLI 脚本中，你需要在文件末尾添加:")
    print('if __name__ == "__main__":')
    print("    app()")
    print()
# endregion

# region 示例2: 带参数的命令
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例2: 带参数的命令")
    print("=" * 50)

    app2 = typer.Typer()

    @app2.command()
    def greet(name: str):
        """
        向指定的人打招呼。

        参数会自动成为必需的命令行参数。
        Typer 会根据类型提示自动进行类型转换和验证。
        """
        print(f"Hello, {name}!")

    # 直接调用演示
    greet("张三")
    greet("Alice")

    print("\n命令行使用方式: python script.py 张三")
    print()
# endregion

# region 示例3: 带默认值的可选参数
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例3: 带默认值的可选参数")
    print("=" * 50)

    app3 = typer.Typer()

    @app3.command()
    def greet_formal(
        name: str,
        formal: bool = False,  # 带默认值的参数自动变为可选参数
        times: int = 1,  # 整数类型的可选参数
    ):
        """
        向指定的人打招呼，支持正式/非正式模式。

        带默认值的参数会自动成为命令行选项 (--formal, --times)。
        """
        greeting = "您好" if formal else "嗨"
        for _ in range(times):
            print(f"{greeting}, {name}!")

    # 演示不同调用方式
    print("默认模式:")
    greet_formal("李四")

    print("\n正式模式 (--formal):")
    greet_formal("李四", formal=True)

    print("\n重复3次 (--times 3):")
    greet_formal("李四", times=3)

    print("\n命令行使用方式:")
    print("  python script.py 李四")
    print("  python script.py 李四 --formal")
    print("  python script.py 李四 --times 3")
    print()
# endregion

# region 示例4: 类型自动转换
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例4: 类型自动转换")
    print("=" * 50)

    app4 = typer.Typer()

    @app4.command()
    def calculate(
        a: int,
        b: int,
        operation: str = "add",
    ):
        """
        Typer 会根据类型提示自动转换命令行字符串参数。

        支持的类型包括: str, int, float, bool, Path 等。
        """
        if operation == "add":
            result = a + b
            print(f"{a} + {b} = {result}")
        elif operation == "multiply":
            result = a * b
            print(f"{a} × {b} = {result}")
        else:
            print(f"未知操作: {operation}")

    # 演示
    calculate(10, 20)
    calculate(5, 3, "multiply")

    print("\n命令行使用方式:")
    print("  python script.py 10 20")
    print("  python script.py 5 3 --operation multiply")
    print()
# endregion

# region 示例5: 获取自动生成的帮助信息
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例5: 自动生成的帮助信息")
    print("=" * 50)

    print("""
Typer 会自动从函数的 docstring 和类型提示生成帮助文档。

运行命令时使用 --help 参数可以查看帮助:

    $ python script.py --help

    Usage: script.py [OPTIONS] NAME

    向指定的人打招呼。

    Arguments:
      NAME  [required]

    Options:
      --formal / --no-formal  [default: no-formal]
      --times INTEGER         [default: 1]
      --help                  Show this message and exit.

这是 Typer 的一大优势: 零配置即可获得专业的帮助文档!
""")
# endregion
