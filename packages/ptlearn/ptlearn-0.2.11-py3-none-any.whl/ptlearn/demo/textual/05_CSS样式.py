"""
Textual CSS 样式系统
====================
Textual 使用类似 CSS 的样式系统，但有自己的特性。
本文件介绍 CSS 选择器、样式属性、响应式设计等。

要求: Python 3.8+, textual 库
"""

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Container
from textual.widgets import Header, Footer, Static, Button

# region 示例1: CSS 选择器
if True:  # 改为 False 可跳过此示例
    """
    Textual 支持多种 CSS 选择器：
    - 类型选择器: Button, Static
    - 类选择器: .classname
    - ID 选择器: #id
    - 伪类: :hover, :focus, :disabled
    - 组合选择器: Parent Child, Parent > Child
    """

    class SelectorApp(App):
        CSS = """
        /* 类型选择器 - 匹配所有 Static 组件 */
        Static {
            margin: 1;
            padding: 1;
        }
        
        /* 类选择器 - 匹配 class="highlight" */
        .highlight {
            background: yellow;
            color: black;
        }
        
        /* ID 选择器 - 匹配 id="special" */
        #special {
            background: $primary;
            border: double $secondary;
            text-style: bold;
        }
        
        /* 伪类选择器 */
        Button:hover {
            background: $primary-lighten-2;
        }
        
        Button:focus {
            border: thick $secondary;
        }
        
        /* 后代选择器 - Container 内的所有 Static */
        Container Static {
            background: $surface-darken-1;
        }
        
        /* 直接子元素选择器 */
        Container > .direct {
            border: solid green;
        }
        """

        def compose(self) -> ComposeResult:
            yield Header()
            yield Static("普通 Static (类型选择器)")
            yield Static("高亮文本", classes="highlight")
            yield Static("特殊元素", id="special")
            with Container():
                yield Static("Container 内的 Static")
                yield Static("直接子元素", classes="direct")
            yield Button("悬停我试试")
            yield Footer()

    print("示例1: CSS 选择器")
    print("=" * 40)
    app = SelectorApp()
    app.run()
# endregion

# region 示例2: 常用样式属性
if False:  # 改为 True 可运行此示例
    """
    Textual CSS 常用属性：
    - 尺寸: width, height, min-width, max-width
    - 边距: margin, padding
    - 边框: border, border-top, border-right...
    - 颜色: background, color
    - 文本: text-align, text-style
    - 布局: display, dock
    """

    class StylePropertiesApp(App):
        CSS = """
        .size-demo {
            width: 30;
            height: 5;
            background: $primary;
            margin: 1;
        }
        
        .margin-padding {
            margin: 2;           /* 外边距 */
            padding: 1 2;        /* 内边距: 上下1, 左右2 */
            background: $surface;
            border: solid $primary;
        }
        
        .border-demo {
            border: heavy red;   /* 粗边框 */
            border-title-align: center;
            margin: 1;
            padding: 1;
        }
        
        .text-demo {
            text-align: center;
            text-style: bold italic;
            color: $text;
            background: $primary-background;
            margin: 1;
            padding: 1;
        }
        
        .dock-demo {
            dock: bottom;        /* 停靠在底部 */
            height: 3;
            background: $warning;
            padding: 1;
        }
        """

        def compose(self) -> ComposeResult:
            yield Header()
            yield Static("固定尺寸 (30x5)", classes="size-demo")
            yield Static("边距和内边距演示", classes="margin-padding")
            yield Static("边框演示", classes="border-demo")
            yield Static("文本样式演示", classes="text-demo")
            yield Static("停靠在底部", classes="dock-demo")
            yield Footer()

    print("示例2: 常用样式属性")
    print("=" * 40)
    app = StylePropertiesApp()
    app.run()
# endregion

# region 示例3: 颜色系统
if False:  # 改为 True 可运行此示例
    """
    Textual 颜色系统：
    - 命名颜色: red, green, blue...
    - 十六进制: #ff0000, #00ff00
    - RGB: rgb(255, 0, 0)
    - 主题变量: $primary, $secondary, $surface...
    - 颜色修改器: $primary-lighten-1, $primary-darken-2
    """

    class ColorApp(App):
        CSS = """
        .named {
            background: red;
            color: white;
            margin: 1;
            padding: 1;
        }
        
        .hex {
            background: #3498db;
            color: #ffffff;
            margin: 1;
            padding: 1;
        }
        
        .rgb {
            background: rgb(46, 204, 113);
            color: rgb(0, 0, 0);
            margin: 1;
            padding: 1;
        }
        
        .theme-primary {
            background: $primary;
            margin: 1;
            padding: 1;
        }
        
        .theme-secondary {
            background: $secondary;
            margin: 1;
            padding: 1;
        }
        
        .lighten {
            background: $primary-lighten-2;
            margin: 1;
            padding: 1;
        }
        
        .darken {
            background: $primary-darken-2;
            margin: 1;
            padding: 1;
        }
        """

        BINDINGS = [("d", "toggle_dark", "切换主题")]

        def compose(self) -> ComposeResult:
            yield Header()
            yield Static("命名颜色: red", classes="named")
            yield Static("十六进制: #3498db", classes="hex")
            yield Static("RGB: rgb(46, 204, 113)", classes="rgb")
            yield Static("主题变量: $primary", classes="theme-primary")
            yield Static("主题变量: $secondary", classes="theme-secondary")
            yield Static("变亮: $primary-lighten-2", classes="lighten")
            yield Static("变暗: $primary-darken-2", classes="darken")
            yield Footer()

        def action_toggle_dark(self) -> None:
            self.theme = "textual-light" if self.theme == "textual-dark" else "textual-dark"

    print("示例3: 颜色系统")
    print("=" * 40)
    app = ColorApp()
    app.run()
