@echo off
call run-cli.cmd

REM Generate Python entrypoints
REM Regular entrypoints are broken on non UTF-8 Windows paths
REM See: https://github.com/pypa/setuptools/issues/1246
REM TODO: Replace the "true" entrypoint on "setup-dev"?
python release\build-entrypoints --quiet --traceback-limit 1000 generate-python

REM Main entrypoint
python build\bin\tkmilan-showcase %*

if %ERRORLEVEL% NEQ 0 (
	pause
)
