"""
Ansible Runner 执行 Playbook
============================
本文件演示如何使用 ansible-runner 执行 Ansible Playbook。
这是 ansible-runner 最常见的使用场景。

Playbook 需要放在 private_data_dir/project/ 目录下
"""

import ansible_runner
import tempfile
from pathlib import Path

# region 示例1: 执行简单的 Playbook
if True:  # 改为 False 可跳过此示例
    """
    执行 Playbook 需要:
    1. 在 private_data_dir/project/ 下创建 playbook 文件
    2. 在 private_data_dir/inventory/ 下创建 inventory 文件
    3. 使用 playbook 参数指定要执行的 playbook 文件名
    """
    print("=" * 60)
    print("示例1: 执行简单的 Playbook")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        
        # 创建 inventory
        inventory_dir = base / "inventory"
        inventory_dir.mkdir()
        (inventory_dir / "hosts").write_text(
            "localhost ansible_connection=local\n"
        )
        
        # 创建 project 目录和 playbook
        project_dir = base / "project"
        project_dir.mkdir()
        
        playbook_content = """
---
- name: 简单演示 Playbook
  hosts: localhost
  gather_facts: false
  tasks:
    - name: 打印欢迎消息
      debug:
        msg: "欢迎使用 ansible-runner!"
    
    - name: 显示当前时间
      command: date
      register: date_result
    
    - name: 输出时间
      debug:
        msg: "当前时间: {{ date_result.stdout }}"
"""
        (project_dir / "hello.yml").write_text(playbook_content)
        
        # 执行 playbook
        result = ansible_runner.run(
            private_data_dir=tmpdir,
            playbook="hello.yml",
        )
        
        print(f"执行状态: {result.status}")
        print(f"返回码: {result.rc}")
    print()
# endregion

# region 示例2: 带变量的 Playbook
if True:  # 改为 False 可跳过此示例
    """
    通过 extravars 向 Playbook 传递变量
    这些变量在 Playbook 中可以直接使用
    """
    print("=" * 60)
    print("示例2: 带变量的 Playbook")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        
        # 创建 inventory
        inventory_dir = base / "inventory"
        inventory_dir.mkdir()
        (inventory_dir / "hosts").write_text(
            "localhost ansible_connection=local\n"
        )
        
        # 创建 playbook
        project_dir = base / "project"
        project_dir.mkdir()
        
        playbook_content = """
---
- name: 变量演示
  hosts: localhost
  gather_facts: false
  tasks:
    - name: 显示用户信息
      debug:
        msg: "用户: {{ username }}, 环境: {{ environment }}"
    
    - name: 根据环境显示不同消息
      debug:
        msg: "这是生产环境，请谨慎操作！"
      when: environment == "production"
    
    - name: 开发环境消息
      debug:
        msg: "开发环境，可以自由测试"
      when: environment == "development"
"""
        (project_dir / "vars_demo.yml").write_text(playbook_content)
        
        # 执行并传递变量
        result = ansible_runner.run(
            private_data_dir=tmpdir,
            playbook="vars_demo.yml",
            extravars={
                "username": "admin",
                "environment": "development",
            },
            quiet=True,
        )
        
        # 提取 debug 消息
        for event in result.events:
            if event.get("event") == "runner_on_ok":
                res = event.get("event_data", {}).get("res", {})
                msg = res.get("msg")
                if msg:
                    print(f"  {msg}")
        
        print(f"\n执行状态: {result.status}")
    print()
# endregion

