"""
Textual 布局系统
================
Textual 提供了强大的布局系统，支持水平、垂直、网格等多种布局方式。
本文件介绍 Container、Horizontal、Vertical 和 Grid 布局。

要求: Python 3.8+, textual 库
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, Grid, ScrollableContainer
from textual.widgets import Static, Header, Footer, Label

# region 示例1: Vertical 垂直布局
if True:  # 改为 False 可跳过此示例
    """
    Vertical 容器将子组件垂直排列
    类似于 CSS 的 flex-direction: column
    """

    class VerticalApp(App):
        CSS = """
        .box {
            height: 3;
            background: $primary;
            margin: 1;
            padding: 1;
        }
        """

        def compose(self) -> ComposeResult:
            yield Header()
            # Vertical 容器内的组件垂直排列
            with Vertical():
                yield Static("第一行", classes="box")
                yield Static("第二行", classes="box")
                yield Static("第三行", classes="box")
            yield Footer()

    print("示例1: Vertical 垂直布局")
    print("=" * 40)
    app = VerticalApp()
    app.run()
# endregion

# region 示例2: Horizontal 水平布局
if False:  # 改为 True 可运行此示例
    """
    Horizontal 容器将子组件水平排列
    类似于 CSS 的 flex-direction: row
    """

    class HorizontalApp(App):
        CSS = """
        .box {
            width: 1fr;
            height: 100%;
            background: $primary;
            margin: 1;
            padding: 1;
        }
        
        .red { background: red; }
        .green { background: green; }
        .blue { background: blue; }
        """

        def compose(self) -> ComposeResult:
            yield Header()
            # Horizontal 容器内的组件水平排列
            with Horizontal():
                yield Static("左", classes="box red")
                yield Static("中", classes="box green")
                yield Static("右", classes="box blue")
            yield Footer()

    print("示例2: Horizontal 水平布局")
    print("=" * 40)
    app = HorizontalApp()
    app.run()
# endregion

# region 示例3: 嵌套布局
if False:  # 改为 True 可运行此示例
    """
    布局容器可以嵌套使用
    实现复杂的界面结构
    """

    class NestedLayoutApp(App):
        CSS = """
        .sidebar {
            width: 20;
            background: $primary-darken-2;
            padding: 1;
        }
        
        .main {
            width: 1fr;
            background: $surface;
            padding: 1;
        }
        
        .top-bar {
            height: 3;
            background: $primary;
            padding: 1;
        }
        
        .content {
            height: 1fr;
            background: $surface-darken-1;
            padding: 1;
        }
        """

        def compose(self) -> ComposeResult:
            yield Header()
            with Horizontal():
                # 左侧边栏
                yield Static("侧边栏\n- 菜单1\n- 菜单2\n- 菜单3", classes="sidebar")
                # 右侧主区域（垂直布局）
                with Vertical(classes="main"):
                    yield Static("顶部工具栏", classes="top-bar")
                    yield Static("主要内容区域", classes="content")
            yield Footer()

    print("示例3: 嵌套布局")
    print("=" * 40)
    app = NestedLayoutApp()
    app.run()
# endregion

# region 示例4: Grid 网格布局
if False:  # 改为 True 可运行此示例
    """
    Grid 容器实现网格布局
    通过 CSS 的 grid-size 属性定义行列数
    """

    class GridApp(App):
        CSS = """
        Grid {
            grid-size: 3 3;  /* 3列 3行 */
            grid-gutter: 1;  /* 网格间距 */
        }
        
        .cell {
            height: 100%;
            background: $primary;
            padding: 1;
            text-align: center;
        }
        
        .cell:hover {
            background: $primary-lighten-2;
        }
        """

        def compose(self) -> ComposeResult:
            yield Header()
            with Grid():
                for i in range(1, 10):
                    yield Static(f"格子 {i}", classes="cell")
            yield Footer()

    print("示例4: Grid 网格布局")
    print("=" * 40)
    app = GridApp()
    app.run()
# endregion

# region 示例5: ScrollableContainer 可滚动容器
if False:  # 改为 True 可运行此示例
    """
    ScrollableContainer 用于内容超出时提供滚动功能
    使用方向键或鼠标滚轮滚动
    """

    class ScrollApp(App):
        CSS = """
        ScrollableContainer {
            height: 100%;
            background: $surface;
        }
        
        .item {
            height: 3;
            background: $primary;
            margin: 1;
            padding: 1;
        }
        """

        def compose(self) -> ComposeResult:
            yield Header()
            with ScrollableContainer():
                # 创建很多项目，超出屏幕高度
                for i in range(1, 21):
                    yield Static(f"可滚动项目 {i}", classes="item")
            yield Footer()

    print("示例5: ScrollableContainer 可滚动容器")
    print("=" * 40)
    app = ScrollApp()
    app.run()
# endregion

# region 示例6: 使用 fr 单位进行弹性布局
if False:  # 改为 True 可运行此示例
    """
    fr (fraction) 单位用于分配剩余空间
    类似于 CSS Flexbox 的 flex-grow
    1fr 表示占用 1 份剩余空间
    """

    class FractionApp(App):
        CSS = """
        Horizontal {
            height: 100%;
        }
        
        .small {
            width: 1fr;  /* 1份 */
            background: red;
            padding: 1;
        }
        
        .medium {
            width: 2fr;  /* 2份 */
            background: green;
            padding: 1;
        }
        
        .large {
            width: 3fr;  /* 3份 */
            background: blue;
            padding: 1;
        }
        """

        def compose(self) -> ComposeResult:
            yield Header()
            with Horizontal():
                yield Static("1fr\n(1份)", classes="small")
                yield Static("2fr\n(2份)", classes="medium")
                yield Static("3fr\n(3份)", classes="large")
            yield Footer()

    print("示例6: fr 弹性单位")
    print("=" * 40)
    app = FractionApp()
    app.run()
# endregion
