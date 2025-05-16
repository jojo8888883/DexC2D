#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修复提示文件编码问题
"""

import os

# 确保目录存在
prompt_dir = 'prompt_and_image'
os.makedirs(prompt_dir, exist_ok=True)

# 写入正确编码的提示文件
prompt_text = "一只手握住一个饼干盒，将其旋转180度。背景是纯白色的。摄像机保持静止。"

with open(os.path.join(prompt_dir, 'prompt.txt'), 'w', encoding='utf-8') as f:
    f.write(prompt_text)

print(f"已创建提示文件：{os.path.join(prompt_dir, 'prompt.txt')}")
print(f"提示内容：{prompt_text}")

# 检查图片文件是否存在
image_path = os.path.join(prompt_dir, 'color_000000.png')
if os.path.exists(image_path):
    print(f"图片文件已存在：{image_path}")
else:
    print(f"警告：图片文件不存在，请将图片放置在 {image_path}") 