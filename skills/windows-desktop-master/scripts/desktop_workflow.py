"""
windows-desktop-master lobster workflow step 入口

用法 - 直接运行:
  python desktop_workflow.py --action run --workflow "examples/auto_trade.yaml"

用法 - lobster Workflow YAML:
  - id: desktop-step
    run: python desktop_workflow.py --action run_workflow --workflow "${workflow_file}"

lobster 变量通过环境变量传入
"""
import argparse
import json
import sys
import os
import io
import time
import yaml

# Windows GBK 兼容
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
EXAMPLES_DIR = os.path.join(SKILL_DIR, 'examples')
OUTPUT_DIR = os.path.join(SKILL_DIR, 'output')
OUTPUT_DIR = os.path.expandvars(r'%TEMP%\windows-desktop-master')
os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_workflow(workflow_path: str) -> dict:
    """加载 YAML workflow"""
    path = os.path.expandvars(os.path.expanduser(workflow_path))
    if not os.path.exists(path):
        path = os.path.join(EXAMPLES_DIR, workflow_path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Workflow 文件不存在: {workflow_path}")
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def run_workflow(workflow: dict) -> dict:
    """执行 desktop workflow"""
    results = {
        'steps': [],
        'success': True,
        'errors': []
    }

    steps = workflow.get('steps', [])
    for i, step in enumerate(steps):
        step_id = step.get('id', f'step_{i}')
        action = step.get('action')
        params = step.get('params', {})
        timeout = step.get('timeout', 30)

        print(f"\n[STEP {i+1}] {step_id} | action={action}")

        try:
            result = execute_action(action, params, timeout)
            results['steps'].append({
                'id': step_id,
                'action': action,
                'result': result,
                'success': True
            })
            print(f"  ✅ {result}")
        except Exception as e:
            error = str(e)
            print(f"  ❌ {error}")
            results['steps'].append({
                'id': step_id,
                'action': action,
                'error': error,
                'success': False
            })
            results['success'] = False
            results['errors'].append(error)
            if not step.get('continue_on_error'):
                break

    return results


def execute_action(action: str, params: dict, timeout: int) -> str:
    """执行单个动作"""
    if action == 'ahk_run':
        # 执行 AHK 脚本
        from scripts.ahk_runner import run_script
        run_script(params['script'], wait=(params.get('wait', False)))
        return f"AHK 已执行: {params['script']}"

    elif action == 'ahk_kill':
        from scripts.ahk_runner import kill_ahk_processes
        kill_ahk_processes()
        return "AHK 进程已终止"

    elif action == 'pywinauto_launch':
        from scripts.pywinauto_helper import AppController
        ctl = AppController(backend=params.get('backend', 'win32'))
        ctl.launch(params['path'])
        ctl.wait_window(
            title_re=params.get('title_re'),
            timeout=params.get('timeout', timeout)
        )
        return f"已启动: {params['path']}"

    elif action == 'pywinauto_click':
        from scripts.pywinauto_helper import AppController
        ctl = AppController(backend=params.get('backend', 'win32'))
        ctl.connect(title_re=params['title_re'], timeout=timeout)
        ctl.click(params.get('spec'))
        return f"已点击: {params.get('spec')}"

    elif action == 'pywinauto_type':
        from scripts.pywinauto_helper import AppController
        ctl = AppController(backend=params.get('backend', 'win32'))
        ctl.connect(title_re=params['title_re'], timeout=timeout)
        ctl.type_into(params.get('spec', 'Edit'), params['text'])
        return f"已输入: {params['text']}"

    elif action == 'snapshot':
        # 截图
        from windows_desktop_snapshot import take_snapshot
        path = params.get('path', os.path.join(OUTPUT_DIR, f'snapshot_{int(time.time())}.png'))
        take_snapshot(path)
        return f"截图已保存: {path}"

    elif action == 'wait':
        time.sleep(params.get('seconds', 1))
        return f"等待 {params.get('seconds')} 秒"

    elif action == 'shell':
        # 执行 Shell 命令
        import subprocess
        cmd = params['command']
        result = subprocess.run(cmd, shell=True,
                                capture_output=True, text=True,
                                encoding='gbk', errors='ignore')
        return f"退出码: {result.returncode}"

    elif action == 'log':
        msg = params.get('message', '')
        print(f"  LOG: {msg}")
        return msg

    else:
        raise ValueError(f"未知动作: {action}")


def main():
    parser = argparse.ArgumentParser(description='windows-desktop-master workflow')
    parser.add_argument('--action', default='run',
                        choices=['run', 'run_workflow', 'list_examples'])
    parser.add_argument('--workflow', '-w',
                        help='workflow YAML 文件路径')
    parser.add_argument('--output', '-o',
                        help='结果输出文件路径（JSON）')
    args = parser.parse_args()

    if args.action == 'list_examples':
        print(f"\n[EXAMPLES] 目录: {EXAMPLES_DIR}")
        if os.path.exists(EXAMPLES_DIR):
            for f in os.listdir(EXAMPLES_DIR):
                if f.endswith(('.yaml', '.yml', '.ahk', '.py')):
                    print(f"  - {f}")
        else:
            print("  (空目录)")
        return

    if args.action in ('run', 'run_workflow'):
        if not args.workflow:
            print("[ERROR] 需要指定 --workflow 参数")
            print("\n可用示例:")
            # 列出示例
            for f in os.listdir(EXAMPLES_DIR) if os.path.exists(EXAMPLES_DIR) else []:
                if f.endswith(('.yaml', '.yml')):
                    print(f"  - {f}")
            return

        workflow = load_workflow(args.workflow)
        print(f"[WORKFLOW] {args.workflow}")
        print(f"[STEPS] {len(workflow.get('steps', []))}")

        results = run_workflow(workflow)

        # 输出结果
        if args.output:
            out_path = os.path.expandvars(os.path.expanduser(args.output))
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\n[OUTPUT] {out_path}")
        else:
            print(f"\n[RESULT] success={results['success']}, "
                  f"steps={len(results['steps'])}, "
                  f"errors={len(results['errors'])}")

        sys.exit(0 if results['success'] else 1)


if __name__ == '__main__':
    main()
