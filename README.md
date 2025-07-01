# DexC2D

DexC2D是一个用于生成和处理3D物体图像数据集的工具。它通过捕获物体图像、生成视频、选择静态视频，并将视频处理为数据集的方式，实现了一个完整的数据集生成流水线。

## 项目架构

```
dexc2d/
│
├── assets/                    # 存储各类资源
│   ├── temp/                  # 临时文件
│   │   ├── static_videos/     # 静态视频
│   │   └── downloaded_videos/ # 下载的视频
│   │
│   ├── raw_datas/             # 原始数据
│   │   ├── temp/              # 临时拍摄
│   │   └── saved/             # 已保存拍摄
│   │
│   └── gen_datasets/          # 生成的数据集
│       ├── gen_datas/         # 生成的数据
│       ├── models/            # 模型文件
│       └── meta.info          # 元数据信息
│
├── pipeline/                  # 核心处理流水线
│   ├── config/                # 配置模块
│   │   ├── input_module_variant.py
│   │   ├── capture_module_variant.py
│   │   ├── generation_module_variant.py
│   │   ├── selection_module_variant.py
│   │   └── arrange_module_variant.py
│   │
│   ├── device_module/         # 设备模块
│   │   └── camera/            # 相机设备
│   │       └── d435i.py       # D435i相机操作
│   │
│   ├── logger_module/         # 日志模块
│   │   └── logger.py          # 日志记录器
│   │
│   ├── preprocess_module/     # 预处理模块
│   │   ├── input_module/      # 输入模块
│   │   ├── capture_module/    # 捕获模块
│   │   │   └── capture_temp.py# 临时捕获
│   │   │
│   │   ├── generation_module/ # 生成模块
│   │   │   └── sora_web_automation/ # Sora网页自动化
│   │   │       ├── sora_web_automation.py
│   │   │       ├── auto_clicker.py
│   │   │       └── complete.png
│   │   │
│   │   ├── selection_module/  # 选择模块
│   │   │   └── selector.py    # 视频选择器
│   │   │
│   │   └── arrange_module/    # 排列模块
│   │       └── mp4_to_data.py # MP4转数据集
│   │
│   └── utils/                 # 工具模块
│       └── common.py          # 通用工具函数
│
├── tools/                     # 工具脚本
│   ├── env_setup.sh           # 环境设置脚本
│   ├── run_main.sh            # 运行主程序
│   └── run_unittest.sh        # 运行单元测试
│
├── logs/                      # 日志目录
├── main.py                    # 主程序
└── requirements.txt           # 依赖包列表
```

## 功能模块说明

1. **捕获模块（Capture Module）**
   - 使用Intel RealSense D435i相机捕获物体的RGB-D图像
   - 支持临时捕获和永久保存捕获结果

2. **生成模块（Generation Module）**
   - 基于Sora API自动生成物体视频
   - 使用网页自动化技术操作Sora网站

3. **选择模块（Selection Module）**
   - 分析视频，筛选出固定镜头的视频
   - 通过光流分析技术识别相机运动

4. **排列模块（Arrange Module）**
   - 将筛选后的视频转换为数据集格式
   - 包含RGB图像、深度图像和相机参数

## 安装与设置

1. 克隆仓库
   ```bash
   git clone <repository-url>
   cd dexc2d
   ```

2. 设置环境
   ```bash
   chmod +x tools/env_setup.sh
   ./tools/env_setup.sh
   ```

3. 确认相机设置
   - 确保Intel RealSense D435i相机已连接
   - 按照提示安装必要的驱动程序

## 使用方法

1. 运行完整流水线
   ```bash
   ./tools/run_main.sh
   ```

2. 运行单元测试
   ```bash
   ./tools/run_unittest.sh
   ```

## 配置说明

主要配置文件位于`pipeline/config/`目录下，包含各个模块的配置参数：

- `input_module_variant.py`: 输入模块配置
- `capture_module_variant.py`: 捕获模块配置
- `generation_module_variant.py`: 生成模块配置
- `selection_module_variant.py`: 选择模块配置
- `arrange_module_variant.py`: 排列模块配置

## 系统要求

- Ubuntu 20.04或更高版本
- Python 3.8或更高版本
- Intel RealSense D435i相机及驱动
- Firefox浏览器 (用于网页自动化)

## 注意事项

- 网页自动化需要正确的屏幕分辨率和浏览器缩放设置
- 运行前请确认prompt.txt文件已正确配置 