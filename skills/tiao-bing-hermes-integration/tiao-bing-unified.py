#!/usr/bin/env python3
"""
调兵系统统一接口 - Hermes Agent 专用
从 WSL 调用 Windows 上的 CoPaw / OpenClaw / OpenCode

用法:
  python3 tiao-bing-unified.py copaw <prompt> [--agent <id>] [--session <id>]
  python3 tiao-bing-unified.py openclaw <prompt> [--agent <id>] [--session <alias>]
  python3 tiao-bing-unified.py opencode <prompt>
  python3 tiao-bing-unified.py status
"""

import subprocess
import json
import re
import sys
import urllib.request
import urllib.parse
import argparse
import time

OPENCLAW_MJS = r"F:\codex\codex\tools\openclaw-gateway-direct.mjs"
OPENCODE_EXE = r"F:\AI\opencode\opencode-cli.exe"

def ps_run(script: str, timeout: int = 120) -> str:
    """Run PowerShell script, return stdout."""
    result = subprocess.run(
        [
            '/mnt/c/WINDOWS/System32/WindowsPowerShell/v1.0/powershell.exe',
            '-NoProfile', '-Command', script
        ],
        capture_output=True, timeout=timeout
    )
    return result.stdout.decode('utf-8', errors='replace')


def copaw_list_agents() -> list:
    """List available CoPaw agents."""
    req = urllib.request.Request(
        "http://127.0.0.1:8088/api/agents",
        headers={"Accept": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
        return data.get('agents', [])


def copaw_ask(prompt: str, agent_id: str = "default", session_id: str = None, timeout: int = 120) -> str:
    """
    Call CoPaw agent via HTTP SSE API.
    Returns the final text response from the assistant.
    """
    if session_id is None:
        session_id = f"hermes-{int(time.time())}"

    payload = json.dumps({
        "session_id": session_id,
        "input": [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
    }).encode()

    req = urllib.request.Request(
        "http://127.0.0.1:8088/api/agent/process",
        data=payload,
        headers={
            "X-Agent-Id": agent_id,
            "Content-Type": "application/json"
        },
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read(20000).decode('utf-8', errors='replace')

    # Parse SSE stream: find the final assistant message with status=completed
    lines = body.split('\n')
    message_texts = []  # list of (type, text) for completed messages

    for line in lines:
        if not line.startswith('data: '):
            continue
        try:
            obj = json.loads(line[6:])
        except:
            continue

        if obj.get('object') == 'message' and obj.get('status') == 'completed':
            msg_type = obj.get('type')
            content = obj.get('content')
            if content and msg_type == 'message':
                # This is the actual assistant response (not reasoning)
                for c in content:
                    if c.get('type') == 'text':
                        message_texts.append(c.get('text', ''))

    if message_texts:
        # Return last non-empty text
        for t in reversed(message_texts):
            if t.strip():
                return t
        return message_texts[-1]

    # Fallback: look for any completed text content
    for line in lines:
        if line.startswith('data: '):
            try:
                obj = json.loads(line[6:])
                if obj.get('object') == 'content' and obj.get('type') == 'text' and obj.get('delta') is None:
                    return obj.get('text', '')
            except:
                pass

    return body[:500]


def openclaw_ask(prompt: str, agent_id: str = "main", session_alias: str = None, timeout: int = 180) -> str:
    """
    Call OpenClaw agent via gateway-direct.mjs.
    Returns the output text from the assistant.
    """
    if session_alias is None:
        session_alias = f"hermes-{int(time.time())}"

    # Escape special PowerShell characters
    escaped_prompt = prompt.replace('"', '`"').replace('$', '`$').replace('`', '``')

    script = f'''
$result = & "C:\\Program Files\\nodejs\\node.exe" "{OPENCLAW_MJS}" ask --agent {agent_id} --session "{session_alias}" --timeout-sec {timeout} "{escaped_prompt}" 2>&1
$result
'''
    output = ps_run(script, timeout=timeout + 30)

    # Parse JSON output, extract "output" field
    # The output is a single-line JSON
    match = re.search(r'"output":\s*"([^"]*)"', output)
    if match:
        return match.group(1)

    # Try to parse full JSON
    try:
        # Strip non-JSON prefix lines
        json_str = output.strip()
        data = json.loads(json_str)
        if isinstance(data, dict) and 'output' in data:
            return data['output']
    except json.JSONDecodeError:
        pass

    return output[:500]


def opencode_run(prompt: str, timeout: int = 180) -> str:
    """
    Call OpenCode CLI run command.
    Returns the stdout text (model output).
    """
    escaped = prompt.replace('"', '\\"')
    script = f'''
& "{OPENCODE_EXE}" run "{escaped}" 2>&1
'''
    output = ps_run(script, timeout=timeout + 30)

    # First non-empty, non-error line is the answer
    for line in output.split('\n'):
        line = line.strip()
        if line:
            # Skip PowerShell error annotations
            if line.startswith('+') or 'CategoryInfo' in line or 'FullyQualifiedError' in line:
                continue
            return line
    return output.split('\n')[0].strip() if output else None


def status() -> dict:
    """Check status of all three systems."""
    result = {
        "copaw": {"status": "unknown"},
        "openclaw": {"status": "unknown"},
        "opencode": {"status": "unknown"}
    }

    # CoPaw
    try:
        req = urllib.request.Request("http://127.0.0.1:8088/api/agents", headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            result["copaw"] = {
                "status": "online",
                "agents": [a['id'] for a in data.get('agents', []) if a.get('enabled')]
            }
    except Exception as e:
        result["copaw"] = {"status": "offline", "error": str(e)}

    # OpenClaw
    try:
        script = f'''
$result = & "C:\\Program Files\\nodejs\\node.exe" "{OPENCLAW_MJS}" health 2>&1
$result
'''
        output = ps_run(script, timeout=15)
        if '"ok": true' in output or '"ok":true' in output:
            result["openclaw"] = {"status": "online"}
        else:
            result["openclaw"] = {"status": "degraded", "raw": output[:200]}
    except Exception as e:
        result["openclaw"] = {"status": "offline", "error": str(e)}

    # OpenCode
    try:
        script = f'''
$proc = Test-NetConnection -ComputerName 127.0.0.1 -Port 4096 -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
if ($proc.TcpTestSucceeded) {{ "online" }} else {{ "offline" }}
'''
        output = ps_run(script, timeout=5)
        if 'online' in output.lower():
            result["opencode"] = {"status": "online", "url": "http://127.0.0.1:4096"}
        else:
            result["opencode"] = {"status": "offline"}
    except Exception as e:
        result["opencode"] = {"status": "offline", "error": str(e)}

    return result


def main():
    parser = argparse.ArgumentParser(description='调兵系统统一接口')
    parser.add_argument('system', choices=['copaw', 'openclaw', 'opencode', 'status', 'list-agents'],
                        help='目标系统')
    parser.add_argument('prompt', nargs='?', help='要发送的提示词')
    parser.add_argument('--agent', default=None, help='Agent ID (copaw/openclaw)')
    parser.add_argument('--session', default=None, help='Session ID/alias')
    parser.add_argument('--timeout', type=int, default=120, help='超时秒数')

    args = parser.parse_args()

    if args.system == 'status':
        result = status()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    if args.system == 'list-agents':
        if args.agent == 'copaw':
            agents = copaw_list_agents()
            print(json.dumps(agents, indent=2, ensure_ascii=False))
        return

    if not args.prompt:
        print("Error: prompt is required", file=sys.stderr)
        sys.exit(1)

    if args.system == 'copaw':
        result = copaw_ask(args.prompt, agent_id=args.agent or "default",
                           session_id=args.session, timeout=args.timeout)
        print(result)

    elif args.system == 'openclaw':
        result = openclaw_ask(args.prompt, agent_id=args.agent or "main",
                              session_alias=args.session, timeout=args.timeout)
        print(result)

    elif args.system == 'opencode':
        result = opencode_run(args.prompt, timeout=args.timeout)
        print(result)


if __name__ == '__main__':
    main()
