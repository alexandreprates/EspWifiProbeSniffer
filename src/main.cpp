
#include <Arduino.h>
#include <WiFi.h>
#include <esp_wifi.h>
#include <esp_event.h>
#include <nvs_flash.h>
#include <ArduinoJson.h>
#include <time.h>
#include <sys/time.h>
#include "wifi_probe_monitor.h"

// Variáveis globais
static uint8_t current_channel = 1;
static unsigned long last_channel_switch = 0;
static unsigned long last_stats_print = 0;
static unsigned long startup_time = 0;
static system_stats_t stats = {0};
static String current_capture_id = "";
static uint32_t packet_counter = 0;

// Intervalo de reinicialização (1 hora = 3.600.000 ms)
const unsigned long RESTART_INTERVAL = 3600000;

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

// Função para gerar UUID simples baseado em timestamp e contador
String generate_packet_id() {
  char uuid[37];
  uint32_t ts = get_current_timestamp();
  uint32_t counter = packet_counter++;
  uint64_t chip_id = ESP.getEfuseMac(); // Usar EfuseMac em vez de getChipId
  sprintf(uuid, "%08x-%04x-%04x-%04x-%08x%04x",
          ts,
          (uint16_t)(counter & 0xFFFF),
          (uint16_t)((counter >> 16) & 0xFFFF),
          (uint16_t)(chip_id & 0xFFFF),
          ts,
          (uint16_t)(millis() & 0xFFFF));
  return String(uuid);
}

// Função para gerar capture ID (um por sessão)
String generate_capture_id() {
  char uuid[37];
  uint32_t ts = get_current_timestamp();
  uint64_t chip_id = ESP.getEfuseMac(); // Usar EfuseMac em vez de getChipId
  sprintf(uuid, "%08x-%04x-%04x-%04x-%08x%04x",
          ts,
          (uint16_t)(chip_id & 0xFFFF),
          (uint16_t)((chip_id >> 16) & 0xFFFF),
          0x4000 | ((ts >> 16) & 0x0FFF),
          ts,
          (uint16_t)(chip_id & 0xFFFF));
  return String(uuid);
}

// Função para gerar timestamp ISO8601
String get_iso8601_timestamp() {
#ifdef BUILD_TIME_UNIX
  time_t now;
  time(&now);
  struct tm* timeinfo = gmtime(&now);

  char buffer[32];
  sprintf(buffer, "%04d-%02d-%02dT%02d:%02d:%02d.%03dZ",
          timeinfo->tm_year + 1900,
          timeinfo->tm_mon + 1,
          timeinfo->tm_mday,
          timeinfo->tm_hour,
          timeinfo->tm_min,
          timeinfo->tm_sec,
          (int)(millis() % 1000));
  return String(buffer);
#else
  // Fallback usando millis para timestamp relativo
  unsigned long ms = millis();
  unsigned long seconds = ms / 1000;
  unsigned long minutes = seconds / 60;
  unsigned long hours = minutes / 60;

  char buffer[32];
  sprintf(buffer, "1970-01-01T%02lu:%02lu:%02lu.%03luZ",
          hours % 24,
          minutes % 60,
          seconds % 60,
          ms % 1000);
  return String(buffer);
#endif
}

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

  Serial.println("=== ESP32 WiFi Probe Request Monitor v2.0 ===");
  Serial.println("Formato: JSON Schema conforme especificação");
  Serial.println("Desenvolvido para detecção de dispositivos WiFi");
  Serial.println("");

  // Gerar capture ID para esta sessão
  current_capture_id = generate_capture_id();

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

  Serial.printf("Sistema iniciado! Capture ID: %s\n", current_capture_id.c_str());
  Serial.println("=========================================================================");

  // Registrar tempo de inicialização
  startup_time = millis();

  stats.uptime_ms = millis();
}

