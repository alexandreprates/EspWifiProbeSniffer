#ifndef WIFI_PROBE_MONITOR_H
#define WIFI_PROBE_MONITOR_H

#include <Arduino.h>
#include <WiFi.h>
#include <esp_wifi.h>
#include <esp_event.h>
#include <ArduinoJson.h>

// Configurações do sistema
#define NODE_ID "esp32-node-01"
#define FIRMWARE_VERSION "watchtower-v1.2.3"
#define MAX_CHANNELS 13
#define CHANNEL_SWITCH_INTERVAL 500  // ms
#define MAX_SSID_COUNT 20
#define MAX_VENDOR_IES 3  // Reduzido ainda mais de 5 para 3
#define MAX_IES 15        // Reduzido de 25 para 15
#define BEACON_TIMEOUT 30000  // ms
#define JSON_BUFFER_SIZE 512  // Reduzido de 1024 para 512

// Configurações específicas para ESP32-32U com antena externa
#ifdef ESP32_32U_EXTERNAL_ANTENNA
  #define WIFI_ANT_SWITCH_GPIO 0          // GPIO para controle de switch de antena
  #define WIFI_MAX_TX_POWER 78            // Potência máxima (19.5 dBm = 78/4)
  #define WIFI_RX_SENSITIVITY_2_4G -96    // Sensibilidade melhorada com antena externa
#else
  #define WIFI_MAX_TX_POWER 68            // Potência padrão (17 dBm = 68/4)
  #define WIFI_RX_SENSITIVITY_2_4G -88    // Sensibilidade padrão
#endif

// IEEE 802.11 Frame Control Field definitions
#define WIFI_FRAME_TYPE_MANAGEMENT 0x00
#define WIFI_FRAME_SUBTYPE_PROBE_REQ 0x04

// Information Element IDs
#define IE_SSID 0
#define IE_SUPPORTED_RATES 1
#define IE_DS_PARAMETER 3
#define IE_EXTENDED_RATES 50
#define IE_HT_CAPABILITIES 45
#define IE_VHT_CAPABILITIES 191
#define IE_HE_CAPABILITIES 255
#define IE_VENDOR_SPECIFIC 221

// Frequency band definitions
#define FREQ_2_4GHZ_BASE 2412
#define CHANNEL_TO_FREQ(ch) (FREQ_2_4GHZ_BASE + ((ch - 1) * 5))

// Estruturas para dados dos probe requests
typedef struct {
  uint8_t id;
  uint8_t len;
  uint8_t value[64]; // Reduzido de 255 para 64
} information_element_t;

typedef struct {
  uint8_t oui[3];
  uint8_t vendor_type;
  uint8_t payload[64]; // Reduzido de 252 para 64
  uint8_t payload_len;
  String meaning;
} vendor_ie_t;

typedef struct {
  uint8_t da[6];      // destination address
  uint8_t sa[6];      // source address
  uint8_t bssid[6];   // BSSID
  uint16_t duration;
  uint16_t seq_ctrl;
  String type;
  String subtype;
} ieee80211_info_t;

typedef struct {
  uint8_t channel;
  uint16_t freq_mhz;
  String band;
  uint8_t bandwidth_mhz;
  uint8_t antenna;
} radio_info_t;

typedef struct {
  String ssid;
  bool ssid_hidden;
} probe_info_t;

typedef struct {
  bool present;
  String mcs_set;
} ht_capabilities_t;

typedef struct {
  uint8_t supported_rates[16];
  uint8_t extended_rates[16];
  uint8_t supported_rates_count;
  uint8_t extended_rates_count;
  ht_capabilities_t ht_capabilities;
  bool vht_capabilities;
  bool he_capabilities;
} capabilities_info_t;

typedef struct {
  String ie_signature;
  float confidence;
} fingerprint_t;

typedef struct {
  String pkt_id;
  radio_info_t radio;
  ieee80211_info_t ieee80211;
  int8_t rssi_dbm;
  String frame_raw_hex;
  probe_info_t probe;
  capabilities_info_t capabilities;
  vendor_ie_t vendor_ies[MAX_VENDOR_IES];
  uint8_t vendor_ies_count;
  information_element_t ies_raw[MAX_IES];
  uint8_t ies_count;
  bool mac_randomized;
  String oui;
  String vendor_inferred;
  fingerprint_t fingerprint;
} packet_data_t;

typedef struct {
  String capture_id;
  String capture_ts;
  String scanner_id;
  String firmware;
  packet_data_t packet;
} capture_data_t;

typedef struct {
  unsigned frame_ctrl:16;
  unsigned duration_id:16;
  uint8_t addr1[6]; // receiver address
  uint8_t addr2[6]; // sender address
  uint8_t addr3[6]; // filtering address
  unsigned sequence_ctrl:16;
  uint8_t addr4[6]; // optional
} wifi_ieee80211_mac_hdr_t;

typedef struct {
  wifi_ieee80211_mac_hdr_t hdr;
  uint8_t payload[0]; // network data ended with 4 bytes csum (CRC32)
} wifi_ieee80211_packet_t;

// Estatísticas do sistema
typedef struct {
  unsigned long total_packets;
  unsigned long probe_requests;
  unsigned long unique_devices;
  unsigned long uptime_ms;
  uint8_t current_channel;
} system_stats_t;

// Protótipos de funções
void wifi_init_promiscuous();
void wifi_promiscuous_rx(void* buf, wifi_promiscuous_pkt_type_t type);
void parse_probe_request(const uint8_t* frame, size_t len, int8_t rssi, uint8_t channel);
void extract_information_elements(const uint8_t* payload, size_t payload_len, packet_data_t& packet);
String extract_ssid(const uint8_t* payload, size_t payload_len);
void extract_supported_rates(const uint8_t* payload, size_t payload_len, capabilities_info_t& capabilities);
void extract_vendor_ies(const uint8_t* payload, size_t payload_len, packet_data_t& packet);
String frame_to_hex(const uint8_t* frame, size_t len);
String mac_to_string(const uint8_t* mac);
String generate_packet_id();
String generate_capture_id();
String get_iso8601_timestamp();
void print_capture_data(const capture_data_t& capture);
void switch_channel();
void print_system_stats();
bool is_randomized_mac(const uint8_t* mac);
String get_vendor_from_mac(const uint8_t* mac);
String create_fingerprint(const packet_data_t& packet);

#endif // WIFI_PROBE_MONITOR_H