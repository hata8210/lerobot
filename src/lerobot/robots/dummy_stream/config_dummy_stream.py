#!/usr/bin/env python

from dataclasses import dataclass, field

from lerobot.cameras import CameraConfig
from ..config import RobotConfig


@dataclass
class DummyStreamConfig:
    cameras: dict[str, CameraConfig] = field(default_factory=dict)


@RobotConfig.register_subclass("dummy_stream")
@dataclass
class DummyStreamRobotConfig(RobotConfig, DummyStreamConfig):
    pass
