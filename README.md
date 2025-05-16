# Sora视频生成自动化脚本

这是一个自动化Sora视频生成的Python脚本，它可以通过控制Chrome浏览器访问Sora网站，自动输入文本提示和上传图片，并生成视频。

## 前提条件

1. 安装Chrome浏览器并**已登录OpenAI账户**
2. Python 3.8+
3. 安装所需依赖包：
   ```
   pip install pyautogui opencv-python numpy pyyaml
   ```

## 配置

在运行脚本前，您可以编辑`pipeline/config.yaml`文件来自定义配置：

- `chrome_user_dir`: Chrome用户数据目录路径（可选）
  - Windows通常为`C:\Users\用户名\AppData\Local\Google\Chrome\User Data`
  - macOS通常为`~/Library/Application Support/Google/Chrome`
- `max_attempts`: 最大尝试次数
- 其他过滤和处理相关参数

## 重要说明

- **必须提前登录OpenAI账户**：脚本使用已登录的Chrome浏览器，不支持自动登录
- 脚本将尝试连接到已打开的Chrome窗口，如果没有打开会启动一个新的实例
- 生成视频过程中可能需要人工干预，如下载生成的视频

## 使用方法

### 创建示例目录结构

```
python pipeline/run_sora_automation.py --init
```

这将创建`prompt_and_image`目录，其中包含示例提示文件`prompt.txt`。您需要将名为`color_000000.png`的图像文件放在同一目录中。

### 运行自动化脚本

```
python pipeline/run_sora_automation.py --output ./output
```

脚本将：
1. 打开或连接到Chrome浏览器
2. 导航到Sora网站
3. 输入提示文本
4. 上传图像
5. 启动视频生成
6. 提示您下载生成的视频
7. 处理和筛选视频
8. 将结果保存到输出目录

### 直接指定提示和图像文件

```
python pipeline/run_sora_automation.py --prompt path/to/prompt.txt --image path/to/image.png --output ./output
```

## 故障排除

- **浏览器连接问题**：确保Chrome已安装在默认位置，如有需要，在`config.yaml`中指定`chrome_user_dir`
- **屏幕分辨率问题**：脚本使用相对位置点击屏幕元素，在高分辨率屏幕上可能需要调整坐标
- **生成超时**：如果生成视频超时，可以尝试增加`generation_time`变量的值

## 注意事项

- 该脚本仅用于研究和开发目的
- 请遵守OpenAI的使用条款和服务条件
- 不要过度使用，避免频繁请求导致账户被限制 