void loop() {
  unsigned long current_time = millis();

  // Verificar se é hora de reiniciar (a cada 1 hora)
  if (current_time - startup_time >= RESTART_INTERVAL) {
    Serial.println("# RESTART: Reiniciando ESP32 após 1 hora de operação...");
    Serial.flush(); // Garantir que a mensagem seja enviada
    delay(1000);
    ESP.restart();
  }

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

  // Inicializar WiFi primeiro
  WiFi.mode(WIFI_STA);
  delay(100);

#ifdef ESP32_32U_EXTERNAL_ANTENNA
  // Configuração específica para ESP32-32U com antena externa
  Serial.println("Configurando ESP32-32U com antena externa 2.4GHz...");

  // Configurar GPIO para controle de antena (após WiFi init)
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
    Serial.printf("Erro ao configurar GPIO antena: %d (0x%x)\n", ant_result, ant_result);
    if (ant_result == 0x3001) {
      Serial.println("ESP_ERR_WIFI_NOT_INIT - WiFi não inicializado");
    } else if (ant_result == 0x3002) {
      Serial.println("ESP_ERR_WIFI_NOT_STARTED - WiFi não iniciado");
    }
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
    Serial.printf("Erro ao configurar antena externa: %d (0x%x)\n", ant_set_result, ant_set_result);
    if (ant_set_result == 0x3001) {
      Serial.println("ESP_ERR_WIFI_NOT_INIT - WiFi não inicializado");
    } else if (ant_set_result == 0x3002) {
      Serial.println("ESP_ERR_WIFI_NOT_STARTED - WiFi não iniciado");
    } else if (ant_set_result == 0x3003) {
      Serial.println("ESP_ERR_WIFI_CONN - WiFi interno erro de conexão");
    }
  }

  // Aumentar potência de transmissão para antena externa
  esp_wifi_set_max_tx_power(78); // 19.5 dBm (78/4)
  Serial.println("Potência TX configurada para antena externa");
#else
  Serial.println("Usando configuração padrão de antena interna");
#endif

  // Configurar modo promíscuo
  esp_wifi_set_promiscuous(true);
  esp_wifi_set_promiscuous_rx_cb(&wifi_promiscuous_rx);
  esp_wifi_set_channel(current_channel, WIFI_SECOND_CHAN_NONE);

  stats.current_channel = current_channel;
  Serial.printf("WiFi promiscuous mode iniciado no canal %d\n", current_channel);
}

void IRAM_ATTR wifi_promiscuous_rx(void* buf, wifi_promiscuous_pkt_type_t type) {
  if (type != WIFI_PKT_MGMT) return;

  // Verificar memória disponível antes de processar - aumentar threshold
  if (ESP.getFreeHeap() < 20000) {
    return; // Pular se memória muito baixa
  }

  stats.total_packets++;

  wifi_promiscuous_pkt_t* pkt = (wifi_promiscuous_pkt_t*)buf;
  wifi_ieee80211_packet_t* ipkt = (wifi_ieee80211_packet_t*)pkt->payload;
  wifi_ieee80211_mac_hdr_t* hdr = &ipkt->hdr;

  // Verificar se é um probe request (frame control type=0, subtype=4)
  uint8_t frame_type = (hdr->frame_ctrl & 0x0C) >> 2;    // bits 3-2: type
  uint8_t frame_subtype = (hdr->frame_ctrl & 0xF0) >> 4; // bits 7-4: subtype

  if (frame_type == WIFI_FRAME_TYPE_MANAGEMENT && frame_subtype == WIFI_FRAME_SUBTYPE_PROBE_REQ) {
    stats.probe_requests++;

    // Limitar processamento para evitar sobrecarga
    static unsigned long last_process = 0;
    if (millis() - last_process > 10) { // Processar no máximo a cada 10ms
      parse_probe_request(pkt->payload, pkt->rx_ctrl.sig_len, pkt->rx_ctrl.rssi, pkt->rx_ctrl.channel);
      last_process = millis();
    }
  }
}

