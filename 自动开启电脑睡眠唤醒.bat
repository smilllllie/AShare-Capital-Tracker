@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ==========================================
echo 正在开启系统的“允许唤醒定时器”全局权限...
echo ==========================================
powercfg /SETACVALUEINDEX SCHEME_CURRENT 238c9fa8-0aad-41ed-83f4-97be242c8f20 bd3b718a-0680-4d9d-8ab2-e1d2b4ac806d 1
powercfg /SETDCVALUEINDEX SCHEME_CURRENT 238c9fa8-0aad-41ed-83f4-97be242c8f20 bd3b718a-0680-4d9d-8ab2-e1d2b4ac806d 1
powercfg /SETACTIVE SCHEME_CURRENT
echo [OK] 电源唤醒权限已开启。

echo.
echo ==========================================
echo 正在为三个 AI 推送任务赋予唤醒电脑的特权...
echo ==========================================
powershell -Command "$tasks = @('AI_News_Morning', 'AI_News_Intraday', 'AI_News_Evening'); foreach ($t in $tasks) { $task = Get-ScheduledTask -TaskName $t -ErrorAction SilentlyContinue; if ($task) { $task.Settings.WakeToRun = $true; Set-ScheduledTask -InputObject $task | Out-Null; Write-Host ('[OK] 成功赋予唤醒权限: ' + $t) } else { Write-Host ('[警告] 找不到任务: ' + $t) } }"

echo.
echo ==========================================
echo 全部自动化设置成功！
echo 现在你的电脑在“睡眠”状态下也会被强行唤醒起来干活了。
echo.
echo 【避坑提醒】：
echo 1. 不用电脑时，请点“睡眠”，千万别点“关机”。
echo 2. 绝大部分笔记本在【拔掉电源】的情况下是拒绝被唤醒的，建议插着电源测试。
echo ==========================================
pause
