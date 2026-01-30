@echo off
call release\python-selection.bat
if %ERRORLEVEL% NEQ 0 (
	exit /B %ERRORLEVEL%
)
call release\activate-venv.cmd

REM Set helper variables
REM TODO: Move all other usage of this here (including PROJECT_NAME)
for /f %%i in ('python setup.py --name') do set PROJECT=%%i
for /f %%i in ('python setup.py --version') do set RELEASE=%%i
:: echo # Project Name = %PROJECT%
:: echo # Release = %RELEASE%

REM Show Python version
python --version
REM Show Python Optimization
if "%PYTHONOPTIMIZE%" NEQ "" (
	echo Python Optimize: %PYTHONOPTIMIZE%
)
