#!/usr/bin/env python

import sys
import os
from functools import cached_property

from lerobot.cameras.utils import make_cameras_from_configs
from lerobot.processor import RobotAction, RobotObservation
from lerobot.utils.decorators import check_if_already_connected, check_if_not_connected

from ..robot import Robot
from .config_dummy import DummyRobotConfig

# Add the CLI-Tool directory to sys.path so we can import ref_tool
cli_tool_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../CLI-Tool"))
if cli_tool_path not in sys.path:
    sys.path.append(cli_tool_path)

try:
    import ref_tool
except ImportError:
    ref_tool = None


class DummyRobot(Robot):
    config_class = DummyRobotConfig
    name = "dummy"

    def __init__(self, config: DummyRobotConfig):
        super().__init__(config)
        self.config = config
        self.my_drive = None
        self.cameras = make_cameras_from_configs(config.cameras)
        
        self.joint_bias = {
            1: 0,
            2: 77,
            3: -185,
            4: 0,
            5: 0,
            6: 0
        }

    @property
    def _cameras_ft(self) -> dict[str, tuple]:
        return {
            cam: (self.config.cameras[cam].height, self.config.cameras[cam].width, 3) for cam in self.cameras
        }

    @cached_property
    def observation_features(self) -> dict[str, type | tuple]:
        obs = {f"joint_{i}.pos": float for i in range(1, 7)}
        obs.update(self._cameras_ft)
        return obs

    @cached_property
    def action_features(self) -> dict[str, type]:
        return {f"joint_{i}.pos": float for i in range(1, 7)}

    @property
    def is_connected(self) -> bool:
        return self.my_drive is not None and all(cam.is_connected for cam in self.cameras.values())

    @check_if_already_connected
    def connect(self, calibrate: bool = True) -> None:
        if ref_tool is None:
            raise ImportError("ref_tool could not be imported. Make sure CLI-Tool is in the correct path.")
            
        self.my_drive = ref_tool.find_any()
        self.my_drive.robot.set_rgb_mode(4)
        self.my_drive.robot.set_enable(1)
        self.my_drive.robot.homing()

        for cam in self.cameras.values():
            cam.connect()

    @property
    def is_calibrated(self) -> bool:
        return True

    def calibrate(self) -> None:
        pass

    def configure(self) -> None:
        pass

    @check_if_not_connected
    def get_observation(self) -> RobotObservation:
        obs_dict = {
            "joint_1.pos": self.my_drive.robot.joint_1.angle - self.joint_bias[1],
            "joint_2.pos": self.my_drive.robot.joint_2.angle - self.joint_bias[2],
            "joint_3.pos": self.my_drive.robot.joint_3.angle - self.joint_bias[3],
            "joint_4.pos": self.my_drive.robot.joint_4.angle - self.joint_bias[4],
            "joint_5.pos": self.my_drive.robot.joint_5.angle - self.joint_bias[5],
            "joint_6.pos": self.my_drive.robot.joint_6.angle - self.joint_bias[6],
        }
        for cam_key, cam in self.cameras.items():
            obs_dict[cam_key] = cam.read_latest()
        return obs_dict

    @check_if_not_connected
    def send_action(self, action: RobotAction) -> RobotAction:
        if "mobile.raw_inputs" in action:
            raw_inputs = action["mobile.raw_inputs"]
            mapping = {1: "a1", 2: "a2", 3: "a3", 4: "a7", 5: "a8", 6: "a6"}
            raw_a_values = {i: float(raw_inputs.get(key, 0.0)) for i, key in mapping.items()}
            joint_moves = {i: val * 10.0 for i, val in raw_a_values.items()}

            target_angles = {
                1: self.my_drive.robot.joint_1.angle - self.joint_bias[1] + joint_moves[1],
                2: self.my_drive.robot.joint_2.angle - self.joint_bias[2] + joint_moves[2],
                3: self.my_drive.robot.joint_3.angle - self.joint_bias[3] + joint_moves[3],
                4: self.my_drive.robot.joint_4.angle - self.joint_bias[4] + joint_moves[4],
                5: self.my_drive.robot.joint_5.angle - self.joint_bias[5] + joint_moves[5],
                6: self.my_drive.robot.joint_6.angle - self.joint_bias[6] + joint_moves[6],
            }
            # Populate the expected action features so downstream scripts log the correct absolute positions
            for i in range(1, 7):
                action[f"joint_{i}.pos"] = target_angles[i]
        else:
            target_angles = {
                1: action.get("joint_1.pos", self.my_drive.robot.joint_1.angle - self.joint_bias[1]),
                2: action.get("joint_2.pos", self.my_drive.robot.joint_2.angle - self.joint_bias[2]),
                3: action.get("joint_3.pos", self.my_drive.robot.joint_3.angle - self.joint_bias[3]),
                4: action.get("joint_4.pos", self.my_drive.robot.joint_4.angle - self.joint_bias[4]),
                5: action.get("joint_5.pos", self.my_drive.robot.joint_5.angle - self.joint_bias[5]),
                6: action.get("joint_6.pos", self.my_drive.robot.joint_6.angle - self.joint_bias[6]),
            }

        self.my_drive.robot.move_j(
            target_angles[1],
            target_angles[2],
            target_angles[3],
            target_angles[4],
            target_angles[5],
            target_angles[6]
        )
        return action

    @check_if_not_connected
    def disconnect(self):
        if self.my_drive:
            self.my_drive.robot.set_enable(0)
            self.my_drive = None
            
        for cam in self.cameras.values():
            cam.disconnect()
