import cv2
import mediapipe as mp
import numpy as np
from collections import deque
import time

class HandTracker:
    def __init__(self, max_hands=2, detection_confidence=0.5, tracking_confidence=0.3):
        """
        初始化手部跟踪器 - 专门用于切水果的手掌侧面检测
        Args:
            max_hands: 最大检测手部数量（设置为2支持双手）
            detection_confidence: 检测置信度阈值（降低以提高灵敏度）
            tracking_confidence: 跟踪置信度阈值（降低以提高灵敏度）
        """
        self.max_hands = max_hands
        self.detection_confidence = detection_confidence
        self.tracking_confidence = tracking_confidence
    
        # 初始化MediaPipe Hands
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=self.max_hands,
            min_detection_confidence=self.detection_confidence,
            min_tracking_confidence=self.tracking_confidence
        )
    
        # 轨迹存储：基于手部类型（Left/Right）而不是索引
        # 缩短轨迹留存时间
        self.trajectories = {
            'Left': deque(maxlen=8),  # 从15减少到8
            'Right': deque(maxlen=8)
        }
        self.trajectories_smooth = {
            'Left': deque(maxlen=6),  # 从10减少到6
            'Right': deque(maxlen=6)
        }
    
        # 手部位置缓存，用于稳定手部识别
        self.hand_positions = {
            'Left': None,
            'Right': None
        }
    
        # 新增：手部消失计数器
        self.hand_missing_count = {
            'Left': 0,
            'Right': 0
        }
        self.max_missing_frames = 3  # 手部消失后保留轨迹的帧数
    
        # 轨迹参数 - 调整灵敏度
        self.min_trajectory_length = 2  # 进一步减少，提高响应速度
        self.min_cut_speed = 3  # 进一步降低，提高灵敏度
    
        # 摄像头参数
        self.cap = None
        self.frame_width = 1280
        self.frame_height = 720
    
        # 性能监控
        self.fps = 0
        self.frame_count = 0
        self.start_time = time.time()
    
        # 颜色配置（为不同手分配不同颜色）
        self.hand_colors = {
            'Left': (0, 255, 0),    # 绿色 - 左手
            'Right': (255, 0, 0)    # 蓝色 - 右手
        }
    
        # 窗口管理
        self.fullscreen = False
    
        # 手部跟踪稳定性
        self.hand_tracking_threshold = 150  # 像素距离阈值，用于区分不同手部（增大以提高稳定性）
        
        # 双手识别优化：使用更稳定的跟踪策略
        self.hand_tracking_history = {
            'Left': deque(maxlen=5),  # 左手位置历史
            'Right': deque(maxlen=5)   # 右手位置历史
        }
        
    def initialize_camera(self):
        """初始化摄像头"""
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            # 尝试其他摄像头索引
            self.cap = cv2.VideoCapture(1)
            if not self.cap.isOpened():
                raise Exception("无法打开摄像头")
        
        # 设置摄像头参数
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        # 获取实际分辨率
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"摄像头实际分辨率: {actual_width}x{actual_height}")
        
        return True
    
    def get_knife_edge_center(self, hand_landmarks):
        """
        获取小拇指到腕部中心点的轨迹点
        使用小拇指侧面关键点(17,18,19,20)和手腕(0)的中心点
        """
        # 小拇指侧面的关键点和手腕
        edge_indices = [0, 17, 18, 19, 20]
        
        # 计算这些点的中心
        x_sum = 0
        y_sum = 0
        count = 0
        
        for idx in edge_indices:
            landmark = hand_landmarks.landmark[idx]
            x_sum += landmark.x
            y_sum += landmark.y
            count += 1
        
        if count > 0:
            center_x = x_sum / count
            center_y = y_sum / count
            x = int(center_x * self.frame_width)
            y = int(center_y * self.frame_height)
            return (x, y)
        
        # 如果计算失败，回退到小指尖端
        tip = hand_landmarks.landmark[20]
        return (int(tip.x * self.frame_width), int(tip.y * self.frame_height))
    
    def calculate_cutting_velocity(self, trajectory):
        """计算切割速度"""
        if len(trajectory) < 2:
            return 0
        
        velocities = []
        for i in range(1, len(trajectory)):
            dx = trajectory[i][0] - trajectory[i-1][0]
            dy = trajectory[i][1] - trajectory[i-1][1]
            distance = np.sqrt(dx**2 + dy**2)
            velocities.append(distance)
        
        return np.mean(velocities) if velocities else 0
    
    def is_valid_cut(self, trajectory):
        """判断是否为有效的切割动作 - 优化版，提高灵敏度"""
        if len(trajectory) < 2:
            return False, None
        
        # 计算速度，使用最近的点对以提高响应速度
        if len(trajectory) >= 2:
            recent_velocity = self.calculate_cutting_velocity(trajectory[-min(3, len(trajectory)):])
            if recent_velocity >= self.min_cut_speed:
                start_point = trajectory[0]
                end_point = trajectory[-1]
                dx = end_point[0] - start_point[0]
                dy = end_point[1] - start_point[1]
                
                if abs(dx) > abs(dy):
                    direction = "horizontal"
                else:
                    direction = "vertical"
                return True, direction
        
        # 也检查整体速度
        velocity = self.calculate_cutting_velocity(trajectory)
        if velocity < self.min_cut_speed:
            return False, None
        
        start_point = trajectory[0]
        end_point = trajectory[-1]
        dx = end_point[0] - start_point[0]
        dy = end_point[1] - start_point[1]
        
        if abs(dx) > abs(dy):
            direction = "horizontal"
        else:
            direction = "vertical"
        
        return True, direction
    
    def smooth_trajectory(self, trajectory):
        """使用加权移动平均法平滑轨迹 - 优化版，减少延迟"""
        if len(trajectory) < 2:
            return trajectory
        
        # 对于短轨迹，使用更轻的平滑
        if len(trajectory) == 2:
            return trajectory
        
        smoothed = []
        # 使用更轻的平滑，优先保持最新点的准确性
        for i in range(len(trajectory)):
            if i == 0:
                # 第一个点保持原样
                smoothed.append(trajectory[i])
            elif i == len(trajectory) - 1:
                # 最后一个点（最新点）保持原样，减少延迟
                smoothed.append(trajectory[i])
            else:
                # 中间点使用轻量平滑
                prev_point = trajectory[i-1]
                curr_point = trajectory[i]
                next_point = trajectory[i+1] if i+1 < len(trajectory) else curr_point
                
                # 加权平均：当前点权重最高
                avg_x = int(prev_point[0] * 0.2 + curr_point[0] * 0.6 + next_point[0] * 0.2)
                avg_y = int(prev_point[1] * 0.2 + curr_point[1] * 0.6 + next_point[1] * 0.2)
                smoothed.append((avg_x, avg_y))
        
        return smoothed
    
    def get_hand_label(self, index, hand_landmarks, results):
        """获取手部标签（左手/右手）"""
        if not results.multi_handedness:
            # 如果没有手部标签信息，根据手部位置猜测
            wrist_x = hand_landmarks.landmark[0].x
            return 'Left' if wrist_x < 0.5 else 'Right'
        
        for idx, classification in enumerate(results.multi_handedness):
            if idx == index:
                label = classification.classification[0].label
                return str(label)
        
        # 如果找不到对应索引，根据手部位置猜测
        wrist_x = hand_landmarks.landmark[0].x
        return 'Left' if wrist_x < 0.5 else 'Right'
    
    def stabilize_hand_tracking(self, results):
        """
        稳定手部跟踪，防止左右手识别跳跃和轨迹交叉 - 优化版
        Args:
            results: MediaPipe检测结果
        Returns:
            stabilized_hands: 稳定后的手部列表，每个元素是(hand_label, position)
        """
        stabilized_hands = []

        if not results.multi_hand_landmarks:
            return stabilized_hands

        # 确保hand_positions字典存在所有需要的键
        for label in ['Left', 'Right']:
            if label not in self.hand_positions:
                self.hand_positions[label] = None

        # 获取当前帧检测到的手部
        detected_hands = []
        for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
            if hand_idx >= self.max_hands:
                break
            
            # 获取手部标签和位置
            hand_label = self.get_hand_label(hand_idx, hand_landmarks, results)
            position = self.get_knife_edge_center(hand_landmarks)
        
            # 由于镜像显示，需要调整x坐标
            position = (self.frame_width - position[0], position[1])
            detected_hands.append((hand_label, position))

        # 如果没有检测到手部，直接返回
        if not detected_hands:
            return stabilized_hands

        # 如果有两只手，使用改进的稳定分配算法
        if len(detected_hands) == 2:
            # 根据x坐标排序：左边的应该是左手，右边的应该是右手
            sorted_hands = sorted(detected_hands, key=lambda h: h[1][0])
            left_candidate_pos = sorted_hands[0][1]
            right_candidate_pos = sorted_hands[1][1]
            
            # 使用历史位置进行更准确的匹配
            if self.hand_positions['Left'] is not None and self.hand_positions['Right'] is not None:
                # 计算两个候选位置到历史位置的距离
                left_to_left = np.sqrt(
                    (left_candidate_pos[0] - self.hand_positions['Left'][0])**2 +
                    (left_candidate_pos[1] - self.hand_positions['Left'][1])**2
                )
                left_to_right = np.sqrt(
                    (left_candidate_pos[0] - self.hand_positions['Right'][0])**2 +
                    (left_candidate_pos[1] - self.hand_positions['Right'][1])**2
                )
                right_to_left = np.sqrt(
                    (right_candidate_pos[0] - self.hand_positions['Left'][0])**2 +
                    (right_candidate_pos[1] - self.hand_positions['Left'][1])**2
                )
                right_to_right = np.sqrt(
                    (right_candidate_pos[0] - self.hand_positions['Right'][0])**2 +
                    (right_candidate_pos[1] - self.hand_positions['Right'][1])**2
                )
                
                # 选择总距离最小的分配方案
                # 方案1: 左边候选->左手, 右边候选->右手
                scheme1_distance = left_to_left + right_to_right
                # 方案2: 左边候选->右手, 右边候选->左手
                scheme2_distance = left_to_right + right_to_left
                
                if scheme2_distance < scheme1_distance * 0.7:  # 如果方案2明显更好，交换
                    stabilized_hands.append(('Right', left_candidate_pos))
                    stabilized_hands.append(('Left', right_candidate_pos))
                else:
                    stabilized_hands.append(('Left', left_candidate_pos))
                    stabilized_hands.append(('Right', right_candidate_pos))
            else:
                # 没有历史位置，直接根据x坐标分配
                stabilized_hands.append(('Left', left_candidate_pos))
                stabilized_hands.append(('Right', right_candidate_pos))
        else:
            # 只有一只手，使用历史位置或位置判断
            hand_label, position = detected_hands[0]
            
            # 如果有历史位置，选择距离更近的标签
            if self.hand_positions['Left'] is not None and self.hand_positions['Right'] is not None:
                dist_to_left = np.sqrt(
                    (position[0] - self.hand_positions['Left'][0])**2 +
                    (position[1] - self.hand_positions['Left'][1])**2
                )
                dist_to_right = np.sqrt(
                    (position[0] - self.hand_positions['Right'][0])**2 +
                    (position[1] - self.hand_positions['Right'][1])**2
                )
                hand_label = 'Left' if dist_to_left < dist_to_right else 'Right'
            else:
                # 根据x位置判断
                hand_label = 'Left' if position[0] < self.frame_width // 2 else 'Right'
            
            stabilized_hands.append((hand_label, position))

        # 更新位置缓存和历史
        for hand_label in ['Left', 'Right']:
            latest_position = None
            for label, pos in stabilized_hands:
                if label == hand_label:
                    latest_position = pos
                    break
            self.hand_positions[hand_label] = latest_position
            if latest_position is not None:
                self.hand_tracking_history[hand_label].append(latest_position)

        return stabilized_hands

    def filter_trajectory_crossing(self):
        """过滤轨迹，防止左右手轨迹交叉"""
        for hand_label in ['Left', 'Right']:
            if len(self.trajectories[hand_label]) >= 2:
                # 确保轨迹点符合手部的一般运动范围
                trajectory = list(self.trajectories[hand_label])
                cleaned_trajectory = []
                
                for point in trajectory:
                    # 根据手部标签过滤异常点
                    if hand_label == 'Left' and point[0] > self.frame_width * 0.6:
                        # 左手不应该出现在屏幕右侧60%的区域
                        continue
                    elif hand_label == 'Right' and point[0] < self.frame_width * 0.4:
                        # 右手不应该出现在屏幕左侧40%的区域
                        continue
                    cleaned_trajectory.append(point)
                
                if cleaned_trajectory:
                    self.trajectories[hand_label] = deque(cleaned_trajectory, maxlen=8)

    def process_frame(self):
        """
        处理单帧图像，检测双手并更新轨迹
        Returns:
            cut_trajectories: 切割轨迹列表，每个元素是(hand_label, trajectory)
            frame: 处理后的帧（镜像显示）
            hands_detected: 检测到的手部数量
        """
        if not self.cap or not self.cap.isOpened():
            return [], None, 0

        success, frame = self.cap.read()
        if not success:
            return [], None, 0

        # 更新FPS计算
        self.frame_count += 1
        if self.frame_count % 30 == 0:
            end_time = time.time()
            self.fps = 30 / (end_time - self.start_time)
            self.start_time = end_time

        # 转换颜色空间 BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False

        # 手部检测
        results = self.hands.process(rgb_frame)

        # 恢复可写状态
        rgb_frame.flags.writeable = True
        debug_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)

        # 创建镜像显示 - 水平翻转帧
        debug_frame = cv2.flip(debug_frame, 1)

        hands_detected = 0
        current_trajectories = []  # 存储(hand_label, trajectory)

        # 创建一个集合来记录当前帧检测到的手部标签
        detected_hands_in_current_frame = set()

        if results.multi_hand_landmarks:
            hands_detected = len(results.multi_hand_landmarks)
        
            # 稳定手部跟踪
            stabilized_hands = self.stabilize_hand_tracking(results)
        
            for hand_label, position in stabilized_hands:
                # 记录当前帧检测到的手
                detected_hands_in_current_frame.add(hand_label)
                # 重置该手的消失计数器
                self.hand_missing_count[hand_label] = 0
            
                # 更新轨迹 - 基于手部标签
                self.trajectories[hand_label].append(position)
            
                # 绘制刀锋中心点（小圆点）
                cv2.circle(debug_frame, position, 6, self.hand_colors[hand_label], -1)

        # 更新未检测到的手的计数器
        for hand_label in ['Left', 'Right']:
            if hand_label not in detected_hands_in_current_frame:
                self.hand_missing_count[hand_label] += 1

        # 轨迹处理 - 基于手部标签处理
        for hand_label in ['Left', 'Right']:
            # 只有当手部存在或刚消失几帧时才绘制轨迹
            if self.hand_missing_count[hand_label] <= self.max_missing_frames:
                if len(self.trajectories[hand_label]) >= 2:
                    # 确保轨迹是坐标列表
                    trajectory = list(self.trajectories[hand_label])
                    
                    # 清理轨迹数据，确保每个点都是坐标元组
                    clean_trajectory = []
                    for point in trajectory:
                        if isinstance(point, tuple) and len(point) == 2:
                            # 检查是否是数字
                            if isinstance(point[0], (int, float)) and isinstance(point[1], (int, float)):
                                clean_trajectory.append((int(point[0]), int(point[1])))
                    
                    if len(clean_trajectory) >= 2:
                        smoothed_trajectory = self.smooth_trajectory(clean_trajectory)
                        self.trajectories_smooth[hand_label] = deque(smoothed_trajectory, maxlen=8)
                    
                        is_valid, direction = self.is_valid_cut(smoothed_trajectory)
                    
                        # 降低有效切割的条件，提高灵敏度
                        if len(smoothed_trajectory) >= self.min_trajectory_length:
                            self.filter_trajectory_crossing()
                            # 存储时包含手部标签，确保格式正确
                            current_trajectories.append((hand_label, smoothed_trajectory))
                        
                            # 绘制该手的独立轨迹
                            for i in range(1, len(smoothed_trajectory)):
                                color = self.hand_colors[hand_label]
                                point1 = smoothed_trajectory[i-1]
                                point2 = smoothed_trajectory[i]
                                # 根据速度调整线条粗细
                                velocity = self.calculate_cutting_velocity(smoothed_trajectory[max(0, i-2):i+1])
                                thickness = max(2, min(5, int(velocity / 5)))
                                cv2.line(debug_frame, point1, point2, color, thickness)
            else:
                # 手部消失超过阈值，清空轨迹
                self.trajectories[hand_label].clear()
                self.trajectories_smooth[hand_label].clear()

        # 确保返回格式正确：[(hand_label, [(x1,y1), (x2,y2), ...]), ...]
        return current_trajectories, debug_frame, hands_detected
    
    def get_trajectory_data(self):
        """
        获取当前切割轨迹数据（供其他模块调用）
        Returns:
            cut_trajectories: 切割轨迹列表，每个元素是(hand_label, trajectory)
        """
        valid_trajectories = []
        for hand_label in ['Left', 'Right']:
            if len(self.trajectories_smooth[hand_label]) >= self.min_trajectory_length:
                # 确保轨迹是列表格式，不是deque
                trajectory_list = list(self.trajectories_smooth[hand_label])
                # 确保每个点是坐标元组
                clean_trajectory = []
                for point in trajectory_list:
                    if isinstance(point, tuple) and len(point) == 2:
                        if isinstance(point[0], (int, float)) and isinstance(point[1], (int, float)):
                            clean_trajectory.append((int(point[0]), int(point[1])))
                
                if len(clean_trajectory) >= self.min_trajectory_length:
                    valid_trajectories.append((hand_label, clean_trajectory))
        
        return valid_trajectories
    
    def toggle_fullscreen(self, window_name):
        """切换全屏模式"""
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        else:
            cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
        return self.fullscreen
    
    def clear_trajectories(self):
        """清空所有轨迹"""
        for hand_label in ['Left', 'Right']:
            self.trajectories[hand_label].clear()
            self.trajectories_smooth[hand_label].clear()
            self.hand_tracking_history[hand_label].clear()
        # 同时清空位置缓存
        self.hand_positions = {'Left': None, 'Right': None}
    
    def release(self):
        """释放资源"""
        if self.cap:
            self.cap.release()
        if self.hands:
            self.hands.close()

