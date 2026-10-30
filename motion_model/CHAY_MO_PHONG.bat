@echo off
cd /d "%~dp0.."
where py >nul 2>nul
if errorlevel 1 (
  python -m motion_model.simulator
) else (
  py -3 -m motion_model.simulator
)
if errorlevel 1 pause
