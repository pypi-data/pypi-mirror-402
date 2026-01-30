"""
Ansible Runner 实战案例
======================
本文件演示 ansible-runner 的实际应用场景。
包括自动化部署、配置管理、批量操作等常见用例。
"""

import ansible_runner
import tempfile
import time
from pathlib import Path
from typing import Callable

# region 示例1: 封装可复用的执行器类
if True:  # 改为 False 可跳过此示例
    """
    封装一个可复用的 Ansible 执行器类
    简化日常使用
    """
    print("=" * 60)
    print("示例1: 可复用的执行器类")
    print("=" * 60)
    
    class AnsibleExecutor:
        """简化的 Ansible 执行器"""
        
        def __init__(self, inventory: str = "localhost ansible_connection=local"):
            self.tmpdir = tempfile.mkdtemp()
            self.base = Path(self.tmpdir)
            
            # 初始化目录结构
            (self.base / "inventory").mkdir()
            (self.base / "inventory" / "hosts").write_text(inventory)
            (self.base / "project").mkdir()
        
        def run_playbook(self, playbook_content: str, **kwargs) -> ansible_runner.Runner:
            """执行 playbook 内容"""
            playbook_file = self.base / "project" / "playbook.yml"
            playbook_file.write_text(playbook_content)
            
            return ansible_runner.run(
                private_data_dir=self.tmpdir,
                playbook="playbook.yml",
                quiet=True,
                **kwargs
            )
        
        def run_module(self, module: str, args: str = "", **kwargs) -> ansible_runner.Runner:
            """执行单个模块"""
            return ansible_runner.run(
                private_data_dir=self.tmpdir,
                host_pattern="localhost",
                module=module,
                module_args=args,
                quiet=True,
                **kwargs
            )
        
        def cleanup(self):
            """清理临时目录"""
            import shutil
            shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    # 使用示例
    executor = AnsibleExecutor()
    
    try:
        # 执行模块
        result = executor.run_module("debug", "msg='Hello from executor!'")
        print(f"模块执行状态: {result.status}")
        
        # 执行 playbook
        playbook = """
---
- hosts: localhost
  gather_facts: false
  tasks:
    - debug:
        msg: "Playbook executed!"
"""
        result = executor.run_playbook(playbook)
        print(f"Playbook 执行状态: {result.status}")
    finally:
        executor.cleanup()
    print()
# endregion

# region 示例2: 带进度回调的执行
if True:  # 改为 False 可跳过此示例
    """
    实现带进度显示的执行
    适用于 CLI 工具或 Web 界面
    """
    print("=" * 60)
    print("示例2: 带进度回调的执行")
    print("=" * 60)
    
    def run_with_progress(
        private_data_dir: str,
        playbook: str,
        on_task_start: Callable[[str], None] = None,
        on_task_ok: Callable[[str], None] = None,
        on_task_failed: Callable[[str], None] = None,
    ) -> ansible_runner.Runner:
        """带进度回调的执行函数"""
        
        def event_handler(event):
            event_type = event.get("event", "")
            event_data = event.get("event_data", {})
            task_name = event_data.get("task", "")
            
            if event_type == "playbook_on_task_start" and on_task_start:
                on_task_start(task_name)
            elif event_type == "runner_on_ok" and on_task_ok:
                on_task_ok(task_name)
            elif event_type == "runner_on_failed" and on_task_failed:
                on_task_failed(task_name)
            
            return True
        
        return ansible_runner.run(
            private_data_dir=private_data_dir,
            playbook=playbook,
            event_handler=event_handler,
            quiet=True,
        )
    
    # 使用示例
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        
        (base / "inventory").mkdir()
        (base / "inventory" / "hosts").write_text(
            "localhost ansible_connection=local\n"
        )
        
        (base / "project").mkdir()
        (base / "project" / "deploy.yml").write_text("""
---
- hosts: localhost
  gather_facts: false
  tasks:
    - name: 检查环境
      debug:
        msg: "环境检查完成"
    
    - name: 下载代码
      debug:
        msg: "代码下载完成"
    
    - name: 安装依赖
      debug:
        msg: "依赖安装完成"
    
    - name: 启动服务
      debug:
        msg: "服务启动完成"
""")
        
        # 定义回调
        def on_start(task):
            print(f"  ⏳ 开始: {task}")
        
        def on_ok(task):
            print(f"  ✓ 完成: {task}")
        
        def on_failed(task):
            print(f"  ✗ 失败: {task}")
        
        print("执行部署流程:")
        result = run_with_progress(
            tmpdir, "deploy.yml",
            on_task_start=on_start,
            on_task_ok=on_ok,
            on_task_failed=on_failed,
        )
        
        print(f"\n最终状态: {result.status}")
    print()
