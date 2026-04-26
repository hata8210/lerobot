#!/usr/bin/env python

from dataclasses import dataclass, field

from lerobot.cameras import CameraConfig
from ..config import RobotConfig


@dataclass
class DummyStreamConfig:
    ip: str = "127.0.0.1"
    port: int = 8001
    cameras: dict[str, CameraConfig] = field(default_factory=dict)


@RobotConfig.register_subclass("dummy_stream")
@dataclass
class DummyStreamRobotConfig(RobotConfig, DummyStreamConfig):
    pass
