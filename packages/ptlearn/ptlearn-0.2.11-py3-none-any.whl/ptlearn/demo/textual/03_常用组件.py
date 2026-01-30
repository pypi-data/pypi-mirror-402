"""
Textual 常用组件
================
Textual 提供了丰富的内置组件，本文件介绍最常用的交互组件：
Button、Input、Checkbox、RadioButton、Select 等。

要求: Python 3.8+, textual 库
"""

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import (
    Header, Footer, Static, Label,
    Button, Input, Checkbox, RadioButton, RadioSet,
    Select, Switch, ProgressBar
)

# region 示例1: Button 按钮组件
if True:  # 改为 False 可跳过此示例
    """
    Button 是最基础的交互组件
    通过 on_button_pressed 事件处理点击
    支持多种样式变体：default, primary, success, warning, error
    """

    class ButtonApp(App):
        CSS = """
        Horizontal {
            height: auto;
            margin: 1;
        }
        
        Button {
            margin: 0 1;
        }
        
        #result {
            margin: 1;
            padding: 1;
            background: $surface;
        }
        """

        def compose(self) -> ComposeResult:
            yield Header()
            with Horizontal():
                yield Button("默认", id="btn_default")
                yield Button("主要", id="btn_primary", variant="primary")
                yield Button("成功", id="btn_success", variant="success")
                yield Button("警告", id="btn_warning", variant="warning")
                yield Button("错误", id="btn_error", variant="error")
            yield Static("点击按钮查看结果", id="result")
            yield Footer()

        def on_button_pressed(self, event: Button.Pressed) -> None:
            """处理按钮点击事件"""
            # event.button 是被点击的按钮
            result = self.query_one("#result", Static)
            result.update(f"你点击了: {event.button.label} (ID: {event.button.id})")

    print("示例1: Button 按钮")
    print("=" * 40)
    app = ButtonApp()
    app.run()
# endregion

# region 示例2: Input 输入框组件
if False:  # 改为 True 可运行此示例
    """
    Input 用于文本输入
    支持 placeholder、password 模式、验证等功能
    """

    class InputApp(App):
        CSS = """
        Input {
            margin: 1;
        }
        
        #output {
            margin: 1;
            padding: 1;
            background: $surface;
            height: 5;
        }
        """

        def compose(self) -> ComposeResult:
            yield Header()
            yield Input(placeholder="请输入用户名...", id="username")
            yield Input(placeholder="请输入密码...", password=True, id="password")
            yield Input(placeholder="只能输入数字", type="integer", id="number")
            yield Button("提交", variant="primary", id="submit")
            yield Static("输入内容将显示在这里", id="output")
            yield Footer()

        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "submit":
                username = self.query_one("#username", Input).value
                password = self.query_one("#password", Input).value
                number = self.query_one("#number", Input).value
                output = self.query_one("#output", Static)
                output.update(
                    f"用户名: {username}\n"
                    f"密码: {'*' * len(password)}\n"
                    f"数字: {number}"
                )

        def on_input_changed(self, event: Input.Changed) -> None:
            """输入内容变化时触发"""
            self.log(f"输入变化: {event.input.id} = {event.value}")

    print("示例2: Input 输入框")
    print("=" * 40)
    app = InputApp()
    app.run()
# endregion

# region 示例3: Checkbox 和 Switch 组件
if False:  # 改为 True 可运行此示例
    """
    Checkbox: 复选框，用于多选
    Switch: 开关，用于开/关状态
    """

    class CheckboxApp(App):
        CSS = """
        .option {
            margin: 1;
        }
        
        #status {
            margin: 1;
            padding: 1;
            background: $surface;
        }
        """

        def compose(self) -> ComposeResult:
            yield Header()
            yield Label("选择你喜欢的编程语言:")
            yield Checkbox("Python", id="python", classes="option", value=True)
            yield Checkbox("JavaScript", id="js", classes="option")
            yield Checkbox("Rust", id="rust", classes="option")
            yield Label("\n设置:")
            yield Switch(value=True, id="dark_mode")
            yield Label("深色模式", id="dark_label")
            yield Static("", id="status")
            yield Footer()

        def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
            """复选框状态变化"""
            self.update_status()

        def on_switch_changed(self, event: Switch.Changed) -> None:
            """开关状态变化"""
            self.theme = "textual-dark" if event.value else "textual-light"
            self.update_status()

        def update_status(self) -> None:
            selected = []
            for cb_id in ["python", "js", "rust"]:
                cb = self.query_one(f"#{cb_id}", Checkbox)
                if cb.value:
                    selected.append(cb.label)
            dark = self.query_one("#dark_mode", Switch).value
            status = self.query_one("#status", Static)
            status.update(f"已选语言: {', '.join(str(s) for s in selected) or '无'}\n深色模式: {'开' if dark else '关'}")

    print("示例3: Checkbox 和 Switch")
    print("=" * 40)
    app = CheckboxApp()
    app.run()
