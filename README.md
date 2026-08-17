# Ecowater Hydrolink Custom

[![GitHub Release][releases-shield]][releases]
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]
[![Author][author-shield]][github]

**Home Assistant integration for Ecowater water softeners, supporting both the Hydrolink platform and the iQua platform (e.g. Aquahome Duo Smart).**

This custom integration retrieves real-time data from your Ecowater water softener and displays it as sensors, binary sensors and (where supported) a switch in Home Assistant. You can monitor water usage, salt level, regeneration status, alerts, and many other parameters. The APIs offer many more sensors; currently the most relevant ones have been added.

> **🧩 Two cloud backends:** Starting from version 1.5.0, this integration supports two different EcoWater cloud platforms - pick the one that matches the app you use for your device:
> - **Hydrolink** (`app.hydrolinkhome.eu` / `.com`) - the original "Hydrolink" app.
> - **iQua** (`apioem.ecowater.com`) - used by the "iQua" app, which covers devices such as the **Aquahome Duo Smart**, and (untested, community feedback welcome) other iQua-family rebrands like Viessmann, North Star, Morton, Whirlpool, Rheem, GE and Kenmore softeners.
>
> You choose the backend as the first step of setting up the integration. See [⚙️ Configuration](#️-configuration) below.

> **🌍 Multi-region support (Hydrolink only):** Starting from version 1.1.0, you can select your region during configuration:  
> - **Europe** (`app.hydrolinkhome.eu`)  
> - **US / Other** (`app.hydrolinkhome.com`)

> **📏 Unit system selection:** Starting from version 1.3.0, you can choose between metric (liters, kg) and imperial (gallons, lbs) units during configuration or via options (Hydrolink backend). The integration automatically displays the correct values based on your preference. The alternative unit is available as an attribute on each sensor (see below). On the iQua backend, the unit system is instead reported by the device itself and mirrored automatically.


## 📦 Features

- Extensive sensor values: salt percentage, water usage (today/total), estimated days until salt runs out, flow rate, hardness, regeneration count, and more.
- Binary sensors for regeneration status, salt alerts, leak alerts, system errors, and audible alarm status.
- Automatic API token renewal.
- Configurable update interval (via options).
- **Hydrolink backend:** multi-region support (EU and US), selectable unit system (metric or imperial) with the alternative unit available as an attribute on each sensor, wake-up mechanism (since v1.2.0) that polls the `/live` endpoint before each update to ensure fresh data, eliminating the need to open the mobile app.
- **iQua backend (since v1.5.0):** support for Aquahome Duo Smart and other iQua-family softeners, a `connectivity` binary sensor, and an optional water shutoff valve switch.

## 🌐 Language support

The integration is translated into several languages and will automatically display sensor and configuration names in your Home Assistant language if available.

Currently supported languages:
- 🇳🇱 **Dutch** (Nederlands)
- 🇬🇧 **English**
- 🇫🇷 **French** (Français)
- 🇩🇪 **German** (Deutsch)
- 🇮🇹 **Italian** (Italiano)
- 🇵🇱 **Polish** (Polski)
- 🇪🇸 **Spanish** (Español)
- 🇵🇹 **Portuguese** (Português)

If your language is not listed, the interface will fall back to English. Translations are community‑contributed – feel free to help add more!

## 🔧 Installation

### Via HACS (recommended)

1. Ensure [HACS](https://hacs.xyz) is installed.
2. Add this repository as a custom repository:
   - HACS → Integrations → three dots → **Custom repositories**
   - Repository URL: `https://github.com/roeli1996/ha-ecowater-hydrolink`
   - Category: **Integration**
3. Click **Install** on the Ecowater Hydrolink Custom page in HACS.
4. Restart Home Assistant.

### Manual installation

1. Download the `ecowater_hydrolink_hydrolink` folder from the [latest release](https://github.com/roeli1996/ha-ecowater-hydrolink/releases).
2. Place it in your `custom_components` directory.
3. Restart Home Assistant.

## ⚙️ Configuration

The integration is fully configured via the Home Assistant user interface.

1. Go to **Settings → Devices & services**.
2. Click **Add Integration** and search for "Ecowater Hydrolink Custom".
3. **Select which cloud platform / app your device uses:**
   - **EcoWater Hydrolink** - if you normally check your softener via the *Hydrolink* app.
   - **EcoWater iQua** - if you use the *iQua* app (this includes the **Aquahome Duo Smart**).
4. Depending on your choice, fill in the next form:

   **Hydrolink:**
   - Email and password of your Hydrolink account.
   - **Region** (EU or US) - determines the correct API endpoint.
   - **Unit system** (metric or imperial).
   - Update interval in minutes (default 5; 1 minute also works).

   **iQua:**
   - Email/username and password of your iQua account.
   - **Device serial number** - open the iQua app, go to your device's settings/info screen to find it.
   - Update interval in minutes (default 5; 1 minute also works).
5. Click **Submit**.

After successful configuration, all sensors, binary sensors and (for iQua) the water shutoff valve switch will appear automatically under one device.

### Changing options

After installation, you can adjust the update interval (and, for Hydrolink, the unit system) via:  
**Device → three dots → Options**

> **Note:** When you change the unit system, the displayed values may not update immediately due to Home Assistant's entity state cache. After saving the options, the integration reloads and the new values will appear on the next sensor update. You can also force a refresh by restarting the integration or waiting for the next scheduled poll.

## 📊 Sensors

The integration adds the following sensors (all grouped under one device). Units depend on your selected unit system (metric shown below; imperial units will be gallons, gpm, lbs). For each sensor that supports both unit systems, the alternative value is available as an attribute (e.g., `imperial_value` or `metric_value`).

The **Backend** column shows which cloud platform(s) actually populate each sensor. On iQua, fields marked "Hydrolink only" will show as `unknown` since the iQua API doesn't expose that data (lifetime totals, regeneration counters, dealer info, software/Wi-Fi diagnostics, and alert flags are Hydrolink-specific).

| Sensor | Description | Unit (metric) | Device class | Backend | Attributes |
|--------|-------------|---------------|--------------|---------|------------|
| `last_update` | Timestamp of last successful update | | timestamp | Both | – |
| `salt_level_percent` | Current salt level | % | | Both | `raw_tenths` (iQua only, unit unconfirmed) |
| `salt_level_rounded` | Rounded salt level (from API) | % | | Both | – |
| `out_of_salt_days` | Estimated days until salt runs out | days | | Both | – |
| `low_salt_trip_days` | Low salt trip level (device setting) | days | | Hydrolink only | – |
| `service_reminder` | Service reminder (e.g. "12 months") | | | Hydrolink only | – |
| `water_used_today` | Water usage today | L | water | Both | `imperial_value` / `metric_value` |
| `total_water_used` | Total water usage since installation | L | water | Hydrolink only | `imperial_value` / `metric_value` |
| `water_available` | Amount of treated water still available | L | water | Both | `imperial_value` / `metric_value` |
| `current_flow` | Current flow rate | L/min | water | Both | `imperial_value` / `metric_value` |
| `avg_daily_use` | Average daily water usage | L | water | Both | `imperial_value` / `metric_value` |
| `hardness` | Water hardness setting | gpg | | Both | – |
| `total_regens` | Total number of regenerations | | | Hydrolink only | – |
| `manual_regens` | Number of manual regenerations | | | Hydrolink only | – |
| `days_since_regen` | Days since last regeneration | days | | Both | – |
| `avg_days_between_regens` | Average days between regenerations | days | | Hydrolink only | – |
| `avg_salt_per_regen` | Average salt consumption per regeneration | kg | | Hydrolink only | `imperial_value` / `metric_value` |
| `model` | Water softener model | | | Both | – |
| `serial` | Serial number | | | Both | – |
| `software_version` | Controller software version | | | Hydrolink only | – |
| `rssi` | Wi-Fi signal strength | dBm | signal_strength | Hydrolink only | – |
| `wifi_ssid` | Wi-Fi network name | | | Hydrolink only | – |
| `days_in_operation` | Days in operation | days | | Hydrolink only | – |
| `power_outages` | Number of power outages | | | Hydrolink only | – |
| `dealer_name` | Dealer name | | | Hydrolink only | – |
| `dealer_phone` | Dealer phone number | | | Hydrolink only | – |
| `rock_removed_since_regen` | Hardness removed since last regeneration | kg | | Hydrolink only | `imperial_value` / `metric_value` |
| `total_rock_removed` | Total hardness removed over lifetime | kg | | Hydrolink only | `imperial_value` / `metric_value` |
| `total_salt_use` | Total salt consumed over lifetime | kg | | Hydrolink only | `imperial_value` / `metric_value` |
| `calculated_daily_use` | Total calculated water use for today | L | water | Both | `imperial_value` / `metric_value` |
| `water_used_in_last_regen` | Water used during the last regeneration cycle (experimental – needs verification) | L | water | Hydrolink only | – |

> **Note:** Attributes containing the alternative unit only appear after the sensor has received at least one update with the new unit setting. If you change the unit system, the attributes may be empty until the next data refresh. On Hydrolink, `calculated_daily_use` is derived from the delta of `total_water_used` between polls and resets to zero after each update; on iQua it simply mirrors `water_used_today`, which the API already tracks per-day. The `water_used_in_last_regen` sensor is experimental and its accuracy depends on whether the device reports total water usage during regeneration (this has not yet been confirmed). It will display `0` until a regeneration cycle has completed after updating.

## 🚨 Binary sensors

| Binary sensor | Description | Device class | Backend |
|---------------|-------------|--------------|---------|
| `is_regenerating` | Device is regenerating | running | Hydrolink only |
| `salt_alert` | Salt low alert | problem | Hydrolink only |
| `leak_alert` | Leak detected | problem | Hydrolink only |
| `error_alert` | System error | problem | Hydrolink only |
| `alarm_beeping` | Audible alarm is active | sound | Hydrolink only |
| `connectivity` | Device is online | connectivity | iQua only |

## 🔌 Switches (iQua only)

| Switch | Description |
|--------|-------------|
| `water_shutoff_valve` | Opens/closes the softener's water shutoff valve, if your device has one. |

> **⚠️ Disabled by default.** Turning this switch off closes the main water shutoff valve on your softener - a real, physical action with consequences (no water will flow through the softener until it's opened again). To avoid accidental automations, the entity is created **disabled**. Enable it explicitly via **Settings → Devices & services → Ecowater Hydrolink Custom → Entities**, find `water_shutoff_valve`, and enable it, only if you actually intend to control the valve from Home Assistant.
>
> The switch becomes `unavailable` if your specific device doesn't report a valve (some iQua-family models don't have one).

## ❓ Troubleshooting

### "No data" or sensors unavailable
- Verify your login credentials, and (Hydrolink) region selection, or (iQua) device serial number.
- Check the Home Assistant logs (**Settings → System → Logs**) for error messages containing `ecowater_hydrolink_custom`.

### Token expiration
The integration automatically renews the token when a 401 response is received. If this fails, check your internet connection.

### Unit change does not update values immediately
After changing the unit system in the options, the integration reloads. However, due to Home Assistant's entity state cache, the displayed values may still show the old unit for a short time. This option only applies to the Hydrolink backend; iQua always mirrors the unit reported by the device itself.

### Attributes not showing
Attributes containing the alternative unit are only populated after the sensor has received a new value following the unit change. 

### Unrealistic values for certain sensors
Some sensors, such as `rock_removed_since_regen`, `total_rock_removed`, and `total_salt_use`, may display values that seem unrealistic (e.g., very high numbers for a newly installed device). These values come directly from the cloud API and are not calculated or modified by the integration. They reflect the data provided by the manufacturer's cloud service.

### iQua / Aquahome Duo Smart: "No devices found" or wrong data
- Double-check the device serial number entered during setup - it must match exactly what's shown in the iQua app (device info/settings screen), not an account or dealer ID.
- The iQua backend is untested against most iQua-family rebrands (Viessmann, North Star, Morton, Whirlpool, Rheem, GE, Kenmore) - it was built from the public iQua API used by Aquahome Duo Smart and community reverse-engineering of the `apioem.ecowater.com` API. If your model reports differently, please open an issue with a redacted example of your device's data.
- Many fields (lifetime totals, regeneration counters, dealer/Wi-Fi info, alert flags) are simply not available from the iQua dashboard endpoint and will always show as `unknown` - see the Backend column in the sensors table above.

### Known limitations
- Not tested on multiple devices under a single account.
- The `water_used_in_last_regen` sensor is experimental; its accuracy is not guaranteed and depends on the device's update behavior during regeneration. It is Hydrolink-only.
- The iQua backend (Aquahome Duo Smart and related rebrands) has only been validated against the public API contract, not a wide range of real devices - please report any discrepancies.
- The unit of the `raw_tenths` attribute on `salt_level_percent` (iQua only) has not been confirmed against a real device; treat it as informational only.

## 📝 Changelog

### v1.5.0 – Added EcoWater iQua backend support (Aquahome Duo Smart and other iQua-family softeners) - 2026-08-17

This release adds support for water softeners managed through the **iQua** app (`apioem.ecowater.com`) instead of Hydrolink - most notably the **Aquahome Duo Smart**, and (untested) other iQua-family rebrands such as Viessmann, North Star, Morton, Whirlpool, Rheem, GE and Kenmore softeners.

#### ✨ New features
- **New "cloud platform" selection step** at the start of setup - choose Hydrolink or iQua.
- **iQua backend**: login with your iQua account and device serial number; reuses the existing sensor/binary_sensor entities where the data is equivalent.
- **`connectivity` binary sensor** (iQua only) - reflects the device's online/offline state.
- **`water_shutoff_valve` switch** (iQua only, **disabled by default**) - opens/closes the softener's main water shutoff valve, for devices that report one.
- **`raw_tenths` attribute** on `salt_level_percent` (iQua only) - the raw, not-yet-unit-confirmed salt reading from the API.

#### 🔧 Improvements
- Refactored the shared HTTP retry logic into a small internal helper module reused by both backends.
- Fixed an inconsistency where the device name shown in Home Assistant differed slightly between sensors and binary sensors.

#### 📝 Notes
- Existing Hydrolink configurations are unaffected and continue to work without any changes; a silent migration adds the new "backend" field in the background.
- The iQua backend exposes noticeably fewer fields than Hydrolink (see the Backend column in the sensor tables) since the underlying API is simpler.
- The water shutoff valve switch is deliberately disabled by default given the real-world consequence of closing it - see [🔌 Switches](#-switches-iqua-only).

### v1.4.0 – Added water usage during last regeneration sensor (experimental) - 2026-06-19

This release adds a new sensor that tracks the amount of water consumed during the most recent regeneration cycle. **Please note:** this feature is experimental and its accuracy depends on whether the device updates total water usage during regeneration – this has not yet been verified.

#### ✨ New features
- **`water_used_in_last_regen` sensor** – shows the water usage (in liters or gallons) during the last regeneration. The value is calculated by comparing the total water used at the start and end of a regeneration cycle.
- **Added device class `water`** to the `current_flow` sensor for better icon and history representation.

#### 📝 Notes
- The new sensor will display `0` until a regeneration has occurred after updating.
- Fully backward compatible; no configuration changes needed.
- This sensor is experimental – please report any issues with its accuracy.

### v1.3.3 – Translating Dutch terms ('keer' and 'dagen') - 2026-03-02

This release only fixes [issue 6](https://github.com/Roeli1996/ha-ecowater-hydrolink/issues/6):
Hard-coded translations of 'keer' and 'dagen'

#### 🔧 Improvements
- Translations

#### 📝 Notes
- The `calculated_daily_use` resets to zero after each update.
- Thanks @parnvard and @redmike121 for the feedback. 


### v1.3.2 – Added calculated daily usage sensor and custom icons

This release introduces two major improvements: a new sensor that estimates your daily water consumption, and meaningful icons for all sensors to enhance your Home Assistant experience.

#### ✨ New features
- **`calculated_daily_use` sensor** – estimates today's water usage based on total water used, resetting automatically at midnight. Units follow your selected unit system (liters or gallons).
- **Custom icons** – every sensor and binary sensor now has a dedicated icon (e.g., water drop for usage, beaker for salt level, alert symbols for problems), making them easily recognizable in dashboards and entity lists.

#### 🔧 Improvements
- The new sensor provides a reliable alternative for users who experience delays in the official `water_used_today` sensor.
- Icons improve visual identification without any configuration changes.

#### 📝 Notes
- Fully backward compatible; no breaking changes.
- If you have manually customized icons, your settings will not be overwritten.
- The new sensor and icons appear automatically after updating.
- The `calculated_daily_use` resets to zero after each update.


### v1.3.1 – Added logo (cosmetic only)

This release adds a logo to the integration for a nicer appearance in the Home Assistant interface.
**No functional changes** – updating is optional and only recommended if you'd like to see the logo.

If you're happy with the current version, you can safely skip this update.

### v1.3.0 - 2026-02-26
#### Added
- **Unit system selection**: Choose between metric (liters, kg) and imperial (gallons, lbs) during configuration or via options. The integration automatically displays the correct values based on your preference.
- **Alternative unit as attribute**: For all unit‑dependent sensors, the value in the other unit system is now available as an attribute (e.g., `imperial_value` or `metric_value`).
- **New sensors**:
  - `alarm_beeping` (binary sensor) – indicates if the audible alarm is active.
  - `rock_removed_since_regen` – hardness removed since the last regeneration.
  - `total_rock_removed` – total hardness removed over the device's lifetime.
  - `total_salt_use` – total salt consumed over the device's lifetime.
- **Extended options** to include unit system selection.

#### Changed
- Updated sensor handling to dynamically display the correct unit and provide the alternative via attributes.
- Improved documentation and troubleshooting notes regarding unit changes and attributes.

#### Notes
- Existing configurations will have the unit system default to metric. You can change it via options.
- If you upgrade from a previous version, you may need to remove and re‑add the integration for the new sensors to appear.

### v1.2.0 - 2026-02-26
#### Added
- **Wake-up mechanism**: The integration now sends a signal to the `/live` endpoint before each update to wake up the device, followed by fetching the latest data via `/detail-or-summary`. This ensures that the displayed data is always up-to-date, similar to the web app, and eliminates the need to open the mobile app for fresh data.

#### Changed
- The coordinator now uses the combination of `/live` (wake-up) and `/detail-or-summary` (data) for every scheduled update once the device ID is known. On the first startup, the device list is still used to determine the ID.
- Internal restructuring of the data fetching method for better readability and error handling.

#### Notes
- This change works for both the EU and US platforms.
- Existing configurations remain intact; no reconfiguration is required.

### v1.1.1 - 2026-02-26
#### Fixed
- **Added migration handler** for existing configurations (version 1 → 2). This resolves the *"Migration handler not found"* error that occurred when updating the integration. Existing users are automatically migrated with the region set to `EU`, ensuring they can continue using the integration without interruption.
- **Note for US users:** If you wish to switch from the EU to the US platform, please remove the integration and add it again with the appropriate region selected. (Region cannot be changed via options at this time.)

#### Changed
- Internal: enhanced logging during migration for improved debugging and troubleshooting.

### v1.1.0 – 2026-02-26
- **Added region selection** (EU / US) during configuration.  
- Updated API endpoints for US platform (`app.hydrolinkhome.com`).  
- Fixed timestamp timezone issue for `last_update` sensor.  
- Improved error handling and logging.

### v1.0.0 – 2026-02-24
- Initial release (EU only).

> **Important note for users upgrading from older versions:**  
> Due to the addition of the unit system and new sensors, it is recommended to remove the integration and add it again after upgrading to v1.3.0. This ensures that all new sensors are created correctly and that the unit selection works as expected. Your historical data will not be lost.

## 📝 License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.

---

**Note:** This integration is not officially affiliated with EcoWater or Hydrolink. Use at your own risk.

[releases-shield]: https://img.shields.io/github/v/release/roeli1996/ha-ecowater-hydrolink?style=for-the-badge
[releases]: https://github.com/roeli1996/ha-ecowater-hydrolink/releases
[license-shield]: https://img.shields.io/github/license/roeli1996/ha-ecowater-hydrolink?style=for-the-badge
[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[author-shield]: https://img.shields.io/badge/Author-roeli1996-blue?style=for-the-badge
[github]: https://github.com/roeli1996
