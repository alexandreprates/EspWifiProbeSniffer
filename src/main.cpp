
#include <Arduino.h>
#include <WiFi.h>
#include <esp_wifi.h>
#include <esp_event.h>
#include <nvs_flash.h>
#include <ArduinoJson.h>
#include <time.h>
#include <sys/time.h>
#include "wifi_probe_monitor.h"

// Protótipo da função para configurar RTC
void setup_rtc_time();

// Função para obter timestamp atual (RTC se disponível, senão millis())
uint32_t get_current_timestamp() {
#ifdef BUILD_TIME_UNIX
  time_t now;
  time(&now);
  return (uint32_t)now;
#else
  return millis();
#endif
}

// Variáveis globais
static uint8_t current_channel = 1;
static unsigned long last_channel_switch = 0;
static unsigned long last_stats_print = 0;
static system_stats_t stats = {0};

// Lista de alguns OUIs conhecidos para identificação de vendors
const char* known_vendors[][2] = {
  {"00:16:01", "Android"},
  {"00:1B:63", "Apple"},
  {"00:23:12", "Apple"},
  {"00:25:00", "Apple"},
  {"28:E0:2C", "Apple"},
  {"3C:15:C2", "Apple"},
  {"40:A6:D9", "Apple"},
  {"64:20:9F", "Apple"},
  {"68:96:7B", "Apple"},
  {"70:56:81", "Apple"},
  {"7C:6D:62", "Apple"},
  {"88:63:DF", "Apple"},
  {"90:B0:ED", "Apple"},
  {"A4:5E:60", "Apple"},
  {"AC:BC:32", "Apple"},
  {"BC:52:B7", "Apple"},
  {"D0:A6:37", "Apple"},
  {"E8:8D:28", "Apple"},
  {"F0:98:9D", "Apple"},
  {"F4:0F:24", "Apple"},
  {"F8:1E:DF", "Apple"},
  {"18:3A:2D", "Samsung"},
  {"1C:62:B8", "Samsung"},
  {"34:23:87", "Samsung"},
  {"38:AA:3C", "Samsung"},
  {"40:4E:36", "Samsung"},
  {"5C:0A:5B", "Samsung"},
  {"78:1F:DB", "Samsung"},
  {"8C:45:00", "Samsung"},
  {"A0:02:DC", "Samsung"},
  {"C8:19:F7", "Samsung"},
  {"E8:50:8B", "Samsung"},
  {NULL, NULL}
};

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("=== ESP32 WiFi Probe Request Monitor ===");
  Serial.println("Desenvolvido para detecção de dispositivos Android/iOS");
  Serial.println("Baseado em IEEE 802.11 Probe Request Analysis");
  Serial.println("");

  // Configurar RTC com tempo de compilação
  setup_rtc_time();

  // Inicializar NVS
  esp_err_t ret = nvs_flash_init();
  if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
    ESP_ERROR_CHECK(nvs_flash_erase());
    ret = nvs_flash_init();
  }

  // Configurar WiFi em modo promíscuo
  wifi_init_promiscuous();

  Serial.println("Sistema iniciado com sucesso!");
  Serial.println("Formato JSON: {timestamp, mac, rssi, ssid_list, channel, node_id, vendor, randomized}");
  Serial.println("=========================================================================");

  stats.uptime_ms = millis();
}

void loop() {
  unsigned long current_time = millis();

  // Alternar canal WiFi periodicamente para máxima cobertura
  if (current_time - last_channel_switch > CHANNEL_SWITCH_INTERVAL) {
    switch_channel();
    last_channel_switch = current_time;
  }

  // Imprimir estatísticas a cada 30 segundos
  if (current_time - last_stats_print > 30000) {
    print_system_stats();
    last_stats_print = current_time;
  }

  // Pequeno delay para não sobrecarregar o sistema
  delay(10);
}

