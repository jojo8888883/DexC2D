#!/bin/bash
echo "Sora Web界面自动化测试脚本"

# 设置环境变量（请替换为您的实际账号信息）
export OPENAI_USERNAME="your_username"
export OPENAI_PASSWORD="your_password"

# 创建prompt_and_image目录结构
python pipeline/run_sora_automation.py --init

echo
echo "请将color_000000.png图像文件放入prompt_and_image目录中"
echo "然后按回车键继续..."
read

# 确认图像文件存在
if [ ! -f "prompt_and_image/color_000000.png" ]; then
  echo "错误：找不到prompt_and_image/color_000000.png文件"
  echo "请确保图像文件已正确放置"
  exit 1
fi

# 运行自动化流程
echo "开始运行Sora自动化流程..."
python pipeline/run_sora_automation.py --output output

echo
if [ $? -eq 0 ]; then
  echo "自动化流程成功完成！"
else
  echo "自动化流程执行失败，请检查日志文件"
fi

echo "按回车键退出..."
read 