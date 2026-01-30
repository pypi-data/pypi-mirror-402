"""
Ansible Runner 目录结构与配置
============================
本文件演示 ansible-runner 的目录结构规范和配置方式。
理解目录结构对于正确使用 ansible-runner 非常重要。

标准目录结构:
private_data_dir/
├── inventory/          # inventory 文件
├── project/            # playbook 和 roles
├── env/                # 环境配置
│   ├── envvars         # 环境变量
│   ├── passwords       # 密码配置
│   ├── cmdline         # 命令行参数
│   ├── settings        # runner 设置
│   └── ssh_key         # SSH 私钥
└── artifacts/          # 执行结果 (自动生成)
"""

import ansible_runner
import tempfile
import json
from pathlib import Path

# region 示例1: 完整的目录结构
if True:  # 改为 False 可跳过此示例
    """
    创建一个完整的 ansible-runner 目录结构
    展示各个目录和文件的作用
    """
    print("=" * 60)
    print("示例1: 完整目录结构")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        
        # 1. 创建 inventory 目录
        inventory_dir = base / "inventory"
        inventory_dir.mkdir()
        (inventory_dir / "hosts").write_text(
            "[local]\nlocalhost ansible_connection=local\n"
        )
        
        # 2. 创建 project 目录 (存放 playbook)
        project_dir = base / "project"
        project_dir.mkdir()
        (project_dir / "site.yml").write_text("""
---
- name: 主 Playbook
  hosts: local
  gather_facts: false
  tasks:
    - name: 显示环境变量
      debug:
        msg: "MY_VAR = {{ lookup('env', 'MY_VAR') }}"
""")
        
        # 3. 创建 env 目录
        env_dir = base / "env"
        env_dir.mkdir()
        
        # 3.1 envvars - 环境变量
        (env_dir / "envvars").write_text(json.dumps({
            "MY_VAR": "Hello from envvars!",
            "ANSIBLE_STDOUT_CALLBACK": "yaml",
        }))
        
        # 3.2 settings - runner 设置
        (env_dir / "settings").write_text(json.dumps({
            "job_timeout": 300,  # 超时时间(秒)
        }))
        
        print("目录结构:")
        for item in sorted(base.rglob("*")):
            rel_path = item.relative_to(base)
            indent = "  " * (len(rel_path.parts) - 1)
            if item.is_dir():
                print(f"{indent}📁 {item.name}/")
            else:
                print(f"{indent}📄 {item.name}")
        
        # 执行
        result = ansible_runner.run(
            private_data_dir=tmpdir,
            playbook="site.yml",
            quiet=True,
        )
        
        print(f"\n执行状态: {result.status}")
        
        # 检查 artifacts 目录
        artifacts_dir = base / "artifacts"
        if artifacts_dir.exists():
            print("\n生成的 artifacts:")
            for item in sorted(artifacts_dir.rglob("*"))[:10]:
                if item.is_file():
                    print(f"  📄 {item.relative_to(artifacts_dir)}")
    print()
# endregion

# region 示例2: 使用 envvars 设置环境变量
if True:  # 改为 False 可跳过此示例
    """
    env/envvars 文件用于设置执行时的环境变量
    支持 JSON 或 YAML 格式
    """
    print("=" * 60)
    print("示例2: 环境变量配置")
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
        (project_dir / "env_test.yml").write_text("""
---
- name: 环境变量测试
  hosts: localhost
  gather_facts: false
  tasks:
    - name: 显示自定义环境变量
      debug:
        msg: |
          APP_NAME: {{ lookup('env', 'APP_NAME') }}
          APP_ENV: {{ lookup('env', 'APP_ENV') }}
          DEBUG: {{ lookup('env', 'DEBUG') }}
""")
        
        env_dir = base / "env"
        env_dir.mkdir()
        
        # 设置环境变量 (JSON 格式)
        envvars = {
            "APP_NAME": "MyApplication",
            "APP_ENV": "development",
            "DEBUG": "true",
        }
        (env_dir / "envvars").write_text(json.dumps(envvars))
        
        result = ansible_runner.run(
            private_data_dir=tmpdir,
            playbook="env_test.yml",
            quiet=True,
        )
        
        # 提取输出
        for event in result.events:
            if event.get("event") == "runner_on_ok":
                res = event.get("event_data", {}).get("res", {})
                msg = res.get("msg", "")
                if msg and "APP_NAME" in msg:
                    print("环境变量值:")
                    print(msg)
    print()
# endregion

