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
import sys
import os
import math
import requests

from lerobot.teleoperators.mobile.config_mobile import MobileConfig
from lerobot.teleoperators.mobile.teleop_mobile import MobileTeleop
from lerobot.utils.robot_utils import precise_sleep

FPS = 30
BASE_URL = "http://127.0.0.1:8000"

def euler_to_quat(roll, pitch, yaw):
    cy = math.cos(yaw * 0.5)
    sy = math.sin(yaw * 0.5)
    cp = math.cos(pitch * 0.5)
    sp = math.sin(pitch * 0.5)
    cr = math.cos(roll * 0.5)
    sr = math.sin(roll * 0.5)

    qw = cr * cp * cy + sr * sp * sy
    qx = sr * cp * cy - cr * sp * sy
    qy = cr * sp * cy + sr * cp * sy
    qz = cr * cp * sy - sr * sp * cy

    return [qx, qy, qz, qw]

def quat_to_euler(qx, qy, qz, qw):
    # roll (x-axis rotation)
    sinr_cosp = 2 * (qw * qx + qy * qz)
    cosr_cosp = 1 - 2 * (qx * qx + qy * qy)
    roll = math.atan2(sinr_cosp, cosr_cosp)

    # pitch (y-axis rotation)
    sinp = 2 * (qw * qy - qz * qx)
    if abs(sinp) >= 1:
        pitch = math.copysign(math.pi / 2, sinp) # use 90 degrees if out of range
    else:
        pitch = math.asin(sinp)

    # yaw (z-axis rotation)
    siny_cosp = 2 * (qw * qz + qx * qy)
    cosy_cosp = 1 - 2 * (qy * qy + qz * qz)
    yaw = math.atan2(siny_cosp, cosy_cosp)

    return roll, pitch, yaw

def main():
    # 1. Initialize the mobile teleoperator
    teleop_config = MobileConfig()
    teleop_device = MobileTeleop(teleop_config)

    # 2. Check MoveIt API Server connection
    print("Checking MoveIt API Server...")
    try:
        response = requests.get(f"{BASE_URL}/api/status")
        if response.status_code != 200:
            print(f"Warning: MoveIt API returned status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"ERROR: Could not connect to MoveIt API Server at {BASE_URL}.")
        print("Please start the ROS 2 API Server first.")
        sys.exit(1)
    print("MoveIt API Server is accessible.")

    # 3. Connect to the teleoperator
    teleop_device.connect()

    if not teleop_device.is_connected:
        raise ValueError("Teleop is not connected!")

    print("Starting mobile teleop loop. Move your phone's A sliders to control the dummy robot end-effector...")
    try:
        while True:
            t0 = time.perf_counter()

            # Get teleop action
            mobile_obs = teleop_device.get_action()

            if mobile_obs and "mobile.raw_inputs" in mobile_obs:
                raw_inputs = mobile_obs["mobile.raw_inputs"]

                # Check if b6 is pressed to reset to initial pose
                b6_pressed = float(raw_inputs.get("b6", 0.0)) > 0.5
                if b6_pressed:
                    payload = {
                        "x": 0.0,
                        "y": -0.29,
                        "z": 0.25,
                        "qx": 0.0,
                        "qy": 0.0,
                        "qz": 0.0,
                        "qw": 1.0
                    }
                    try:
                        requests.post(f"{BASE_URL}/api/move_optimal", json=payload, timeout=0.5)
                        print("Resetting to initial pose (b6 pressed).")
                    except requests.exceptions.RequestException as e:
                        print(f"Failed to send reset move command: {e}")
                    precise_sleep(max(1.0 / FPS - (time.perf_counter() - t0), 0.0))
                    continue

                # Extract raw values
                # a1, a2, a3 for XYZ
                # a6, a7, a8 for Roll, Pitch, Yaw
                mapping = {1: "a1", 2: "a2", 3: "a3", 4: "a6", 5: "a7", 6: "a8"}
                raw_a_values = {i: float(raw_inputs.get(key, 0.0)) for i, key in mapping.items()}

                # Apply deadzone to avoid drift when not touching
                deadzone = 0.05
                for i in raw_a_values:
                    if abs(raw_a_values[i]) < deadzone:
                        raw_a_values[i] = 0.0

                # If no input, skip HTTP calls
                if all(v == 0.0 for v in raw_a_values.values()):
                    precise_sleep(max(1.0 / FPS - (time.perf_counter() - t0), 0.0))
                    continue

                # Check if robot is IDLE
                try:
                    status_res = requests.get(f"{BASE_URL}/api/status", timeout=0.2)
                    if status_res.status_code == 200:
                        status_data = status_res.json()
                        if status_data.get("robot_state") != "IDLE":
                            # Robot is executing, skip this frame
                            precise_sleep(max(1.0 / FPS - (time.perf_counter() - t0), 0.0))
                            continue
                except requests.exceptions.RequestException:
                    pass

                # 1. Get current Cartesian pose from MoveIt
                try:
                    pose_res = requests.get(f"{BASE_URL}/api/pose", timeout=0.2)
                    if pose_res.status_code != 200:
                        continue
                    current_pose = pose_res.json()
                except requests.exceptions.RequestException:
                    continue

                pos = current_pose.get("position", {"x": 0.0, "y": 0.0, "z": 0.0})
                ori = current_pose.get("orientation", {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0})

                roll, pitch, yaw = quat_to_euler(ori["x"], ori["y"], ori["z"], ori["w"])

                # 2. Extract incremental values
                linear_speed = 0.01  # Max 1 cm per frame
                angular_speed = 0.05 # Max ~2.8 degrees per frame

                x_move = -raw_a_values[1] * linear_speed
                y_move = -raw_a_values[2] * linear_speed
                z_move = raw_a_values[3] * linear_speed

                roll_move = raw_a_values[4] * angular_speed
                pitch_move = raw_a_values[5] * angular_speed
                yaw_move = raw_a_values[6] * angular_speed

                # 3. Calculate target pose
                target_x = pos["x"] + x_move
                target_y = pos["y"] + y_move
                target_z = pos["z"] + z_move

                target_roll = roll + roll_move
                target_pitch = pitch + pitch_move
                target_yaw = yaw + yaw_move

                qx, qy, qz, qw = euler_to_quat(target_roll, target_pitch, target_yaw)

                # 4. Print logs
                print(f"Inputs: a1(X):{raw_a_values[1]:.2f}, a2(Y):{raw_a_values[2]:.2f}, a3(Z):{raw_a_values[3]:.2f}, "
                      f"a6(R):{raw_a_values[4]:.2f}, a7(P):{raw_a_values[5]:.2f}, a8(Yw):{raw_a_values[6]:.2f}")
                print(f"Target Pose: X:{target_x:.3f}, Y:{target_y:.3f}, Z:{target_z:.3f}, "
                      f"R:{target_roll:.2f}, P:{target_pitch:.2f}, Yw:{target_yaw:.2f}")

                # 5. Instruct MoveIt
                payload = {
                    "x": target_x,
                    "y": target_y,
                    "z": target_z,
                    "qx": qx,
                    "qy": qy,
                    "qz": qz,
                    "qw": qw
                }
                
                try:
                    requests.post(f"{BASE_URL}/api/move_optimal", json=payload, timeout=0.5)
                except requests.exceptions.RequestException as e:
                    print(f"Failed to send move command: {e}")

            precise_sleep(max(1.0 / FPS - (time.perf_counter() - t0), 0.0))
    except KeyboardInterrupt:
        print("\nStopping mobile teleop operate loop.")

if __name__ == "__main__":
    main()