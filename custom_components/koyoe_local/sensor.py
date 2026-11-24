"""Read-only test sensors; new register meanings need display comparison."""
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.const import EntityCategory
from . import DOMAIN
from .protocol import READINGS
from .diagnostic_runner import DIAGNOSTIC_KEYS

# name, unit, device class; V7 manufacturer protocol, 2025-04-10, pages 4,6-10.
META = {
    "status": ("Betriebszustand (Rohcode)", None, None),
    "heatsink_temperature": ("Kühlkörpertemperatur", "°C", "temperature"),
    "battery_soc": ("Batterieladestand", "%", "battery"),
    "pv1_voltage": ("PV1 Spannung", "V", "voltage"),
    "pv2_voltage": ("PV2 Spannung", "V", "voltage"),
    "pv1_current": ("PV1 Strom", "A", "current"),
    "pv2_current": ("PV2 Strom", "A", "current"),
    "grid_l1_voltage": ("Netz L1 Spannung", "V", "voltage"),
    "grid_l2_voltage": ("Netz L2 Spannung", "V", "voltage"),
    "grid_l3_voltage": ("Netz L3 Spannung", "V", "voltage"),
    "grid_frequency": ("Netzfrequenz", "Hz", "frequency"),
    "pv_power": ("PV Leistung", "W", "power"),
    "grid_power": ("Netz Wirkleistung (Vorzeichen prüfen)", "W", "power"),
    "inverter_power": ("Wechselrichter Wirkleistung", "W", "power"),
    "load_power": ("Lokale Lastleistung", "W", "power"),
    "battery_current": ("Batteriestrom (Vorzeichen prüfen)", "A", "current"),
    "battery_voltage": ("Batteriespannung", "V", "voltage"),
    "battery_soh": ("Batterie Gesundheitszustand", "%", None),
    "pv_energy_today": ("PV Ertrag heute", "kWh", "energy"),
    "pv_energy_total": ("PV Ertrag gesamt", "kWh", "energy"),
    "poll_cycles": ("Abfragezyklen seit Start", None, None),
    "read_attempts": ("Leseversuche seit Start", None, None),
    "failed_attempts": ("Fehlgeschlagene Leseversuche", None, None),
    "failed_cycles": ("Fehlgeschlagene Abfragezyklen", None, None),
    "retry_recoveries": ("Durch Wiederholung gerettete Zyklen", None, None),
    "consecutive_failed_cycles": ("Fehlerzyklen in Folge", None, None),
    "last_error": ("Letzter Lesefehler", None, None),
    "last_error_time": ("Zeitpunkt letzter Lesefehler", None, "timestamp"),
    "last_error_register": ("Letztes Fehlerregister", None, None),
    "last_error_phase": ("Letzte Fehlerphase", None, None),
    "poll_duration": ("Dauer letzter Abfragezyklus", "s", "duration"),
    "collection_state": ("Datenerfassung", None, None),
    "last_success": ("Letzte erfolgreiche Abfrage", None, "timestamp"),
    "successful_polls": ("Erfolgreiche Abfragen seit Start", None, None),
    "unsupported_registers": ("Nicht verfügbare Testregister", None, None),
}

async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(KoyoeSensor(entry, key) for key in META)

class KoyoeSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, entry, key):
        super().__init__(entry.runtime_data)
        self.key = key
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)}, manufacturer="Koyoe",
            model="KY-EST20KH", name="Koyoe KY-EST20KH",
        )
        self._attr_name, self._attr_native_unit_of_measurement, device_class = META[key]
        if device_class:
            self._attr_device_class = SensorDeviceClass(device_class)
        if key in DIAGNOSTIC_KEYS:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        elif key == "pv_energy_total":
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        elif self._attr_native_unit_of_measurement and device_class != "energy":
            self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_extra_state_attributes = {}
        if key in READINGS:
            self._attr_extra_state_attributes.update({
                "modbus_register": READINGS[key][0],
                "validation": "display_compared" if key in ("status", "heatsink_temperature", "battery_soc") else "experimental_manufacturer_v7",
            })

    @property
    def available(self):
        return super().available and self.coordinator.data.get(self.key) is not None

    @property
    def native_value(self):
        return self.coordinator.data.get(self.key)
