# This file is part of RADKit / Lazy Maestro <radkit@cisco.com>
# Copyright (c) 2018-2025 by Cisco Systems, Inc.
# All rights reserved.

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any

from genie.conf.base.utils import QDict  # type:ignore[import-untyped]
from genie.libs.conf.device import Device as GenieDevice  # type:ignore[import-untyped]
from genie.libs.parser.utils import get_parser_exclude  # type:ignore[import-untyped]

from radkit_client.async_ import ExecError, ExecRecord, ExecStatus
from radkit_client.async_.formatting import (
    SmartMappingPtRepr,
    SmartMappingRepr,
    SmartPtRepr,
    SmartRepr,
)
from radkit_client.sync.exec import ExecResponse_ByDevice_ByCommand, ExecResponseBase
from radkit_common import nglog
from radkit_genie.devices import get_device_os_platform
from radkit_genie.exceptions import RADKitGenieException, RADKitGenieMissingOS


class GenieResultStatus(Enum):
    FAILURE = "FAILURE"
    SUCCESS = "SUCCESS"


class GenieParseResult(Mapping[str, QDict]):
    # Custom result type for execresult.data as we need
    # to carry exclude information (hidden from the user, but
    # used internally by genie diff)

    __repr__ = SmartMappingRepr["GenieParseResult"]()

    def __init__(
        self,
        data: QDict,
        exclude: list[str] | None = None,
    ) -> None:
        self._data = data
        self._exclude = exclude

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    @property
    def exclude(self) -> list[str] | None:
        return self._exclude

    @property
    def q(self) -> Any:
        return self._data.q

    def copy(self) -> QDict:
        return self._data.copy()


@dataclass(repr=False)
class GenieSingleResult:
    # don't display result "data" as it's typically far too long to be displayed on screen
    __repr__ = SmartRepr["GenieSingleResult"](fields=["status", "status_message"])
    __pt_repr__ = SmartPtRepr["GenieSingleResult"](
        fields=["status_message", "data"],
        with_status=True,
    )
    data: QDict | None
    status: GenieResultStatus
    status_message: str
    exclude: list[str] | None = None


class GenieDeviceResult(dict[str, GenieSingleResult]):
    __repr__ = SmartMappingRepr["GenieDeviceResult"]()
    __pt_repr__ = SmartMappingPtRepr["GenieDeviceResult"](
        key_name="command",
    )

    @property
    def success_count(self) -> int:
        count = 0
        for single_result in self.values():
            if single_result.status == GenieResultStatus.SUCCESS:
                count += 1
        return count

    @property
    def fail_count(self) -> int:
        return len(self) - self.success_count


class GenieResult(dict[str, GenieDeviceResult]):
    __repr__ = SmartMappingRepr["GenieResult"]()
    __pt_repr__ = SmartMappingPtRepr["GenieResult"](
        fields=["commands", "success_count", "fail_count"],
        getters={
            "commands": lambda obj: list(obj),
        },
    )

    def to_dict(self, add_exclude: bool = False) -> QDict:
        """
        convert GenieResult to a dict (actually: QDict()) to allow for easier parsing

        :param add_exclude: Add information about excluded keys which genie diff would exclude
            when comparing two results (default: False)
        """
        result: dict[str, Any] = {}
        for dev, res in self.items():
            for cmd, output in res.items():
                if output.data is not None:
                    result.setdefault(dev, {})[cmd] = output.data.copy()
                    if add_exclude and output.exclude:
                        result[dev][cmd]["_exclude"] = output.exclude
                else:
                    result.setdefault(dev, {})[cmd] = None

        return QDict(result)


tGENIE = nglog.Tags.GENIE
logger = nglog.getAdapter(__name__, tags=[tGENIE])


