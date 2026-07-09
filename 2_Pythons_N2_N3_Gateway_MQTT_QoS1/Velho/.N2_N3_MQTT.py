# CURSO FEE247 Turma 3
# EXP11 com MAC centralizada
# Versão MQTT - Comunicação via broker HiveMQ (broker.hivemq.com:1883)
# Troca a camada USB/Serial por Wi-Fi MQTT entre Python e ESP32 Gateway
# ======================================================================
#
#
# 
#
# 
# ======================================================================

# ========================== 1 - Bibliotecas
import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion
import math
import time
import struct
from time import localtime, strftime
import os
import threading

# ========================= 2 - Configurações MQTT
BROKER        = "broker.hivemq.com"
PORTA_MQTT    = 1883
TOPIC_DL      = "mot_lora/gateway/downlink"   # Python publica → ESP32 assina
TOPIC_UL      = "mot_lora/gateway/uplink"     # ESP32 publica  → Python assina

# ========================= 3 - Variáveis globais
Tamanho_pacote = 20

# Evento para sinalizar chegada de pacote UL
evento_UL = threading.Event()
PacoteUL_recebido = bytearray(Tamanho_pacote)

# ========================= 4 - Callbacks MQTT
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("[MQTT] Conectado ao broker HiveMQ com sucesso.")
        client.subscribe(TOPIC_UL)
        print(f"[MQTT] Inscrito no tópico: {TOPIC_UL}")
    else:
        print(f"[MQTT] Falha na conexão. Código: {reason_code}")

def on_message(client, userdata, msg):
    """Callback disparado ao receber pacote UL vindo do ESP32."""
    global PacoteUL_recebido
    payload = msg.payload
    if len(payload) >= Tamanho_pacote:
        PacoteUL_recebido = bytearray(payload[:Tamanho_pacote])
        evento_UL.set()   # Sinaliza que chegou um pacote válido

def on_disconnect(client, userdata, flags, reason_code, properties):
    if reason_code != 0:
        print(f"[MQTT] Desconectado inesperadamente (rc={reason_code}). Tentando reconectar...")

# ========================= 5 - Inicialização do cliente MQTT
client = mqtt.Client(CallbackAPIVersion.VERSION2)
client.on_connect    = on_connect
client.on_message    = on_message
client.on_disconnect = on_disconnect

print("[MQTT] Conectando ao broker.hivemq.com porta 1883...")
client.connect(BROKER, PORTA_MQTT, keepalive=60)
client.loop_start()   # Thread de fundo para receber mensagens

# Aguarda conexão ser estabelecida
time.sleep(2)

# ========================= 6 - Arquivos de saída
Grava_log = 0

filename2 = "medidas_rssi.txt"
filename3 = "medidas_luminosidade.txt"

# ========================= 7 - Parâmetros de rede / camadas
ID_sensor      = 1
ID_gateway     = 0
Tempo_entre_pacotes = 2   # segundos (colocado no byte 4 do DL)
ESPERA_UL_s    = 5        # segundos de espera pelo pacote UL após envio do DL

