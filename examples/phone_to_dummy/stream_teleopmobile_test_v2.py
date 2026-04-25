#!/usr/bin/env python

# Copyright 2025 The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time
import requests

from lerobot.teleoperators.mobile.config_mobile import MobileConfig
from lerobot.teleoperators.mobile.teleop_mobile import MobileTeleop
from lerobot.utils.robot_utils import precise_sleep

FPS = 50
# 假设你的流式API服务器IP为 127.0.0.1，端口为 8001 (请根据实际情况修改IP)
STREAM_API_URL = "http://127.0.0.1:8001/api/stream"
JOINT_STREAM_API_URL = "http://127.0.0.1:8001/api/joint_stream"
RESTORE_API_URL = "http://127.0.0.1:8001/api/restore_initial"


def send_joint_stream(v1=0.0, v2=0.0, v3=0.0, v4=0.0, v5=0.0, v6=0.0):
    """
    发送关节空间速度控制指令 (值域: -1.0 到 1.0)
    """
    payload = {"v1": v1, "v2": v2, "v3": v3, "v4": v4, "v5": v5, "v6": v6}
    try:
        response = requests.post(JOINT_STREAM_API_URL, json=payload, timeout=0.2)
        if response.status_code != 200:
             pass
    except requests.exceptions.RequestException:
        pass


def trigger_restore():
    """
    触发恢复初始位姿
    """
    try:
        requests.post(RESTORE_API_URL, timeout=1.0)
    except requests.exceptions.RequestException as e:
        print(f"\n复位请求失败: {e}")


def send_joystick_command(x=0.0, y=0.0, z=0.0, roll=0.0, pitch=0.0, yaw=0.0):
    """
    发送遥控器杆量 (值域: -1.0 到 1.0)
    """
    payload = {
        "x": x,
        "y": y,
        "z": z,
        "roll": roll,
        "pitch": pitch,
        "yaw": yaw
    }
    try:
        # 设置较短的超时时间，保证流式控制的非阻塞特性
        response = requests.post(STREAM_API_URL, json=payload, timeout=0.2)
        if response.status_code != 200:
             print(f"指令发送失败: 状态码 {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"网络请求错误 (请确保 stream_api_server.py 已经启动): {e}")


def main():
    # Initialize the mobile teleoperator
    teleop_config = MobileConfig()
    teleop_device = MobileTeleop(teleop_config)

    # Connect to the teleoperator
    teleop_device.connect()

    if not teleop_device.is_connected:
        raise ValueError("Teleop is not connected!")

    print(f"Starting stream mobile teleop test loop. Sending commands to {STREAM_API_URL}")
    print("Move your phone and press B1 to see the output...")
    
    try:
        is_active = False
        prev_b1 = 0
        prev_b6 = 0

        while True:
            t0 = time.perf_counter()

            # Get teleop action
            mobile_obs = teleop_device.get_action()
            
            # Extract raw inputs
            raw_inputs = mobile_obs.get("mobile.raw_inputs", {})
            
            # 检测 B1 按键按下（上升沿）以切换激活状态
            current_b1 = raw_inputs.get("b1", 0)
            if current_b1 == 1 and prev_b1 == 0:
                is_active = not is_active
            prev_b1 = current_b1

            # 检测 B6 按键按下（上升沿）以触发复位
            current_b6 = raw_inputs.get("b6", 0)
            if current_b6 == 1 and prev_b6 == 0:
                print("\n[Action] 触发复位初始位姿...")
                trigger_restore()
            prev_b6 = current_b6

            # 获取 B3 状态：按下时切换为关节流控制模式
            current_b3 = raw_inputs.get("b3", 0)

            if is_active:
                if current_b3 == 1:
                    # 关节控制模式 (长按 B3)
                    # a1 -> joint1 (v1), a2 -> joint2 (v2)
                    # a3 -> joint3 (v3)
                    # a7 -> joint4 (v4), a8 -> joint5 (v5)
                    # a6 -> joint6 (v6)
                    v1 = raw_inputs.get("a1", 0.0)
                    v2 = raw_inputs.get("a2", 0.0)
                    v3 = raw_inputs.get("a3", 0.0)
                    v4 = raw_inputs.get("a7", 0.0)
                    v5 = raw_inputs.get("a8", 0.0)
                    v6 = raw_inputs.get("a6", 0.0)

                    send_joint_stream(v1=v1, v2=v2, v3=v3, v4=v4, v5=v5, v6=v6)
                    # 停止末端位姿流式控制，防止互相干扰
                    send_joystick_command(0, 0, 0, 0, 0, 0)
                    print(f"Joints: v1={v1:.2f}, v2={v2:.2f}, v3={v3:.2f}, v4={v4:.2f}, v5={v5:.2f}, v6={v6:.2f}                ", end="\r")
                else:
                    # Mapping with speed multipliers:
                    # a1 -> x (水平左右) 
                    # a2 -> y (水平前后) 
                    # a3 -> z (垂直上下) 
                    # a6 -> Pitch 
                    # a7 -> Yaw 
                    # a8 -> Roll
                    # 速度将乘以静态运动倍数
                    # 方向将乘以静态正反
                    x = raw_inputs.get("a1", 0.0) * -1.0 * 12.0
                    y = raw_inputs.get("a2", 0.0) * 1.0 * 8.0
                    z = raw_inputs.get("a3", 0.0) * 1.0 * 8.0
                    pitch = raw_inputs.get("a6", 0.0) * 1.0 * 12.0
                    yaw = raw_inputs.get("a7", 0.0) * 1.0 *12.0
                    roll = raw_inputs.get("a8", 0.0) * 1.0 * 12.0

                    send_joystick_command(x=x, y=y, z=z, roll=roll, pitch=pitch, yaw=yaw)
                    # 停止关节流式控制
                    send_joint_stream(0, 0, 0, 0, 0, 0)
                    print(f"Sent: x={x:.2f}, y={y:.2f}, z={z:.2f}, roll={roll:.2f}, pitch={pitch:.2f}, yaw={yaw:.2f}                ", end="\r")
            else:
                # If not enabled, send zeros to stop
                send_joystick_command(0, 0, 0, 0, 0, 0)
                send_joint_stream(0, 0, 0, 0, 0, 0)
                print("Disabled (Press B1 to toggle on/off, B6 to restore)                          ", end="\r")

            precise_sleep(max(1.0 / FPS - (time.perf_counter() - t0), 0.0))
    except KeyboardInterrupt:
        print("\nStopping mobile teleop test loop.")
        # Send zero command on exit
        try:
            send_joystick_command(0, 0, 0, 0, 0, 0)
            send_joint_stream(0, 0, 0, 0, 0, 0)
        except:
            pass


if __name__ == "__main__":
    main()
