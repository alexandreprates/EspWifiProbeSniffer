#!/usr/bin/env python3
"""
Analisador Avançado de Dados do ESP32 WiFi Probe Monitor v2.0
Processa logs JSON Schema e gera análises detalhadas sobre dispositivos e atividade WiFi
Versão atualizada para trabalhar com o novo formato JSON Schema completo
"""

import json
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import seaborn as sns
import re
import os
from dataclasses import dataclass
from typing import Dict, List, Set, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')


class VendorDatabase:
    """Classe para gerenciar a base de dados de fabricantes (vendors) por OUI"""

    def __init__(self, vendors_file_path=None):
        self.vendors = {}  # Dicionário OUI -> vendor info
        self.loaded = False

        if vendors_file_path:
            self.load_vendors(vendors_file_path)

    def load_vendors(self, vendors_file_path):
        """Carrega dados de vendors do arquivo JSON"""
        try:
            print(f"Carregando base de vendors de {vendors_file_path}...")

            with open(vendors_file_path, 'r', encoding='utf-8') as f:
                vendors_data = json.load(f)

            self.vendors = {}

            for vendor_entry in vendors_data:
                if isinstance(vendor_entry, dict) and 'macPrefix' in vendor_entry:
                    mac_prefix = vendor_entry['macPrefix'].upper()
                    # Extrair OUI (primeiros 3 octetos) do macPrefix
                    oui = mac_prefix.replace(':', '').replace('-', '')[:6]

                    self.vendors[oui] = {
                        'vendor_name': vendor_entry.get('vendorName', 'Unknown'),
                        'mac_prefix': mac_prefix,
                        'private': vendor_entry.get('private', False),
                        'block_type': vendor_entry.get('blockType', 'Unknown'),
                        'last_update': vendor_entry.get('lastUpdate', 'Unknown')
                    }

            self.loaded = True
            print(f"Carregados {len(self.vendors)} prefixos de fabricantes")

        except FileNotFoundError:
            print(f"Arquivo de vendors não encontrado: {vendors_file_path}")
            self.loaded = False
        except json.JSONDecodeError as e:
            print(f"Erro ao decodificar JSON do arquivo de vendors: {e}")
            self.loaded = False
        except Exception as e:
            print(f"Erro ao carregar vendors: {e}")
            self.loaded = False

    def get_vendor_by_mac(self, mac_address):
        """Busca fabricante pelo endereço MAC completo"""
        if not self.loaded or not mac_address:
            return None

        # Extrair OUI do MAC address (primeiros 3 octetos)
        oui = self.extract_oui(mac_address)
        return self.get_vendor_by_oui(oui)

    def get_vendor_by_oui(self, oui):
        """Busca fabricante pelo OUI"""
        if not self.loaded or not oui:
            return None

        # Normalizar OUI (remover separadores e converter para maiúsculo)
        oui_clean = oui.replace(':', '').replace('-', '').upper()

        return self.vendors.get(oui_clean)

    def extract_oui(self, mac_address):
        """Extrai OUI (Organization Unique Identifier) do MAC address"""
        if not mac_address:
            return None

        # Remover separadores e pegar primeiros 6 caracteres (3 octetos)
        mac_clean = mac_address.replace(':', '').replace('-', '').upper()

        if len(mac_clean) >= 6:
            return mac_clean[:6]

        return None

    def get_vendor_name(self, mac_address):
        """Retorna apenas o nome do fabricante para um MAC address"""
        vendor_info = self.get_vendor_by_mac(mac_address)
        if vendor_info:
            return vendor_info['vendor_name']
        return 'Unknown'

    def is_randomized_mac(self, mac_address):
        """Verifica se o MAC address é provavelmente randomizado"""
        if not mac_address:
            return False

        # MAC randomizado geralmente tem o bit "locally administered" setado
        # Isso significa que o segundo dígito do primeiro octeto é ímpar
        mac_clean = mac_address.replace(':', '').replace('-', '')

        if len(mac_clean) >= 2:
            first_octet = mac_clean[:2]
            try:
                first_byte = int(first_octet, 16)
                # Bit 1 (second least significant bit) indica locally administered
                return bool(first_byte & 0x02)
            except ValueError:
                return False

        return False

    def get_stats(self):
        """Retorna estatísticas da base de vendors"""
        if not self.loaded:
            return None

        stats = {
            'total_prefixes': len(self.vendors),
            'private_count': sum(1 for v in self.vendors.values() if v.get('private', False)),
            'public_count': sum(1 for v in self.vendors.values() if not v.get('private', False))
        }

        # Contar por tipo de bloco
        block_types = {}
        for vendor in self.vendors.values():
            block_type = vendor.get('block_type', 'Unknown')
            block_types[block_type] = block_types.get(block_type, 0) + 1

        stats['block_types'] = block_types

        return stats


# JSON Schema para validação dos dados
PROBE_DATA_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["capture_id", "capture_ts", "scanner_id", "packet"],
    "properties": {
        "capture_id": {"type": "string"},
        "capture_ts": {"type": "string", "format": "date-time"},
        "scanner_id": {"type": "string"},
        "firmware": {"type": ["string", "null"]},
        "location": {
            "type": ["object", "null"],
            "properties": {
                "lat": {"type": ["number", "null"]},
                "lon": {"type": ["number", "null"]},
                "label": {"type": ["string", "null"]}
            }
        },
        "packet": {
            "type": "object",
            "required": ["pkt_id", "ieee80211", "rssi_dbm", "frame_raw_hex"],
            "properties": {
                "pkt_id": {"type": "string"},
                "radio": {
                    "type": "object",
                    "properties": {
                        "channel": {"type": "integer"},
                        "freq_mhz": {"type": "integer"},
                        "band": {"type": "string"},
                        "bandwidth_mhz": {"type": "integer"}
                    }
                },
                "ieee80211": {"type": "object"},
                "rssi_dbm": {"type": "integer"},
                "frame_raw_hex": {"type": "string"},
                "probe": {"type": "object"},
                "vendor_ies": {"type": "array"}
            }
        }
    }
}


@dataclass
class DeviceInfo:
    """Estrutura para armazenar informações de dispositivos"""
    mac: str
    vendor: str
    randomized: bool
    first_seen: datetime
    last_seen: datetime
    probe_count: int
    channels: Set[int]
    rssi_values: List[int]
    frequencies: Set[int]
    vendor_ies: Set[str]
    fingerprints: Set[str]
    ssids: Set[str]


