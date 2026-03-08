"""
图片资源加载器
用于加载和管理游戏中的水果图片资源
"""
import cv2
import os
import math
import numpy as np

class ImageLoader:
    def __init__(self, assets_dir="assets/fruits"):
        self.assets_dir = assets_dir
        self.images = {}
        self.load_all_images()

    def load_all_images(self):
        """加载所有6种水果+炸弹+连击图片（兼容大小写/多格式）"""
        if not os.path.exists(self.assets_dir):
            print(f"⚠️ 资源目录不存在：{self.assets_dir}，请创建并放入以下图片：")
            print("apple.png, banana.png, orange.png, watermelon.png, grape.png, peach.png")
            return

        # 全量水果映射（key=强制匹配名，value=可选文件名）
        fruit_mapping = {
            "apple": ["apple"],
            "banana": ["banana"],
            "orange": ["orange"],
            "watermelon": ["watermelon"],
            "grape": ["grape"],
            "peach": ["peach"],
            "bomb": ["bomb"],
            "combo": ["combo"]
        }
        extensions = ['.png', '.jpg', '.jpeg']

        # 加载图片（兼容大小写）
        for fruit_name, filenames in fruit_mapping.items():
            for fname in filenames:
                for ext in extensions:
                    # 尝试小写/大写后缀
                    paths = [
                        os.path.join(self.assets_dir, f"{fname}{ext}"),
                        os.path.join(self.assets_dir, f"{fname}{ext.upper()}")
                    ]
                    for path in paths:
                        if os.path.exists(path):
                            img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
                            if img is not None:
                                # 统一转为4通道BGRA（透明）
                                if len(img.shape) == 2:
                                    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
                                elif img.shape[2] == 3:
                                    img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
                                self.images[fruit_name] = img
                                print(f"✅ 加载成功：{path}")
                                break
                    if fruit_name in self.images:
                        break
            if fruit_name not in self.images:
                print(f"❌ 未找到 {fruit_name} 的图片（请检查 {self.assets_dir}/{fruit_name}.png）")

    def get_image(self, fruit_type=None, fruit_color=None, fruit_name=None):
        """
        精准匹配：优先fruit_name → 其次按fruit_color匹配对应水果 → 兜底苹果
        """
        # 1. 优先强制指定水果名（最高优先级）
        if fruit_name and fruit_name in self.images:
            return self.images[fruit_name]

        # 2. 按颜色精准匹配6种水果（核心：给每个颜色绑定唯一水果名）
        color_to_fruit = {
            (255, 0, 0): "apple",  # 红→苹果
            (255, 165, 0): "orange",  # 橙→橙子
            (255, 255, 0): "banana",  # 黄→香蕉
            (0, 255, 0): "watermelon",  # 绿→西瓜
            (128, 0, 128): "grape",  # 紫→葡萄
            (255, 192, 203): "peach"  # 粉→桃子
        }
        if fruit_color in color_to_fruit:
            target_fruit = color_to_fruit[fruit_color]
            return self.images.get(target_fruit)

        # 3. 兜底（仅无匹配时返回苹果）
        return self.images.get("apple")
     # 保留原有resize/rotate方法（不变）
    def resize_image(self, image, size):
        """
        调整图片大小
        Args:
            image: 原始图片
            size: 目标大小 (width, height)
        Returns:
            resized_image: 调整后的图片
        """
        if image is None:
            return None
        return cv2.resize(image, size, interpolation=cv2.INTER_LINEAR)
    
    def rotate_image(self, image, angle):
        """
        旋转图片
        Args:
            image: 原始图片
            angle: 旋转角度（度）
        Returns:
            rotated_image: 旋转后的图片
        """
        if image is None:
            return None
        
        # 获取图片中心
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        
        # 创建旋转矩阵
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # 执行旋转
        rotated = cv2.warpAffine(image, rotation_matrix, (w, h), 
                                 flags=cv2.INTER_LINEAR,
                                 borderMode=cv2.BORDER_CONSTANT,
                                 borderValue=(0, 0, 0, 0))
        
        return rotated

