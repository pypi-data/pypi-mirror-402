@echo off
call release\python-selection.bat
if %ERRORLEVEL% NEQ 0 (
	exit /B %ERRORLEVEL%
)
REM Reimplements "Makefile.venv"

REM Deactivate the current VENV, if active
WHERE deactivate >NUL
if %ERRORLEVEL% EQU 0 (
	call deactivate
)

call release\clean-venv.cmd
