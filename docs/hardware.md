# KY-EST20KH hardware setup

**Tested path:** Koyoe KY-EST20KH → PARA RS-485 → Waveshare USB TO RS485 (B) → AUX-2 USB-A → local network → Home Assistant ESPHome integration → Koyoe integration.

## Parts and checks before wiring

- A Koyoe **KY-EST20KH** with the same PARA interface as described below.
- A Home Assistant Connect AUX-2 and a **Waveshare USB TO RS485 (B)** adapter. Use this exact suffix. The USB-A port is occupied by the adapter. Nabu Casa documents direct attachment and the supported adapter in its [USB dongle guide](https://support.nabucasa.com/hc/en-us/articles/40528805559965-Using-a-USB-to-serial-dongle).
- A suitable twisted pair for the RS-485 line, and power/network for AUX-2 according to the [official setup instructions](https://support.nabucasa.com/hc/en-us/articles/40527754954653-Set-up-Home-Assistant-Connect-AUX-2). Use the inverter installation manual and a qualified installer for access to its terminals and for shutdown/restart.

The tested connector is the **PARA** pair on the inverter communication terminal block. Koyoe documentation varies by revision, including which pins are marked ground and whether PARA is reserved. Confirm the connector, pin numbers and permitted use with the installer or manufacturer for your inverter before connecting. Pin numbers below describe the tested device, not the orientation of every terminal block.

## Data wiring on the tested device

| KY-EST20KH communication terminal | Label | Waveshare (B) |
| --- | --- | --- |
| Pin **9** | PARA-485-B | **B−** |
| Pin **10** | PARA-485-A | **A+** |

Use the printed labels and the confirmed terminal numbering. Cable colours are arbitrary. The confirmed mapping covers the two signal wires. If a signal ground or termination is needed, follow the manufacturer’s instructions for the exact hardware revision and bus topology. There is no universal ground-pin or termination setting in this guide. The tested setup required no DIP switch or EMS change. Existing BMS, meter and data logger wiring do not form part of the connection above.

## Connect and verify

1. With the inverter made safe by your installer, connect the data pair as above. Plug the Waveshare adapter directly into **USB-A on the AUX-2**. The AUX-2's two 3.5 mm serial ports are RS-232.
2. Power and join AUX-2 to the network by Ethernet or Wi-Fi. Add the AUX-2 to Home Assistant through **ESPHome**. Follow the [Nabu Casa Modbus guide](https://support.nabucasa.com/hc/en-us/articles/40528804425245-Using-Connect-AUX-2-with-Modbus-devices).
3. In Home Assistant open **Settings → Devices & services → ESPHome → Connect AUX-2**. Verify that **USB Serial Port** is available. Stop any other active Modbus client on the same bus, including a separate test HA instance.
4. Install Koyoe and select that port in the [integration setup](../README.md#install). The profile uses **Modbus RTU, device address 247, 9600 baud, 8N1**, with function 03 to read measurements. If your inverter uses a different address, this version will not read it. Verify the address in the inverter display or with the installer.
5. Check the success counter across at least two automatic updates. Compare battery charge, temperature and PV values with the display or app. Watch the failed-cycle count over a day before treating the data as dependable. A listed serial port only confirms that Home Assistant sees the bridge.

Use [official AUX-2 troubleshooting](https://support.nabucasa.com/hc/en-us/articles/40528982833565-Troubleshooting) for issues before the serial port appears. For Koyoe-specific issues, follow the [project troubleshooting table](../README.md#troubleshooting).
