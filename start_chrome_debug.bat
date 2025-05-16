@echo off
echo Starting Chrome with debugging port...

:: Close all existing Chrome processes
taskkill /F /IM chrome.exe /T > nul 2>&1
timeout /t 2 > nul

:: Start Chrome with debugging port
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 https://sora.chatgpt.com/explore

echo Chrome started with debugging port.
echo Please ensure you are logged in to Sora.
echo.
echo After logging in, press any key to continue...
pause

:: Check if Chrome is listening on the port
netstat -ano | findstr :9222
if %errorlevel% neq 0 (
    echo ERROR: Chrome is not listening on port 9222
    pause
    exit /b 1
)

echo Running Python script...
python raw2mp4.py color_000000.png prompt.txt 