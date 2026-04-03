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

# Add the CLI-Tool directory to sys.path so we can import ref_tool
cli_tool_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../CLI-Tool"))
if cli_tool_path not in sys.path:
    sys.path.append(cli_tool_path)

import ref_tool

from lerobot.teleoperators.mobile.config_mobile import MobileConfig
from lerobot.teleoperators.mobile.teleop_mobile import MobileTeleop
from lerobot.utils.robot_utils import precise_sleep

FPS = 30


def main():
    # 1. Initialize the mobile teleoperator
    teleop_config = MobileConfig()
    teleop_device = MobileTeleop(teleop_config)

    # 2. Initialize the robot arm
    print("Initializing robot arm...")
    my_drive = ref_tool.find_any()
    my_drive.robot.set_rgb_mode(4)
    my_drive.robot.set_enable(1)
    my_drive.robot.homing()
    print("Robot arm initialized.")

    # Program angle vs actual angle bias (actual = program - bias)
    joint_bias = {
        1: 0,
        2: 77,
        3: -185,
        4: 0,
        5: 0,
        6: 0
    }

    # 3. Connect to the teleoperator
    teleop_device.connect()

    if not teleop_device.is_connected:
        raise ValueError("Teleop is not connected!")

    print("Starting mobile teleop loop. Move your phone's A sliders to control the dummy robot...")
    try:
        while True:
            t0 = time.perf_counter()

            # Get teleop action
            mobile_obs = teleop_device.get_action()

            # Ensure the device is returning valid action observations
            if mobile_obs and "mobile.raw_inputs" in mobile_obs:
                raw_inputs = mobile_obs["mobile.raw_inputs"]

                # 1. Get current JOINT angles from hardware and apply bias
                current_actual_angles = {
                    1: my_drive.robot.joint_1.angle - joint_bias[1],
                    2: my_drive.robot.joint_2.angle - joint_bias[2],
                    3: my_drive.robot.joint_3.angle - joint_bias[3],
                    4: my_drive.robot.joint_4.angle - joint_bias[4],
                    5: my_drive.robot.joint_5.angle - joint_bias[5],
                    6: my_drive.robot.joint_6.angle - joint_bias[6],
                }

                # 2. Extract incremental values (range [-1, 1]) based on new mapping and scale by 10
                # Mapping: J1:a1, J2:a2, J3:a3, J4:a7, J5:a8, J6:a6
                mapping = {1: "a1", 2: "a2", 3: "a3", 4: "a7", 5: "a8", 6: "a6"}
                
                raw_a_values = {i: float(raw_inputs.get(key, 0.0)) for i, key in mapping.items()}
                joint_moves = {i: val * 10.0 for i, val in raw_a_values.items()}

                # 3. Calculate final target angles for this loop
                target_angles = {}
                for i in range(1, 7):
                    target_angles[i] = current_actual_angles[i] + joint_moves[i]

                # 4. Print the raw inputs and final target angles
                print(f"Inputs: a1(J1):{raw_a_values[1]:.2f}, a2(J2):{raw_a_values[2]:.2f}, a3(J3):{raw_a_values[3]:.2f}, "
                      f"a7(J4):{raw_a_values[4]:.2f}, a8(J5):{raw_a_values[5]:.2f}, a6(J6):{raw_a_values[6]:.2f}")
                print(f"Target Angles: J1:{target_angles[1]:.2f}, J2:{target_angles[2]:.2f}, "
                      f"J3:{target_angles[3]:.2f}, J4:{target_angles[4]:.2f}, "
                      f"J5:{target_angles[5]:.2f}, J6:{target_angles[6]:.2f}")

                # 5. Instruct the robot arm to move
                my_drive.robot.move_j(
                    target_angles[1],
                    target_angles[2],
                    target_angles[3],
                    target_angles[4],
                    target_angles[5],
                    target_angles[6]
                )

            precise_sleep(max(1.0 / FPS - (time.perf_counter() - t0), 0.0))
    except KeyboardInterrupt:
        print("\nStopping mobile teleop operate loop.")


if __name__ == "__main__":
    main()
