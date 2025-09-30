# ESP32 WiFi Probe Request Monitor

Sistema avançado de detecção e análise de dispositivos móveis (Android/iOS) através da captura de probe requests WiFi no ESP32.

## 📋 Descrição

Este projeto implementa um monitor WiFi que opera em modo promíscuo para capturar e analisar probe requests enviados por dispositivos móveis. É especialmente útil para:

- **Análise de presença**: Detectar dispositivos em uma área específica
- **Contagem de pessoas**: Estimar número de pessoas baseado em dispositivos únicos
- **Estudos de mobilidade**: Análise de padrões de movimento
- **Pesquisa acadêmica**: Coleta de dados para estudos sobre comportamento urbano

## 🚀 Características

### Funcionalidades Principais
- ✅ **Modo Promíscuo WiFi**: Captura todos os frames de management
- ✅ **Filtro de Probe Requests**: Foca apenas em frames relevantes (type/subtype 0x40)
- ✅ **Rotação de Canais**: Varre canais 1-13 para máxima cobertura
- ✅ **Detecção de MAC Randomizado**: Identifica endereços MAC aleatorizados
- ✅ **Identificação de Vendor**: Reconhece fabricantes (Apple, Samsung, etc.)
- ✅ **Extração de SSIDs**: Lista redes procuradas pelo dispositivo
- ✅ **Output JSON Estruturado**: Formato padronizado para análise
- ✅ **Estatísticas em Tempo Real**: Monitoramento de performance

### Dados Coletados
```json
{
  "timestamp": 12345678,
  "mac": "AA:BB:CC:DD:EE:FF",
  "rssi": -45,
  "ssid_list": ["WiFi_Network", "Another_Network"],
  "channel": 6,
  "node_id": "ESP32_PROBE_001",
  "sequence": 1234,
  "randomized": true,
  "vendor": "Apple"
}
```

## 🛠️ Hardware Necessário

### Configurações Disponíveis

#### 📡 **ESP32-S3 DevKit (Padrão)**
- **Recomendado para**: Desenvolvimento e testes
- **Antena**: Interna integrada
- **Alcance**: ~30-50m em área aberta
- **Facilidade**: Plug-and-play, sem configuração adicional

#### 🔥 **ESP32-32U com Antena Externa (Alta Performance)**
- **Recomendado para**: Produção e máximo alcance
- **Antena**: Externa 2.4GHz (até 15 dBi)
- **Alcance**: 100-200m+ em área aberta
- **Configuração**: GPIO para switch de antena

### Hardware Comum
- **Cabo USB** para programação e alimentação
- **Fonte externa** (opcional, para maior estabilidade)

## 📦 Instalação