void parse_probe_request(const uint8_t* frame, size_t len, int8_t rssi, uint8_t channel) {
  if (len < sizeof(wifi_ieee80211_mac_hdr_t)) return;

  // Usar variável global estática em vez de malloc para evitar heap corruption
  static capture_data_t capture;

  wifi_ieee80211_packet_t* pkt = (wifi_ieee80211_packet_t*)frame;

  // Limpar estrutura antes do uso
  memset(&capture, 0, sizeof(capture_data_t));

  // Preencher dados básicos da captura
  capture.capture_id = current_capture_id;
  capture.capture_ts = get_iso8601_timestamp();
  capture.scanner_id = NODE_ID;
  capture.firmware = FIRMWARE_VERSION;

  // Preencher dados do pacote
  capture.packet.pkt_id = generate_packet_id();

  // Informações de rádio
  capture.packet.radio.channel = channel;
  capture.packet.radio.freq_mhz = CHANNEL_TO_FREQ(channel);
  capture.packet.radio.band = "2.4GHz";
  capture.packet.radio.bandwidth_mhz = 20;
  capture.packet.radio.antenna = 0;

  // Informações IEEE 802.11
  capture.packet.ieee80211.type = "management";
  capture.packet.ieee80211.subtype = "probe-request";
  capture.packet.ieee80211.duration = pkt->hdr.duration_id;
  capture.packet.ieee80211.seq_ctrl = (pkt->hdr.sequence_ctrl & 0xFFF0) >> 4;

  // Endereços
  memcpy(capture.packet.ieee80211.da, pkt->hdr.addr1, 6);    // destination
  memcpy(capture.packet.ieee80211.sa, pkt->hdr.addr2, 6);    // source
  memcpy(capture.packet.ieee80211.bssid, pkt->hdr.addr3, 6); // BSSID

  // RSSI
  capture.packet.rssi_dbm = rssi;

  // Frame raw em hex (limitar tamanho para economizar memória)
  size_t hex_len = (len > 64) ? 64 : len; // Reduzir ainda mais para 64 bytes
  capture.packet.frame_raw_hex = frame_to_hex(frame, hex_len);

  // Analisar MAC randomization
  capture.packet.mac_randomized = is_randomized_mac(pkt->hdr.addr2);

  // OUI e vendor
  capture.packet.oui = mac_to_string(pkt->hdr.addr2).substring(0, 8);
  capture.packet.vendor_inferred = get_vendor_from_mac(pkt->hdr.addr2);

  // Extrair Information Elements se há payload
  size_t payload_offset = sizeof(wifi_ieee80211_mac_hdr_t);
  if (len > payload_offset) {
    extract_information_elements(frame + payload_offset, len - payload_offset, capture.packet);
  }

  // Criar fingerprint
  capture.packet.fingerprint.ie_signature = create_fingerprint(capture.packet);
  capture.packet.fingerprint.confidence = 0.65; // valor padrão

  // Imprimir resultado
  print_capture_data(capture);
}

