import colorsys
from PIL import Image
import tkinter as tk
from tkinter import filedialog, Scale, Button, Label
from PIL import ImageTk
import numpy as np


def update_image(event=None):
    global saturation_threshold, value_threshold, original_image_data
    saturation_threshold = saturation_scale.get()
    value_threshold = value_threshold_scale.get()

    image = Image.fromarray(original_image_data)
    image = image.convert("RGBA")
    data = image.getdata()

    new_data = []
    for item in data:
        hsv = colorsys.rgb_to_hsv(item[0] / 255, item[1] / 255, item[2] / 255)
        if hsv[1] < saturation_threshold and hsv[2] < value_threshold:
            alpha = 0
            new_data.append((item[0], item[1], item[2], alpha))
        else:
            new_data.append(item)

    image.putdata(new_data)
    processed_image = ImageTk.PhotoImage(image)
    processed_image_label.config(image=processed_image)
    processed_image_label.image = processed_image


def select_input_image():
    global input_image_path, original_image, original_image_data
    input_image_path = filedialog.askopenfilename()
    original_image = Image.open(input_image_path)
    original_image_data = np.array(original_image)
    show_original_image()


def select_output_image_path():
    global output_image_path
    output_image_path = filedialog.asksaveasfilename(defaultextension=".png")


def show_original_image():
    global original_image
    original_image.thumbnail((300, 300))  # 调整图片大小以便更好展示
    original_image_tk = ImageTk.PhotoImage(original_image)
    original_image_label.config(image=original_image_tk)
    original_image_label.image = original_image_tk


def save_processed_image():
    global output_image_path, processed_image
    processed_image.save(output_image_path)


if __name__ == "__main__":
    root = tk.Tk()

    input_image_path = ""
    output_image_path = ""
    saturation_threshold = 0.1
    value_threshold = 0.1
    original_image = None
    original_image_data = None
    processed_image = None

    # 选择输入图片按钮
    select_input_button = Button(
        root, text="选择输入图片", command=select_input_image)
    select_input_button.pack()

    # 显示原图的标签和图片框
    original_image_label = Label(root)
    original_image_label.pack()

    # 饱和度阈值调整滑块
    saturation_scale = Scale(root, from_=0, to=1, resolution=0.01, orient=tk.HORIZONTAL,
                             label="饱和度阈值", command=update_image)
    saturation_scale.set(saturation_threshold)
    saturation_scale.pack()

    # 明度阈值调整滑块
    value_threshold_scale = Scale(root, from_=0, to=1, resolution=0.01, orient=tk.HORIZONTAL,
                                  label="明度阈值", command=update_image)
    value_threshold_scale.set(value_threshold)
    value_threshold_scale.pack()

    # 显示处理后图片的标签和图片框
    processed_image_label = Label(root)
    processed_image_label.pack()

    # 选择输出图片路径按钮
    select_output_button = Button(
        root, text="选择输出图片路径", command=select_output_image_path)
    select_output_button.pack()

    # 保存按钮
    save_button = Button(root, text="保存", command=save_processed_image)
    save_button.pack()

    root.mainloop()
