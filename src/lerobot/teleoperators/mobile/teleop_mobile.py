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

import logging
import time

import hebi
import numpy as np

from lerobot.teleoperators.mobile.config_mobile import MobileConfig
from lerobot.teleoperators.teleoperator import Teleoperator
from lerobot.utils.decorators import check_if_already_connected, check_if_not_connected

logger = logging.getLogger(__name__)


class MobileTeleop(Teleoperator):
    """
    Mobile teleoperator using HEBI Mobile I/O App, without AR/Pose features.
    Exposes all 8 analog (a1-a8) and 8 digital (b1-b8) inputs continuously.
    Press and hold **B1** to enable teleoperation.
    """

    config_class = MobileConfig
    name = "mobile"

    def __init__(self, config: MobileConfig):
        super().__init__(config)
        self.config = config
        self._group = None
        self._enabled = False
        self._last_raw_inputs: dict[str, float | int] = {}
        for i in range(1, 9):
            self._last_raw_inputs[f"a{i}"] = 0.0
            self._last_raw_inputs[f"b{i}"] = 0

    @property
    def is_connected(self) -> bool:
        return self._group is not None

    @check_if_already_connected
    def connect(self) -> None:
        logger.info("Connecting to Mobile I/O, make sure to open the HEBI Mobile I/O app.")
        lookup = hebi.Lookup()
        time.sleep(2.0)
        group = lookup.get_group_from_names(["HEBI"], ["mobileIO"])
        if group is None:
            raise RuntimeError("Mobile I/O not found — check name/family settings in the app.")
        self._group = group
        logger.info(f"{self} connected to HEBI group with {group.size} module(s).")
        self.calibrate()

    def calibrate(self) -> None:
        print("Press and hold B1 in the HEBI Mobile I/O app to start...\n")
        self._wait_for_capture_trigger()
        self._enabled = False
        print("Calibration done\n")

    def _wait_for_capture_trigger(self) -> None:
        """
        Blocks execution until the trigger is detected from the mobile device.
        """
        while True:
            fbk = self._group.get_next_feedback(timeout_ms=10.0)
            if fbk is None:
                continue

            fb_pose = fbk[0]
            io = getattr(fb_pose, "io", None)
            button_b = getattr(io, "b", None) if io is not None else None
            button_b1_pressed = False
            if button_b is not None:
                button_b1_pressed = bool(button_b.get_int(1))
            if button_b1_pressed:
                return

    @property
    def is_calibrated(self) -> bool:
        return True

    @property
    def action_features(self) -> dict[str, type]:
        return {
            "mobile.raw_inputs": dict,  # analogs/buttons
            "mobile.enabled": bool,
        }

    @property
    def feedback_features(self) -> dict[str, type]:
        return {}

    def configure(self) -> None:
        pass

    def send_feedback(self, feedback: dict[str, float]) -> None:
        raise NotImplementedError

    @check_if_not_connected
    def get_action(self) -> dict:
        # Drain the queue to process ALL pending feedback packets.
        # This prevents falling behind the high-frequency sensor stream 
        # and ensures we don't miss event-driven UI updates.
        while True:
            fbk = self._group.get_next_feedback(timeout_ms=0.0)
            if fbk is None:
                break
                
            fb_pose = fbk[0]
            io = getattr(fb_pose, "io", None)
            if io is not None:
                bank_a, bank_b = io.a, io.b
                if bank_a:
                    for ch in range(1, 9):
                        if bank_a.has_float(ch):
                            self._last_raw_inputs[f"a{ch}"] = float(bank_a.get_float(ch))
                if bank_b:
                    for ch in range(1, 9):
                        if bank_b.has_int(ch):
                            self._last_raw_inputs[f"b{ch}"] = int(bank_b.get_int(ch))
                        elif hasattr(bank_b, "has_bool") and bank_b.has_bool(ch):
                            self._last_raw_inputs[f"b{ch}"] = int(bank_b.get_bool(ch))

        self._enabled = bool(self._last_raw_inputs.get("b1", 0))

        return {
            "mobile.raw_inputs": dict(self._last_raw_inputs),
            "mobile.enabled": self._enabled,
        }

    @check_if_not_connected
    def disconnect(self) -> None:
        self._group = None
