#!/bin/bash

# 运行主程序的脚本

# 检查是否已经在虚拟环境中
if [[ -z "$VIRTUAL_ENV" ]]; then
    # 如果没有在虚拟环境中，尝试激活默认环境
    VENV_DIR="venv"
    if [ -d "$VENV_DIR" ]; then
        echo "激活虚拟环境..."
        source "$VENV_DIR/bin/activate"
    else
        echo "警告: 未在虚拟环境中运行，且默认虚拟环境不存在"
        echo "建议在虚拟环境中运行或先执行 tools/env_setup.sh"
        read -p "是否继续执行? (y/n): " confirm
        if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
            exit 1
        fi
    fi
else
    echo "检测到已在虚拟环境中运行: $(basename "$VIRTUAL_ENV")"
fi

# 运行主程序
echo "运行DexC2D主程序..."
python main.py

# 获取退出状态
EXIT_CODE=$?

# 根据退出状态提供反馈
if [ $EXIT_CODE -eq 0 ]; then
    echo "程序成功完成！"
else
    echo "程序执行失败，退出码: $EXIT_CODE"
fi

exit $EXIT_CODE