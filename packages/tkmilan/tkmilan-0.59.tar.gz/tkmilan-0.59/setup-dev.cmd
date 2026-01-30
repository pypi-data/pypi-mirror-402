@echo off
call release\python-selection.bat
if %ERRORLEVEL% NEQ 0 (
	exit /B %ERRORLEVEL%
)
REM Reimplements "make venv"
REM See `Makefile.venv`

call release\setup-venv.cmd

call release\activate-venv.cmd
call release\setup-dependencies.cmd
echo -- Install project dependencies
for /F %%G in ('DIR /B %REQUIREMENTS_TXT%') DO pip install -r %%G
echo -- Install this project, development mode
pip install -e .