### 1. Pré-requisitos
- [PlatformIO](https://platformio.org/) instalado
- [VS Code](https://code.visualstudio.com/) com extensão PlatformIO

### 2. Configuração do Projeto
```bash
# Clone este repositório
git clone <your-repo-url>
cd wifi_package

# Para ESP32-S3 DevKit (padrão - antena interna)
pio run -e esp32-s3 -t upload

# Para ESP32-32U com antena externa (máximo alcance)
pio run -e esp32-32u -t upload

# Monitor serial (qualquer configuração)
pio device monitor
```

> **📡 Para ESP32-32U**: Consulte [ESP32-32U_SETUP.md](ESP32-32U_SETUP.md) para configuração detalhada da antena externa.

### 3. Dependências
O projeto usa as seguintes bibliotecas (configuradas automaticamente):
- `ArduinoJson@^7.0.4`: Para formatação JSON
- `Adafruit NeoPixel@^1.15.1`: Para indicadores LED (opcional)

## 🔧 Configuração

### Parâmetros Principais (`include/wifi_probe_monitor.h`)
```cpp
#define NODE_ID "ESP32_PROBE_001"           // ID único do dispositivo
#define MAX_CHANNELS 13                     // Canais WiFi a varrer (1-13)
#define CHANNEL_SWITCH_INTERVAL 500         // Tempo por canal (ms)
#define MAX_SSID_COUNT 20                   // Máximo de SSIDs por probe
```

### Canais WiFi Suportados
- **Canais 1-13**: Cobertura completa 2.4GHz
- **Rotação automática**: 500ms por canal (configurável)
- **Cobertura total**: ~6.5 segundos por ciclo completo

## 📊 Análise dos Dados

### Formato de Saída
Cada probe request gera uma linha JSON com:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `timestamp` | number | Timestamp em milissegundos |
| `mac` | string | Endereço MAC do dispositivo |
| `rssi` | number | Força do sinal (-100 a 0 dBm) |
| `ssid_list` | array | Lista de redes procuradas |
| `channel` | number | Canal WiFi onde foi capturado |
| `node_id` | string | ID do monitor ESP32 |
| `sequence` | number | Número de sequência do frame |
| `randomized` | boolean | Se o MAC é randomizado |
| `vendor` | string | Fabricante identificado |

### Exemplo de Saída Real
```json
{"timestamp":15234,"mac":"A2:B3:C4:D5:E6:F7","rssi":-42,"ssid_list":["iPhone de João","Casa_WiFi"],"channel":6,"node_id":"ESP32_PROBE_001","sequence":1842,"randomized":true,"vendor":"Apple"}
{"timestamp":15891,"mac":"D8:E9:FA:0B:1C:2D","rssi":-68,"ssid_list":["AndroidAP","Shopping_WiFi"],"channel":1,"node_id":"ESP32_PROBE_001","sequence":2156,"randomized":false,"vendor":"Samsung"}
```

### Estatísticas do Sistema
A cada 30 segundos, o sistema imprime estatísticas:
```json
# STATS: {"type":"stats","uptime_ms":180000,"total_packets":15420,"probe_requests":2341,"current_channel":8,"node_id":"ESP32_PROBE_001","free_heap":245632,"min_free_heap":240128}
```

## 📈 Interpretação dos Resultados

### Detecção de Dispositivos Android
- **MAC Randomizado**: Indica Android 6+ ou iOS 8+
- **SSIDs Específicos**: Podem indicar redes salvas no dispositivo
- **Frequência de Probe**: Dispositivos ativos fazem mais probe requests

### Padrões Observados
1. **iPhones**: Frequentemente usam MAC randomizado, probe requests esporádicos
2. **Android**: Varia por versão, alguns modelos são mais "conversadores"
3. **Tablets**: Geralmente menos probe requests que smartphones
4. **Dispositivos IoT**: Padrões distintos de SSID e frequência

### Análise de Presença
- **RSSI > -50 dBm**: Dispositivo muito próximo (< 5m)
- **RSSI -50 a -70 dBm**: Proximidade média (5-20m)
- **RSSI < -70 dBm**: Dispositivo distante (> 20m)

## 🔬 Aplicações Práticas

### 1. Contagem de Pessoas
```python
# Script Python para análise (exemplo)
import json
from collections import defaultdict

unique_devices = defaultdict(list)
for line in log_file:
    data = json.loads(line)
    mac = data['mac']
    timestamp = data['timestamp']
    unique_devices[mac].append(timestamp)

print(f"Dispositivos únicos detectados: {len(unique_devices)}")
```

### 2. Mapa de Calor de Presença
- Use múltiplos ESP32s em diferentes locais
- Correlacione RSSI com posicionamento
- Crie visualizações em tempo real

### 3. Análise Temporal
- Identifique padrões de horário de pico
- Detecte eventos ou gatherings
- Monitore fluxo em espaços públicos

## ⚖️ Considerações Éticas e Legais

### ⚠️ IMPORTANTE - Uso Responsável
- **Privacidade**: Este sistema coleta dados de dispositivos próximos
- **Anonimização**: MACs randomizados oferecem alguma proteção
- **Legislação Local**: Verifique leis locais sobre interceptação WiFi
- **Consentimento**: Considere avisos em áreas monitoradas
- **Retenção de Dados**: Implemente políticas de exclusão

### Boas Práticas
- ✅ Use apenas para pesquisa legítima
- ✅ Anonimize dados coletados
- ✅ Implemente rotação de logs
- ✅ Respeite privacidade individual
- ❌ Não use para tracking individual
- ❌ Não correlacione com dados pessoais

## 🐛 Troubleshooting

### Problemas Comuns

**Poucos probe requests detectados:**
- Verifique se há dispositivos WiFi ativos na área
- Ajuste `CHANNEL_SWITCH_INTERVAL` (tente 1000ms)
- Considere usar antena externa

**ESP32 reinicia constantemente:**
- Verifique alimentação (use fonte 5V/2A)
- Monitore uso de memória nas estatísticas
- Reduza `MAX_SSID_COUNT` se necessário

**JSON malformado:**
- Caracteres especiais em SSIDs podem causar problemas
- Monitor serial pode truncar linhas longas
- Use baud rate adequado (115200)

### Debug Avançado
```cpp
// No main.cpp, adicione para debug:
#define DEBUG_FRAMES 1

// Ative logs detalhados:
#define CORE_DEBUG_LEVEL 3
```

## 📚 Referências Técnicas

- [ESP-IDF WiFi API](https://docs.espressif.com/projects/esp-idf/en/v5.0.6/esp32/api-reference/network/esp_wifi.html)
- [IEEE 802.11 Standard](https://standards.ieee.org/ieee/802.11/7028/)
- [WiFi Frame Format](https://mrncciew.com/2014/10/08/802-11-mgmt-probe-requestresponse/)
- [MAC Address Randomization](https://papers.mathyvanhoef.com/asiaccs2016.pdf)

## 🤝 Contribuições

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma feature branch
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto é fornecido para fins educacionais e de pesquisa. Use responsavelmente e de acordo com as leis locais.

---

**⚡ Desenvolvido para ESP32-S3 | PlatformIO | Arduino Framework**