void wifi_init_promiscuous() {
  // Desconectar WiFi se estiver conectado
  WiFi.disconnect();
  WiFi.mode(WIFI_OFF);
  delay(100);

#ifdef ESP32_32U_EXTERNAL_ANTENNA
  // Configuração específica para ESP32-32U com antena externa
  Serial.println("Configurando ESP32-32U com antena externa 2.4GHz...");

  // Configurar GPIO para controle de antena
  wifi_ant_gpio_config_t ant_gpio_config = {
    .gpio_cfg = {
      {.gpio_select = 1, .gpio_num = 0},  // GPIO 0 para switch de antena
      {.gpio_select = 0, .gpio_num = 0}   // GPIO 1 não usado
    }
  };

  esp_err_t ant_result = esp_wifi_set_ant_gpio(&ant_gpio_config);
  if (ant_result == ESP_OK) {
    Serial.println("GPIO antena configurado com sucesso");
  } else {
    Serial.printf("Erro ao configurar GPIO antena: %d\n", ant_result);
  }

  // Configurar para usar antena externa
  wifi_ant_config_t ant_config = {
    .rx_ant_mode = WIFI_ANT_MODE_ANT1,
    .rx_ant_default = WIFI_ANT_ANT1,
    .tx_ant_mode = WIFI_ANT_MODE_ANT1,
    .enabled_ant0 = 0,
    .enabled_ant1 = 1
  };

  esp_err_t ant_set_result = esp_wifi_set_ant(&ant_config);
  if (ant_set_result == ESP_OK) {
    Serial.println("Configuração de antena externa aplicada com sucesso");
  } else {
    Serial.printf("Erro ao configurar antena externa: %d\n", ant_set_result);
  }

  // Aumentar potência de transmissão para antena externa
  esp_wifi_set_max_tx_power(78); // 19.5 dBm (78/4)
  Serial.println("Potência TX configurada para antena externa");
#endif

  // Inicializar WiFi
  WiFi.mode(WIFI_STA);
  esp_wifi_set_promiscuous(true);
  esp_wifi_set_promiscuous_rx_cb(&wifi_promiscuous_rx);
  esp_wifi_set_channel(current_channel, WIFI_SECOND_CHAN_NONE);

  stats.current_channel = current_channel;
  Serial.printf("WiFi promiscuous mode iniciado no canal %d\n", current_channel);
}

void IRAM_ATTR wifi_promiscuous_rx(void* buf, wifi_promiscuous_pkt_type_t type) {
  if (type != WIFI_PKT_MGMT) return;

  stats.total_packets++;

  wifi_promiscuous_pkt_t* pkt = (wifi_promiscuous_pkt_t*)buf;
  wifi_ieee80211_packet_t* ipkt = (wifi_ieee80211_packet_t*)pkt->payload;
  wifi_ieee80211_mac_hdr_t* hdr = &ipkt->hdr;

  // Verificar se é um probe request (frame control type=0, subtype=4)
  uint8_t frame_type = (hdr->frame_ctrl & 0x0C) >> 2;    // bits 3-2: type
  uint8_t frame_subtype = (hdr->frame_ctrl & 0xF0) >> 4; // bits 7-4: subtype

  if (frame_type == WIFI_FRAME_TYPE_MANAGEMENT && frame_subtype == WIFI_FRAME_SUBTYPE_PROBE_REQ) {
    stats.probe_requests++;
    parse_probe_request(pkt->payload, pkt->rx_ctrl.sig_len, pkt->rx_ctrl.rssi, pkt->rx_ctrl.channel);
  }
}

void parse_probe_request(const uint8_t* frame, size_t len, int8_t rssi, uint8_t channel) {
  if (len < sizeof(wifi_ieee80211_mac_hdr_t)) return;

  wifi_ieee80211_packet_t* pkt = (wifi_ieee80211_packet_t*)frame;
  probe_request_t probe;

  // Extrair MAC address do sender (addr2)
  memcpy(probe.mac, pkt->hdr.addr2, 6);
  probe.rssi = rssi;
  probe.channel = channel;
  probe.timestamp = get_current_timestamp();
  probe.sequence_number = (pkt->hdr.sequence_ctrl & 0xFFF0) >> 4;
  probe.is_valid = true;

  // Extrair lista de SSIDs do payload
  size_t payload_offset = sizeof(wifi_ieee80211_mac_hdr_t);
  if (len > payload_offset) {
    probe.ssid_list = extract_ssid_list(frame + payload_offset, len - payload_offset);
  } else {
    probe.ssid_list = "[]";
  }

  // Imprimir resultado
  print_probe_request(probe);
}

