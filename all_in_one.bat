@echo off
chcp 65001 > nul
echo Sora自动化一键运行工具
echo =====================
echo.

:: 设置默认参数
set IMAGE_PATH=color_000000.png
set PROMPT_PATH=prompt.txt
set OUTPUT_DIR=./videos
set CHROME_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"

:: 检查Chrome是否存在
if not exist %CHROME_PATH% (
    echo 找不到Chrome浏览器程序，请确认安装路径:
    echo %CHROME_PATH%
    echo.
    set /p "CHROME_PATH=请输入Chrome浏览器的正确路径 (包含引号): "
    if not exist %CHROME_PATH% (
        echo 输入的路径不存在，无法继续
        pause
        exit /b 1
    )
)

:: 获取自定义参数
echo 当前默认参数:
echo 图片路径: %IMAGE_PATH%
echo 提示文件: %PROMPT_PATH%
echo 输出目录: %OUTPUT_DIR%
echo.

:: 询问是否使用自定义参数
echo 是否要使用自定义参数?
choice /C YN /M "选择 Y=是，N=否"
if %errorlevel% equ 1 (
    :: 询问图片路径
    set /p "IMAGE_PATH=输入图片路径 (直接回车使用默认值): "
    if "%IMAGE_PATH%"=="" set IMAGE_PATH=color_000000.png
    
    :: 询问提示文件路径
    set /p "PROMPT_PATH=输入提示文件路径 (直接回车使用默认值): "
    if "%PROMPT_PATH%"=="" set PROMPT_PATH=prompt.txt
    
    :: 询问输出目录
    set /p "OUTPUT_DIR=输入输出目录 (直接回车使用默认值): "
    if "%OUTPUT_DIR%"=="" set OUTPUT_DIR=./videos
)

:: 显示将使用的参数
echo.
echo 使用以下参数运行脚本:
echo 图片路径: %IMAGE_PATH%
echo 提示文件: %PROMPT_PATH%
echo 输出目录: %OUTPUT_DIR%
echo.

:: 检查图片文件是否存在
if not exist "%IMAGE_PATH%" (
    echo 错误: 图片文件不存在 - %IMAGE_PATH%
    pause
    exit /b 1
)

:: 检查提示文件是否存在
if not exist "%PROMPT_PATH%" (
    echo 错误: 提示文件不存在 - %PROMPT_PATH%
    pause
    exit /b 1
)

:: 确保输出目录存在
if not exist "%OUTPUT_DIR%" (
    echo 输出目录不存在，将创建该目录: %OUTPUT_DIR%
    mkdir "%OUTPUT_DIR%"
)

:: 询问是否关闭现有Chrome
echo.
echo 是否关闭所有现有Chrome窗口?
choice /C YN /M "选择 Y=是，N=否"
if %errorlevel% equ 1 (
    echo 正在关闭Chrome...
    taskkill /F /IM chrome.exe /T > nul 2>&1
    timeout /t 2 > nul
)

:: 使用调试端口启动Chrome - 尝试更可靠的方式
echo 使用调试端口启动Chrome浏览器...

:: 创建临时VBS脚本以提升特权
echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\start_chrome.vbs"
echo UAC.ShellExecute %CHROME_PATH%, "--remote-debugging-port=9222 --disable-web-security --no-sandbox https://sora.chatgpt.com/explore", "", "runas", 1 >> "%temp%\start_chrome.vbs"

:: 运行VBS脚本
cscript //nologo "%temp%\start_chrome.vbs"
del "%temp%\start_chrome.vbs"

:: 等待Chrome启动
echo 等待Chrome启动并检查调试端口(15秒)...
timeout /t 15 > nul

:: 检查调试端口
netstat -ano | findstr :9222
if %errorlevel% neq 0 (
    echo 警告: 未检测到Chrome在9222端口监听
    echo 尝试再次启动Chrome...
    
    :: 再次尝试启动Chrome，这次使用直接命令
    start "" %CHROME_PATH% --remote-debugging-port=9222 --disable-web-security https://sora.chatgpt.com/explore
    
    :: 再次等待
    echo 再次等待Chrome启动(15秒)...
    timeout /t 15 > nul
    
    :: 再次检查
    netstat -ano | findstr :9222
    if %errorlevel% neq 0 (
        echo 仍然无法检测到Chrome在9222端口监听
        echo 请确保Chrome已正常启动，且没有别的程序占用9222端口
        choice /C YN /M "是否仍要继续? (Y=是，N=否)"
        if %errorlevel% neq 1 (
            echo 操作已取消
            pause
            exit /b 1
        )
    ) else (
        echo 成功！Chrome已在9222端口上运行
    )
) else (
    echo 成功！Chrome已在9222端口上运行
)

echo.
echo 请在Chrome中登录Sora账户...
echo 确保您已成功登录并可以看到Sora页面
choice /C YN /M "已完成登录并准备开始自动化流程? (Y=是，N=否)"
if %errorlevel% neq 1 (
    echo 操作已取消
    pause
    exit /b 1
)

:: 运行自动化脚本
echo.
echo 正在运行自动化脚本...
python improved_sora_auto.py "%IMAGE_PATH%" "%PROMPT_PATH%" "%OUTPUT_DIR%"

:: 检查Python脚本的返回值
if %errorlevel% neq 0 (
    echo 脚本执行失败，返回错误代码 %errorlevel%
    echo 请查看生成的截图文件以了解详情
) else (
    echo 脚本执行成功！
    echo 视频应已保存在 %OUTPUT_DIR% 目录中
)

echo.
echo 操作完成。按任意键退出...
pause 