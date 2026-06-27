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

# Camada de Aplicação
byte34 = 1
byte37 = 0
byte40 = 0

# Camada de Transporte
byte12 = 0
byte13 = 0
byte14 = 0
perda_PK_RX = 0

# Camada de Rede
byte8 = 1
byte10 = 0

# Remove arquivos antigos
if os.path.exists("medidas_rssi.txt"):
   os.remove("medidas_rssi.txt")
if os.path.exists("medidas_luminosidade.txt"):
   os.remove("medidas_luminosidade.txt")

# Cria arquivos
filename1 = strftime("B_Medidas_%Y_%m_%d_%H-%M-%S.txt")
filename2 = "medidas_rssi.txt"
filename3 = "medidas_luminosidade.txt"

print("Arquivo de log: %s" % filename1)
Log_dados = open(filename1, 'w')

# 🔹 NOVO ARQUIVO RESULTADO
arquivo_resultado = open("RESULTADO.txt", "a", encoding="utf-8")

# Cabeçalho opcional
arquivo_resultado.write("Contador;RSSI_DL;RSSI_UL;Luminosidade\n")

print('Time stamp;Contador;RSSI_DL;PSR;Status LED NodeMCU; Status LED Esp', file=Log_dados)

num_medidas = input('Entre com o número de medidas = ')

PacoteTX =[0]*52
PacoteRX=[0]*52

for i in range(52):
   PacoteTX[i] = 0
   PacoteRX[i] = 0

PacoteTX[16] = 16
PacoteTX[17] = 17
PacoteTX[18] = 18
PacoteTX[34] = 1
PacoteTX[37] = 1
PacoteTX[40] = 1

PacoteTX[8] = int(byte8)
PacoteTX[10] = int(byte10)

w = int(num_medidas)+1
perda_PK_RX = 0
PKT_down = 0

try:
   for j in range(1, w):

      PKT_down += 1
      if PKT_down == 256:
         PKT_down = 0

      PacoteTX[12] = int(PKT_down)
      PacoteTX[13] = int(byte13)
      
      PacoteTX[8] = 1
      PacoteTX[10] = 0

      for k in range(52):
         ser.write(chr(PacoteTX[k]).encode('latin1'))
           
      time.sleep(2)

      Pacote_RX = ser.read(52)

      if len(Pacote_RX) == 52:
         # RSSI Uplink
         byte0 = Pacote_RX[0]
         RSSIu = ((byte0-256)/2.0)-74 if byte0 > 128 else (byte0/2.0)-74

         # RSSI Downlink
         byte2 = Pacote_RX[2]
         RSSId = ((byte2-256)/2.0)-74 if byte2 > 128 else (byte2/2.0)-74

         # Luminosidade
         luminosidade = (Pacote_RX[17]*256 + Pacote_RX[18])

         # 🔹 Formatação Excel
         RSSId_str = str(RSSId).replace('.', ',')
         RSSIu_str = str(RSSIu).replace('.', ',')

         linha = f"{j};{RSSId_str};{RSSIu_str};{luminosidade}"

         print(linha)
         arquivo_resultado.write(linha + "\n")

         # Logs existentes
         print(time.asctime(), ';', j, ';', RSSId, ';', luminosidade, file=Log_dados)

         with open(filename2, 'a+') as f:
            print(RSSId, file=f)

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