def parse(
    radkitrequest: ExecResponseBase[Any],
    parser: str | None = None,
    os: str | None = None,
    skip_unknown_os: bool = False,
) -> ExecResponse_ByDevice_ByCommand[GenieParseResult]:
    """
    .. USERFACING

    This function uses Genie parsers to parse command output returned
    by RADKit Client's :meth:`Device.exec() <radkit_client.device.Device.exec>`
    call into structured data.

    Please check https://pubhub.devnetcloud.com/media/genie-feature-browser/docs/#/parsers
    for supported parsers. Genie tries to search for the relevant parser based on the
    command executed (using fuzzy search); if the search fails, you can provide the parser
    and the OS manually.

    This method returns the same result type as RADKit Client's :meth:`Device.exec() <radkit_client.device.Device.exec>`,
    and the result can be post-processed using the same methods like by_device, by_status etc.

    Please note the following behavioural changes compared to previous versions (1.8.x and earlier) of radkit_genie.parse():

    *   Accessing `data` from unsuccessful parsing will raise an ExecError exception.
    *   The return type no longer supports the ``to_dict()`` method to convert the result structure into a
        genie ``QDict`` which can be parsed using Genie's `dq method
        <https://pubhub.devnetcloud.com/media/genie-docs/docs/userguide/utils/index.html#dq>`_.
        This can be achieved using :meth:`radkit_genie.to_dict() <radkit_genie.to_dict>`

    :param radkitrequest: return value of RADKit Client's :meth:`Device.exec() <radkit_client.device.Device.exec>` call
    :param parser: parser to choose (if omitted, the parser is derived from the command issued)
    :param os: the genie device OS. If this option is omitted, the OS found by :func:`radkit_genie.fingerprint()` is
        used; else the RADKit Device Type is used. If none of the previous result in a valid genie device OS,
        this parameter is mandatory)
    :param skip_unknown_os: this parameter is now ignored for the ``parse()`` function and will be removed in a future release.
    :return: ``ExecResponse_ByDevice_ByCommand`` structure, use ``result[device][cmd].data`` to access the parsed data
    :raises: :exc:`RADKitGenieMissingOS <radkit_genie.RADKitGenieMissingOS>` if a device OS is missing

    Examples:

        .. code:: python

            # Parse the output from a single device and a single command, specifying the OS explicitly
            single_response = service.inventory['devicename'].exec('show ip route').wait()
            result = radkit_genie.parse(single_response, os='iosxe')
            parsed_data = result['devicename']['show ip route'].data

            # Parse the output from multiple devices and multiple commands, leveraging RADkit device type
            # to genie OS mapping
            multi_response = service.inventory.filter('name', 'Edge').exec(['show ip route', 'show version']).wait()
            parsed = radkit_genie.parse(multi_response)
            for device in parsed.keys():
                parsed_routes = parsed[device]['show ip route'].data
                parsed_version = parsed[device]['show version'].data

    """

    def _genie_parser_map(entry: ExecRecord[str]) -> GenieParseResult:
        """
        Perform the actual parsing of the command output using Genie.
        """

        try:
            if os is None:
                os_platform = get_device_os_platform(
                    entry.device_type, entry.device_attributes_ephemeral
                )
                device_os = os_platform.os
                if not device_os:
                    raise RADKitGenieMissingOS(
                        f"{entry.device_name} is missing 'os' information"
                    )
                platform = os_platform.platform
                model = os_platform.model
            else:
                device_os = os
                platform = None
                model = None

            _parser = parser or entry.command
            parsed_data, exclude = _genie_parse_text(
                entry.data, _parser, device_os, platform, model
            )
        except (
            BaseException
        ) as e:  # genie parsers can raise many different exceptions, impossible to know
            logger.error(
                "Genie exception",
                command=entry.command,
                device_name=entry.device_name,
                err=e,
            )
            raise e

        return GenieParseResult(
            data=parsed_data,
            exclude=exclude,
        )

    if parser:
        if len(list(radkitrequest.by_command.keys())) > 1:
            raise ValueError(
                "parser hint option only supported with single-command responses"
            )
        else:
            logger.debug("Using genie parser", parser=parser)

    if len(radkitrequest.by_status[ExecStatus.PROCESSING]) > 0:
        raise RADKitGenieException(
            "Error, cannot parse requests which are still being processed"
        )

    result = radkitrequest.map(_genie_parser_map)
    # ensure that we keep the same return structure as legacy radkit_genie.parse()
    return result.by_device_by_command


def parsed_to_dict(
    parsed: ExecResponseBase[GenieParseResult],
    add_exclude: bool = False,
) -> QDict:
    """
    Convert the parsed output of a RADKit exec call into a genie QDict structure.

    :param parsed: parsed output of a previous radkit_genie.parse() call
    :param add_exclude: Add information about excluded keys which genie diff would exclude
        when comparing two results (default: False)
    :return: QDict structure containing the parsed data

    """
    result: dict[str, Any] = {}
    for dev, cmds in parsed.by_device_by_command.items():
        for cmd, output in cmds.items():
            try:
                data = output.data.copy()
            except ExecError:
                data = None
            result.setdefault(dev, {})[cmd] = data
            if data and add_exclude and output.data.exclude:
                result[dev][cmd]["_exclude"] = output.data.exclude

    return QDict(result)


def _genie_parse_text(
    text: str,
    parser: str,
    os: str,
    platform: str | None = None,
    model: str | None = None,
) -> tuple[QDict, list[str]]:
    """
    helper function to parse text using genie parser. Any exceptions raised from genie functions need to be
    caught by the caller if desired
    """
    geniedevice = GenieDevice(
        "_",
        os=os,
        platform=platform,
        model=model,
        custom={"abstraction": {"order": ["os"]}},
    )
    parsed_output = geniedevice.parse(parser, output=text)
    exclude = get_parser_exclude(parser, geniedevice)
    return parsed_output, exclude


def parse_text(
    text: str,
    parser: str,
    os: str,
) -> QDict:
    """
    .. USERFACING

    While radkit_genie's :func:`parse() <radkit_genie.parse>` function is most commonly invoked
    when dealing with parsing the output of the RADKit :meth:`Device.exec() <radkit_client.sync.device.Device.exec()>` call,
    we also provide a convenience function to invoke Genie's parsers on raw text output, for example collected
    as part of RADKit's exec-sequence.

    This method expects the output of a single command, the parser to be used (i.e. the command executed) and the
    device's operating system (os).

    Please check https://pubhub.devnetcloud.com/media/genie-feature-browser/docs/#/parsers
    for supported parsers.

    :param text: the text output of a single command
    :param parser: parser to choose (typically the command executed)
    :param os: the genie device OS (mandatory)
    :param platform: the genie device platform (optional)
    :param model: the genie device model (optional)
    :return: ``dict`` structure as returned by Genie's parse method

    Examples:

        .. code:: python

            # Parse the output from a device output
            parsed_result = radkit_genie.parse_text(output, "show version", "iosxe")
            version = parsed_result["version"]["xe_version"]
            serial = parsed_result["version"]["chassis_sn"]

    """

    if not isinstance(text, str):
        raise TypeError("Please pass plain text output as input to this function")

    return _genie_parse_text(text, parser, os)[0]
