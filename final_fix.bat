@echo off
chcp 65001 > nul 2>&1
echo Sora自动化工具 - 最终解决方案
echo ============================
echo.

:menu
cls
echo 请选择要执行的操作:
echo.
echo [1] 启动调试模式Chrome并登录Sora
echo [2] 运行Sora自动化脚本
echo [3] 修复连接问题
echo [4] 验证调试端口状态
echo [5] 退出
echo.
set /p choice="请输入数字 (1-5): "

if "%choice%"=="1" goto start_chrome
if "%choice%"=="2" goto run_script
if "%choice%"=="3" goto fix_connection
if "%choice%"=="4" goto check_port
if "%choice%"=="5" goto end
goto menu

:start_chrome
cls
echo 启动调试模式Chrome...
echo.
call chrome_debug_fix.bat
goto menu

:run_script
cls
echo 运行自动化脚本...
echo.
set /p img_path="输入图片路径 (留空使用默认值): "
set /p prompt_path="输入提示文本文件路径 (留空使用默认值): "
set /p output_dir="输入输出目录 (留空使用默认值): "

if "%img_path%"=="" set img_path=color_000000.png
if "%prompt_path%"=="" set prompt_path=prompt.txt
if "%output_dir%"=="" set output_dir=./videos

echo.
echo 使用以下参数:
echo 图片: %img_path%
echo 提示: %prompt_path%
echo 输出: %output_dir%
echo.
echo 开始运行...
python improved_sora_auto.py "%img_path%" "%prompt_path%" "%output_dir%"
echo.
pause
goto menu

:fix_connection
cls
echo 修复Chrome连接问题...
echo.
echo 1. 检查Chrome调试端口状态
netstat -ano | findstr :9222
if %errorlevel% neq 0 (
    echo 警告: 未检测到Chrome在端口9222上运行
) else (
    echo 成功: 检测到Chrome在端口9222上运行
)

echo.
echo 2. 尝试访问调试URL
echo 正在执行测试连接...
curl -s http://localhost:9222/json/version > debug_info.txt
type debug_info.txt
echo.

echo 3. 检查Chrome进程
tasklist | findstr chrome.exe

echo.
echo 4. 可能的解决方案:
echo  - 重新启动Chrome调试模式 (选项1)
echo  - 关闭所有Chrome实例后再试
echo  - 检查防火墙设置是否阻止连接
echo  - 重启计算机

echo.
pause
goto menu

:check_port
cls
echo 验证Chrome调试端口状态...
echo.
echo 检查端口9222:
netstat -ano | findstr :9222
echo.

echo 尝试连接到调试端口:
curl -s http://localhost:9222/json/version
echo.
echo.

echo 如果上面显示了JSON响应，说明调试端口工作正常
echo 如果没有响应，则调试端口可能未正确开启

echo.
pause
goto menu

:end
echo.
echo 感谢使用Sora自动化工具!
echo. 