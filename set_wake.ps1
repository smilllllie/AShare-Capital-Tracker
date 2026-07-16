$tasks = @("AI_News_Morning", "AI_News_Intraday", "AI_News_Evening")
foreach ($t in $tasks) {
    try {
        $task = Get-ScheduledTask -TaskName $t
        if ($task) {
            $task.Settings.WakeToRun = $true
            Set-ScheduledTask -InputObject $task | Out-Null
            Write-Host "Success: $t"
        }
    } catch {
        Write-Host "Failed: $t"
    }
}
