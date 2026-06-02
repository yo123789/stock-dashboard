@echo off
chcp 65001 >nul
cd /d D:\stock-dashboard
echo ========================================
echo   A鑲℃儏缁华琛ㄧ洏 - 鏈湴鏈嶅姟鍣ㄥ惎鍔ㄤ腑...
echo ========================================
echo.
echo   娴忚鍣ㄥ皢鑷姩鎵撳紑 http://localhost:8765
echo   鎸?Ctrl+C 鍙仠姝㈡湇鍔″櫒
echo.
start http://localhost:8765
python -m http.server 8765
pause
