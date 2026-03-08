import random
import time
import pickle
import os
from collections import deque
import numpy as np

class Fruit:
    def __init__(self, x, y, fruit_type="normal"):
        """
        水果类 - 增强版
        Args:
            x: 初始x坐标
            y: 初始y坐标
            fruit_type: 水果类型 ("normal", "bomb", "combo")
        """
        self.x = x
        self.y = y
        self.type = fruit_type
        self.cut = False
        
        # 根据水果类型设置不同的下落速度（调整版，整体变慢）
        if self.type == "normal":
            # 普通水果：中等速度，有变化
            self.velocity_y = random.uniform(3.0, 4.5)
        elif self.type == "bomb":
            # 炸弹：稍慢，给玩家更多反应时间
            self.velocity_y = random.uniform(2.0, 3.5)
        elif self.type == "combo":
            # 连击水果：中等偏快
            self.velocity_y = random.uniform(3.5, 5.0)
        else:
            # 默认速度
            self.velocity_y = random.uniform(3.0, 4.5)
        
        self.velocity_x = random.uniform(-0.5, 0.5)  # 水平移动速度（轻微摆动）
        self.rotation = 0  # 旋转角度
        self.rotation_speed = random.uniform(-5, 5)  # 旋转速度
        self.size = random.randint(60, 80)  # 水果大小
        
        # 根据类型设置颜色和属性
        if self.type == "normal":
            self.color = self._get_random_fruit_color()
            self.points = 10
        elif self.type == "bomb":
            self.color = (50, 50, 50)  # 炸弹为灰色
            self.points = -1  # 扣生命
        elif self.type == "combo":
            self.color = (255, 0, 255)  # 紫色
            self.points = 20  # 连击奖励水果
            self.size = random.randint(65, 85)
        else:
            self.color = self._get_random_fruit_color()
            self.points = 10
    
    def _get_random_fruit_color(self):
        """获取随机水果颜色"""
        colors = [
            (255, 0, 0),    # 红色 - 苹果
            (255, 165, 0),  # 橙色 - 橙子
            (255, 255, 0),  # 黄色 - 香蕉
            (0, 255, 0),    # 绿色 - 西瓜
            (128, 0, 128),  # 紫色 - 葡萄
            (255, 192, 203) # 粉色 - 桃子
        ]
        return random.choice(colors)
    
    def update(self):
        """更新水果位置"""
        self.y += self.velocity_y
        self.x += self.velocity_x
        self.rotation += self.rotation_speed
        
        # 限制旋转角度在0-360之间
        if self.rotation >= 360:
            self.rotation -= 360
        elif self.rotation < 0:
            self.rotation += 360
        
    
    def is_out_of_bounds(self, screen_height):
        """检查水果是否超出屏幕底部"""
        return self.y > screen_height
    
    def get_bounding_circle(self):
        """获取水果的边界圆（用于碰撞检测）"""
        return (self.x, self.y, self.size // 2)

class FruitGame:
    def __init__(self, screen_width=1280, screen_height=720):
        """
        水果游戏逻辑类
        Args:
            screen_width: 屏幕宽度
            screen_height: 屏幕高度
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # 游戏状态
        self.game_state = "RUNNING"  # RUNNING, PAUSED, GAME_OVER
        self.score = 0
        self.lives = 10
        self.max_score = 0
        self.difficulty_level = 1
        
        # 水果管理
        self.fruits = []
        self.fruit_spawn_timer = 0
        self.fruit_spawn_interval = 1.2  # 初始生成间隔（秒）- 提速，更频繁生成
        self.fruits_per_spawn = 1  # 每次生成的水果数量
        
        # 水果类型概率
        self.bomb_probability = 0.08  # 炸弹概率固定为8%
        self.combo_probability = 0.03  # 连击水果概率
        
        # 水果速度范围（基础速度，会根据类型和难度调整）
        self.min_fruit_speed = 4.5
        self.max_fruit_speed = 7.0
        
        # 不同类型水果的速度倍数（用于难度调整）
        self.fruit_speed_multipliers = {
            "normal": 1.0,    # 普通水果：基准速度
            "bomb": 0.8,      # 炸弹：稍慢，但也要有挑战性
            "combo": 1.05     # 连击水果：稍快
        }
        
        # 切割效果
        self.cut_effects = []  # 存储切割效果（轨迹和水果的交互效果）
        
        # 爆炸效果
        self.explosions = []  # 存储爆炸效果
        
        # 游戏统计
        self.fruits_cut = 0
        self.bombs_avoided = 0
        self.combo = 0
        self.combo_timer = 0
        self.max_combo = 0
        
        # 加载最高分
        self.load_high_score()
    
    def load_high_score(self):
        """加载历史最高分"""
        try:
            if os.path.exists("assets/high_score.pkl"):
                with open("assets/high_score.pkl", "rb") as f:
                    self.max_score = pickle.load(f)
        except:
            self.max_score = 0
            print("无法加载最高分，将创建新的记录")
    
    def save_high_score(self):
        """保存最高分"""
        try:
            # 确保assets目录存在
            os.makedirs("assets", exist_ok=True)
            with open("assets/high_score.pkl", "wb") as f:
                pickle.dump(self.max_score, f)
        except Exception as e:
            print(f"保存最高分时出错: {e}")
    
    def spawn_fruit(self):
        """生成水果 - 增强版，支持多种水果类型"""
        # 随机x坐标（在屏幕内）
        x = random.randint(50, self.screen_width - 50)
        
        # 决定生成什么类型的水果
        rand = random.random()
        if rand < self.bomb_probability:
            fruit_type = "bomb"
        elif rand < self.bomb_probability + self.combo_probability:
            fruit_type = "combo"
        else:
            fruit_type = "normal"
        
        # 创建水果
        fruit = Fruit(x, -50, fruit_type)
        
        # 根据分数动态计算速度系数（0-200分更简单，之后匀速增长）
        # 0-200分：保持1.0x（更简单）
        # 200-1000分：从1.0x增长到1.10x（之前400分时的状态）
        # 1000分之后：保持1.10x不变
        capped_score = min(self.score, 1000)  # 1000分封顶
        if capped_score <= 200:
            score_based_speed_multiplier = 1.0  # 0-200分保持基础速度
        else:
            # 200-1000分匀速增长
            score_based_speed_multiplier = 1.0 + ((capped_score - 200) / 800) * 0.10
        type_multiplier = self.fruit_speed_multipliers.get(fruit_type, 1.0)  # 类型系数
        
        # 应用速度调整
        fruit.velocity_y *= score_based_speed_multiplier * type_multiplier
        fruit.velocity_x *= score_based_speed_multiplier * type_multiplier
        
        self.fruits.append(fruit)
    
    def update_difficulty(self):
        """根据得分更新难度 - 平滑提升版，基于分数动态调整"""
        # 根据分数计算当前难度等级（仅用于显示，每200分一级）
        new_level = int(self.score / 200) + 1
        
        if new_level > self.difficulty_level:
            self.difficulty_level = new_level
            
            # 根据分数动态调整特殊水果概率
            # 炸弹概率固定为8%，不再随分数变化
            self.bomb_probability = 0.08
            
            # 随着分数增加，特殊水果概率也增加（0-200分更低，之后匀速增长）
            capped_score = min(self.score, 1000)  # 1000分封顶
            if capped_score <= 200:
                # 0-200分：保持3%（更简单，连击水果更少）
                self.combo_probability = 0.03
            else:
                # 200-1000分：从3%增长到6%（之前400分时的状态）
                self.combo_probability = min(0.06, 0.03 + ((capped_score - 200) / 800) * 0.03)
    
    def check_collision(self, trajectories):
        """
        检查轨迹与水果的碰撞 - 修复版
        Args:
            trajectories: 手部轨迹列表，每个轨迹是一个(hand_label, trajectory)元组
        Returns:
            cut_fruits: 被切割的水果列表
        """
        cut_fruits = []
        
        # 调试信息：打印传入的轨迹数据
        #print(f"检查碰撞，轨迹数量: {len(trajectories)}")
        
        for hand_label, trajectory in trajectories:
            # 确保 trajectory 是坐标列表
            if not isinstance(trajectory, list) or len(trajectory) < 2:
                continue
            
            #print(f"  手部: {hand_label}, 轨迹点数: {len(trajectory)}")
            
            # 检查轨迹中的每一段与每个水果的碰撞
            for i in range(len(trajectory) - 1):
                point1 = trajectory[i]
                point2 = trajectory[i + 1]
                
                # 确保点是坐标元组
                if not isinstance(point1, (tuple, list)) or not isinstance(point2, (tuple, list)):
                    continue
                
                # 计算轨迹段的长度和方向
                dx = point2[0] - point1[0]
                dy = point2[1] - point1[1]
                segment_length = np.sqrt(dx*dx + dy*dy)
                
                # 如果轨迹段太短，跳过（可能是噪声）
                if segment_length < 5:
                    continue
                
                for fruit in self.fruits:
                    if not fruit.cut:
                        # 检查线段与水果的碰撞
                        if self._line_circle_collision(point1, point2, fruit.get_bounding_circle()):
                            fruit.cut = True
                            cut_fruits.append(fruit)
                            
                            # 添加切割效果
                            self._add_cut_effect(point1, point2, fruit)
                            
                            # 处理切割结果
                            self._handle_fruit_cut(fruit)
                            
                            # 一个轨迹段只能切割一个水果
                            break  # 跳出内层循环，继续检查下一个轨迹段
        
        #if cut_fruits:
         #   print(f"  切中 {len(cut_fruits)} 个水果!")
        
        return cut_fruits
    
    def _line_circle_collision(self, point1, point2, circle):
        """
        检查线段与圆的碰撞
        Args:
            point1: 线段起点 (x1, y1)
            point2: 线段终点 (x2, y2)
            circle: 圆 (cx, cy, radius)
        Returns:
            bool: 是否发生碰撞
        """
        cx, cy, radius = circle
        
        # 线段向量
        line_vec = (point2[0] - point1[0], point2[1] - point1[1])
        line_len = (line_vec[0]**2 + line_vec[1]**2)**0.5
        
        # 如果线段长度为0，检查点与圆的碰撞
        if line_len == 0:
            dist = ((cx - point1[0])**2 + (cy - point1[1])**2)**0.5
            return dist <= radius
        
        # 线段单位向量
        line_unit_vec = (line_vec[0] / line_len, line_vec[1] / line_len)
        
        # 圆心到线段起点的向量
        to_circle = (cx - point1[0], cy - point1[1])
        
        # 投影长度
        projection = to_circle[0] * line_unit_vec[0] + to_circle[1] * line_unit_vec[1]
        
        # 最近点在线段上的位置
        closest_point = (
            point1[0] + max(0, min(line_len, projection)) * line_unit_vec[0],
            point1[1] + max(0, min(line_len, projection)) * line_unit_vec[1]
        )
        
        # 计算最近点到圆心的距离
        dist = ((cx - closest_point[0])**2 + (cy - closest_point[1])**2)**0.5
        
        return dist <= radius
    
    def _add_cut_effect(self, point1, point2, fruit):
        """添加切割效果"""
        # 切割效果包含切割轨迹和水果位置
        effect = {
            "points": [point1, point2],
            "fruit_pos": (fruit.x, fruit.y),
            "fruit_type": fruit.type,
            "timer": 10  # 效果持续帧数
        }
        self.cut_effects.append(effect)
    
    def _handle_fruit_cut(self, fruit):
        """处理水果被切割的逻辑 - 增强版"""
        if fruit.type == "normal":
            # 普通水果：增加分数
            base_points = fruit.points
            
            # 连击奖励
            combo_bonus = min(50, self.combo * 2)  # 最大连击奖励50分
            
            # 计算总分
            points = base_points + combo_bonus
            self.score += points
            
            # 更新连击
            self.combo += 1
            self.combo_timer = 30  # 连击有效帧数
            self.fruits_cut += 1
            
            # 更新最大连击
            if self.combo > self.max_combo:
                self.max_combo = self.combo
            
        elif fruit.type == "combo":
            # 连击水果：延长连击时间并增加连击数
            base_points = fruit.points
            combo_bonus = min(50, self.combo * 2)
            points = base_points + combo_bonus
            self.score += points
            
            # 连击水果大幅增加连击数和时间
            self.combo += 3
            self.combo_timer = 50  # 更长的连击时间
            self.fruits_cut += 1
            
            if self.combo > self.max_combo:
                self.max_combo = self.combo
            
        else:  # bomb
            # 炸弹：减少生命值并触发爆炸
            self.lives -= 1
            self.combo = 0  # 连击中断
            
            # 添加爆炸效果
            self._add_explosion(fruit.x, fruit.y, fruit.size)
            
            # 检查爆炸范围内的其他水果（可选：爆炸可以清除附近的水果）
            self._check_explosion_range(fruit.x, fruit.y, fruit.size)
            
            print(f"切中炸弹! 生命值: {self.lives}")
            
            # 检查游戏是否结束
            if self.lives <= 0:
                self.game_state = "GAME_OVER"
                # 更新最高分
                if self.score > self.max_score:
                    self.max_score = self.score
                    self.save_high_score()
                    print(f"New Record! Highest Score: {self.max_score}")
    
    def update(self, trajectories, delta_time):
        """
        更新游戏状态
        Args:
            trajectories: 手部轨迹数据
            delta_time: 时间增量（秒）
        Returns:
            game_data: 游戏状态数据
        """
        # 更新连击计时器
        if self.combo_timer > 0:
            self.combo_timer -= 1
        else:
            self.combo = 0
        
        # 只在游戏运行时更新
        if self.game_state != "RUNNING":
            return self.get_game_data()
        
        # 根据分数动态计算生成间隔（0-200分更慢，之后匀速减少）
        # 0-200分：保持1.5秒（更简单，生成更慢）
        # 200-1000分：从1.5秒减少到1.44秒（之前400分时的状态）
        # 1000分之后：保持1.44秒不变
        capped_score = min(self.score, 1000)  # 1000分封顶
        if capped_score <= 200:
            dynamic_spawn_interval = 1.5  # 0-200分保持基础间隔
        else:
            # 200-1000分匀速减少
            dynamic_spawn_interval = max(0.5, 1.5 - ((capped_score - 200) / 800) * 0.06)
        
        # 更新水果生成计时器
        self.fruit_spawn_timer += delta_time
        if self.fruit_spawn_timer >= dynamic_spawn_interval:
            # 根据分数计算每次生成的水果数量（0-200分更简单）
            # 0-200分：1个（更简单）
            # 200-1000分：从2个增长到3个（之前400分时的状态）
            # 1000分之后：保持3个不变
            capped_score_for_count = min(self.score, 1000)  # 1000分封顶
            if capped_score_for_count <= 200:
                dynamic_fruits_per_spawn = 1  # 0-200分只生成1个，更简单
            elif capped_score_for_count < 600:
                dynamic_fruits_per_spawn = 2  # 200-599分：2个
            elif capped_score_for_count < 1000:
                # 600-999分：逐渐从2个增加到3个
                dynamic_fruits_per_spawn = 2 + int((capped_score_for_count - 600) / 400)
            else:
                dynamic_fruits_per_spawn = 3  # 1000分及以上：3个
            
            for _ in range(dynamic_fruits_per_spawn):
                self.spawn_fruit()
            self.fruit_spawn_timer = 0
        
        # 更新所有水果位置
        for fruit in self.fruits:
            fruit.update()
        
        # 移除超出屏幕的水果（未被切割的普通水果会扣生命）
        fruits_to_remove = []
        for fruit in self.fruits:
            if fruit.is_out_of_bounds(self.screen_height):
                fruits_to_remove.append(fruit)
                if not fruit.cut and fruit.type == "normal":
                    self.lives -= 1
                    self.combo = 0  # 连击中断
                    print(f"Fruit Dropped! Lives: {self.lives}")
                    
                    # 检查游戏是否结束
                    if self.lives <= 0:
                        self.game_state = "GAME_OVER"
                        # 更新最高分
                        if self.score > self.max_score:
                            self.max_score = self.score
                            self.save_high_score()
                            print(f"New Record! Highest Score: {self.max_score}")
        
        # 移除超出屏幕的水果和已被切割的水果
        self.fruits = [f for f in self.fruits if f not in fruits_to_remove and not f.cut]
        
        # 检查碰撞
        self.check_collision(trajectories)
        
        # 更新切割效果
        self._update_cut_effects()
        
        # 更新爆炸效果
        self._update_explosions()
        
        # 更新难度（概率等，速度已在spawn_fruit中动态计算）
        self.update_difficulty()
        
        return self.get_game_data()
    
    def _update_cut_effects(self):
        """更新切割效果"""
        effects_to_remove = []
        for effect in self.cut_effects:
            effect["timer"] -= 1
            if effect["timer"] <= 0:
                effects_to_remove.append(effect)
        
        self.cut_effects = [e for e in self.cut_effects if e not in effects_to_remove]
    
    def _add_explosion(self, x, y, size):
        """添加爆炸效果 - 大量红色粒子喷涌"""
        explosion_radius = size * 1.5  # 爆炸范围是水果大小的1.5倍
        explosion = {
            "x": x,
            "y": y,
            "max_radius": explosion_radius,
            "timer": 30,  # 爆炸持续30帧
            "max_timer": 30,
            "particles": []  # 爆炸粒子
        }
        
        # 生成大量红色粒子（30-40个）
        particle_count = random.randint(30, 40)
        for _ in range(particle_count):
            angle = random.random() * 2 * np.pi
            # 速度更快，更分散
            speed = random.uniform(5, 12)
            particle = {
                "x": x + random.uniform(-size * 0.3, size * 0.3),  # 小范围内随机起始位置
                "y": y + random.uniform(-size * 0.3, size * 0.3),
                "vx": np.cos(angle) * speed,
                "vy": np.sin(angle) * speed,
                "lifetime": random.randint(20, 35),
                "max_lifetime": random.randint(20, 35),
                "size": random.randint(4, 8),
                "color": random.choice([
                    (255, 50, 0),    # 深红色
                    (255, 80, 0),    # 红色
                    (255, 120, 0),   # 橙红色
                    (255, 0, 0),     # 纯红色
                    (200, 30, 0)     # 暗红色
                ])
            }
            explosion["particles"].append(particle)
        
        self.explosions.append(explosion)
    
    def _update_explosions(self):
        """更新爆炸效果"""
        explosions_to_remove = []
        for explosion in self.explosions:
            explosion["timer"] -= 1
            
            # 更新粒子
            particles_to_remove = []
            for particle in explosion["particles"]:
                particle["x"] += particle["vx"]
                particle["y"] += particle["vy"]
                particle["vy"] += 0.2  # 轻微重力效果
                particle["vx"] *= 0.98  # 轻微阻力，让粒子逐渐减速
                particle["lifetime"] -= 1
                
                if particle["lifetime"] <= 0:
                    particles_to_remove.append(particle)
            
            # 移除生命周期结束的粒子
            explosion["particles"] = [p for p in explosion["particles"] if p not in particles_to_remove]
            
            # 如果所有粒子都消失了，移除爆炸效果
            if explosion["timer"] <= 0 or len(explosion["particles"]) == 0:
                explosions_to_remove.append(explosion)
        
        self.explosions = [e for e in self.explosions if e not in explosions_to_remove]
    
    def _check_explosion_range(self, x, y, size):
        """检查爆炸范围内的其他水果（可选功能：爆炸可以清除附近的水果）"""
        explosion_radius = size * 1.5
        for fruit in self.fruits:
            if fruit.cut or fruit.type == "bomb":
                continue
            
            # 计算距离
            distance = np.sqrt((fruit.x - x)**2 + (fruit.y - y)**2)
            
            # 如果在爆炸范围内，标记为被切割（可选）
            # 如果不想让爆炸清除其他水果，可以注释掉下面的代码
            if distance < explosion_radius:
                fruit.cut = True
                # 添加切割效果
                self._add_cut_effect((fruit.x, fruit.y), (fruit.x, fruit.y), fruit)
                # 处理切割逻辑（但不给分，因为是爆炸清除的）
                # self._handle_fruit_cut(fruit)  # 取消注释如果想让爆炸清除的水果也给分
    
    def get_game_data(self):
        """
        获取游戏状态数据（供界面渲染模块使用）
        Returns:
            game_data: 游戏状态字典
        """
        return {
            "fruit_list": self.fruits,
            "cut_effects": self.cut_effects,
            "explosions": self.explosions,
            "score": self.score,
            "lives": self.lives,
            "max_score": self.max_score,
            "game_state": self.game_state,
            "combo": self.combo,
            "difficulty_level": self.difficulty_level,
            "fruits_cut": self.fruits_cut,
            "bombs_avoided": self.bombs_avoided,
            "max_combo": self.max_combo
        }
    
    def handle_user_input(self, command):
        """
        处理用户输入
        Args:
            command: 用户命令 ("continue", "restart", "exit")
        """

        if command == "pause":
            # 切换暂停/继续状态
            if self.game_state == "RUNNING":
                self.game_state = "PAUSED"
                print("Game Paused")
            elif self.game_state == "PAUSED":
                self.game_state = "RUNNING"
                print("Game Continue")

        elif command == "continue":
            if self.game_state == "PAUSED":
                self.game_state = "RUNNING"
                print("Game Continue")
            elif self.game_state == "RUNNING":
                self.game_state = "PAUSED"
                print("Game Paused")
        
        elif command == "restart":
            self.reset_game()
            print("Game Restart")
        
        elif command == "exit":
            # 保存最高分
            if self.score > self.max_score:
                self.max_score = self.score
                self.save_high_score()
            print("Exit Game")
    
    def reset_game(self):
        """重置游戏状态"""
        self.game_state = "RUNNING"
        self.score = 0
        self.lives = 3
        self.difficulty_level = 1
        self.fruits = []
        self.cut_effects = []
        self.explosions = []
        self.fruit_spawn_timer = 0
        self.fruit_spawn_interval = 1.2  # 基础间隔，实际会根据分数动态计算
        self.bomb_probability = 0.08  # 炸弹概率固定为8%
        self.combo_probability = 0.03
        self.combo = 0
        self.combo_timer = 0
        self.fruits_cut = 0
        self.bombs_avoided = 0
        self.max_combo = 0

# 测试代码
if __name__ == "__main__":
    print("水果游戏逻辑模块测试")
    
    # 创建游戏实例
    game = FruitGame()
    
    # 模拟一些轨迹数据
    test_trajectories = [
        [(100, 100), (200, 200), (300, 150)],  # 轨迹1
        [(500, 300), (600, 400)]               # 轨迹2
    ]
    
    # 生成一些测试水果
    for i in range(5):
        game.spawn_fruit()
    
    # 模拟游戏循环
    print("模拟游戏更新...")
    for i in range(10):
        game_data = game.update(test_trajectories, 0.1)
        print(f"帧 {i+1}: 分数={game_data['score']}, 生命={game_data['lives']}, 水果数量={len(game_data['fruit_list'])}")
        time.sleep(0.1)
    
    print("测试完成")