"""
Typer 输入输出与交互
====================
学习如何使用 Typer 进行用户交互、彩色输出和进度显示。

注意: Typer 集成了 Rich 库，提供丰富的终端输出功能。
"""

import typer

# region 示例1: 彩色输出
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例1: 彩色输出")
    print("=" * 50)

    # typer.echo 是 print 的增强版，支持一些额外功能
    typer.echo("这是普通输出")

    # typer.secho 支持样式化输出 (style + echo)
    typer.secho("这是绿色文本", fg=typer.colors.GREEN)
    typer.secho("这是红色加粗文本", fg=typer.colors.RED, bold=True)
    typer.secho("这是蓝色背景白色文本", fg=typer.colors.WHITE, bg=typer.colors.BLUE)
    typer.secho("这是下划线文本", underline=True)

    print("\n可用的颜色常量:")
    colors = [
        "BLACK",
        "RED",
        "GREEN",
        "YELLOW",
        "BLUE",
        "MAGENTA",
        "CYAN",
        "WHITE",
        "BRIGHT_BLACK",
        "BRIGHT_RED",
        "BRIGHT_GREEN",
        "BRIGHT_YELLOW",
        "BRIGHT_BLUE",
        "BRIGHT_MAGENTA",
        "BRIGHT_CYAN",
        "BRIGHT_WHITE",
    ]
    print(f"  typer.colors.{', '.join(colors[:4])}, ...")

    print()
# endregion

# region 示例2: 使用 typer.style 组合样式
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例2: 使用 typer.style 组合样式")
    print("=" * 50)

    # 可以先创建样式化的字符串，再输出
    success_msg = typer.style("成功", fg=typer.colors.GREEN, bold=True)
    error_msg = typer.style("失败", fg=typer.colors.RED, bold=True)
    warning_msg = typer.style("警告", fg=typer.colors.YELLOW)

    typer.echo(f"操作状态: {success_msg}")
    typer.echo(f"操作状态: {error_msg}")
    typer.echo(f"操作状态: {warning_msg}")

    # 在一行中混合多种样式
    name = typer.style("张三", fg=typer.colors.CYAN, bold=True)
    action = typer.style("登录", fg=typer.colors.GREEN)
    typer.echo(f"用户 {name} 已 {action} 系统")

    print()
# endregion

# region 示例3: 用户输入提示
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例3: 用户输入提示 (模拟)")
    print("=" * 50)

    # typer.prompt 用于获取用户输入
    # 这里我们只展示语法，不实际调用（需要交互）

    print("typer.prompt 示例代码:")
    print("""
    # 基本输入
    name = typer.prompt("请输入你的名字")

    # 带默认值
    age = typer.prompt("请输入年龄", default="18")

    # 隐藏输入 (用于密码)
    password = typer.prompt("请输入密码", hide_input=True)

    # 类型转换
    count = typer.prompt("数量", type=int)

    # 确认输入
    password = typer.prompt("密码", hide_input=True, confirmation_prompt=True)
""")

    # typer.confirm 用于是/否确认
    print("\ntyper.confirm 示例代码:")
    print("""
    # 基本确认
    if typer.confirm("确定要继续吗?"):
        typer.echo("继续执行...")
    else:
        typer.echo("操作已取消")

    # 默认为 Yes
    proceed = typer.confirm("是否继续?", default=True)

    # 选择 No 时自动退出
    typer.confirm("删除所有数据?", abort=True)  # 选 No 会抛出 Abort
""")

    print()
# endregion

# region 示例4: 命令行参数中使用 prompt
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例4: 命令行参数中使用 prompt")
    print("=" * 50)

    app = typer.Typer()

    @app.command()
    def login(
        username: str = typer.Option(
            ...,  # 必需
            prompt=True,  # 如果未提供，会提示输入
        ),
        password: str = typer.Option(
            ...,
            prompt=True,
            hide_input=True,  # 隐藏输入
            confirmation_prompt=True,  # 需要确认
        ),
    ):
        """用户登录 - 未提供参数时会提示输入"""
        print(f"用户 {username} 登录中...")
        print(f"密码长度: {len(password)}")

    print("命令定义示例:")
    print("""
    @app.command()
    def login(
        username: str = typer.Option(..., prompt=True),
        password: str = typer.Option(
            ...,
            prompt=True,
            hide_input=True,
            confirmation_prompt=True,
        ),
    ):
        ...
""")

    print("\n使用方式:")
    print("  python script.py login")
    print("  # 未提供 --username 和 --password 时会交互式提示输入")
    print("  python script.py login --username admin --password secret")
    print("  # 直接提供参数则跳过提示")

    print()
# endregion

# region 示例5: 进度条与状态指示
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例5: 进度条与状态指示")
    print("=" * 50)

    import time

    # typer.progressbar 提供进度条功能
    print("进度条演示 (快速):")

    # 模拟一些数据
    data = range(10)

    with typer.progressbar(data, label="处理中") as progress:
        for item in progress:
            # 模拟处理
            time.sleep(0.05)

    print("处理完成!")

    print("\n进度条代码示例:")
    print("""
    # 基本进度条
    with typer.progressbar(items) as progress:
        for item in progress:
            process(item)

    # 带标签和长度
    with typer.progressbar(range(100), label="下载中", length=100) as progress:
        for i in progress:
            download_chunk(i)

    # 手动更新进度
    with typer.progressbar(length=1000, label="传输") as progress:
        while not done:
            bytes_sent = send_data()
            progress.update(bytes_sent)
""")

    print()
# endregion

# region 示例6: 启动外部编辑器
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例6: 启动外部应用")
    print("=" * 50)

    print("Typer 提供了几个实用的系统交互函数:")

    print("""
    # 启动默认编辑器编辑文本
    message = typer.edit("请输入你的消息")

    # 编辑指定文件
    typer.edit(filename="config.yaml")

    # 指定编辑器
    typer.edit("内容", editor="code")  # 使用 VS Code

    # 在浏览器中打开 URL
    typer.launch("https://typer.tiangolo.com")

    # 打开文件 (使用系统默认程序)
    typer.launch("report.pdf")

    # 定位到文件所在目录
    typer.launch("output/data.csv", locate=True)
""")

    print()
# endregion
