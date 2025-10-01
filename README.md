# ESP32 WiFi Probe Sniffer

<div align="center">

[![PlatformIO CI](https://img.shields.io/badge/PlatformIO-Ready-orange?logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjUwMCIgaGVpZ2h0PSIyNTAwIiB2aWV3Qm94PSIwIDAgMjU2IDI1NiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZmlsbC1ydWxlPSJldmVub2RkIiBjbGlwLXJ1bGU9ImV2ZW5vZGQiIGQ9Ik0yNTYgMTI4QzI1NiAxOTguNjkyIDE5OC42OTIgMjU2IDEyOCAyNTZDNTcuMzA4IDI1NiAwIDE5OC42OTIgMCAxMjhDMCA1Ny4zMDggNTcuMzA4IDAgMTI4IDBDMTk4LjY5MiAwIDI1NiA1Ny4zMDggMjU2IDEyOFoiIGZpbGw9IiNGRjdBMDAiLz4KPC9zdmc+)](https://platformio.org/)
[![ESP32](https://img.shields.io/badge/ESP32-Compatible-blue?logo=espressif)](https://www.espressif.com/en/products/socs/esp32)
[![Arduino](https://img.shields.io/badge/Arduino-Framework-00979C?logo=arduino)](https://www.arduino.cc/)
[![License](https://img.shields.io/badge/License-Educational%20Use-green)](LICENSE)
[![Python](https://img.shields.io/badge/Python-Analysis%20Tools-blue?logo=python)](https://python.org)

**Advanced WiFi probe request monitor and analyzer for presence detection and mobile device tracking research**

[� Documentation](#documentation) • [🚀 Quick Start](#quick-start) • [🎯 Features](#features) • [📊 Analysis](#analysis-tools) • [⚖️ Legal Notice](#legal-and-ethical-considerations)

</div>

## 🎯 Overview

ESP32 WiFi Probe Sniffer is a comprehensive system for detecting and analyzing mobile devices through WiFi probe requests. It captures 802.11 management frames in promiscuous mode, providing valuable insights for:

- **Presence Detection**: Real-time device detection in specific areas
- **Crowd Analytics**: People counting based on unique device signatures
- **Mobility Studies**: Movement pattern analysis and spatial behavior
- **Academic Research**: Standardized data collection for urban behavior studies
- **Event Management**: Crowd density monitoring and flow analysis

### Key Capabilities

- **High Detection Rate**: Scans all 13 WiFi channels with 500ms intervals
- **Privacy-Aware**: Detects and handles MAC address randomization
- **Multi-Platform**: Optimized for ESP32-S3, ESP32-32U, and ESP32-WROOM-32
- **Professional Analysis**: Python toolkit for advanced data processing
- **Real-time Monitoring**: Live statistics and performance metrics
- **Production Ready**: Robust error handling and memory management

## 🚀 Quick Start

### Prerequisites

- [PlatformIO](https://platformio.org/) installed
- ESP32 development board (ESP32-S3 recommended)
- Python 3.7+ for analysis tools

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/EspWifiProbeSniffer.git
cd EspWifiProbeSniffer

# Flash to ESP32-S3 (recommended)
pio run -e esp32-s3 -t upload

# Start monitoring
pio device monitor > probe_data_$(date +%Y%m%d_%H%M%S).log
```

### Basic Analysis

```bash
# Install Python dependencies
cd tools
pip install -r requirements.txt

# Run analysis with visualizations
python analyze_probes.py ../probe_data_20241001_120000.log --plots
```

## 🎯 Features

### Core Functionality

| Feature | Description | Implementation |
|---------|-------------|----------------|
| **Promiscuous Mode** | Captures all 802.11 management frames | ESP32 WiFi API |
| **Probe Filtering** | Isolates probe request frames (type/subtype 0x40) | Hardware-level filtering |
| **Channel Scanning** | Rotates through channels 1-13 automatically | 500ms per channel |
| **MAC Analysis** | Detects randomized vs. real MAC addresses | IEEE 802.11 standard compliance |
| **Vendor Detection** | Identifies device manufacturers (Apple, Samsung, etc.) | OUI database lookup |
| **SSID Extraction** | Captures network names being searched | Information Element parsing |
| **JSON Output** | Structured data format for analysis | Schema-validated output |

### Advanced Features

- **Multi-Board Support**: ESP32-S3, ESP32-32U (external antenna), ESP32-WROOM-32
- **Memory Optimization**: Efficient processing of high-volume data streams
- **Error Recovery**: Automatic restart and memory management
- **Real-time Stats**: Performance monitoring and health checks
- **Configurable Parameters**: Adjustable scan intervals and buffer sizes

### Sample Data Output

```json
{
  "capture_id": "550e8400-e29b-41d4-a716-446655440000",
  "capture_ts": "2024-01-15T14:30:45.123Z",
  "scanner_id": "esp32-node-01",
  "firmware": "watchtower-v1.2.3",
  "packet": {
    "pkt_id": "12345678-1234-1234-1234-123456789abc",
    "radio": {
      "channel": 6,
      "freq_mhz": 2437,
      "band": "2.4GHz",
      "bandwidth_mhz": 20
    },
    "ieee80211": {
      "type": "management",
      "subtype": "probe-request",
      "sa": "A2:B3:C4:D5:E6:F7",
      "da": "FF:FF:FF:FF:FF:FF",
      "seq_ctrl": 1842
    },
    "rssi_dbm": -42,
    "probe": {
      "ssid": "iPhone_John",
      "ssid_hidden": false
    },
    "mac_randomized": true,
    "vendor_inferred": "Apple"
  }
}
```

## � Analysis Tools

### Python Analysis Suite

The project includes a comprehensive Python toolkit for processing and analyzing captured probe request data:

```bash
# Basic analysis
python tools/analyze_probes.py probe_data.log

# Generate visualizations
python tools/analyze_probes.py probe_data.log --plots

# Export to CSV
python tools/analyze_probes.py probe_data.log -o summary.csv --verbose
```

### Analysis Features

- **Device Analytics**: Unique device counting, vendor identification, activity patterns
- **Temporal Analysis**: Time-based patterns, peak detection, duration analysis
- **Signal Strength Mapping**: RSSI-based proximity classification
- **Network Analysis**: Most searched SSIDs, network popularity trends
- **Statistical Reports**: Comprehensive data summaries and insights
- **Data Visualization**: Automated chart generation (matplotlib)

### Sample Analysis Output

```
=== DEVICE ANALYSIS SUMMARY ===
📱 Total unique devices: 47
🔒 Randomized MAC addresses: 28 (59.6%)
🏢 Known vendors: 31 (65.9%)

📊 Vendor Distribution:
  Apple: 18 devices (38.3%)
  Samsung: 12 devices (25.5%)
  Unknown: 17 devices (36.2%)

📡 Signal Strength Distribution:
  Very Close (-30 to -50 dBm): 16 devices (34%)
  Moderate (-50 to -70 dBm): 24 devices (51%)
  Distant (-70 to -90 dBm): 7 devices (15%)

⏰ Peak Activity: 14:30-15:00 (23 devices)
```

## 🛠️ Hardware Setup

### Supported Platforms

#### ESP32-S3 DevKit (Recommended)
**Best for**: Development and testing

- Integrated antenna with good performance
- USB-C connectivity for easy programming
- ~30-50m detection range in open areas
- Plug-and-play setup

#### ESP32-32U with External Antenna (High Performance)
**Best for**: Production deployments requiring maximum range

- External 2.4GHz antenna support (up to 15 dBi)
- 100-200m+ detection range in open areas
- GPIO-controlled antenna switching
- Requires additional antenna hardware

#### ESP32-WROOM-32 (Budget Option)
**Best for**: Cost-sensitive deployments

- Built-in PCB antenna
- ~20-40m detection range
- Standard ESP32 development board

### Installation Steps

1. **Install PlatformIO**
   ```bash
   pip install platformio
   ```

2. **Clone and Build**
   ```bash
   git clone https://github.com/yourusername/EspWifiProbeSniffer.git
   cd EspWifiProbeSniffer

   # For ESP32-S3 (recommended)
   pio run -e esp32-s3 -t upload

   # For ESP32-32U with external antenna
   pio run -e esp32-32u -t upload

   # For standard ESP32-WROOM-32
   pio run -e esp32 -t upload
   ```

3. **Start Monitoring**
   ```bash
   pio device monitor
   ```

### Dependencies

The project automatically manages these dependencies:

- `ArduinoJson@^7.0.4`: JSON formatting and parsing
- `Adafruit NeoPixel@^1.15.1`: Status LED indicators (optional)

## ⚙️ Configuration

### Key Parameters

Edit `include/wifi_probe_monitor.h` to customize behavior:

```cpp
#define NODE_ID "esp32-node-01"          // Unique device identifier
#define MAX_CHANNELS 13                  // WiFi channels to scan (1-13)
#define CHANNEL_SWITCH_INTERVAL 500      // Time per channel (ms)
#define MAX_SSID_COUNT 20               // Maximum SSIDs per probe request
#define JSON_BUFFER_SIZE 512            // JSON output buffer size
```

### Channel Configuration

- **Channels 1-13**: Complete 2.4GHz coverage
- **Auto-rotation**: 500ms per channel (configurable)
- **Full cycle**: ~6.5 seconds for complete spectrum scan

### Performance Tuning

For high-traffic environments:

```cpp
#define CHANNEL_SWITCH_INTERVAL 1000     // Slower scanning for better capture
#define MAX_SSID_COUNT 30               // Capture more SSIDs per device
```

For memory-constrained deployments:

```cpp
#define JSON_BUFFER_SIZE 256            // Smaller JSON buffers
#define MAX_SSID_COUNT 10               // Fewer SSIDs per probe
```

## � Data Format and Output

### JSON Schema Structure

Each probe request generates a structured JSON record following this schema:

| Field | Type | Description |
|-------|------|-------------|
| `capture_id` | string | Unique session identifier |
| `capture_ts` | string | ISO8601 timestamp |
| `scanner_id` | string | ESP32 device identifier |
| `packet.pkt_id` | string | Unique packet identifier |
| `packet.ieee80211.sa` | string | Source MAC address |
| `packet.rssi_dbm` | integer | Signal strength (-120 to 0 dBm) |
| `packet.radio.channel` | integer | WiFi channel (1-13) |
| `packet.probe.ssid` | string | Network name being searched |
| `packet.mac_randomized` | boolean | Whether MAC is randomized |
| `packet.vendor_inferred` | string | Device manufacturer |

### Live Data Example

```json
{
  "capture_id": "550e8400-e29b-41d4-a716-446655440000",
  "capture_ts": "2024-01-15T14:30:45.123Z",
  "scanner_id": "esp32-node-01",
  "packet": {
    "pkt_id": "12345678-1234-1234-1234-123456789abc",
    "ieee80211": {"sa": "A2:B3:C4:D5:E6:F7"},
    "rssi_dbm": -42,
    "radio": {"channel": 6},
    "probe": {"ssid": "iPhone_John"},
    "mac_randomized": true,
    "vendor_inferred": "Apple"
  }
}
```

### System Statistics

Every 30 seconds, the system outputs performance statistics:

```json
{
  "type": "stats",
  "uptime_ms": 180000,
  "total_packets": 15420,
  "probe_requests": 2341,
  "current_channel": 8,
  "scanner_id": "esp32-node-01",
  "free_heap": 245632,
  "min_free_heap": 240128
}
```

## � Understanding the Data

### Device Detection Patterns

**Android Devices (6.0+)**
- MAC randomization enabled by default
- Periodic probe requests (every 15-30 seconds)
- Searches for saved networks and open hotspots

**iOS Devices (8.0+)**
- Aggressive MAC randomization
- Less frequent probing when locked
- Distinctive probe patterns

**Legacy Devices**
- Real MAC addresses (pre-2014 devices)
- More predictable probe patterns
- Easier vendor identification

### Signal Strength Interpretation

| RSSI Range | Distance | Interpretation |
|------------|----------|----------------|
| -30 to -50 dBm | 0-5m | Very close (same room) |
| -50 to -70 dBm | 5-20m | Moderate distance |
| -70 to -90 dBm | 20-50m | Far but detectable |
| < -90 dBm | 50m+ | Very weak signal |

### Privacy and Randomization

Modern devices implement MAC address randomization to protect user privacy:

- **Locally Administered Bit**: Second bit of first octet indicates randomization
- **Temporal Patterns**: Randomized MACs change periodically
- **Network-Specific**: Some devices use consistent MACs per network
- **Vendor Signatures**: Even randomized MACs may reveal device type

## 🎯 Use Cases and Applications

### People Counting and Presence Detection

```python
# Example: Real-time unique device counting
import json
from collections import defaultdict

devices = defaultdict(list)
with open('probe_data.log') as f:
    for line in f:
        if line.startswith('{'):
            data = json.loads(line)
            mac = data['packet']['ieee80211']['sa']
            timestamp = data['capture_ts']
            devices[mac].append(timestamp)

print(f"Unique devices detected: {len(devices)}")
```

### Crowd Flow Analysis

Deploy multiple ESP32 units to track movement between areas:

```cpp
// Configure different node IDs for each location
#define NODE_ID "entrance-monitor"    // Location 1
#define NODE_ID "exit-monitor"        // Location 2
#define NODE_ID "main-hall-monitor"   // Location 3
```

### Event Monitoring

- **Peak Detection**: Identify unusual device concentrations
- **Dwell Time**: Calculate how long devices remain in area
- **Repeat Visitors**: Track returning devices over time
- **Capacity Management**: Real-time occupancy monitoring

### Academic Research Applications

- **Urban Mobility Studies**: Movement patterns in public spaces
- **Retail Analytics**: Customer behavior and store traffic
- **Transportation Research**: Pedestrian flow analysis
- **Smart City Infrastructure**: Data for urban planning

## 🛡️ Legal and Ethical Considerations

### ⚠️ Important Legal Notice

This tool captures data from nearby WiFi devices. Users must understand and comply with applicable laws and regulations.

### Privacy Protection Measures

**Built-in Privacy Features:**
- No personal data collection beyond MAC addresses
- MAC randomization detection and handling
- No attempt to decrypt or access network traffic
- Data limited to publicly broadcast probe requests

**Recommended Practices:**
- ✅ Obtain necessary permissions before deployment
- ✅ Post clear signage in monitored areas
- ✅ Implement data retention policies (recommend 7 days max)
- ✅ Anonymize data for analysis
- ✅ Use aggregated statistics instead of individual tracking

### Legal Compliance

**United States:**
- Generally legal to monitor publicly broadcast WiFi frames
- Check local and state regulations
- Consider FCC guidelines for radio monitoring

**European Union (GDPR):**
- MAC addresses may be considered personal data
- Implement privacy by design principles
- Consider legitimate interest vs. privacy rights
- Provide opt-out mechanisms where possible

**Other Jurisdictions:**
- Research local privacy and telecommunications laws
- Consult legal counsel for commercial deployments
- Consider industry-specific regulations

### Ethical Guidelines

**Acceptable Use:**
- Academic research with proper oversight
- Anonymous crowd analytics
- Public safety applications with transparency
- Private property monitoring with clear disclosure

**Prohibited Use:**
- Individual tracking without consent
- Commercial profiling for advertising
- Data sharing with third parties
- Covert surveillance operations

## 🐛 Troubleshooting

### Common Issues

**Low Detection Rates**

*Symptoms:* Few probe requests captured despite presence of WiFi devices

*Solutions:*
- Increase channel dwell time: `#define CHANNEL_SWITCH_INTERVAL 1000`
- Check for active WiFi devices in area
- Verify antenna connections (ESP32-32U)
- Move device to central location

**Memory Issues**

*Symptoms:* ESP32 restarts frequently, heap warnings in stats

*Solutions:*
- Reduce buffer sizes: `#define JSON_BUFFER_SIZE 256`
- Lower SSID limit: `#define MAX_SSID_COUNT 10`
- Use external power supply (5V/2A)

**Data Quality Issues**

*Symptoms:* Malformed JSON, missing fields

*Solutions:*
- Filter logs: `grep '^{' raw_data.log > clean_data.log`
- Check serial baud rate (115200)
- Verify stable power supply

**Performance Optimization**

```cpp
// For high-traffic environments
#define CHANNEL_SWITCH_INTERVAL 1000    // Slower scanning
#define MAX_CHANNELS 6                  // Limit to common channels

// For memory-constrained deployments
#define JSON_BUFFER_SIZE 256            // Smaller buffers
#define MAX_SSID_COUNT 5                // Fewer SSIDs per probe
```

### Debug Mode

Enable detailed logging for troubleshooting:

```cpp
#define CORE_DEBUG_LEVEL 3              // Verbose ESP32 logs
#define DEBUG_FRAMES 1                  // Frame-level debugging
```

## 📚 Documentation

- **[Installation Guide](docs/INSTALL.md)**: Detailed setup instructions
- **[Feature Overview](docs/FEATURES.md)**: Complete functionality reference
- **[ESP32-32U Setup](docs/ESP32-32U_SETUP.md)**: External antenna configuration
- **[Analysis Tools](docs/README_ANALYZER.md)**: Python toolkit documentation

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow existing code style and conventions
- Add tests for new functionality
- Update documentation for any changes
- Ensure compatibility with all supported ESP32 variants

## 📄 License

This project is provided for educational and research purposes. Users are responsible for compliance with applicable laws and regulations regarding wireless monitoring and privacy.

## � Technical References

- [ESP-IDF WiFi API Documentation](https://docs.espressif.com/projects/esp-idf/en/v5.0.6/esp32/api-reference/network/esp_wifi.html)
- [IEEE 802.11 Standard Specification](https://standards.ieee.org/ieee/802.11/7028/)
- [WiFi Frame Format Reference](https://mrncciew.com/2014/10/08/802-11-mgmt-probe-requestresponse/)
- [MAC Address Randomization Research](https://papers.mathyvanhoef.com/asiaccs2016.pdf)

---

**Developed for ESP32 | PlatformIO | Arduino Framework**

*For questions, issues, or contributions, please visit our [GitHub repository](https://github.com/yourusername/EspWifiProbeSniffer)*