# Analisador de Dados do ESP32 WiFi Probe Monitor

## Visão Geral

O script `analyze_probes.py` processa logs JSON gerados pelo ESP32 WiFi Probe Monitor e produz análises detalhadas sobre dispositivos WiFi detectados.

## Funcionalidades

### 🔍 **Análises Realizadas**
- **Dispositivos Únicos**: Contagem e análise de dispositivos detectados
- **Padrões Temporais**: Análise de atividade por hora e canal
- **Força do Sinal**: Distribuição de RSSI e classificação por proximidade
- **SSIDs**: Análise de redes procuradas pelos dispositivos
- **Vendors**: Identificação de fabricantes de dispositivos

### 📊 **Saídas Geradas**

- **CSV de Resumo**: `./data/analyze/device_summary_<data>.csv` com estatísticas por dispositivo
- **Gráficos PNG**: `./data/analyze/probe_analysis_<data>.png` com visualizações
- **Relatório Console**: Análise detalhada em tempo real

## Nomenclatura de Arquivos

### 🎯 **Sistema de Sufixos de Data**
O script automaticamente extrai o sufixo de data do arquivo de log e aplica aos arquivos de saída:

```bash
# Arquivo de entrada:
data/raw/probe_data_20250930_144336.log

# Arquivos de saída gerados:
data/analyze/device_summary_20250930_144336.csv
data/analyze/probe_analysis_20250930_144336.png
```

### 📅 **Padrão de Data Esperado**
- **Formato**: `_YYYYMMDD_HHMMSS.log`
- **Exemplo**: `probe_data_20250930_144336.log`
- **Fallback**: Se não houver padrão de data, usa timestamp atual

## Uso

### Comando Básico
```bash
python3 analyze_probes.py <arquivo_log>
```

### Com Gráficos
```bash
python3 analyze_probes.py <arquivo_log> --plots
```

### Especificar Arquivo de Saída
```bash
python3 analyze_probes.py <arquivo_log> --output custom_name.csv
```

## Exemplos de Uso

### Exemplo 1: Análise Simples

```bash
python3 tools/analyze_probes.py data/raw/probe_data_20250930_144336.log
```

**Saída**: `data/analyze/device_summary_20250930_144336.csv`

### Exemplo 2: Com Gráficos

```bash
python3 tools/analyze_probes.py data/raw/probe_data_20250930_144336.log --plots
```

**Saídas**:

- `data/analyze/device_summary_20250930_144336.csv`
- `data/analyze/probe_analysis_20250930_144336.png`

### Exemplo 3: Nome Customizado

```bash
python3 tools/analyze_probes.py data/raw/probe_data_20250930_144336.log --output relatorio_especial.csv
```

**Saída**: `data/analyze/relatorio_especial.csv`## Formato de Entrada

### Log JSON Esperado
```json
{"type":"probe_request","timestamp":1727705416123,"mac":"aa:bb:cc:dd:ee:01","ssid":"WiFi-Test","rssi":-45,"channel":6,"sequence":1234,"vendor":"Apple","randomized":false}
```

### Campos Obrigatórios
- `timestamp`: Unix timestamp em milissegundos
- `mac`: Endereço MAC do dispositivo
- `rssi`: Força do sinal em dBm
- `channel`: Canal WiFi

### Campos Opcionais
- `ssid`: SSID procurado
- `vendor`: Fabricante do dispositivo
- `randomized`: Se o MAC é randomizado
- `sequence`: Número de sequência

## Saídas Detalhadas

### 📋 **CSV de Resumo**
| Campo | Descrição |
|-------|-----------|
| `mac` | Endereço MAC do dispositivo |
| `vendor` | Fabricante identificado |
| `randomized` | Se usa MAC randomizado |
| `probe_count` | Total de probe requests |
| `avg_rssi` | RSSI médio em dBm |
| `duration_seconds` | Duração da detecção |
| `first_seen` | Primeira detecção |
| `last_seen` | Última detecção |

### 📈 **Gráficos Gerados**
1. **Atividade Temporal**: Probe requests por minuto
2. **Distribuição RSSI**: Histograma de força do sinal
3. **Atividade por Canal**: Probe requests por canal WiFi
4. **Dispositivos Únicos**: Contagem por hora