void extract_information_elements(const uint8_t* payload, size_t payload_len, packet_data_t& packet) {
  size_t offset = 0;

  // Inicializar estruturas
  packet.probe.ssid = "";
  packet.probe.ssid_hidden = false;
  packet.capabilities.supported_rates_count = 0;
  packet.capabilities.extended_rates_count = 0;
  packet.capabilities.ht_capabilities.present = false;
  packet.capabilities.vht_capabilities = false;
  packet.capabilities.he_capabilities = false;
  packet.vendor_ies_count = 0;
  packet.ies_count = 0;

  // Pular os campos fixos do probe request (timestamp, beacon interval, capability info)
  offset += 12; // 8 bytes timestamp + 2 bytes beacon interval + 2 bytes capability

  // Processar Information Elements
  while (offset + 2 < payload_len && packet.ies_count < MAX_IES) {
    uint8_t element_id = payload[offset];
    uint8_t element_length = payload[offset + 1];

    if (offset + 2 + element_length > payload_len) break;

    // Armazenar IE raw
    if (packet.ies_count < MAX_IES) {
      packet.ies_raw[packet.ies_count].id = element_id;
      packet.ies_raw[packet.ies_count].len = element_length;
      uint8_t copy_len = (element_length > 64) ? 64 : element_length; // Limitar a 64 bytes
      memcpy(packet.ies_raw[packet.ies_count].value, payload + offset + 2, copy_len);
      packet.ies_count++;
    }

    switch (element_id) {
      case IE_SSID:
        if (element_length > 0 && element_length <= 32) {
          packet.probe.ssid = "";
          for (uint8_t i = 0; i < element_length; i++) {
            char c = payload[offset + 2 + i];
            if (c >= 32 && c <= 126) {
              packet.probe.ssid += c;
            }
          }
        } else {
          packet.probe.ssid = "";
          packet.probe.ssid_hidden = false;
        }
        break;

      case IE_SUPPORTED_RATES:
        if (element_length <= 16) {
          for (uint8_t i = 0; i < element_length && packet.capabilities.supported_rates_count < 16; i++) {
            uint8_t rate = payload[offset + 2 + i] & 0x7F; // Remove MSB
            packet.capabilities.supported_rates[packet.capabilities.supported_rates_count++] = rate;
          }
        }
        break;

      case IE_EXTENDED_RATES:
        if (element_length <= 16) {
          for (uint8_t i = 0; i < element_length && packet.capabilities.extended_rates_count < 16; i++) {
            uint8_t rate = payload[offset + 2 + i] & 0x7F; // Remove MSB
            packet.capabilities.extended_rates[packet.capabilities.extended_rates_count++] = rate;
          }
        }
        break;

      case IE_HT_CAPABILITIES:
        if (element_length >= 26) {
          packet.capabilities.ht_capabilities.present = true;
          packet.capabilities.ht_capabilities.mcs_set = "0-7"; // Simplificado
        }
        break;

      case IE_VHT_CAPABILITIES:
        if (element_length >= 12) {
          packet.capabilities.vht_capabilities = true;
        }
        break;

      case IE_VENDOR_SPECIFIC:
        if (element_length >= 3 && packet.vendor_ies_count < MAX_VENDOR_IES) {
          vendor_ie_t& vendor_ie = packet.vendor_ies[packet.vendor_ies_count];
          memcpy(vendor_ie.oui, payload + offset + 2, 3);
          vendor_ie.vendor_type = element_length > 3 ? payload[offset + 5] : 0;
          vendor_ie.payload_len = element_length > 4 ? element_length - 4 : 0;
          if (vendor_ie.payload_len > 64) vendor_ie.payload_len = 64; // Limitar a 64 bytes
          if (vendor_ie.payload_len > 0) {
            memcpy(vendor_ie.payload, payload + offset + 6, vendor_ie.payload_len);
          }
          vendor_ie.meaning = ""; // Pode ser preenchido com lógica específica
          packet.vendor_ies_count++;
        }
        break;
    }

    offset += 2 + element_length;
  }
}

