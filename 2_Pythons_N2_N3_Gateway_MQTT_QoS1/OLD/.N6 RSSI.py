import tkinter as tk
from tkinter import messagebox, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.style as style

# Usa um estilo mais limpo para os gráficos
style.use("ggplot")

# --- CONFIGURAÇÕES DO GRÁFICO ---
MAX_PONTOS = 60  # Tamanho da "Janela Deslizante" (Mostra apenas as últimas 60 leituras)

def atualizar_grafico(ax, canvas, raiz):
    valores_rssi = []
    
    # -------- Lê o arquivo linha por linha de forma blindada --------
    try:
        with open("medidas_rssi.txt", 'r') as dados:
            for linha in dados:
                linha_limpa = linha.strip()
                if linha_limpa:
                    # IGNORA AS LINHAS COM ERRO/PACOTE PERDIDO (Ex: "5 ;; 1")
                    if ";;" in linha_limpa:
                        continue
                    
                    try:
                        # Tenta converter o valor real de RSSI
                        valores_rssi.append(float(linha_limpa))
                    except ValueError:
                        pass # Ignora qualquer outro lixo que cair aqui
    except FileNotFoundError:
        pass # Se o arquivo não existir ainda, segue o jogo

    # [DEBUG] Mostra no terminal o que está acontecendo
    #print(f"[DEBUG] Lendo RSSI... Encontrados {len(valores_rssi)} valores válidos.")

    # -------- Aplica a Janela Deslizante --------
    valores_rssi = valores_rssi[-MAX_PONTOS:]

    ax.clear()

    # -------- Plota as linhas --------
    if len(valores_rssi) > 0:
        # Usando a cor verde e 'marker=o' para o ponto ficar visível imediatamente
        ax.plot(valores_rssi, label='Sinal RSSI (dBm)', color='green', linewidth=2, marker='o', markersize=4)

    # -------- Ajuste Dinâmico de Escala --------
    ax.legend(loc='upper right')
    ax.set_ylabel('Intensidade do Sinal (dBm)')
    ax.set_xlabel(f'Últimas {MAX_PONTOS} Medidas')
    ax.set_title('Monitoramento de Qualidade do Link (RSSI)')

    if len(valores_rssi) > 0:
        val_min = min(valores_rssi)
        val_max = max(valores_rssi)
        
        margem = abs(val_max - val_min) * 0.1
        if margem == 0: 
            margem = 5 
            
        limite_inferior = max(-130, val_min - margem)
        limite_superior = min(0, val_max + margem)
        
        ax.set_ylim(limite_inferior, limite_superior)

    canvas.figure.subplots_adjust(left=0.12, bottom=0.12, right=0.95, top=0.90)
    canvas.draw()
    
    raiz.after(1000, atualizar_grafico, ax, canvas, raiz)

def fechar_aplicacao():
    if messagebox.askokcancel("Sair", "Tem certeza que deseja fechar o monitor de sinal?"):
        raiz.destroy()

def salvar_grafico(figura):
    arquivo = filedialog.asksaveasfilename(
        defaultextension=".png", 
        filetypes=[("Imagens PNG", "*.png"), ("Todos os Arquivos", "*.*")],
        title="Salvar Gráfico de RSSI Como..."
    )
    if arquivo:
        figura.savefig(arquivo)
        print(f"Gráfico salvo em: {arquivo}")

# ==============================================================================
#  INTERFACE GRÁFICA (TKINTER)
# ==============================================================================
raiz = tk.Tk()
raiz.title("MONITOR LORA - SINAL RSSI (ESP32)")
raiz.geometry('1000x600')
raiz.resizable(False, False)

frame_baixo = tk.Frame(master=raiz, borderwidth=1, relief='sunken')
frame_baixo.place(x=10, y=10, width=980, height=580)

fig = Figure(figsize=(9.8, 5), facecolor='white')
eixo = fig.add_subplot(111) 

b_salvar = tk.Button(frame_baixo, text='Salvar Gráfico Atual', command=lambda: salvar_grafico(fig))
b_salvar.place(x=430, y=530)

canvas = FigureCanvasTkAgg(fig, master=frame_baixo)
canvas.get_tk_widget().place(x=0, y=10, width=980, height=500)

atualizar_grafico(eixo, canvas, raiz)
raiz.protocol("WM_DELETE_WINDOW", fechar_aplicacao)
raiz.mainloop()