# CURSO FEE247 Turma 2
# EXP8 com MAC centralizada

# ========================== 1 - Bibliotecas

import serial
import math
import time
import struct
from time import localtime, strftime
import os

Tamanho_pacote = 20

# ========================= 2 - Variáveis e arquivos

# Cria os pacotes de DL e UL
Pacote_DL =[0]*Tamanho_pacote
PacoteUL=[0]*Tamanho_pacote

# Garante que os pacotes de DL e UL estão com valor 0
for i in range(Tamanho_pacote):
   Pacote_DL[i] = 0
   PacoteUL[i] = 0

# Arquivos temporários que são apagados a cada início de rodadas de medidas
# Esses arquivos são utilizados para exibir os dados brutos em tempo real

if os.path.exists("medidas_rssi.txt"):
   os.remove("medidas_rssi.txt")

if os.path.exists("medidas_luminosidade.txt"):
   os.remove("medidas_luminosidade.txt")

# Arquivos de armazenamento de logs que devem ser guardados
# em todas as rodadas de medidas

filename1 = strftime("B_Medidas_%Y_%m_%d_%H-%M-%S.txt")
filename2 = "medidas_rssi.txt"
filename3 = "medidas_luminosidade.txt"

print("Arquivo de log: %s" % filename1)

Log_dados = open(filename1, 'w')

print(
   'Time stamp;Contador;RSSI_DL;PSR;Status LED NodeMCU; Status LED Esp',
   file=Log_dados
)

# ============= INICIALIZAÇÃO

# Abre a porta serial
# Configura a serial

n_serial = input("Digite o número da serial = ")

n_serial1 = int(n_serial) - 1

ser = serial.Serial(
   "COM"+str(n_serial),
   115200,
   timeout=0.5,
   parity=serial.PARITY_NONE
)

# --- INÍCIO DA ROTINA DE RESET DO ESP32 ---

ser.setDTR(False)
ser.setRTS(False)

time.sleep(0.1)

ser.setDTR(True)
ser.setRTS(True)

time.sleep(1.5) # Tempo de estabilização de 1,5 segundos

# Limpa buffers

ser.reset_input_buffer()
ser.reset_output_buffer()

# =============== Camada de aplicação DL

Comando_LED_amarelo = 0  # Inicia apagado

# ================ Camada de Transporte DL

Contador_pkt_DL = 0

perda_PK_RX = 0

# ================ Camada de Rede DL

ID_sensor = 1
ID_gateway = 0

# ================ Camada MAC DL

Tempo_entre_pacotes = 2

num_medidas = input('Entre com o número de medidas = ')

Variavel_loop = int(num_medidas) + 1

# ================ Envio de pacote de DL

try:

   for j in range(1, int(Variavel_loop)):

      # ======== Camada de aplicação PACOTE DL

      # Lê o arquivo cmd_led_amarelo.txt

      try:

         with open("cmd_led_amarelo.txt", "r") as f:

            linha = f.readline()

            # Remove espaços e ENTER
            linha = linha.strip()

            # Se o valor for 0 ou 1
            if linha == "0":
               Comando_LED_amarelo = 0

            elif linha == "1":
               Comando_LED_amarelo = 1

            else:
               # Qualquer outro conteúdo assume 0
               Comando_LED_amarelo = 0

      except:

         # Se houver qualquer erro assume 0
         Comando_LED_amarelo = 0

      # Coloca o comando no byte 16

      Pacote_DL[16] = Comando_LED_amarelo

      # ======== Camada de transporte DL

      Contador_pkt_DL = Contador_pkt_DL + 1
      if Contador_pkt_DL == 256:
         Contador_pkt_DL = 0
      
      Pacote_DL[12] = int(Contador_pkt_DL)

      # ======== Camada de rede DL

      Pacote_DL[8] = ID_sensor
      Pacote_DL[9] = ID_gateway

      # ======== Camada MAC de DL

      Pacote_DL[4] = Tempo_entre_pacotes

      # Envia pacote de DL para ESP32 através da serial

      for Bytes_DL in range(Tamanho_pacote):

         ser.write(chr(Pacote_DL[Bytes_DL]).encode('latin1'))

      time.sleep(Tempo_entre_pacotes)

      # =========== Leitura do pacote UL recebido pela USB vindo do ESP32

      Pacote_UL = ser.read(Tamanho_pacote)

      if len(Pacote_UL) == Tamanho_pacote:

         # ======= Camada física UL

         # RSSI Down link

         RSSI_DL = (
            ((Pacote_UL[0]-256)/2.0)-74
            if Pacote_UL[0] > 128
            else (Pacote_UL[0]/2.0)-74
         )

         # RSSI Up link

         RSSI_UL = (
            ((Pacote_UL[2]-256)/2.0)-74
            if Pacote_UL[2] > 128
            else (Pacote_UL[2]/2.0)-74
         )

         SNR_DL = Pacote_UL[1]
         SNR_UL = Pacote_UL[3]
         # ======== Camada de aplicação

         # Luminosidade

         luminosidade = (Pacote_UL[17]*256 + Pacote_UL[18])

         print(
            'Pacote = ',
            j,
            ' | RSSI DL = ',
            RSSI_DL,
            '| RSSI UL = ',
            RSSI_UL,
            ' | Luminosidade = ',
            luminosidade,
            ' | LED = ',
            Comando_LED_amarelo
         )

         print(
            time.asctime(),
            ';',
            j,
            ';',
            RSSI_DL,
            ';',
            RSSI_UL,
            ';',
            luminosidade,
            ';',
            Comando_LED_amarelo,
            file=Log_dados
         )

         with open(filename2, 'a+') as f:

            print(RSSI_DL, RSSI_UL, file=f)

         with open(filename3, 'a+') as f:

            print(luminosidade, file=f)

      else:

         perda_PK_RX += 1

         print('Cont = ', j, ' PERDEU PACOTE ')

         print(
            time.asctime(),
            ';',
            j,
            ';;',
            file=Log_dados
         )

         with open(filename2, 'a+') as f:

            print(j, ';;', perda_PK_RX, file=f)

   print(
      'Pacotes enviados = ',
      j,
      ' Pacotes perdidos = ',
      perda_PK_RX
   )

   Log_dados.close()

   ser.close()

   print('Fim da Execução')

except KeyboardInterrupt:

   ser.close()

   Log_dados.close()
