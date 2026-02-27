# Ecowater Hydrolink Custom

[![GitHub Release][releases-shield]][releases]
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]
[![Author][author-shield]][github]

**Home Assistant integration for Ecowater water softeners via the Hydrolink platform.**

This custom integration retrieves real-time data from your Ecowater water softener through the Hydrolink API and displays it as sensors and binary sensors in Home Assistant. You can monitor water usage, salt level, regeneration status, alerts, and many other parameters. The API offers many more sensors; currently the most relevant ones have been added.

> **🌍 Multi-region support:** Starting from version 1.1.0, you can select your region during configuration:  
> - **Europe** (`app.hydrolinkhome.eu`)  
> - **US / Other** (`app.hydrolinkhome.com`)

> **📏 Unit system selection:** Starting from version 1.3.0, you can choose between metric (liters, kg) and imperial (gallons, lbs) units during configuration or via options. The integration automatically displays the correct values based on your preference. The alternative unit is available as an attribute on each sensor (see below).


## 📦 Features

- Extensive sensor values: salt percentage, water usage (today/total), estimated days until salt runs out, flow rate, hardness, regeneration count, and more.
- Binary sensors for regeneration status, salt alerts, leak alerts, system errors, and audible alarm status.
- Automatic API token renewal.
- Configurable update interval (via options).
- Multi-region support (EU and US).
- Selectable unit system (metric or imperial) with the alternative unit available as an attribute on each sensor.
- Wake-up mechanism (since v1.2.0) that polls the `/live` endpoint before each update to ensure fresh data, eliminating the need to open the mobile app.

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
3. Enter your login credentials (email and password of your Hydrolink account).
4. **Select your region** (EU or US). This determines the correct API endpoint.
5. **Select your preferred unit system** (metric or imperial).
6. Set the desired **update interval** in minutes (default 5 minutes; 1 minute also works).
7. Click **Submit**.

After successful configuration, all sensors and binary sensors will appear automatically under one device.

### Changing options

After installation, you can adjust the update interval and unit system via:  
**Device → three dots → Options**

> **Note:** When you change the unit system, the displayed values may not update immediately due to Home Assistant's entity state cache. After saving the options, the integration reloads and the new values will appear on the next sensor update. You can also force a refresh by restarting the integration or waiting for the next scheduled poll.

## 📊 Sensors

The integration adds the following sensors (all grouped under one device). Units depend on your selected unit system (metric shown below; imperial units will be gallons, gpm, lbs). For each sensor that supports both unit systems, the alternative value is available as an attribute (e.g., `imperial_value` or `metric_value`).

| Sensor | Description | Unit (metric) | Device class | Attributes |
|--------|-------------|---------------|--------------|------------|
| `last_update` | Timestamp of last successful update | | timestamp | – |
| `salt_level_percent` | Current salt level | % | | – |
| `salt_level_rounded` | Rounded salt level (from API) | % | | – |
| `out_of_salt_days` | Estimated days until salt runs out | days | | – |
| `low_salt_trip_days` | Low salt trip level (device setting) | days | | – |
| `service_reminder` | Service reminder (e.g. "12 months") | | | – |
| `water_used_today` | Water usage today | L | water | `imperial_value` / `metric_value` |
| `total_water_used` | Total water usage since installation | L | water | `imperial_value` / `metric_value` |
| `water_available` | Amount of treated water still available | L | water | `imperial_value` / `metric_value` |
| `current_flow` | Current flow rate | L/min | | `imperial_value` / `metric_value` |
| `avg_daily_use` | Average daily water usage | L | water | `imperial_value` / `metric_value` |
| `hardness` | Water hardness setting | gpg | | – |
| `total_regens` | Total number of regenerations | | | – |
| `manual_regens` | Number of manual regenerations | | | – |
| `days_since_regen` | Days since last regeneration | days | | – |
| `avg_days_between_regens` | Average days between regenerations | days | | – |
| `avg_salt_per_regen` | Average salt consumption per regeneration | kg | | `imperial_value` / `metric_value` |
| `model` | Water softener model | | | – |
| `serial` | Serial number | | | – |
| `software_version` | Controller software version | | | – |
| `rssi` | Wi-Fi signal strength | dBm | signal_strength | – |
| `wifi_ssid` | Wi-Fi network name | | | – |
| `days_in_operation` | Days in operation | days | | – |
| `power_outages` | Number of power outages | | | – |
| `dealer_name` | Dealer name | | | – |
| `dealer_phone` | Dealer phone number | | | – |
| `rock_removed_since_regen` | Hardness removed since last regeneration | kg | | `imperial_value` / `metric_value` |
| `total_rock_removed` | Total hardness removed over lifetime | kg | | `imperial_value` / `metric_value` |
| `total_salt_use` | Total salt consumed over lifetime | kg | | `imperial_value` / `metric_value` |
| `calculated_daily_use` | Total calculated water use for today | L | Water | `imperial_value` / `metric_value` |

> **Note:** Attributes containing the alternative unit only appear after the sensor has received at least one update with the new unit setting. If you change the unit system, the attributes may be empty until the next data refresh. The calculated_daily_use resets to zero after each update.

## 🚨 Binary sensors

| Binary sensor | Description | Device class |
|---------------|-------------|--------------|
| `is_regenerating` | Device is regenerating | running |
| `salt_alert` | Salt low alert | problem |
| `leak_alert` | Leak detected | problem |
| `error_alert` | System error | problem |
| `alarm_beeping` | Audible alarm is active | sound |

## ❓ Troubleshooting

### "No data" or sensors unavailable
- Verify your login credentials and region selection.
- Check the Home Assistant logs (**Settings → System → Logs**) for error messages containing `ecowater_hydrolink_custom`.

### Token expiration
The integration automatically renews the token when a 401 response is received. If this fails, check your internet connection.

### Unit change does not update values immediately
After changing the unit system in the options, the integration reloads. However, due to Home Assistant's entity state cache, the displayed values may still show the old unit for a short time. 

### Attributes not showing
Attributes containing the alternative unit are only populated after the sensor has received a new value following the unit change. 

### Unrealistic values for certain sensors
Some sensors, such as `rock_removed_since_regen`, `total_rock_removed`, and `total_salt_use`, may display values that seem unrealistic (e.g., very high numbers for a newly installed device). These values come directly from the Hydrolink API and are not calculated or modified by the integration. They reflect the data provided by the manufacturer's cloud service.

### Known limitations
- Not tested on multiple devices under a single account.

## 📝 Changelog

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
