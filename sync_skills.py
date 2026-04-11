#!/usr/bin/env python3
"""Batch upload skills to GitHub chunbi-workspace"""
import base64, json, os, subprocess, time, urllib.request, urllib.error
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

REPO = "SnowLove0303/chunbi-workspace"
SKILLS_DIR = r"F:\openclaw1\.openclaw\workspace\skills"

SKIP_EXTS = {'.pyc', '.pyo', '.pyd', '.dll', '.so', '.dylib', '.exe', '.zip', '.tar', '.gz'}
SKIP_NAMES = {'__pycache__', '.git', 'node_modules', '.venv', 'venv', 'temp', 'tmp'}

TOKEN = None

def get_token():
    global TOKEN
    if TOKEN is None:
        r = subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True)
        TOKEN = r.stdout.strip()
    return TOKEN

def get_sha(path):
    """用 gh api 获取文件 sha，避免大文件响应截断"""
    r = subprocess.run(['gh', 'api', f'repos/{REPO}/contents/{path}', '--jq', '.sha'],
                      capture_output=True, text=True)
    if r.returncode == 0:
        return r.stdout.strip()
    return None

def upload_file(content_bytes, path, msg):
    token = get_token()
    b64 = base64.b64encode(content_bytes).decode()
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"

    payload = {"message": msg, "content": b64}
    sha = get_sha(path)
    if sha:
        payload["sha"] = sha

    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data,
        headers={"Authorization": "Bearer " + token,
                 "Accept": "application/vnd.github+json",
                 "Content-Type": "application/json"},
        method="PUT")
    try:
        with urllib.request.urlopen(req) as r:
            return True
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read())
            err_msg = body.get('message', str(body))[:100]
        except:
            err_msg = str(e)
        return False, f"HTTP {e.code}: {err_msg}"
    except Exception as e:
        return False, str(e)

def walk_skill(dir_path):
    files = []
    for root, dirs, filenames in os.walk(dir_path):
        dirs[:] = [d for d in dirs if d not in SKIP_NAMES]
        for fname in filenames:
            if any(fname.endswith(ext) for ext in SKIP_EXTS):
                continue
            fpath = os.path.join(root, fname)
            rel = os.path.relpath(fpath, dir_path)
            size = os.path.getsize(fpath)
            if size > 5 * 1024 * 1024:  # 跳过 > 5MB 的文件
                print(f"  [SKIP large {size//1024}KB] {rel}")
                continue
            files.append((fpath, rel))
    return files

def main():
    if not get_token():
        print("ERROR: Not authenticated with gh"); return

    skills = sorted([d for d in os.listdir(SKILLS_DIR)
                     if os.path.isdir(os.path.join(SKILLS_DIR, d))])
    print(f"Found {len(skills)} skills, uploading...\n")
    flush = sys.stdout.flush

    results = {}
    for skill in skills:
        skill_path = os.path.join(SKILLS_DIR, skill)
        files = walk_skill(skill_path)
        if not files:
            print(f"  [SKIP] {skill} (no files)")
            continue
        print(f"[{skill}] {len(files)} files")
        flush()
        ok, fail = 0, 0
        for fpath, rel in files:
            git_path = f"skills/{skill}/{rel.replace(os.sep, '/')}"
            with open(fpath, 'rb') as f:
                content = f.read()
            ok_upload = upload_file(content, git_path, f"sync: {skill}/{rel}")
            if ok_upload is True:
                print(f"  [OK] {rel}")
                ok += 1
            else:
                err = ok_upload[1] if isinstance(ok_upload, tuple) else str(ok_upload)
                print(f"  [FAIL] {rel}: {err}")
                fail += 1
            flush()
            time.sleep(0.4)
        results[skill] = (ok, fail)
        print(f"  -> {ok} ok, {fail} failed\n")
        flush()

    print("=== SUMMARY ===")
    for s, (o, f) in results.items():
        tag = "OK" if f == 0 else "PARTIAL"
        print(f"  [{tag}] {s}: {o} ok, {f} fail")

if __name__ == "__main__":
    main()
