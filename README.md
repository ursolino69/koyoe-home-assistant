# Koyoe for AUX-2

<img src="custom_components/koyoe_local/brand/logo.png" alt="Koyoe" width="172" />

Read PV production, battery status and inverter measurements from a **Koyoe KY-EST20KH** over a local RS-485 connection. Set up the integration in the Home Assistant UI without YAML or a vendor cloud account.

**Status:** Community preview by Smartdomo. Hardware-tested on one **KY-EST20KH** using **Home Assistant Connect AUX-2** and **Waveshare USB TO RS485 (B)** at **Modbus address 247**. Confirm the PARA terminal assignment for your hardware revision before wiring. [Hardware guide](docs/hardware.md)

**Other KY-ESTxxKH models awaiting hardware verification:** KY-EST06KH, KY-EST08KH, KY-EST10KH, KY-EST12KH, KY-EST15KH and KY-EST17KH.

On 24 November 2026, a build preceding v0.4.3 recorded 911 consecutive successful read cycles on the test system, with zero failed attempts. This is the historical test baseline.

| Readings | Examples |
| --- | --- |
| Solar | Live power, two PV inputs, daily and lifetime generation |
| Battery | State of charge, voltage, current and reported health |
| Inverter and grid | Temperature, phase voltages, frequency and signed power |
| Diagnostics | Last successful update, failed attempts and recovered cycles |

The integration sends Modbus read requests only. It does not change inverter, battery or grid settings.

## Install

Use Home Assistant **2026.11 or later**. Connect the inverter and add the AUX-2 in ESPHome first. [Hardware setup guide](docs/hardware.md)

### Marketplace

1. In Home Assistant, open **Settings → Marketplace → Add from link**. Enter `https://github.com/ursolino69/koyoe-home-assistant`. Connect your GitHub account when prompted and select **Integration** if the Marketplace asks for a type.
2. Open **Koyoe for AUX-2** and select **v0.4.3** if offered. It is a GitHub pre-release. To enable pre-releases, open the repository's device under **Settings → Devices & services → Marketplace**, enable its **Pre-release** entity and turn on the switch. If that device or version is unavailable on your first install, use the ZIP below. [Marketplace documentation](https://www.home-assistant.io/integrations/marketplace/)

After a Marketplace update, restart Home Assistant to apply it.

### Manual ZIP installation

Download the ZIP and unpack it. Copy the complete `custom_components/koyoe_local` folder into your Home Assistant configuration directory's `custom_components` folder. On HA OS, verify that `/config/custom_components/koyoe_local/manifest.json` exists. Restart Home Assistant. [Download v0.4.3 ZIP](https://github.com/ursolino69/koyoe-home-assistant/releases/download/v0.4.3/koyoe-local-0.4.3.zip)

### Add the integration

1. Open **Settings → Devices & services → Add integration → Koyoe for AUX-2**. Select the USB adapter entry under the name of your AUX-2. Home Assistant may label it **USB Serial Port** or show a longer identifier containing `USB_Single_Serial`. The setup reads the inverter before saving the entry.
2. Open the device and check **Datenerfassung** (`ok`), **Letzte erfolgreiche Abfrage** and **Erfolgreiche Abfragen seit Start**. Check that the success counter increases and compare live PV and battery readings with the inverter display or vendor app. Sensor labels in this preview are German. Setup dialogs are available in German and English.

When upgrading the Smartdomo test build, back up its integration folder and keep the existing entry. This package keeps the `koyoe_local` domain and existing sensor identifiers. Restart after replacing the files. Before migrating the physical connection to a different HA instance, stop the old reader. Configure the AUX-2 on the destination instance and select its port there.

## Energy dashboard

Under **Settings → Dashboards → Energy → Solar production**, use **PV Ertrag gesamt** for production energy (kWh) and **PV Leistung** for production power (W). Use the lifetime counter even if you normally look at the daily reading. Home Assistant calculates production from changes in the counter, starting with the statistics it has collected.

This preview covers solar generation. Grid import, grid export and battery charge/discharge energy are outside the verified scope. Compare the lifetime counter against the inverter before relying on it for energy accounting.

## Troubleshooting

| What you see | What to check |
| --- | --- |
| The AUX-2 USB port is missing | Look for **USB Serial Port** or `USB_Single_Serial` under your AUX-2. Confirm that the AUX-2 is online in ESPHome and the Waveshare **(B)** is plugged directly into USB-A. |
| Setup cannot read the inverter | Verify the PARA pinout for your revision, A/B polarity and address 247. Stop any other Modbus reader on this port. |
| Old `serialx==1.11.0` requirement conflict | Check that you replaced the complete legacy folder and restarted. This release requests `serialx>=1.15.1`. |
| Sensors briefly unavailable | Check the diagnostic counters and last error phase. A failed cycle is retried once with a fresh connection. If both attempts fail, the cycle’s measurements become unavailable and collection resumes on the next scheduled cycle. |
| Solar energy is initially zero | Allow Home Assistant to collect statistics and wait for the lifetime counter to increase. Check that **PV Ertrag gesamt** is selected. |

For a reproducible problem, [open an issue](https://github.com/ursolino69/koyoe-home-assistant/issues) with versions, hardware revision, adapter model and the first relevant error. Review diagnostics before sharing. They omit the port URI and credentials but contain measurements. Remove private data from logs and photos.

## Development

Run the focused protocol and diagnostic tests with `python -m unittest discover -v` after installing `serialx==1.15.1`. GitHub Actions also run Hassfest and HACS validation. This repository is a community integration distributed as a custom repository.

[Hardware setup](docs/hardware.md) · [Deutsch](docs/de.md) · [Changelog](CHANGELOG.md) · [MIT license](LICENSE)
