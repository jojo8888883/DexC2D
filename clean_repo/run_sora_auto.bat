@echo off
chcp 65001 > nul
echo Sora自动化脚本启动器
echo.

:: 设置默认参数
set IMAGE_PATH=color_000000.png
set PROMPT_PATH=prompt.txt
set OUTPUT_DIR=./videos

:: 获取自定义参数（如果提供）
echo 当前默认参数:
echo 图片路径: %IMAGE_PATH%
echo 提示文件: %PROMPT_PATH%
echo 输出目录: %OUTPUT_DIR%
echo.

:: 询问是否使用自定义参数
choice /C YN /M "是否要使用自定义参数(Y=是，N=否)"
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

:: 运行Python脚本
echo 正在运行自动化脚本...
python improved_sora_auto.py "%IMAGE_PATH%" "%PROMPT_PATH%" "%OUTPUT_DIR%"

:: 检查Python脚本的返回值
if %errorlevel% neq 0 (
    echo 脚本执行失败，返回错误代码 %errorlevel%
) else (
    echo 脚本执行成功
)

pause 