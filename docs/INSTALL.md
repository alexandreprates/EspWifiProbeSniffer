# GUIA DE INSTALAÇÃO E USO - ESP32 WiFi Probe Monitor

## 🚀 Instalação Rápida

### 1. Preparar o ambiente
```bash
# No macOS/Linux:
git clone <your-repo>
cd wifi_package

# Instalar PlatformIO se não tiver
pip install platformio

# Instalar dependências Python para análise
cd tools
pip install -r requirements.txt
```

### 2. Upload para ESP32
```bash
# Conectar ESP32-S3 via USB-C
# Compilar e fazer upload
pio run -t upload

# Monitorar saída serial
pio device monitor
```

### 3. Coleta de dados
```bash
# Capturar para arquivo por 10 minutos
timeout 600 pio device monitor > probe_data_$(date +%Y%m%d_%H%M%S).log

# Ou manualmente: CTRL+C para parar
pio device monitor > meus_dados.log
```

### 4. Análise dos dados
```bash
# Análise básica
python tools/analyze_probes.py meus_dados.log

# Com gráficos
python tools/analyze_probes.py meus_dados.log --plots

# Output customizado
python tools/analyze_probes.py meus_dados.log -o relatorio.csv
```

## 📊 Exemplo de saída

### Console do ESP32:
```
=== ESP32 WiFi Probe Request Monitor ===
WiFi promiscuous mode iniciado no canal 1

{"timestamp":15234,"mac":"A2:B3:C4:D5:E6:F7","rssi":-42,"ssid_list":["iPhone_João"],"channel":6,"node_id":"ESP32_PROBE_001","sequence":1842,"randomized":true,"vendor":"Apple"}
{"timestamp":15891,"mac":"D8:E9:FA:0B:1C:2D","rssi":-68,"ssid_list":["AndroidAP"],"channel":1,"node_id":"ESP32_PROBE_001","sequence":2156,"randomized":false,"vendor":"Samsung"}

# STATS: {"type":"stats","uptime_ms":30000,"total_packets":1542,"probe_requests":234,"current_channel":8,"free_heap":245632}
```

### Análise Python:
```
=== ANÁLISE DE DISPOSITIVOS ===
Total de dispositivos únicos: 13
Dispositivos com MAC randomizado: 6 (46.2%)

Dispositivos por fabricante:
  Apple: 6
  Samsung: 5
  Unknown: 2

Top 10 dispositivos mais ativos:
  A2:B3:C4:D5:E6:F7: 2 probes, RSSI médio: -43.0 dBm
```

## 🔧 Configurações Avançadas

### Ajustar sensibilidade (main.cpp):
```cpp
#define CHANNEL_SWITCH_INTERVAL 1000  // Mais tempo por canal
#define MAX_SSID_COUNT 30             // Mais SSIDs por probe
```

### Filtrar por RSSI:
```cpp
// No callback wifi_promiscuous_rx, adicionar:
if (pkt->rx_ctrl.rssi < -70) return;  // Ignorar sinais fracos
```

### Múltiplos monitores:
```cpp
#define NODE_ID "ESP32_ENTRADA"    // Monitor 1
#define NODE_ID "ESP32_SAIDA"      // Monitor 2
```

## 🛠️ Troubleshooting

### Problema: Poucas detecções
**Solução:**
- Verificar se há dispositivos WiFi ativos
- Aumentar CHANNEL_SWITCH_INTERVAL para 1000ms
- Usar antena externa
- Posicionar ESP32 em local central

### Problema: ESP32 reinicia
**Solução:**
- Usar fonte externa 5V/2A
- Reduzir MAX_SSID_COUNT
- Verificar conexões

### Problema: JSON inválido
**Solução:**
- Verificar baudrate (115200)
- Filtrar linhas de debug:
```bash
grep '^{' dados.log > dados_limpos.log
```

### Problema: Memória insuficiente
**Solução:**
```cpp
// Reduzir buffers
#define MAX_SSID_COUNT 10
#define JSON_BUFFER_SIZE 256
```

## 📈 Análise Avançada

### Contagem em tempo real:
```bash
# Contar dispositivos únicos
tail -f dados.log | grep -v "^#" | jq -r '.mac' | sort | uniq | wc -l
```

### Filtrar por vendor:
```bash
# Apenas dispositivos Apple
grep '"vendor":"Apple"' dados.log | jq '.mac' | sort | uniq
```

### Análise temporal:
```python
import pandas as pd
import json

# Carregar dados
data = []
with open('dados.log') as f:
    for line in f:
        if line.startswith('{'):
            data.append(json.loads(line))

df = pd.DataFrame(data)
df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')

# Dispositivos únicos por hora
hourly = df.groupby(df['datetime'].dt.hour)['mac'].nunique()
print(hourly)
```

## 🎯 Casos de Uso

### 1. Análise de tráfego de pessoas
- Monitor em entrada/saída
- Correlacionar com horários
- Identificar padrões

### 2. Mapeamento de dispositivos
- Múltiplos ESP32 com NODE_ID diferentes
- Triangulação por RSSI
- Mapa de presença

### 3. Detecção de eventos
- Picos anômalos de dispositivos
- Alertas em tempo real
- Análise de tendências

### 4. Pesquisa acadêmica
- Coleta padronizada
- Export para ferramentas de análise
- Anonimização de dados

## ⚖️ Considerações Legais

### ✅ Uso Permitido:
- Pesquisa acadêmica
- Propriedade privada com avisos
- Análise agregada sem identificação
- Estudos de mobilidade urbana

### ❌ Uso Proibido:
- Tracking individual sem consentimento
- Comercialização de dados pessoais
- Vigilância não autorizada
- Correlação com identidades

### 📋 Boas Práticas:
- Implementar rotação de logs (7 dias)
- Anonizar MACs após coleta
- Documentar finalidade do estudo
- Respeitar legislação local (LGPD, GDPR)

## 🔗 Links Úteis

- [Documentação ESP-IDF WiFi](https://docs.espressif.com/projects/esp-idf/en/v5.0.6/esp32/api-reference/network/esp_wifi.html)
- [IEEE 802.11 Standard](https://www.ieee802.org/11/)
- [PlatformIO Docs](https://docs.platformio.org/)
- [ArduinoJson Library](https://arduinojson.org/)

## 📞 Suporte

Para dúvidas técnicas:
1. Verificar troubleshooting acima
2. Consultar logs de compilação
3. Testar com dados de exemplo
4. Abrir issue no repositório

---
**Desenvolvido para ESP32-S3 | Framework Arduino | PlatformIO**