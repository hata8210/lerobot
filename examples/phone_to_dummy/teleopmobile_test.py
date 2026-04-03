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

from lerobot.teleoperators.mobile.config_mobile import MobileConfig
from lerobot.teleoperators.mobile.teleop_mobile import MobileTeleop
from lerobot.utils.robot_utils import precise_sleep

FPS = 30


def main():
    # Initialize the mobile teleoperator
    teleop_config = MobileConfig()
    teleop_device = MobileTeleop(teleop_config)

    # Connect to the teleoperator
    teleop_device.connect()

    if not teleop_device.is_connected:
        raise ValueError("Teleop is not connected!")

    print("Starting mobile teleop test loop. Move your phone and press B1 to see the output...")
    try:
        while True:
            t0 = time.perf_counter()

            # Get teleop action
            mobile_obs = teleop_device.get_action()

            # Print the received action
            # This will now include a full dictionary of 'mobile.raw_inputs' with a1-a8 and b1-b8
            print(f"Received action: {mobile_obs}")

            precise_sleep(max(1.0 / FPS - (time.perf_counter() - t0), 0.0))
    except KeyboardInterrupt:
        print("\nStopping mobile teleop test loop.")


if __name__ == "__main__":
    main()
