"""
Ansible Runner 异步执行
======================
本文件演示如何使用 ansible-runner 的异步执行功能。
异步执行允许在后台运行 Ansible，同时可以监控执行进度。

主要函数:
- run_async(): 异步执行，返回 (thread, runner) 元组
"""

import ansible_runner
import tempfile
import time
from pathlib import Path

# region 示例1: 基本异步执行
if True:  # 改为 False 可跳过此示例
    """
    run_async() 会立即返回，不等待执行完成
    返回一个元组: (thread, runner)
    - thread: 执行线程对象
    - runner: Runner 对象，可用于检查状态
    """
    print("=" * 60)
    print("示例1: 基本异步执行")
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
        
        # 创建一个需要一点时间执行的 playbook
        playbook_content = """
---
- name: 异步演示
  hosts: localhost
  gather_facts: false
  tasks:
    - name: 任务1
      debug:
        msg: "开始执行任务1"
    
    - name: 模拟耗时操作
      pause:
        seconds: 2
    
    - name: 任务2
      debug:
        msg: "任务2完成"
"""
        (project_dir / "async_demo.yml").write_text(playbook_content)
        
        # 异步执行
        thread, runner = ansible_runner.run_async(
            private_data_dir=tmpdir,
            playbook="async_demo.yml",
            quiet=True,
        )
        
        print("Playbook 已在后台启动...")
        print(f"初始状态: {runner.status}")
        
        # 等待执行完成
        while thread.is_alive():
            print(f"  执行中... 状态: {runner.status}")
            time.sleep(0.5)
        
        print(f"最终状态: {runner.status}")
        print(f"返回码: {runner.rc}")
    print()
# endregion

# region 示例2: 实时监控事件
if True:  # 改为 False 可跳过此示例
    """
    在异步执行过程中，可以实时获取事件
    这对于构建进度显示或日志记录很有用
    """
    print("=" * 60)
    print("示例2: 实时监控事件")
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
- name: 事件监控演示
  hosts: localhost
  gather_facts: false
  tasks:
    - name: 步骤1 - 初始化
      debug:
        msg: "初始化完成"
    
    - name: 步骤2 - 处理数据
      debug:
        msg: "数据处理完成"
    
    - name: 步骤3 - 清理
      debug:
        msg: "清理完成"
"""
        (project_dir / "events_demo.yml").write_text(playbook_content)
        
        # 用于收集事件的列表
        collected_events = []
        
        # 定义事件处理器
        def event_handler(event):
            event_type = event.get("event", "")
            if event_type == "runner_on_ok":
                task = event.get("event_data", {}).get("task", "")
                collected_events.append(f"✓ {task}")
            return True  # 返回 True 保留事件
        
        thread, runner = ansible_runner.run_async(
            private_data_dir=tmpdir,
            playbook="events_demo.yml",
            event_handler=event_handler,
            quiet=True,
        )
        
        # 等待完成
        thread.join()
        
        print("收集到的事件:")
        for event in collected_events:
            print(f"  {event}")
        
        print(f"\n执行状态: {runner.status}")
    print()
# endregion

# region 示例3: 使用 cancel_callback 取消执行
if True:  # 改为 False 可跳过此示例
    """
    cancel_callback 允许在执行过程中取消 Ansible 进程
    回调函数返回 True 时会取消执行
    """
    print("=" * 60)
    print("示例3: 取消执行")
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
- name: 可取消的任务
  hosts: localhost
  gather_facts: false
  tasks:
    - name: 任务1
      debug:
        msg: "任务1"
    
    - name: 长时间任务
      pause:
        seconds: 10
    
    - name: 任务2 (不会执行)
      debug:
        msg: "任务2"
"""
        (project_dir / "cancel_demo.yml").write_text(playbook_content)
        
        # 计数器，用于在一定时间后取消
        start_time = time.time()
        
        def cancel_callback():
            # 1秒后取消执行
            elapsed = time.time() - start_time
            if elapsed > 1:
                print("  触发取消...")
                return True
            return False
        
        thread, runner = ansible_runner.run_async(
            private_data_dir=tmpdir,
            playbook="cancel_demo.yml",
            cancel_callback=cancel_callback,
            quiet=True,
        )
        
        print("开始执行，1秒后将取消...")
        thread.join()
        
        print(f"最终状态: {runner.status}")  # 应该是 canceled
    print()
# endregion

# region 示例4: 使用 finished_callback
if True:  # 改为 False 可跳过此示例
    """
    finished_callback 在 Ansible 执行完成后立即调用
    可用于执行清理操作或发送通知
    """
    print("=" * 60)
    print("示例4: 完成回调")
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
- name: 完成回调演示
  hosts: localhost
  gather_facts: false
  tasks:
    - name: 执行任务
      debug:
        msg: "任务执行中..."
"""
        (project_dir / "finished_demo.yml").write_text(playbook_content)
        
        # 完成回调
        def finished_callback(runner):
            print(f"  [回调] 执行已完成!")
            print(f"  [回调] 状态: {runner.status}")
            print(f"  [回调] 返回码: {runner.rc}")
        
        thread, runner = ansible_runner.run_async(
            private_data_dir=tmpdir,
            playbook="finished_demo.yml",
            finished_callback=finished_callback,
            quiet=True,
        )
        
        print("等待执行完成...")
        thread.join()
        print("主线程继续...")
    print()
# endregion

# region 示例5: 使用 status_handler 监控状态变化
if True:  # 改为 False 可跳过此示例
    """
    status_handler 在状态发生变化时被调用
    可能的状态: starting, running, successful, failed, canceled
    """
    print("=" * 60)
    print("示例5: 状态变化监控")
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
- name: 状态监控演示
  hosts: localhost
  gather_facts: false
  tasks:
    - name: 任务1
      debug:
        msg: "执行任务1"
    
    - name: 任务2
      debug:
        msg: "执行任务2"
"""
        (project_dir / "status_demo.yml").write_text(playbook_content)
        
        status_history = []
        
        def status_handler(status_data, runner_config):
            status = status_data.get("status", "unknown")
            status_history.append(status)
            print(f"  状态变化: {status}")
        
        thread, runner = ansible_runner.run_async(
            private_data_dir=tmpdir,
            playbook="status_demo.yml",
            status_handler=status_handler,
            quiet=True,
        )
        
        thread.join()
        
        print(f"\n状态变化历史: {' -> '.join(status_history)}")
    print()
# endregion
