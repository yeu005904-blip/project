import cv2
import numpy as np
import time
import pickle
import os
from datetime import datetime
from utils.image_loader import ImageLoader

class UIRenderer:
    def __init__(self, screen_width=1280, screen_height=720):
        """
        界面渲染与状态管理类
        Args:
            screen_width: 屏幕宽度
            screen_height: 屏幕高度
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # 窗口和显示设置
        self.window_name = "Fruit Ninja - MediaPipe Edition"
        self.fullscreen = False
        
        # 颜色定义
        self.colors = {
            'background': (25, 25, 50),      # 深蓝色背景
            'text': (255, 255, 255),         # 白色文字
            'combo': (255, 215, 0),          # 金色连击文字
            'life': (255, 50, 50),           # 红色生命值
            'score': (50, 255, 50),          # 绿色分数
            'bomb': (50, 50, 50),            # 灰色炸弹
            'trajectory_green': (0, 255, 0), # 绿色轨迹（左手）
            'trajectory_blue': (255, 0, 0),  # 蓝色轨迹（右手）
            'menu_bg': (0, 0, 0, 180),       # 半透明菜单背景
            'button': (70, 130, 180),        # 按钮蓝色
            'button_hover': (100, 160, 220), # 按钮悬停色
        }
        
        # 字体设置
        self.font_scale_small = 0.6
        self.font_scale_medium = 0.8
        self.font_scale_large = 1.2
        self.font_scale_xlarge = 1.8
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_bold = cv2.FONT_HERSHEY_DUPLEX
        
        # 游戏状态
        self.game_state = "RUNNING"  # RUNNING, PAUSED, GAME_OVER
        self.last_game_state = "RUNNING"
        
        # 帧率控制
        self.target_fps = 30
        self.frame_time = 1.0 / self.target_fps
        self.last_frame_time = time.time()
        self.current_fps = 0
        
        # 菜单状态
        self.menu_options = ["继续游戏", "重新开始", "退出游戏"]
        self.selected_option = 0
        
        # 视觉效果
        self.particle_effects = []
        
        # 图片资源加载器
        self.image_loader = ImageLoader()
        self.use_images = len(self.image_loader.images) > 0  # 如果有图片就使用图片，否则使用颜色
        
        # 初始化窗口
        self._init_window()
    
    def _init_window(self):
        """初始化游戏窗口"""
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, self.screen_width, self.screen_height)
        print(f"游戏窗口初始化完成: {self.screen_width}x{self.screen_height}")
    
    def toggle_fullscreen(self):
        """切换全屏模式"""
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        else:
            cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
        return self.fullscreen
    
    def draw_background(self, frame):
        """绘制游戏背景 - 使用摄像头画面作为背景"""
        # 不再绘制渐变网格背景，而是使用传入的frame（摄像头画面）
        # 可以添加一个半透明的覆盖层，让游戏元素更清晰
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (self.screen_width, self.screen_height), 
                    (25, 25, 50, 100), -1)  # 半透明深蓝色覆盖层
        cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)

    def draw_fruit(self, frame, fruit):
        """绘制水果 - 增强版，支持多种水果类型（修复图片绘制+颜色+边界问题）"""
        # 新增：确保ImageLoader实例存在（需在类初始化中定义self.image_loader = ImageLoader()）
        if not hasattr(self, 'image_loader'):
            from utils.image_loader import ImageLoader
            self.image_loader = ImageLoader()

        # 新增：边界检查 - 水果超出画面则不绘制
        h, w = frame.shape[:2]
        if (fruit.x < 0 or fruit.x > w or fruit.y < 0 or fruit.y > h):
            return

        # 基础参数统一
        fruit_center = (int(fruit.x), int(fruit.y))
        fruit_radius = fruit.size // 2

        if fruit.type == "normal":
            # ========== 核心修复：绘制加载的水果图片 ==========
            # 颜色转换：BGR(RGB) → RGB（适配ImageLoader的颜色匹配）
            fruit_color_rgb = (fruit.color[2], fruit.color[1], fruit.color[0]) if len(fruit.color) == 3 else fruit.color
            fruit_img = self.image_loader.get_image("normal", fruit_color=fruit_color_rgb)

            if fruit_img is not None:
                # 调整图片尺寸匹配水果大小
                img_resized = self.image_loader.resize_image(fruit_img, (fruit.size, fruit.size))
                if img_resized is not None:
                    # 计算图片绘制坐标（中心对齐+边界裁剪）
                    y1 = max(0, int(fruit.y - fruit.size // 2))
                    y2 = min(h, int(fruit.y + fruit.size // 2))
                    x1 = max(0, int(fruit.x - fruit.size // 2))
                    x2 = min(w, int(fruit.x + fruit.size // 2))

                    # 裁剪图片到画面可视区域（避免越界）
                    img_y1 = max(0, int(fruit.size // 2 - (fruit.y - y1)))
                    img_y2 = img_y1 + (y2 - y1)
                    img_x1 = max(0, int(fruit.size // 2 - (fruit.x - x1)))
                    img_x2 = img_x1 + (x2 - x1)
                    img_crop = img_resized[img_y1:img_y2, img_x1:img_x2]

                    # 处理透明通道（关键：图片叠加到画面）
                    alpha = img_crop[:, :, 3] / 255.0
                    for c in range(3):
                        frame[y1:y2, x1:x2, c] = (1 - alpha) * frame[y1:y2, x1:x2, c] + alpha * img_crop[:, :, c]
            else:
                # 图片加载失败时，保留原有圆形绘制逻辑（修复颜色格式）
                # 颜色转换：RGB → BGR（适配OpenCV绘制）
                bgr_color = (fruit.color[2], fruit.color[1], fruit.color[0]) if len(fruit.color) == 3 else fruit.color
                cv2.circle(frame, fruit_center, fruit_radius, bgr_color, -1)

                # 水果高光效果（新增边界检查）
                highlight_radius = max(1, fruit_radius // 4)
                highlight_pos = (max(0, int(fruit.x - fruit_radius // 4)),
                                 max(0, int(fruit.y - fruit_radius // 4)))
                cv2.circle(frame, highlight_pos, highlight_radius, (255, 255, 255), -1)

                # 水果轮廓
                cv2.circle(frame, fruit_center, fruit_radius, (255, 255, 255), 2)

            # 切割效果（保留原有逻辑）
            if fruit.cut:
                self._add_cut_particles(fruit.x, fruit.y, fruit.color)

        elif fruit.type == "combo":
            # ========== 修复Combo绘制：支持图片+脉冲限制 ==========
            combo_img = self.image_loader.get_image("combo")
            if combo_img is not None:
                # 脉冲效果优化：限制范围避免负半径
                pulse = int(5 * np.sin(time.time() * 6))
                pulse = max(-3, min(3, pulse))
                combo_size = fruit.size + pulse

                # 调整图片尺寸
                img_resized = self.image_loader.resize_image(combo_img, (combo_size, combo_size))
                if img_resized is not None:
                    # 绘制坐标计算（边界裁剪）
                    y1 = max(0, int(fruit.y - combo_size // 2))
                    y2 = min(h, int(fruit.y + combo_size // 2))
                    x1 = max(0, int(fruit.x - combo_size // 2))
                    x2 = min(w, int(fruit.x + combo_size // 2))

                    # 图片裁剪
                    img_y1 = max(0, int(combo_size // 2 - (fruit.y - y1)))
                    img_y2 = img_y1 + (y2 - y1)
                    img_x1 = max(0, int(combo_size // 2 - (fruit.x - x1)))
                    img_x2 = img_x1 + (x2 - x1)
                    img_crop = img_resized[img_y1:img_y2, img_x1:img_x2]

                    # 透明通道处理
                    alpha = img_crop[:, :, 3] / 255.0
                    for c in range(3):
                        frame[y1:y2, x1:x2, c] = (1 - alpha) * frame[y1:y2, x1:x2, c] + alpha * img_crop[:, :, c]
            else:
                # 原有Combo绘制逻辑（修复脉冲+颜色+边界）
                pulse = int(5 * np.sin(time.time() * 6))
                pulse = max(-3, min(3, pulse))

                # 绘制连击水果（带脉冲光晕）
                cv2.circle(frame, fruit_center, fruit_radius + pulse, (255, 0, 255), -1)

                # 修复颜色格式：RGB→BGR
                bgr_color = (fruit.color[2], fruit.color[1], fruit.color[0]) if len(fruit.color) == 3 else fruit.color
                cv2.circle(frame, fruit_center, fruit_radius, bgr_color, -1)

                # 高光效果（边界检查）
                highlight_radius = max(1, fruit_radius // 4)
                highlight_pos = (max(0, int(fruit.x - fruit_radius // 4)),
                                 max(0, int(fruit.y - fruit_radius // 4)))
                cv2.circle(frame, highlight_pos, highlight_radius, (255, 255, 255), -1)

                # 轮廓（紫色）
                cv2.circle(frame, fruit_center, fruit_radius, (200, 0, 200), 2)

                # 连击标记（边界检查）
                text_pos = (max(0, int(fruit.x - 6)), min(h, int(fruit.y + 6)))
                cv2.putText(frame, "C", text_pos,
                            cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 2)

            if fruit.cut:
                self._add_cut_particles(fruit.x, fruit.y, fruit.color, count=12)

        else:  # bomb
            # ========== 修复炸弹绘制：支持图片+边界检查 ==========
            bomb_img = self.image_loader.get_image("bomb")
            if bomb_img is not None:
                # 调整炸弹图片尺寸
                img_resized = self.image_loader.resize_image(bomb_img, (fruit.size, fruit.size))
                if img_resized is not None:
                    # 绘制坐标计算（边界裁剪）
                    y1 = max(0, int(fruit.y - fruit.size // 2))
                    y2 = min(h, int(fruit.y + fruit.size // 2))
                    x1 = max(0, int(fruit.x - fruit.size // 2))
                    x2 = min(w, int(fruit.x + fruit.size // 2))

                    # 图片裁剪
                    img_y1 = max(0, int(fruit.size // 2 - (fruit.y - y1)))
                    img_y2 = img_y1 + (y2 - y1)
                    img_x1 = max(0, int(fruit.size // 2 - (fruit.x - x1)))
                    img_x2 = img_x1 + (x2 - x1)
                    img_crop = img_resized[img_y1:img_y2, img_x1:img_x2]

                    # 透明通道处理
                    alpha = img_crop[:, :, 3] / 255.0
                    for c in range(3):
                        frame[y1:y2, x1:x2, c] = (1 - alpha) * frame[y1:y2, x1:x2, c] + alpha * img_crop[:, :, c]
            else:
                # 原有炸弹绘制逻辑（修复边界检查）
                # 确保self.colors已定义，无则默认黑色
                bomb_color = self.colors.get('bomb', (0, 0, 0)) if hasattr(self, 'colors') else (0, 0, 0)
                cv2.circle(frame, fruit_center, fruit_radius, bomb_color, -1)

                # 炸弹引线（边界检查）
                fuse_length = max(1, fruit_radius // 2)
                fuse_start = (int(fruit.x), max(0, int(fruit.y - fruit_radius)))
                fuse_end = (int(fruit.x), max(0, int(fruit.y - fruit_radius - fuse_length)))
                cv2.line(frame, fuse_start, fuse_end, (150, 150, 150), 3)

                # 引线火花（边界检查）
                spark_radius = 5
                spark_pos = (fuse_end[0], max(0, fuse_end[1] - spark_radius))
                spark_color = (255, 200, 0) if int(time.time() * 10) % 2 == 0 else (255, 100, 0)
                cv2.circle(frame, spark_pos, spark_radius, spark_color, -1)

                # 炸弹危险标志（边界检查）
                text_pos = (max(0, int(fruit.x - 5)), min(h, int(fruit.y + 5)))
                cv2.putText(frame, "!", text_pos,
                            cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 2)
    
    def _add_cut_particles(self, x, y, color, count=10):
        """添加切割粒子效果 - 增强版"""
        for _ in range(count):  # 生成粒子
            angle = np.random.random() * 2 * np.pi
            speed = np.random.uniform(2, 8)
            velocity = (np.cos(angle) * speed, np.sin(angle) * speed)
            lifetime = np.random.randint(20, 40)
            
            particle = {
                'x': x,
                'y': y,
                'vx': velocity[0],
                'vy': velocity[1],
                'color': color,
                'size': np.random.randint(3, 8),
                'lifetime': lifetime,
                'max_lifetime': lifetime
            }
            self.particle_effects.append(particle)
    
    def draw_particles(self, frame):
        """绘制粒子效果"""
        particles_to_remove = []
        
        for particle in self.particle_effects:
            # 更新粒子位置
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['vy'] += 0.2  # 重力效果
            
            # 减少生命周期
            particle['lifetime'] -= 1
            
            # 计算透明度
            alpha = particle['lifetime'] / particle['max_lifetime']
            
            # 绘制粒子
            if particle['lifetime'] > 0:
                color = particle['color']
                # 根据生命周期调整颜色亮度
                brightness = int(255 * alpha)
                adjusted_color = (
                    min(255, color[0] + brightness),
                    min(255, color[1] + brightness),
                    min(255, color[2] + brightness)
                )
                
                cv2.circle(frame, 
                          (int(particle['x']), int(particle['y'])), 
                          particle['size'], 
                          adjusted_color, 
                          -1)
            else:
                particles_to_remove.append(particle)
        
        # 移除生命周期结束的粒子
        self.particle_effects = [p for p in self.particle_effects if p not in particles_to_remove]
    
    def draw_trajectories(self, frame, trajectories):
        """绘制手部轨迹"""
        if not trajectories:
            return
        
        for hand_label, trajectory in trajectories:
            if len(trajectory) < 2:
                continue
            
            # 选择轨迹颜色
            if hand_label == 'Left':
                color = self.colors['trajectory_green']
            else:
                color = self.colors['trajectory_blue']
            
            # 绘制轨迹线段
            for i in range(1, len(trajectory)):
                point1 = (int(trajectory[i-1][0]), int(trajectory[i-1][1]))
                point2 = (int(trajectory[i][0]), int(trajectory[i][1]))
                
                # 计算线段长度来调整粗细
                dx = point2[0] - point1[0]
                dy = point2[1] - point1[1]
                length = np.sqrt(dx*dx + dy*dy)
                thickness = max(2, min(6, int(length / 10)))
                
                cv2.line(frame, point1, point2, color, thickness)
            
            # 绘制当前手部位置
            if trajectory:
                last_point = (int(trajectory[-1][0]), int(trajectory[-1][1]))
                cv2.circle(frame, last_point, 10, color, -1)
                cv2.circle(frame, last_point, 6, (255, 255, 255), -1)
    
    def draw_ui(self, frame, game_data):
        """绘制游戏UI"""
        score = game_data.get('score', 0)
        lives = game_data.get('lives', 3)
        max_score = game_data.get('max_score', 0)
        combo = game_data.get('combo', 0)
        fruits_cut = game_data.get('fruits_cut', 0)
        max_combo = game_data.get('max_combo', 0)
        
        # 绘制分数（左上角）
        score_text = f"Score: {score}"
        cv2.putText(frame, score_text, (20, 40), self.font_bold, 
                   self.font_scale_large, self.colors['score'], 3)
        
        # 绘制最高分
        high_score_text = f"Highest Score: {max_score}"
        cv2.putText(frame, high_score_text, (20, 80), self.font, 
                   self.font_scale_medium, self.colors['text'], 2)
        
        # 绘制生命值（右上角）
        life_text = f"Lives: {lives}"
        life_x = self.screen_width - 180
        cv2.putText(frame, life_text, (life_x, 40), self.font_bold, 
                   self.font_scale_large, self.colors['life'], 3)
        
        # 绘制连击数（如果大于0）
        if combo > 1:
            combo_text = f"{combo} Combo!"
            combo_x = self.screen_width // 2
            combo_y = 100
            
            # 连击背景效果
            text_size = cv2.getTextSize(combo_text, self.font_bold, 
                                       self.font_scale_xlarge, 3)[0]
            bg_x1 = combo_x - text_size[0] // 2 - 20
            bg_y1 = combo_y - text_size[1] - 10
            bg_x2 = combo_x + text_size[0] // 2 + 20
            bg_y2 = combo_y + 10
            
            # 绘制半透明背景
            overlay = frame.copy()
            cv2.rectangle(overlay, (bg_x1, bg_y1), (bg_x2, bg_y2), 
                         (0, 0, 0, 150), -1)
            cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)
            
            # 绘制连击文字
            cv2.putText(frame, combo_text, (combo_x - text_size[0] // 2, combo_y), 
                       self.font_bold, self.font_scale_xlarge, self.colors['combo'], 3)
        
        
        # 绘制统计信息（右下角）
        stats_text = f"Fruits: {fruits_cut}  Best Combo: {max_combo}"
        text_size = cv2.getTextSize(stats_text, self.font, self.font_scale_small, 1)[0]
        stats_x = self.screen_width - text_size[0] - 20
        cv2.putText(frame, stats_text, (stats_x, self.screen_height - 20), 
                   self.font, self.font_scale_small, self.colors['text'], 1)
        
        # 绘制FPS（左上角下方）
        #fps_text = f"FPS: {self.current_fps:.1f}"
        #cv2.putText(frame, fps_text, (20, 120), self.font, 
         #          self.font_scale_small, self.colors['text'], 1)
    
    def draw_pause_menu(self, frame):
        """绘制暂停菜单"""
        # 创建半透明遮罩
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (self.screen_width, self.screen_height), 
                     (0, 0, 0, 180), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # 菜单标题
        title = "Game Paused"
        title_size = cv2.getTextSize(title, self.font_bold, self.font_scale_xlarge, 3)[0]
        title_x = (self.screen_width - title_size[0]) // 2
        title_y = self.screen_height // 3
        
        cv2.putText(frame, title, (title_x, title_y), self.font_bold, 
                   self.font_scale_xlarge, self.colors['text'], 3)
        
        # 菜单选项
        self.menu_options = ["Continue", "Restart", "Exit Game"]

        option_y = title_y + 80
        option_spacing = 70
        
        for i, option in enumerate(self.menu_options):
            option_x = (self.screen_width - 200) // 2
            
            # 绘制选项背景
            if i == self.selected_option:
                bg_color = self.colors['button_hover']
                text_color = (255, 255, 255)
                border_color = (255, 255, 0)  # 黄色边框
                border_thickness = 3 
            else:
                bg_color = self.colors['button']
                text_color = (200, 200, 200)
                border_color = self.colors['text']
                border_thickness = 2
            
            cv2.rectangle(frame, (option_x - 20, option_y - 35), 
                         (option_x + 220, option_y + 5), bg_color, -1)
            cv2.rectangle(frame, (option_x - 20, option_y - 35), 
                         (option_x + 220, option_y + 5), border_color, border_thickness)
            
            # 绘制选项文字
            cv2.putText(frame, option, (option_x, option_y), self.font, 
                       self.font_scale_medium, text_color, 2)
            
            # 绘制快捷键提示
            shortcut = f"({i+1})"
            shortcut_size = cv2.getTextSize(shortcut, self.font, 
                                          self.font_scale_small, 1)[0]
            shortcut_x = option_x + 180 - shortcut_size[0]
            cv2.putText(frame, shortcut, (shortcut_x, option_y), 
                       self.font, self.font_scale_small, text_color, 1)
            
            option_y += option_spacing
        
        # 操作提示
        hint = "Use up or down to Select, Enter to Confirm | ESC to Return"
        hint_size = cv2.getTextSize(hint, self.font, self.font_scale_small, 1)[0]
        hint_x = (self.screen_width - hint_size[0]) // 2
        hint_y = self.screen_height - 50
        
        cv2.putText(frame, hint, (hint_x, hint_y), self.font, 
                   self.font_scale_small, self.colors['text'], 1)
    
    def draw_game_over(self, frame, game_data):
        """绘制游戏结束画面"""
        score = game_data.get('score', 0)
        max_score = game_data.get('max_score', 0)
        fruits_cut = game_data.get('fruits_cut', 0)
        max_combo = game_data.get('max_combo', 0)
        
        # 创建半透明遮罩
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (self.screen_width, self.screen_height), 
                     (0, 0, 0, 200), -1)
        cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)
        
        # 游戏结束标题
        title = "GAME OVER!"
        title_size = cv2.getTextSize(title, self.font_bold, self.font_scale_xlarge, 4)[0]
        title_x = (self.screen_width - title_size[0]) // 2
        title_y = self.screen_height // 4
        
        cv2.putText(frame, title, (title_x, title_y), self.font_bold, 
                   self.font_scale_xlarge, self.colors['life'], 4)
        
        # 最终分数
        score_text = f"Final Score: {score}"
        score_size = cv2.getTextSize(score_text, self.font_bold, 
                                    self.font_scale_large, 3)[0]
        score_x = (self.screen_width - score_size[0]) // 2
        score_y = title_y + 80
        
        cv2.putText(frame, score_text, (score_x, score_y), self.font_bold, 
                   self.font_scale_large, self.colors['score'], 3)
        
        # 如果打破纪录
        if score == max_score and score > 0:
            record_text = "New Record!"
            record_size = cv2.getTextSize(record_text, self.font_bold, 
                                         self.font_scale_medium, 2)[0]
            record_x = (self.screen_width - record_size[0]) // 2
            record_y = score_y + 50
            
            cv2.putText(frame, record_text, (record_x, record_y), self.font_bold, 
                       self.font_scale_medium, self.colors['combo'], 2)
        
        # 游戏统计
        stats_y = score_y + 100
        
        stats = [
            f"High Score: {max_score}",
            f"Fruits Cut: {fruits_cut}",
            f"Max Combo: {max_combo}",
            f"Game Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        ]
        
        for i, stat in enumerate(stats):
            stat_size = cv2.getTextSize(stat, self.font, 
                                       self.font_scale_medium, 2)[0]
            stat_x = (self.screen_width - stat_size[0]) // 2
            stat_y = stats_y + i * 40
            
            cv2.putText(frame, stat, (stat_x, stat_y), self.font, 
                       self.font_scale_medium, self.colors['text'], 2)
        
        # 重新开始选项
        restart_y = stats_y + len(stats) * 40 + 50
        options = ["Press R to Reset", "Press ESC to Exit"]
        
        for i, option in enumerate(options):
            option_size = cv2.getTextSize(option, self.font, 
                                         self.font_scale_medium, 2)[0]
            option_x = (self.screen_width - option_size[0]) // 2
            option_y = restart_y + i * 50
            
            cv2.putText(frame, option, (option_x, option_y), self.font, 
                       self.font_scale_medium, self.colors['text'], 2)
    
    def draw_cut_effects(self, frame, cut_effects):
        """绘制切割效果"""
        for effect in cut_effects:
            if effect['timer'] > 0:
                # 绘制切割线
                points = effect['points']
                if len(points) >= 2:
                    for i in range(len(points) - 1):
                        cv2.line(frame, 
                                (int(points[i][0]), int(points[i][1])),
                                (int(points[i+1][0]), int(points[i+1][1])),
                                (255, 255, 255), 3)
                
                # 绘制水果切割效果
                fruit_pos = effect['fruit_pos']
                fruit_type = effect['fruit_type']
                
                if fruit_type == "normal":
                    # 水果切割闪光效果
                    flash_radius = effect['timer'] * 2
                    cv2.circle(frame, 
                              (int(fruit_pos[0]), int(fruit_pos[1])),
                              flash_radius, 
                              (255, 255, 255), 
                              2)
    
    def draw_explosions(self, frame, explosions):
        """绘制爆炸效果 - 大量红色粒子喷涌"""
        for explosion in explosions:
            # 只绘制粒子，不绘制圆圈
            for particle in explosion['particles']:
                if particle['lifetime'] > 0:
                    alpha = particle['lifetime'] / particle['max_lifetime']
                    px = int(particle['x'])
                    py = int(particle['y'])
                    
                    # 根据生命周期调整粒子大小
                    base_size = particle['size']
                    size = max(2, int(base_size * (0.5 + 0.5 * alpha)))  # 粒子逐渐变小
                    
                    if size > 0 and 0 <= px < frame.shape[1] and 0 <= py < frame.shape[0]:
                        # 粒子颜色转换为BGR格式
                        color_rgb = particle['color']  # RGB格式
                        color_bgr = (color_rgb[2], color_rgb[1], color_rgb[0])  # 转换为BGR
                        
                        # 根据生命周期调整亮度和大小
                        # 早期更亮，后期逐渐变暗
                        brightness_factor = alpha
                        adjusted_color = (
                            min(255, int(color_bgr[0] * brightness_factor)),
                            min(255, int(color_bgr[1] * brightness_factor)),
                            min(255, int(color_bgr[2] * brightness_factor))
                        )
                        
                        # 绘制粒子（实心圆）
                        cv2.circle(frame, (px, py), size, adjusted_color, -1)
                        
                        # 添加高光效果（让粒子更亮）
                        if size > 3:
                            highlight_size = max(1, size // 3)
                            cv2.circle(frame, (px - highlight_size // 2, py - highlight_size // 2), 
                                      highlight_size, (255, 255, 255), -1)
    
    def update_fps(self):
        """更新FPS计算"""
        current_time = time.time()
        delta_time = current_time - self.last_frame_time
        self.last_frame_time = current_time
        
        if delta_time > 0:
            self.current_fps = 1.0 / delta_time
    
    def handle_keyboard_input(self):
        """
        处理键盘输入
        Returns:
            command: 用户操作指令字符串
        """
        key = cv2.waitKey(1) & 0xFF
        command = None
        
        if self.game_state == "RUNNING":
            if key == ord('p') or key == ord('P'):
                self.last_game_state = self.game_state
                self.game_state = "PAUSED"
                command = "pause"
                print("Game Paused")
            elif key == ord('f') or key == ord('F'):
                self.toggle_fullscreen()
                print(f"Fullscreen Mode: {'ON' if self.fullscreen else 'OFF'}")
        
        elif self.game_state == "PAUSED":
            if key == 27:  # ESC键
                self.game_state = self.last_game_state
                command = "continue"
                print("Game Continue")
            elif key == 13:  # 回车键
                if self.selected_option == 0:  # 继续游戏
                    self.game_state = self.last_game_state
                    command = "continue"
                    print("Game Continue")
                elif self.selected_option == 1:  # 重新开始
                    command = "restart"
                    print("Restart Game")
                elif self.selected_option == 2:  # 退出游戏
                    command = "exit"
                    print("Exit Game")
            elif key == ord('1'):
                self.game_state = self.last_game_state
                command = "continue"
                print("Game Continue")
            elif key == ord('2'):
                command = "restart"
                print("Restart Game")
            elif key == ord('3'):
                command = "exit"
                print("Exit Game")
            elif key == 38:  # 上箭头
                self.selected_option = (self.selected_option - 1) % len(self.menu_options)
            elif key == 40:  # 下箭头
                self.selected_option = (self.selected_option + 1) % len(self.menu_options)
        
        elif self.game_state == "GAME_OVER":
            if key == ord('r') or key == ord('R'):
                command = "restart"
                print("Restart Game")
            elif key == 27:  # ESC键
                command = "exit"
                print("Exit Game")
        
        # 全局快捷键
        if key == ord('q') or key == ord('Q'):
            command = "exit"
            print("Exit Game")
        
        return command
    
    def render(self, frame, game_data, trajectories):
        """
        渲染完整游戏画面
        Args:
            frame: 基础视频帧（摄像头画面）
            game_data: 游戏数据字典
            trajectories: 手部轨迹数据
        Returns:
            rendered_frame: 渲染后的帧
        """
        # 创建渲染帧的副本
        rendered_frame = frame.copy()
        
        # 更新游戏状态
        self.game_state = game_data.get('game_state', self.game_state)
        
        # 绘制背景（使用摄像头画面作为基础）
        self.draw_background(rendered_frame)
        
        # 绘制水果（水果在背景之上）
        for fruit in game_data.get('fruit_list', []):
            self.draw_fruit(rendered_frame, fruit)
        
        # 绘制切割效果
        self.draw_cut_effects(rendered_frame, game_data.get('cut_effects', []))
        
        # 绘制爆炸效果
        self.draw_explosions(rendered_frame, game_data.get('explosions', []))
        
        # 绘制粒子效果
        self.draw_particles(rendered_frame)
        
        # 绘制手部轨迹（在水果之上，这样可以看到切割路径）
        self.draw_trajectories(rendered_frame, trajectories)
        
        # 绘制UI（最上层）
        self.draw_ui(rendered_frame, game_data)
        
        # 根据游戏状态绘制额外界面
        if self.game_state == "PAUSED":
            self.draw_pause_menu(rendered_frame)
        elif self.game_state == "GAME_OVER":
            self.draw_game_over(rendered_frame, game_data)
        
        # 更新FPS
        self.update_fps()
        
        return rendered_frame
    
    def cleanup(self):
        """清理资源"""
        cv2.destroyAllWindows()

# 测试代码
if __name__ == "__main__":
    print("界面渲染模块测试")
    print("按P键暂停，ESC退出")
    
    # 创建渲染器
    renderer = UIRenderer()
    
    # 创建测试用的游戏数据
    test_game_data = {
        'fruit_list': [],
        'cut_effects': [],
        'score': 150,
        'lives': 3,
        'max_score': 300,
        'game_state': 'RUNNING',
        'combo': 5,
        'difficulty_level': 3,
        'fruits_cut': 25,
        'bombs_avoided': 3,
        'max_combo': 8
    }
    
    # 创建测试用的轨迹数据
    test_trajectories = [
        ('Left', [(100, 100), (200, 150), (300, 120)]),
        ('Right', [(800, 200), (900, 250), (1000, 220)])
    ]
    
    # 创建测试帧
    test_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    
    try:
        while True:
            # 模拟游戏循环
            command = renderer.handle_keyboard_input()
            
            if command == "exit":
                break
            
            # 渲染画面
            rendered = renderer.render(test_frame.copy(), test_game_data, test_trajectories)
            
            # 显示画面
            cv2.imshow(renderer.window_name, rendered)
            
            # 添加一些测试水果
            if len(test_game_data['fruit_list']) < 5:
                import random
                from fruit_game import Fruit
                test_game_data['fruit_list'].append(
                    Fruit(random.randint(50, 1230), random.randint(50, 670))
                )
    
    except KeyboardInterrupt:
        print("测试中断")
    
    finally:
        renderer.cleanup()
        print("测试完成")