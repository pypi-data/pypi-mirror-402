@echo off
call run-cli.cmd
if %ERRORLEVEL% NEQ 0 (
	call release\messagebox.vbs "ERROR: Missing IDE setup" "Run 'setup-ide.cmd' first."
	exit 1
)

REM Generate Python entrypoints
REM Regular entrypoints are broken on non UTF-8 Windows paths
REM See: https://github.com/pypa/setuptools/issues/1246
REM TODO: Replace the "true" entrypoint on "setup-dev"?
python release\build-entrypoints --quiet --traceback-limit 1000 generate-python

REM Run Spyder (Open Main Entrypoint)
REM - Run on "background"
start spyder --project=%CD% --workdir=%CD% %* ^
	build\bin\tkmilan-showcase
