@echo off
REM EDUAI Learning — Backup Database (wrapper PowerShell)
REM Usage: backup_db.bat
REM Requires: pg_dump in PATH, PowerShell 5+

powershell -ExecutionPolicy Bypass -File "%~dp0backup_db.ps1" %*