# endregion

# region 示例3: 收集执行结果报告
if True:  # 改为 False 可跳过此示例
    """
    收集详细的执行结果，生成报告
    """
    print("=" * 60)
    print("示例3: 执行结果报告")
    print("=" * 60)
    
    def generate_report(runner: ansible_runner.Runner) -> dict:
        """生成执行报告"""
        report = {
            "status": runner.status,
            "rc": runner.rc,
            "tasks": [],
            "summary": {
                "ok": 0,
                "failed": 0,
                "skipped": 0,
                "changed": 0,
            }
        }
        
        for event in runner.events:
            event_type = event.get("event", "")
            event_data = event.get("event_data", {})
            
            if event_type == "runner_on_ok":
                report["summary"]["ok"] += 1
                res = event_data.get("res", {})
                report["tasks"].append({
                    "name": event_data.get("task", ""),
                    "status": "ok",
                    "changed": res.get("changed", False),
                })
                if res.get("changed"):
                    report["summary"]["changed"] += 1
            
            elif event_type == "runner_on_failed":
                report["summary"]["failed"] += 1
                report["tasks"].append({
                    "name": event_data.get("task", ""),
                    "status": "failed",
                    "msg": event_data.get("res", {}).get("msg", ""),
                })
            
            elif event_type == "runner_on_skipped":
                report["summary"]["skipped"] += 1
                report["tasks"].append({
                    "name": event_data.get("task", ""),
                    "status": "skipped",
                })
        
        return report
    
    # 使用示例
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        
        (base / "inventory").mkdir()
        (base / "inventory" / "hosts").write_text(
            "localhost ansible_connection=local\n"
        )
        
        (base / "project").mkdir()
        (base / "project" / "test.yml").write_text("""
---
- hosts: localhost
  gather_facts: false
  tasks:
    - name: 任务1
      debug:
        msg: "OK"
    
    - name: 任务2 (有变更)
      command: echo "changed"
      changed_when: true
    
    - name: 任务3 (跳过)
      debug:
        msg: "Skip"
      when: false
""")
        
        result = ansible_runner.run(
            private_data_dir=tmpdir,
            playbook="test.yml",
            quiet=True,
        )
        
        report = generate_report(result)
        
        print("执行报告:")
        print(f"  状态: {report['status']}")
        print(f"  返回码: {report['rc']}")
        print("\n摘要:")
        print(f"  成功: {report['summary']['ok']}")
        print(f"  变更: {report['summary']['changed']}")
        print(f"  跳过: {report['summary']['skipped']}")
        print(f"  失败: {report['summary']['failed']}")
        print("\n任务详情:")
        for task in report["tasks"]:
            status_icon = {"ok": "✓", "failed": "✗", "skipped": "⊘"}.get(task["status"], "?")
            print(f"  {status_icon} {task['name']}")
    print()
# endregion

# region 示例4: 批量主机操作
if True:  # 改为 False 可跳过此示例
    """
    对多个主机执行操作并收集结果
    (这里用 localhost 模拟多主机)
    """
    print("=" * 60)
    print("示例4: 批量主机操作")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        
        (base / "inventory").mkdir()
        # 模拟多主机 (实际都是 localhost)
        (base / "inventory" / "hosts").write_text("""
[webservers]
web1 ansible_connection=local ansible_host=localhost
web2 ansible_connection=local ansible_host=localhost

[dbservers]
db1 ansible_connection=local ansible_host=localhost
""")
        
        (base / "project").mkdir()
        (base / "project" / "batch.yml").write_text("""
---
- hosts: all
  gather_facts: false
  tasks:
    - name: 检查主机
      debug:
        msg: "主机 {{ inventory_hostname }} 检查完成"
""")
        
        result = ansible_runner.run(
            private_data_dir=tmpdir,
            playbook="batch.yml",
            quiet=True,
        )
        
        # 按主机收集结果
        host_results = {}
        for event in result.events:
            if event.get("event") == "runner_on_ok":
                host = event.get("event_data", {}).get("host", "")
                if host:
                    host_results[host] = "成功"
        
        print("主机执行结果:")
        for host, status in host_results.items():
            print(f"  {host}: {status}")
        
        print(f"\n总体状态: {result.status}")
    print()
