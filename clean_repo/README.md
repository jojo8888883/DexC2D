# Sora视频自动化生成工具

这个工具能够自动与Sora平台交互，上传图片、提供文本提示，并下载生成的视频。

## 主要功能

- 自动连接到Chrome浏览器或启动新实例
- 导航到Sora平台
- 上传图片
- 输入提示文本
- 自动下载生成的视频

## 系统要求

- Windows 10/11
- Python 3.8+
- Google Chrome浏览器
- Sora账户

## 安装步骤

1. 确保已安装Python 3.8+
2. 安装所需的Python库:
   ```
   pip install playwright asyncio
   ```
3. 安装Playwright的浏览器依赖:
   ```
   python -m playwright install
   ```

## 使用方法

有两种使用方式：

### 方法1: 使用批处理文件启动Chrome (推荐)

1. 运行批处理文件启动Chrome:
   ```
   simple_chrome_starter.bat
   ```
2. 确保在Chrome中登录Sora账户
3. 运行Python脚本:
   ```
   python improved_sora_auto.py [图片路径] [提示文本文件] [输出目录]
   ```

### 方法2: 直接运行Python脚本

1. 直接运行Python脚本:
   ```
   python improved_sora_auto.py [图片路径] [提示文本文件] [输出目录]
   ```
2. 脚本会尝试连接到已运行的Chrome，如果失败会询问是否要启动新实例

## 参数说明

- `[图片路径]`: 要上传的图片文件路径 (默认: color_000000.png)
- `[提示文本文件]`: 包含提示的文本文件路径 (默认: prompt.txt)
- `[输出目录]`: 保存生成视频的目录 (默认: ./videos)

## 脚本说明

- `improved_sora_auto.py`: 主要Python脚本，处理整个自动化流程
- `simple_chrome_starter.bat`: 批处理文件，用于启动带调试端口的Chrome

## 常见问题解决

### 1. 无法连接到Chrome

确保Chrome已经使用`--remote-debugging-port=9222`选项启动。可以使用`simple_chrome_starter.bat`批处理文件来自动启动Chrome。

### 2. 登录问题

如果脚本检测到需要登录，会提示您手动在浏览器中登录并按Enter键继续。

### 3. 找不到元素

如果脚本无法找到页面上的特定元素，它会保存截图到当前目录，帮助您诊断问题。

### 4. 视频未下载

脚本使用两种方式尝试下载视频：
1. 捕获视频URL并直接下载
2. 尝试查找和点击下载按钮

如果这两种方法都失败，请查看生成的截图以了解详情。

## 改进内容

与之前的解决方案相比，这个版本：

1. 改进了与Chrome的连接方式，可以连接到已有实例或启动新实例
2. 正确处理Sora的页面导航，从/explore进入/create
3. 增强了元素定位策略，使用多种选择器
4. 提供了更详细的错误处理和截图
5. 简化了批处理文件，使其更易于使用 