@echo off
chcp 65001 > nul 2>&1
echo 简单Sora自动化启动器

:: 设置Chrome路径
set CHROME_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"

:: 检查Chrome是否存在
if not exist %CHROME_PATH% (
    echo Chrome浏览器未找到，请手动输入Chrome路径
    set /p CHROME_PATH="输入Chrome完整路径 (需要引号): "
    if not exist %CHROME_PATH% (
        echo 输入的路径不存在
        pause
        exit /b 1
    )
)

:: 停止现有Chrome进程
echo 关闭现有Chrome实例...
taskkill /F /IM chrome.exe >nul 2>&1

:: 启动Chrome
echo 启动Chrome浏览器...
start "" %CHROME_PATH% --remote-debugging-port=9222 https://sora.chatgpt.com/explore

echo 请等待Chrome完全启动并登录Sora账户...
echo 按任意键继续...
pause > nul

:: 运行Python脚本
echo 开始运行自动化脚本...
python improved_sora_auto.py

echo 脚本执行完成。按任意键退出...
pause > nul 