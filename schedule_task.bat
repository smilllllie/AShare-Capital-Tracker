@echo off
chcp 65001 >nul
echo ==========================================
echo    创建职业级 AI 新闻推送三段式定时任务
echo ==========================================

:: 获取当前目录
set "CURRENT_DIR=%~dp0"
set "PYTHON_SCRIPT=%CURRENT_DIR%daily_news_pusher.py"

:: 假设用户的 Python 在环境变量中，直接调用 python
set "PYTHON_EXE=python"

:: 尝试创建早盘定调任务 (每天早上 08:30 运行)
echo [1/3] 正在注册早盘定调任务 (08:30)...
schtasks /create /tn "AI_News_Morning" /tr "\"%PYTHON_EXE%\" \"%PYTHON_SCRIPT%\" --mode morning" /sc daily /st 08:30 /f

:: 尝试创建盘中监控任务 (每天 09:00 至 15:00 每小时运行一次)
echo [2/3] 正在注册盘中突发监控任务 (09:00-15:00 每小时)...
schtasks /create /tn "AI_News_Intraday" /tr "\"%PYTHON_EXE%\" \"%PYTHON_SCRIPT%\" --mode intraday" /sc hourly /mo 1 /st 09:30 /et 15:00 /f

:: 尝试创建盘后复盘任务 (每天晚上 22:00 运行)
echo [3/3] 正在注册盘后资金复盘任务 (22:00)...
schtasks /create /tn "AI_News_Evening" /tr "\"%PYTHON_EXE%\" \"%PYTHON_SCRIPT%\" --mode evening" /sc daily /st 22:00 /f

echo.
echo ==========================================
echo 所有定时任务创建完成！
echo 你可以在 Windows 搜索栏输入 "任务计划程序" 来查看或修改这些任务。
pause
