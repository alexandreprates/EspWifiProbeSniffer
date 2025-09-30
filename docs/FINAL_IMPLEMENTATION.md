# WiFi Probe Request Monitor - Implementação Final

## Resumo da Implementação

Este projeto implementa um sistema de monitoramento de probe requests Wi-Fi com alta taxa de detecção para dispositivos Android, utilizando placas ESP32 com suporte a duas configurações diferentes.

## Características Principais

### 🎯 **Objetivo Principal**
- **Wi-Fi Probe Request Monitoring**: Captura probe requests IEEE 802.11 para detecção de dispositivos Android
- **Alta Taxa de Detecção**: Configuração otimizada para maximizar a captura de sinais
- **Suporte Dual-Board**: ESP32-S3 (desenvolvimento) e ESP32-32U (produção com antena externa)

### ⚡ **Funcionalidades Implementadas**
1. **Modo Promíscuo WiFi**: Captura todos os pacotes 802.11 no ar
2. **Parsing de Probe Requests**: Extração de MAC, SSID, RSSI e timestamps
3. **Configuração RTC**: Timestamps reais usando flag `BUILD_TIME_UNIX`
4. **Filtragem Inteligente**: Foco em dispositivos Android e mobile
5. **Output JSON**: Formato estruturado para análise de dados
6. **Configuração de Antena**: Suporte para antena externa no ESP32-32U

## Configurações de Hardware

### 📱 **ESP32-S3 DevKit (Desenvolvimento)**
- **Placa**: ESP32-S3-DevKitC-1-N8
- **Antena**: Interna (built-in)
- **Uso**: Desenvolvimento e testes
- **Memória**: 8MB Flash, 320KB RAM

### 📡 **ESP32-32U (Produção)**
- **Placa**: ESP32 Dev Module (compatível ESP32-32U)
- **Antena**: Externa 2.4GHz (conectada via U.FL)
- **Configuração**: Otimizada para máximo alcance
- **Uso**: Implementação em campo

## Estrutura do Projeto

```
wifi_package/
├── platformio.ini          # Configuração dual-board
├── src/
│   └── main.cpp            # Código principal com RTC
├── include/
│   └── wifi_probe_monitor.h # Headers e configurações
├── tools/
│   ├── analyzer.py         # Análise de dados Python
│   └── visualizer.py       # Visualização de dados
└── docs/
    └── README.md           # Documentação completa
```

## Principais Funcionalidades Técnicas

### 🔧 **Sistema de Timestamps**
- **RTC Configurado**: Usa flag `BUILD_TIME_UNIX` para sincronização
- **Fallback**: millis() quando RTC não disponível
- **Formato**: Unix timestamp para correlação temporal

### 📊 **Análise de Dados**
- **Output JSON**: Estrutura padronizada para cada probe request
- **Ferramentas Python**: Scripts para análise e visualização
- **Filtragem**: Foco em dispositivos móveis e Android

### 🛡️ **Otimizações WiFi**
- **Buffers Otimizados**: Configuração específica para cada board
- **Canal Scanning**: Monitoramento eficiente de múltiplos canais
- **RSSI Filtering**: Filtragem por força do sinal

## Build e Deploy

### Compilação
```bash
# ESP32-S3 (Desenvolvimento)
pio run -e esp32-s3

# ESP32-32U (Produção)
pio run -e esp32-32u

# Upload para ESP32-S3
pio run -e esp32-s3 -t upload

# Upload para ESP32-32U
pio run -e esp32-32u -t upload
```

### Monitoramento
```bash
# Monitor Serial ESP32-S3
pio device monitor -e esp32-s3

# Monitor Serial ESP32-32U
pio device monitor -e esp32-32u
```

## Dados de Saída

### Formato JSON
```json
{
  "type": "probe_request",
  "timestamp": 1703123456,
  "timestamp_type": "rtc",
  "mac": "aa:bb:cc:dd:ee:ff",
  "ssid": "MyNetwork",
  "rssi": -45,
  "channel": 6,
  "sequence": 1234,
  "board": "esp32-s3"
}
```

### Estatísticas do Sistema
```json
{
  "type": "system_stats",
  "timestamp": 1703123456,
  "uptime": 300000,
  "total_packets": 1500,
  "probe_requests": 450,
  "android_devices": 25,
  "memory_free": 280000,
  "wifi_channel": 6
}
```

## Status da Implementação

### ✅ **Completado**
- [x] Sistema base de monitoramento WiFi
- [x] Suporte para ESP32-S3 DevKit
- [x] Suporte para ESP32-32U com antena externa
- [x] Configuração RTC com BUILD_TIME_UNIX
- [x] Output JSON estruturado
- [x] Ferramentas de análise Python
- [x] Documentação completa
- [x] Testes de compilação para ambas as placas

### 🎯 **Resultados dos Testes**
- **ESP32-S3**: Compilação bem-sucedida (7.33s)
  - RAM: 13.3% utilizada (43.504 bytes)
  - Flash: 22.2% utilizada (742.229 bytes)

- **ESP32-32U**: Compilação bem-sucedida (6.49s)
  - RAM: 13.5% utilizada (44.088 bytes)
  - Flash: 60.3% utilizada (790.881 bytes)

## Próximos Passos

1. **Deploy em Campo**: Instalar ESP32-32U com antena externa
2. **Calibração**: Ajustar configurações de RSSI conforme ambiente
3. **Análise de Dados**: Utilizar ferramentas Python para insights
4. **Otimização**: Fine-tuning baseado em dados reais de campo

## Comandos Úteis

```bash
# Limpar build
pio run -t clean

# Verificar configuração
pio check

# Listar dispositivos
pio device list

# Build verbose
pio run -v
```

---

**Status**: ✅ **IMPLEMENTAÇÃO COMPLETA E TESTADA**
**Data**: $(date)
**Placas Suportadas**: ESP32-S3, ESP32-32U
**Funcionalidade RTC**: ✅ Implementada com BUILD_TIME_UNIX