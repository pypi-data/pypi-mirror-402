"""
Textual 事件处理
================
Textual 使用事件驱动模型，本文件介绍事件处理机制：
消息传递、事件冒泡、键盘事件、鼠标事件等。

要求: Python 3.8+, textual 库
"""

from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Header, Footer, Static, Button, Label
from textual.message import Message
from textual import events

# region 示例1: 键盘事件处理
if True:  # 改为 False 可跳过此示例
    """
    通过 on_key 方法处理键盘事件
    或使用 BINDINGS 定义快捷键
    """

    class KeyboardApp(App):
        CSS = """
        #display {
            height: 5;
            margin: 1;
            padding: 1;
            background: $surface;
            border: solid $primary;
        }
        
        #history {
            height: 1fr;
            margin: 1;
            padding: 1;
            background: $surface-darken-1;
        }
        """

        # 定义快捷键绑定
        BINDINGS = [
            ("q", "quit", "退出"),
            ("c", "clear", "清除"),
            ("up", "move('up')", "上移"),
            ("down", "move('down')", "下移"),
        ]

        def __init__(self):
            super().__init__()
            self.key_history: list[str] = []

        def compose(self) -> ComposeResult:
            yield Header()
            yield Static("按任意键查看按键信息\n按 c 清除历史", id="display")
            yield Static("按键历史:", id="history")
            yield Footer()

        def on_key(self, event: events.Key) -> None:
            """处理所有键盘事件"""
            display = self.query_one("#display", Static)
            display.update(
                f"按键: {event.key}\n"
                f"字符: {event.character or '(无)'}\n"
                f"是否为可打印字符: {event.is_printable}"
            )
            self.key_history.append(event.key)
            self.update_history()

        def update_history(self) -> None:
            history = self.query_one("#history", Static)
            recent = self.key_history[-10:]  # 只显示最近10个
            history.update(f"按键历史: {' → '.join(recent)}")

        def action_clear(self) -> None:
            """清除历史"""
            self.key_history.clear()
            self.update_history()
            self.query_one("#display", Static).update("已清除")

        def action_move(self, direction: str) -> None:
            """处理方向键"""
            display = self.query_one("#display", Static)
            display.update(f"移动方向: {direction}")

    print("示例1: 键盘事件")
    print("=" * 40)
    app = KeyboardApp()
    app.run()
# endregion

# region 示例2: 鼠标事件处理
if False:  # 改为 True 可运行此示例
    """
    处理鼠标点击、移动、滚轮等事件
    """

    class MouseApp(App):
        CSS = """
        #canvas {
            height: 1fr;
            margin: 1;
            background: $surface;
            border: solid $primary;
        }
        
        #info {
            height: 3;
            margin: 1;
            padding: 1;
            background: $surface-darken-1;
        }
        """

        def compose(self) -> ComposeResult:
            yield Header()
            yield Static("在此区域移动鼠标或点击", id="canvas")
            yield Static("鼠标信息将显示在这里", id="info")
            yield Footer()

        def on_click(self, event: events.Click) -> None:
            """鼠标点击事件"""
            info = self.query_one("#info", Static)
            info.update(
                f"点击位置: ({event.x}, {event.y}) | "
                f"按钮: {event.button} | "
                f"点击次数: {event.chain}"
            )

        def on_mouse_move(self, event: events.MouseMove) -> None:
            """鼠标移动事件"""
            canvas = self.query_one("#canvas", Static)
            canvas.update(f"鼠标位置: ({event.x}, {event.y})")

    print("示例2: 鼠标事件")
    print("=" * 40)
    app = MouseApp()
    app.run()
# endregion

# region 示例3: 自定义消息
if False:  # 改为 True 可运行此示例
    """
    组件可以发送自定义消息
    父组件可以监听并处理这些消息
    """

    class CounterWidget(Static):
        """自定义计数器组件"""

        # 定义自定义消息
        class CountChanged(Message):
            """计数变化消息"""
            def __init__(self, count: int) -> None:
                self.count = count
                super().__init__()

        def __init__(self, name: str) -> None:
            super().__init__()
            self.counter_name = name
            self.count = 0

        def compose(self) -> ComposeResult:
            yield Label(f"{self.counter_name}: 0", id="label")
            with Horizontal():
                yield Button("+", id="inc", variant="success")
                yield Button("-", id="dec", variant="error")

        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "inc":
                self.count += 1
            elif event.button.id == "dec":
                self.count -= 1
            # 更新显示
            self.query_one("#label", Label).update(f"{self.counter_name}: {self.count}")
            # 发送自定义消息
            self.post_message(self.CountChanged(self.count))

    class CustomMessageApp(App):
        CSS = """
        CounterWidget {
            height: auto;
            margin: 1;
            padding: 1;
            background: $surface;
            border: solid $primary;
        }
        
        Horizontal {
            height: auto;
        }
        
        Button {
            margin: 0 1;
        }
        
        #total {
            margin: 1;
            padding: 1;
            background: $primary;
            text-style: bold;
        }
        """

        def compose(self) -> ComposeResult:
            yield Header()
            yield CounterWidget("计数器 A")
            yield CounterWidget("计数器 B")
            yield Static("总计: 0", id="total")
            yield Footer()

        def on_counter_widget_count_changed(self, event: CounterWidget.CountChanged) -> None:
            """处理自定义消息"""
            # 计算所有计数器的总和
            total = sum(w.count for w in self.query(CounterWidget))
            self.query_one("#total", Static).update(f"总计: {total}")

    print("示例3: 自定义消息")
    print("=" * 40)
    app = CustomMessageApp()
    app.run()