# ========================= 8 - Loop principal: repete pedindo número de medidas
print("\n========== Gateway LoRa - Comunicação MQTT ==========")
try:
    while True:

        # ----- Entrada do usuário -----
        num_medidas = input("\nEntre com o número de medidas (0 para sair): ").strip()
        if num_medidas == "0":
            print("Encerrando...")
            break
        try:
            Variavel_loop = int(num_medidas)
        except ValueError:
            print("Valor inválido. Tente novamente.")
            continue

        # ----- Limpa arquivos temporários a cada rodada -----
        for arq in [filename2, filename3]:
            if os.path.exists(arq):
                os.remove(arq)


        # ----- Grava arquivos temporários a cada rodada -----        
        if Grava_log == 1:
            filename1 = strftime("B_Medidas_%Y_%m_%d_%H-%M-%S.txt")
            Log_dados = open(filename1, 'w')
            print(f"Arquivo de log: {filename1}")
            print('Time stamp;Contador;RSSI_DL;RSSI_UL;Luminosidade;LED', file=Log_dados)

        Contador_pkt_DL = 0
        perda_PK_RX     = 0
        Comando_LED_amarelo = 0

        # ----- Montagem e envio dos pacotes -----
        for j in range(1, Variavel_loop + 1):

            # -------- Camada de Aplicação DL: lê comando LED --------
            try:
                with open("cmd_led_amarelo.txt", "r") as f:
                    linha = f.readline().strip()
                    Comando_LED_amarelo = 1 if linha == "1" else 0
            except Exception:
                Comando_LED_amarelo = 0

            # -------- Monta pacote DL de 20 bytes --------
            Pacote_DL = bytearray(Tamanho_pacote)

            # Camada MAC
            Pacote_DL[4]  = Tempo_entre_pacotes
            # Camada de Rede
            Pacote_DL[8]  = ID_sensor
            Pacote_DL[9]  = ID_gateway
            # Camada de Transporte
            Contador_pkt_DL = (Contador_pkt_DL + 1) % 256
            Pacote_DL[12] = Contador_pkt_DL
            # Camada de Aplicação
            Pacote_DL[16] = Comando_LED_amarelo

            # -------- Publica pacote DL no broker MQTT --------
            evento_UL.clear()
            result = client.publish(TOPIC_DL, bytes(Pacote_DL))
            result.wait_for_publish()
            print(f"[TX] Pacote {j:03d} publicado no broker | LED={Comando_LED_amarelo}")

            # -------- Aguarda pacote UL (timeout = ESPERA_UL_s) --------
            chegou = evento_UL.wait(timeout=ESPERA_UL_s)

            if chegou:
                Pacote_UL = PacoteUL_recebido

                # -------- Decodifica RSSI DL (byte 0) --------
                raw_rssi_dl = Pacote_UL[0]
                RSSI_DL = ((raw_rssi_dl - 256) / 2.0) - 74 if raw_rssi_dl > 128 else (raw_rssi_dl / 2.0) - 74

                # -------- Decodifica SNR DL (byte 1) --------
                SNR_DL = Pacote_UL[1]

                # -------- Decodifica RSSI UL (byte 2) --------
                raw_rssi_ul = Pacote_UL[2]
                RSSI_UL = ((raw_rssi_ul - 256) / 2.0) - 74 if raw_rssi_ul > 128 else (raw_rssi_ul / 2.0) - 74

                # -------- Decodifica SNR UL (byte 3) --------
                SNR_UL = Pacote_UL[3]

                # -------- Camada de Aplicação: Luminosidade (bytes 18-19) --------
                luminosidade = Pacote_UL[18] * 256 + Pacote_UL[19]

                print(f"[RX] Pacote {j:03d} | RSSI_DL={RSSI_DL:.1f} dBm | RSSI_UL={RSSI_UL:.1f} dBm | Lum={luminosidade} | LED={Comando_LED_amarelo}")

                # Salva dados em arquivo
                with open(filename2, 'a+') as f:
                    print(RSSI_DL, RSSI_UL, file=f)
                with open(filename3, 'a+') as f:
                    print(luminosidade, file=f)

                if Grava_log == 1:
                    print(f"{time.asctime()};{j};{RSSI_DL};{RSSI_UL};{luminosidade};{Comando_LED_amarelo}", file=Log_dados)
            else:
                perda_PK_RX += 1
                print(f"[RX] Pacote {j:03d} | TIMEOUT - pacote UL não recebido")
                with open(filename2, 'a+') as f:
                    print(f"{j};;{perda_PK_RX}", file=f)

                if Grava_log == 1:
                    print(f"{time.asctime()};{j};;", file=Log_dados)

            # Aguarda intervalo entre pacotes antes do próximo envio
            time.sleep(Tempo_entre_pacotes)

        # ----- Resumo da rodada -----
        print(f"\n--- Rodada concluída: {Variavel_loop} enviados | {perda_PK_RX} perdidos ---")

        if Grava_log == 1:
            Log_dados.close()

except KeyboardInterrupt:
    print("\n[INFO] Interrompido pelo usuário.")
finally:
    client.loop_stop()
    client.disconnect()
    print("[MQTT] Desconectado do broker.")
