@echo off
chcp 65001 > nul
echo 启动带调试端口的Chrome浏览器...

:: 设置Chrome路径 (根据实际情况可能需要修改)
set CHROME_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"

:: 检查Chrome是否存在
if not exist %CHROME_PATH% (
    echo 找不到Chrome浏览器程序，请确认安装路径:
    echo %CHROME_PATH%
    echo.
    echo 如路径不正确，请编辑脚本文件手动设置正确路径
    pause
    exit /b 1
)

:: 关闭现有Chrome进程 (可选，如果不希望关闭现有进程，可注释掉这几行)
echo 关闭所有现有Chrome进程(如果不想关闭现有Chrome，请取消本操作)...
choice /C YN /M "是否关闭所有Chrome窗口(Y=是，N=否)"
if %errorlevel% equ 1 (
    echo 正在关闭Chrome...
    taskkill /F /IM chrome.exe /T > nul 2>&1
    timeout /t 2 > nul
)

:: 使用调试端口启动Chrome
echo 使用调试端口启动Chrome浏览器...
start "" %CHROME_PATH% --remote-debugging-port=9222 https://sora.chatgpt.com/explore

:: 检测端口是否打开
echo 等待Chrome启动(5秒)...
timeout /t 5 > nul

echo 检查调试端口是否成功打开...
netstat -ano | findstr :9222
if %errorlevel% neq 0 (
    echo 警告: 未检测到Chrome在9222端口监听，调试连接可能会失败
    echo 请确保Chrome已正常启动，且没有别的程序占用9222端口
) else (
    echo 成功！Chrome已在9222端口上运行
)

echo.
echo Chrome已启动，请确保登录Sora账户
echo 然后运行Python脚本: python improved_sora_auto.py
echo.
pause 