# endregion

# region 示例4: RadioButton 和 RadioSet 组件
if False:  # 改为 True 可运行此示例
    """
    RadioSet 包含多个 RadioButton
    同一组内只能选择一个选项
    """

    class RadioApp(App):
        CSS = """
        RadioSet {
            margin: 1;
            background: $surface;
            padding: 1;
        }
        
        #result {
            margin: 1;
            padding: 1;
            background: $primary-background;
        }
        """

        def compose(self) -> ComposeResult:
            yield Header()
            yield Label("选择你的操作系统:")
            with RadioSet(id="os_choice"):
                yield RadioButton("Windows", id="windows")
                yield RadioButton("macOS", id="macos")
                yield RadioButton("Linux", id="linux", value=True)  # 默认选中
            yield Static("当前选择: Linux", id="result")
            yield Footer()

        def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
            """单选组选择变化"""
            result = self.query_one("#result", Static)
            # event.pressed 是被选中的 RadioButton
            result.update(f"当前选择: {event.pressed.label}")

    print("示例4: RadioButton 单选")
    print("=" * 40)
    app = RadioApp()
    app.run()
# endregion

# region 示例5: Select 下拉选择组件
if False:  # 改为 True 可运行此示例
    """
    Select 提供下拉选择功能
    适合选项较多的场景
    """

    class SelectApp(App):
        CSS = """
        Select {
            margin: 1;
            width: 40;
        }
        
        #info {
            margin: 1;
            padding: 1;
            background: $surface;
        }
        """

        # 定义选项：(显示文本, 值)
        CITIES = [
            ("北京", "beijing"),
            ("上海", "shanghai"),
            ("广州", "guangzhou"),
            ("深圳", "shenzhen"),
            ("杭州", "hangzhou"),
        ]

        def compose(self) -> ComposeResult:
            yield Header()
            yield Label("选择城市:")
            yield Select(self.CITIES, prompt="请选择一个城市", id="city")
            yield Static("尚未选择", id="info")
            yield Footer()

        def on_select_changed(self, event: Select.Changed) -> None:
            """下拉选择变化"""
            info = self.query_one("#info", Static)
            if event.value == Select.BLANK:
                info.update("尚未选择")
            else:
                info.update(f"你选择了: {event.value}")

    print("示例5: Select 下拉选择")
    print("=" * 40)
    app = SelectApp()
    app.run()
# endregion

# region 示例6: ProgressBar 进度条组件
if False:  # 改为 True 可运行此示例
    """
    ProgressBar 显示进度
    可以手动更新进度值
    """

    class ProgressApp(App):
        CSS = """
        ProgressBar {
            margin: 1;
            padding: 1;
        }
        
        Horizontal {
            height: auto;
            margin: 1;
        }
        """

        def compose(self) -> ComposeResult:
            yield Header()
            yield Label("下载进度:")
            yield ProgressBar(total=100, id="progress")
            with Horizontal():
                yield Button("开始", id="start", variant="primary")
                yield Button("重置", id="reset", variant="warning")
            yield Footer()

        def on_button_pressed(self, event: Button.Pressed) -> None:
            progress = self.query_one("#progress", ProgressBar)
            if event.button.id == "start":
                # 模拟进度增加
                self.simulate_progress()
            elif event.button.id == "reset":
                progress.update(progress=0)

        def simulate_progress(self) -> None:
            """模拟进度更新"""
            progress = self.query_one("#progress", ProgressBar)
            current = progress.progress or 0
            if current < 100:
                progress.update(progress=min(current + 10, 100))
                # 使用定时器继续更新
                self.set_timer(0.2, self.simulate_progress)

    print("示例6: ProgressBar 进度条")
    print("=" * 40)
    app = ProgressApp()
    app.run()
# endregion
