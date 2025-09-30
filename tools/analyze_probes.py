#!/usr/bin/env python3
"""
Analisador de Dados do ESP32 WiFi Probe Monitor
Processa logs JSON e gera estatísticas sobre dispositivos detectados
"""

import json
import argparse
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import seaborn as sns
import re
import os

class ProbeAnalyzer:
    def __init__(self, log_file):
        self.log_file = log_file
        self.probe_data = []
        self.stats_data = []
        self.date_suffix = self._extract_date_suffix(log_file)
        self.load_data()

    def _extract_date_suffix(self, log_file):
        """Extrai o sufixo de data do nome do arquivo de log"""
        # Padrão: probe_data_YYYYMMDD_HHMMSS.log
        basename = os.path.basename(log_file)
        match = re.search(r'_(\d{8}_\d{6})\.log$', basename)
        if match:
            return match.group(1)

        # Fallback: usar timestamp atual
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def load_data(self):
        """Carrega e processa dados do arquivo de log"""
        print(f"Carregando dados de {self.log_file}...")

        with open(self.log_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    if line.startswith('# STATS:'):
                        # Linha de estatísticas
                        json_part = line.replace('# STATS: ', '')
                        data = json.loads(json_part)
                        self.stats_data.append(data)
                    elif line.startswith('#'):
                        # Outras linhas de comentário, ignorar
                        continue
                    else:
                        # Dados de probe request
                        data = json.loads(line)
                        # Validar campos obrigatórios
                        required_fields = ['timestamp', 'mac', 'rssi', 'channel']
                        if all(field in data for field in required_fields):
                            self.probe_data.append(data)
                        else:
                            print(f"Linha {line_num}: Campos obrigatórios faltando")

                except json.JSONDecodeError as e:
                    print(f"Erro JSON na linha {line_num}: {e}")
                except Exception as e:
                    print(f"Erro na linha {line_num}: {e}")

        print(f"Carregados {len(self.probe_data)} probe requests e {len(self.stats_data)} estatísticas")

    def analyze_devices(self):
        """Análise de dispositivos únicos detectados"""
        print("\n=== ANÁLISE DE DISPOSITIVOS ===")

        device_stats = defaultdict(lambda: {
            'first_seen': float('inf'),
            'last_seen': 0,
            'probe_count': 0,
            'channels': set(),
            'rssi_values': [],
            'ssids': set(),
            'vendor': 'Unknown',
            'randomized': False
        })

        for probe in self.probe_data:
            mac = probe['mac']
            timestamp = probe['timestamp']

            stats = device_stats[mac]
            stats['first_seen'] = min(stats['first_seen'], timestamp)
            stats['last_seen'] = max(stats['last_seen'], timestamp)
            stats['probe_count'] += 1
            stats['channels'].add(probe['channel'])
            stats['rssi_values'].append(probe['rssi'])

            if 'vendor' in probe:
                stats['vendor'] = probe['vendor']
            if 'randomized' in probe:
                stats['randomized'] = probe['randomized']

            # Processar SSIDs
            if 'ssid_list' in probe and isinstance(probe['ssid_list'], list):
                stats['ssids'].update(probe['ssid_list'])

        # Estatísticas gerais
        total_devices = len(device_stats)
        randomized_devices = sum(1 for stats in device_stats.values() if stats['randomized'])

        print(f"Total de dispositivos únicos: {total_devices}")
        print(f"Dispositivos com MAC randomizado: {randomized_devices} ({randomized_devices/total_devices*100:.1f}%)")

        # Análise por vendor
        vendor_count = Counter(stats['vendor'] for stats in device_stats.values())
        print(f"\nDispositivos por fabricante:")
        for vendor, count in vendor_count.most_common():
            print(f"  {vendor}: {count}")

        # Dispositivos mais ativos
        most_active = sorted(device_stats.items(),
                           key=lambda x: x[1]['probe_count'], reverse=True)[:10]

        print(f"\nTop 10 dispositivos mais ativos:")
        for mac, stats in most_active:
            duration = (stats['last_seen'] - stats['first_seen']) / 1000  # segundos
            avg_rssi = sum(stats['rssi_values']) / len(stats['rssi_values'])
            print(f"  {mac}: {stats['probe_count']} probes, "
                  f"RSSI médio: {avg_rssi:.1f} dBm, "
                  f"Duração: {duration:.1f}s, "
                  f"Vendor: {stats['vendor']}")

        return device_stats

    def analyze_temporal_patterns(self):
        """Análise de padrões temporais"""
        print("\n=== ANÁLISE TEMPORAL ===")

        if not self.probe_data:
            print("Sem dados para análise temporal")
            return

        # Converter timestamps para datetime
        df = pd.DataFrame(self.probe_data)
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')

        # Análise por hora
        df['hour'] = df['datetime'].dt.hour
        hourly_counts = df.groupby('hour').size()

        print("Atividade por hora do dia:")
        for hour, count in hourly_counts.items():
            print(f"  {hour:02d}:00 - {count} probe requests")

        # Análise por canal
        channel_counts = df.groupby('channel').size()
        print(f"\nAtividade por canal WiFi:")
        for channel, count in channel_counts.items():
            print(f"  Canal {channel}: {count} probe requests")

        return df

    def analyze_signal_strength(self):
        """Análise de força do sinal (RSSI)"""
        print("\n=== ANÁLISE DE FORÇA DO SINAL ===")

        rssi_values = [probe['rssi'] for probe in self.probe_data]

        if not rssi_values:
            print("Sem dados de RSSI")
            return

        avg_rssi = sum(rssi_values) / len(rssi_values)
        min_rssi = min(rssi_values)
        max_rssi = max(rssi_values)

        print(f"RSSI médio: {avg_rssi:.1f} dBm")
        print(f"RSSI mínimo: {min_rssi} dBm")
        print(f"RSSI máximo: {max_rssi} dBm")

        # Classificação por proximidade
        very_close = sum(1 for rssi in rssi_values if rssi > -50)
        close = sum(1 for rssi in rssi_values if -70 <= rssi <= -50)
        far = sum(1 for rssi in rssi_values if rssi < -70)

        total = len(rssi_values)
        print(f"\nClassificação por proximidade:")
        print(f"  Muito próximo (>-50 dBm): {very_close} ({very_close/total*100:.1f}%)")
        print(f"  Proximidade média (-70 a -50 dBm): {close} ({close/total*100:.1f}%)")
        print(f"  Distante (<-70 dBm): {far} ({far/total*100:.1f}%)")

    def analyze_ssids(self):
        """Análise de SSIDs procurados"""
        print("\n=== ANÁLISE DE SSIDs ===")

        all_ssids = []
        for probe in self.probe_data:
            if 'ssid_list' in probe and isinstance(probe['ssid_list'], list):
                all_ssids.extend(probe['ssid_list'])

        if not all_ssids:
            print("Nenhum SSID encontrado nos dados")
            return

        ssid_counts = Counter(all_ssids)

        print(f"Total de SSIDs únicos: {len(ssid_counts)}")
        print(f"Top 20 SSIDs mais procurados:")

        for ssid, count in ssid_counts.most_common(20):
            if ssid:  # Ignorar SSIDs vazios
                print(f"  '{ssid}': {count} vezes")

    def generate_plots(self, output_dir='./data/analyze'):
        """Gera gráficos de análise"""
        if not self.probe_data:
            print("Sem dados para gerar gráficos")
            return

        print("\n=== GERANDO GRÁFICOS ===")

        # Garantir que o diretório existe
        os.makedirs(output_dir, exist_ok=True)

        df = pd.DataFrame(self.probe_data)
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')

        # Configurar estilo
        plt.style.use('seaborn-v0_8')
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Análise de Probe Requests WiFi', fontsize=16)

        # Gráfico 1: Atividade temporal
        df.set_index('datetime').resample('1T').size().plot(ax=axes[0,0])
        axes[0,0].set_title('Atividade por Minuto')
        axes[0,0].set_ylabel('Probe Requests')

        # Gráfico 2: Distribuição RSSI
        axes[0,1].hist(df['rssi'], bins=30, alpha=0.7, edgecolor='black')
        axes[0,1].set_title('Distribuição de RSSI')
        axes[0,1].set_xlabel('RSSI (dBm)')
        axes[0,1].set_ylabel('Frequência')

        # Gráfico 3: Atividade por canal
        channel_counts = df['channel'].value_counts().sort_index()
        channel_counts.plot(kind='bar', ax=axes[1,0])
        axes[1,0].set_title('Atividade por Canal WiFi')
        axes[1,0].set_xlabel('Canal')
        axes[1,0].set_ylabel('Probe Requests')

        # Gráfico 4: Dispositivos únicos por hora
        unique_devices_hourly = df.groupby(df['datetime'].dt.hour)['mac'].nunique()
        unique_devices_hourly.plot(kind='line', marker='o', ax=axes[1,1])
        axes[1,1].set_title('Dispositivos Únicos por Hora')
        axes[1,1].set_xlabel('Hora do Dia')
        axes[1,1].set_ylabel('Dispositivos Únicos')

        plt.tight_layout()
        output_file = os.path.join(output_dir, f'probe_analysis_{self.date_suffix}.png')
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Gráficos salvos em '{output_file}'")

    def export_summary(self, output_file):
        """Exporta resumo em CSV"""
        print(f"\n=== EXPORTANDO RESUMO ===")

        device_stats = defaultdict(lambda: {
            'first_seen': float('inf'),
            'last_seen': 0,
            'probe_count': 0,
            'avg_rssi': 0,
            'vendor': 'Unknown',
            'randomized': False
        })

        for probe in self.probe_data:
            mac = probe['mac']
            stats = device_stats[mac]
            stats['first_seen'] = min(stats['first_seen'], probe['timestamp'])
            stats['last_seen'] = max(stats['last_seen'], probe['timestamp'])
            stats['probe_count'] += 1

            if 'vendor' in probe:
                stats['vendor'] = probe['vendor']
            if 'randomized' in probe:
                stats['randomized'] = probe['randomized']

        # Calcular RSSI médio
        for mac in device_stats:
            rssi_values = [p['rssi'] for p in self.probe_data if p['mac'] == mac]
            if rssi_values:
                device_stats[mac]['avg_rssi'] = sum(rssi_values) / len(rssi_values)

        # Converter para DataFrame e exportar
        summary_data = []
        for mac, stats in device_stats.items():
            duration = (stats['last_seen'] - stats['first_seen']) / 1000
            summary_data.append({
                'mac': mac,
                'vendor': stats['vendor'],
                'randomized': stats['randomized'],
                'probe_count': stats['probe_count'],
                'avg_rssi': round(stats['avg_rssi'], 1),
                'duration_seconds': round(duration, 1),
                'first_seen': datetime.fromtimestamp(stats['first_seen']/1000),
                'last_seen': datetime.fromtimestamp(stats['last_seen']/1000)
            })

        df_summary = pd.DataFrame(summary_data)
        df_summary.to_csv(output_file, index=False)
        print(f"Resumo exportado para '{output_file}'")

def main():
    parser = argparse.ArgumentParser(description='Analisador de dados do ESP32 WiFi Probe Monitor')
    parser.add_argument('log_file', help='Arquivo de log para analisar')
    parser.add_argument('--output', '-o', default=None,
                       help='Arquivo de saída CSV (padrão: device_summary_<data>.csv)')
    parser.add_argument('--plots', '-p', action='store_true',
                       help='Gerar gráficos de análise')

    args = parser.parse_args()

    try:
        analyzer = ProbeAnalyzer(args.log_file)

        if not analyzer.probe_data:
            print("Erro: Nenhum dado válido encontrado no arquivo de log")
            return

        # Definir diretório de saída para análises
        analyze_dir = './data/analyze'
        os.makedirs(analyze_dir, exist_ok=True)

        # Definir nome do arquivo de saída com sufixo de data
        if args.output is None:
            output_file = os.path.join(analyze_dir, f'device_summary_{analyzer.date_suffix}.csv')
        else:
            # Se especificado pelo usuário, manter o caminho relativo ou absoluto
            if not os.path.isabs(args.output) and not args.output.startswith('./'):
                output_file = os.path.join(analyze_dir, args.output)
            else:
                output_file = args.output

        # Executar análises
        analyzer.analyze_devices()
        analyzer.analyze_temporal_patterns()
        analyzer.analyze_signal_strength()
        analyzer.analyze_ssids()

        # Exportar resumo
        analyzer.export_summary(output_file)

        # Gerar gráficos se solicitado
        if args.plots:
            analyzer.generate_plots(analyze_dir)

        print(f"\n=== ANÁLISE CONCLUÍDA ===")
        print(f"Dados processados: {len(analyzer.probe_data)} probe requests")
        print(f"Resumo salvo em: {output_file}")
        if args.plots:
            print(f"Gráficos salvos em: probe_analysis_{analyzer.date_suffix}.png")

    except FileNotFoundError:
        print(f"Erro: Arquivo '{args.log_file}' não encontrado")
    except Exception as e:
        print(f"Erro durante análise: {e}")


if __name__ == "__main__":
    main()