from PIL import Image, ImageFilter, ImageEnhance
def filter_image(image_path, output_path, type):
    pass

def filter_old_photo(image_path, output_path):
    # 打开图片
    img = Image.open(image_path)

    # 转换为灰度图像
    gray_img = img.convert("L")

    # 应用模糊效果
    blurred_img = gray_img.filter(ImageFilter.GaussianBlur(radius=2))

    # 将模糊的灰度图像转换为RGB
    blurred_img = blurred_img.convert("RGB")

    # 创建一个对比度增强对象，并应用增强
    enhancer = ImageEnhance.Contrast(blurred_img)
    contrasted_img = enhancer.enhance(2)  # 增加对比度

    # 创建一个亮度增强对象，并应用增强
    enhancer = ImageEnhance.Brightness(contrasted_img)
    final_img = enhancer.enhance(0.9)  # 稍微降低亮度

    # 保存修改后的图片
    final_img.save(output_path)

def filter_sketch(image_path, output_path):
    # https://github.com/emcconville/wand
    
    pass

# 颜色调整
# https://zhuanlan.zhihu.com/p/358711310
def adjustment_color(image_path, output_path, type):
    pass


def adjustment_color_candy_colors(image_path, output_path):
    pass


def adjustment_color_macaron_colors(image_path, output_path):
    pass


def adjustment_color_comic_book_feel(image_path, output_path):
    pass


def adjustment_color_fresh_and_simple(image_path, output_path):
    pass


def adjustment_color_blue_and_yellow(image_path, output_path):
    pass


def adjustment_color_morandi_color(image_path, output_path):
    pass