def validate_probe_data(data):
    """Valida dados de probe request contra o JSON Schema"""
    try:
        # Verificar campos obrigatórios do nível superior
        required_fields = ['capture_id', 'capture_ts', 'scanner_id', 'packet']
        for field in required_fields:
            if field not in data:
                return False, f"Campo obrigatório ausente: {field}"

        # Validar tipos básicos
        if not isinstance(data['capture_id'], str):
            return False, "capture_id deve ser string"
        if not isinstance(data['capture_ts'], str):
            return False, "capture_ts deve ser string"
        if not isinstance(data['scanner_id'], str):
            return False, "scanner_id deve ser string"

        # Validar estrutura do packet
        packet = data['packet']
        if not isinstance(packet, dict):
            return False, "packet deve ser objeto"

        # Verificar campos obrigatórios do packet
        packet_required = ['pkt_id', 'ieee80211', 'rssi_dbm', 'frame_raw_hex']
        for field in packet_required:
            if field not in packet:
                return False, f"Campo obrigatório do packet ausente: {field}"

        # Validar tipos do packet
        if not isinstance(packet['pkt_id'], str):
            return False, "pkt_id deve ser string"
        if not isinstance(packet['ieee80211'], dict):
            return False, "ieee80211 deve ser objeto"
        if not isinstance(packet['rssi_dbm'], int):
            return False, "rssi_dbm deve ser integer"
        if not isinstance(packet['frame_raw_hex'], str):
            return False, "frame_raw_hex deve ser string"

        # Validar timestamp ISO8601
        try:
            datetime.fromisoformat(data['capture_ts'].replace('Z', '+00:00'))
        except ValueError:
            return False, "capture_ts deve estar em formato ISO8601"

        # Validar campos opcionais se presentes
        if 'radio' in packet and packet['radio'] is not None:
            radio = packet['radio']
            if 'channel' in radio and not isinstance(radio['channel'], int):
                return False, "radio.channel deve ser integer"
            if 'freq_mhz' in radio and not isinstance(radio['freq_mhz'], int):
                return False, "radio.freq_mhz deve ser integer"

        if 'vendor_ies' in packet and not isinstance(packet['vendor_ies'], list):
            return False, "vendor_ies deve ser array"

        return True, "Válido"

    except Exception as e:
        return False, f"Erro na validação: {str(e)}"


def validate_ieee80211_required_fields(ieee80211):
    """Valida se os campos essenciais do IEEE 802.11 estão presentes"""
    if not isinstance(ieee80211, dict):
        return False

    # Campos essenciais para análise
    essential_fields = ['sa']  # source address é essencial
    return all(field in ieee80211 for field in essential_fields)


def validate_packet_integrity(packet):
    """Validação adicional de integridade dos dados do packet"""
    try:
        # Validar RSSI em range válido
        rssi = packet.get('rssi_dbm')
        if rssi is not None and (rssi < -120 or rssi > 0):
            return False, f"RSSI fora do range válido: {rssi}"

        # Validar channel em range válido
        if 'radio' in packet and packet['radio'] is not None:
            channel = packet['radio'].get('channel')
            if channel is not None and (channel < 1 or channel > 14):
                return False, f"Canal WiFi inválido: {channel}"

        # Validar MAC address format
        ieee80211 = packet.get('ieee80211', {})
        sa = ieee80211.get('sa')
        if sa is not None:
            # Verificar formato MAC básico
            if not re.match(r'^([0-9a-f]{2}:){5}[0-9a-f]{2}$', sa.lower()):
                return False, f"Formato MAC inválido: {sa}"

        # Validar timestamp ISO8601 se presente no nível superior
        # (isso seria validado no validate_probe_data)

        return True, "Packet válido"

    except Exception as e:
        return False, f"Erro na validação do packet: {str(e)}"


def get_validation_summary(data):
    """Retorna resumo da validação para debugging"""
    summary = {
        'has_capture_id': 'capture_id' in data,
        'has_capture_ts': 'capture_ts' in data,
        'has_scanner_id': 'scanner_id' in data,
        'has_packet': 'packet' in data,
        'packet_fields': []
    }

    if 'packet' in data and isinstance(data['packet'], dict):
        packet = data['packet']
        summary['packet_fields'] = list(packet.keys())

        if 'ieee80211' in packet:
            summary['ieee80211_fields'] = list(packet['ieee80211'].keys())

    return summary


