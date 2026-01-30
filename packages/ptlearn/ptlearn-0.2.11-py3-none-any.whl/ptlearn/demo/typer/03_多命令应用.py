"""
Typer 多命令应用
================
学习如何创建包含多个子命令的 CLI 应用，类似 git、docker 等工具。
"""

import typer

# region 示例1: 基础多命令应用
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例1: 基础多命令应用")
    print("=" * 50)

    # 创建主应用
    app = typer.Typer(help="用户管理命令行工具")

    @app.command()
    def create(username: str, email: str):
        """创建新用户"""
        print(f"创建用户: {username}")
        print(f"邮箱: {email}")

    @app.command()
    def delete(username: str, force: bool = False):
        """删除用户"""
        if force:
            print(f"强制删除用户: {username}")
        else:
            print(f"删除用户: {username} (需要确认)")

    @app.command()
    def list_users():
        """列出所有用户"""
        print("用户列表:")
        print("  1. admin")
        print("  2. guest")
        print("  3. developer")

    # 演示各个命令
    print("演示 create 命令:")
    create("新用户", "user@example.com")

    print("\n演示 delete 命令:")
    delete("旧用户", force=True)

    print("\n演示 list 命令:")
    list_users()

    print("\n命令行使用方式:")
    print("  python script.py create 新用户 user@example.com")
    print("  python script.py delete 旧用户 --force")
    print("  python script.py list-users")
    print("  python script.py --help  # 查看所有命令")
    print()
# endregion

# region 示例2: 使用 add_typer 组织子命令组
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例2: 使用 add_typer 组织子命令组")
    print("=" * 50)

    # 主应用
    main_app = typer.Typer(help="项目管理工具")

    # 用户相关子命令组
    users_app = typer.Typer(help="用户管理命令")

    @users_app.command("list")
    def users_list():
        """列出所有用户"""
        print("用户: admin, guest, developer")

    @users_app.command("add")
    def users_add(name: str):
        """添加用户"""
        print(f"添加用户: {name}")

    # 项目相关子命令组
    projects_app = typer.Typer(help="项目管理命令")

    @projects_app.command("list")
    def projects_list():
        """列出所有项目"""
        print("项目: web-app, api-server, mobile-app")

    @projects_app.command("create")
    def projects_create(name: str, template: str = "default"):
        """创建新项目"""
        print(f"创建项目: {name} (模板: {template})")

    # 将子命令组添加到主应用
    main_app.add_typer(users_app, name="users")
    main_app.add_typer(projects_app, name="projects")

    # 演示
    print("演示嵌套命令结构:")
    print("\n用户命令:")
    users_list()
    users_add("新成员")

    print("\n项目命令:")
    projects_list()
    projects_create("my-project", "react")

    print("\n命令行使用方式:")
    print("  python script.py users list")
    print("  python script.py users add 新成员")
    print("  python script.py projects list")
    print("  python script.py projects create my-project --template react")
    print()
# endregion

# region 示例3: 命令别名
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例3: 命令别名与命名")
    print("=" * 50)

    app3 = typer.Typer()

    # 使用 name 参数自定义命令名称
    @app3.command(name="ls")
    def list_items():
        """列出项目 (别名: ls)"""
        print("项目列表...")

    @app3.command(name="rm")
    def remove_item(item: str):
        """删除项目 (别名: rm)"""
        print(f"删除: {item}")

    # 演示
    list_items()
    remove_item("old-file")

    print("\n命令行使用方式:")
    print("  python script.py ls")
    print("  python script.py rm old-file")
    print()
# endregion

# region 示例4: 命令回调 (全局选项)
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例4: 命令回调 (全局选项)")
    print("=" * 50)

    app4 = typer.Typer()

    # 使用回调定义在所有命令之前执行的逻辑和全局选项
    @app4.callback()
    def main_callback(
        verbose: bool = typer.Option(False, "--verbose", "-v", help="详细输出"),
        config: str = typer.Option("config.yaml", "--config", "-c", help="配置文件"),
    ):
        """
        一个带有全局选项的 CLI 应用。

        全局选项可以在任何子命令之前使用。
        """
        # 这里可以处理全局配置
        if verbose:
            print(f"[详细模式] 使用配置文件: {config}")

    @app4.command()
    def init():
        """初始化项目"""
        print("初始化项目...")

    @app4.command()
    def build():
        """构建项目"""
        print("构建项目...")

    # 演示
    print("演示回调效果:")
    main_callback(verbose=True, config="custom.yaml")
    init()

    print("\n命令行使用方式:")
    print("  python script.py --verbose init")
    print("  python script.py -c custom.yaml build")
    print("  python script.py build  # 使用默认配置")
    print()
# endregion

# region 示例5: 默认命令
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例5: 默认命令")
    print("=" * 50)

    # 当只有一个命令时，它会自动成为默认命令
    single_app = typer.Typer()

    @single_app.command()
    def process(filename: str):
        """处理文件 - 这是唯一的命令，会自动成为默认命令"""
        print(f"处理文件: {filename}")

    # 演示
    process("data.txt")

    print("\n命令行使用方式:")
    print("  python script.py data.txt")
    print("  # 不需要指定命令名，直接传参数即可")
    print()

    # 使用 invoke_without_command 处理无子命令的情况
    app_with_default = typer.Typer(invoke_without_command=True)

    @app_with_default.callback()
    def default_action(
        ctx: typer.Context,
        version: bool = typer.Option(False, "--version", "-V"),
    ):
        """主入口，支持 --version 选项"""
        if version:
            print("版本: 1.0.0")
            raise typer.Exit()
        # 如果没有子命令被调用
        if ctx.invoked_subcommand is None:
            print("欢迎使用! 使用 --help 查看帮助")

    @app_with_default.command()
    def run():
        """运行应用"""
        print("运行中...")

    print("\ninvoke_without_command 示例:")
    default_action(typer.Context(app_with_default), version=True)

    print("\n命令行使用方式:")
    print("  python script.py          # 显示欢迎信息")
    print("  python script.py --version  # 显示版本")
    print("  python script.py run       # 运行子命令")
    print()
# endregion
