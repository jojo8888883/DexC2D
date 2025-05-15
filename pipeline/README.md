# 端到端自动化流水线

该流水线用于自动化捕获图像、生成提示、生成视频、过滤视频并将视频转换为PNG序列。

## 目录结构

```
pipeline/
├── capture.py            # 相机捕获模块
├── prompt_builder.py     # 提示生成模块
├── sora_client.py        # Sora API客户端
├── rule_filter.py        # 基于规则的视频过滤
├── model_filter.py       # 基于深度学习模型的视频过滤
├── video2png.py          # 视频转PNG模块
├── utils.py              # 工具函数
├── run_pipeline.py       # 主流水线驱动
├── config.yaml           # 配置文件
└── README.md             # 说明文档
```

## 环境设置

1. 创建并激活环境：

```bash
conda create -n dexc2d python=3.8
conda activate dexc2d
```

2. 安装依赖：

```bash
pip install opencv-python ultralytics mediapipe openai torch torchvision pyyaml aiohttp aiofiles 
```

3. 设置API密钥（用于Sora视频生成）：

```bash
# Linux/macOS
export OPENAI_API_KEY=your_api_key_here

# Windows (CMD)
set OPENAI_API_KEY=your_api_key_here

# Windows (PowerShell)
$env:OPENAI_API_KEY="your_api_key_here"
```

## 使用方法

### 单次运行

使用特定对象名称运行流水线：

```bash
python run_pipeline.py --object cracker_box
```

使用自定义版本号：

```bash
python run_pipeline.py --object cracker_box --ver 01
```

使用自定义配置文件：

```bash
python run_pipeline.py --object cracker_box --config custom_config.yaml
```

### 监听模式

启动监听模式，等待相机触发：

```bash
python run_pipeline.py --watch
```

### 高级选项

设置最大重试次数：

```bash
python run_pipeline.py --object cracker_box --retry 5
```

## 配置文件

配置文件使用YAML格式，详见`config.yaml`。可以为每个阶段配置特定参数，包括：

- 相机设置
- 提示生成选项
- Sora API设置
- 规则过滤器阈值
- 模型过滤器设置
- 视频转PNG选项
- 整体流水线行为

## 自定义和扩展

### 添加物体

在`gen_dataset/meta.info`中添加物体到CAD模型的映射。

### 自定义过滤器

1. `rule_filter.py`中的过滤规则可以直接修改
2. `model_filter.py`可以接入自定义训练的物理可行性模型

### 批处理多个对象

创建一个简单的脚本，循环调用`run_pipeline.py`：

```python
import subprocess
import time

objects = ['cracker_box', 'sugar_box', 'tomato_soup_can']

for obj in objects:
    print(f"处理对象: {obj}")
    subprocess.run(['python', 'run_pipeline.py', '--object', obj])
    time.sleep(10)  # 等待一段时间再处理下一个对象
```

## 故障排除

- 检查相机是否正确连接
- 确保API密钥已设置
- 检查生成日志`pipeline.log`获取详细错误信息
- 对于失败的生成，查看对应运行目录下的`failed.log` 