# Estrutura de Pastas Organizada - Resumo das Modificações

## 📁 Nova Estrutura Implementada

```
wifi_package/
├── data/
│   ├── raw/                # Logs originais do ESP32
│   └── analyze/           # Arquivos de análise gerados
├── docs/                  # Documentação do projeto
├── tools/                 # Scripts de análise
└── [outros diretórios do projeto...]
```

## 🔧 Modificações Realizadas

### 1. **Script `analyze_probes.py`**

#### Mudanças Principais:
- ✅ **Diretório de Saída**: Agora salva automaticamente em `./data/analyze/`
- ✅ **Criação Automática**: Cria o diretório se não existir
- ✅ **Compatibilidade**: Mantém funcionalidade de `--output` customizado

#### Comportamento de Saída:

**Padrão (sem --output):**
```bash
python3 tools/analyze_probes.py data/raw/probe_data_20250930_145036.log
# Saída: ./data/analyze/device_summary_20250930_145036.csv
```

**Com gráficos:**
```bash
python3 tools/analyze_probes.py data/raw/probe_data_20250930_145036.log --plots
# Saídas:
# - ./data/analyze/device_summary_20250930_145036.csv
# - ./data/analyze/probe_analysis_20250930_145036.png
```

**Nome simples customizado:**
```bash
python3 tools/analyze_probes.py data/raw/log.log --output report.csv
# Saída: ./data/analyze/report.csv (vai para pasta organize)
```

**Caminho específico:**
```bash
python3 tools/analyze_probes.py data/raw/log.log --output ./custom/report.csv
# Saída: ./custom/report.csv (respeita o caminho)
```

### 2. **Lógica de Decisão de Caminhos**

```python
# Se não especificado --output
output_file = os.path.join(analyze_dir, f'device_summary_{date_suffix}.csv')

# Se especificado nome simples (sem caminho)
if not os.path.isabs(args.output) and not args.output.startswith('./'):
    output_file = os.path.join(analyze_dir, args.output)

# Se especificado caminho absoluto ou relativo
else:
    output_file = args.output
```

### 3. **Função `generate_plots()` Atualizada**

- ✅ Recebe parâmetro `output_dir` (padrão: `'./data/analyze'`)
- ✅ Cria diretório automaticamente se necessário
- ✅ Salva PNG na pasta correta com sufixo de data

## 🧪 Testes Realizados

### Cenários Testados:
1. ✅ **Análise básica**: CSV salvo em `data/analyze/`
2. ✅ **Com gráficos**: CSV + PNG salvos em `data/analyze/`
3. ✅ **Nome customizado simples**: Vai para `data/analyze/`
4. ✅ **Caminho específico**: Respeita o caminho fornecido
5. ✅ **Criação automática de diretórios**: Funcional

### Exemplos de Saída:
```bash
# Estrutura gerada após execução:
data/
├── analyze/
│   ├── device_summary_20250930_145036.csv
│   └── probe_analysis_20250930_145036.png
└── raw/
    └── probe_data_20250930_145036.log
```

## 📚 Documentação Atualizada

### Arquivos Modificados:
- ✅ `docs/README_ANALYZER.md`: Exemplos com nova estrutura
- ✅ Paths atualizados para refletir organização
- ✅ Seção de "Organização de Pastas" adicionada

## 🎯 Benefícios da Nova Estrutura

### 🔍 **Organização Clara**
- **Separação**: Logs brutos vs análises processadas
- **Rastreabilidade**: Fácil correlação entre entrada e saída
- **Manutenção**: Estrutura padrão para todos os projetos

### 🚀 **Automação Melhorada**
- **Zero configuração**: Funciona out-of-the-box
- **Criação automática**: Não precisa criar pastas manualmente
- **Compatibilidade**: Mantém funcionalidades existentes

### 📊 **Fluxo de Trabalho**
```
1. ESP32 gera logs → data/raw/
2. Script processa → data/analyze/
3. Fácil backup e organização
```

## ✅ Status Final

**✅ IMPLEMENTAÇÃO COMPLETA**

- ✅ Script modificado e testado
- ✅ Estrutura de pastas implementada
- ✅ Documentação atualizada
- ✅ Compatibilidade mantida
- ✅ Funcionalidades existentes preservadas

**O sistema está pronto para uso em produção com a nova estrutura organizada!** 🎉