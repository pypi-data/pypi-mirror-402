"""
Ansible Runner 事件处理
======================
本文件演示如何处理 ansible-runner 产生的事件。
事件是 Ansible 执行过程中产生的详细信息，包含任务状态、输出等。

常见事件类型:
- playbook_on_start: Playbook 开始
- playbook_on_play_start: Play 开始
- playbook_on_task_start: Task 开始
- runner_on_ok: 任务成功
- runner_on_failed: 任务失败
- runner_on_skipped: 任务跳过
- playbook_on_stats: 执行统计
"""

import ansible_runner
import tempfile
import json
from pathlib import Path

# region 示例1: 遍历所有事件
if True:  # 改为 False 可跳过此示例
    """
    Runner.events 是一个生成器，可以遍历所有事件
    每个事件是一个字典，包含事件类型和相关数据
    """
    print("=" * 60)
    print("示例1: 遍历所有事件")
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
- name: 事件演示
  hosts: localhost
  gather_facts: false
  tasks:
    - name: 任务A
      debug:
        msg: "Hello"
    
    - name: 任务B
      debug:
        msg: "World"
"""
        (project_dir / "events.yml").write_text(playbook_content)
        
        result = ansible_runner.run(
            private_data_dir=tmpdir,
            playbook="events.yml",
            quiet=True,
        )
        
        print("所有事件类型:")
        event_types = set()
        for event in result.events:
            event_type = event.get("event", "unknown")
            event_types.add(event_type)
        
        for et in sorted(event_types):
            print(f"  - {et}")
    print()
# endregion

# region 示例2: 过滤特定类型的事件
if True:  # 改为 False 可跳过此示例
    """
    通常我们只关心特定类型的事件
    比如 runner_on_ok, runner_on_failed 等
    """
    print("=" * 60)
    print("示例2: 过滤特定事件")
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
- name: 过滤事件演示
  hosts: localhost
  gather_facts: false
  tasks:
    - name: 成功的任务
      debug:
        msg: "这个会成功"
    
    - name: 跳过的任务
      debug:
        msg: "这个会跳过"
      when: false
    
    - name: 另一个成功的任务
      command: echo "Hello"
"""
        (project_dir / "filter.yml").write_text(playbook_content)
        
        result = ansible_runner.run(
            private_data_dir=tmpdir,
            playbook="filter.yml",
            quiet=True,
        )
        
        print("成功的任务:")
        for event in result.events:
            if event.get("event") == "runner_on_ok":
                task = event.get("event_data", {}).get("task", "")
                print(f"  ✓ {task}")
        
        # 重新遍历查找跳过的任务
        print("\n跳过的任务:")
        for event in result.events:
            if event.get("event") == "runner_on_skipped":
                task = event.get("event_data", {}).get("task", "")
                print(f"  ⊘ {task}")
    print()
# endregion

# region 示例3: 提取任务输出
if True:  # 改为 False 可跳过此示例
    """
    从事件中提取任务的实际输出
    输出数据在 event_data.res 中
    """
    print("=" * 60)
    print("示例3: 提取任务输出")
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
- name: 输出提取演示
  hosts: localhost
  gather_facts: false
  tasks:
    - name: 执行命令
      command: hostname
      register: hostname_result
    
    - name: 显示主机名
      debug:
        var: hostname_result.stdout
    
    - name: 获取目录列表
      command: ls -la /tmp
      register: ls_result
