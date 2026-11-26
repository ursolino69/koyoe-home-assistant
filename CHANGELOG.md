# Changelog

## 0.4.3 (community preview)

- Log each failed read attempt at DEBUG with the attempt number, error, register and phase. Enable debugging for `custom_components.koyoe_local` to collect these details during a field test.
- Log when communication returns after an outage, including when the first successful cycle required a retry.
- Use the original Koyoe logo in the README and Home Assistant, with its blue shield as the integration icon.

## 0.4.2 (community preview)

- Clear bounded pending input before the first request on a new connection. Reject a cycle if bytes arrive between requests, including after its final reply.
- Wait three seconds before the existing single retry. Keep measurement values unavailable when both attempts fail.
- Log the start of a sustained outage once. Diagnostic counters continue tracking failed attempts and cycles.

The transport changes passed 15 automated tests. Field verification of their effect on intermittent outages is pending.

## 0.4.1

- Use the English display name **Koyoe for AUX-2** in Home Assistant and HACS.

## 0.4.0

- First community preview of Koyoe für AUX-2 for Koyoe KY-EST20KH using Connect AUX-2 and Waveshare USB TO RS485 (B).
- Includes the 20 read-only measurements and 15 diagnostic entities from the test integration.
- Exposes the lifetime PV energy counter to Home Assistant's long-term statistics and Energy dashboard.
- Preserves the integration domain and existing sensor identifiers from 0.3.1.
- Adds the hardware guide, English and German setup dialogs, installation instructions and automated validation.
