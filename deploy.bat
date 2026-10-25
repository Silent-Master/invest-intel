@echo off
chcp 65001 >nul
echo ========================================================
echo        InvestIntel · 一键全自动 GitHub 部署工具
echo ========================================================
echo.
echo 本工具将自动在你的 GitHub 创建仓库、推送代码并开启 GitHub Pages。
echo.

set /p GITHUB_TOKEN="请输入你的 GitHub Personal Access Token (粘贴后回车): "
if "%GITHUB_TOKEN%"=="" (
    echo [错误] Token 不能为空！
    pause
    exit /b 1
)

set REPO_NAME=invest-intel
set /p REPO_INPUT="请输入仓库名称 [默认: invest-intel，直接回车即可]: "
if not "%REPO_INPUT%"=="" set REPO_NAME=%REPO_INPUT%

echo.
echo [1/3] 正在执行全自动部署管线...
python scripts\deploy_to_github.py %GITHUB_TOKEN% %REPO_NAME%

echo.
echo ========================================================
echo 部署流程执行完毕！按任意键退出窗口。
echo ========================================================
pause
