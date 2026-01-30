"""
Textual 高级功能
================
本文件介绍 Textual 的高级功能：屏幕管理、模态对话框、
异步操作、数据表格、树形视图等。

要求: Python 3.8+, textual 库
"""

from textual.app import App, ComposeResult
from textual.screen import Screen, ModalScreen
from textual.containers import Vertical, Horizontal
from textual.widgets import (
    Header, Footer, Static, Button, Label, Input,
    DataTable, Tree, LoadingIndicator
)
from textual import work
import asyncio

# region 示例1: 多屏幕管理
if True:  # 改为 False 可跳过此示例
    """
    Textual 支持多屏幕切换
    使用 push_screen/pop_screen 管理屏幕栈
    """

    class HomeScreen(Screen):
        """主屏幕"""

        def compose(self) -> ComposeResult:
            yield Header()
            yield Static("这是主屏幕", id="content")
            yield Button("进入设置", id="settings", variant="primary")
            yield Button("进入关于", id="about")
            yield Footer()

        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "settings":
                self.app.push_screen(SettingsScreen())
            elif event.button.id == "about":
                self.app.push_screen(AboutScreen())

    class SettingsScreen(Screen):
        """设置屏幕"""

        BINDINGS = [("escape", "go_back", "返回")]

        def compose(self) -> ComposeResult:
            yield Header()
            yield Static("⚙️ 设置页面")
            yield Input(placeholder="用户名", id="username")
            yield Input(placeholder="邮箱", id="email")
            yield Button("保存", variant="success")
            yield Button("返回", id="back", variant="warning")
            yield Footer()

        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "back":
                self.app.pop_screen()

        def action_go_back(self) -> None:
            self.app.pop_screen()

    class AboutScreen(Screen):
        """关于屏幕"""

        BINDINGS = [("escape", "go_back", "返回")]

        def compose(self) -> ComposeResult:
            yield Header()
            yield Static("ℹ️ 关于")
            yield Static("Textual 多屏幕演示\n版本: 1.0.0")
            yield Button("返回", id="back")
            yield Footer()

        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "back":
                self.app.pop_screen()

        def action_go_back(self) -> None:
            self.app.pop_screen()

    class MultiScreenApp(App):
        def on_mount(self) -> None:
            self.push_screen(HomeScreen())

    print("示例1: 多屏幕管理")
    print("=" * 40)
    app = MultiScreenApp()
    app.run()
# endregion

# region 示例2: 模态对话框
if False:  # 改为 True 可运行此示例
    """
    ModalScreen 创建模态对话框
    阻止与底层屏幕的交互
    """

    class ConfirmDialog(ModalScreen[bool]):
        """确认对话框"""

        DEFAULT_CSS = """
        ConfirmDialog {
            align: center middle;
        }
        
        ConfirmDialog > Vertical {
            width: 50;
            height: auto;
            background: $surface;
            border: thick $primary;
            padding: 1 2;
        }
        
        ConfirmDialog #question {
            margin: 1;
            text-align: center;
        }
        
        ConfirmDialog Horizontal {
            height: auto;
            align: center middle;
            margin-top: 1;
        }
        
        ConfirmDialog Button {
            margin: 0 1;
        }
        """

        def __init__(self, question: str) -> None:
            super().__init__()
            self.question = question

        def compose(self) -> ComposeResult:
            with Vertical():
                yield Label("⚠️ 确认", id="title")
                yield Static(self.question, id="question")
                with Horizontal():
                    yield Button("确定", id="yes", variant="success")
                    yield Button("取消", id="no", variant="error")

        def on_button_pressed(self, event: Button.Pressed) -> None:
            self.dismiss(event.button.id == "yes")

    class ModalApp(App):
        CSS = """
        #status {
            margin: 1;
            padding: 1;
            background: $surface;
        }
        """

        def compose(self) -> ComposeResult:
            yield Header()
            yield Static("点击按钮打开对话框")
            yield Button("删除数据", id="delete", variant="error")
            yield Static("", id="status")
            yield Footer()

        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "delete":
                self.push_screen(
                    ConfirmDialog("确定要删除所有数据吗？"),
                    self.handle_confirm
                )

        def handle_confirm(self, confirmed: bool) -> None:
            """处理对话框结果"""
            status = self.query_one("#status", Static)
            if confirmed:
                status.update("✅ 数据已删除")
            else:
                status.update("❌ 操作已取消")

    print("示例2: 模态对话框")
    print("=" * 40)
    app = ModalApp()
    app.run()
