@echo off
call run-cli.cmd

call release\test.cmd

echo:
echo # Test Process Completed!
echo:
pause
REM TODO: Use timeout -T 30
