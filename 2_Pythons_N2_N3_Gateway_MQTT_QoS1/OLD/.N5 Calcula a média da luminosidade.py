import time
import os

arquivo_entrada = "medidas_luminosidade.txt"
arquivo_saida = "media_luminosidade.txt"

while not os.path.exists(arquivo_entrada):
    print("Aguardando criação do arquivo medidas_luminosidade.txt...")
    time.sleep(1)

print("Arquivo encontrado.")

while True:

    try:

        luminosidades = []

        with open(arquivo_entrada, "r") as f:

            for linha in f:

                linha = linha.strip()

                if linha:
                    try:
                        luminosidades.append(float(linha))
                    except ValueError:
                        pass

        if luminosidades:

            soma = 0.0

            with open(arquivo_saida, "w") as arq_media:

                for i, valor in enumerate(luminosidades):

                    soma += valor

                    media = soma / (i + 1)

                    arq_media.write(f"{media:.2f}\n")

            print(
                f"Última luminosidade = {luminosidades[-1]:.2f} | "
                f"Amostras = {len(luminosidades)} | "
                f"Média atual = {media:.2f}"
            )

    except Exception as erro:
        print(f"Erro: {erro}")

    time.sleep(1)
