#!/usr/bin/env python

from dataclasses import dataclass, field

from lerobot.cameras import CameraConfig
from ..config import RobotConfig


@dataclass
class DummyStreamConfig:
    ip: str = "192.168.31.7"
    port: int = 8001
    cameras: dict[str, CameraConfig] = field(default_factory=dict)


@RobotConfig.register_subclass("dummy_stream")
@dataclass
class DummyStreamRobotConfig(RobotConfig, DummyStreamConfig):
    pass
