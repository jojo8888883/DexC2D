# Sora Web界面自动化工具

这个工具可以自动控制Sora Web界面来生成视频，并应用规则过滤来选择符合条件的视频。

## 重要前提

**在使用此工具前，您必须先在您的 Google Chrome 浏览器中登录 Sora 网站！**

1. 打开您电脑上的 Google Chrome 浏览器
2. 访问 https://sora.chatgpt.com/explore
3. 如果需要，登录您的 OpenAI 账户
4. 确认您可以正常访问和使用 Sora

此工具将使用您浏览器中已有的登录状态，而不是自动登录。

## 功能特点

- 自动使用已登录的 Chrome 浏览器会话访问 Sora Web 界面
- 根据提示文本和输入图像生成视频
- 自动设置视频参数（3:2宽高比，480p分辨率）
- 自动下载生成的视频
- 使用规则过滤器筛选符合条件的视频
  - 手部动作检测
  - 物体检测
  - 静态相机检测
- 将视频转换为帧序列
- 支持自动重试机制

## 安装依赖

在使用之前，需要安装必要的依赖项：

```bash
pip install -r requirements.txt
```

此外，由于工具使用Selenium来控制Chrome浏览器，还需要安装相应版本的ChromeDriver。可以使用webdriver-manager自动管理：

```bash
python -m webdriver_manager.chrome
```

## 配置说明

在配置文件 `config.yaml` 中，您可以指定以下选项：

```yaml
sora:
  chrome_user_dir: null        # Chrome用户数据目录路径，如果为null则使用系统默认位置
  headless: false              # 是否使用无头模式运行浏览器
```

**注意**：强烈建议保持 `headless: false`，这样您可以在需要时手动接管浏览器操作。

## 使用方法

### 初始化

首先，初始化目录结构：

```bash
python run_sora_automation.py --init
```

这个命令会创建`prompt_and_image`目录，并生成一个默认的`prompt.txt`文件。然后，将`color_000000.png`图像文件放入该目录。

### 运行自动化流程

```bash
python run_sora_automation.py [--output OUTPUT_DIR] [--retry RETRY_COUNT]
```

参数说明：
- `--output`: 指定输出目录，默认为`./output`
- `--retry`: 指定失败后的重试次数，默认为3

也可以手动指定提示文件和图像文件的路径：

```bash
python run_sora_automation.py --prompt path/to/prompt.txt --image path/to/color_000000.png
```

### 输出结果

程序成功运行后，会在输出目录中创建以下内容：

- `run_YYYYMMDD_HHMMSS/`: 运行过程中的临时文件
  - `video_1/`, `video_2/`等: 通过过滤的视频目录
    - `rgb/`: 视频帧目录
    - `video.mp4`: 原始视频
    - `filter.json`: 过滤信息
- `output_YYYYMMDD_HHMMSS/`: 最终输出目录
  - `rgb/`: 包含所有通过过滤的视频帧，格式为`frame_XXXXXX.png`
  - `success.txt`: 成功标记文件

## 故障排除

如果遇到问题，请检查以下几点：

1. 确保您已在Chrome浏览器中成功登录Sora
2. 检查ChromeDriver是否与Chrome浏览器版本匹配
3. 查看日志文件了解详细错误信息
4. 如果登录会话失效，请先在Chrome浏览器中重新登录，然后再运行脚本
5. 手动检查 https://sora.chatgpt.com/explore 页面是否可正常访问

## 自定义

如果需要调整过滤规则，可以修改`rule_filter.py`文件中的参数：

- `flow_threshold`: 光流阈值，越小要求相机越静止
- `detection_threshold`: 检测阈值
- `min_frame_ratio`: 最小帧比例，要求至少指定比例的帧满足条件

## 注意事项

- 该工具需要稳定的网络连接
- 如果脚本检测到您未登录，会提示您在打开的浏览器窗口中手动登录
- 生成视频可能需要较长时间，请耐心等待
- 不要在脚本运行时关闭自动打开的Chrome浏览器窗口 