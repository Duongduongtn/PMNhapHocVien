@echo off
setlocal
set PORT=3021

echo [openprototype] Kiem tra cong %PORT%...
netstat -aon | findstr /C:":%PORT% " | findstr LISTENING >nul 2>&1
if not errorlevel 1 (
    echo [openprototype] Cong %PORT% dang BAN - co the la du an khac dang chay.
    echo [openprototype] Kiem tra roi doi cong trong ~/.claude/local-ports.md, KHONG tu kill.
    pause
    exit /b 1
)

echo [openprototype] Khoi dong ui-demo tai http://localhost:%PORT%
cd /d "%~dp0ui-demo"

echo [openprototype] Se mo trinh duyet sau 8 giay...
start "" /b cmd /c "timeout /t 8 /nobreak >nul & start http://localhost:%PORT%"

call pnpm dev
endlocal
