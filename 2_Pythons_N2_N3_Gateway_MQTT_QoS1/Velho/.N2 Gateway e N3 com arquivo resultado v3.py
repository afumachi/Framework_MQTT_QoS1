# CURSO FEE247 Turma 2
# EXP8 com MAC centralizada

# ========================== 1 - Bibliotecas
import serial
import math
import time
import struct
from time import localtime, strftime
import os

# ========================= 2 - Variáveis e arquivos
# Cria os pacotes de DL e UL
PacoteDL =[0]*52
PacoteUL=[0]*52
# Garante que os pacotes de DL e UL estão com valor 0
for i in range(52):
   PacoteDL[i] = 0
   PacoteUL[i] = 0

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

print('Time stamp;Contador;RSSI_DL;PSR;Status LED NodeMCU; Status LED Esp', file=Log_dados)

# ============= INICIALIZAÇÃO
# Abre a porta serial
# Configura a serial
n_serial = input("Digite o número da serial = ")
n_serial1 = int(n_serial) - 1
ser = serial.Serial("COM"+str(n_serial), 115200, timeout=0.5, parity=serial.PARITY_NONE)

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
Comando_LED_amarelo = 0 # comando do LED amarelo que estará no byte34


# ================ Camada de Transporte DL
Contador_pkt_DL = 0 # contador de pacotes DL byte 12

perda_PK_RX = 0 # Variável de medida de perda de pacote

# ================ Camada de Rede DL
ID_sensor = 1  # Endereço do nó sensor vai ser colocado no Byte 8
ID_gateway = 0 # Endereço do gateway vai ser colocado no Byte 10

# ================ Camada MAC DL
Tamanho_pacote = 52
Tempo_entre_pacotes = 2
num_medidas = input('Entre com o número de medidas = ')
Variavel_loop = int(num_medidas)+1

# ================ Envio de pacote de DL
try:
   for j in range(1, Variavel_loop):

# ======== Camada de aplicação PACOTE DL
      PacoteDL[34] = Comando_LED_amarelo

# ======== Camada de trasporte DL
      Contador_pkt_DL = Contador_pkt_DL + 1
      
      PacoteDL[12] = int(Contador_pkt_DL)

# ======== Camada de rede DL
      PacoteDL[8] = ID_sensor
      PacoteDL[10] = ID_gateway

# ======== Camada MAC de DL
      PacoteDL[4] = Tempo_entre_pacotes

# Envia pacote de DL para ESP32 através da serial
      for Bytes_DL in range(Tamanho_pacote):
         ser.write(chr(PacoteDL[Bytes_DL]).encode('latin1'))
           
      time.sleep(Tempo_entre_pacotes) # Intervalo entre o pacote de DL e UL

# =========== Leitura do pacote UL recebido pela USB  vido do ESP32
      Pacote_UL = ser.read(52) # Checa se chegou o pacote UL

      if len(Pacote_UL) == 52: # Verifica se chegaram 52 bytes do pacote de UL

# ======= Camada física UL
         # RSSI Uplink
         RSSI_DL = ((Pacote_UL[0]-256)/2.0)-74 if Pacote_UL[0] > 128 else (Pacote_UL[0]/2.0)-74

         # RSSI Downlink
         RSSI_UL = ((Pacote_UL[2]-256)/2.0)-74 if Pacote_UL[2] > 128 else (Pacote_UL[2]/2.0)-74
         SNR = (Pacote_UL[1]*256 + Pacote_UL[18])
# ======= Camada MAC UL
# Não tem nenhuma função nessa versão. Pode ser colocado nos byte 4, 5, 6 e 7 a medida de energia para estratégia de economia de energia

# ======= Camada de rede NET UL
# Não tem nenhuma função nessa versão. Pode colocar um condicionande para avaliar se o pacote recebido é destinado para esse gateway

# ======= Camada de transporte UL
# Contabilização de pacotes de DL  e UL

# ========Camada de aplicação
         # Luminosidade converte inteiro e resto para o valor medido pelo ADC de 12 bits no Nó Sensor LoRa
         luminosidade = (Pacote_UL[17]*256 + Pacote_UL[18])

         # Arquivo de log com as medidas de cada rodada com time stamp
         print('Pacote = ',j,' | RSSI DL = ',RSSI_DL,'| RSSI UL = ', RSSI_UL,' |Luminosidade = ',luminosidade)
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
   ser.close()

   print('Fim da Execução')

except KeyboardInterrupt:
   ser.close()
   Log_dados.close()

