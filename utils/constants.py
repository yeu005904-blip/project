# 游戏常量定义

# 屏幕尺寸
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

# 颜色定义
BACKGROUND_COLOR = (25, 25, 50)  # 深蓝色背景
TEXT_COLOR = (255, 255, 255)     # 白色文字
COMBO_COLOR = (255, 215, 0)      # 金色连击文字

# 水果颜色
FRUIT_COLORS = {
    "apple": (255, 0, 0),
    "orange": (255, 165, 0),
    "banana": (255, 255, 0),
    "watermelon": (0, 255, 0),
    "grape": (128, 0, 128),
    "peach": (255, 192, 203)
}

# 游戏参数
INITIAL_LIVES = 3
INITIAL_SPAWN_INTERVAL = 1.0  # 初始水果生成间隔（秒）
BOMB_PROBABILITY = 0.1        # 初始炸弹概率
POINTS_PER_FRUIT = 10         # 每个水果基础分数

# 难度参数
DIFFICULTY_INCREASE_SCORE = 20  # 每20分增加一次难度
SPAWN_INTERVAL_DECREASE = 0.1   # 每次难度增加减少的生成间隔
BOMB_PROBABILITY_INCREASE = 0.05  # 每次难度增加的炸弹概率增量
MAX_BOMB_PROBABILITY = 0.3     # 最大炸弹概率
MIN_SPAWN_INTERVAL = 0.3       # 最小生成间隔

# 连击系统
COMBO_DURATION = 30            # 连击有效帧数
MAX_COMBO_BONUS = 50          # 最大连击奖励分数