@echo off
echo 正在启动Chrome并打开Sora...
echo 请确保您的网络环境可以访问Sora

mkdir "C:\tmp\chrome-sora-profile" 2>nul

"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\tmp\chrome-sora-profile" https://sora.chatgpt.com/create

echo Chrome已启动，请完成登录后，再运行raw2mp4.py脚本 