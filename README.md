# Koyoe for AUX-2

Read PV production, battery status and inverter measurements from a **Koyoe KY-EST20KH** over a local RS-485 connection. The tested route uses **Home Assistant Connect AUX-2** and the **Waveshare USB TO RS485 (B)**. Setup is through the Home Assistant UI and requires no YAML or vendor cloud account.

**Status:** Community preview by Smartdomo. The hardware route was tested on one KY-EST20KH. On 24 November 2026, HA-Test recorded 911 consecutive successful read cycles after the restart, with zero failed attempts. That observation was on the test build preceding this package. Other Koyoe models, board revisions and firmware combinations need their own verification.

| Readings | Examples |
| --- | --- |
| Solar | Live power, two PV inputs, daily and lifetime generation |
| Battery | State of charge, voltage, current and reported health |
| Inverter and grid | Temperature, phase voltages, frequency and signed power |
| Diagnostics | Last successful update, failed attempts and recovered cycles |

The integration sends Modbus read requests only. It does not change inverter, battery or grid settings.

## Install

1. Check the [hardware setup guide](docs/hardware.md) before wiring. Use Home Assistant 2026.11 or later. The tested installation used the `serialx` 1.15.1 library supplied by its Home Assistant version.
2. In HACS / Marketplace, open **Custom repositories** and add `https://github.com/ursolino69/koyoe-home-assistant` as an **Integration**. Download **Koyoe for AUX-2**. If the preview is hidden, enable pre-releases in the download dialog.
3. For manual installation, download and unpack the `koyoe-local-<version>.zip` asset from [Releases](https://github.com/ursolino69/koyoe-home-assistant/releases). Copy the complete `custom_components/koyoe_local` folder into the `custom_components` folder of your Home Assistant configuration directory. The final path is `/config/custom_components/koyoe_local/manifest.json` on HA OS.
4. Restart Home Assistant after a manual install or when replacing an existing version. Go to **Settings → Devices & services → Add integration → Koyoe for AUX-2**. Choose the AUX-2 **USB Serial Port**. The setup reads the inverter before saving the entry.
5. Open the device and check **Datenerfassung** (`ok`), **Letzte erfolgreiche Abfrage** and **Erfolgreiche Abfragen seit Start**. Check that the success counter increases and compare live PV and battery readings with the inverter display or vendor app. Sensor labels in this preview are German. Setup dialogs are available in German and English.

When upgrading the Smartdomo test build, back up its integration folder and keep the existing entry. This package keeps the `koyoe_local` domain and existing sensor identifiers. Restart after replacing the files. Before migrating the physical connection to a different HA instance, stop the old reader. Configure the AUX-2 on the destination instance and select its port there.

## Energy dashboard

Under **Settings → Dashboards → Energy → Solar production**, use **PV Ertrag gesamt** for production energy (kWh) and **PV Leistung** for production power (W). Use the lifetime counter even if you normally look at the daily reading. Home Assistant calculates production from changes in the counter, starting with the statistics it has collected.

This preview covers solar generation. Grid import, grid export and battery charge/discharge energy are outside the verified scope. Compare the lifetime counter against the inverter before relying on it for energy accounting.

## Troubleshooting

| What you see | What to check |
| --- | --- |
| USB Serial Port is missing | Confirm that AUX-2 is online in ESPHome and the exact Waveshare **(B)** model is plugged directly into USB-A. |
| Setup cannot read the inverter | Verify the PARA pinout for your revision, A/B polarity and address 247. Stop any other Modbus reader on this port. |
| Old `serialx==1.11.0` requirement conflict | Check that you replaced the complete legacy folder and restarted. This release requests `serialx>=1.15.1`. |
| Sensors briefly unavailable | Check the diagnostic counters and last error phase. A failed cycle is retried once with a fresh connection. If both attempts fail, the cycle’s measurements become unavailable and collection resumes on the next scheduled cycle. |
| Solar energy is initially zero | Allow Home Assistant to collect statistics and wait for the lifetime counter to increase. Check that **PV Ertrag gesamt** is selected. |

For a reproducible problem, [open an issue](https://github.com/ursolino69/koyoe-home-assistant/issues) with versions, hardware revision, adapter model and the first relevant error. Review diagnostics before sharing. They omit the port URI and credentials but contain measurements. Remove private data from logs and photos.

## Development

Run the focused protocol and diagnostic tests with `python -m unittest discover -v` after installing `serialx==1.15.1`. GitHub Actions also run Hassfest and HACS validation. This repository is a community integration distributed as a custom repository.

[Hardware setup](docs/hardware.md) · [Deutsch](docs/de.md) · [Changelog](CHANGELOG.md) · [MIT license](LICENSE)
