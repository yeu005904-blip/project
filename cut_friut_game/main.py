import cv2
import time
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hand_tracker import HandTracker
from fruit_game import FruitGame
from ui_renderer import UIRenderer

class FruitNinjaGame:
    def __init__(self):
        """初始化切水果游戏"""
        # 屏幕尺寸
        self.screen_width = 1280
        self.screen_height = 720
        
        # 初始化各模块
        print("正在初始化切水果游戏...")
        
        # 手部跟踪模块
        print("初始化手部跟踪模块...")
        self.hand_tracker = HandTracker(max_hands=2)
        
        # 游戏逻辑模块
        print("初始化游戏逻辑模块...")
        self.fruit_game = FruitGame(self.screen_width, self.screen_height)
        
        # 界面渲染模块
        print("初始化界面渲染模块...")
        self.ui_renderer = UIRenderer(self.screen_width, self.screen_height)
        
        # 游戏状态
        self.running = True
        self.last_update_time = time.time()
        
        print("游戏初始化完成!")
    
    def initialize(self):
        """初始化游戏"""
        try:
            # 初始化摄像头
            if not self.hand_tracker.initialize_camera():
                print("摄像头初始化失败")
                return False
            
            print("\n游戏操作说明:")
            print("=" * 40)
            print("游戏控制:")
            print("  P 键 - 暂停/继续游戏")
            print("  F 键 - 切换全屏模式")
            print("  Q 键 - 退出游戏")
            print()
            print("暂停菜单操作:")
            print("  1 键 - 继续游戏")
            print("  2 键 - 重新开始")
            print("  3 键 - 退出游戏")
            print("  ↑↓键 - 选择菜单选项")
            print("  回车 - 确认选择")
            print("  ESC  - 返回游戏")
            print()
            print("游戏结束操作:")
            print("  R 键 - 重新开始")
            print("  ESC  - 退出游戏")
            print("=" * 40)
            print("\n游戏开始! 请用手掌侧面做切割动作...")
            
            return True
        
        except Exception as e:
            print(f"初始化失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run(self):
        """运行游戏主循环"""
        if not self.initialize():
            return
        
        try:
            while self.running:
                # 计算时间增量
                current_time = time.time()
                delta_time = current_time - self.last_update_time
                self.last_update_time = current_time
                
                # 处理手部跟踪
                trajectories, camera_frame, hands_detected = self.hand_tracker.process_frame()
                
                if camera_frame is None:
                    print("无法获取摄像头画面")
                    break
                
                # 调试信息：打印轨迹数据格式
                #if trajectories:
                 #   print(f"轨迹数量: {len(trajectories)}")
                  #  for i, (hand_label, trajectory) in enumerate(trajectories):
                   #     print(f"  轨迹{i+1}: 手部={hand_label}, 点数={len(trajectory)}")
                
                # 处理游戏逻辑
                game_data = self.fruit_game.update(trajectories, delta_time)
                
                # 处理用户输入
                command = self.ui_renderer.handle_keyboard_input()
                if command:
                    self.handle_command(command)
                
                # 渲染游戏画面
                rendered_frame = self.ui_renderer.render(camera_frame, game_data, trajectories)
                
                # 显示游戏画面
                cv2.imshow(self.ui_renderer.window_name, rendered_frame)
                
                # 检查窗口是否被关闭
                if cv2.getWindowProperty(self.ui_renderer.window_name, cv2.WND_PROP_VISIBLE) < 1:
                    print("窗口已关闭")
                    break
                
                # 添加调试显示手部数量
                #if hands_detected > 0:
                 #   cv2.putText(rendered_frame, f"检测到手部: {hands_detected}", 
                  #             (self.screen_width - 300, self.screen_height - 50),
                   #            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        except KeyboardInterrupt:
            print("游戏被中断")
        
        except Exception as e:
            print(f"游戏运行错误: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            self.cleanup()
    
    def handle_command(self, command):
        """处理用户命令"""
        if command == "continue":
            # 继续游戏
            self.fruit_game.handle_user_input("continue")
        
        elif command == "restart":
            # 重新开始游戏
            self.fruit_game.handle_user_input("restart")
            # 清空手部轨迹
            self.hand_tracker.clear_trajectories()
        
        elif command == "exit":
            # 退出游戏
            self.fruit_game.handle_user_input("exit")
            self.running = False
        
        elif command == "pause":
            # 暂停游戏 - 这里需要调用 handle_user_input("pause") 或直接设置状态
            # 由于 FruitGame 没有单独的 pause 命令，可以直接设置游戏状态
            if self.fruit_game.game_state == "RUNNING":
                self.fruit_game.game_state = "PAUSED"
                print("Game Paused")
            else:
                self.fruit_game.game_state = "RUNNING"
                print("Game Continue")
    
    def cleanup(self):
        """清理资源"""
        print("正在清理资源...")
        
        # 保存最高分
        if self.fruit_game.score > self.fruit_game.max_score:
            self.fruit_game.max_score = self.fruit_game.score
            self.fruit_game.save_high_score()
            print(f"保存最高分: {self.fruit_game.max_score}")
        
        # 释放资源
        self.hand_tracker.release()
        self.ui_renderer.cleanup()
        
        print("游戏结束")

def main():
    """主函数"""
    print("=" * 50)
    print("切水果游戏")
    print("=" * 50)
    
    # 检查依赖
    try:
        import mediapipe
        import numpy
        import cv2
    except ImportError as e:
        print(f"缺少依赖库: {e}")
        print("请安装所需依赖: pip install mediapipe opencv-python numpy")
        return
    
    # 创建并运行游戏
    game = FruitNinjaGame()
    game.run()

if __name__ == "__main__":
    main()