@echo off
echo ===========================================
echo 连接到已有Chrome实例的指南
echo ===========================================
echo.
echo 请按照以下步骤操作:
echo.
echo 1. 关闭您桌面上的所有Chrome窗口(请先保存重要内容)
echo 2. 按任意键继续，将使用远程调试模式重启Chrome
echo    这将保留您的登录状态和浏览历史
echo.
echo 注意: 这将重新打开您之前的Chrome窗口和标签页
echo ===========================================
pause

rem 启动带调试端口的Chrome
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222

echo.
echo Chrome已启动并开启了调试端口
echo 请在Chrome中访问: https://sora.chatgpt.com/create
echo 并确保已登录
echo.
echo 然后运行脚本: python raw2mp4.py color_000000.png prompt.txt
echo =========================================== 