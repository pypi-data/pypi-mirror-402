#!/usr/bin/env python3
# This file is part of RADKit / Lazy Maestro <radkit@cisco.com>
# Copyright (c) 2018-2025 by Cisco Systems, Inc.
# All rights reserved.

from __future__ import annotations

from functools import cache

from pydantic import PositiveInt

from radkit_common.settings import SettingsModel, field

__all__ = [
    "GenieSettings",
    "get_settings",
]


class GenieSettings(SettingsModel, env_prefix="RADKIT_GENIE_"):
    """
    RADKit Genie settings.
    """

    exec_timeout: PositiveInt = field(60, description="Exec timeout")
    num_threads: PositiveInt = field(5, description="Thread num")


class AllGenieSettings(SettingsModel, env_prefix=None):
    genie: GenieSettings


@cache
def get_settings() -> GenieSettings:
    "Load the Genie settings from environment variables."
    return GenieSettings.load()