# 简洁的测试代码
if __name__ == "__main__":
    print("初始化手部跟踪器...")
    tracker = HandTracker(max_hands=2)
    
    try:
        if tracker.initialize_camera():
            window_name = 'Improved Hand Tracker'
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(window_name, 1200, 800)
            
            print("改进版双手刀锋轨迹检测测试中...")
            print("主要改进:")
            print("  1. 使用小拇指到腕部中心点轨迹，更稳定")
            print("  2. 缩短轨迹留存时间")
            print("  3. 提高快速移动识别灵敏度")
            print("操作说明:")
            print("  'q' - 退出程序")
            print("  'f' - 切换全屏")
            print("  'c' - 清空所有轨迹")
            print("  用手掌侧面做切割动作进行测试")
            
            while True:
                trajectories, frame, hands_detected = tracker.process_frame()
                
                if frame is not None:
                    cv2.imshow(window_name, frame)
                
                # 键盘事件处理
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:  # q 或 ESC
                    print("退出程序...")
                    break
                elif key == ord('f'):
                    fullscreen = tracker.toggle_fullscreen(window_name)
                    print(f"全屏模式: {'开启' if fullscreen else '关闭'}")
                elif key == ord('c'):
                    tracker.clear_trajectories()
                    print("所有轨迹已清空")
    
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        tracker.release()
        cv2.destroyAllWindows()