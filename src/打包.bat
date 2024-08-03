@echo off
del /q /s /f "D:\Zropk\Documents\pythonProject\idv-tool\src\build"
del /q /s /f "D:\Zropk\Documents\pythonProject\idv-tool\src\dist"
del /q "D:\Zropk\Documents\pythonProject\idv-tool\src\test\idv-tool.exe
del /q "D:\Zropk\Documents\pythonProject\idv-tool\src\idv-tool.exe.spec"
del /q "D:\Zropk\Documents\pythonProject\idv-tool\src\updater.exe.spec"
pyinstaller main.py --onefile -n idv-tool.exe --uac-admin