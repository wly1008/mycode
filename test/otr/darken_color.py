# -*- coding: utf-8 -*-
"""
Created on Thu Oct 17 14:44:57 2024

@author: wly
"""

def darken_color(color, factor=0.5):
    """
    Darkens the given color by a factor.
    
    :param color: A string representing the color in hex format (e.g., '#RRGGBB').
    :param factor: A float between 0 and 1, where 0 is black and 1 is the original color.
    :return: A new color string in hex format.
    """
    # 去掉 '#' 符号并转换为 RGB
    r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
    
    # 加深颜色
    r = int(r * factor)
    g = int(g * factor)
    b = int(b * factor)
    
    # 确保颜色值在有效范围内
    r = max(0, min(r, 255))
    g = max(0, min(g, 255))
    b = max(0, min(b, 255))
    
    # 返回新的颜色字符串
    return f'#{r:02x}{g:02x}{b:02x}'

# 示例：加深颜色 '#addd8e'
original_color = '#addd8e'
darkened_color = darken_color(original_color, factor=0.5)  # 因子 0.5 表示加深一半

print(f"Original Color: {original_color}")
print(f"Darkened Color: {darkened_color}")