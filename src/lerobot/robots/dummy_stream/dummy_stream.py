#!/usr/bin/env python

import sys
import os
import time
import requests
from functools import cached_property

from lerobot.cameras.utils import make_cameras_from_configs
from lerobot.processor import RobotAction, RobotObservation
from lerobot.utils.decorators import check_if_already_connected, check_if_not_connected

from ..robot import Robot
from .config_dummy_stream import DummyStreamRobotConfig

# Add the CLI-Tool directory to sys.path so we can import ref_tool
cli_tool_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../CLI-Tool"))
if cli_tool_path not in sys.path:
    sys.path.append(cli_tool_path)

try:
    import ref_tool
except ImportError:
    ref_tool = None

class DummyStreamRobot(Robot):
    config_class = DummyStreamRobotConfig
    name = "dummy_stream"

    def __init__(self, config: DummyStreamRobotConfig):
        super().__init__(config)
        self.config = config
        self.my_drive = None
        self._is_connected = False
        self.cameras = make_cameras_from_configs(config.cameras)
        
        # Dynamic API URLs based on config
        base_url = f"http://{config.ip}:{config.port}"
        self.stream_api_url = f"{base_url}/api/stream"
        self.joint_stream_api_url = f"{base_url}/api/joint_stream"
        self.restore_api_url = f"{base_url}/api/restore_initial"
        self.joints_api_url = f"{base_url}/api/joints"

        self.joint_bias = {
            1: 0,
            2: 77,
            3: -185,
            4: 0,
            5: 0,
            6: 0
        }

        # Teleop state
        self.is_active = False
        self.prev_b1 = 0
        self.prev_b6 = 0

        # Performance Cache
        self._joints_cache = {f"joint_{i}.pos": 0.0 for i in range(1, 7)}
        self._last_fetch_time = 0

        # Use Session for persistent connections
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(pool_connections=1, pool_maxsize=1)
        self.session.mount('http://', adapter)

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
        return self._is_connected

    @check_if_already_connected
    def connect(self, calibrate: bool = True) -> None:
        for cam in self.cameras.values():
            cam.connect()
        self._is_connected = True
        print("DummyStreamRobot connected (Cameras started, hardware connection deferred)")

    def _ensure_hardware_connected(self):
        if self.my_drive is not None:
            return
        if ref_tool is None:
            raise ImportError("ref_tool could not be imported. Make sure CLI-Tool is in the correct path.")
        print("Connecting to ODrive hardware via ref_tool...")
        self.my_drive = ref_tool.find_any()
        self.my_drive.robot.set_rgb_mode(4)
        self.my_drive.robot.set_enable(1)
        print("Hardware connected.")

    @property
    def is_calibrated(self) -> bool:
        return True

    def calibrate(self) -> None:
        pass

    def configure(self) -> None:
        pass

    def _send_joystick_command(self, x=0.0, y=0.0, z=0.0, roll=0.0, pitch=0.0, yaw=0.0):
        payload = {"x": x, "y": y, "z": z, "roll": roll, "pitch": pitch, "yaw": yaw}
        try:
            # Very short timeout for control commands
            self.session.post(self.stream_api_url, json=payload, timeout=(0.01, 0.02))
        except:
            pass

    def _send_joint_stream(self, v1=0.0, v2=0.0, v3=0.0, v4=0.0, v5=0.0, v6=0.0):
        payload = {"v1": v1, "v2": v2, "v3": v3, "v4": v4, "v5": v5, "v6": v6}
        try:
            self.session.post(self.joint_stream_api_url, json=payload, timeout=(0.01, 0.02))
        except:
            pass

    def _trigger_restore(self):
        try:
            self.session.post(self.restore_api_url, timeout=1.0)
        except:
            pass

    def _get_joints(self, use_cache=False) -> dict[str, float]:
        now = time.perf_counter()
        # If cache is requested and it's fresh (within 15ms), reuse it to save an HTTP call
        if use_cache and (now - self._last_fetch_time < 0.015):
            return self._joints_cache

        try:
            response = self.session.get(self.joints_api_url, timeout=(0.01, 0.04))
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok":
                    joints = data["joints"]
                    self._joints_cache = {f"joint_{''.join(filter(str.isdigit, name))}.pos": pos for name, pos in joints.items()}
                    self._last_fetch_time = now
                    return self._joints_cache
        except:
            pass
        
        if self.my_drive is not None:
            res = {
                "joint_1.pos": self.my_drive.robot.joint_1.angle - self.joint_bias[1],
                "joint_2.pos": self.my_drive.robot.joint_2.angle - self.joint_bias[2],
                "joint_3.pos": self.my_drive.robot.joint_3.angle - self.joint_bias[3],
                "joint_4.pos": self.my_drive.robot.joint_4.angle - self.joint_bias[4],
                "joint_5.pos": self.my_drive.robot.joint_5.angle - self.joint_bias[5],
                "joint_6.pos": self.my_drive.robot.joint_6.angle - self.joint_bias[6],
            }
            self._joints_cache = res
            self._last_fetch_time = now
            return res
            
        return self._joints_cache

    @check_if_not_connected
    def get_observation(self) -> RobotObservation:
        # Observation always gets a fresh read
        obs_dict = self._get_joints(use_cache=False).copy()
        for cam_key, cam in self.cameras.items():
            obs_dict[cam_key] = cam.read_latest()
        return obs_dict

    @check_if_not_connected
    def send_action(self, action: RobotAction) -> RobotAction:
        if "mobile.raw_inputs" in action:
            raw_inputs = action.pop("mobile.raw_inputs")
            action.pop("mobile.enabled", None)
            
            # Toggle Active State (B1)
            current_b1 = raw_inputs.get("b1", 0)
            if current_b1 == 1 and self.prev_b1 == 0:
                self.is_active = not self.is_active
                print(f"\n[Status] Mobile Control {'Activated' if self.is_active else 'Deactivated'}")
            self.prev_b1 = current_b1

            # Trigger Restore (B6)
            current_b6 = raw_inputs.get("b6", 0)
            if current_b6 == 1 and self.prev_b6 == 0:
                self._trigger_restore()
            self.prev_b6 = current_b6

            if self.is_active:
                current_b3 = raw_inputs.get("b3", 0)
                if current_b3 == 1:
                    v1 = raw_inputs.get("a1", 0.0)
                    v2 = raw_inputs.get("a2", 0.0)
                    v3 = raw_inputs.get("a3", 0.0)
                    v4 = raw_inputs.get("a7", 0.0)
                    v5 = raw_inputs.get("a8", 0.0)
                    v6 = raw_inputs.get("a6", 0.0)
                    self._send_joint_stream(v1=v1, v2=v2, v3=v3, v4=v4, v5=v5, v6=v6)
                    self._send_joystick_command(0, 0, 0, 0, 0, 0)
                else:
                    x = raw_inputs.get("a1", 0.0) * -1.0 * 12.0
                    y = raw_inputs.get("a2", 0.0) * 1.0 * 8.0
                    z = raw_inputs.get("a3", 0.0) * 1.0 * 8.0
                    pitch = raw_inputs.get("a6", 0.0) * 1.0 * 12.0
                    yaw = raw_inputs.get("a7", 0.0) * 1.0 * 12.0
                    roll = raw_inputs.get("a8", 0.0) * 1.0 * 12.0
                    self._send_joystick_command(x=x, y=y, z=z, roll=roll, pitch=pitch, yaw=yaw)
                    self._send_joint_stream(0, 0, 0, 0, 0, 0)
            else:
                self._send_joystick_command(0, 0, 0, 0, 0, 0)
                self._send_joint_stream(0, 0, 0, 0, 0, 0)

            # Use cache here because get_observation was just called milliseconds ago
            current_joints = self._get_joints(use_cache=True)
            for key, val in current_joints.items():
                action[key] = val
            
        else:
            self._ensure_hardware_connected()
            target_angles = {
                1: float(action.get("joint_1.pos", self.my_drive.robot.joint_1.angle - self.joint_bias[1])),
                2: float(action.get("joint_2.pos", self.my_drive.robot.joint_2.angle - self.joint_bias[2])),
                3: float(action.get("joint_3.pos", self.my_drive.robot.joint_3.angle - self.joint_bias[3])),
                4: float(action.get("joint_4.pos", self.my_drive.robot.joint_4.angle - self.joint_bias[4])),
                5: float(action.get("joint_5.pos", self.my_drive.robot.joint_5.angle - self.joint_bias[5])),
                6: float(action.get("joint_6.pos", self.my_drive.robot.joint_6.angle - self.joint_bias[6])),
            }
            self.my_drive.robot.move_j(
                target_angles[1] + self.joint_bias[1],
                target_angles[2] + self.joint_bias[2],
                target_angles[3] + self.joint_bias[3],
                target_angles[4] + self.joint_bias[4],
                target_angles[5] + self.joint_bias[5],
                target_angles[6] + self.joint_bias[6]
            )
        return action

    @check_if_not_connected
    def disconnect(self):
        if self.my_drive:
            self.my_drive.robot.set_enable(0)
            self.my_drive = None
        for cam in self.cameras.values():
            cam.disconnect()
        self.session.close()
        self._is_connected = False
