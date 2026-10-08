# Changelog

All notable changes to this project are documented in this file.

## GL-S10 multi-lamp fork — 2026-09

- Target GL.iNet GL-S10 (ESP32, Ethernet IP101), no Wi-Fi.
- Several Steinel Connect luminaires from one gateway (primary + extra lamps, 4 elements each; tested L 42 SC + 2 × L 810 SC).
- Per lamp: mode, light, live intensity, motion, illuminance, threshold, power, standby light, hold time, firmware, signal.
- Twilight threshold limited to 1–40 lx (fine adjustment); Home Assistant lights re-send the intensity 1.5 s after Always On.
- Motion and illuminance pushed by the lamps (groups 0xC001 / 0xC000); values sent to Home Assistant only on change.
- Bilingual FR/EN web interface (dashboard, advanced page, firmware upload); GitHub auto-update (ESP32-C3) disabled.
- Status LEDs (network / Home Assistant, Bluetooth Mesh); Steinel vendor-message listener (0xFEFF).
- ESPHome 2026.9 compatibility; ESPHome Device Builder configuration; Home Assistant examples.
- Removed upstream-only files (ESP32-C3 configuration, GitHub Pages, upstream READMEs, HA package, scripts).

## Upstream history (supczinskib/steinel-nightmatiq-esp32-c3-gateway)

## 1.1.1 — 2026-08-27

- Wi-Fi credentials can now be changed from the local gateway administration page.
- The configured SSID is displayed without exposing the saved Wi-Fi password.
- The standard ESPHome captive portal starts after 60 seconds when the configured Wi-Fi network is unavailable.
- The fallback access point uses channel 6 for predictable discovery and connection.

## 1.1.0 — 2026-08-26

- One universal firmware image for every supported ESP32-C3 board.
- First-run Wi-Fi provisioning through a password-protected access point and captive portal.
- Unique device and access-point names derived from the ESP32-C3 MAC address.
- Persistent administrator password managed from the local page and shared with firmware updates.
- Build, validation and upload scripts no longer require `secrets.yaml`.
- Clean, pinned ESPHome 2026.7.3 build environment without modifications to the installed toolchain.
- Automatic update checks against the latest stable GitHub release when the gateway page opens.
- Dedicated Mesh-free HTTPS update mode with image-size and SHA-256 verification.
- Reproducible release packaging for factory, OTA and checksum files.
- Unified gateway administration panel for firmware updates, directly visible administrator access and factory reset.
- Confirmed factory reset that clears Wi-Fi, administrator and Bluetooth Mesh settings without changing firmware.
- Automatic Mesh address recovery now requires a NightmatIQ advertisement detected during the current boot, preventing address rotation and restart while the sensor is offline or out of range.
- Ready-made factory-image installation instructions and complete English, Polish and German documentation.

## 1.0.0 — 2026-08-24

- Initial stable standalone release for ESP32-C3 Super Mini.
- Local Steinel NightmatIQ Plus control through Bluetooth Mesh.
- Browser-assisted import of the Steinel network configuration.
- Automatic gateway Mesh address selection, recovery and confirmation.
- Local bilingual web interface with control, diagnostics and firmware updates.
- Native Home Assistant integration through ESPHome.
- Optional bilingual Home Assistant area tile and compact control dialog.
- USB, OTA, validation and secrets-configuration scripts.
- Password-protected fallback access point and captive portal.
