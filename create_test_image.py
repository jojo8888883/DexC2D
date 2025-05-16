import cv2
import numpy as np
import os

# 创建prompt_and_image目录
os.makedirs("prompt_and_image", exist_ok=True)

# 创建一个480x720的白色背景图像（3:2宽高比）
img = np.ones((480, 720, 3), dtype=np.uint8) * 255

# 在中心位置画一个黑色矩形代表饼干盒
box_width = 200
box_height = 300
x = (720 - box_width) // 2
y = (480 - box_height) // 2
cv2.rectangle(img, (x, y), (x + box_width, y + box_height), (0, 0, 0), 2)

# 保存图像
cv2.imwrite("prompt_and_image/color_000000.png", img)
print("已创建测试图像：prompt_and_image/color_000000.png") 