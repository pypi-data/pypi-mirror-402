@echo off
call run-cli.cmd
if %ERRORLEVEL% NEQ 0 (
	call release\messagebox.vbs "ERROR: Missing IDE setup" "Run 'setup-ide.cmd' first."
	exit 1
)

REM Find a VSCode family binary
REM - Ordered from less specific to more specific
REM   AKA: last program wins
set program=
where /Q code
if %ERRORLEVEL% EQU 0 (
	set program=code
)
where /Q codium
if %ERRORLEVEL% EQU 0 (
	set program=codium
)
if [%program%] EQU [] (
	call release\messagebox.vbs "ERROR: Missing IDE" "Cannot find any VSCode-family IDE\nSupported:\n- code\n- codium"
	exit 1
)

REM Make sure the Python extension is installed: "ms-python.python"
REM -- %program% --list-extensions
REM -- %program% --install-extension "ms-python.python"

REM Generate Python entrypoints
REM Regular entrypoints are broken on non UTF-8 Windows paths
REM See: https://github.com/pypa/setuptools/issues/1246
REM TODO: Replace the "true" entrypoint on "setup-dev"?
python release\build-entrypoints --quiet --traceback-limit 1000 generate-python

echo:
echo Running VSCode [%program%]
echo:
echo ----
echo NOTE: This window will remain open while VSCode remains open. Please minimize it, I can't close it.
echo ----
echo:
REM Run VSCode Program (Open Main Entrypoint is technically optional)
REM - Run on "foreground", since it blocks this window anyway
%program% ^
	-g build\bin\tkmilan-showcase ^
	%* ^
	%CD%
