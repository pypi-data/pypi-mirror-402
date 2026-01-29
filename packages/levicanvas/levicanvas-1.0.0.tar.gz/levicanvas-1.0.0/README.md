# LeviCanvas - 图片处理工具箱

[![PyPI version](https://badge.fury.io/py/levicanvas.svg)](https://badge.fury.io/py/levicanvas)
[![Python versions](https://img.shields.io/pypi/pyversions/levicanvas.svg)](https://pypi.org/project/levicanvas/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

LeviCanvas 是一个功能强大的图片处理工具箱，提供了丰富的图片处理功能，包括图片压缩、圆角处理、渐变效果、文本绘制、二维码生成等。

## 功能特性

- 🖼️ **图片处理**: 压缩、缩放、圆角化、圆形裁剪
- 🎨 **图形绘制**: 半透明区域、纯色圆角矩形、渐变图片
- ✏️ **文本处理**: 文本绘制、居中显示、多行文本处理
- 📊 **进度条**: 线性进度条、圆环进度条
- 🔲 **二维码生成**: 普通二维码、带头像二维码
- 🌐 **网络图片**: 从URL加载图片
- 🎭 **特效处理**: 高斯模糊、透明渐变

## 安装

使用 pip 安装：

```bash
pip install levicanvas
```

## 快速开始

```python
from levicanvas import LeviCanvas
from PIL import Image

# 压缩图片
LeviCanvas.compress_image("input.jpg", "output.jpg", quality=80)

# 从URL加载图片
img = LeviCanvas.load_image_from_url("https://example.com/image.jpg")

# 创建圆角图片
rounded_img = LeviCanvas.get_round_image(img, radius=20)

# 生成二维码
qr_img = LeviCanvas.generate_qr_code("https://example.com")

# 绘制文本
font = ImageFont.truetype("arial.ttf", 24)
img = LeviCanvas.Draw_Text(img, font, (10, 10), (0, 0, 0), "Hello World")
```

## 主要功能

### 图片处理

#### 压缩图片
```python
# 压缩图片到指定质量
success = LeviCanvas.compress_image("input.jpg", "output.jpg", quality=80)
```

#### 圆角处理
```python
# 普通圆角
rounded_img = LeviCanvas.get_round_image(img, radius=20)

# 自定义圆角（左上、右上、左下、右下）
rounded_img = LeviCanvas.get_round_imageEx(img, radius=20, type=(1, 1, 0, 0))

# 纯色圆角矩形
color_rect = LeviCanvas.get_solidColorRound_image(200, 100, (255, 0, 0), radius=10)
```

#### 圆形图片
```python
# 创建圆形图片
circular_img = LeviCanvas.get_circular_image(img, radius=100)
```

#### 图片缩放
```python
# 等比例缩放，自动填充空白
resized_img = LeviCanvas.zoom_img(img, width=500, height=300, alpha=True)
```

### 图形绘制

#### 半透明区域
```python
# 在图片上创建半透明区域
translucent_img = LeviCanvas.get_translucent_area(
    img, 
    area=(10, 10, 100, 100),  # (x1, y1, x2, y2)
    color=(255, 0, 0, 128),    # RGBA
    _radius=10
)
```

#### 渐变图片
```python
# 创建渐变图片
gradient_img = LeviCanvas.get_gradient_image(
    width=200,
    height=100,
    start_color=(255, 0, 0),
    end_color=(0, 0, 255),
    direction=1  # 1:左到右, 2:上到下, 3:左上到右下, 4:左下到右上
)
```

### 文本处理

#### 基本文本绘制
```python
font = ImageFont.truetype("arial.ttf", 24)
img = LeviCanvas.Draw_Text(img, font, (10, 10), (0, 0, 0), "Hello World")
```

#### 居中文本
```python
# 在指定区域内居中显示文本
img = LeviCanvas.Draw_TextMax(
    img, 
    font, 
    area=(0, 0, 200, 100),  # (x, y, width, height)
    color=(0, 0, 0),
    text="Centered Text"
)
```

#### 高级文本处理
```python
# 多行文本，自定义间距和对齐方式
img = LeviCanvas.Draw_TextMaxEX(
    img,
    font,
    area=(0, 0, 200, 100),
    clearance=5,  # 行间距
    color=(0, 0, 0),
    text="Line 1\nLine 2\nLine 3",
    mid=True  # 居中显示，False为左对齐
)
```

### 进度条

#### 线性进度条
```python
font = ImageFont.truetype("arial.ttf", 24)
img = LeviCanvas.draw_progress_bar(
    img,
    font=font,
    progress=0.75,  # 0.0-1.0
    text="75%",
    area=(50, 50, 250, 100),  # (x1, y1, x2, y2)
    auto=True  # 自动根据进度值变色
)
```

#### 圆环进度条
```python
img = LeviCanvas.draw_circle_outline(
    img,
    font=font,
    progress=0.6,  # 0.0-1.0
    text="60%",
    point=(200, 200),  # 圆心坐标
    radius=100,
    thickness=20,
    auto=True  # 自动根据进度值变色
)
```

### 二维码生成

#### 普通二维码
```python
# 基本二维码
qr_img = LeviCanvas.generate_qr_code("https://example.com")

# 自定义样式二维码
config = {
    "version": 1,
    "box_size": 10,
    "border": 2,
    "fill_color": "black",
    "back_color": "white"
}
qr_img = LeviCanvas.generate_qr_code("https://example.com", config=config)
```

#### 带头像的二维码
```python
# 生成带头像的二维码
qr_with_logo = LeviCanvas.generate_qr_code_with_logo(
    "https://example.com",
    config=config,
    logo_path="logo.png"
)
```

### 特效处理

#### 高斯模糊
```python
# 对指定区域应用高斯模糊
blurred_img = LeviCanvas.apply_gaussian_blur(
    img,
    box=(50, 50, 150, 150),  # (left, upper, right, lower)
    radius=10
)
```

#### 透明渐变
```python
# 从指定位置开始透明渐变
gradient_img = LeviCanvas.grad_transparent_rectangle(img, y_begin=100)
```

## 依赖项

- Pillow >= 9.0.0
- httpx >= 0.24.0
- qrcode >= 7.4.0

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 更新日志

### v1.0.0
- 初始版本发布
- 包含所有核心图片处理功能
- 支持圆角、渐变、文本绘制、二维码生成等功能