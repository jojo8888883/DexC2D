@echo off
chcp 65001 > nul 2>&1
echo Sora自动化 - Chrome调试模式启动工具
echo ==================================
echo.

:: 查找Chrome路径
echo 查找Chrome安装位置...
set CHROME_PATH=

:: 常见安装位置
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    set CHROME_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"
    goto :chrome_found
)

if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    set CHROME_PATH="C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    goto :chrome_found
)

:: 查找用户本地安装
for %%a in (
    "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
    "%USERPROFILE%\AppData\Local\Google\Chrome\Application\chrome.exe"
) do (
    if exist %%a (
        set CHROME_PATH=%%a
        goto :chrome_found
    )
)

:: 没找到，手动输入
echo 未找到Chrome浏览器，请输入Chrome可执行文件的完整路径:
set /p CHROME_PATH="Chrome路径 (包含引号): "
if not exist %CHROME_PATH% (
    echo 路径无效: %CHROME_PATH%
    echo 无法继续
    pause
    exit /b 1
)

:chrome_found
echo 找到Chrome: %CHROME_PATH%

:: 关闭现有Chrome进程
echo.
echo 是否关闭所有现有的Chrome窗口?
echo 注意: 这将关闭所有打开的Chrome窗口!
choice /C YN /M "选择 (Y=是, N=否): "
if %errorlevel% equ 1 (
    echo 正在关闭Chrome...
    taskkill /F /IM chrome.exe >nul 2>&1
    timeout /t 3 >nul
)

:: 启动Chrome调试模式
echo.
echo 正在启动Chrome调试模式...
echo 调试端口: 9222
echo 启动URL: https://sora.chatgpt.com/explore
echo.

:: 运行Chrome
echo 正在启动Chrome...
start "" %CHROME_PATH% --remote-debugging-port=9222 --disable-features=IsolateOrigins,site-per-process --user-data-dir="%USERPROFILE%\Chrome-Debug-Profile" https://sora.chatgpt.com/explore

:: 等待启动
echo 等待Chrome启动 (15秒)...
timeout /t 15 >nul

:: 验证调试端口
echo 验证调试端口...
netstat -ano | findstr :9222
if %errorlevel% neq 0 (
    echo 警告: 未检测到Chrome调试端口9222
    echo Chrome可能未正确启动或无法使用调试端口
    echo.
    echo 请尝试以下操作:
    echo 1. 确保没有其他Chrome实例占用端口9222
    echo 2. 以管理员权限运行此批处理文件
    echo 3. 检查防火墙设置是否阻止了连接
) else (
    echo 成功! Chrome已在调试模式下运行，端口9222开启
)

echo.
echo 请在Chrome中登录Sora账户
echo 完成后再运行improved_sora_auto.py脚本
echo.
echo 按任意键退出...
pause >nul 