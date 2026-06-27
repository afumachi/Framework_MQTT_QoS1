# Python para o Radiuino over Arduino
import serial
import math
import time
import struct
import socket
from time import localtime, strftime
import os

# Configura a serial
n_serial = input("Digite o número da serial = ")
n_serial1 = int(n_serial) - 1

# ============= Camada física
# Abre a porta serial
ser = serial.Serial("COM"+str(n_serial), 115200, timeout=0.5, parity=serial.PARITY_NONE)

# --- INÍCIO DA ROTINA DE RESET DO ESP32 ---
ser.setDTR(False)
ser.setRTS(False)
time.sleep(0.1)
ser.setDTR(True)
ser.setRTS(True)

time.sleep(1.5)

ser.reset_input_buffer()
ser.reset_output_buffer()

# DEFINIÇÃO DAS INFORMAÇÕES DO PACOTE NO MoT
# Camada de Aplicação: bytes de 16 a 51 - Tópico 2.6

Comando_LED_amarelo = 0 # comando do LED amarelo

# =============== Camada de aplicação
# Arquivos temporários que são apagados a cada início de rodadas de medidas
# Esses arquivos são utilizados para exibir os dados brutos em tempo real
if os.path.exists("medidas_rssi.txt"):
   os.remove("medidas_rssi.txt")
if os.path.exists("medidas_luminosidade.txt"):
   os.remove("medidas_luminosidade.txt")

# Arquivos de armazenamento de logs que devem ser guardados em todas as rodadas de medidas
filename1 = strftime("B_Medidas_%Y_%m_%d_%H-%M-%S.txt")
filename2 = "medidas_rssi.txt"
filename3 = "medidas_luminosidade.txt"

print("Arquivo de log: %s" % filename1)
Log_dados = open(filename1, 'w')

# Cria um arquivo simples com as informações a serem analisadas, como RSSI UL, RSSI DL e luminosidade.
arquivo_resultado = open("RESULTADO.txt", "a", encoding="utf-8")

# Cabeçalho do arquivo RESULTADO.txt
arquivo_resultado.write("Contador;RSSI_DL;RSSI_UL;Luminosidade\n")

print('Time stamp;Contador;RSSI_DL;PSR;Status LED NodeMCU; Status LED Esp', file=Log_dados)

# ================ Camada de Transporte
Contador_pkt_DL_inteiro = 0 # Inteiro do contador de pacote de DL
Contador_pkt_DL_resto = 0   # Resto do contador de pacote de  DL
Contador_pkt_UL_inteiro = 0 # Inteiro do contador de pacote de UL
Contador_pkt_UL_resto = 0   # Resto do contador de pacote de  UL

perda_PK_RX = 0 # Variável de medida de perda de pacote

# ================ Camada de Rede
ID_sensor = 1  # Endereço do nó sensor
ID_gateway = 0 # Endereço do gateway

# ================ Camada MAC
Tempo_entre_pacotes = 2
num_medidas = input('Entre com o número de medidas = ')

# Cria os pacotes de DL e UL
PacoteDL =[0]*52
PacoteUL=[0]*52

for i in range(52):
   PacoteDL[i] = 0
   PacoteUL[i] = 0

PacoteDL[34] = Comando_LED_amarelo

PacoteDL[8] = int(ID_sensor)
PacoteDL[10] = int(ID_gateway)

Variavel_loop = int(num_medidas)+1
perda_PK_RX = 0
PKT_down = 0

try:
   for j in range(1, Variavel_loop):

# Camada de trasporte DL
      PacoteDL[12] = int(Contador_pkt_DL_inteiro)
      PacoteDL[13] = int(Contador_pkt_DL_resto)

# Camada de rede DL
      PacoteDL[8] = ID_sensor
      PacoteDL[10] = ID_gateway

# Camada MAC de DL
      PacoteDL[4] = Tempo_entre_pacotes

# Camada física DL - transmite o pacote DL pela serial do computados para o ESP32
      for Bytes_DL in range(52):
         ser.write(chr(PacoteDL[Bytes_DL]).encode('latin1'))
           
      time.sleep(1) # Intervalo entre o pacote de DL e UL

# Camada física UL - verifica a leitura de pacote UL recebido pela serial
      Pacote_UL = ser.read(52)

      if len(Pacote_UL) == 52: # Verifica se chegaram 52 bytes do pacote de UL

# Camada física UL
         # RSSI Uplink
         RSSI_DL = ((Pacote_UL[0]-256)/2.0)-74 if Pacote_UL[0] > 128 else (Pacote_UL[0]/2.0)-74

         # RSSI Downlink
         RSSI_UL = ((Pacote_UL[2]-256)/2.0)-74 if Pacote_UL[2] > 128 else (Pacote_UL[2]/2.0)-74


# Camada de aplicação
         # Luminosidade converte inteiro e resto para o valor medido pelo ADC de 12 bits no Nó Sensor LoRa
         luminosidade = (Pacote_UL[17]*256 + Pacote_UL[18])

         # Formatação Excel
         RSSId_str = str(RSSI_DL).replace('.', ',')
         RSSIu_str = str(RSSI_UL).replace('.', ',')

         # Formatação Excel
         RSSI_DL_str = str(RSSI_DL).replace('.', ',')
         RSSI_UL_str = str(RSSI_UL).replace('.', ',')

         linha = f"{j};{RSSI_DL_str};{RSSI_UL_str};{luminosidade}"

         print(linha)
         arquivo_resultado.write(linha + "\n")

         # Arquivo de log com as medidas de cada rodada com time stamp
         print(time.asctime(), ';', j, ';', RSSI_DL, ';', RSSI_UL, ';', luminosidade, file=Log_dados)

         with open(filename2, 'a+') as f:
            print(RSSI_DL,RSSI_UL, file=f)

         with open(filename3, 'a+') as f:
            print(luminosidade, file=f)

      else:
         perda_PK_RX += 1
         print('Cont = ', j, ' PERDEU PACOTE ')
         print(time.asctime(), ';', j, ';;', file=Log_dados)

         with open(filename2, 'a+') as f:
            print(j, ';;', perda_PK_RX, file=f)

   print('Pacotes enviados = ', j, ' Pacotes perdidos = ', perda_PK_RX)

   Log_dados.close()
   arquivo_resultado.close()
   ser.close()

   print('Fim da Execução')

except KeyboardInterrupt:
   ser.close()
   Log_dados.close()
   arquivo_resultado.close()