# endregion

# region 示例3: 异步操作与加载指示器
if False:  # 改为 True 可运行此示例
    """
    Textual 完全支持 async/await
    可以执行异步操作而不阻塞 UI
    """

    class AsyncApp(App):
        CSS = """
        #result {
            height: 1fr;
            margin: 1;
            padding: 1;
            background: $surface;
        }
        
        LoadingIndicator {
            height: 3;
        }
        
        Horizontal {
            height: auto;
            margin: 1;
        }
        """

        def compose(self) -> ComposeResult:
            yield Header()
            with Horizontal():
                yield Button("获取数据", id="fetch", variant="primary")
                yield Button("清除", id="clear")
            yield LoadingIndicator(id="loading")
            yield Static("点击按钮获取数据", id="result")
            yield Footer()

        def on_mount(self) -> None:
            # 初始隐藏加载指示器
            self.query_one("#loading").display = False

        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "fetch":
                # 启动异步任务
                self.fetch_data()
            elif event.button.id == "clear":
                self.query_one("#result", Static).update("已清除")

        @work(exclusive=True)  # 使用 worker 装饰器
        async def fetch_data(self) -> None:
            """异步获取数据"""
            loading = self.query_one("#loading")
            result = self.query_one("#result", Static)

            # 显示加载指示器
            loading.display = True
            result.update("正在加载...")

            # 模拟网络请求
            await asyncio.sleep(2)

            # 隐藏加载指示器，显示结果
            loading.display = False
            result.update(
                "📊 数据加载完成!\n\n"
                "用户数: 1,234\n"
                "订单数: 5,678\n"
                "收入: ¥123,456"
            )

    print("示例3: 异步操作")
    print("=" * 40)
    app = AsyncApp()
    app.run()
# endregion

# region 示例4: DataTable 数据表格
if False:  # 改为 True 可运行此示例
    """
    DataTable 用于显示表格数据
    支持排序、选择、滚动等功能
    """

    class DataTableApp(App):
        CSS = """
        DataTable {
            height: 1fr;
            margin: 1;
        }
        
        #info {
            height: 3;
            margin: 1;
            padding: 1;
            background: $surface;
        }
        """

        BINDINGS = [
            ("a", "add_row", "添加行"),
            ("d", "delete_row", "删除行"),
        ]

        def compose(self) -> ComposeResult:
            yield Header()
            yield DataTable(id="table")
            yield Static("选择一行查看详情", id="info")
            yield Footer()

        def on_mount(self) -> None:
            table = self.query_one("#table", DataTable)
            # 添加列
            table.add_columns("ID", "姓名", "年龄", "城市")
            # 添加数据
            table.add_rows([
                (1, "张三", 25, "北京"),
                (2, "李四", 30, "上海"),
                (3, "王五", 28, "广州"),
                (4, "赵六", 35, "深圳"),
                (5, "钱七", 22, "杭州"),
            ])
            # 设置光标类型
            table.cursor_type = "row"

        def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
            """行被选中时触发"""
            info = self.query_one("#info", Static)
            row_data = event.data_table.get_row(event.row_key)
            info.update(f"选中: ID={row_data[0]}, 姓名={row_data[1]}, 年龄={row_data[2]}, 城市={row_data[3]}")

        def action_add_row(self) -> None:
            """添加新行"""
            table = self.query_one("#table", DataTable)
            row_count = table.row_count
            table.add_row(row_count + 1, f"新用户{row_count + 1}", 20, "未知")

        def action_delete_row(self) -> None:
            """删除当前行"""
            table = self.query_one("#table", DataTable)
            if table.cursor_row is not None:
                row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
                table.remove_row(row_key)

    print("示例4: DataTable 数据表格")
    print("=" * 40)
    app = DataTableApp()
    app.run()
