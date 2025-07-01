#!/bin/bash

# 设置环境变量和安装依赖包的脚本

# 检查是否已经在虚拟环境中
if [[ ! -z "$VIRTUAL_ENV" ]]; then
    echo "检测到已在虚拟环境中运行: $(basename "$VIRTUAL_ENV")"
    read -p "是否继续在当前环境中安装依赖? (y/n): " confirm
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        echo "操作已取消"
        exit 0
    fi
    # 使用当前环境
    USING_CURRENT_ENV=true
else
    USING_CURRENT_ENV=false
    # 询问是否使用自定义环境名称
    read -p "是否使用自定义虚拟环境名称? (y/n，默认使用'venv'): " custom_env
    if [[ "$custom_env" == "y" || "$custom_env" == "Y" ]]; then
        read -p "请输入虚拟环境名称: " VENV_DIR
        VENV_DIR=${VENV_DIR:-venv}
    else
        VENV_DIR="venv"
    fi
fi

# 检查Python环境
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "检测到Python版本: $PYTHON_VERSION"

# 检查是否已安装pip
if ! command -v pip3 &> /dev/null; then
    echo "未找到pip3，正在安装..."
    sudo apt-get update
    sudo apt-get install -y python3-pip
fi

if [[ "$USING_CURRENT_ENV" == "false" ]]; then
    # 检查是否已安装venv模块
    if ! python3 -c "import venv" &> /dev/null; then
        echo "未找到venv模块，正在安装..."
        sudo apt-get install -y python3-venv
    fi

    # 创建虚拟环境
    if [ ! -d "$VENV_DIR" ]; then
        echo "创建虚拟环境: $VENV_DIR"
        python3 -m venv "$VENV_DIR"
    else
        echo "虚拟环境已存在: $VENV_DIR"
        read -p "是否重新创建? (y/n): " recreate
        if [[ "$recreate" == "y" || "$recreate" == "Y" ]]; then
            echo "删除并重新创建虚拟环境: $VENV_DIR"
            rm -rf "$VENV_DIR"
            python3 -m venv "$VENV_DIR"
        fi
    fi

    # 激活虚拟环境
    echo "激活虚拟环境..."
    source "$VENV_DIR/bin/activate"
fi

# 安装依赖包
echo "安装Python依赖包..."
pip install --upgrade pip
pip install -r requirements.txt

# 检查相机库依赖
if ! ldconfig -p | grep librealsense &> /dev/null; then
    echo "未找到Intel RealSense库，建议按照以下说明安装:"
    echo "请访问: https://github.com/IntelRealSense/librealsense/blob/master/doc/installation.md"
    echo "或运行以下命令安装（Ubuntu系统）:"
    echo "sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-key F6E65AC044F831AC80A06380C8B3A55A6F3EFCDE"
    echo "sudo add-apt-repository \"deb https://librealsense.intel.com/Debian/apt-repo $(lsb_release -cs) main\" -u"
    echo "sudo apt-get install -y librealsense2-dkms librealsense2-utils librealsense2-dev"
fi

# 创建必要的目录结构
echo "创建项目目录结构..."
mkdir -p assets/{temp/{static_videos,downloaded_videos},raw_datas/{temp,saved},gen_datasets/{gen_datas,models}}
mkdir -p logs

echo "环境设置完成！"
if [[ "$USING_CURRENT_ENV" == "false" ]]; then
    echo "请使用 'source $VENV_DIR/bin/activate' 命令激活虚拟环境" 
fi 