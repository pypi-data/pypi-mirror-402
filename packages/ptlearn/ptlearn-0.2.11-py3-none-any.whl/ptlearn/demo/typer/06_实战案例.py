"""
Typer 实战案例
==============
通过完整的实战案例，学习如何构建专业的 CLI 应用。
"""

import typer
from enum import Enum
from pathlib import Path
from typing import Optional, List
from datetime import datetime
import json

# region 示例1: 文件管理工具
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例1: 文件管理工具")
    print("=" * 50)

    file_app = typer.Typer(
        name="fileutil",
        help="文件管理实用工具",
        no_args_is_help=True,  # 无参数时显示帮助
    )

    @file_app.command()
    def info(
        path: Path = typer.Argument(..., help="文件或目录路径"),
        json_output: bool = typer.Option(False, "--json", "-j", help="JSON格式输出"),
    ):
        """显示文件/目录信息"""
        # 模拟文件信息
        file_info = {
            "path": str(path),
            "name": path.name,
            "suffix": path.suffix,
            "is_file": True,
            "size": 1024,
            "modified": datetime.now().isoformat(),
        }

        if json_output:
            print(json.dumps(file_info, indent=2, ensure_ascii=False))
        else:
            print(f"路径: {file_info['path']}")
            print(f"名称: {file_info['name']}")
            print(f"类型: {'文件' if file_info['is_file'] else '目录'}")
            print(f"大小: {file_info['size']} 字节")
            print(f"修改时间: {file_info['modified']}")

    @file_app.command()
    def find(
        pattern: str = typer.Argument(..., help="搜索模式 (glob)"),
        path: Path = typer.Option(Path("."), "--path", "-p", help="搜索路径"),
        type_filter: Optional[str] = typer.Option(
            None, "--type", "-t", help="类型: file/dir"
        ),
    ):
        """查找文件"""
        print(f"在 {path} 中查找: {pattern}")
        if type_filter:
            print(f"类型过滤: {type_filter}")

        # 模拟搜索结果
        results = ["file1.txt", "file2.txt", "subdir/file3.txt"]
        for r in results:
            typer.secho(f"  {r}", fg=typer.colors.CYAN)

    # 演示
    print("演示 info 命令:")
    info(Path("example/document.pdf"))

    print("\n演示 info --json 命令:")
    info(Path("example/document.pdf"), json_output=True)

    print("\n演示 find 命令:")
    find("*.txt", Path("/home/user"), "file")

    print()
# endregion

# region 示例2: 任务管理器
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例2: 任务管理器")
    print("=" * 50)

    class Priority(str, Enum):
        low = "low"
        medium = "medium"
        high = "high"

    class Status(str, Enum):
        pending = "pending"
        in_progress = "in_progress"
        done = "done"

    # 模拟数据存储
    tasks_db: List[dict] = [
        {"id": 1, "title": "学习 Typer", "priority": "high", "status": "in_progress"},
        {"id": 2, "title": "编写文档", "priority": "medium", "status": "pending"},
        {"id": 3, "title": "代码审查", "priority": "low", "status": "done"},
    ]

    task_app = typer.Typer(help="任务管理工具")

    @task_app.command("list")
    def list_tasks(
        status: Optional[Status] = typer.Option(None, "--status", "-s"),
        priority: Optional[Priority] = typer.Option(None, "--priority", "-p"),
    ):
        """列出所有任务"""
        filtered = tasks_db

        if status:
            filtered = [t for t in filtered if t["status"] == status.value]
        if priority:
            filtered = [t for t in filtered if t["priority"] == priority.value]

        if not filtered:
            typer.secho("没有找到任务", fg=typer.colors.YELLOW)
            return

        print(f"{'ID':<4} {'标题':<20} {'优先级':<10} {'状态':<12}")
        print("-" * 50)
        for task in filtered:
            # 根据优先级设置颜色
            color = {
                "high": typer.colors.RED,
                "medium": typer.colors.YELLOW,
                "low": typer.colors.GREEN,
            }.get(task["priority"], typer.colors.WHITE)

            line = f"{task['id']:<4} {task['title']:<20} {task['priority']:<10} {task['status']:<12}"
            typer.secho(line, fg=color)

    @task_app.command("add")
    def add_task(
        title: str = typer.Argument(..., help="任务标题"),
        priority: Priority = typer.Option(Priority.medium, "--priority", "-p"),
    ):
        """添加新任务"""
        new_id = max(t["id"] for t in tasks_db) + 1
        new_task = {
            "id": new_id,
            "title": title,
            "priority": priority.value,
            "status": "pending",
        }
        tasks_db.append(new_task)
        typer.secho(f"✓ 任务已添加 (ID: {new_id})", fg=typer.colors.GREEN)

    @task_app.command("done")
    def complete_task(
        task_id: int = typer.Argument(..., help="任务ID"),
    ):
        """标记任务为完成"""
        for task in tasks_db:
            if task["id"] == task_id:
                task["status"] = "done"
                typer.secho(f"✓ 任务 '{task['title']}' 已完成", fg=typer.colors.GREEN)
                return

        typer.secho(f"✗ 未找到 ID 为 {task_id} 的任务", fg=typer.colors.RED)

    # 演示
    print("任务列表:")
    list_tasks(status=None, priority=None)

    print("\n添加任务:")
    add_task("部署应用", Priority.high)

    print("\n更新后的任务列表:")
    list_tasks(status=None, priority=None)

    print("\n完成任务:")
    complete_task(1)

    print("\n高优先级任务:")
    list_tasks(status=None, priority=Priority.high)

    print()
