@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3.12 -m venv .venv
  if errorlevel 1 goto :error
)
call ".venv\Scripts\activate.bat"
python -m pip install -r requirements.txt
if errorlevel 1 goto :error
python backend\app.py
exit /b %errorlevel%
:error
echo.
echo FoodSafe could not start. Check that Python 3.12 is installed.
pause
exit /b 1
