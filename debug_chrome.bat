@echo off
chcp 65001 > nul
echo 正在启动Chrome调试模式...

:: 关闭所有Chrome进程
echo 关闭现有Chrome...
taskkill /F /IM chrome.exe /T > nul 2>&1
timeout /t 2 > nul

:: 创建用户数据目录
echo 创建用户数据目录...
mkdir "C:\tmp\chrome-sora-profile" 2>nul

:: 启动带调试端口的Chrome
echo 启动Chrome...
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\tmp\chrome-sora-profile" https://sora.chatgpt.com/create

echo Chrome已启动，等待20秒让浏览器完全加载...
timeout /t 20 > nul

:: 检查Chrome是否正在监听端口
echo 检查Chrome是否监听9222端口...
netstat -ano | findstr :9222
if %errorlevel% neq 0 (
    echo Chrome似乎未能以调试模式启动
    echo 请手动确认Chrome已启动并访问Sora
    pause
    exit /b
)

echo Chrome已成功在9222端口监听
echo 运行Python脚本...
python raw2mp4.py color_000000.png prompt.txt 