class ProbeAnalyzer:
    def __init__(self, log_file, vendors_file=None):
        self.log_file = log_file
        self.probe_data = []
        self.stats_data = []
        self.date_suffix = self._extract_date_suffix(log_file)
        self.devices = {}  # Dicionário de DeviceInfo por MAC

        # Inicializar base de vendors
        if vendors_file is None:
            # Tentar carregar do local padrão (pasta tools/vendors)
            vendors_file = './tools/vendors/mac-vendors-export.json'

        self.vendor_db = VendorDatabase(vendors_file)

        self.load_data()

    def _extract_date_suffix(self, log_file):
        """Extrai o sufixo de data do nome do arquivo de log"""
        basename = os.path.basename(log_file)
        match = re.search(r'_(\d{8}_\d{6})\.log$', basename)
        if match:
            return match.group(1)
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def load_data(self):
        """Carrega e processa dados do arquivo de log com validação JSON Schema"""
        print(f"Carregando dados de {self.log_file}...")

        valid_count = 0
        invalid_count = 0
        schema_errors = defaultdict(int)

        with open(self.log_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('Warning!') or line.startswith('==='):
                    continue

                try:
                    if line.startswith('# STATS:'):
                        # Linha de estatísticas
                        json_part = line.replace('# STATS: ', '')
                        data = json.loads(json_part)
                        self.stats_data.append(data)
                    elif line.startswith('#') or 'configurado' in line.lower():
                        # Linhas de log do sistema, ignorar
                        continue
                    else:
                        # Dados de probe request no formato JSON Schema
                        data = json.loads(line)

                        # Validar contra JSON Schema
                        is_valid, error_msg = validate_probe_data(data)

                        if is_valid:
                            # Validação adicional dos campos IEEE 802.11
                            packet = data.get('packet', {})
                            ieee80211 = packet.get('ieee80211', {})

                            if validate_ieee80211_required_fields(ieee80211):
                                # Validação adicional de integridade do packet
                                packet_valid, packet_error = \
                                    validate_packet_integrity(packet)

                                if packet_valid:
                                    self.probe_data.append(data)
                                    valid_count += 1
                                else:
                                    invalid_count += 1
                                    error_key = ("packet_integrity: " +
                                                 f"{packet_error}")
                                    schema_errors[error_key] += 1
                            else:
                                invalid_count += 1
                                schema_errors["ieee80211_invalid"] += 1
                        else:
                            invalid_count += 1
                            schema_errors[error_msg] += 1

                except json.JSONDecodeError as e:
                    print(f"Erro JSON na linha {line_num}: {e}")
                    invalid_count += 1
                    schema_errors["json_decode_error"] += 1
                except Exception as e:
                    print(f"Erro inesperado na linha {line_num}: {e}")
                    invalid_count += 1
                    schema_errors["unexpected_error"] += 1

        # Relatório de validação
        total_entries = valid_count + invalid_count

        # Armazenar estatísticas de validação para o relatório Markdown
        self._validation_summary = {
            'total': total_entries,
            'valid': valid_count,
            'invalid': invalid_count,
            'valid_rate': valid_count/total_entries*100 if total_entries > 0 else 0
        }

        if total_entries > 0:
            print(f"Carregados {valid_count} probe requests válidos e "
                  f"{len(self.stats_data)} estatísticas")

            if invalid_count > 0:
                print(f"Descartados {invalid_count} registros inválidos "
                      f"({invalid_count/total_entries*100:.1f}%)")
                print("Principais erros encontrados:")
                sorted_errors = sorted(
                    schema_errors.items(),
                    key=lambda x: x[1], reverse=True)
            for error, count in sorted_errors[:5]:
                print(f"  - {error}: {count} vezes")

            print(f"Taxa de validade: {valid_count/total_entries*100:.1f}%")

            # Criar relatório detalhado de validação se solicitado
            if invalid_count > 0:
                self._generate_validation_report(schema_errors, total_entries)
        else:
            print("Nenhum dado foi processado")

        # Processar dados dos dispositivos
        self._process_devices()

    def _get_output_directories(self, base_dir='./data/analyze'):
        """Retorna os diretórios de saída organizados por timestamp"""
        # Diretório principal para o markdown
        main_dir = base_dir

        # Subdiretório para arquivos específicos (gráficos, CSV, validação)
        timestamp_dir = os.path.join(base_dir, self.date_suffix)

        # Criar diretórios se não existirem
        os.makedirs(main_dir, exist_ok=True)
        os.makedirs(timestamp_dir, exist_ok=True)

        return main_dir, timestamp_dir

    def _generate_validation_report(self, schema_errors, total_entries):
        """Gera relatório detalhado de validação para debugging"""
        try:
            main_dir, timestamp_dir = self._get_output_directories()

            report_file = os.path.join(
                timestamp_dir,
                f'validation_report_{self.date_suffix}.txt')

            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("RELATÓRIO DE VALIDAÇÃO JSON SCHEMA\n")
                f.write("="*50 + "\n\n")
                f.write(f"Arquivo analisado: {self.log_file}\n")
                f.write(f"Data/hora: {datetime.now()}\n\n")

                f.write("ESTATÍSTICAS DE VALIDAÇÃO:\n")
                f.write(f"Total de entradas processadas: {total_entries}\n")
                valid_count = total_entries - sum(schema_errors.values())
                f.write(f"Entradas válidas: {valid_count}\n")
                f.write(f"Entradas inválidas: {sum(schema_errors.values())}\n")
                valid_rate = valid_count/total_entries*100
                f.write(f"Taxa de validade: {valid_rate:.2f}%\n\n")

                f.write("DETALHAMENTO DOS ERROS:\n")
                sorted_errors = sorted(
                    schema_errors.items(),
                    key=lambda x: x[1], reverse=True)
                for error, count in sorted_errors:
                    error_rate = count/total_entries*100
                    f.write(f"- {error}: {count} ocorrências "
                            f"({error_rate:.1f}%)\n")

                f.write("\nRECOMENDAÇÕES:\n")
                f.write("- Verificar logs do ESP32 para erros de saída "
                        "serial\n")
                f.write("- Validar configuração do JSON Schema no firmware\n")
                f.write("- Considerar filtros de limpeza de dados\n")

            print(f"Relatório de validação salvo em: {report_file}")

        except Exception as e:
            print(f"Erro ao gerar relatório de validação: {e}")

    def _process_devices(self):
        """Processa dados de dispositivos a partir dos probe requests"""
        for probe in self.probe_data:
            packet = probe['packet']
            mac = packet['ieee80211']['sa']  # Source address

            # Converter timestamp ISO8601 para datetime
            timestamp = datetime.fromisoformat(
                probe['capture_ts'].replace('Z', '+00:00')
            )

            if mac not in self.devices:
                # Buscar informações do fabricante usando a base de vendors
                vendor_name = self.vendor_db.get_vendor_name(mac)
                is_randomized = self.vendor_db.is_randomized_mac(mac)

                self.devices[mac] = DeviceInfo(
                    mac=mac,
                    vendor=vendor_name,
                    randomized=is_randomized,
                    first_seen=timestamp,
                    last_seen=timestamp,
                    probe_count=1,
                    channels=set(),
                    rssi_values=[],
                    frequencies=set(),
                    vendor_ies=set(),
                    fingerprints=set(),
                    ssids=set()
                )

            device = self.devices[mac]
            device.last_seen = max(device.last_seen, timestamp)
            device.probe_count += 1
            device.channels.add(packet['radio']['channel'])
            device.rssi_values.append(packet['rssi_dbm'])
            device.frequencies.add(packet['radio']['freq_mhz'])

            # Processar vendor IEs
            if 'vendor_ies' in packet:
                for vie in packet['vendor_ies']:
                    if isinstance(vie, dict) and 'oui' in vie:
                        device.vendor_ies.add(vie['oui'])

            # Processar fingerprints
            if 'fingerprint' in packet and 'ie_signature' in packet['fingerprint']:
                sig = packet['fingerprint']['ie_signature']
                if sig:
                    device.fingerprints.add(sig)

            # Processar SSIDs
            if 'probe' in packet and 'ssid' in packet['probe']:
                ssid = packet['probe']['ssid']
                if ssid:
                    device.ssids.add(ssid)

    def analyze_devices(self):
        """Análise avançada de dispositivos detectados"""
        total_devices = len(self.devices)
        randomized_devices = sum(1 for dev in self.devices.values()
                               if dev.randomized)

        # Calcular estatísticas para armazenamento
        vendor_count = Counter(dev.vendor for dev in self.devices.values())
        known_vendors = sum(1 for d in self.devices.values() if d.vendor != 'Unknown')

        # Mostrar apenas resumo no console
        print(f"\n📱 Dispositivos: {total_devices} únicos, {known_vendors} identificados, {randomized_devices} randomizados")

        # Armazenar estatísticas para o markdown
        self._device_stats = {
            'total_devices': total_devices,
            'randomized_devices': randomized_devices,
            'known_vendors': known_vendors,
            'vendor_count': vendor_count,
            'most_active': sorted(self.devices.items(),
                                key=lambda x: x[1].probe_count, reverse=True)[:10]
        }

        return self.devices

    def analyze_advanced_features(self):
        """Análise das funcionalidades avançadas capturadas"""
        # Análise de Information Elements
        ie_counts = Counter()
        vendor_ie_counts = Counter()
        fingerprint_counts = Counter()

        for probe in self.probe_data:
            packet = probe['packet']

            # Contar IEs raw
            if 'ies_raw' in packet:
                for ie in packet['ies_raw']:
                    if isinstance(ie, dict) and 'id' in ie:
                        ie_counts[ie['id']] += 1

            # Contar Vendor IEs
            if 'vendor_ies' in packet:
                for vie in packet['vendor_ies']:
                    if isinstance(vie, dict) and 'oui' in vie:
                        vendor_ie_counts[vie['oui']] += 1

            # Contar fingerprints
            if 'fingerprint' in packet and 'ie_signature' in packet['fingerprint']:
                sig = packet['fingerprint']['ie_signature']
                if sig:
                    fingerprint_counts[sig] += 1

        # Armazenar dados para markdown
        self._advanced_stats = {
            'ie_counts': ie_counts,
            'vendor_ie_counts': vendor_ie_counts,
            'fingerprint_counts': fingerprint_counts
        }

        print(f"🔍 IEs: {len(ie_counts)} tipos, Vendor IEs: {len(vendor_ie_counts)} OUIs, Fingerprints: {len(fingerprint_counts)} únicos")

    def _get_ie_name(self, ie_id):
        """Retorna o nome do Information Element"""
        ie_names = {
            0: "SSID",
            1: "Supported Rates",
            3: "DS Parameter Set",
            45: "HT Capabilities",
            50: "Extended Supported Rates",
            127: "Extended Capabilities",
            191: "VHT Capabilities",
            221: "Vendor Specific",
            255: "Reserved/Extension"
        }
        return ie_names.get(ie_id, "Unknown")

    def analyze_temporal_patterns(self):
        """Análise avançada de padrões temporais"""
        if not self.probe_data:
            print("Sem dados para análise temporal")
            return

        # Criar DataFrame com timestamps convertidos
        df_data = []
        for probe in self.probe_data:
            packet = probe['packet']
            timestamp = datetime.fromisoformat(
                probe['capture_ts'].replace('Z', '+00:00')
            )

            df_data.append({
                'datetime': timestamp,
                'mac': packet['ieee80211']['sa'],
                'channel': packet['radio']['channel'],
                'freq_mhz': packet['radio']['freq_mhz'],
                'rssi_dbm': packet['rssi_dbm'],
                'randomized': packet.get('mac_randomized', False),
                'vendor': packet.get('vendor_inferred', 'Unknown')
            })

        df = pd.DataFrame(df_data)

        # Análise por hora
        df['hour'] = df['datetime'].dt.hour
        hourly_counts = df.groupby('hour').size()
        hourly_unique = df.groupby('hour')['mac'].nunique()

        # Análise por canal
        channel_analysis = df.groupby('channel').agg({
            'mac': 'nunique',
            'rssi_dbm': 'mean',
            'freq_mhz': 'first'
        }).round(1)

        # Armazenar para markdown
        self._temporal_stats = {
            'hourly_counts': hourly_counts,
            'hourly_unique': hourly_unique,
            'channel_analysis': channel_analysis,
            'time_range': (df['datetime'].min(), df['datetime'].max())
        }

        active_hours = len(hourly_counts)
        active_channels = len(channel_analysis)
        print(f"⏰ Temporal: {active_hours} horas ativas, {active_channels} canais utilizados")

        return df

    def analyze_signal_strength(self):
        """Análise avançada de força do sinal (RSSI)"""
        all_rssi = []
        vendor_rssi = defaultdict(list)

        for device in self.devices.values():
            all_rssi.extend(device.rssi_values)
            vendor_rssi[device.vendor].extend(device.rssi_values)

        if not all_rssi:
            print("Sem dados de RSSI")
            return

        avg_rssi = sum(all_rssi) / len(all_rssi)
        min_rssi = min(all_rssi)
        max_rssi = max(all_rssi)

        # Classificação por proximidade
        very_close = sum(1 for rssi in all_rssi if rssi > -50)
        close = sum(1 for rssi in all_rssi if -70 <= rssi <= -50)
        far = sum(1 for rssi in all_rssi if rssi < -70)

        # Armazenar para markdown
        self._signal_stats = {
            'avg_rssi': avg_rssi,
            'min_rssi': min_rssi,
            'max_rssi': max_rssi,
            'proximity': {
                'very_close': very_close,
                'close': close,
                'far': far,
                'total': len(all_rssi)
            },
            'vendor_rssi': dict(vendor_rssi)
        }

        print(f"📶 RSSI: {avg_rssi:.1f} dBm médio ({min_rssi} a {max_rssi} dBm), {very_close} próximos")

    def analyze_ssids(self):
        """Análise avançada de SSIDs"""
        all_ssids = set()
        for device in self.devices.values():
            all_ssids.update(device.ssids)

        # Também extrair SSIDs dos probe requests diretamente
        probe_ssids = []
        for probe in self.probe_data:
            packet = probe['packet']
            if 'probe' in packet and 'ssid' in packet['probe']:
                ssid = packet['probe']['ssid']
                if ssid:
                    probe_ssids.append(ssid)

        if not probe_ssids:
            print("Nenhum SSID encontrado nos dados")
            return

        ssid_counts = Counter(probe_ssids)

        # Armazenar para markdown
        self._ssid_stats = {
            'unique_ssids': len(set(probe_ssids)),
            'ssid_counts': ssid_counts,
            'total_requests': len(probe_ssids)
        }

        print(f"📡 SSIDs: {len(set(probe_ssids))} únicos em {len(probe_ssids)} requisições")

    def generate_plots(self, output_dir='./data/analyze'):
        """Gera gráficos de análise expandidos"""
        if not self.probe_data:
            print("Sem dados para gerar gráficos")
            return

        print("\n=== GERANDO GRÁFICOS ===")

        # Usar subdiretório para gráficos
        main_dir, timestamp_dir = self._get_output_directories(output_dir)

        # Preparar dados para visualização no novo formato JSON
        viz_data = []
        for probe in self.probe_data:
            if 'capture_ts' in probe and 'packet' in probe:
                packet = probe['packet']
                viz_data.append({
                    'datetime': pd.to_datetime(probe['capture_ts']),
                    'mac': packet['ieee80211']['sa'],
                    'rssi': packet['rssi_dbm'],
                    'channel': packet['radio']['channel']
                })

        if not viz_data:
            print("Erro: Sem dados válidos para visualização")
            return

        df = pd.DataFrame(viz_data)

        # Gerar múltiplos gráficos
        self._generate_main_plots(df, timestamp_dir)
        self._generate_detailed_plots(df, timestamp_dir)
        self._generate_analysis_plots(timestamp_dir)

    def _generate_main_plots(self, df, output_dir):
        """Gera os gráficos principais (4 em 1)"""
        plt.style.use('seaborn-v0_8')
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Análise Principal - WiFi Probe Requests', fontsize=16)

        # Gráfico 1: Atividade temporal
        df.set_index('datetime').resample('1T').size().plot(ax=axes[0, 0])
        axes[0, 0].set_title('Atividade por Minuto')
        axes[0, 0].set_ylabel('Probe Requests')
        axes[0, 0].grid(True, alpha=0.3)

        # Gráfico 2: Distribuição RSSI
        axes[0, 1].hist(df['rssi'], bins=30, alpha=0.7,
                       edgecolor='black', color='skyblue')
        axes[0, 1].set_title('Distribuição de RSSI')
        axes[0, 1].set_xlabel('RSSI (dBm)')
        axes[0, 1].set_ylabel('Frequência')
        axes[0, 1].grid(True, alpha=0.3)

        # Gráfico 3: Atividade por canal
        channel_counts = df['channel'].value_counts().sort_index()
        channel_counts.plot(kind='bar', ax=axes[1, 0], color='lightgreen')
        axes[1, 0].set_title('Atividade por Canal WiFi')
        axes[1, 0].set_xlabel('Canal')
        axes[1, 0].set_ylabel('Probe Requests')
        axes[1, 0].grid(True, alpha=0.3)

        # Gráfico 4: Dispositivos únicos por hora
        unique_devices_hourly = df.groupby(
            df['datetime'].dt.hour)['mac'].nunique()
        unique_devices_hourly.plot(kind='line', marker='o', ax=axes[1, 1],
                                  color='orange', linewidth=2)
        axes[1, 1].set_title('Dispositivos Únicos por Hora')
        axes[1, 1].set_xlabel('Hora do Dia')
        axes[1, 1].set_ylabel('Dispositivos Únicos')
        axes[1, 1].grid(True, alpha=0.3)

        plt.tight_layout()
        output_file = os.path.join(
            output_dir, f'probe_analysis_{self.date_suffix}.png')
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

    def _generate_detailed_plots(self, df, output_dir):
        """Gera gráficos detalhados de análise"""
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('Análise Detalhada - WiFi Probe Requests', fontsize=16)

        # Gráfico 1: Heatmap de atividade por hora e canal
        hourly_channel = df.groupby([df['datetime'].dt.hour,
                                   'channel']).size().unstack(fill_value=0)
        if not hourly_channel.empty:
            import seaborn as sns
            sns.heatmap(hourly_channel, ax=axes[0, 0], cmap='YlOrRd',
                       annot=True, fmt='d', cbar_kws={'label': 'Probe Requests'})
            axes[0, 0].set_title('Heatmap: Atividade por Hora e Canal')
            axes[0, 0].set_xlabel('Canal')
            axes[0, 0].set_ylabel('Hora do Dia')

        # Gráfico 2: Top 10 dispositivos mais ativos
        top_devices = df['mac'].value_counts().head(10)
        top_devices.plot(kind='barh', ax=axes[0, 1], color='coral')
        axes[0, 1].set_title('Top 10 Dispositivos Mais Ativos')
        axes[0, 1].set_xlabel('Número de Probe Requests')

        # Gráfico 3: Distribuição de RSSI por canal
        if len(df['channel'].unique()) > 1:
            df.boxplot(column='rssi', by='channel', ax=axes[0, 2])
            axes[0, 2].set_title('Distribuição RSSI por Canal')
            axes[0, 2].set_xlabel('Canal')
            axes[0, 2].set_ylabel('RSSI (dBm)')

        # Gráfico 4: Timeline de atividade
        activity_timeline = df.set_index('datetime').resample('5T').size()
        activity_timeline.plot(ax=axes[1, 0], color='purple', linewidth=2)
        axes[1, 0].set_title('Timeline de Atividade (5 min)')
        axes[1, 0].set_ylabel('Probe Requests')
        axes[1, 0].grid(True, alpha=0.3)

        # Gráfico 5: Scatter RSSI vs Tempo
        scatter_df = df.sample(min(500, len(df)))  # Limitar pontos
        axes[1, 1].scatter(scatter_df['datetime'], scatter_df['rssi'],
                          alpha=0.6, c=scatter_df['channel'],
                          cmap='viridis', s=30)
        axes[1, 1].set_title('RSSI vs Tempo (por Canal)')
        axes[1, 1].set_ylabel('RSSI (dBm)')
        axes[1, 1].grid(True, alpha=0.3)

        # Gráfico 6: Classificação de proximidade
        proximity_ranges = [
            (-float('inf'), -70, 'Distante'),
            (-70, -50, 'Médio'),
            (-50, float('inf'), 'Próximo')
        ]
        proximity_counts = []
        proximity_labels = []

        for min_rssi, max_rssi, label in proximity_ranges:
            if min_rssi == -float('inf'):
                count = len(df[df['rssi'] < max_rssi])
            elif max_rssi == float('inf'):
                count = len(df[df['rssi'] >= min_rssi])
            else:
                count = len(df[(df['rssi'] >= min_rssi) & (df['rssi'] < max_rssi)])
            proximity_counts.append(count)
            proximity_labels.append(f'{label}\n({count})')

        axes[1, 2].pie(proximity_counts, labels=proximity_labels,
                      autopct='%1.1f%%', startangle=90,
                      colors=['lightcoral', 'lightyellow', 'lightgreen'])
        axes[1, 2].set_title('Classificação por Proximidade')

        plt.tight_layout()
        output_file = os.path.join(
            output_dir, f'detailed_analysis_{self.date_suffix}.png')
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

    def _generate_analysis_plots(self, output_dir):
        """Gera gráficos baseados nas análises realizadas"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Análise Avançada - Características WiFi', fontsize=16)

        # Gráfico 1: Information Elements mais comuns
        if hasattr(self, 'ie_stats') and self.ie_stats:
            ie_top = dict(sorted(self.ie_stats.items(),
                               key=lambda x: x[1], reverse=True)[:10])
            ie_names = [f'IE {k}' for k in ie_top.keys()]
            axes[0, 0].bar(range(len(ie_top)), list(ie_top.values()),
                          color='lightblue')
            axes[0, 0].set_title('Top 10 Information Elements')
            axes[0, 0].set_xlabel('IE Type')
            axes[0, 0].set_ylabel('Ocorrências')
            axes[0, 0].set_xticks(range(len(ie_top)))
            axes[0, 0].set_xticklabels(ie_names, rotation=45)

        # Gráfico 2: Vendor IEs
        if hasattr(self, 'vendor_stats') and self.vendor_stats:
            vendor_top = dict(sorted(self.vendor_stats.items(),
                                   key=lambda x: x[1], reverse=True)[:8])
            axes[0, 1].bar(range(len(vendor_top)), list(vendor_top.values()),
                          color='lightcoral')
            axes[0, 1].set_title('Top Vendor IEs (OUI)')
            axes[0, 1].set_xlabel('OUI')
            axes[0, 1].set_ylabel('Ocorrências')
            axes[0, 1].set_xticks(range(len(vendor_top)))
            axes[0, 1].set_xticklabels(list(vendor_top.keys()), rotation=45)

        # Gráfico 3: Atividade por hora (se disponível)
        if hasattr(self, 'hourly_activity') and self.hourly_activity:
            hours = sorted(self.hourly_activity.keys())
            counts = [self.hourly_activity[h]['count'] for h in hours]
            axes[1, 0].plot(hours, counts, marker='o', linewidth=2,
                           color='green', markersize=8)
            axes[1, 0].set_title('Atividade por Hora do Dia')
            axes[1, 0].set_xlabel('Hora')
            axes[1, 0].set_ylabel('Probe Requests')
            axes[1, 0].grid(True, alpha=0.3)

        # Gráfico 4: Estatísticas de randomização
        if hasattr(self, 'devices'):
            randomized = sum(1 for d in self.devices.values() if d.randomized)
            not_randomized = len(self.devices) - randomized

            labels = ['MAC Randomizado', 'MAC Original']
            sizes = [randomized, not_randomized]
            colors = ['lightblue', 'lightpink']

            axes[1, 1].pie(sizes, labels=labels, autopct='%1.1f%%',
                          startangle=90, colors=colors)
            axes[1, 1].set_title('Distribuição de Randomização MAC')

        plt.tight_layout()
        output_file = os.path.join(
            output_dir, f'advanced_analysis_{self.date_suffix}.png')
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"📊 Gráficos salvos: análise principal, detalhada e avançada")

    def export_summary(self, output_file):
        """Exporta resumo em CSV"""
        print("\n=== EXPORTANDO RESUMO ===")

        device_stats = defaultdict(lambda: {
            'first_seen': float('inf'),
            'last_seen': 0,
            'probe_count': 0,
            'avg_rssi': 0,
            'ssids': set()
        })

        for probe in self.probe_data:
            if 'capture_ts' not in probe or 'packet' not in probe:
                continue

            packet = probe['packet']
            mac = packet['ieee80211']['sa']
            timestamp = datetime.fromisoformat(probe['capture_ts']).timestamp()

            stats = device_stats[mac]
            stats['probe_count'] += 1
            stats['first_seen'] = min(stats['first_seen'], timestamp)
            stats['last_seen'] = max(stats['last_seen'], timestamp)

            # Adicionar SSID se disponível
            if 'probe' in packet and 'ssid' in packet['probe']:
                ssid = packet['probe']['ssid']
                if ssid:
                    stats['ssids'].add(ssid)

        # Calcular RSSI médio e duração para cada dispositivo
        for mac, stats in device_stats.items():
            rssi_values = [probe['packet']['rssi_dbm']
                          for probe in self.probe_data
                          if (probe.get('packet', {}).get('ieee80211', {})
                              .get('sa') == mac)]
            if rssi_values:
                stats['avg_rssi'] = sum(rssi_values) / len(rssi_values)

            duration = stats['last_seen'] - stats['first_seen']
            stats['duration'] = duration

        # Converter para lista de dicionários para CSV
        summary_data = []
        for mac, stats in device_stats.items():
            summary_data.append({
                'mac': mac,
                'probe_count': stats['probe_count'],
                'avg_rssi': round(stats['avg_rssi'], 1),
                'duration': round(stats['duration'], 1),
                'first_seen': datetime.fromtimestamp(stats['first_seen']),
                'last_seen': datetime.fromtimestamp(stats['last_seen']),
                'ssids': ','.join(sorted(stats['ssids']))
            })

        # Salvar CSV
        df = pd.DataFrame(summary_data)
        df.to_csv(output_file, index=False)
        print(f"Resumo exportado para '{output_file}'")

    def export_summary(self, output_file):
        """Exporta resumo em CSV"""
        device_stats = defaultdict(lambda: {
            'first_seen': float('inf'),
            'last_seen': 0,
            'probe_count': 0,
            'avg_rssi': 0,
            'vendor': 'Unknown',
            'randomized': False
        })

        for probe in self.probe_data:
            packet = probe['packet']
            mac = packet['ieee80211']['sa']

            # Converter timestamp para timestamp Unix se necessário
            if isinstance(probe['capture_ts'], str):
                timestamp = datetime.fromisoformat(
                    probe['capture_ts'].replace('Z', '+00:00')
                ).timestamp() * 1000
            else:
                timestamp = probe['capture_ts']

            stats = device_stats[mac]
            stats['first_seen'] = min(stats['first_seen'], timestamp)
            stats['last_seen'] = max(stats['last_seen'], timestamp)
            stats['probe_count'] += 1

            if 'vendor_inferred' in packet:
                stats['vendor'] = packet['vendor_inferred']
            if 'mac_randomized' in packet:
                stats['randomized'] = packet['mac_randomized']

        # Calcular RSSI médio
        for mac in device_stats:
            rssi_values = [p['packet']['rssi_dbm']
                          for p in self.probe_data
                          if p['packet']['ieee80211']['sa'] == mac]
            if rssi_values:
                avg_rssi = sum(rssi_values) / len(rssi_values)
                device_stats[mac]['avg_rssi'] = avg_rssi

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
        print(f"💾 CSV exportado: {len(summary_data)} dispositivos")

    def generate_markdown_report(self, output_dir='./data/analyze'):
        """Gera relatório completo em formato Markdown"""
        main_dir, timestamp_dir = self._get_output_directories(output_dir)

        # Salvar markdown no diretório principal
        report_file = os.path.join(
            main_dir, f'analysis_report_{self.date_suffix}.md')

        # Verificar se há gráficos gerados no subdiretório
        plot_files = [
            f'probe_analysis_{self.date_suffix}.png',
            f'detailed_analysis_{self.date_suffix}.png',
            f'advanced_analysis_{self.date_suffix}.png'
        ]

        existing_plots = []
        for plot_file in plot_files:
            plot_path = os.path.join(timestamp_dir, plot_file)
            if os.path.exists(plot_path):
                existing_plots.append(plot_file)

        with open(report_file, 'w', encoding='utf-8') as f:
            # Cabeçalho do relatório
            f.write(f"# Relatório de Análise WiFi Probe Requests\n\n")
            f.write(f"**Data/Hora:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"**Arquivo analisado:** {self.log_file}\n")
            f.write(f"**Total de registros válidos:** {len(self.probe_data)}\n\n")

            # Resumo da validação
            if hasattr(self, '_validation_summary'):
                f.write("## 📊 Resumo da Validação\n\n")
                summary = self._validation_summary
                f.write(f"- **Total processado:** {summary['total']} registros\n")
                f.write(f"- **Válidos:** {summary['valid']} registros\n")
                f.write(f"- **Inválidos:** {summary['invalid']} registros\n")
                f.write(f"- **Taxa de validade:** {summary['valid_rate']:.1f}%\n\n")

            # Análise de dispositivos
            if hasattr(self, 'devices'):
                f.write("## 📱 Análise de Dispositivos\n\n")
                total_devices = len(self.devices)
                randomized = sum(1 for d in self.devices.values() if d.randomized)
                known_vendors = sum(1 for d in self.devices.values() if d.vendor != 'Unknown')

                f.write(f"- **Total de dispositivos únicos:** {total_devices}\n")
                f.write(f"- **Dispositivos com MAC randomizado:** {randomized} ({randomized/total_devices*100:.1f}%)\n")
                f.write(f"- **Fabricantes identificados:** {known_vendors} ({known_vendors/total_devices*100:.1f}%)\n")

                # Informações da base de vendors
                if self.vendor_db.loaded:
                    vendor_stats = self.vendor_db.get_stats()
                    f.write(f"- **Base de vendors carregada:** {vendor_stats['total_prefixes']} prefixos\n")
                    f.write(f"- **Prefixos privados:** {vendor_stats['private_count']}\n")
                    f.write(f"- **Prefixos públicos:** {vendor_stats['public_count']}\n")

                f.write("\n")

                # Top fabricantes
                vendor_count = Counter(dev.vendor for dev in self.devices.values())
                f.write("### 🏭 Top Fabricantes\n\n")
                f.write("| Fabricante | Dispositivos | Percentual |\n")
                f.write("|------------|--------------|------------|\n")

                for vendor, count in vendor_count.most_common(15):
                    percentage = count/total_devices*100
                    f.write(f"| {vendor} | {count} | {percentage:.1f}% |\n")
                f.write("\n")

                # Top dispositivos mais ativos
                f.write("### 🔝 Top 10 Dispositivos Mais Ativos\n\n")
                f.write("| MAC Address | Probes | RSSI Médio | Duração | Vendor | OUI |\n")
                f.write("|-------------|--------|------------|---------|--------|---------|\n")

                sorted_devices = sorted(
                    self.devices.items(),
                    key=lambda x: x[1].probe_count, reverse=True)[:10]

                for mac, device in sorted_devices:
                    duration_delta = device.last_seen - device.first_seen
                    duration_seconds = duration_delta.total_seconds()
                    if device.rssi_values:
                        avg_rssi = sum(device.rssi_values) / len(device.rssi_values)
                    else:
                        avg_rssi = 0
                    oui = self.vendor_db.extract_oui(mac) if self.vendor_db.loaded else "N/A"
                    f.write(f"| `{mac}` | {device.probe_count} | "
                            f"{avg_rssi:.1f} dBm | {duration_seconds:.1f}s | "
                            f"{device.vendor} | {oui} |\n")
                f.write("\n")

            # Análise de características avançadas
            if hasattr(self, 'ie_stats'):
                f.write("## 🔍 Características Avançadas\n\n")

                # Information Elements
                f.write("### Information Elements Mais Comuns\n\n")
                f.write("| IE | Tipo | Ocorrências |\n")
                f.write("|----|------|-------------|\n")

                sorted_ies = sorted(
                    self.ie_stats.items(),
                    key=lambda x: x[1], reverse=True)[:10]

                for ie_type, count in sorted_ies:
                    ie_name = self.get_ie_name(ie_type)
                    f.write(f"| {ie_type} | {ie_name} | {count} |\n")
                f.write("\n")

                # Vendor IEs
                if hasattr(self, 'vendor_stats'):
                    f.write("### Vendor IEs Mais Comuns\n\n")
                    f.write("| OUI | Ocorrências |\n")
                    f.write("|-----|-------------|\n")

                    sorted_vendors = sorted(
                        self.vendor_stats.items(),
                        key=lambda x: x[1], reverse=True)[:10]

                    for oui, count in sorted_vendors:
                        f.write(f"| {oui} | {count} |\n")
                    f.write("\n")

            # Análise temporal
            if hasattr(self, 'hourly_activity'):
                f.write("## ⏰ Análise Temporal\n\n")
                f.write("### Atividade por Hora\n\n")
                f.write("| Hora | Probes | Dispositivos Únicos |\n")
                f.write("|------|--------|--------------------|\n")

                for hour, data in sorted(self.hourly_activity.items()):
                    f.write(f"| {hour:02d}:00 | {data['count']} | {data['unique_devices']} |\n")
                f.write("\n")

            # Análise de canais
            if hasattr(self, 'channel_stats'):
                f.write("### Análise por Canal WiFi\n\n")
                f.write("| Canal | Frequência | Dispositivos | RSSI Médio |\n")
                f.write("|-------|------------|--------------|------------|\n")

                for channel, data in sorted(self.channel_stats.items()):
                    freq = 2412 + (channel - 1) * 5
                    f.write(f"| {channel} | {freq} MHz | {data['devices']} | {data['rssi_dbm']:.1f} dBm |\n")
                f.write("\n")

            # Análise de sinal
            if hasattr(self, 'rssi_stats'):
                f.write("## 📶 Análise de Sinal\n\n")
                stats = self.rssi_stats
                f.write(f"- **RSSI médio:** {stats['avg']:.1f} dBm\n")
                f.write(f"- **RSSI mínimo:** {stats['min']} dBm\n")
                f.write(f"- **RSSI máximo:** {stats['max']} dBm\n\n")

                # Classificação por proximidade
                if hasattr(self, 'proximity_stats'):
                    f.write("### Classificação por Proximidade\n\n")
                    prox = self.proximity_stats
                    total = sum(prox.values())
                    f.write("| Categoria | Quantidade | Percentual |\n")
                    f.write("|-----------|------------|------------|\n")
                    f.write(f"| Muito próximo (>-50 dBm) | {prox.get('very_close', 0)} | {prox.get('very_close', 0)/total*100:.1f}% |\n")
                    f.write(f"| Proximidade média (-70 a -50 dBm) | {prox.get('medium', 0)} | {prox.get('medium', 0)/total*100:.1f}% |\n")
                    f.write(f"| Distante (<-70 dBm) | {prox.get('far', 0)} | {prox.get('far', 0)/total*100:.1f}% |\n")
                    f.write("\n")

            # Análise de SSIDs
            if hasattr(self, 'ssid_stats'):
                f.write("## 📡 Análise de SSIDs\n\n")
                f.write(f"**Total de SSIDs únicos:** {len(self.ssid_stats)}\n\n")

                if self.ssid_stats:
                    f.write("### Top SSIDs Mais Procurados\n\n")
                    f.write("| SSID | Ocorrências |\n")
                    f.write("|------|-------------|\n")

                    sorted_ssids = sorted(
                        self.ssid_stats.items(),
                        key=lambda x: x[1], reverse=True)[:20]

                    for ssid, count in sorted_ssids:
                        ssid_display = f"'{ssid}'" if ssid else "(vazio)"
                        f.write(f"| {ssid_display} | {count} |\n")
                    f.write("\n")

            # Incluir gráficos se existirem
            if existing_plots:
                f.write("## 📈 Visualizações\n\n")

                for i, plot_file in enumerate(existing_plots):
                    # Referenciar arquivos no subdiretório
                    plot_path = f"{self.date_suffix}/{plot_file}"

                    if 'probe_analysis' in plot_file:
                        f.write("### Análise Principal\n")
                        f.write("Visão geral da atividade, distribuição RSSI, canais e dispositivos únicos.\n\n")
                        f.write(f"![Análise Principal]({plot_path})\n\n")
                    elif 'detailed_analysis' in plot_file:
                        f.write("### Análise Detalhada\n")
                        f.write("Heatmaps, top dispositivos, distribuições por canal e timeline de atividade.\n\n")
                        f.write(f"![Análise Detalhada]({plot_path})\n\n")
                    elif 'advanced_analysis' in plot_file:
                        f.write("### Análise Avançada\n")
                        f.write("Information Elements, Vendor IEs, atividade horária e randomização MAC.\n\n")
                        f.write(f"![Análise Avançada]({plot_path})\n\n")

            # Rodapé
            f.write("---\n")
            f.write(f"*Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}*\n")

        print(f"Relatório Markdown salvo em: {report_file}")
        return report_file

def main():
    """Função principal do analisador"""
    parser = argparse.ArgumentParser(
        description='Analisador de Probe Requests WiFi (JSON Schema)')
    parser.add_argument('log_file',
                        help='Arquivo de log com dados de probe requests')
    parser.add_argument('--output', '-o', default=None,
                        help='Arquivo de saída CSV (opcional)')
    parser.add_argument('--plots', '-p', action='store_true',
                        help='Gerar gráficos de análise')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Modo verboso')
    parser.add_argument('--vendors', default=None,
                        help='Arquivo JSON com dados de fabricantes (vendors)')

    args = parser.parse_args()

    try:
        analyzer = ProbeAnalyzer(args.log_file, args.vendors)

        if not analyzer.probe_data:
            print("Erro: Nenhum dado válido encontrado no arquivo de log")
            return 1

        # Definir diretório de saída para análises
        analyze_dir = './data/analyze'
        os.makedirs(analyze_dir, exist_ok=True)

        # Executar análises completas
        analyzer.analyze_devices()
        if hasattr(analyzer, 'analyze_advanced_features'):
            analyzer.analyze_advanced_features()
        analyzer.analyze_temporal_patterns()
        analyzer.analyze_signal_strength()
        analyzer.analyze_ssids()

        # Gerar visualizações automaticamente
        if hasattr(analyzer, 'generate_visualizations'):
            analyzer.generate_visualizations()
        else:
            analyzer.generate_plots(analyze_dir)

        # Exportar resumo detalhado em CSV
        if hasattr(analyzer, 'export_summary'):
            if hasattr(analyzer.export_summary, '__code__') and \
               analyzer.export_summary.__code__.co_argcount == 1:
                analyzer.export_summary()
            else:
                # Usar subdiretório para o arquivo CSV
                main_dir, timestamp_dir = analyzer._get_output_directories(analyze_dir)
                output_file = os.path.join(
                    timestamp_dir, f'summary_{analyzer.date_suffix}.csv')
                analyzer.export_summary(output_file)

        # Gerar relatório em Markdown
        markdown_file = analyzer.generate_markdown_report(analyze_dir)

        print("\n=== ANÁLISE CONCLUÍDA ===")
        print(f"Dados processados: {len(analyzer.probe_data)} "
              f"probe requests")
        if hasattr(analyzer, 'devices'):
            print(f"Dispositivos únicos: {len(analyzer.devices)}")
        if analyzer.vendor_db.loaded:
            vendor_stats = analyzer.vendor_db.get_stats()
            if vendor_stats:
                print(f"Base de vendors: {vendor_stats['total_prefixes']} prefixos")
        print(f"Relatório Markdown: {markdown_file}")
        print(f"Outros arquivos salvos em: {analyze_dir}")

    except FileNotFoundError:
        print(f"Erro: Arquivo '{args.log_file}' não encontrado")
        return 1
    except Exception as e:
        print(f"Erro durante análise: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
