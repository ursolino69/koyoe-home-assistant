# Koyoe for AUX-2 in Home Assistant

Die Community-Vorabversion liest PV-Erzeugung, Batteriewerte und Daten des Wechselrichters lokal aus. Der Hardwaretest erfolgte an einem **KY-EST20KH** mit **Connect AUX-2**, **Waveshare USB TO RS485 (B)** und **Modbus-Adresse 247**. Für KY-EST06KH, KY-EST08KH, KY-EST10KH, KY-EST12KH, KY-EST15KH und KY-EST17KH steht der Hardwaretest noch aus.

## Hardware vorbereiten

Prüfe das genaue Modell und die Klemmenbelegung mit dem Installateur oder Hersteller. Am Testgerät ist **PARA Pin 9 (B)** mit **B−** und **PARA Pin 10 (A)** mit **A+** am Waveshare-Adapter verbunden. Die Herstellerunterlagen unterscheiden sich je nach Revision. Lass die Verdrahtung am Wechselrichter fachgerecht vornehmen und die Signalmasse sowie Terminierung für deine Anlage prüfen. [Anschlussanleitung](hardware.md)

Stecke den Waveshare **(B)** direkt in den USB-A-Anschluss des AUX-2 und binde den AUX-2 über **ESPHome** ein. Beende vor einem Wechsel des Home-Assistant-Systems die Abfrage im bisherigen System, damit nur ein Modbus-Client denselben Bus nutzt.

## Installieren

Voraussetzung ist Home Assistant **2026.11 oder neuer**.

1. Öffne **Einstellungen → Marketplace → Per Link hinzufügen** (**Add from link**) und gib `https://github.com/ursolino69/koyoe-home-assistant` ein. Verbinde dein GitHub-Konto, wenn du dazu aufgefordert wirst, und wähle bei Bedarf den Typ **Integration**.
2. Öffne **Koyoe for AUX-2** und wähle **v0.4.3**, wenn sie angeboten wird. Die Version ist als Vorabversion veröffentlicht. Öffne zum Aktivieren von Vorabversionen unter **Einstellungen → Geräte & Dienste → Marketplace** das Gerät des Repositorys. Aktiviere die Entität **Vorabversion** (**Pre-release**) und schalte sie ein. Fehlen Gerät oder Version bei der Erstinstallation, verwende das ZIP. [Marketplace-Anleitung](https://www.home-assistant.io/integrations/marketplace/)

Starte Home Assistant nach einem Update über den Marketplace neu.

Für die **manuelle Installation** entpackst du das ZIP und kopierst den vollständigen Ordner `custom_components/koyoe_local` in den Ordner `custom_components` deiner Home-Assistant-Konfiguration. Unter HA OS lautet der vollständige Pfad zur Manifestdatei `/config/custom_components/koyoe_local/manifest.json`. Starte Home Assistant anschließend neu. [v0.4.3 als ZIP herunterladen](https://github.com/ursolino69/koyoe-home-assistant/releases/download/v0.4.3/koyoe-local-0.4.3.zip)

## Einrichten und Messwerte prüfen

1. Gehe zu **Einstellungen → Geräte & Dienste → Integration hinzufügen → Koyoe for AUX-2**. Wähle den USB-Eintrag unter dem Namen deines AUX-2. Er kann als **USB Serial Port** oder mit einer längeren Kennung erscheinen, die `USB_Single_Serial` enthält. Das Profil fragt mit **Adresse 247**, **9600 Baud**, **8N1** ab. Im Testaufbau waren die vorhandenen DIP-Schalter- und EMS-Einstellungen ausreichend.
2. Öffne das Koyoe-Gerät. Der Zähler **Erfolgreiche Abfragen seit Start** soll bei den folgenden Abfragen steigen. Vergleiche PV-Leistung und Batterieladestand mit Display oder App und beobachte **Fehlgeschlagene Abfragezyklen**. Die Integration liest ausschließlich Messwerte.
3. Im **Energie-Dashboard → Solarproduktion** kannst du **PV Ertrag gesamt** (kWh) und **PV Leistung** (W) auswählen. Die Historie wächst mit der erfassten Statistik. Prüfe den Gesamtzähler gegen das Gerät. Die Verifizierung von Netzbezug, Einspeisung und Batterieenergie steht noch aus.

Wenn der Port fehlt, prüfe zuerst ESPHome, die Stromversorgung und den exakten Adaptertyp. Wenn der Port erscheint, aber der Wechselrichter nicht antwortet, prüfe PARA-Belegung, Adresse und einen eventuell parallel laufenden Leser. Für einen [Fehlerbericht](https://github.com/ursolino69/koyoe-home-assistant/issues) genügen Modell, Firmwarestände, Adapter und die passende Fehlermeldung. Entferne vor dem Teilen Schlüssel, Seriennummern und private Netzwerkdaten.
