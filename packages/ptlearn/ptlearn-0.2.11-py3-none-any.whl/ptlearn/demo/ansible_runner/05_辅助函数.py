"""
Ansible Runner 辅助函数
======================
本文件演示 ansible-runner 提供的各种辅助函数。
这些函数封装了常用的 Ansible 命令行工具。

主要辅助函数:
- run_command(): 执行任意 Ansible 命令
- get_inventory(): 获取 inventory 信息
- get_ansible_config(): 获取 Ansible 配置
- get_plugin_docs(): 获取插件文档
- get_plugin_list(): 获取插件列表
"""

import ansible_runner
import tempfile
import json
from pathlib import Path

# region 示例1: 使用 run_command 执行命令
if True:  # 改为 False 可跳过此示例
    """
    run_command() 可以执行任意命令
    返回 (stdout, stderr, rc) 元组
    """
    print("=" * 60)
    print("示例1: run_command 执行命令")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        
        inventory_dir = base / "inventory"
        inventory_dir.mkdir()
        (inventory_dir / "hosts").write_text(
            "[local]\nlocalhost ansible_connection=local\n"
        )
        
        # 执行 ansible --version
        out, err, rc = ansible_runner.run_command(
            executable_cmd="ansible",
            cmdline_args=["--version"],
        )
        
        print(f"返回码: {rc}")
        print(f"输出 (前200字符):\n{out[:200]}...")
    print()
# endregion

# region 示例2: 获取 Inventory 信息
if True:  # 改为 False 可跳过此示例
    """
    get_inventory() 执行 ansible-inventory 命令
    可以获取主机列表、主机变量等信息
    
    action 参数:
    - 'list': 列出所有主机和组
    - 'host': 获取特定主机信息
    - 'graph': 显示 inventory 图形结构
    """
    print("=" * 60)
    print("示例2: 获取 Inventory 信息")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        
        # 创建一个复杂一点的 inventory
        inventory_file = base / "hosts"
        inventory_content = """
[webservers]
web1 ansible_host=192.168.1.10
web2 ansible_host=192.168.1.11

[dbservers]
db1 ansible_host=192.168.1.20

[all:vars]
ansible_connection=local
"""
        inventory_file.write_text(inventory_content)
        
        # 获取 inventory 列表
        out, err, rc = ansible_runner.get_inventory(
            action="list",
            inventories=[str(inventory_file)],
            response_format="json",
        )
        
        if rc == 0:
            try:
                inv_data = json.loads(out)
                print("主机组:")
                for group in inv_data.get("all", {}).get("children", []):
                    print(f"  - {group}")
                
                # 显示 webservers 组的主机
                if "webservers" in inv_data:
                    print("\nwebservers 组的主机:")
                    for host in inv_data["webservers"].get("hosts", []):
                        print(f"  - {host}")
            except json.JSONDecodeError:
                print(f"输出: {out}")
        else:
            print(f"错误: {err}")
    print()
# endregion

# region 示例3: 获取 Ansible 配置
if True:  # 改为 False 可跳过此示例
    """
    get_ansible_config() 执行 ansible-config 命令
    可以查看当前的 Ansible 配置
    
    action 参数:
    - 'list': 列出所有配置选项
    - 'dump': 显示当前配置值
    - 'view': 显示配置文件内容
    """
    print("=" * 60)
    print("示例3: 获取 Ansible 配置")
    print("=" * 60)
    
    # 获取当前生效的配置 (只显示已更改的)
    out, err, rc = ansible_runner.get_ansible_config(
        action="dump",
        only_changed=True,
    )
    
    if rc == 0:
        print("已更改的配置项:")
        lines = out.strip().split("\n")
        for line in lines[:10]:  # 只显示前10行
            if line.strip():
                print(f"  {line}")
        if len(lines) > 10:
            print(f"  ... 还有 {len(lines) - 10} 项")
    else:
        print(f"错误: {err}")
    print()
# endregion

# region 示例4: 获取插件列表
if True:  # 改为 False 可跳过此示例
    """
    get_plugin_list() 获取已安装的 Ansible 插件列表
    可以指定插件类型: module, callback, connection 等
    """
    print("=" * 60)
    print("示例4: 获取插件列表")
    print("=" * 60)
    
    # 获取 callback 插件列表
    out, err, rc = ansible_runner.get_plugin_list(
        plugin_type="callback",
        response_format="json",
    )
    
    if rc == 0:
        try:
            plugins = json.loads(out)
            print("Callback 插件 (前10个):")
            count = 0
            for name, info in plugins.items():
                if count >= 10:
                    break
                desc = info.get("description", [""])[0][:50]
                print(f"  - {name}: {desc}...")
                count += 1
        except json.JSONDecodeError:
            print(f"输出: {out[:500]}")
    else:
        print(f"错误: {err}")
    print()
# endregion

# region 示例5: 获取插件文档
if True:  # 改为 False 可跳过此示例
    """
    get_plugin_docs() 获取特定插件的详细文档
    对于了解模块参数很有帮助
    """
    print("=" * 60)
    print("示例5: 获取插件文档")
    print("=" * 60)
    
    # 获取 debug 模块的文档
    out, err, rc = ansible_runner.get_plugin_docs(
        plugin_names=["debug"],
        plugin_type="module",
        response_format="json",
    )
    
    if rc == 0:
        try:
            docs = json.loads(out)
            debug_doc = docs.get("debug", {}).get("doc", {})
            
            print("模块: debug")
            print(f"简介: {debug_doc.get('short_description', 'N/A')}")
            print(f"描述: {debug_doc.get('description', ['N/A'])[0][:100]}...")
            
            # 显示参数
            options = debug_doc.get("options", {})
            print("\n参数:")
            for opt_name, opt_info in list(options.items())[:5]:
                desc = opt_info.get("description", [""])[0][:50]
                print(f"  - {opt_name}: {desc}...")
        except json.JSONDecodeError:
            print(f"输出: {out[:500]}")
    else:
        print(f"错误: {err}")
    print()
# endregion

# region 示例6: 使用 run_command 执行 ansible-playbook
if True:  # 改为 False 可跳过此示例
    """
    run_command 也可以用来执行 ansible-playbook
    这提供了更底层的控制
    """
    print("=" * 60)
    print("示例6: run_command 执行 playbook")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        
        # 创建 inventory
        inventory_file = base / "hosts"
        inventory_file.write_text("localhost ansible_connection=local\n")
        
        # 创建 playbook
        playbook_file = base / "test.yml"
        playbook_content = """
---
- name: 测试
  hosts: localhost
  gather_facts: false
  tasks:
    - name: 打印消息
      debug:
        msg: "通过 run_command 执行"
"""
        playbook_file.write_text(playbook_content)
        
        # 使用 run_command 执行
        out, err, rc = ansible_runner.run_command(
            executable_cmd="ansible-playbook",
            cmdline_args=[
                str(playbook_file),
                "-i", str(inventory_file),
            ],
        )
        
        print(f"返回码: {rc}")
        # 提取关键输出
        for line in out.split("\n"):
            if "TASK" in line or "PLAY" in line or "ok=" in line:
                print(f"  {line}")
    print()
# endregion
