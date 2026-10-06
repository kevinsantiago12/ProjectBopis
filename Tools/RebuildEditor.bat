@echo off
rem Double-click wrapper for RebuildEditor.ps1: close editor -> build -> reopen editor.
rem Pass-through arguments work too, e.g.  RebuildEditor.bat -Clean
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0RebuildEditor.ps1" %*
echo.
pause