String extract_ssid_list(const uint8_t* payload, size_t payload_len) {
  JsonDocument doc;
  JsonArray ssids = doc.to<JsonArray>();

  size_t offset = 0;

  // Pular os campos fixos do probe request (timestamp, beacon interval, capability info)
  offset += 12; // 8 bytes timestamp + 2 bytes beacon interval + 2 bytes capability

  // Processar Information Elements
  while (offset + 2 < payload_len && ssids.size() < MAX_SSID_COUNT) {
    uint8_t element_id = payload[offset];
    uint8_t element_length = payload[offset + 1];

    if (offset + 2 + element_length > payload_len) break;

    // Element ID 0 = SSID
    if (element_id == 0 && element_length > 0 && element_length <= 32) {
      String ssid = "";
      bool valid_ssid = true;

      for (uint8_t i = 0; i < element_length; i++) {
        char c = payload[offset + 2 + i];
        if (c >= 32 && c <= 126) { // Caracteres imprimíveis ASCII
          ssid += c;
        } else if (c == 0) {
          // SSID vazio ou terminado com null
          break;
        } else {
          valid_ssid = false;
          break;
        }
      }

      if (valid_ssid && ssid.length() > 0) {
        ssids.add(ssid);
      }
    }

    offset += 2 + element_length;
  }

  String result;
  serializeJson(doc, result);
  return result;
}

String mac_to_string(const uint8_t* mac) {
  char mac_str[18];
  sprintf(mac_str, "%02X:%02X:%02X:%02X:%02X:%02X",
          mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
  return String(mac_str);
}

bool is_randomized_mac(const uint8_t* mac) {
  // Bit 1 do primeiro octeto indica MAC address randomizado (locally administered)
  return (mac[0] & 0x02) != 0;
}

String get_vendor_from_mac(const uint8_t* mac) {
  char oui[9];
  sprintf(oui, "%02X:%02X:%02X", mac[0], mac[1], mac[2]);

  for (int i = 0; known_vendors[i][0] != NULL; i++) {
    if (strcmp(oui, known_vendors[i][0]) == 0) {
      return String(known_vendors[i][1]);
    }
  }

  return "Unknown";
}

void print_probe_request(const probe_request_t& probe) {
  JsonDocument doc;

  doc["timestamp"] = probe.timestamp;
  doc["mac"] = mac_to_string(probe.mac);
  doc["rssi"] = probe.rssi;
  doc["ssid_list"] = serialized(probe.ssid_list);
  doc["channel"] = probe.channel;
  doc["node_id"] = NODE_ID;
  doc["sequence"] = probe.sequence_number;
  doc["randomized"] = is_randomized_mac(probe.mac);
  doc["vendor"] = get_vendor_from_mac(probe.mac);

  String output;
  serializeJson(doc, output);
  Serial.println(output);
}

void switch_channel() {
  current_channel++;
  if (current_channel > MAX_CHANNELS) {
    current_channel = 1;
  }

  esp_wifi_set_channel(current_channel, WIFI_SECOND_CHAN_NONE);
  stats.current_channel = current_channel;
}

void print_system_stats() {
  JsonDocument doc;

  doc["type"] = "stats";
  doc["uptime_ms"] = millis() - stats.uptime_ms;
  doc["total_packets"] = stats.total_packets;
  doc["probe_requests"] = stats.probe_requests;
  doc["current_channel"] = stats.current_channel;
  doc["node_id"] = NODE_ID;
  doc["free_heap"] = ESP.getFreeHeap();
  doc["min_free_heap"] = ESP.getMinFreeHeap();

#ifdef BUILD_TIME_UNIX
  doc["timestamp_type"] = "unix_epoch";
  doc["current_time"] = get_current_timestamp();
#else
  doc["timestamp_type"] = "millis";
  doc["current_time"] = millis();
#endif

  String output;
  serializeJson(doc, output);
  Serial.println("# STATS: " + output);
}

void setup_rtc_time() {
#ifdef BUILD_TIME_UNIX
  // Configurar RTC com tempo de compilação do PlatformIO
  struct timeval tv;
  tv.tv_sec = BUILD_TIME_UNIX;
  tv.tv_usec = 0;

  if (settimeofday(&tv, NULL) == 0) {
    Serial.printf("RTC configurado com timestamp de compilação: %lu\n", (unsigned long)BUILD_TIME_UNIX);

    // Verificar se a configuração funcionou
    time_t now;
    time(&now);
    struct tm* timeinfo = localtime(&now);

    Serial.printf("Data/Hora atual: %04d-%02d-%02d %02d:%02d:%02d UTC\n",
                  timeinfo->tm_year + 1900,
                  timeinfo->tm_mon + 1,
                  timeinfo->tm_mday,
                  timeinfo->tm_hour,
                  timeinfo->tm_min,
                  timeinfo->tm_sec);
  } else {
    Serial.println("Erro: Falha ao configurar RTC");
  }
#else
  Serial.println("Aviso: BUILD_TIME_UNIX não definido, usando millis() para timestamps");
#endif
}