@echo off
chcp 65001 >nul
rem ================================================================
rem  Mo TOOL nap DB (backend FastAPI 8000 + webui Vite 3011).
rem  Chay trong cua so rieng, ben. Tat: chay tool-stop.bat
rem ================================================================
cd /d "%~dp0"
echo === Don tien trinh cu tren cong 8000 / 3011 (neu co) ===
call "%~dp0tool-stop.bat" quiet
echo === Khoi dong backend (FastAPI, cong 8000) ===
start "Tool Backend 8000" cmd /k "chcp 65001 >nul & cd tool & set PYTHONUTF8=1& .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
echo === Khoi dong webui (Vite, cong 3011) ===
start "Tool WebUI 3011" cmd /k "chcp 65001 >nul & cd tool\webui & pnpm dev"
echo === Doi vai giay roi mo trinh duyet ===
timeout /t 8 >nul
start "" http://localhost:3011
echo.
echo Tool dang chay. Dang nhap: admin / admin@123 (quan tri).
echo Dong 2 cua so "Tool Backend 8000" / "Tool WebUI 3011" hoac chay tool-stop.bat de tat.
echo.
pause
