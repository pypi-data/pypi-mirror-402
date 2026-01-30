@echo off
REM Run the regular development script
call setup-dev.cmd

echo -- Install IDE dependencies
pip install -r requirements-ide.txt
echo -- Setup IDE configuration
python release\setup-ide-vscode.py

REM Hide IDE settings folders
attrib +H .spyproject /D
attrib +H .vscode /D

call release\messagebox.vbs "Location: %VENV_LOCATION%" "Virtual Environment setup!\nSupported IDE:\n- Spyder: Use 'run-ide-spyder.cmd'\n- VSCode: Use 'run-ide-vscode.cmd'"
