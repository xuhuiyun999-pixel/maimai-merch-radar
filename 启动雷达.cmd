@echo off
chcp 65001 >nul
setlocal
set "RADAR_ROOT=%~dp0"
if not exist "%RADAR_ROOT%.venv\Scripts\python.exe" (
  echo 请先按 README.md 完成安装，再运行本启动器。
  if /i not "%~1"=="--check" pause
  exit /b 1
)
if /i "%~1"=="--check" goto check
"%RADAR_ROOT%.venv\Scripts\python.exe" -m maimai_radar.cli query --open
set "RADAR_RESULT=%ERRORLEVEL%"
echo.
echo 报告保存在项目的 output 文件夹。
pause
exit /b %RADAR_RESULT%

:check
"%RADAR_ROOT%.venv\Scripts\python.exe" -m maimai_radar.cli query
exit /b %ERRORLEVEL%
