import math
from PIL import Image, ImageDraw, ImageFont
import random
import string
import colorsys
import io
import base64
from io import BytesIO


class VerifyCode:

    def __init__(self):
        self.length = 4
        self.font_size = 18
        self.padding = 2
        self.chaos = True
        self.chaos_color = (192, 192, 192)  # LightGray
        self.background_color = (255, 255, 255)  # White
        self.colors = [(0, 0, 0), (255, 0, 0), (0, 0, 139), (0, 128, 0), (255, 140, 0), (165, 42, 42), (0, 139, 139), (128, 0, 128)]
        self.fonts = ["arial.ttf", "georgia.ttf"]
        self.code_serial = string.ascii_letters + string.digits

    def twist_image(self, src_img, b_x_dir, d_mult_value, d_phase):
        width, height = src_img.size
        dest_img = Image.new('RGB', (width, height), self.background_color)
        d_base_axis_len = height if b_x_dir else width

        for i in range(width):
            for j in range(height):
                dx = (3.1415926535897932384626433832795 * 2 * j) / d_base_axis_len if b_x_dir else (3.1415926535897932384626433832795 * 2 * i) / d_base_axis_len
                dx += d_phase
                dy = math.sin(dx)

                n_old_x = i + int(dy * d_mult_value) if b_x_dir else i
                n_old_y = j if b_x_dir else j + int(dy * d_mult_value)

                color = src_img.getpixel((i, j))
                if 0 <= n_old_x < width and 0 <= n_old_y < height:
                    dest_img.putpixel((n_old_x, n_old_y), color)

        return dest_img

    def create_image_code(self, code):
        f_size = self.font_size
        f_width = f_size + self.padding

        image_width = int(len(code) * f_width) + 4 + self.padding * 2
        image_height = f_size * 2 + self.padding

        image = Image.new('RGB', (image_width, image_height), self.background_color)
        draw = ImageDraw.Draw(image)

        if self.chaos:
            for _ in range(self.length * 10):
                x = random.randint(0, image_width - 1)
                y = random.randint(0, image_height - 1)
                draw.point((x, y), fill=self.chaos_color)

        top1 = (image_height - f_size - self.padding * 2) // 4
        top2 = top1 * 2

        for i, char in enumerate(code):
            c_index = random.randint(0, len(self.colors) - 1)
            f_index = random.randint(0, len(self.fonts) - 1)

            try:
                font = ImageFont.truetype(self.fonts[f_index], f_size)
            except IOError:
                font = ImageFont.load_default()

            top = top2 if i % 2 == 1 else top1
            left = i * f_width

            draw.text((left, top), char, font=font, fill=self.colors[c_index])

        draw.rectangle([0, 0, image_width - 1, image_height - 1], outline=(190, 190, 190))

        image = self.twist_image(image, True, 3, 1)
        return image

    def create_verify_code(self, code_len=0):
        if code_len == 0:
            code_len = self.length

        code = ''.join(random.choice(self.code_serial) for _ in range(code_len))
        return code


def getVerifyCode(length: int, codeSerial: str):
    from fastapi.responses import StreamingResponse
    verify_code_instance = VerifyCode()
    code = verify_code_instance.create_verify_code()
    image = verify_code_instance.create_image_code(code)

    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()

    response = StreamingResponse(io.BytesIO(img_byte_arr), media_type="image/jpeg")
    response.set_cookie(key="VerifyCode", value=code.upper())
    return response


def makeThumbnail(image_path, output_path, max_width, max_height):
    '''
    生成缩略图
    '''
    # 读取原始图片
    from PIL import Image, ImageChops
    img = Image.open(image_path)

    # 计算缩略图的宽度和高度，保持原始图片的比例
    ratio = min(max_width / img.width, max_height / img.height)
    width = int(img.width * ratio)
    height = int(img.height * ratio)

    # 生成缩略图，并保存到文件
    img.thumbnail((width, height), Image.ANTIALIAS)
    img.save(output_path)


def colorOverlay(img, rgba):
    """
    给图像添加颜色叠加层。

    参数:
        img (PIL.Image.Image): 原始图像。
        rgba (tuple): 包含颜色信息的元组，形如 (R, G, B, A)。

    返回:
        PIL.Image.Image: 添加颜色叠加层后的图像。
    """

    # 创建一个与原始图像大小相同的图像，填充指定颜色
    from PIL import Image, ImageChops
    overlay = Image.new("RGBA", img.size, rgba)

    result_image = Image.composite(overlay, Image.new("RGBA", img.size), img.convert("RGBA"))
    return result_image


def setAlpha(img, alpha):
    """
    设置图像的透明度。

    参数:
        img (PIL.Image.Image): 要设置透明度的图像。
        alpha (float): 透明度值，取值范围在 0 到 1 之间。

    返回:
        None: 该函数直接修改传入的图像对象，不返回新的图像。
    """

    alpha1 = img.getchannel("A")
    alpha1 = alpha1.point(lambda x: x * alpha)
    img.putalpha(alpha1)


def removeDarkWithTransparent(input_image_path, output_image_path):
    from PIL import Image
    import colorsys
    # 定义饱和度和明度接近黑色的阈值，可根据实际情况调整
    saturation_threshold = 0.8
    value_threshold = 0.8

    # 打开图片
    image = Image.open(input_image_path)

    # 将图片转换为RGBA模式，以便处理透明度
    image = image.convert("RGBA")

    # 获取图片的像素数据
    data = image.getdata()

    new_data = []
    for item in data:
        # 将RGB颜色转换为HSV颜色空间
        # 色调（Hue）、饱和度（Saturation）和明度（Value）
        hsv = colorsys.rgb_to_hsv(item[0] / 255, item[1] / 255, item[2] / 255)

        # 判断是否接近黑色（饱和度和明度都小于阈值）
        if hsv[1] < saturation_threshold and hsv[2] < value_threshold:
            # 根据接近程度设置透明度，这里简单地用固定值设置，你也可以根据更复杂的逻辑来设置
            alpha = 0
            new_data.append((item[0], item[1], item[2], alpha))
        else:
            new_data.append(item)

    # 更新图片的像素数据
    image.putdata(new_data)

    # 保存为PNG格式，PNG支持透明度
    image.save(output_image_path, "PNG")


def convert_svg_to_png(svg_content, output_png_path):
    """
    将SVG内容转换为PNG图像并保存到指定路径。

    参数:
    svg_content (str): SVG内容。
    output_png_path (str): 输出PNG文件的路径。
    """
    import cairosvg

    # 将SVG内容转换为PNG，并写入到输出路径
    cairosvg.svg2png(bytestring=svg_content, write_to=output_png_path)
    return True


def image_to_base64(image_path, format='JPEG'):
    """图片转Base64"""
    with Image.open(image_path) as img:
        buffered = BytesIO()
        img.save(buffered, format=format.upper())
        return base64.b64encode(buffered.getvalue()).decode('utf-8')


def base64_to_image(base64_str, output_path=None):
    """Base64转图片，可保存或返回PIL对象"""
    img_data = base64.b64decode(base64_str)
    img = Image.open(BytesIO(img_data))
    if output_path:
        img.save(output_path)
    return img


if __name__ == "__main__":
    input_image_path = r"E:\AI数字人\logos\logo.jpg"  # 替换为你的输入图片路径
    output_image_path = r"E:\AI数字人\logos\logo.png"  # 替换为你想要保存的输出图片路径
    removeDarkWithTransparent(input_image_path, output_image_path)
