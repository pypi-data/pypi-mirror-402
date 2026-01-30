"""
Textual 自定义组件
==================
学习如何创建可复用的自定义组件，包括组合组件、
响应式属性、组件通信等高级技巧。

要求: Python 3.8+, textual 库
"""

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Button, Label, Input
from textual.widget import Widget
from textual.reactive import reactive
from textual.message import Message

# region 示例1: 简单的自定义组件
if True:  # 改为 False 可跳过此示例
    """
    继承 Static 或 Widget 创建自定义组件
    重写 compose() 方法定义组件结构
    """

    class InfoCard(Static):
        """信息卡片组件"""

        DEFAULT_CSS = """
        InfoCard {
            background: $surface;
            border: solid $primary;
            padding: 1;
            margin: 1;
            height: auto;
        }
        
        InfoCard .title {
            text-style: bold;
            color: $primary;
        }
        
        InfoCard .content {
            margin-top: 1;
        }
        """

        def __init__(self, title: str, content: str) -> None:
            super().__init__()
            self.title_text = title
            self.content_text = content

        def compose(self) -> ComposeResult:
            yield Label(self.title_text, classes="title")
            yield Static(self.content_text, classes="content")

    class SimpleCustomApp(App):
        def compose(self) -> ComposeResult:
            yield Header()
            yield InfoCard("Python", "一种简洁优雅的编程语言")
            yield InfoCard("Textual", "现代化的 TUI 框架")
            yield InfoCard("Rich", "终端富文本渲染库")
            yield Footer()

    print("示例1: 简单自定义组件")
    print("=" * 40)
    app = SimpleCustomApp()
    app.run()
# endregion

# region 示例2: 响应式属性 (reactive)
if False:  # 改为 True 可运行此示例
    """
    reactive 属性会在值变化时自动触发更新
    可以定义 watch_xxx 方法监听变化
    """

    class Counter(Static):
        """带响应式属性的计数器"""

        # 定义响应式属性
        count: reactive[int] = reactive(0)

        DEFAULT_CSS = """
        Counter {
            background: $surface;
            border: solid $primary;
            padding: 1;
            margin: 1;
            height: auto;
        }
        
        Counter #display {
            text-align: center;
            text-style: bold;
            height: 3;
            content-align: center middle;
        }
        
        Counter Horizontal {
            height: auto;
            align: center middle;
        }
        
        Counter Button {
            margin: 0 1;
        }
        """

        def compose(self) -> ComposeResult:
            yield Static(str(self.count), id="display")
            with Horizontal():
                yield Button("-", id="dec", variant="error")
                yield Button("+", id="inc", variant="success")

        def watch_count(self, new_value: int) -> None:
            """当 count 变化时自动调用"""
            display = self.query_one("#display", Static)
            display.update(str(new_value))

        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "inc":
                self.count += 1
            elif event.button.id == "dec":
                self.count -= 1

    class ReactiveApp(App):
        def compose(self) -> ComposeResult:
            yield Header()
            yield Label("响应式计数器演示")
            yield Counter()
            yield Counter()
            yield Footer()

    print("示例2: 响应式属性")
    print("=" * 40)
    app = ReactiveApp()
    app.run()
# endregion

