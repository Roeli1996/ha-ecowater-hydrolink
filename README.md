# Ecowater Hydrolink Custom

[![GitHub Release][releases-shield]][releases]
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]
[![Author][author-shield]][github]

**Home Assistant integration for Ecowater water softeners via the Hydrolink platform.**

This custom integration retrieves 'real-time' data from your Ecowater water softener through the 'Hydrolink API' and displays it as sensors and binary sensors in Home Assistant. You can monitor water usage, salt level, regeneration status, alerts, and many other parameters. Many more sensors are available in the API. Currently, the most relevant sensors have been added.

API refers to the European platform. Since version 1.1.0 there is also the posibility to use the US platform. This is not tested yet, because I don't have a device on that platform. Please provide me with feedback if you have a device! 

---
## Known limitations 
Reading new data only works after the local app has been started. I'm still looking for a way to bypass this.
---

## 📦 Features

- Extensive sensor values such as salt percentage, water usage (today/total), estimated days until salt runs out, flow rate, hardness, regeneration count, etc.
- Binary sensors for regeneration status, salt and leak alerts.
- Automatic API token renewal.
- Configurable update interval (via options).
- Supports multiple devices? (The API returns one device, but the code is prepared for multiple.)

## 🔧 Installation

### Via HACS (recommended)

1. Ensure [HACS](https://hacs.xyz) is installed.
2. Add this repository as a custom repository:
   - HACS → Integrations → three dots → Custom repositories
   - Repository URL: `https://github.com/roeli1996/ha-ecowater-custom`
   - Category: Integration
3. Click "Install" on the Ecowater Hydrolink Custom page in HACS.
4. Restart Home Assistant.

### Manual installation

1. Download the `ecowater_hydrolink_custom` folder from the repository.
2. Place it in your `custom_components` directory.
3. Restart Home Assistant.

## ⚙️ Configuration

The integration is fully configured via the Home Assistant user interface.

1. Go to **Settings → Devices & services**.
2. Click **Add Integration** and search for "Ecowater Hydrolink Custom".
3. Enter your login credentials (email and password of your Hydrolink account).
4. Set the desired **update interval** in minutes (default 5 minutes, it works on 1 minute also).
5. Click Submit.

After successful configuration, sensors and binary sensors will appear automatically.

### Changing options

After installation, you can adjust the update interval via:

**Device → three dots → Options**

## 📊 Sensors

The integration adds the following sensors (all grouped under one device):

| Sensor | Description | Unit | Device class |
|--------|-------------|------|--------------|
| `last_update` | Timestamp of last successful update | | timestamp |
| `salt_level_percent` | Current salt level | % | |
| `salt_level_rounded` | Rounded salt level (from API) | % | |
| `out_of_salt_days` | Estimated days until salt runs out | days | |
| `low_salt_trip_days` | Low salt trip level (device setting) | days | |
| `service_reminder` | Service reminder (e.g. "12 months") | | |
| `water_used_today` | Water usage today | L | water |
| `total_water_used` | Total water usage since installation | L | water |
| `water_available` | Amount of treated water still available | L | water |
| `current_flow` | Current flow rate | L/min | |
| `avg_daily_use` | Average daily water usage | L | water |
| `hardness` | Water hardness setting | gpg | |
| `total_regens` | Total number of regenerations | | |
| `manual_regens` | Number of manual regenerations | | |
| `days_since_regen` | Days since last regeneration | days | |
| `avg_days_between_regens` | Average days between regenerations | days | |
| `avg_salt_per_regen` | Average salt consumption per regeneration | kg | |
| `model` | Water softener model | | |
| `serial` | Serial number | | |
| `software_version` | Controller software version | | |
| `rssi` | Wi-Fi signal strength | dBm | signal_strength |
| `wifi_ssid` | Wi-Fi network name | | |
| `days_in_operation` | Days in operation | days | |
| `power_outages` | Number of power outages | | |
| `dealer_name` | Dealer name | | |
| `dealer_phone` | Dealer phone number | | |

## 🚨 Binary sensors

| Binary sensor | Description | Device class |
|---------------|-------------|--------------|
| `is_regenerating` | Device is regenerating | running |
| `salt_alert` | Salt low alert | problem |
| `leak_alert` | Leak detected | problem |
| `error_alert` | System error | problem |

## ❓ Troubleshooting

### "No data"
- Verify your login credentials.
- Check the Home Assistant logs (Settings → System → Logs) for error messages containing `ecowater_hydrolink_custom`.


### Token expiration
The integration automatically renews the token when a 401 response is received. If this fails, check your internet connection.


### Test limitations
Not tested on multiple devices on a single account.
Only tested on an "eVO REFINER POWER".

## 📝 License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.


## 📝 Changelog
### V1.1.0 - 25-02-2026
Support for US platform (not tested, I don't have a devica on that platform).

### V1.0.0 - 24-02-2026
Initial release.


---

**Note:** This integration is not officially affiliated with EcoWater or Hydrolink. Use at your own risk.

[releases-shield]: https://img.shields.io/github/v/release/roeli1996/ha-ecowater-hydrolink?style=for-the-badge
[releases]: https://github.com/Roeli1996/ha-ecowater-hydrolink/releases/
[license-shield]: https://img.shields.io/github/license/roeli1996/ha-ecowater-hydrolink?style=for-the-badge
[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[author-shield]: https://img.shields.io/badge/Author-roeli1996-blue?style=for-the-badge
[github]: https://github.com/roeli1996
