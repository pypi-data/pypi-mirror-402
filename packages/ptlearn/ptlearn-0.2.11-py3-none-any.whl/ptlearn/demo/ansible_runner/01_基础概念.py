"""
Ansible Runner 基础概念
=======================
ansible-runner 是一个 Python 库和命令行工具，用于以编程方式与 Ansible 交互。
它提供了稳定一致的接口抽象，适用于需要在 Python 代码中调用 Ansible 的场景。

安装: pip install ansible-runner
前提: 需要安装 ansible-core

官方文档: https://ansible.readthedocs.io/projects/runner/en/stable/
"""

import ansible_runner
import tempfile
import os
from pathlib import Path

# region 示例1: 使用 run() 执行简单的 ad-hoc 命令
if True:  # 改为 False 可跳过此示例
    """
    ansible_runner.run() 是最常用的入口函数
    它会在前台执行 Ansible 并返回 Runner 对象
    
    关键参数:
    - private_data_dir: 工作目录，存放 inventory、playbook 等
    - host_pattern: 目标主机模式
    - module: 要执行的 Ansible 模块
    - module_args: 模块参数
    """
    print("=" * 60)
    print("示例1: 使用 run() 执行 ad-hoc 命令")
    print("=" * 60)
    
    # 创建临时工作目录
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建 inventory 文件
        inventory_dir = Path(tmpdir) / "inventory"
        inventory_dir.mkdir()
        (inventory_dir / "hosts").write_text("localhost ansible_connection=local\n")
        
        # 执行 ping 模块
        result = ansible_runner.run(
            private_data_dir=tmpdir,
            host_pattern="localhost",
            module="ping",
        )
        
        # 检查执行结果
        print(f"状态: {result.status}")  # successful, failed, canceled
        print(f"返回码: {result.rc}")
        print(f"统计信息: {result.stats}")
    print()
# endregion

# region 示例2: 理解 Runner 对象的属性
if True:  # 改为 False 可跳过此示例
    """
    Runner 对象包含执行结果的所有信息:
    - status: 执行状态 (successful/failed/canceled)
    - rc: 返回码
    - stats: playbook 统计信息
    - events: 事件生成器
    - stdout: 标准输出文件句柄
    """
    print("=" * 60)
    print("示例2: Runner 对象属性详解")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        inventory_dir = Path(tmpdir) / "inventory"
        inventory_dir.mkdir()
        (inventory_dir / "hosts").write_text("localhost ansible_connection=local\n")
        
        result = ansible_runner.run(
            private_data_dir=tmpdir,
            host_pattern="localhost",
            module="setup",
            module_args="filter=ansible_hostname",
            quiet=True,  # 减少输出
        )
        
        print(f"执行状态: {result.status}")
        print(f"返回码: {result.rc}")
        
        # 遍历事件
        event_count = 0
        for event in result.events:
            event_count += 1
            if event.get("event") == "runner_on_ok":
                # 获取模块返回的数据
                event_data = event.get("event_data", {})
                res = event_data.get("res", {})
                facts = res.get("ansible_facts", {})
                if facts:
                    print(f"主机名: {facts.get('ansible_hostname', 'N/A')}")
        
        print(f"总事件数: {event_count}")
    print()
# endregion

# region 示例3: 使用 module_args 传递参数
if True:  # 改为 False 可跳过此示例
    """
    module_args 用于向 Ansible 模块传递参数
    可以是字符串格式或字典格式
    """
    print("=" * 60)
    print("示例3: 模块参数传递")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        inventory_dir = Path(tmpdir) / "inventory"
        inventory_dir.mkdir()
        (inventory_dir / "hosts").write_text("localhost ansible_connection=local\n")
        
        # 使用 debug 模块输出消息
        result = ansible_runner.run(
            private_data_dir=tmpdir,
            host_pattern="localhost",
            module="debug",
            module_args="msg='Hello from ansible-runner!'",
            quiet=True,
        )
        
        # 从事件中提取 debug 输出
        for event in result.events:
            if event.get("event") == "runner_on_ok":
                res = event.get("event_data", {}).get("res", {})
                msg = res.get("msg")
                if msg:
                    print(f"Debug 输出: {msg}")
        
        print(f"执行状态: {result.status}")
    print()
# endregion

# region 示例4: 使用 extravars 传递额外变量
if True:  # 改为 False 可跳过此示例
    """
    extravars 参数用于传递额外的变量给 Ansible
    相当于命令行的 -e 或 --extra-vars 选项
    """
    print("=" * 60)
    print("示例4: 使用 extravars 传递变量")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        inventory_dir = Path(tmpdir) / "inventory"
        inventory_dir.mkdir()
        (inventory_dir / "hosts").write_text("localhost ansible_connection=local\n")
        
        # 通过 extravars 传递变量
        result = ansible_runner.run(
            private_data_dir=tmpdir,
            host_pattern="localhost",
            module="debug",
            module_args="msg={{ my_message }}",
            extravars={
                "my_message": "这是通过 extravars 传递的消息！"
            },
            quiet=True,
        )
        
        for event in result.events:
            if event.get("event") == "runner_on_ok":
                res = event.get("event_data", {}).get("res", {})
                msg = res.get("msg")
                if msg:
                    print(f"输出: {msg}")
    print()
# endregion

# region 示例5: 检查执行状态和错误处理
if True:  # 改为 False 可跳过此示例
    """
    正确处理执行结果和错误是很重要的
    status 可能的值: successful, failed, canceled, timeout
    """
    print("=" * 60)
    print("示例5: 状态检查与错误处理")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        inventory_dir = Path(tmpdir) / "inventory"
        inventory_dir.mkdir()
        (inventory_dir / "hosts").write_text("localhost ansible_connection=local\n")
        
        # 执行一个会成功的命令
        result = ansible_runner.run(
            private_data_dir=tmpdir,
            host_pattern="localhost",
            module="command",
            module_args="echo 'Hello World'",
            quiet=True,
        )
        
        # 根据状态进行处理
        if result.status == "successful":
            print("✓ 执行成功!")
            # 获取命令输出
            for event in result.events:
                if event.get("event") == "runner_on_ok":
                    res = event.get("event_data", {}).get("res", {})
                    stdout = res.get("stdout", "")
                    if stdout:
                        print(f"  命令输出: {stdout}")
        elif result.status == "failed":
            print("✗ 执行失败!")
            print(f"  返回码: {result.rc}")
        else:
            print(f"? 其他状态: {result.status}")
    print()
# endregion