# region 示例3: 组件间通信 (消息)
if False:  # 改为 True 可运行此示例
    """
    组件可以发送自定义消息
    父组件通过 on_xxx 方法接收消息
    """

    class TodoItem(Static):
        """待办事项组件"""

        # 自定义消息
        class Deleted(Message):
            def __init__(self, item: "TodoItem") -> None:
                self.item = item
                super().__init__()

        class Toggled(Message):
            def __init__(self, item: "TodoItem", done: bool) -> None:
                self.item = item
                self.done = done
                super().__init__()

        DEFAULT_CSS = """
        TodoItem {
            height: 3;
            margin: 1;
            padding: 0 1;
            background: $surface;
        }
        
        TodoItem.done {
            opacity: 0.5;
        }
        
        TodoItem Horizontal {
            height: 100%;
            align: left middle;
        }
        
        TodoItem #text {
            width: 1fr;
        }
        
        TodoItem.done #text {
            text-style: strike;
        }
        """

        def __init__(self, text: str) -> None:
            super().__init__()
            self.text = text
            self.done = False

        def compose(self) -> ComposeResult:
            with Horizontal():
                yield Button("✓", id="toggle", variant="success")
                yield Label(self.text, id="text")
                yield Button("✗", id="delete", variant="error")

        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "toggle":
                self.done = not self.done
                self.toggle_class("done")
                self.post_message(self.Toggled(self, self.done))
            elif event.button.id == "delete":
                self.post_message(self.Deleted(self))

    class TodoApp(App):
        CSS = """
        #input-area {
            height: auto;
            margin: 1;
        }
        
        #input-area Input {
            width: 1fr;
        }
        
        #stats {
            dock: bottom;
            height: 3;
            background: $primary;
            padding: 1;
        }
        """

        def __init__(self):
            super().__init__()
            self.total = 0
            self.completed = 0

        def compose(self) -> ComposeResult:
            yield Header()
            with Horizontal(id="input-area"):
                yield Input(placeholder="输入待办事项...", id="todo-input")
                yield Button("添加", id="add", variant="primary")
            yield Vertical(id="todo-list")
            yield Static("总计: 0 | 完成: 0", id="stats")
            yield Footer()

        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "add":
                input_widget = self.query_one("#todo-input", Input)
                if input_widget.value.strip():
                    todo_list = self.query_one("#todo-list", Vertical)
                    todo_list.mount(TodoItem(input_widget.value))
                    input_widget.value = ""
                    self.total += 1
                    self.update_stats()

        def on_todo_item_deleted(self, event: TodoItem.Deleted) -> None:
            """处理删除消息"""
            if event.item.done:
                self.completed -= 1
            self.total -= 1
            event.item.remove()
            self.update_stats()

        def on_todo_item_toggled(self, event: TodoItem.Toggled) -> None:
            """处理切换消息"""
            if event.done:
                self.completed += 1
            else:
                self.completed -= 1
            self.update_stats()

        def update_stats(self) -> None:
            stats = self.query_one("#stats", Static)
            stats.update(f"总计: {self.total} | 完成: {self.completed}")

    print("示例3: 组件间通信")
    print("=" * 40)
    app = TodoApp()
    app.run()
# endregion