String frame_to_hex(const uint8_t* frame, size_t len) {
  // Limitar drasticamente o tamanho para evitar uso excessivo de memória
  if (len > 32) len = 32; // Reduzir para apenas 32 bytes

  String hex = "";
  hex.reserve(len * 2 + 1); // Pre-allocate string

  for (size_t i = 0; i < len; i++) {
    char buf[3];
    sprintf(buf, "%02x", frame[i]);
    hex += buf;
  }
  return hex;
}String mac_to_string(const uint8_t* mac) {
  char mac_str[18];
  sprintf(mac_str, "%02x:%02x:%02x:%02x:%02x:%02x",
          mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
  return String(mac_str);
}

void print_capture_data(const capture_data_t& capture) {
  JsonDocument doc;

  // Campos obrigatórios do schema
  doc["capture_id"] = capture.capture_id;
  doc["capture_ts"] = capture.capture_ts;
  doc["scanner_id"] = capture.scanner_id;
  doc["firmware"] = capture.firmware;

  // Opcional: location (null por enquanto)
  doc["location"]["lat"] = nullptr;
  doc["location"]["lon"] = nullptr;
  doc["location"]["label"] = nullptr;

  // Objeto packet (obrigatório)
  JsonObject packet = doc["packet"].to<JsonObject>();
  packet["pkt_id"] = capture.packet.pkt_id;

  // Radio info
  JsonObject radio = packet["radio"].to<JsonObject>();
  radio["channel"] = capture.packet.radio.channel;
  radio["freq_mhz"] = capture.packet.radio.freq_mhz;
  radio["band"] = capture.packet.radio.band;
  radio["bandwidth_mhz"] = capture.packet.radio.bandwidth_mhz;
  radio["antenna"] = capture.packet.radio.antenna;

  // IEEE 802.11 info
  JsonObject ieee80211 = packet["ieee80211"].to<JsonObject>();
  ieee80211["type"] = capture.packet.ieee80211.type;
  ieee80211["subtype"] = capture.packet.ieee80211.subtype;
  ieee80211["duration"] = capture.packet.ieee80211.duration;
  ieee80211["da"] = mac_to_string(capture.packet.ieee80211.da);
  ieee80211["sa"] = mac_to_string(capture.packet.ieee80211.sa);
  ieee80211["bssid"] = mac_to_string(capture.packet.ieee80211.bssid);
  ieee80211["seq_ctrl"] = capture.packet.ieee80211.seq_ctrl;

  // Campos obrigatórios do packet
  packet["rssi_dbm"] = capture.packet.rssi_dbm;
  packet["frame_raw_hex"] = capture.packet.frame_raw_hex;

  // Probe info
  JsonObject probe = packet["probe"].to<JsonObject>();
  probe["ssid"] = capture.packet.probe.ssid;
  probe["ssid_hidden"] = capture.packet.probe.ssid_hidden;

  // Supported rates
  if (capture.packet.capabilities.supported_rates_count > 0) {
    JsonArray supported_rates = packet["supported_rates"].to<JsonArray>();
    for (uint8_t i = 0; i < capture.packet.capabilities.supported_rates_count; i++) {
      supported_rates.add(capture.packet.capabilities.supported_rates[i]);
    }
  }

  // Extended rates
  if (capture.packet.capabilities.extended_rates_count > 0) {
    JsonArray extended_rates = packet["extended_rates"].to<JsonArray>();
    for (uint8_t i = 0; i < capture.packet.capabilities.extended_rates_count; i++) {
      extended_rates.add(capture.packet.capabilities.extended_rates[i]);
    }
  }

  // HT capabilities
  if (capture.packet.capabilities.ht_capabilities.present) {
    JsonObject ht_cap = packet["ht_capabilities"].to<JsonObject>();
    ht_cap["present"] = true;
    ht_cap["mcs_set"] = capture.packet.capabilities.ht_capabilities.mcs_set;
  } else {
    packet["ht_capabilities"] = nullptr;
  }

  // VHT e HE capabilities
  if (capture.packet.capabilities.vht_capabilities) {
    packet["vht_capabilities"]["present"] = true;
  } else {
    packet["vht_capabilities"] = nullptr;
  }

  if (capture.packet.capabilities.he_capabilities) {
    packet["he_capabilities"]["present"] = true;
  } else {
    packet["he_capabilities"] = nullptr;
  }

  // Vendor IEs
  JsonArray vendor_ies = packet["vendor_ies"].to<JsonArray>();
  for (uint8_t i = 0; i < capture.packet.vendor_ies_count; i++) {
    JsonObject vendor_ie = vendor_ies.add<JsonObject>();
    char oui_str[9];
    sprintf(oui_str, "%02x:%02x:%02x",
            capture.packet.vendor_ies[i].oui[0],
            capture.packet.vendor_ies[i].oui[1],
            capture.packet.vendor_ies[i].oui[2]);
    vendor_ie["oui"] = oui_str;
    vendor_ie["vendor_type"] = capture.packet.vendor_ies[i].vendor_type;

    // Payload em hex
    String payload_hex = "";
    for (uint8_t j = 0; j < capture.packet.vendor_ies[i].payload_len; j++) {
      char hex_byte[3];
      sprintf(hex_byte, "%02x", capture.packet.vendor_ies[i].payload[j]);
      payload_hex += hex_byte;
    }
    vendor_ie["payload_hex"] = payload_hex;
    vendor_ie["meaning"] = capture.packet.vendor_ies[i].meaning;
  }

  // IEs raw
  JsonArray ies_raw = packet["ies_raw"].to<JsonArray>();
  for (uint8_t i = 0; i < capture.packet.ies_count; i++) {
    JsonObject ie_raw = ies_raw.add<JsonObject>();
    ie_raw["id"] = capture.packet.ies_raw[i].id;
    ie_raw["len"] = capture.packet.ies_raw[i].len;

    String value_hex = "";
    for (uint8_t j = 0; j < capture.packet.ies_raw[i].len; j++) {
      char hex_byte[3];
      sprintf(hex_byte, "%02x", capture.packet.ies_raw[i].value[j]);
      value_hex += hex_byte;
    }
    ie_raw["value_hex"] = value_hex;
  }

  // MAC info
  packet["mac_randomized"] = capture.packet.mac_randomized;
  packet["oui"] = capture.packet.oui;
  packet["vendor_inferred"] = capture.packet.vendor_inferred;

  // Fingerprint
  JsonObject fingerprint = packet["fingerprint"].to<JsonObject>();
  fingerprint["ie_signature"] = capture.packet.fingerprint.ie_signature;
  fingerprint["confidence"] = capture.packet.fingerprint.confidence;

  String output;
  serializeJson(doc, output);
  Serial.println(output);
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

String create_fingerprint(const packet_data_t& packet) {
  String signature = "";

  // Adicionar informações sobre HT capabilities
  if (packet.capabilities.ht_capabilities.present) {
    signature += "HT+";
  }

  // Adicionar vendor IEs
  for (uint8_t i = 0; i < packet.vendor_ies_count; i++) {
    signature += "VENDOR(";
    char oui_str[9];
    sprintf(oui_str, "%02x:%02x:%02x",
            packet.vendor_ies[i].oui[0],
            packet.vendor_ies[i].oui[1],
            packet.vendor_ies[i].oui[2]);
    signature += oui_str;
    signature += ")+";
  }

  // Adicionar supported rates
  if (packet.capabilities.supported_rates_count > 0) {
    signature += "rates(";
    for (uint8_t i = 0; i < packet.capabilities.supported_rates_count; i++) {
      if (i > 0) signature += ",";
      signature += String(packet.capabilities.supported_rates[i]);
    }
    signature += ")";
  }

  return signature;
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

  unsigned long current_uptime = millis() - stats.uptime_ms;
  unsigned long time_since_startup = millis() - startup_time;
  unsigned long time_to_restart = RESTART_INTERVAL - time_since_startup;

  doc["type"] = "stats";
  doc["uptime_ms"] = current_uptime;
  doc["time_to_restart_ms"] = time_to_restart;
  doc["time_to_restart_minutes"] = time_to_restart / 60000;
  doc["total_packets"] = stats.total_packets;
  doc["probe_requests"] = stats.probe_requests;
  doc["current_channel"] = stats.current_channel;
  doc["scanner_id"] = NODE_ID;
  doc["capture_id"] = current_capture_id;
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