# endregion

# region 示例5: Tree 树形视图
if False:  # 改为 True 可运行此示例
    """
    Tree 组件用于显示层级数据
    支持展开/折叠、选择等功能
    """

    class TreeApp(App):
        CSS = """
        Tree {
            height: 1fr;
            margin: 1;
            background: $surface;
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
            yield Tree("📁 项目根目录", id="tree")
            yield Static("点击节点查看详情", id="info")
            yield Footer()

        def on_mount(self) -> None:
            tree = self.query_one("#tree", Tree)

            # 构建树结构
            src = tree.root.add("📁 src", expand=True)
            src.add_leaf("📄 main.py")
            src.add_leaf("📄 utils.py")

            components = src.add("📁 components")
            components.add_leaf("📄 button.py")
            components.add_leaf("📄 input.py")
            components.add_leaf("📄 table.py")

            tests = tree.root.add("📁 tests")
            tests.add_leaf("📄 test_main.py")
            tests.add_leaf("📄 test_utils.py")

            tree.root.add_leaf("📄 README.md")
            tree.root.add_leaf("📄 pyproject.toml")

            # 展开根节点
            tree.root.expand()

        def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
            """节点被选中时触发"""
            info = self.query_one("#info", Static)
            node = event.node
            path = []
            current = node
            while current.parent:
                path.insert(0, str(current.label))
                current = current.parent
            info.update(f"路径: {' / '.join(path)}")

    print("示例5: Tree 树形视图")
    print("=" * 40)
    app = TreeApp()
    app.run()
# endregion

# region 示例6: 命令面板
if False:  # 改为 True 可运行此示例
    """
    Textual 内置命令面板功能
    按 Ctrl+P 打开命令面板
    """

    from textual.command import Hit, Hits, Provider

    class CustomCommands(Provider):
        """自定义命令提供者"""

        async def search(self, query: str) -> Hits:
            """搜索命令"""
            commands = [
                ("打开文件", "open_file", "打开一个文件"),
                ("保存文件", "save_file", "保存当前文件"),
                ("切换主题", "toggle_theme", "切换深色/浅色主题"),
                ("显示帮助", "show_help", "显示帮助信息"),
            ]

            for name, action, help_text in commands:
                if query.lower() in name.lower():
                    yield Hit(
                        1.0,  # 匹配分数
                        name,
                        help=help_text,
                        command=lambda a=action: self.app.action_custom(a),
                    )

    class CommandPaletteApp(App):
        CSS = """
        #status {
            margin: 1;
            padding: 1;
            background: $surface;
            height: 5;
        }
        """

        COMMANDS = {CustomCommands}  # 注册命令提供者

        BINDINGS = [
            ("ctrl+p", "command_palette", "命令面板"),
        ]

        def compose(self) -> ComposeResult:
            yield Header()
            yield Static(
                "按 Ctrl+P 打开命令面板\n"
                "输入命令名称进行搜索"
            )
            yield Static("等待命令...", id="status")
            yield Footer()

        def action_custom(self, action: str) -> None:
            """执行自定义命令"""
            status = self.query_one("#status", Static)
            messages = {
                "open_file": "📂 打开文件对话框",
                "save_file": "💾 文件已保存",
                "toggle_theme": "🎨 主题已切换",
                "show_help": "❓ 显示帮助信息",
            }
            status.update(messages.get(action, f"执行: {action}"))

            if action == "toggle_theme":
                self.theme = "textual-light" if self.theme == "textual-dark" else "textual-dark"

    print("示例6: 命令面板")
    print("=" * 40)
    app = CommandPaletteApp()
    app.run()
# endregion