# endregion

# region 示例4: 外部 CSS 文件
if False:  # 改为 True 可运行此示例
    """
    可以将 CSS 放在外部文件中
    使用 CSS_PATH 类属性指定路径
    或使用 DEFAULT_CSS 作为默认样式
    """

    class ExternalCSSApp(App):
        # 方式1: 使用 CSS_PATH 指定外部文件
        # CSS_PATH = "styles.tcss"  # 相对于 Python 文件的路径

        # 方式2: 使用 DEFAULT_CSS (会被实例 CSS 覆盖)
        DEFAULT_CSS = """
        Static {
            margin: 1;
            padding: 1;
            background: $surface;
        }
        """

        # 方式3: 实例 CSS (优先级最高)
        CSS = """
        #main {
            background: $primary;
            border: solid $secondary;
        }
        """

        def compose(self) -> ComposeResult:
            yield Header()
            yield Static("使用 DEFAULT_CSS 样式")
            yield Static("使用实例 CSS 样式", id="main")
            yield Static(
                "CSS 优先级:\n"
                "1. 实例 CSS (最高)\n"
                "2. CSS_PATH 外部文件\n"
                "3. DEFAULT_CSS (最低)"
            )
            yield Footer()

    print("示例4: 外部 CSS")
    print("=" * 40)
    app = ExternalCSSApp()
    app.run()
# endregion

# region 示例5: 动态修改样式
if False:  # 改为 True 可运行此示例
    """
    可以在运行时动态修改组件样式
    通过 styles 属性或 add_class/remove_class 方法
    """

    class DynamicStyleApp(App):
        CSS = """
        #box {
            width: 100%;
            height: 5;
            margin: 1;
            padding: 1;
            background: $surface;
            transition: background 500ms;
        }
        
        .red { background: red; }
        .green { background: green; }
        .blue { background: blue; }
        
        .big {
            height: 8;
            text-style: bold;
        }
        
        Horizontal {
            height: auto;
            margin: 1;
        }
        """

        def compose(self) -> ComposeResult:
            yield Header()
            yield Static("动态样式演示", id="box")
            with Horizontal():
                yield Button("红色", id="red", variant="error")
                yield Button("绿色", id="green", variant="success")
                yield Button("蓝色", id="blue", variant="primary")
                yield Button("放大", id="big", variant="warning")
            yield Footer()

        def on_button_pressed(self, event: Button.Pressed) -> None:
            box = self.query_one("#box", Static)

            if event.button.id in ("red", "green", "blue"):
                # 移除所有颜色类
                box.remove_class("red", "green", "blue")
                # 添加新颜色类
                box.add_class(event.button.id)
                box.update(f"当前颜色: {event.button.id}")

            elif event.button.id == "big":
                # 切换 big 类
                box.toggle_class("big")
                is_big = box.has_class("big")
                box.update(f"大小: {'大' if is_big else '正常'}")

    print("示例5: 动态样式")
    print("=" * 40)
    app = DynamicStyleApp()
    app.run()
# endregion

# region 示例6: 响应式布局
if False:  # 改为 True 可运行此示例
    """
    Textual 支持基于终端尺寸的响应式设计
    使用 @media 查询或在代码中检测尺寸
    """

    class ResponsiveApp(App):
        CSS = """
        #content {
            width: 100%;
            height: 1fr;
            margin: 1;
            padding: 1;
            background: $surface;
        }
        
        #sidebar {
            width: 20;
            height: 100%;
            background: $primary;
            padding: 1;
        }
        
        /* 当宽度小于 60 时隐藏侧边栏 */
        #sidebar.hidden {
            display: none;
        }
        
        #size-info {
            dock: bottom;
            height: 3;
            background: $surface-darken-1;
            padding: 1;
        }
        """

        def compose(self) -> ComposeResult:
            yield Header()
            with Horizontal():
                yield Static("侧边栏\n调整终端\n宽度试试", id="sidebar")
                yield Static("主内容区域", id="content")
            yield Static("终端尺寸: ", id="size-info")
            yield Footer()

        def on_resize(self, event) -> None:
            """终端尺寸变化时调用"""
            sidebar = self.query_one("#sidebar", Static)
            size_info = self.query_one("#size-info", Static)

            # 更新尺寸信息
            size_info.update(f"终端尺寸: {event.size.width} x {event.size.height}")

            # 响应式隐藏侧边栏
            if event.size.width < 60:
                sidebar.add_class("hidden")
            else:
                sidebar.remove_class("hidden")

    print("示例6: 响应式布局")
    print("=" * 40)
    app = ResponsiveApp()
    app.run()
# endregion
