import cv2 as cv
import numpy as np


# Hex to RGB
def hex2rgb(hex_color):
    r = (hex_color >> 16) & 255
    g = (hex_color >> 8) & 255
    b = (hex_color >> 0) & 255
    return r, g, b


# Hex to RGB
def rgb2hex(rgb_color):
    r, g, b = rgb_color
    return ('#' + '{:02X}' * 3).format(r, g, b)


# RGB颜色转换为HSL颜色
def rgb2hsl(rgb):
    rgb_normal = [[[rgb[0] / 255, rgb[1] / 255, rgb[2] / 255]]]
    hls = cv.cvtColor(np.array(rgb_normal, dtype=np.float32), cv.COLOR_RGB2HLS)
    return hls[0][0][0], hls[0][0][2], hls[0][0][1]  # hls to hsl


# HSL颜色转换为RGB颜色
def hsl2rgb(hsl):
    hls = [[[hsl[0], hsl[2], hsl[1]]]]  # hsl to hls
    rgb_normal = cv.cvtColor(np.array(hls, dtype=np.float32), cv.COLOR_HLS2RGB)
    return int(rgb_normal[0][0][0] * 255), int(rgb_normal[0][0][1] * 255), int(rgb_normal[0][0][2] * 255)


# HSL渐变色
def get_multi_colors_by_hsl(begin_color, end_color, color_count):
    if color_count < 2:
        return []

    colors = []
    hsl1 = rgb2hsl(begin_color)
    hsl2 = rgb2hsl(end_color)
    steps = [(hsl2[i] - hsl1[i]) / (color_count - 1) for i in range(3)]
    for color_index in range(color_count):
        hsl = [hsl1[i] + steps[i] * color_index for i in range(3)]
        colors.append(hsl2rgb(hsl))

    return colors


color_dict = {  # to render
    'obstacle': (0, 0, 0),
    'vacant': (255, 255, 255),
    'unvisited': (128, 128, 128),
}


#   0xFDD819-0xE04C4C
colors = get_multi_colors_by_hsl(hex2rgb(0xFDD819), hex2rgb(0xE04C4C), 100)     # 黄--红
colors = [(255, 255, 255), ] + colors[:80]   # 信息素为0时，设为白色
# print(colors)


def get_color_by_pheromone(p):
    idx = min(len(colors)-1, int(p * len(colors)))
    return rgb2hex(colors[idx])
