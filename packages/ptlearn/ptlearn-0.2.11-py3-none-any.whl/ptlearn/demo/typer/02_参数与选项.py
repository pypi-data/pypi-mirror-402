"""
Typer 参数与选项详解
====================
深入了解 Typer 中 Argument 和 Option 的区别与高级用法。

- Argument: 位置参数，按顺序传递，通常是必需的
- Option: 命名选项，使用 --name 形式，通常是可选的
"""

from typing import Optional
from pathlib import Path

import typer

# region 示例1: 使用 typer.Argument 定义参数
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例1: 使用 typer.Argument 定义参数")
    print("=" * 50)

    app = typer.Typer()

    @app.command()
    def process_file(
        # 使用 typer.Argument 可以添加更多元数据
        filename: str = typer.Argument(
            ...,  # ... 表示必需参数
            help="要处理的文件名",
            metavar="FILE",  # 在帮助文档中显示的参数名
        ),
        encoding: str = typer.Argument(
            "utf-8",  # 默认值
            help="文件编码格式",
        ),
    ):
        """处理指定的文件"""
        print(f"处理文件: {filename}")
        print(f"使用编码: {encoding}")

    # 演示
    process_file("data.txt")
    process_file("data.txt", "gbk")

    print("\n命令行使用方式:")
    print("  python script.py data.txt")
    print("  python script.py data.txt gbk")
    print()
# endregion

# region 示例2: 使用 typer.Option 定义选项
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例2: 使用 typer.Option 定义选项")
    print("=" * 50)

    app2 = typer.Typer()

    @app2.command()
    def search(
        query: str = typer.Argument(..., help="搜索关键词"),
        # Option 提供更多配置选项
        case_sensitive: bool = typer.Option(
            False,
            "--case-sensitive",
            "-c",  # 短选项
            help="区分大小写",
        ),
        max_results: int = typer.Option(
            10,
            "--max",
            "-m",
            help="最大结果数量",
            min=1,  # 最小值验证
            max=100,  # 最大值验证
        ),
        output_format: str = typer.Option(
            "text",
            "--format",
            "-f",
            help="输出格式: text 或 json",
        ),
    ):
        """执行搜索操作"""
        print(f"搜索: {query}")
        print(f"区分大小写: {case_sensitive}")
        print(f"最大结果: {max_results}")
        print(f"输出格式: {output_format}")

    # 演示
    search("python")
    print()
    search("Python", case_sensitive=True, max_results=5, output_format="json")

    print("\n命令行使用方式:")
    print("  python script.py python")
    print("  python script.py Python -c --max 5 -f json")
    print()
# endregion

# region 示例3: 布尔选项的三种形式
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例3: 布尔选项的三种形式")
    print("=" * 50)

    app3 = typer.Typer()

    @app3.command()
    def demo_bool(
        # 形式1: 标准 --flag / --no-flag
        verbose: bool = typer.Option(False, "--verbose/--quiet", "-v/-q"),
        # 形式2: 只有开启选项 (is_flag=True)
        debug: bool = typer.Option(False, "--debug", "-d", is_flag=True),
        # 形式3: 自定义正反选项名
        colored: bool = typer.Option(
            True,
            "--color/--no-color",
            help="是否使用彩色输出",
        ),
    ):
        """演示布尔选项的不同形式"""
        print(f"详细模式: {verbose}")
        print(f"调试模式: {debug}")
        print(f"彩色输出: {colored}")

    # 演示
    print("默认值:")
    demo_bool()

    print("\n开启所有选项:")
    demo_bool(verbose=True, debug=True, colored=True)

    print("\n命令行使用方式:")
    print("  python script.py --verbose --debug --color")
    print("  python script.py -v -d")
    print("  python script.py --quiet --no-color")
    print()
# endregion

# region 示例4: 可选参数 (Optional 类型)
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例4: 可选参数 (Optional 类型)")
    print("=" * 50)

    app4 = typer.Typer()

    @app4.command()
    def greet(
        name: str = typer.Argument(..., help="你的名字"),
        # 使用 Optional 表示参数可以为 None
        nickname: Optional[str] = typer.Option(
            None,
            "--nickname",
            "-n",
            help="你的昵称 (可选)",
        ),
        age: Optional[int] = typer.Option(
            None,
            "--age",
            "-a",
            help="你的年龄 (可选)",
        ),
    ):
        """个性化问候"""
        greeting = f"你好, {name}"
        if nickname:
            greeting += f" ({nickname})"
        greeting += "!"
        print(greeting)

        if age is not None:
            print(f"你今年 {age} 岁")

    # 演示
    greet("张三")
    print()
    greet("李四", nickname="小李", age=25)

    print("\n命令行使用方式:")
    print("  python script.py 张三")
    print("  python script.py 李四 -n 小李 -a 25")
    print()
# endregion

# region 示例5: Path 类型参数
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例5: Path 类型参数")
    print("=" * 50)

    app5 = typer.Typer()

    @app5.command()
    def file_info(
        # Typer 对 Path 类型有特殊支持
        filepath: Path = typer.Argument(
            ...,
            help="文件路径",
            exists=False,  # 设为 True 会验证文件必须存在
            file_okay=True,  # 允许是文件
            dir_okay=False,  # 不允许是目录
            readable=False,  # 设为 True 会验证可读
            resolve_path=True,  # 自动解析为绝对路径
        ),
        output_dir: Optional[Path] = typer.Option(
            None,
            "--output",
            "-o",
            help="输出目录",
            file_okay=False,
            dir_okay=True,
        ),
    ):
        """显示文件信息"""
        print(f"文件路径: {filepath}")
        print(f"文件名: {filepath.name}")
        print(f"扩展名: {filepath.suffix}")
        print(f"父目录: {filepath.parent}")

        if output_dir:
            print(f"输出目录: {output_dir}")

    # 演示 (注意: 这里的路径不需要真实存在)
    file_info(Path("example/data.json"))
    print()
    file_info(Path("report.pdf"), output_dir=Path("./output"))

    print("\n命令行使用方式:")
    print("  python script.py example/data.json")
    print("  python script.py report.pdf -o ./output")
    print()
# endregion
