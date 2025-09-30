#ifndef WIFI_PROBE_MONITOR_H
#define WIFI_PROBE_MONITOR_H

#include <Arduino.h>
#include <WiFi.h>
#include <esp_wifi.h>
#include <esp_event.h>
#include <ArduinoJson.h>

// Configurações do sistema
#define NODE_ID "ESP32_PROBE_001"
#define MAX_CHANNELS 13
#define CHANNEL_SWITCH_INTERVAL 500  // ms
#define MAX_SSID_COUNT 20
#define BEACON_TIMEOUT 30000  // ms
#define JSON_BUFFER_SIZE 512

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

// Estruturas para dados dos probe requests
typedef struct {
  uint8_t mac[6];
  int8_t rssi;
  uint8_t channel;
  uint32_t timestamp;
  String ssid_list;
  bool is_valid;
  uint16_t sequence_number;
} probe_request_t;

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
String extract_ssid_list(const uint8_t* payload, size_t payload_len);
String mac_to_string(const uint8_t* mac);
void print_probe_request(const probe_request_t& probe);
void switch_channel();
void print_system_stats();
bool is_randomized_mac(const uint8_t* mac);
String get_vendor_from_mac(const uint8_t* mac);

#endif // WIFI_PROBE_MONITOR_H