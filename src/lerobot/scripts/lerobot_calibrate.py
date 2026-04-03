# Copyright 2024 The HuggingFace Inc. team. All rights reserved.
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

"""
Simple script to calibrate a robot.
Example of use:
```bash
lerobot-calibrate --robot.type=so100_follower --robot.port=/dev/tty.usbmodem5A460814411 --robot.id=my_awesome_follower_arm
```
"""

import logging
from dataclasses import dataclass
from pprint import pformat

import draccus

from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig  # noqa: F401
from lerobot.cameras.realsense.configuration_realsense import RealSenseCameraConfig  # noqa: F401
from lerobot.robots import (  # noqa: F401
    Robot,
    RobotConfig,
    bi_openarm_follower,
    bi_so_follower,
    hope_jr,
    koch_follower,
    lekiwi,
    make_robot_from_config,
    omx_follower,
    openarm_follower,
    so_follower,
    dummy,
)
from lerobot.teleoperators import (  # noqa: F401
    Teleoperator,
    TeleoperatorConfig,
    bi_openarm_leader,
    bi_so_leader,
    homunculus,
    koch_leader,
    make_teleoperator_from_config,
    omx_leader,
    openarm_leader,
    openarm_mini,
    so_leader,
    mobile,
)
from lerobot.utils.import_utils import register_third_party_plugins
from lerobot.utils.utils import init_logging


@dataclass
class CalibrateConfig:
    robot: RobotConfig | None = None
    teleop: TeleoperatorConfig | None = None


@draccus.wrap()
def calibrate(cfg: CalibrateConfig):
    init_logging()
    logging.info(pformat(cfg))

    register_third_party_plugins()
    
    if cfg.robot is None and cfg.teleop is None:
        raise ValueError("You must provide either a robot or a teleoperator to calibrate.")

    if cfg.robot is not None:
        robot = make_robot_from_config(cfg.robot)
        robot.connect()
        robot.calibrate()
        robot.disconnect()

    if cfg.teleop is not None:
        teleop = make_teleoperator_from_config(cfg.teleop)
        teleop.connect()
        teleop.calibrate()
        teleop.disconnect()


def main():
    calibrate()


if __name__ == "__main__":
    main()