### 🖥️ **Relatório Console**
- Estatísticas gerais de dispositivos
- Top 10 dispositivos mais ativos
- Análise de padrões temporais
- Classificação por força do sinal
- Lista de SSIDs mais procurados

## Dependências

### Python 3.6+
```bash
pip install pandas matplotlib seaborn
```

### Bibliotecas Necessárias
- `pandas`: Processamento de dados
- `matplotlib`: Geração de gráficos
- `seaborn`: Estilização de gráficos
- `json`: Parsing de dados (built-in)
- `argparse`: Interface de linha de comando (built-in)

## Opções de Linha de Comando

```
usage: analyze_probes.py [-h] [--output OUTPUT] [--plots] log_file

Analisador de dados do ESP32 WiFi Probe Monitor

positional arguments:
  log_file              Arquivo de log para analisar

optional arguments:
  -h, --help            show this help message and exit
  --output OUTPUT, -o OUTPUT
                        Arquivo de saída CSV (padrão: device_summary_<data>.csv)
  --plots, -p           Gerar gráficos de análise
```

## Tratamento de Erros

### Arquivo Não Encontrado
```
Erro: Arquivo 'arquivo_inexistente.log' não encontrado
```

### Dados Inválidos
```
Erro: Nenhum dado válido encontrado no arquivo de log
```

### Linha com Erro JSON
```
Erro JSON na linha 15: Expecting ',' delimiter: line 1 column 45 (char 44)
```

## Exemplos de Saída

### Console Output
```
=== ANÁLISE DE DISPOSITIVOS ===
Total de dispositivos únicos: 4
Dispositivos com MAC randomizado: 2 (50.0%)

Dispositivos por fabricante:
  Apple: 1
  Samsung: 1
  Unknown: 1
  Google: 1

=== ANÁLISE CONCLUÍDA ===
Dados processados: 5 probe requests
Resumo salvo em: device_summary_20250930_144336.csv
Gráficos salvos em: probe_analysis_20250930_144336.png
```

### Estrutura de Arquivos Resultantes

```
projeto/
├── data/
│   ├── raw/
│   │   └── probe_data_20250930_144336.log      # Log de entrada
│   └── analyze/
│       ├── device_summary_20250930_144336.csv  # Resumo CSV
│       └── probe_analysis_20250930_144336.png  # Gráficos PNG
├── tools/
│   └── analyze_probes.py                       # Script principal
└── docs/
    └── README_ANALYZER.md                      # Esta documentação
```

## Organização de Pastas

### 📁 **Estrutura do Projeto**

O analisador segue uma estrutura organizada de pastas:

- **`./data/raw/`**: Logs originais gerados pelo ESP32
- **`./data/analyze/`**: Arquivos de análise gerados pelo script
- **`./tools/`**: Scripts de análise e ferramentas
- **`./docs/`**: Documentação do projeto

### 🎯 **Comportamento de Saída**

#### Saída Padrão (sem --output)
```bash
# Comando:
python3 tools/analyze_probes.py data/raw/probe_data_20250930_144336.log

# Saída automática:
data/analyze/device_summary_20250930_144336.csv
```

#### Com Gráficos
```bash
# Comando:
python3 tools/analyze_probes.py data/raw/probe_data_20250930_144336.log --plots

# Saídas automáticas:
data/analyze/device_summary_20250930_144336.csv
data/analyze/probe_analysis_20250930_144336.png
```

#### Nome Simples Customizado
```bash
# Comando:
python3 tools/analyze_probes.py data/raw/log.log --output my_report.csv

# Saída:
data/analyze/my_report.csv  # Vai para pasta organize automaticamente
```

#### Caminho Absoluto ou Relativo
```bash
# Comando:
python3 tools/analyze_probes.py data/raw/log.log --output ./custom/report.csv

# Saída:
./custom/report.csv  # Respeita o caminho especificado
```

## Integração com Sistema de Logs

O sistema automaticamente:
1. **Detecta** o padrão de data no nome do arquivo
2. **Extrai** o sufixo `YYYYMMDD_HHMMSS`
3. **Aplica** o mesmo sufixo aos arquivos de saída
4. **Garante** rastreabilidade temporal dos dados

Isso permite correlacionar facilmente os dados de entrada com suas análises correspondentes.