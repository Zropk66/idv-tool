@echo off
pyinstaller main.py --onefile -n idv-tool.exe --uac-admin
pyarmor gen --pack dist/idv-tool.exe main.py