# endregion

# region 示例3: 完整应用结构
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例3: 完整应用结构")
    print("=" * 50)

    print("""
推荐的项目结构:

myapp/
├── __init__.py
├── __main__.py      # 使得可以 python -m myapp 运行
├── main.py          # 主应用入口
├── cli/
│   ├── __init__.py
│   ├── app.py       # Typer 应用定义
│   ├── users.py     # 用户相关命令
│   └── projects.py  # 项目相关命令
├── core/
│   ├── __init__.py
│   ├── config.py    # 配置管理
│   └── database.py  # 数据访问
└── utils/
    ├── __init__.py
    └── helpers.py   # 工具函数

__main__.py 内容:
```python
from myapp.cli.app import app

if __name__ == "__main__":
    app()
```

cli/app.py 内容:
```python
import typer
from .users import users_app
from .projects import projects_app

app = typer.Typer(
    name="myapp",
    help="我的应用程序",
    no_args_is_help=True,
)

# 注册子命令组
app.add_typer(users_app, name="users")
app.add_typer(projects_app, name="projects")

@app.command()
def version():
    \"\"\"显示版本信息\"\"\"
    typer.echo("myapp v1.0.0")

@app.callback()
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    config: str = typer.Option("config.yaml", "--config", "-c"),
):
    \"\"\"应用主入口\"\"\"
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["config"] = config
```
""")
    print()
# endregion

# region 示例4: 配合 Rich 美化输出
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例4: 配合 Rich 美化输出")
    print("=" * 50)

    # Typer 与 Rich 天然集成
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel

        console = Console()

        # 创建精美的表格
        table = Table(title="任务列表", show_header=True, header_style="bold magenta")
        table.add_column("ID", style="cyan", width=6)
        table.add_column("任务", style="white")
        table.add_column("优先级", justify="center")
        table.add_column("状态", justify="center")

        table.add_row("1", "学习 Typer", "[red]高[/red]", "[yellow]进行中[/yellow]")
        table.add_row("2", "编写文档", "[yellow]中[/yellow]", "[blue]待处理[/blue]")
        table.add_row("3", "代码审查", "[green]低[/green]", "[green]已完成[/green]")

        console.print(table)

        # 创建面板
        console.print()
        console.print(
            Panel.fit(
                "[bold green]✓ 操作成功![/bold green]\n\n任务已添加到列表中。",
                title="成功",
                border_style="green",
            )
        )

    except ImportError:
        print("(需要安装 rich: pip install rich)")
        print()
        print("Rich + Typer 代码示例:")
        print("""
    from rich.console import Console
    from rich.table import Table

    console = Console()

    @app.command()
    def list_items():
        table = Table(title="项目列表")
        table.add_column("ID", style="cyan")
        table.add_column("名称", style="green")

        for item in items:
            table.add_row(str(item.id), item.name)

        console.print(table)
""")

    print()
# endregion

# region 示例5: 使用 PyPI 发布 CLI 工具
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例5: 使用 PyPI 发布 CLI 工具")
    print("=" * 50)

    print("""
pyproject.toml 配置示例 (使用 Poetry):

```toml
[tool.poetry]
name = "myapp"
version = "1.0.0"
description = "我的命令行工具"
authors = ["Your Name <your@email.com>"]

[tool.poetry.dependencies]
python = "^3.8"
typer = {extras = ["all"], version = "^0.9.0"}

[tool.poetry.scripts]
myapp = "myapp.cli.app:app"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

pyproject.toml 配置示例 (使用 setuptools):

```toml
[project]
name = "myapp"
version = "1.0.0"
dependencies = [
    "typer[all]>=0.9.0",
]

[project.scripts]
myapp = "myapp.cli.app:app"
```

安装后可以直接使用 myapp 命令:

    $ myapp --help
    $ myapp users list
    $ myapp projects create new-project
""")
    print()
# endregion
