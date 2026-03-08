# 工具函数

import math
import random

def distance(point1, point2):
    """计算两点之间的距离"""
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

def interpolate_color(color1, color2, factor):
    """在两个颜色之间插值"""
    r = int(color1[0] + (color2[0] - color1[0]) * factor)
    g = int(color1[1] + (color2[1] - color1[1]) * factor)
    b = int(color1[2] + (color2[2] - color1[2]) * factor)
    return (r, g, b)

def get_random_position(width, height, margin=50):
    """获取随机位置（考虑边界留白）"""
    return (
        random.randint(margin, width - margin),
        random.randint(margin, height - margin)
    )

def format_time(seconds):
    """格式化时间显示"""
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

def clamp(value, min_val, max_val):
    """将值限制在最小值和最大值之间"""
    return max(min_val, min(value, max_val))