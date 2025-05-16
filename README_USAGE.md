# Sora自动化视频生成工具使用说明

本工具可以自动访问Sora Web界面，上传提示和图片，生成四个3:2比例、480p分辨率的视频，并自动下载到本地。

## 前置条件

1. 安装必要的Python依赖包：

```bash
pip install -r pipeline/requirements.txt
```

2. 准备界面识别图片：

要使脚本正确识别和进行交互，必须创建以下图片样本文件：

- `pipeline/resources/login_button.png` - Sora登录按钮
- `pipeline/resources/text_input.png` - 文本输入框
- `pipeline/resources/settings_button.png` - 设置按钮
- `pipeline/resources/upload_button.png` - 上传按钮
- `pipeline/resources/generate_button.png` - 生成按钮
- `pipeline/resources/download_button.png` - 下载按钮

可以通过以下步骤获取这些图片：

1. 打开Sora网站：https://sora.chatgpt.com/explore
2. 使用截图工具捕捉各个界面元素
3. 将截图保存到相应位置

## 准备提示和图片

1. 将你的提示内容保存在 `prompt_and_image/prompt.txt` 文件中
2. 将你的图片文件保存为 `prompt_and_image/color_000000.png`

## 运行脚本

基本用法：

```bash
python run_sora_automation.py
```

指定输出目录和重试次数：

```bash
python run_sora_automation.py --output ./my_output --retry 3
```

手动指定提示和图片文件：

```bash
python run_sora_automation.py --prompt path/to/prompt.txt --image path/to/image.png
```

## 小贴士

1. 运行脚本时，程序可能会要求您手动登录Sora网站，请按照提示操作
2. 如果图片识别出现问题，可能需要手动操作帮助软件完成任务
3. 生成的视频文件会保存在输出目录下
4. 输出目录中的 `temp` 文件夹包含了流程中的截图，有助于调试

## 注意事项

- 请确保已经安装所有的依赖包
- 脚本使用PyAutoGUI模拟鼠标和键盘操作，运行期间不要移动鼠标或使用键盘
- 如果需要紧急停止脚本，请将鼠标移到屏幕左上角 