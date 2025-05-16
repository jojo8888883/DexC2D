from PIL import Image, ImageDraw
import os

# 确保资源目录存在
resources_dir = 'pipeline/resources'
os.makedirs(resources_dir, exist_ok=True)

# 创建一个蓝色背景的图像，中间有白色矩形
img = Image.new('RGB', (200, 100), color=(73, 109, 137))
d = ImageDraw.Draw(img)
d.rectangle([(50, 25), (150, 75)], fill=(255, 255, 255))

# 保存为所需的所有图像文件
files = [
    'login_button.png',
    'text_input.png',
    'settings_button.png',
    'upload_button.png',
    'generate_button.png',
    'download_button.png'
]

for file in files:
    img.save(f'{resources_dir}/{file}')
    print(f'已创建: {resources_dir}/{file}')

print('所有占位图像文件创建完成') 