@echo off
setlocal EnableExtensions
chcp 65001 >nul
title Exiles Game Manager Launcher
set "EGM_ROOT=%~dp0"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%EGM_ROOT%Start_Exiles_Game_Manager.ps1"
exit /b %ERRORLEVEL%
