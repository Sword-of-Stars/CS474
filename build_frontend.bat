@echo off
setlocal
cd /d "%~dp0frontend"
copy /Y "..\interfaces\automataeditor.jsx" "src\AutomataEditor.jsx" >nul
call npm install
if errorlevel 1 exit /b %errorlevel%
call npm run build
exit /b %errorlevel%
