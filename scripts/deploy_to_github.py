#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键全自动部署 InvestIntel 到 GitHub & 开启 GitHub Pages
"""

import os
import sys
import json
import urllib.request
import urllib.error
import subprocess

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def call_github_api(url, token, data=None, method="GET"):
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "InvestIntel-Deployer")
    
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        req.add_header("Content-Type", "application/json")
        
    try:
        with urllib.request.urlopen(req, data=body) as resp:
            return json.loads(resp.read().decode("utf-8")), resp.status
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode("utf-8")
        return {"error": error_msg}, e.code

def run_git_cmd(cmd_list):
    res = subprocess.run(cmd_list, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[Git Warning/Error] {' '.join(cmd_list)}:\n{res.stderr}")
    return res.returncode == 0

def deploy(token: str, repo_name: str = "invest-intel"):
    token = token.strip()
    if not token:
        print("[Error] GitHub Token 不能为空！")
        return

    print("==================================================")
    print("🚀 开始执行 InvestIntel 全自动 GitHub 部署流程")
    print("==================================================")

    # 1. 获取用户信息
    print("\n[1/4] 验证 GitHub Token 并获取用户信息...")
    user_data, status = call_github_api("https://api.github.com/user", token)
    if status != 200 or "login" not in user_data:
        print(f"[Error] Token 无效或过期 (HTTP {status}): {user_data}")
        return
    
    username = user_data["login"]
    print(f"[OK] 验证成功！当前 GitHub 用户名: {username}")

    # 2. 创建或确认 GitHub 仓库
    print(f"\n[2/4] 正在检查或自动创建 GitHub 仓库: {username}/{repo_name}...")
    repo_url = f"https://api.github.com/repos/{username}/{repo_name}"
    _, check_status = call_github_api(repo_url, token)

    if check_status == 404:
        print(f"仓库不存在，正在全自动创建公开仓库 {repo_name}...")
        create_payload = {
            "name": repo_name,
            "description": "InvestIntel · 统一多券商投资驾驶舱与每日投研助手",
            "private": False,
            "has_issues": False,
            "has_projects": False,
            "has_wiki": False
        }
        res, c_status = call_github_api("https://api.github.com/user/repos", token, create_payload, method="POST")
        if c_status not in [200, 201]:
            print(f"[Error] 创建仓库失败 (HTTP {c_status}): {res}")
            return
        print(f"[OK] 仓库创建成功: https://github.com/{username}/{repo_name}")
    elif check_status == 200:
        print(f"[OK] 仓库已存在，将直接推送到已有仓库: https://github.com/{username}/{repo_name}")
    else:
        print(f"[Warning] 检查仓库状态返回 HTTP {check_status}")

    # 3. 推送本地代码
    print(f"\n[3/4] 正在配置 Git 远程并推送本地代码到 main 分支...")
    push_remote_url = f"https://{username}:{token}@github.com/{username}/{repo_name}.git"
    
    # 移除已有的 origin 并添加带认证的 origin
    run_git_cmd(["git", "-c", "safe.directory=*", "remote", "remove", "origin"])
    run_git_cmd(["git", "-c", "safe.directory=*", "remote", "add", "origin", push_remote_url])
    run_git_cmd(["git", "-c", "safe.directory=*", "branch", "-M", "main"])
    
    push_ok = run_git_cmd(["git", "-c", "safe.directory=*", "push", "-u", "origin", "main", "--force"])
    if not push_ok:
        print("[Error] Git 推送失败，请检查网络连接或 Token 权限。")
        return
    print("[OK] 代码与数据成功推送到 GitHub main 分支！")

    # 4. 全自动开启 GitHub Pages
    print(f"\n[4/4] 正在全自动调用 API 启用 GitHub Pages...")
    pages_api_url = f"https://api.github.com/repos/{username}/{repo_name}/pages"
    pages_payload = {
        "source": {
            "branch": "main",
            "path": "/"
        }
    }
    pages_res, p_status = call_github_api(pages_api_url, token, pages_payload, method="POST")
    
    if p_status in [200, 201]:
        print("[OK] GitHub Pages 已成功启用！")
    elif p_status == 409:
        print("[OK] GitHub Pages 之前已处于启用状态。")
    else:
        print(f"[Notice] 启用 GitHub Pages API 返回: HTTP {p_status} (GitHub 会在初次推送到 main 时自动激活 Pages)")

    # 5. 完成
    pages_url = f"https://{username}.github.io/{repo_name}/"
    print("\n==================================================")
    print("🎉 恭喜！全自动部署已顺利完成！")
    print(f"👉 GitHub 仓库: https://github.com/{username}/{repo_name}")
    print(f"👉 GitHub Pages 公网访问链接: {pages_url}")
    print("💡 提示: GitHub Pages 初次生效通常需要 1~2 分钟，稍等片刻即可访问。")
    print("==================================================")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        token_arg = sys.argv[1]
        repo_arg = sys.argv[2] if len(sys.argv) > 2 else "invest-intel"
        deploy(token_arg, repo_arg)
    else:
        env_token = os.environ.get("GITHUB_TOKEN", "")
        if env_token:
            deploy(env_token, "invest-intel")
        else:
            print("Usage: python scripts/deploy_to_github.py <GITHUB_TOKEN> [REPO_NAME]")