# endregion

# region 示例4: 事件冒泡与阻止
if False:  # 改为 True 可运行此示例
    """
    事件会从子组件冒泡到父组件
    可以使用 stop() 阻止事件继续冒泡
    """

    class BubbleApp(App):
        CSS = """
        .outer {
            background: blue;
            padding: 2;
            margin: 1;
        }
        
        .inner {
            background: green;
            padding: 2;
        }
        
        Button {
            margin: 1;
        }
        
        #log {
            height: 8;
            margin: 1;
            padding: 1;
            background: $surface;
        }
        """

        def __init__(self):
            super().__init__()
            self.logs: list[str] = []

        def compose(self) -> ComposeResult:
            yield Header()
            with Vertical(classes="outer", id="outer"):
                yield Label("外层容器 (蓝色)")
                with Vertical(classes="inner", id="inner"):
                    yield Label("内层容器 (绿色)")
                    yield Button("普通按钮", id="normal")
                    yield Button("阻止冒泡", id="stop")
            yield Static("事件日志:", id="log")
            yield Footer()

        def add_log(self, msg: str) -> None:
            self.logs.append(msg)
            self.logs = self.logs[-5:]  # 保留最近5条
            self.query_one("#log", Static).update("事件日志:\n" + "\n".join(self.logs))

        def on_button_pressed(self, event: Button.Pressed) -> None:
            self.add_log(f"App 收到按钮事件: {event.button.id}")
            if event.button.id == "stop":
                event.stop()  # 阻止事件继续冒泡
                self.add_log("  → 事件已阻止冒泡")

    print("示例4: 事件冒泡")
    print("=" * 40)
    app = BubbleApp()
    app.run()
# endregion

# region 示例5: 定时器事件
if False:  # 改为 True 可运行此示例
    """
    使用 set_timer 和 set_interval 创建定时任务
    """

    class TimerApp(App):
        CSS = """
        #clock {
            height: 3;
            margin: 1;
            padding: 1;
            background: $primary;
            text-align: center;
            text-style: bold;
        }
        
        #countdown {
            height: 3;
            margin: 1;
            padding: 1;
            background: $surface;
            text-align: center;
        }
        
        Horizontal {
            height: auto;
            margin: 1;
        }
        """

        def __init__(self):
            super().__init__()
            self.seconds = 0
            self.countdown = 10
            self.timer_handle = None

        def compose(self) -> ComposeResult:
            yield Header()
            yield Static("运行时间: 0 秒", id="clock")
            yield Static("倒计时: 10", id="countdown")
            with Horizontal():
                yield Button("开始倒计时", id="start", variant="primary")
                yield Button("重置", id="reset", variant="warning")
            yield Footer()

        def on_mount(self) -> None:
            """应用启动时开始计时"""
            # set_interval 创建重复定时器
            self.set_interval(1, self.update_clock)

        def update_clock(self) -> None:
            """每秒更新时钟"""
            self.seconds += 1
            self.query_one("#clock", Static).update(f"运行时间: {self.seconds} 秒")

        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "start":
                self.start_countdown()
            elif event.button.id == "reset":
                self.countdown = 10
                self.query_one("#countdown", Static).update("倒计时: 10")

        def start_countdown(self) -> None:
            """开始倒计时"""
            if self.countdown > 0:
                self.countdown -= 1
                self.query_one("#countdown", Static).update(f"倒计时: {self.countdown}")
                # set_timer 创建一次性定时器
                self.set_timer(1, self.start_countdown)
            else:
                self.query_one("#countdown", Static).update("倒计时结束！")

    print("示例5: 定时器")
    print("=" * 40)
    app = TimerApp()
    app.run()
# endregion