"""
        (project_dir / "output.yml").write_text(playbook_content)
        
        result = ansible_runner.run(
            private_data_dir=tmpdir,
            playbook="output.yml",
            quiet=True,
        )
        
        print("命令输出:")
        for event in result.events:
            if event.get("event") == "runner_on_ok":
                event_data = event.get("event_data", {})
                task = event_data.get("task", "")
                res = event_data.get("res", {})
                
                # command 模块的输出
                if "stdout" in res:
                    print(f"\n任务: {task}")
                    print(f"输出: {res['stdout'][:100]}...")  # 截取前100字符
    print()
# endregion

# region 示例4: 使用 event_handler 实时处理
if True:  # 改为 False 可跳过此示例
    """
    event_handler 允许在事件产生时立即处理
    而不是等到执行完成后再遍历
    """
    print("=" * 60)
    print("示例4: 实时事件处理")
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
- name: 实时处理演示
  hosts: localhost
  gather_facts: false
  tasks:
    - name: 步骤1
      debug:
        msg: "执行步骤1"
    
    - name: 步骤2
      debug:
        msg: "执行步骤2"
    
    - name: 步骤3
      debug:
        msg: "执行步骤3"
"""
        (project_dir / "realtime.yml").write_text(playbook_content)
        
        task_count = {"ok": 0, "failed": 0, "skipped": 0}
        
        def my_event_handler(event):
            event_type = event.get("event", "")
            
            if event_type == "runner_on_ok":
                task_count["ok"] += 1
                task = event.get("event_data", {}).get("task", "")
                print(f"  [实时] ✓ {task}")
            elif event_type == "runner_on_failed":
                task_count["failed"] += 1
                task = event.get("event_data", {}).get("task", "")
                print(f"  [实时] ✗ {task}")
            elif event_type == "runner_on_skipped":
                task_count["skipped"] += 1
            
            return True  # 保留事件
        
        result = ansible_runner.run(
            private_data_dir=tmpdir,
            playbook="realtime.yml",
            event_handler=my_event_handler,
            quiet=True,
        )
        
        print(f"\n统计: 成功={task_count['ok']}, 失败={task_count['failed']}, 跳过={task_count['skipped']}")
    print()
# endregion

# region 示例5: 获取主机特定事件
if True:  # 改为 False 可跳过此示例
    """
    Runner.host_events() 方法可以获取特定主机的所有事件
    这在多主机场景下很有用
    """
    print("=" * 60)
    print("示例5: 主机特定事件")
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
- name: 主机事件演示
  hosts: localhost
  gather_facts: false
  tasks:
    - name: 任务1
      debug:
        msg: "任务1在 {{ inventory_hostname }}"
    
    - name: 任务2
      debug:
        msg: "任务2在 {{ inventory_hostname }}"
"""
        (project_dir / "host_events.yml").write_text(playbook_content)
        
        result = ansible_runner.run(
            private_data_dir=tmpdir,
            playbook="host_events.yml",
            quiet=True,
        )
        
        # 获取 localhost 的所有事件
        print("localhost 的事件:")
        host_events = result.host_events("localhost")
        for event in host_events:
            event_type = event.get("event", "")
            if event_type in ["runner_on_ok", "runner_on_failed"]:
                task = event.get("event_data", {}).get("task", "")
                print(f"  - {task}: {event_type}")
    print()
# endregion

# region 示例6: 获取执行统计信息
if True:  # 改为 False 可跳过此示例
    """
    Runner.stats 属性包含最终的执行统计
    包括每个主机的 ok, changed, failed 等计数
    """
    print("=" * 60)
    print("示例6: 执行统计信息")
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
- name: 统计演示
  hosts: localhost
  gather_facts: false
  tasks:
    - name: 成功任务1
      debug:
        msg: "OK"
    
    - name: 成功任务2
      debug:
        msg: "OK"
    
    - name: 跳过的任务
      debug:
        msg: "Skip"
      when: false
    
    - name: 有变更的任务
      command: echo "changed"
      changed_when: true
"""
        (project_dir / "stats.yml").write_text(playbook_content)
        
        result = ansible_runner.run(
            private_data_dir=tmpdir,
            playbook="stats.yml",
            quiet=True,
        )
        
        print("执行统计:")
        stats = result.stats
        if stats:
            print(f"  OK: {stats.get('ok', {})}")
            print(f"  Changed: {stats.get('changed', {})}")
            print(f"  Skipped: {stats.get('skipped', {})}")
            print(f"  Failures: {stats.get('failures', {})}")
    print()
# endregion