# region 示例3: 使用 cmdline 文件
if True:  # 改为 False 可跳过此示例
    """
    env/cmdline 文件包含传递给 ansible-playbook 的额外命令行参数
    """
    print("=" * 60)
    print("示例3: cmdline 配置")
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
        (project_dir / "cmdline_test.yml").write_text("""
---
- name: Cmdline 测试
  hosts: localhost
  gather_facts: false
  tasks:
    - name: 显示变量
      debug:
        msg: "version={{ version }}, env={{ env }}"
""")
        
        env_dir = base / "env"
        env_dir.mkdir()
        
        # cmdline 文件内容是字符串
        cmdline = "-e version=1.0.0 -e env=staging"
        (env_dir / "cmdline").write_text(cmdline)
        
        result = ansible_runner.run(
            private_data_dir=tmpdir,
            playbook="cmdline_test.yml",
            quiet=True,
        )
        
        for event in result.events:
            if event.get("event") == "runner_on_ok":
                res = event.get("event_data", {}).get("res", {})
                msg = res.get("msg", "")
                if msg and "version" in msg:
                    print(f"输出: {msg}")
        
        print(f"执行状态: {result.status}")
    print()
# endregion

# region 示例4: 使用 settings 配置 Runner
if True:  # 改为 False 可跳过此示例
    """
    env/settings 文件用于配置 Runner 本身的行为
    常用设置:
    - job_timeout: 任务超时时间
    - idle_timeout: 空闲超时时间
    - fact_cache_type: fact 缓存类型
    """
    print("=" * 60)
    print("示例4: Runner 设置")
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
        (project_dir / "settings_test.yml").write_text("""
---
- name: Settings 测试
  hosts: localhost
  gather_facts: false
  tasks:
    - name: 快速任务
      debug:
        msg: "任务完成"
""")
        
        env_dir = base / "env"
        env_dir.mkdir()
        
        # Runner 设置
        settings = {
            "job_timeout": 60,      # 60秒超时
            "idle_timeout": 30,     # 30秒空闲超时
        }
        (env_dir / "settings").write_text(json.dumps(settings))
        
        result = ansible_runner.run(
            private_data_dir=tmpdir,
            playbook="settings_test.yml",
            quiet=True,
        )
        
        print(f"执行状态: {result.status}")
        print("(设置了 60 秒任务超时和 30 秒空闲超时)")
    print()
# endregion

# region 示例5: 直接通过参数配置 (不使用文件)
if True:  # 改为 False 可跳过此示例
    """
    除了使用目录结构，也可以直接通过 run() 参数配置
    这在简单场景下更方便
    """
    print("=" * 60)
    print("示例5: 参数方式配置")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        
        # 只需要最基本的目录
        inventory_dir = base / "inventory"
        inventory_dir.mkdir()
        (inventory_dir / "hosts").write_text(
            "localhost ansible_connection=local\n"
        )
        
        project_dir = base / "project"
        project_dir.mkdir()
        (project_dir / "param_test.yml").write_text("""
---
- name: 参数配置测试
  hosts: localhost
  gather_facts: false
  tasks:
    - name: 显示配置
      debug:
        msg: "app={{ app_name }}, MY_ENV={{ lookup('env', 'MY_ENV') }}"
""")
        
        # 通过参数直接配置
        result = ansible_runner.run(
            private_data_dir=tmpdir,
            playbook="param_test.yml",
            extravars={
                "app_name": "DirectConfig",
            },
            envvars={
                "MY_ENV": "production",
            },
            quiet=True,
        )
        
        for event in result.events:
            if event.get("event") == "runner_on_ok":
                res = event.get("event_data", {}).get("res", {})
                msg = res.get("msg", "")
                if msg and "app=" in msg:
                    print(f"输出: {msg}")
        
        print(f"执行状态: {result.status}")
    print()
# endregion

# region 示例6: 查看 artifacts 输出
if True:  # 改为 False 可跳过此示例
    """
    执行完成后，artifacts 目录包含详细的执行结果
    包括 stdout, rc, status, job_events 等
    """
    print("=" * 60)
    print("示例6: Artifacts 输出")
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
        (project_dir / "artifacts_test.yml").write_text("""
---
- name: Artifacts 测试
  hosts: localhost
  gather_facts: false
  tasks:
    - name: 任务1
      debug:
        msg: "Hello"
    - name: 任务2
      command: echo "World"
""")
        
        # 指定 ident 以便找到 artifacts
        result = ansible_runner.run(
            private_data_dir=tmpdir,
            playbook="artifacts_test.yml",
            ident="my_job",  # 指定任务标识
            quiet=True,
        )
        
        # 查看 artifacts
        artifacts_dir = base / "artifacts" / "my_job"
        if artifacts_dir.exists():
            print("Artifacts 内容:")
            
            # 读取 status
            status_file = artifacts_dir / "status"
            if status_file.exists():
                print(f"  status: {status_file.read_text().strip()}")
            
            # 读取 rc
            rc_file = artifacts_dir / "rc"
            if rc_file.exists():
                print(f"  rc: {rc_file.read_text().strip()}")
            
            # 统计 job_events
            events_dir = artifacts_dir / "job_events"
            if events_dir.exists():
                event_count = len(list(events_dir.glob("*.json")))
                print(f"  job_events: {event_count} 个事件文件")
    print()
# endregion