# endregion

# region 示例5: 错误处理与重试
if True:  # 改为 False 可跳过此示例
    """
    实现带重试机制的执行
    """
    print("=" * 60)
    print("示例5: 错误处理与重试")
    print("=" * 60)
    
    def run_with_retry(
        private_data_dir: str,
        playbook: str,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> ansible_runner.Runner:
        """带重试的执行"""
        
        for attempt in range(1, max_retries + 1):
            print(f"  尝试 {attempt}/{max_retries}...")
            
            result = ansible_runner.run(
                private_data_dir=private_data_dir,
                playbook=playbook,
                quiet=True,
            )
            
            if result.status == "successful":
                print(f"  ✓ 第 {attempt} 次尝试成功")
                return result
            
            if attempt < max_retries:
                print(f"  ✗ 失败，{retry_delay}秒后重试...")
                time.sleep(retry_delay)
        
        print(f"  ✗ 所有 {max_retries} 次尝试均失败")
        return result
    
    # 使用示例
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        
        (base / "inventory").mkdir()
        (base / "inventory" / "hosts").write_text(
            "localhost ansible_connection=local\n"
        )
        
        (base / "project").mkdir()
        # 这个 playbook 会成功
        (base / "project" / "retry_test.yml").write_text("""
---
- hosts: localhost
  gather_facts: false
  tasks:
    - name: 模拟操作
      debug:
        msg: "操作成功"
""")
        
        print("执行带重试的任务:")
        result = run_with_retry(tmpdir, "retry_test.yml", max_retries=3)
        print(f"最终状态: {result.status}")
    print()
# endregion

# region 示例6: 动态生成 Playbook
if True:  # 改为 False 可跳过此示例
    """
    根据参数动态生成 Playbook 并执行
    适用于需要灵活配置的场景
    """
    print("=" * 60)
    print("示例6: 动态生成 Playbook")
    print("=" * 60)
    
    import yaml
    
    def create_deployment_playbook(
        app_name: str,
        version: str,
        services: list[str],
    ) -> str:
        """动态生成部署 playbook"""
        
        tasks = [
            {
                "name": f"部署 {app_name} v{version}",
                "debug": {"msg": f"开始部署 {app_name} 版本 {version}"}
            }
        ]
        
        for service in services:
            tasks.append({
                "name": f"启动服务: {service}",
                "debug": {"msg": f"服务 {service} 已启动"}
            })
        
        tasks.append({
            "name": "部署完成",
            "debug": {"msg": "所有服务部署完成!"}
        })
        
        playbook = [{
            "name": f"{app_name} 部署",
            "hosts": "localhost",
            "gather_facts": False,
            "tasks": tasks,
        }]
        
        return yaml.dump(playbook, allow_unicode=True, default_flow_style=False)
    
    # 使用示例
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        
        (base / "inventory").mkdir()
        (base / "inventory" / "hosts").write_text(
            "localhost ansible_connection=local\n"
        )
        
        (base / "project").mkdir()
        
        # 动态生成 playbook
        playbook_content = create_deployment_playbook(
            app_name="MyApp",
            version="2.0.0",
            services=["web", "api", "worker"],
        )
        
        print("生成的 Playbook:")
        print(playbook_content[:300] + "...")
        
        (base / "project" / "deploy.yml").write_text(playbook_content)
        
        result = ansible_runner.run(
            private_data_dir=tmpdir,
            playbook="deploy.yml",
            quiet=True,
        )
        
        print(f"执行状态: {result.status}")
    print()
# endregion
