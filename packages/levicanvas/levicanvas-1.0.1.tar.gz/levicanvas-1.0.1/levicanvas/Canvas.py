#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
@Created on : 2025/2/14 21:18
@Author: XDTEAM
@Des: 图片工具箱
"""
import random
from io import BytesIO
import httpx
import qrcode
from PIL import ImageDraw, ImageFont, Image, ImageFilter


class LeviCanvas:

    @classmethod
    def compress_image(cls, input_path, output_path, quality=80):
        """
        压缩图片

        参数:
        input_path (str): 输入图片的文件路径
        output_path (str): 压缩后图片的保存路径
        quality (int): 压缩质量, 取值范围为0-100, 默认为80

        返回:
        bool: 压缩成功返回True, 否则返回False
        """
        try:
            image = Image.open(input_path)

            image.save(output_path, optimize=True, quality=quality)

            return True
        except Exception as e:
            print(f"压缩图片失败: {str(e)}")
            return False

    @classmethod
    def get_random_color(cls):
        """
        获取随机颜色
        :return:
        """
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        color = (r, g, b)
        return color

    @classmethod
    def load_image_from_url(cls, url) -> Image:
        """
        从url加载图片, 跳过保存本地步骤
        :param url:
        :return: Image
        """
        res = httpx.get(url)
        image_content = BytesIO(res.content)
        return Image.open(image_content)

    @classmethod
    def get_translucent_area(cls, img, area: tuple, color: tuple, _radius, type=(1, 1, 1, 1)) -> Image:
        """
        在图片上创建一个半透明图框
        :param img: 原始图片
        :param area: (x1, y1, x2, y2) 左上右下
        :param color: (r, g, b, a) RGBA颜色值
        :param _radius: 圆角半径
        :param type: (tl, tr, bl, br) 表示左上, 右上, 左下, 右下圆角半径的倍数
        :return: Image
        """
        # 创建新的透明图片作为蒙版
        mask = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(mask)

        # 解构区域坐标
        x1, y1, x2, y2 = area

        # 绘制圆角矩形所需的圆弧
        draw.pieslice((x1, y1, x1 + type[0] * _radius * 2, y1 + type[0] * _radius * 2), 180, 270, fill=color)  # 左上角圆弧
        draw.pieslice((x2 - type[1] * _radius * 2, y1, x2, y1 + type[1] * _radius * 2), 270, 360, fill=color)  # 右上角圆弧
        draw.pieslice((x1, y2 - type[2] * 2 * _radius, x1 + type[2] * 2 * _radius, y2), 90, 180, fill=color)  # 左下角圆弧
        draw.pieslice((x2 - type[3] * 2 * _radius, y2 - type[3] * 2 * _radius, x2, y2), 0, 90, fill=color)  # 右下角圆弧

        # 绘制矩形部分, 确保圆角部分不被覆盖
        draw.rectangle((x1 + _radius, y1, x2 - _radius, y2), fill=color)
        draw.rectangle((x1, y1 + type[0] * _radius, x1 + _radius, y2 - type[2] * _radius), fill=color)
        draw.rectangle((x1 + type[0] * _radius, y1, x2 - type[1] * _radius, y1 + _radius), fill=color)
        draw.rectangle((x1 + type[2] * _radius, y2 - _radius, x2 - type[3] * _radius, y2), fill=color)
        draw.rectangle((x2 - _radius, y1 + type[1] * _radius, x2, y2 - type[3] * _radius), fill=color)

        # 将蒙版应用到原始图片上
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        result = Image.alpha_composite(img, mask)

        return result

    @classmethod
    def get_circular_image(cls, img, radius) -> Image:
        """
        返回圆型图片, 传入图片img, 半径, 配合Image.open使用
        :param img:
        :param radius:
        :return: Image
        """
        avatar = img
        avatar = avatar.resize((1000, 1000))
        avatar = avatar.convert("RGBA")
        circle = Image.new('L', avatar.size, 0)  # 创建一个黑色正方形画布
        draw = ImageDraw.Draw(circle)
        draw.ellipse(
            (0, 0, avatar.size[0], avatar.size[1]), fill=255)  # 画一个白色圆形
        avatar.putalpha(circle)  # 白色区域透明可见, 黑色区域不可见
        avatar = avatar.resize((radius, radius))
        return avatar

    @classmethod
    def get_round_image(cls, img, _radius) -> Image:
        """
        返回图片圆角化, 传入图片img, 半径, 配合Image.open使用
        :param img:
        :param _radius:
        :return:img
        """
        _img = img.convert('RGBA')
        w, h = _img.size
        _img = _img.resize((w * 10, h * 10))

        radius = _radius * 10
        circle = Image.new('L', (radius * 2, radius * 2), 0)  # 创建黑色方形

        draw = ImageDraw.Draw(circle)
        draw.ellipse((0, 0, radius * 2, radius * 2),
                     fill=255)  # 黑色方形内切白色圆形,ellipse绘制椭圆
        alpha = Image.new('L', (w * 10, h * 10), 255)
        alpha.paste(circle.crop((0, 0, radius, radius)), (0, 0))  # 左上角
        alpha.paste(circle.crop((radius, 0, radius * 2, radius)),
                    (w * 10 - radius, 0))  # 右上角
        alpha.paste(circle.crop((radius, radius, radius * 2, radius * 2)),
                    (w * 10 - radius, h * 10 - radius))  # 右下角
        alpha.paste(circle.crop((0, radius, radius, radius * 2)),
                    (0, h * 10 - radius))  # 左下角

        _img.putalpha(alpha)  # 白色区域透明可见, 黑色区域不可见
        _img = _img.resize((w, h))
        return _img

    @classmethod
    def get_round_imageEx(cls, img, _radius, type=(1, 1, 1, 1)) -> Image:
        """
        返回图片圆角化, 传入图片img, 半径, ,类型（左上, 右上, 左下, 右下）配合Image.open使用
        :param img:
        :param _radius:
        :param type: 类型（左上, 右上, 左下, 右下）
        :return: Image
        """
        _img = img.convert('RGBA')
        w, h = _img.size
        _img = _img.resize((w * 10, h * 10))

        radius = _radius * 10
        circle = Image.new('L', (radius * 2, radius * 2), 0)  # 创建黑色方形

        draw = ImageDraw.Draw(circle)
        draw.ellipse((0, 0, radius * 2, radius * 2),
                     fill=255)  # 黑色方形内切白色圆形,ellipse绘制椭圆
        alpha = Image.new('L', (w * 10, h * 10), 255)
        if type[0] == 1:
            alpha.paste(circle.crop((0, 0, radius, radius)), (0, 0))  # 左上角
        if type[1] == 1:
            alpha.paste(circle.crop((radius, 0, radius * 2, radius)),
                        (w * 10 - radius, 0))  # 右上角
        if type[3] == 1:
            alpha.paste(circle.crop((radius, radius, radius * 2, radius * 2)),
                        (w * 10 - radius, h * 10 - radius))  # 右下角
        if type[2] == 1:
            alpha.paste(circle.crop((0, radius, radius, radius * 2)),
                        (0, h * 10 - radius))  # 左下角

        _img.putalpha(alpha)  # 白色区域透明可见, 黑色区域不可见
        _img = _img.resize((w, h))
        return _img

    @classmethod
    def get_solidColorRound_image(cls, width, height, color, radius) -> Image:
        """
        返回纯色图片圆角化, 传入图片高度, 宽度, 颜色, 半径,类型（左上, 右上, 左下, 右下）
        :param width:
        :param height:
        :param color:
        :param radius:
        :return: Image
        """
        _color = color
        table = 3  # 越大处理速度越慢
        width = width * table
        height = height * table
        img = Image.new('RGBA', (width, height), _color)

        w, h = img.size
        size = (int(w / table), int(h / table))
        radius = radius * table

        circle = Image.new('L', (radius * 2, radius * 2), 0)  # 创建黑色方形
        draw = ImageDraw.Draw(circle)
        draw.ellipse((0, 0, radius * 2, radius * 2),
                     fill=255)  # 黑色方形内切白色圆形,ellipse绘制椭圆

        alpha = Image.new('L', img.size, 255)
        alpha.paste(circle.crop((0, 0, radius, radius)), (0, 0))  # 左上角
        alpha.paste(circle.crop((radius, 0, radius * 2, radius)),
                    (w - radius, 0))  # 右上角
        alpha.paste(circle.crop((radius, radius, radius * 2,
                                 radius * 2)), (w - radius, h - radius))  # 右下角
        alpha.paste(circle.crop((0, radius, radius, radius * 2)),
                    (0, h - radius))  # 左下角
        img.putalpha(alpha)  # 白色区域透明可见, 黑色区域不可见
        img = img.resize(size)

        return img

    @classmethod
    def get_solidColorRound_imageEx(cls, width: int, height: int, color, radius: int, type=(1, 1, 1, 1)) -> Image:
        """
        返回纯色图片圆角化
        :param width: 宽度
        :param height: 高度
        :param color: 颜色
        :param radius: 半径
        :param type: 类型（左上, 右上, 左下, 右下）
        :return: Image
        """
        _color = color
        table = 3  # 越大处理速度越慢
        width = width * table
        height = height * table
        img = Image.new('RGBA', (width, height), _color)

        w, h = img.size
        size = (int(w / table), int(h / table))
        radius = radius * table

        circle = Image.new('L', (radius * 2, radius * 2), 0)  # 创建黑色方形
        draw = ImageDraw.Draw(circle)
        draw.ellipse((0, 0, radius * 2, radius * 2),
                     fill=255)  # 黑色方形内切白色圆形,ellipse绘制椭圆

        alpha = Image.new('L', img.size, 255)
        if type[0] == 1:
            alpha.paste(circle.crop((0, 0, radius, radius)), (0, 0))  # 左上角
        if type[1] == 1:
            alpha.paste(circle.crop((radius, 0, radius * 2, radius)),
                        (w - radius, 0))  # 右上角
        if type[3] == 1:
            alpha.paste(circle.crop((radius, radius, radius * 2,
                                     radius * 2)), (w - radius, h - radius))  # 右下角
        if type[2] == 1:
            alpha.paste(circle.crop((0, radius, radius, radius * 2)),
                        (0, h - radius))  # 左下角
        img.putalpha(alpha)  # 白色区域透明可见, 黑色区域不可见
        img = img.resize(size)

        return img

    @classmethod
    def get_filledSolidColorRectangle_image(cls, img, x, y, w, h, color) -> Image:
        """
        填充颜色矩形, 传入img,起点x, 起点y, 宽度w, 高度h, 颜色
        :param img:
        :param x:
        :param y:
        :param w:
        :param h:
        :param color:
        :return: Image
        """
        _img = img
        draw = ImageDraw.Draw(_img)
        area = [(x, y), (x + w, y), (x, y + h), (x + w, y + h)]
        draw.polygon(area, fill=color)
        return _img

    @classmethod
    def get_filledSolidColorRectangle_imageEx(cls, img, area, color):
        """
        填充颜色矩形, 传入img, 颜色
        :param img:
        :param area:
        :param color:
        :return: Image
        """
        _img = img
        draw = ImageDraw.Draw(_img)
        draw.rectangle(area, fill=color)
        return _img

    @classmethod
    def zoom_img(cls, img: Image, width: int, height: int, alpha=True, fill_color=None) -> Image:
        """
        缩放图片, 等比例缩放, 自动填充空白
        :param img:
        :param width:
        :param height:
        :param alpha: 是否自动填充空白, 为False则填充白色
        :param fill_color: 非透明填充时的颜色, 默认为白色
        :return: 处理后的图像
        """
        # 计算图片的宽高比
        proportion = img.size[0] / img.size[1]

        # 如果图片的宽高都小于设置的宽高,  则放大图片
        if img.size[0] < width and img.size[1] < height:
            img = img.resize((img.size[0] * 10, img.size[1] * 10))

        # 计算图片的新宽高
        if width <= img.size[0]:
            pic_width = width
            pic_height = int(width / proportion)
        else:
            pic_height = height
            pic_width = int(pic_height * proportion)

        # 缩放图片
        img = img.resize((pic_width, pic_height))

        # 计算图片的偏移量
        if pic_height <= height:
            yy = int((height - pic_height) / 2)
            xx = int((width - pic_width) / 2) if pic_width < width else 0
        else:
            yy = 0
            xx = int((pic_width - width) / 2) if pic_width > width else 0

        # 创建新图片
        if alpha:
            # base_img = Image.new('L', (width, height), 0)
            face_img = Image.new('RGBA', (width, height), 255)
        else:
            # base_img = Image.new('RGBA', (width, height), (236, 244, 248))
            face_img = Image.new('RGBA', (width, height), (255, 255, 255))

        # 将图片粘贴到新图片上
        face_img.paste(img, (xx, yy))

        return face_img

    @classmethod
    def Draw_Text(cls, img, font, area, color, text) -> Image:
        """
        画文本, 传入img, 字体, 区域（10, 10）, 文本
        :param img:
        :param font:
        :param area:
        :param color:
        :param text:
        :return: Image
        """
        draw = ImageDraw.Draw(img)  # 修改图片
        _font = font
        draw.text(area, text, color, _font)  # 文字位置, 内容, 字体
        return img

    @classmethod
    def Draw_TextMax(cls, img, font, area, color, text) -> Image:
        """
        画文本, 居中显示
        :param img:
        :param font: ImageFont.truetype(FONTS_ROUTE + "/simhei.ttf", size=80)
        :param area: （起点x,起点y, 宽, 高）
        :param color:
        :param text:
        :return:
        """

        draw = ImageDraw.Draw(img)  # 修改图片

        _font = font
        _text_list = text.split('\n')
        x = area[2]
        y = area[3]
        _color = color
        for i in range(0, len(_text_list)):
            if color == 'random':
                _color = cls.get_random_color()
            font_size = _font.getbbox(_text_list[i])

            xx = font_size[2]
            yy = font_size[3]
            # 文字水平居中
            offset_x = (x - xx) / 2 + area[0]
            # 文字垂直居中
            offset_y = (y - yy) / 2 + area[1]

            draw.text((offset_x, offset_y + i * yy),
                      _text_list[i], _color, _font)  # 文字位置, 内容, 字体
        return img

    @classmethod
    def Draw_TextMaxEX(cls, img, font, area, clearance, color, text, mid=True) -> Image:
        """
        画文本, 居中显示
        :param img:
        :param font: 字体（ImageFont.truetype(FONTS_ROUTE + "/simhei.ttf", size=80)）
        :param area: （起点x,起点y, 宽, 高）
        :param clearance: 两行之间的间隙
        :param color:
        :param text: 文本
        :param mid: 是否居中, 为Flase 是居左
        :return:
        """

        draw = ImageDraw.Draw(img)  # 修改图片
        _font = font
        offset_y_1 = 0
        _text_list = text.split('\n')
        if clearance == 0:
            clearance = 3
        x = area[2]  # 图片宽度
        y = area[3]  # 图片高度
        numy = len(_text_list)
        numyy = _font.getbbox(_text_list[0])[3]
        _color = color
        for i in range(0, len(_text_list)):
            font_size = _font.getbbox(_text_list[i])
            xx = font_size[2]
            yy = numyy  # 字体高度
            if color == 'random':
                _color = cls.get_random_color()
            # 文字水平居中
            offset_x = (x - xx) / 2 + area[0]
            # 文字垂直居中
            if i == 0:
                offset_y = (y - numy * yy - (numy - 1)
                            * clearance) / 2 + area[1]
                offset_y_1 = offset_y
            else:
                offset_y = offset_y_1 + i * (yy + clearance - 1)
            if mid:

                draw.text((offset_x, offset_y),
                          _text_list[i], _color, _font)  # 文字位置, 内容, 字体
            else:
                draw.text((area[0], offset_y), _text_list[i],
                          _color, _font)  # 文字位置, 内容, 字体
        return img

    @classmethod
    def Draw_TextMaxEX_left_right(cls, img, font, area, clearance, distance, color, text, left_right=True) -> Image:
        """
        画文本, 左右显示
        :param img:
        :param font: 字体
        :param area: 制（起点x, 起点y, 宽, 高）
        :param clearance: 两行之间的间隙
        :param distance: 左右距离
        :param color:
        :param text:
        :param left_right:
        :return:
        """
        draw = ImageDraw.Draw(img)  # 修改图片
        _font = font
        _text_list = text.split('\n')
        if clearance == 0:
            clearance = 3
        x = area[2]  # 图片宽度
        y = area[3]  # 图片高度
        numy = len(_text_list)
        numyy = _font.getbbox(_text_list[0])[3]
        _color = color
        for i in range(0, len(_text_list)):
            if color == 'random':
                _color = cls.get_random_color()
            font_size = _font.getbbox(_text_list[i])
            xx = font_size[2]
            yy = numyy  # 字体高度
            # 文字水平右对齐
            offset_x1 = area[0] + x - distance - xx
            # 文字水平左对齐
            offset_x2 = area[0] + distance
            offset_y_1 = 0
            # 文字垂直居中
            if i == 0:
                offset_y = (y - numy * yy - (numy - 1)
                            * clearance) / 2 + area[1]
                offset_y_1 = offset_y
            else:
                offset_y = offset_y_1 + i * (yy + clearance - 1)

            if left_right:
                draw.text((offset_x2, offset_y),
                          _text_list[i], _color, _font)  # 文字位置, 内容, 字体
            else:
                draw.text((offset_x1, offset_y),
                          _text_list[i], _color, _font)  # 文字位置, 内容, 字体
        return img

    @classmethod
    def get_FontHeight(cls, font, text):
        """
        取字体高度
        :param font:
        :param text:
        :return:
        """
        return font.getbbox(text)[3]

    @classmethod
    def get_FontWidth(cls, font, text):
        """
        取字体宽度
        :param font:
        :param text:
        :return:
        """
        return font.getbbox(text)[2]

    @classmethod
    def grad_transparent_rectangle(cls, ori_img, y_begin) -> Image:
        """
        图片透明渐变处理, 传入img
        :param ori_img:
        :param y_begin:
        :return:
        """
        # 只有RGBA通道才有alpha值
        ori_img = ori_img.convert("RGBA")
        w, h = ori_img.size
        # mode L 灰度图片, 作为蒙版
        # 在alpha值中, 白色表示透明（255）, 黑色表示不透明（0）
        img = Image.new('L', ori_img.size, 255)
        y_end = h
        # 在坐标(y_begin, y_end)中设置渐变蒙版
        # range左闭右开, 所以下面的坐标+1
        for y in range(y_begin, y_end + 1):
            alpha = 255 - int((y - y_begin) / (y_end - y_begin) * 255)

            tmp_img = Image.new('L', (w, 1), alpha)
            img.paste(tmp_img, (0, y))
        ori_img.putalpha(img)
        return ori_img

    @classmethod
    def get_gradient_image(cls, width, height, start_color, end_color, direction) -> Image:
        """
        创建渐变色图片

        :param width: 图片宽度
        :param height: 图片高度
        :param start_color: 起始颜色 (R, G, B)
        :param end_color: 结束颜色 (R, G, B)
        :param direction: 渐变方向 {
                            1:"left_to_right",
                            2:"top_to_bottom",
                            3:"top_left_to_bottom_right",
                            4:"bottom_left_to_top_right",
                              }
        :return: Image
        """
        _direction = {
            1: "left_to_right",
            2: "top_to_bottom",
            3: "top_left_to_bottom_right",
            4: "bottom_left_to_top_right",
        }
        image = Image.new("RGB", (width, height))
        _direction = _direction.get(direction, "left_to_right")
        for y in range(height):
            for x in range(width):
                if _direction == 'top_to_bottom':
                    factor = y / height
                elif _direction == 'left_to_right':
                    factor = x / width
                elif _direction == 'top_left_to_bottom_right':
                    factor = (x + y) / (width + height - 2)
                else:
                    factor = (width + height - 2 - (x + y)) / (width + height - 2)

                r = int(start_color[0] + (end_color[0] - start_color[0]) * factor)
                g = int(start_color[1] + (end_color[1] - start_color[1]) * factor)
                b = int(start_color[2] + (end_color[2] - start_color[2]) * factor)

                image.putpixel((x, y), (r, g, b))

        return image

    @classmethod
    def get_gradient_color(cls):
        """
        获取随机颜色数组
        :return:
        """
        type = random.randint(1, 8)
        if type == 1:
            color_list = [(218, 112, 214), (138, 43, 226)]  # 粉紫
        elif type == 2:
            color_list = [(103, 221, 247), (70, 83, 199)]  # 青蓝
        elif type == 3:
            color_list = [(214, 191, 145), (238, 154, 131)]  # 黄粉
        elif type == 4:
            color_list = [(197, 155, 249), (249, 176, 188)]  # 紫粉
        elif type == 5:
            color_list = [(180, 241, 250), (246, 245, 205)]  # 青黄
        elif type == 6:
            color_list = [(251, 201, 226), (158, 236, 253)]  # 蓝粉
        elif type == 7:
            color_list = [(189, 255, 158), (194, 236, 255)]  # 青绿
        else:
            color_list = [(179, 162, 253), (237, 252, 196)]  # 青黄

        return color_list

    @classmethod
    def draw_progress_bar(cls, img, font, progress: int | float, text: str, area: tuple, color: tuple = (85, 175, 123),
                          auto=True, font_color=(34, 34, 34)):
        """
        绘制进度条
        :param font_color:
        :param img: img
        :param font: ImageFont.truetype(FONTS_ROUTE + "/simhei.ttf", size=80)
        :param progress: n/100
        :param text: 进度条中间文字
        :param area: (100,100,200,200) 左上角右下角
        :param color: 默认底色, 当auto是True时失效
        :param auto: 是否自动变色
        :return:
        """
        number = round(progress, 1)
        width_x = area[2] - area[0]
        width = int((area[2] - area[0]) * number)
        # 问题点
        if width <= 0:
            width = 1
        height = area[3] - area[1]

        img = LeviCanvas.get_translucent_area(img, area, (231, 229, 226, 120), 8)
        main_color = color
        if auto:
            if 0 <= number <= 0.5:
                main_color = (85, 175, 123, 210)
            elif 0.5 < number <= 0.9:
                main_color = (250, 157, 88, 210)
            else:
                main_color = (232, 69, 56, 210)
        model_img = LeviCanvas.get_solidColorRound_imageEx(width, height, main_color, 8)
        img.paste(model_img, (area[0], area[1]), model_img)
        font.size = int(height / 1.5)
        font = ImageFont.truetype(font)
        img = LeviCanvas.Draw_TextMax(img, font, (area[0], area[1] - 2, width_x, height), font_color, text)
        return img

    @classmethod
    def draw_circle_outline(cls, img, font, progress: int | float, text: str, point: tuple, radius: int = 250,
                            thickness: int = 50,
                            color: tuple = (85, 175, 123), auto=True, font_color=(34, 34, 34)):
        """
        绘制圆环进度条
        :param font_color:
        :param img:
        :param font: ImageFont.truetype(FONTS_ROUTE + "/simhei.ttf", size=80)
        :param progress: n/100
        :param text:
        :param point: 圆心坐标（x, y）
        :param radius:
        :param thickness:
        :param color: 默认底色, 当auto是True时失效
        :param auto: 是否自动变色
        :return:
        """
        # 打开指定的图片
        img = img.convert('RGBA')
        mask = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(mask)
        radius = radius - thickness
        cx, cy = point[0], point[1]
        # cx, cy 是圆心位置
        x0, y0 = cx - radius, cy - radius
        x1, y1 = cx + radius, cy + radius
        draw.arc((x0 - thickness, y0 - thickness, x1 + thickness, y1 + thickness), 0, 360, fill=(204, 204, 204, 120),
                 width=thickness)

        angle = int(progress * 360)

        number = progress
        start_angle = 270
        end_angle = 270 + angle

        if auto:
            if 0 < number <= 0.5:
                color = (85, 175, 123, 210)
            elif 0.5 < number <= 0.9:
                color = (250, 157, 88, 210)
            else:
                color = (232, 69, 56, 210)
        draw.arc((x0 - thickness, y0 - thickness, x1 + thickness, y1 + thickness), start_angle,
                 end_angle, fill=color, width=thickness)

        masked_img = Image.alpha_composite(img, mask)
        # 绘制文本
        font.size = int(radius * 2 * 0.24)
        font = ImageFont.truetype(font, size=font)

        masked_img = LeviCanvas.Draw_TextMax(masked_img, font, (x0, y0, 2 * radius, 2 * radius), font_color, text)
        return masked_img

    @staticmethod
    def generate_qr_code(url, config=None) -> Image:
        """
        生成普通二维码。

        :param url: 要编码的网址路径。
        :param config: 二维码相关配置, JSON 格式。支持以下键：
            - version: 二维码版本号（1-40, 默认为 1）。
            - box_size: 每个格子的像素大小（默认为 10）。
            - border: 边框宽度（默认为 2）。
            - fill_color: 二维码颜色（默认为 "black"）。
            - back_color: 背景颜色（默认为 "white"）。
        :return: 生成的二维码图像对象。
        """
        if config is None:
            config = {}

        # 默认配置
        default_config = {
            "version": 1,
            "box_size": 10,
            "border": 2,
            "fill_color": "black",
            "back_color": "white"
        }

        # 合并默认配置和用户配置
        config = {**default_config, **config}

        qr = qrcode.QRCode(
            version=config["version"],
            box_size=config["box_size"],
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            border=config["border"]
        )
        qr.add_data(url)
        qr.make(fit=True)

        # 将颜色字符串转换为 RGB 元组
        fill_color = config["fill_color"]
        back_color = config["back_color"]
        if isinstance(fill_color, str):
            fill_color = fill_color.lower()
        if isinstance(back_color, str):
            back_color = back_color.lower()

        img = qr.make_image(
            fill_color=fill_color,
            back_color=back_color
        )
        return img

    @staticmethod
    def generate_qr_code_with_logo(url, config=None, logo_path=None) -> Image:
        """
        生成带头像的二维码。

        :param url: 要编码的网址路径。
        :param config: 二维码相关配置, JSON 格式。
        :param logo_path: 头像图片路径。
        :return: 生成的二维码图像对象。
        """
        # 生成基础二维码
        img = LeviCanvas.generate_qr_code(url, config)

        if logo_path:
            logo = Image.open(logo_path)
            w, h = img.size
            logo_size = int(min(w, h) * 0.25)  # 头像大小为二维码的 25%
            logo = logo.resize((logo_size, logo_size))
            pos = ((w - logo_size) // 2, (h - logo_size) // 2)  # 头像居中
            img.paste(logo, pos, logo)

        return img

    @staticmethod
    def apply_gaussian_blur(img: Image, box: tuple, radius: int = 60) -> Image:
        """
        对图片的某个区域应用指定程度的高斯模糊。

        :param img: 原始图片img
        :param box: 需要应用高斯模糊的区域, 格式为(left, upper, right, lower)
        :param radius: 高斯模糊的半径, 决定模糊程度
        :return: Image
        """
        # 打开原始图片
        crop_box = box
        region_to_blur = img.crop(crop_box)

        # 对该区域应用指定程度的高斯模糊
        blurred_region = region_to_blur.filter(ImageFilter.GaussianBlur(radius=radius))

        # 将模糊后的区域粘贴回原图
        img.paste(blurred_region, crop_box)
        return img
