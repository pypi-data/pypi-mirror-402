"""Data classes for Redback Tech API"""

from __future__ import annotations

from dataclasses import dataclass
import datetime
from typing import Any, Optional


@dataclass
class RedbackTechData:
    """Dataclass for all RedbackTech Data."""

    user_id: str
    openvelopes: Optional[dict[int, Any]] = None
    text: Optional[dict[int, Any]] = None
    entities: Optional[dict[int, Any]] = None
    devices: Optional[dict[int, Any]] = None
    numbers: Optional[dict[int, Any]] = None
    buttons: Optional[dict[int, Any]] = None
    schedules: Optional[dict[int, Any]] = None
    selects: Optional[dict[int, Any]] = None
    schedules_datetime_data: Optional[dict[int, Any]] = None
    inverter_calendar: Optional[dict[int, Any]] = None
    envelope_calendar: Optional[dict[int, Any]] = None


@dataclass
class Site:
    """Dataclass for Redback Sites."""

    id: str
    data: dict[str, Any]
    type: str


@dataclass
class RedbackEntitys:
    entity_id: str
    device_id: str
    data: dict[str, Any]
    type: Optional[str] = None
    device_data: Optional[dict[str, Any]] = None


@dataclass
class Inverters:
    """Dataclass for Redback Inverters."""

    id: str
    device_serial_number: str
    data: dict[str, Any]
    type: str


@dataclass
class OpEnvelopes:
    """Dataclass for Redback Inverters."""

    id: str
    site_id: str
    data: dict[str, Any]


@dataclass
class Batterys:
    """Dataclass for RedBack Batteries."""

    id: str
    device_serial_number: str
    data: dict[str, Any]
    type: str


@dataclass
class DeviceInfo:
    """Dataclass for Device Info."""

    identifiers: str
    name: str
    model: str
    sw_version: str
    hw_version: str
    serial_number: str


@dataclass
class Numbers:
    """Dataclass for Redback Inverters."""

    id: str
    device_serial_number: str
    data: dict[str, Any]
    type: str


@dataclass
class ActiveSchedule:
    """Dataclass for Redback Inverters."""

    id: str
    device_serial_number: str
    data: dict[str, Any]
    type: str


@dataclass
class Buttons:
    """Dataclass for Redback Inverters."""

    id: str
    device_serial_number: str
    data: dict[str, Any]
    type: str


@dataclass
class Text:
    """Dataclass for Redback Inverters."""

    id: str
    site_id: str
    data: dict[str, Any]


@dataclass
class Selects:
    """Dataclass for Redback Inverters."""

    id: str
    device_serial_number: str
    data: dict[str, Any]
    type: str


@dataclass
class ScheduleDateTime:
    """Dataclass for Redback Inverters."""

    id: str
    device_serial_number: str
    data: dict[str, Any]
    type: str


@dataclass
class ScheduleInfo:
    """Dataclass for Schedule Info."""

    schedule_id: str
    device_serial_number: str
    start_time: datetime.datetime
    data: dict[str, Any]