# region 示例4: 组件验证与计算属性
if False:  # 改为 True 可运行此示例
    """
    reactive 支持验证器和计算属性
    validate_xxx: 验证并可能修改新值
    compute_xxx: 基于其他属性计算值
    """

    class TemperatureConverter(Static):
        """温度转换器 - 演示验证和计算属性"""

        # 摄氏度 (主属性)
        celsius: reactive[float] = reactive(0.0)
        # 华氏度 (计算属性)
        fahrenheit: reactive[float] = reactive(32.0)

        DEFAULT_CSS = """
        TemperatureConverter {
            background: $surface;
            border: solid $primary;
            padding: 1;
            margin: 1;
            height: auto;
        }
        
        TemperatureConverter .row {
            height: 3;
            margin: 1 0;
        }
        
        TemperatureConverter Input {
            width: 20;
        }
        """

        def compose(self) -> ComposeResult:
            with Horizontal(classes="row"):
                yield Label("摄氏度: ")
                yield Input(str(self.celsius), id="celsius", type="number")
            with Horizontal(classes="row"):
                yield Label("华氏度: ")
                yield Input(str(self.fahrenheit), id="fahrenheit", type="number")
            yield Static("", id="status")

        def validate_celsius(self, value: float) -> float:
            """验证摄氏度 (不能低于绝对零度)"""
            return max(value, -273.15)

        def watch_celsius(self, value: float) -> None:
            """摄氏度变化时更新华氏度"""
            self.fahrenheit = value * 9 / 5 + 32
            self.query_one("#fahrenheit", Input).value = f"{self.fahrenheit:.2f}"
            self.update_status()

        def watch_fahrenheit(self, value: float) -> None:
            """华氏度变化时更新摄氏度"""
            new_celsius = (value - 32) * 5 / 9
            if abs(new_celsius - self.celsius) > 0.01:  # 避免循环更新
                self.celsius = new_celsius
                self.query_one("#celsius", Input).value = f"{self.celsius:.2f}"

        def update_status(self) -> None:
            status = self.query_one("#status", Static)
            if self.celsius < 0:
                status.update("🥶 很冷!")
            elif self.celsius < 20:
                status.update("😊 凉爽")
            elif self.celsius < 30:
                status.update("😎 舒适")
            else:
                status.update("🥵 很热!")

        def on_input_changed(self, event: Input.Changed) -> None:
            try:
                value = float(event.value) if event.value else 0
                if event.input.id == "celsius":
                    self.celsius = value
                elif event.input.id == "fahrenheit":
                    self.fahrenheit = value
            except ValueError:
                pass

    class ValidateApp(App):
        def compose(self) -> ComposeResult:
            yield Header()
            yield Label("温度转换器 (演示验证和计算属性)")
            yield TemperatureConverter()
            yield Footer()

    print("示例4: 验证与计算属性")
    print("=" * 40)
    app = ValidateApp()
    app.run()
# endregion

# region 示例5: 可复用组件库模式
if False:  # 改为 True 可运行此示例
    """
    创建可复用的组件库
    组件应该自包含样式和行为
    """

    class Card(Static):
        """通用卡片组件"""

        DEFAULT_CSS = """
        Card {
            background: $surface;
            border: solid $primary;
            padding: 1;
            margin: 1;
            height: auto;
        }
        
        Card > .card-header {
            text-style: bold;
            border-bottom: solid $primary;
            padding-bottom: 1;
            margin-bottom: 1;
        }
        
        Card > .card-footer {
            border-top: solid $primary;
            padding-top: 1;
            margin-top: 1;
            text-align: right;
        }
        """

        def __init__(
            self,
            title: str = "",
            footer: str = "",
            *children: Widget,
        ) -> None:
            super().__init__()
            self.title = title
            self.footer_text = footer
            self.card_children = children

        def compose(self) -> ComposeResult:
            if self.title:
                yield Label(self.title, classes="card-header")
            for child in self.card_children:
                yield child
            if self.footer_text:
                yield Label(self.footer_text, classes="card-footer")

    class Badge(Static):
        """徽章组件"""

        DEFAULT_CSS = """
        Badge {
            width: auto;
            height: 1;
            padding: 0 1;
            background: $primary;
            color: $text;
        }
        
        Badge.success { background: $success; }
        Badge.warning { background: $warning; }
        Badge.error { background: $error; }
        """

        def __init__(self, text: str, variant: str = "") -> None:
            super().__init__(text)
            if variant:
                self.add_class(variant)

    class ComponentLibraryApp(App):
        CSS = """
        Horizontal {
            height: auto;
        }
        """

        def compose(self) -> ComposeResult:
            yield Header()
            yield Card(
                "用户信息",
                "最后更新: 2024-01-01",
                Static("姓名: 张三"),
                Static("邮箱: zhangsan@example.com"),
                Horizontal(
                    Badge("管理员", "success"),
                    Badge("已验证"),
                ),
            )
            yield Card(
                "系统状态",
                "",
                Horizontal(
                    Badge("CPU: 正常", "success"),
                    Badge("内存: 警告", "warning"),
                    Badge("磁盘: 错误", "error"),
                ),
            )
            yield Footer()

    print("示例5: 可复用组件库")
    print("=" * 40)
    app = ComponentLibraryApp()
    app.run()
# endregion
