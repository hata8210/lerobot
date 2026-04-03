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

from lerobot.teleoperators.phone.config_phone import PhoneConfig, PhoneOS
from lerobot.teleoperators.phone.teleop_phone import Phone
from lerobot.utils.robot_utils import precise_sleep

FPS = 1


def main():

    print(f"Teleop is connecting!")
    
    # Initialize the teleoperator
    teleop_config = PhoneConfig(phone_os=PhoneOS.IOS)  # or PhoneOS.ANDROID
    teleop_device = Phone(teleop_config)

    # Connect to the teleoperator
    teleop_device.connect()

    if not teleop_device.is_connected:
        raise ValueError("Teleop is not connected!")

    print(f"Teleop is connected!")
    print("Starting teleop test loop. Move your phone to see the output...")
    try:
        while True:
            t0 = time.perf_counter()

            # Get teleop action
            phone_obs = teleop_device.get_action()

            # Print the received action
            print(f"Received action: {phone_obs}")

            precise_sleep(max(1.0 / FPS - (time.perf_counter() - t0), 0.0))
    except KeyboardInterrupt:
        print("Stopping teleop test loop.")


if __name__ == "__main__":
    main()
