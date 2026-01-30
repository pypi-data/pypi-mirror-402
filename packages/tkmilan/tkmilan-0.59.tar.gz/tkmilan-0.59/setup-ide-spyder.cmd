@echo off
REM Run the regular development script
call setup-dev.cmd

echo -- Install IDE dependencies
pip install -r requirements-ide.txt

REM Hide IDE settings folders
attrib +H .spyproject /D

call release\messagebox.vbs "Location: %VENV_LOCATION%" "Virtual Environment setup!\nSupported IDE 'Spyder':\nUse 'run-ide-spyder.cmd'"
