@echo off
setlocal
title Revisor Livro

powershell.exe -NoExit -ExecutionPolicy Bypass -File "%~dp0Revisor-Livro.ps1" -LauncherPath "%~f0"

