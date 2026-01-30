@echo off
REM Run the regular development script
call setup-dev.cmd

echo -- Setup IDE configuration
python release\setup-ide-vscode.py

REM Hide IDE settings folders
attrib +H .vscode /D

call release\messagebox.vbs "Location: %VENV_LOCATION%" "Virtual Environment setup!\nSupported IDE 'VSCode':\nUse 'run-ide-vscode.cmd'"
