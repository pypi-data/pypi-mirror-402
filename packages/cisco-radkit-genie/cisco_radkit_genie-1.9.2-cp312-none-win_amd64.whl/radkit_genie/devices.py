# This file is part of RADKit / Lazy Maestro <radkit@cisco.com>
# Copyright (c) 2018-2025 by Cisco Systems, Inc.
# All rights reserved.

# mock a Genie's device object with methods we need to integrate RADKit

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from genie.conf.base.utils import QDict  # type:ignore[import-untyped]
from genie.libs.conf.device import Device as GenieDevice  # type:ignore[import-untyped]

from radkit_client.sync.device import Device as RADKitDevice
from radkit_client.sync.exceptions import ClientError
from radkit_common import nglog
from radkit_common.types import DeviceType

from .exceptions import RADKitGenieException, RADKitGenieMissingOS
from .settings import get_settings

tGENIE = nglog.Tags.GENIE
logger = nglog.getAdapter(__name__, tags=[tGENIE])


@dataclass(repr=False)
class DeviceOsPlatform:
    os: str | None = None
    platform: str | None = None
    model: str | None = None


# Mapping of device type identifier to Genie OS name,
# and optionally platform and model. Use None if no mapping is available
# (code also handles missing key)
# please refer to https://pubhub.devnetcloud.com/media/unicon/docs/user_guide/supported_platforms.html#supported-platforms
# for supported device types
GenieDeviceOS: dict[str, tuple[str, ...] | None] = {
    DeviceType.AIRE_OS: ("aireos",),
    DeviceType.APIC: ("apic",),
    DeviceType.ASA: ("asa",),
    DeviceType.BROADWORKS: None,
    DeviceType.CATALYST_CENTER: None,
    DeviceType.CEDGE: ("iosxe", "sdwan"),
    DeviceType.CIMC: None,
    DeviceType.CISCO_AP_OS: ("iosxe", "c9800", "ewc_ap"),
    DeviceType.CML: None,
    DeviceType.CMS: None,
    DeviceType.CPS: ("linux",),
    DeviceType.CROSSWORK: None,
    DeviceType.CSPC: None,
    DeviceType.CUCM: None,
    DeviceType.CVOS: None,
    DeviceType.CVP: None,
    DeviceType.ESA: None,
    DeviceType.EXPRESSWAY: None,
    DeviceType.FDM: None,
    DeviceType.FMC: None,
    DeviceType.FTD: None,
    DeviceType.GENERIC: ("linux",),
    DeviceType.HYPERFLEX: None,
    DeviceType.INTERSIGHT: None,
    DeviceType.INTERSIGHT_API: None,
    DeviceType.IOS_XE: ("iosxe",),
    DeviceType.IOS_XR: ("iosxr",),
    DeviceType.ISE: None,
    DeviceType.LINUX: ("linux",),
    DeviceType.NCS_2000: None,
    DeviceType.NEXUS_DASHBOARD: None,
    DeviceType.NSO: ("nso",),
    DeviceType.NX_OS: ("nxos",),
    DeviceType.RADKIT_SERVICE: None,
    DeviceType.ROUTED_PON: None,
    DeviceType.SMA: None,
    DeviceType.SNA: None,
    DeviceType.SPLUNK: None,
    DeviceType.STAR_OS: ("staros",),
    DeviceType.UCCE: None,
    DeviceType.UCS_MANAGER: None,
    DeviceType.ULTRA_CORE_5G_AMF: None,
    DeviceType.ULTRA_CORE_5G_PCF: None,
    DeviceType.ULTRA_CORE_5G_SMF: None,
    DeviceType.WAS: None,
    DeviceType.WLC: ("iosxe", "c9800"),
    DeviceType.VMANAGE: None,
}


def _get_device_os_platform_from_radkitdevice(
    device: RADKitDevice,
) -> DeviceOsPlatform:
    """
    Get device OS, platform and model from ephemarl attributes (if set via
    fingerprint()), or from RADKit device type.
    """
    return get_device_os_platform(device.device_type, device.attributes.ephemeral)


def get_device_os_platform(
    device_type: str,
    ephemeral_attributes: Mapping[str, object],
) -> DeviceOsPlatform:
    """
    Get device OS, platform and model from ephemarl attributes (if set via
    fingerprint()), or from RADKit device type.
    """

    def _get_ephemeral_attributes(key: str) -> str | None:
        """
        Get ephemeral attribute value as string, or None if not set.
        """
        value = ephemeral_attributes.get(key)
        if value is not None:
            return str(value)  # cast from object type
        return None

    os: str | None = None
    platform: str | None = None
    model: str | None = None

    os = _get_ephemeral_attributes("os")
    if os:
        platform = _get_ephemeral_attributes("platform")
    else:
        genie_os_mapping: tuple[str, ...] | None = GenieDeviceOS.get(device_type)
        if genie_os_mapping is not None:
            os = genie_os_mapping[0]
            if len(genie_os_mapping) > 1:
                platform = genie_os_mapping[1]
            if len(genie_os_mapping) > 2:
                model = genie_os_mapping[2]

    return DeviceOsPlatform(os=os, platform=platform, model=model)


class Device(GenieDevice):  # type: ignore[misc] # Class cannot subclass "GenieDevice" (has type "Any")
    """
    RADKitGenie Device object
    """

    def __init__(
        self,
        device: RADKitDevice,
        os: str | None = None,
        exec_timeout: int | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Instantiate Genie device object based on RADKit Device passed.
        """
        self.radkitdevice = device

        if exec_timeout is not None:
            self.exec_timeout = exec_timeout
        else:
            self.exec_timeout = get_settings().exec_timeout

        if os is None:
            os_platform = _get_device_os_platform_from_radkitdevice(device)
            os = os_platform.os
            if not os:
                raise RADKitGenieMissingOS(
                    f"{device.name} is missing 'os' information, can't instantiate Device"
                )
            platform = os_platform.platform
            model = os_platform.model
        else:
            platform = None
            model = None

        # instantiate Genie Device object
        custom = {"abstraction": {"order": ["os"]}}
        super().__init__(
            device.name, os=os, custom=custom, platform=platform, model=model, **kwargs
        )

    def connect(self, *args: Any, **kwargs: Any) -> None:
        pass

    def disconnect(self, *args: Any, **kwargs: Any) -> None:
        pass

    # Overload the execute() method to return device command output
    # back to genie. This is needed for genie learn which interactively
    # collects device command output
    def execute(self, command: str, **kwargs: Any) -> str:
        logger.debug("Executing command", device_name=self.name, command=command)
        timeout = kwargs.get("timeout", self.exec_timeout)
        response = self.radkitdevice.exec(command, timeout=timeout).wait()
        if response.result is not None:
            try:
                return response.result.data
            except ClientError:
                raise RADKitGenieException(
                    f'Error executing "{command}" on device {self.name}: {response.result.status_message}'
                )
        else:
            raise RADKitGenieException(
                f'Unknown error executing "{command}" on device {self.name}'
            )

    # overload parse() method to support genie device api
    # this method is called from radkit_genie.parse() with output set,
    # and from genie's device api without it being set.
    def parse(self, parser: str, output: str | None = None) -> QDict:
        if output is None:
            output = self.execute(parser)
        return super().parse(parser, output=output)
