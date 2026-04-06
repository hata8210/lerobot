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

            if is_active:
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
                print(f"Sent: x={x:.2f}, y={y:.2f}, z={z:.2f}, roll={roll:.2f}, pitch={pitch:.2f}, yaw={yaw:.2f}                ", end="\r")
            else:
                # If not enabled, send zeros to stop
                send_joystick_command(0, 0, 0, 0, 0, 0)
                print("Disabled (Press B1 to toggle on/off)                          ", end="\r")

            precise_sleep(max(1.0 / FPS - (time.perf_counter() - t0), 0.0))
    except KeyboardInterrupt:
        print("\nStopping mobile teleop test loop.")
        # Send zero command on exit
        try:
            send_joystick_command(0, 0, 0, 0, 0, 0)
        except:
            pass


if __name__ == "__main__":
    main()
