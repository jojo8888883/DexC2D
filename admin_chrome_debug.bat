@echo off
echo Starting Chrome with debugging port (Admin mode)...

:: Create a temporary VBS script to elevate privileges
echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\elevate.vbs"
echo UAC.ShellExecute "C:\Program Files\Google\Chrome\Application\chrome.exe", "--remote-debugging-port=9222 https://sora.chatgpt.com/explore", "", "runas", 1 >> "%temp%\elevate.vbs"

:: Run the VBS script
echo Launching Chrome with elevated privileges...
cscript //nologo "%temp%\elevate.vbs"
del "%temp%\elevate.vbs"

echo Chrome should now be starting with admin rights.
echo Please ensure you are logged in to Sora.
echo.
echo Wait 10 seconds for Chrome to initialize...
timeout /t 10 > nul

:: Check if Chrome is listening on the port
echo Checking if Chrome is listening on port 9222...
netstat -ano | findstr :9222
if %errorlevel% neq 0 (
    echo WARNING: Chrome may not be properly listening on port 9222
    echo We will try to run the script anyway.
)

echo Running Python script...
python raw2mp4.py color_000000.png prompt.txt 