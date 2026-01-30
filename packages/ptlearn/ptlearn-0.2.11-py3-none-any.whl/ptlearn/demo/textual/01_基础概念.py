"""
Textual 基础概念
================
Textual 是一个现代化的 Python TUI 框架，用于在终端中构建丰富的用户界面。
本文件介绍 Textual 的核心概念：App、Widget 和基本布局。

要求: Python 3.8+, textual 库
安装: pip install textual 或 uv add textual
"""

from textual.app import App, ComposeResult
from textual.widgets import Static, Label, Header, Footer

# region 示例1: 最简单的 Textual 应用
if True:  # 改为 False 可跳过此示例
    """
    每个 Textual 应用都继承自 App 类
    compose() 方法定义界面组件
    run() 方法启动应用
    按 Ctrl+C 或 q 退出应用
    """

    class HelloApp(App):
        """最简单的 Textual 应用"""

        def compose(self) -> ComposeResult:
            # yield 返回要显示的组件
            yield Static("你好，Textual！按 q 退出")

    # 运行应用
    print("示例1: 最简单的应用")
    print("=" * 40)
    app = HelloApp()
    app.run()
# endregion

# region 示例2: 使用 Label 组件显示文本
if False:  # 改为 True 可运行此示例
    """
    Label 是用于显示文本的基础组件
    支持 Rich 标记语法来设置样式
    """

    class LabelApp(App):
        def compose(self) -> ComposeResult:
            # Label 支持 Rich 标记语法
            yield Label("普通文本")
            yield Label("[bold]粗体文本[/bold]")
            yield Label("[italic red]红色斜体[/italic red]")
            yield Label("[bold blue on white]蓝字白底[/bold blue on white]")
            yield Label("[underline]下划线文本[/underline]")

    print("示例2: Label 组件与 Rich 标记")
    print("=" * 40)
    app = LabelApp()
    app.run()
# endregion

# region 示例3: Header 和 Footer 组件
if False:  # 改为 True 可运行此示例
    """
    Header: 显示应用标题栏
    Footer: 显示快捷键提示栏
    这两个组件让应用看起来更专业
    """

    class HeaderFooterApp(App):
        # 设置应用标题（显示在 Header 中）
        TITLE = "我的第一个 TUI 应用"
        # 设置副标题
        SUB_TITLE = "学习 Textual"

        # 定义快捷键绑定（显示在 Footer 中）
        BINDINGS = [
            ("q", "quit", "退出"),
            ("d", "toggle_dark", "切换主题"),
        ]

        def compose(self) -> ComposeResult:
            yield Header()  # 顶部标题栏
            yield Static("主要内容区域\n\n按 d 切换深色/浅色主题")
            yield Footer()  # 底部快捷键栏

        def action_toggle_dark(self) -> None:
            """切换深色模式"""
            self.theme = "textual-light" if self.theme == "textual-dark" else "textual-dark"

    print("示例3: Header 和 Footer")
    print("=" * 40)
    app = HeaderFooterApp()
    app.run()
# endregion

# region 示例4: 自定义 Static 组件样式
if False:  # 改为 True 可运行此示例
    """
    Static 组件可以通过 CSS 类来设置样式
    Textual 使用类似 CSS 的语法来定义样式
    """

    class StyledApp(App):
        # 内联 CSS 样式定义
        CSS = """
        .box {
            background: $primary;
            color: $text;
            padding: 1 2;
            margin: 1;
            border: solid green;
        }
        
        .highlight {
            background: yellow;
            color: black;
            text-style: bold;
        }
        """

        def compose(self) -> ComposeResult:
            yield Header()
            # classes 参数指定 CSS 类
            yield Static("这是一个带边框的盒子", classes="box")
            yield Static("这是高亮文本", classes="highlight")
            yield Static("普通文本，没有特殊样式")
            yield Footer()

    print("示例4: CSS 样式")
    print("=" * 40)
    app = StyledApp()
    app.run()
# endregion

# region 示例5: 应用生命周期方法
if False:  # 改为 True 可运行此示例
    """
    Textual 应用有多个生命周期方法：
    - on_mount: 应用挂载后调用
    - on_ready: 应用准备就绪后调用
    这些方法可用于初始化操作
    """

    class LifecycleApp(App):
        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)  # 显示时钟
            yield Static("观察控制台输出了解生命周期", id="content")
            yield Footer()

        def on_mount(self) -> None:
            """应用挂载时调用"""
            self.log("on_mount: 应用已挂载")
            # 可以在这里进行初始化操作

        def on_ready(self) -> None:
            """应用准备就绪时调用"""
            self.log("on_ready: 应用已就绪")

    print("示例5: 生命周期方法")
    print("=" * 40)
    app = LifecycleApp()
    app.run()
# endregion
