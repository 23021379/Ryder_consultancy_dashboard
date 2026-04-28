"""
Completely Generated

backend/sensors.py
──────────────────
Abstract base class for the sensor backend, plus a FakeSensorBackend
implementation that returns realistic-looking static data.

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class SensorReading:
    """One telemetry channel belonging to a SensorDevice."""
    key: str            # machine key, e.g. "supply_temp_c"
    label: str          # human label, e.g. "Supply Air Temp"
    value: float | str | bool
    unit: str           # "°C", "kW", "ppm", … (empty string if dimensionless)
    last_updated: str   # ISO-8601 or human string for fake data


@dataclass
class SensorDevice:
    """
    A named physical device that exposes one or more sensor channels.

    `status` is the top-level health signal rendered on the floor plan.
    It is provided by the backend (and will later be overridden by an
    AI inference step).

    Allowed status values:  "ok" | "warning" | "alert" | "offline"
    """
    id: str
    name: str
    group: str
    device_type: str        # e.g. "HVAC", "Electrical Panel", "BMS Node"
    x_pct: float            # position on floor plan image, 0–100
    y_pct: float
    status: str
    status_reason: str      # one-line explanation shown in the detail panel
    readings: list[SensorReading] = field(default_factory=list)


@dataclass
class FloorPlan:
    """Metadata describing one floor-plan image."""
    name: str
    level: str
    image_path: Optional[str]   # None → use placeholder canvas
    width_m: float
    height_m: float


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

class SensorBackendBase(ABC):
    """
    Contract every backend must fulfil.  All methods are synchronous;
    wrap in an executor on the Streamlit side if async is required.
    """

    @abstractmethod
    def get_floor_plans(self) -> list[FloorPlan]:
        """Return all available floor plans."""

    @abstractmethod
    def get_devices(self, floor_plan_name: str) -> list[SensorDevice]:
        """
        Return every SensorDevice placed on the given floor plan,
        including current readings and status.
        """

    @abstractmethod
    def get_device(self, device_id: str) -> Optional[SensorDevice]:
        """Return a single device by id, or None if not found."""

    @abstractmethod
    def health_check(self) -> bool:
        """Return True when the backend is reachable and healthy."""


# ---------------------------------------------------------------------------
# Fake / stub implementation
# ---------------------------------------------------------------------------

class FakeSensorBackend(SensorBackendBase):
    """
    Deterministic stub that returns plausible hospital sensor data.

    To connect to a real platform, subclass SensorBackendBase and
    implement the four abstract methods.  Example:

        class AzureIoTBackend(SensorBackendBase):
            def __init__(self, connection_string: str): ...
            def get_floor_plans(self): ...
            ...
    """

    _DEVICES: list[dict] = [
        {
            "id": "hvac_01",
            "name": "HVAC Unit 1",
            "group": "Mechanical",
            "device_type": "HVAC",
            "x_pct": 18.0, "y_pct": 22.0,
            "status": "ok",
            "status_reason": "All parameters within normal range",
            "readings": [
                {"key": "supply_temp_c",  "label": "Supply Air Temp",     "value": 18.4,  "unit": "°C",   "last_updated": "10s ago"},
                {"key": "return_temp_c",  "label": "Return Air Temp",     "value": 22.1,  "unit": "°C",   "last_updated": "10s ago"},
                {"key": "power_kw",       "label": "Power Draw",          "value": 12.3,  "unit": "kW",   "last_updated": "10s ago"},
                {"key": "airflow_m3h",    "label": "Airflow",             "value": 4200,  "unit": "m³/h", "last_updated": "10s ago"},
                {"key": "filter_dp_pa",   "label": "Filter Differential", "value": 85,    "unit": "Pa",   "last_updated": "10s ago"},
            ],
        },
        {
            "id": "hvac_02",
            "name": "HVAC Unit 2",
            "group": "Mechanical",
            "device_type": "HVAC",
            "x_pct": 68.0, "y_pct": 18.0,
            "status": "warning",
            "status_reason": "Filter differential pressure elevated — service overdue",
            "readings": [
                {"key": "supply_temp_c",  "label": "Supply Air Temp",     "value": 19.1,  "unit": "°C",   "last_updated": "10s ago"},
                {"key": "return_temp_c",  "label": "Return Air Temp",     "value": 23.4,  "unit": "°C",   "last_updated": "10s ago"},
                {"key": "power_kw",       "label": "Power Draw",          "value": 14.7,  "unit": "kW",   "last_updated": "10s ago"},
                {"key": "airflow_m3h",    "label": "Airflow",             "value": 3850,  "unit": "m³/h", "last_updated": "10s ago"},
                {"key": "filter_dp_pa",   "label": "Filter Differential", "value": 210,   "unit": "Pa",   "last_updated": "10s ago"},
            ],
        },
        {
            "id": "elec_panel_a",
            "name": "Electrical Panel A",
            "group": "Electrical",
            "device_type": "Electrical Panel",
            "x_pct": 35.0, "y_pct": 55.0,
            "status": "ok",
            "status_reason": "Load balanced, no faults detected",
            "readings": [
                {"key": "load_kw",    "label": "Active Load",     "value": 87.4,  "unit": "kW", "last_updated": "5s ago"},
                {"key": "voltage_v",  "label": "Supply Voltage",  "value": 231.2, "unit": "V",  "last_updated": "5s ago"},
                {"key": "current_a",  "label": "Current",         "value": 378,   "unit": "A",  "last_updated": "5s ago"},
                {"key": "pf",         "label": "Power Factor",    "value": 0.96,  "unit": "",   "last_updated": "5s ago"},
                {"key": "thd_pct",    "label": "THD",             "value": 3.1,   "unit": "%",  "last_updated": "5s ago"},
            ],
        },
        {
            "id": "elec_panel_b",
            "name": "Electrical Panel B",
            "group": "Electrical",
            "device_type": "Electrical Panel",
            "x_pct": 78.0, "y_pct": 60.0,
            "status": "alert",
            "status_reason": "Phase imbalance detected — investigate immediately",
            "readings": [
                {"key": "load_kw",    "label": "Active Load",     "value": 103.1, "unit": "kW", "last_updated": "5s ago"},
                {"key": "voltage_v",  "label": "Supply Voltage",  "value": 228.7, "unit": "V",  "last_updated": "5s ago"},
                {"key": "current_a",  "label": "Current",         "value": 451,   "unit": "A",  "last_updated": "5s ago"},
                {"key": "pf",         "label": "Power Factor",    "value": 0.81,  "unit": "",   "last_updated": "5s ago"},
                {"key": "thd_pct",    "label": "THD",             "value": 8.9,   "unit": "%",  "last_updated": "5s ago"},
            ],
        },
        {
            "id": "bms_ward3",
            "name": "BMS Node — Ward 3",
            "group": "Building Management",
            "device_type": "BMS Node",
            "x_pct": 52.0, "y_pct": 38.0,
            "status": "ok",
            "status_reason": "All zones within setpoint",
            "readings": [
                {"key": "zone_temp_c",    "label": "Zone Temperature",    "value": 21.5,  "unit": "°C",  "last_updated": "30s ago"},
                {"key": "humidity_pct",   "label": "Relative Humidity",   "value": 48.2,  "unit": "%",   "last_updated": "30s ago"},
                {"key": "co2_ppm",        "label": "CO2 Level",           "value": 612,   "unit": "ppm", "last_updated": "30s ago"},
                {"key": "occupancy",      "label": "Occupancy",           "value": True,  "unit": "",    "last_updated": "30s ago"},
                {"key": "setpoint_c",     "label": "Temp Setpoint",       "value": 21.0,  "unit": "°C",  "last_updated": "30s ago"},
            ],
        },
        {
            "id": "bms_icu",
            "name": "BMS Node — ICU",
            "group": "Building Management",
            "device_type": "BMS Node",
            "x_pct": 22.0, "y_pct": 72.0,
            "status": "warning",
            "status_reason": "CO2 rising — ventilation may be undersized for current occupancy",
            "readings": [
                {"key": "zone_temp_c",    "label": "Zone Temperature",    "value": 22.8,  "unit": "°C",  "last_updated": "30s ago"},
                {"key": "humidity_pct",   "label": "Relative Humidity",   "value": 55.1,  "unit": "%",   "last_updated": "30s ago"},
                {"key": "co2_ppm",        "label": "CO2 Level",           "value": 1180,  "unit": "ppm", "last_updated": "30s ago"},
                {"key": "occupancy",      "label": "Occupancy",           "value": True,  "unit": "",    "last_updated": "30s ago"},
                {"key": "setpoint_c",     "label": "Temp Setpoint",       "value": 22.0,  "unit": "°C",  "last_updated": "30s ago"},
            ],
        },
        {
            "id": "ups_server",
            "name": "UPS — Server Room",
            "group": "Electrical",
            "device_type": "UPS",
            "x_pct": 88.0, "y_pct": 35.0,
            "status": "ok",
            "status_reason": "Battery at 94 %, runtime 28 min at current load",
            "readings": [
                {"key": "battery_pct",  "label": "Battery Charge",  "value": 94,    "unit": "%",   "last_updated": "1m ago"},
                {"key": "load_pct",     "label": "Load",            "value": 61,    "unit": "%",   "last_updated": "1m ago"},
                {"key": "runtime_min",  "label": "Est. Runtime",    "value": 28,    "unit": "min", "last_updated": "1m ago"},
                {"key": "input_v",      "label": "Input Voltage",   "value": 230.1, "unit": "V",   "last_updated": "1m ago"},
                {"key": "output_v",     "label": "Output Voltage",  "value": 230.0, "unit": "V",   "last_updated": "1m ago"},
            ],
        },
        {
            "id": "water_main",
            "name": "Water Meter — Main",
            "group": "Utilities",
            "device_type": "Water Meter",
            "x_pct": 45.0, "y_pct": 80.0,
            "status": "offline",
            "status_reason": "No telemetry received in 14 minutes",
            "readings": [
                {"key": "flow_lpm",       "label": "Flow Rate",         "value": "N/A", "unit": "L/min", "last_updated": "14m ago"},
                {"key": "total_m3",       "label": "Total Consumption", "value": "N/A", "unit": "m³",    "last_updated": "14m ago"},
                {"key": "pressure_bar",   "label": "Pressure",          "value": "N/A", "unit": "bar",   "last_updated": "14m ago"},
            ],
        },
    ]

    def get_floor_plans(self) -> list[FloorPlan]:
        return [
            FloorPlan(name="Ground Floor", level="Level 0", image_path=None, width_m=120.0, height_m=80.0),
            FloorPlan(name="Level 1",      level="Level 1", image_path=None, width_m=120.0, height_m=80.0),
        ]

    def get_devices(self, floor_plan_name: str) -> list[SensorDevice]:
        return [
            SensorDevice(
                id=d["id"], name=d["name"], group=d["group"],
                device_type=d["device_type"],
                x_pct=d["x_pct"], y_pct=d["y_pct"],
                status=d["status"], status_reason=d["status_reason"],
                readings=[SensorReading(**r) for r in d["readings"]],
            )
            for d in self._DEVICES
        ]

    def get_device(self, device_id: str) -> Optional[SensorDevice]:
        return next((d for d in self.get_devices("") if d.id == device_id), None)

    def health_check(self) -> bool:
        return True
