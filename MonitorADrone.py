from OpenDJI import OpenDJI
from OpenDJI import EventListener

import cv2
import numpy as np
import keyboard
import time
import threading

"""
本示例实现一个无人机起飞、飞行、降落的控制方法
通过图像处理检测目标信息，并根据目标信息控制无人机运动
"""

"""
键盘控制说明：
    F键 - 无人机起飞
    R键 - 无人机降落
    E键 - 启用键盘控制（禁用摇杆控制）
    Q键 - 禁用键盘控制（启用摇杆控制）
    X键 - 关闭程序

    W/S键 - 上升/下降（高度控制）
    A/D键 - 左转/右转（偏航控制）
    ↑/↓键 - 前进/后退（俯仰控制）
    ←/→键 - 左移/右移（横滚控制）
"""

# MSDK服务端APP设备的IP地址
IP_ADDR = "192.168.1.102"

# 移动控制系数
MOVE_VALUE = 0.03  # 移动速度系数
ROTATE_VALUE = 0.15  # 旋转速度系数

# 图像处理参数
SCALE_FACTOR = 0.25  # 图像缩放系数

# 创建空白帧用于无图像时显示
BLANK_FRAME = np.zeros((1080, 1920, 3))
BLANK_FRAME = cv2.putText(BLANK_FRAME, "无图像", (200, 300),
                         cv2.FONT_HERSHEY_PLAIN, 10,
                         (255, 255, 255), 10)

# 线程间共享数据，使用线程安全的方式
shared_data = {
    'frame': None,               # 当前帧
    'frame_ready': threading.Event(),  # 新帧就绪事件
    'target_info': None,         # 目标检测结果
    'lock': threading.Lock()     # 线程锁
}

def detect_targets(frame):
    """
    目标检测函数（示例）
    实际应用中应替换为真实的目标检测算法
    """
    # 这里只是一个示例，返回固定值
    # 实际应用中应该实现真实的目标检测逻辑
    return [0.0, 0.0, 0.0, 0.0]  # [rcw, du, lr, bf]

def process_frame(shared_data):
    """
    图像处理线程函数
    负责接收图像帧并进行目标检测
    """
    while True:
        # 等待新帧就绪
        shared_data['frame_ready'].wait()
        
        # 获取当前帧
        with shared_data['lock']:
            frame = shared_data['frame']
            shared_data['frame_ready'].clear()
        
        # 无图像时显示空白帧
        if frame is None:
            cv2.imshow("实时视频", BLANK_FRAME)
            cv2.waitKey(1)
            continue
            
        try:
            # 执行目标检测
            target_info = detect_targets(frame)
            
            # 更新目标信息
            with shared_data['lock']:
                shared_data['target_info'] = target_info
            
            # 图像显示处理
            frame = cv2.resize(frame, dsize=None, 
                              fx=SCALE_FACTOR, 
                              fy=SCALE_FACTOR)
            cv2.imshow("实时视频", frame)
            cv2.waitKey(1)
            
        except Exception as e:
            print(f"图像处理错误: {e}")
            cv2.imshow("实时视频", BLANK_FRAME)
            cv2.waitKey(1)

def main():
    """
    主控制函数
    """
    # 启动图像处理线程
    thread = threading.Thread(target=process_frame, 
                             args=(shared_data,), 
                             daemon=True)
    thread.start()
    
    # 初始化无人机连接
    drone = OpenDJI(IP_ADDR)
    
    print("按X键关闭程序")
    try:
        target_info = [0.0, 0.0, 0.0, 0.0]
        while not keyboard.is_pressed('x'):
            # 获取新帧
            frame = drone.getFrame()
            if frame is not None:
                with shared_data['lock']:
                    shared_data['frame'] = frame
                    # 同时获取目标信息(不等待图像处理结果)
                    target_info = shared_data['target_info']
                shared_data['frame_ready'].set()
            
            # 解析控制参数
            if target_info is None:
                rcw, du, lr, bf = (0.0, 0.0, 0.0, 0.0)
            else:
                rcw, du, lr, bf = target_info
            
            # 发送控制指令
            print(drone.move(rcw, du, lr, bf, True))
            
            # 处理特殊控制指令
            if keyboard.is_pressed('f'): 
                print(drone.takeoff(True))
            if keyboard.is_pressed('r'): 
                print(drone.land(True))
            if keyboard.is_pressed('e'): 
                print(drone.enableControl(True))
            if keyboard.is_pressed('q'): 
                print(drone.disableControl(True))
            
            # 控制频率
            time.sleep(0.1)
                
    except KeyboardInterrupt:
        pass
    finally:
        # 清理资源
        cv2.destroyAllWindows()
        print("程序已退出")

if __name__ == "__main__":
    main()