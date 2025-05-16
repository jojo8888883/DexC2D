@echo off
chcp 65001 > nul
echo 正在准备连接到您的桌面Chrome...

:: 关闭所有Chrome进程
echo 关闭所有现有Chrome进程(请先保存您的工作)...
taskkill /F /IM chrome.exe /T > nul 2>&1
timeout /t 2 > nul

:: 使用默认用户数据目录启动Chrome
echo 使用您的默认配置启动Chrome...
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 https://sora.chatgpt.com/explore

echo Chrome已启动，请确保您已登录Sora
echo 将等待15秒让浏览器加载...
timeout /t 15 > nul

:: 检查Chrome是否正在监听端口
echo 检查Chrome是否监听9222端口...
netstat -ano | findstr :9222
if %errorlevel% neq 0 (
    echo Chrome似乎未能以调试模式启动
    echo 请手动确认Chrome已启动
    pause
    exit /b
)

echo 成功！Chrome已在调试模式下运行，使用您的默认配置。
echo.
echo 确认您已成功登录后，按任意键继续...
pause

echo 运行Python脚本...
python raw2mp4.py color_000000.png prompt.txt 