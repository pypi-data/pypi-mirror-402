"""
Textual 实战案例
================
综合运用前面学到的知识，构建一个完整的 TUI 应用。
本文件展示一个简单的任务管理器应用。

要求: Python 3.8+, textual 库
"""

from textual.app import App, ComposeResult
from textual.screen import ModalScreen
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import (
    Header, Footer, Static, Button, Label, Input, Select
)
from textual.reactive import reactive
from textual.message import Message
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# region 数据模型定义
class Priority(Enum):
    LOW = "低"
    MEDIUM = "中"
    HIGH = "高"

@dataclass
class Task:
    """任务数据模型"""
    id: int
    title: str
    priority: Priority
    done: bool = False
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
# endregion

# region 任务项组件
class TaskItem(Static):
    """单个任务项组件"""

    class Toggled(Message):
        def __init__(self, task_id: int) -> None:
            self.task_id = task_id
            super().__init__()

    class Deleted(Message):
        def __init__(self, task_id: int) -> None:
            self.task_id = task_id
            super().__init__()

    DEFAULT_CSS = """
    TaskItem {
        height: 3;
        margin: 0 1 1 1;
        padding: 0 1;
        background: $surface;
        border-left: thick $primary;
    }
    
    TaskItem.done {
        opacity: 0.6;
        border-left: thick $success;
    }
    
    TaskItem.high {
        border-left: thick $error;
    }
    
    TaskItem.medium {
        border-left: thick $warning;
    }
    
    TaskItem Horizontal {
        height: 100%;
        align: left middle;
    }
    
    TaskItem #title {
        width: 1fr;
    }
    
    TaskItem.done #title {
        text-style: strike;
    }
    
    TaskItem #priority {
        width: 6;
        text-align: center;
    }
    
    TaskItem Button {
        min-width: 4;
        margin-left: 1;
    }
    """

    def __init__(self, task_data: Task) -> None:
        super().__init__()
        self.task_data = task_data
        # 根据优先级添加类
        if not task_data.done:
            self.add_class(task_data.priority.name.lower())
        if task_data.done:
            self.add_class("done")

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Button("✓" if self.task_data.done else "○", id="toggle", variant="success" if self.task_data.done else "default")
            yield Label(self.task_data.title, id="title")
            yield Label(f"[{self.task_data.priority.value}]", id="priority")
            yield Button("✗", id="delete", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "toggle":
            self.post_message(self.Toggled(self.task_data.id))
        elif event.button.id == "delete":
            self.post_message(self.Deleted(self.task_data.id))
# endregion

# region 添加任务对话框
class AddTaskDialog(ModalScreen[Task | None]):
    """添加任务对话框"""

    DEFAULT_CSS = """
    AddTaskDialog {
        align: center middle;
    }
    
    AddTaskDialog > Vertical {
        width: 60;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }
    
    AddTaskDialog #dialog-title {
        text-style: bold;
        text-align: center;
        margin-bottom: 1;
    }
    
    AddTaskDialog .field {
        height: auto;
        margin: 1 0;
    }
    
    AddTaskDialog .field Label {
        margin-bottom: 1;
    }
    
    AddTaskDialog Input {
        width: 100%;
    }
    
    AddTaskDialog Select {
        width: 100%;
    }
    
    AddTaskDialog .buttons {
        height: auto;
        align: center middle;
        margin-top: 1;
    }
    
    AddTaskDialog .buttons Button {
        margin: 0 1;
    }
    """

    BINDINGS = [("escape", "cancel", "取消")]

    def __init__(self, next_id: int) -> None:
        super().__init__()
        self.next_id = next_id

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("➕ 添加新任务", id="dialog-title")
            with Vertical(classes="field"):
                yield Label("任务标题:")
                yield Input(placeholder="输入任务标题...", id="title-input")
            with Vertical(classes="field"):
                yield Label("优先级:")
                yield Select(
                    [(p.value, p) for p in Priority],
                    value=Priority.MEDIUM,
                    id="priority-select"
                )
            with Horizontal(classes="buttons"):
                yield Button("添加", id="add", variant="success")
                yield Button("取消", id="cancel", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add":
            title = self.query_one("#title-input", Input).value.strip()
            if title:
                priority = self.query_one("#priority-select", Select).value
                task = Task(id=self.next_id, title=title, priority=priority)
                self.dismiss(task)
            else:
                self.query_one("#title-input", Input).focus()
        elif event.button.id == "cancel":
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)
# endregion

# region 主应用
class TaskManagerApp(App):
    """任务管理器应用"""

    CSS = """
    #toolbar {
        height: 3;
        background: $primary-background;
        padding: 0 1;
    }
    
    #toolbar Horizontal {
        height: 100%;
        align: left middle;
    }
    
    #toolbar Button {
        margin-right: 1;
    }
    
    #toolbar #filter {
        width: 20;
    }
    
    #task-list {
        height: 1fr;
    }
    
    #empty-message {
        height: 100%;
        content-align: center middle;
        text-style: italic;
        color: $text-muted;
    }
    
    #stats {
        height: 3;
        background: $surface-darken-1;
        padding: 0 1;
        content-align: center middle;
    }
    """

    BINDINGS = [
        ("a", "add_task", "添加任务"),
        ("q", "quit", "退出"),
        ("d", "toggle_dark", "切换主题"),
    ]

    # 响应式属性
    task_count: reactive[int] = reactive(0)
    done_count: reactive[int] = reactive(0)

    def __init__(self) -> None:
        super().__init__()
        self.tasks: dict[int, Task] = {}
        self.next_id = 1
        self.current_filter = "all"

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="toolbar"):
            with Horizontal():
                yield Button("➕ 添加", id="add-btn", variant="success")
                yield Button("🗑️ 清除已完成", id="clear-done", variant="warning")
                yield Select(
                    [("全部", "all"), ("未完成", "active"), ("已完成", "done")],
                    value="all",
                    id="filter"
                )
        yield ScrollableContainer(id="task-list")
        yield Static("", id="stats")
        yield Footer()

    def on_mount(self) -> None:
        # 添加一些示例任务
        sample_tasks = [
            ("学习 Textual 基础", Priority.HIGH),
            ("完成项目文档", Priority.MEDIUM),
            ("代码审查", Priority.LOW),
        ]
        for title, priority in sample_tasks:
            task = Task(id=self.next_id, title=title, priority=priority)
            self.tasks[task.id] = task
            self.next_id += 1

        self.refresh_task_list()
        self.update_stats()

    def refresh_task_list(self) -> None:
        """刷新任务列表"""
        task_list = self.query_one("#task-list", ScrollableContainer)
        task_list.remove_children()

        # 根据过滤器筛选任务
        filtered_tasks = []
        for task in self.tasks.values():
            if self.current_filter == "all":
                filtered_tasks.append(task)
            elif self.current_filter == "active" and not task.done:
                filtered_tasks.append(task)
            elif self.current_filter == "done" and task.done:
                filtered_tasks.append(task)

        if filtered_tasks:
            # 按优先级和完成状态排序
            filtered_tasks.sort(key=lambda t: (t.done, t.priority.name))
            for task_item in filtered_tasks:
                task_list.mount(TaskItem(task_item))
        else:
            task_list.mount(Static("暂无任务", id="empty-message"))

    def update_stats(self) -> None:
        """更新统计信息"""
        self.task_count = len(self.tasks)
        self.done_count = sum(1 for t in self.tasks.values() if t.done)
        stats = self.query_one("#stats", Static)
        stats.update(
            f"📊 总计: {self.task_count} | "
            f"✅ 已完成: {self.done_count} | "
            f"⏳ 待完成: {self.task_count - self.done_count}"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add-btn":
            self.action_add_task()
        elif event.button.id == "clear-done":
            self.clear_done_tasks()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "filter":
            self.current_filter = event.value
            self.refresh_task_list()

    def on_task_item_toggled(self, event: TaskItem.Toggled) -> None:
        """处理任务切换"""
        if event.task_id in self.tasks:
            task = self.tasks[event.task_id]
            task.done = not task.done
            self.refresh_task_list()
            self.update_stats()

    def on_task_item_deleted(self, event: TaskItem.Deleted) -> None:
        """处理任务删除"""
        if event.task_id in self.tasks:
            del self.tasks[event.task_id]
            self.refresh_task_list()
            self.update_stats()

    def action_add_task(self) -> None:
        """打开添加任务对话框"""
        self.push_screen(AddTaskDialog(self.next_id), self.handle_add_task)

    def handle_add_task(self, task: Task | None) -> None:
        """处理添加任务结果"""
        if task:
            self.tasks[task.id] = task
            self.next_id += 1
            self.refresh_task_list()
            self.update_stats()

    def clear_done_tasks(self) -> None:
        """清除已完成的任务"""
        self.tasks = {k: v for k, v in self.tasks.items() if not v.done}
        self.refresh_task_list()
        self.update_stats()

    def action_toggle_dark(self) -> None:
        """切换深色模式"""
        self.theme = "textual-light" if self.theme == "textual-dark" else "textual-dark"
# endregion

# region 运行应用
if True:  # 改为 False 可跳过此示例
    print("任务管理器 - Textual 实战案例")
    print("=" * 40)
    print("快捷键:")
    print("  a - 添加任务")
    print("  d - 切换主题")
    print("  q - 退出")
    print("=" * 40)
    app = TaskManagerApp()
    app.run()
# endregion