# region 示例3: 使用 Tags 选择性执行任务
if True:  # 改为 False 可跳过此示例
    """
    使用 tags 参数可以只执行带有特定标签的任务
    使用 skip_tags 可以跳过特定标签的任务
    """
    print("=" * 60)
    print("示例3: 使用 Tags 选择性执行")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        
        inventory_dir = base / "inventory"
        inventory_dir.mkdir()
        (inventory_dir / "hosts").write_text(
            "localhost ansible_connection=local\n"
        )
        
        project_dir = base / "project"
        project_dir.mkdir()
        
        playbook_content = """
---
- name: Tags 演示
  hosts: localhost
  gather_facts: false
  tasks:
    - name: 配置任务
      debug:
        msg: "执行配置..."
      tags: [config]
    
    - name: 部署任务
      debug:
        msg: "执行部署..."
      tags: [deploy]
    
    - name: 测试任务
      debug:
        msg: "执行测试..."
      tags: [test]
    
    - name: 清理任务
      debug:
        msg: "执行清理..."
      tags: [cleanup]
"""
        (project_dir / "tags_demo.yml").write_text(playbook_content)
        
        # 只执行 deploy 和 test 标签的任务
        print("只执行 deploy 和 test 标签:")
        result = ansible_runner.run(
            private_data_dir=tmpdir,
            playbook="tags_demo.yml",
            tags=["deploy", "test"],
            quiet=True,
        )
        
        for event in result.events:
            if event.get("event") == "runner_on_ok":
                task = event.get("event_data", {}).get("task", "")
                print(f"  ✓ {task}")
    print()
# endregion

# region 示例4: 限制目标主机
if True:  # 改为 False 可跳过此示例
    """
    使用 limit 参数可以限制 Playbook 只在特定主机上执行
    相当于 ansible-playbook 的 --limit 选项
    """
    print("=" * 60)
    print("示例4: 限制目标主机")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        
        inventory_dir = base / "inventory"
        inventory_dir.mkdir()
        
        # 创建包含多个主机的 inventory
        inventory_content = """
[webservers]
localhost ansible_connection=local

[dbservers]
localhost ansible_connection=local
"""
        (inventory_dir / "hosts").write_text(inventory_content)
        
        project_dir = base / "project"
        project_dir.mkdir()
        
        playbook_content = """
---
- name: 多主机组演示
  hosts: all
  gather_facts: false
  tasks:
    - name: 显示主机组
      debug:
        msg: "在主机 {{ inventory_hostname }} 上执行"
"""
        (project_dir / "limit_demo.yml").write_text(playbook_content)
        
        # 只在 webservers 组执行
        print("限制只在 webservers 组执行:")
        result = ansible_runner.run(
            private_data_dir=tmpdir,
            playbook="limit_demo.yml",
            limit="webservers",
            quiet=True,
        )
        
        print(f"执行状态: {result.status}")
    print()
# endregion

# region 示例5: 使用 cmdline 传递额外命令行参数
if True:  # 改为 False 可跳过此示例
    """
    cmdline 参数允许传递任意 ansible-playbook 命令行参数
    这提供了最大的灵活性
    """
    print("=" * 60)
    print("示例5: 使用 cmdline 传递命令行参数")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        
        inventory_dir = base / "inventory"
        inventory_dir.mkdir()
        (inventory_dir / "hosts").write_text(
            "localhost ansible_connection=local\n"
        )
        
        project_dir = base / "project"
        project_dir.mkdir()
        
        playbook_content = """
---
- name: Cmdline 演示
  hosts: localhost
  gather_facts: false
  tasks:
    - name: 显示变量
      debug:
        msg: "app_name={{ app_name }}, version={{ version }}"
"""
        (project_dir / "cmdline_demo.yml").write_text(playbook_content)
        
        # 使用 cmdline 传递额外参数
        result = ansible_runner.run(
            private_data_dir=tmpdir,
            playbook="cmdline_demo.yml",
            cmdline="-e app_name=myapp -e version=1.0.0",
            quiet=True,
        )
        
        for event in result.events:
            if event.get("event") == "runner_on_ok":
                res = event.get("event_data", {}).get("res", {})
                msg = res.get("msg")
                if msg:
                    print(f"  {msg}")
        
        print(f"执行状态: {result.status}")
    print()
# endregion
