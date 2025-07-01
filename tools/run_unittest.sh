#!/bin/bash

# 运行单元测试的脚本

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

# 获取脚本参数
if [ $# -eq 0 ]; then
    # 没有参数，运行所有测试
    echo "运行所有单元测试..."
    python -m unittest discover -s tests
else
    # 有参数，运行指定的测试
    TEST_MODULE=$1
    echo "运行指定的测试模块: $TEST_MODULE"
    python -m unittest $TEST_MODULE
fi

# 获取退出状态
EXIT_CODE=$?

# 根据退出状态提供反馈
if [ $EXIT_CODE -eq 0 ]; then
    echo "测试成功完成！"
else
    echo "测试执行失败，退出码: $EXIT_CODE"
fi

exit $EXIT_CODE 