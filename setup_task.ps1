# ============================================================
# A鑲℃儏缁华琛ㄧ洏 - Windows 璁″垝浠诲姟閰嶇疆鑴氭湰
# 姣忎釜浜ゆ槗鏃ヤ笅鍗?3:30 鑷姩杩愯 data_fetcher.py
# 浣跨敤鏂规硶锛氫互绠＄悊鍛樿韩浠借繍琛?PowerShell锛屾墽琛屾鑴氭湰
# ============================================================

$ErrorActionPreference = "Stop"

$TaskName = "StockDashboard-Update"
$ScriptPath = "D:\stock-dashboard\data_fetcher.py"
$PythonPath = "python"
$TaskTime = "15:30"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  A鑲℃儏缁华琛ㄧ洏 - 瀹氭椂浠诲姟閰嶇疆" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 妫€鏌ョ鐞嗗憳鏉冮檺
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "[璀﹀憡] 褰撳墠涓嶆槸绠＄悊鍛樻潈闄愶紝鍙兘鏃犳硶鍒涘缓璁″垝浠诲姟銆? -ForegroundColor Yellow
    Write-Host "璇峰彸閿?PowerShell 閫夋嫨銆屼互绠＄悊鍛樿韩浠借繍琛屻€嶅悗閲嶈瘯銆? -ForegroundColor Yellow
    Write-Host ""
}

# 妫€鏌?Python
try {
    $pythonVersion = & $PythonPath --version 2>&1
    Write-Host "[OK] Python 鍙敤: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[閿欒] 鏈壘鍒?Python锛岃纭繚 python 鍦?PATH 涓? -ForegroundColor Red
    exit 1
}

# 妫€鏌ヨ剼鏈?if (-not (Test-Path $ScriptPath)) {
    Write-Host "[閿欒] 鎵句笉鍒拌剼鏈? $ScriptPath" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] 鎵惧埌鑴氭湰: $ScriptPath" -ForegroundColor Green

# 鍒犻櫎鏃т换鍔★紙濡傛灉瀛樺湪锛?$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "[淇℃伅] 宸插瓨鍦ㄥ悓鍚嶄换鍔★紝姝ｅ湪鍒犻櫎..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# 鍒涘缓浠诲姟鎿嶄綔
$Action = New-ScheduledTaskAction -Execute $PythonPath `
    -Argument "`"$ScriptPath`"" `
    -WorkingDirectory "D:\stock-dashboard"

# 鍒涘缓瑙﹀彂鍣細姣忎釜浜ゆ槗鏃ワ紙鍛ㄤ竴鍒板懆浜旓級涓嬪崍3:30
$Trigger = New-ScheduledTaskTrigger -Daily -At $TaskTime
# 璁剧疆涓哄懆涓€鑷冲懆浜?$Trigger.DaysOfWeek = 62  # 鍛ㄤ竴(2)+鍛ㄤ簩(4)+鍛ㄤ笁(8)+鍛ㄥ洓(16)+鍛ㄤ簲(32)=62

# 鍒涘缓浠诲姟璁剧疆
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10)

# 鍒涘缓浠诲姟涓讳綋
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

# 娉ㄥ唽浠诲姟
Register-ScheduledTask -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description "姣忎釜浜ゆ槗鏃ヤ笅鍗?:30鑷姩鎶撳彇A鑲¤鎯呮暟鎹苟鏇存柊浠〃鐩? `
    -Force

Write-Host ""
Write-Host "[鎴愬姛] 璁″垝浠诲姟宸插垱寤?" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  浠诲姟鍚嶇О: $TaskName" -ForegroundColor White
Write-Host "  鎵ц鏃堕棿: 姣忎釜浜ゆ槗鏃?$TaskTime" -ForegroundColor White
Write-Host "  鎵ц鍛戒护: $PythonPath `"$ScriptPath`"" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 鍙€夛細绔嬪嵆娴嬭瘯杩愯涓€娆?$confirm = Read-Host "鏄惁绔嬪嵆娴嬭瘯杩愯涓€娆★紵(y/n)"
if ($confirm -eq 'y' -or $confirm -eq 'Y') {
    Write-Host "姝ｅ湪杩愯娴嬭瘯..." -ForegroundColor Yellow
    & $PythonPath $ScriptPath
    Write-Host "娴嬭瘯瀹屾垚銆? -ForegroundColor Green
}

Write-Host ""
Write-Host "鎻愮ず锛氬彲鍦ㄣ€屼换鍔¤鍒掔▼搴忋€嶄腑绠＄悊姝や换鍔★紙taskschd.msc锛? -ForegroundColor Gray
