#!/usr/bin/env python

from dataclasses import dataclass, field

from lerobot.cameras import CameraConfig
from ..config import RobotConfig


@dataclass
class DummyConfig:
    cameras: dict[str, CameraConfig] = field(default_factory=dict)


@RobotConfig.register_subclass("dummy")
@dataclass
class DummyRobotConfig(RobotConfig, DummyConfig):
    pass
