#!/usr/bin/env python3
"""上传项目文件夹到 GitHub chunbi-workspace/projects/<项目名>"""
import base64, json, os, subprocess, sys, urllib.request, urllib.error
from urllib.parse import quote

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

REPO = "SnowLove0303/chunbi-workspace"
BRANCH = "main"
GITHUB_BASE = f"https://api.github.com/repos/{REPO}"
PROJECTS_DIR = "projects/browser-control"


def get_token():
    r = subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True)
    return r.stdout.strip()


def get_sha(path):
    encoded_path = quote(path, safe='/')
    url = f"{GITHUB_BASE}/contents/{encoded_path}"
    token = get_token()
    req = urllib.request.Request(url,
        headers={"Authorization": f"Bearer {token}",
                 "Accept": "application/vnd.github+json"})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            return data.get('sha')
    except (urllib.error.HTTPError, Exception):
        return None


def upload_file(content_bytes, path, msg="auto upload"):
    token = get_token()
    b64 = base64.b64encode(content_bytes).decode()
    encoded_path = quote(path, safe='/')
    url = f"{GITHUB_BASE}/contents/{encoded_path}"
    payload = {"message": msg, "content": b64, "branch": BRANCH}
    sha = get_sha(path)
    if sha:
        payload["sha"] = sha

    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data,
        headers={"Authorization": f"Bearer {token}",
                 "Accept": "application/vnd.github+json",
                 "Content-Type": "application/json"},
        method="PUT")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read()).get('content', {}).get('path', path)
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"    ❌ HTTP {e.code}: {body[:200]}")
        return None


def upload_dir(local_dir, remote_base):
    """递归上传目录"""
    uploaded = 0
    skipped = 0
    errors = []

    SKIP_EXTS = {'.pyc', '.pyo', '.pyd', '.dll', '.so', '.dylib', '.exe',
                 '.zip', '.tar', '.gz', '.whl', '.iso', '.img'}
    SKIP_NAMES = {'__pycache__', '.git', 'node_modules', '.venv', 'venv',
                   'temp', 'tmp', '.DS_Store', 'Thumbs.db'}

    for root, dirs, files in os.walk(local_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_NAMES]

        for fname in files:
            if fname in SKIP_NAMES:
                continue
            ext = os.path.splitext(fname)[1].lower()
            if ext in SKIP_EXTS:
                continue

            local_path = os.path.join(root, fname)
            rel_path = os.path.relpath(local_path, local_dir)
            remote_path = f"{remote_base}/{rel_path}".replace("\\", "/")

            try:
                size = os.path.getsize(local_path)
                content = open(local_path, 'rb').read()
            except Exception as e:
                print(f"    ❌ 读取失败 {rel_path}: {e}")
                errors.append((rel_path, str(e)))
                continue

            if size > 5 * 1024 * 1024:
                print(f"    ⏭  跳过（大文件 {size//1024}KB）: {rel_path}")
                skipped += 1
                continue

            print(f"  {'上传' if not get_sha(remote_path) else '更新':4s} {rel_path} ({size//1024}KB)", end=" ... ")
            result = upload_file(content, remote_path)
            if result:
                print(" ✅")
                uploaded += 1
            else:
                print(" ❌")
                errors.append((rel_path, "upload failed"))

    return uploaded, skipped, errors


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="上传项目到 GitHub")
    parser.add_argument("local_dir", help="本地目录")
    parser.add_argument("--repo", default=REPO, help="目标仓库")
    parser.add_argument("--branch", default=BRANCH, help="分支")
    parser.add_argument("--remote-dir", default=PROJECTS_DIR, help="远程目录")
    args = parser.parse_args()

    local = args.local_dir
    if not os.path.isdir(local):
        print(f"❌ 目录不存在: {local}")
        sys.exit(1)

    file_count = sum(1 for _, _, files in os.walk(local)
                      for f in files if not f.startswith('.'))
    print(f"\n📁 {local}")
    print(f"   → {args.repo}/{args.remote_dir}")
    print(f"   文件数: {file_count}\n")

    uploaded, skipped, errors = upload_dir(local, args.remote_dir)

    print(f"\n{'='*50}")
    print(f"✅ 上传完成: {uploaded} 个文件")
    if skipped:
        print(f"⏭  跳过: {skipped} 个（大文件/二进制）")
    if errors:
        print(f"❌ 失败: {len(errors)} 个")
        for path, err in errors[:5]:
            print(f"   {path}: {err[:80]}")
    print(f"{'='*50}\n")
    print(f"🔗 https://github.com/{args.repo}/tree/{args.branch}/{args.remote_dir}")
