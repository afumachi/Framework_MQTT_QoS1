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
    valores_luminosidade = []

    # -------- Lê os arquivos linha por linha de forma blindada --------
    try:
        # Procurando o arquivo com o nome CORRETO (sem espaços)
        with open("medidas_luminosidade.txt", 'r') as dados:
            for linha in dados:
                linha_limpa = linha.strip()
                if linha_limpa: 
                    try:
                        valores_luminosidade.append(float(linha_limpa))
                    except ValueError:
                        pass 
    except FileNotFoundError:
        pass 

    # [DEBUG] Mostra no terminal preto do Python o que está acontecendo
    #print(f"[DEBUG] Lendo arquivo... Encontrados {len(valores_luminosidade)} valores.")

    # -------- Aplica a Janela Deslizante --------
    valores_luminosidade = valores_luminosidade[-MAX_PONTOS:]

    ax.clear()

    # -------- Plota as linhas --------
    if len(valores_luminosidade) > 0:
        ax.plot(valores_luminosidade, label='LUMINOSIDADE', color='blue', linewidth=2, marker='o', markersize=4)

    # -------- Ajuste Dinâmico de Escala --------
    ax.legend(loc='upper right')
    ax.set_ylabel('Intensidade (0 - 4095)')
    ax.set_xlabel(f'Últimas {MAX_PONTOS} Medidas')
    ax.set_title('Monitoramento de Luminosidade em Tempo Real')

    if len(valores_luminosidade) > 0:
        val_min = min(valores_luminosidade)
        val_max = max(valores_luminosidade)
        margem = (val_max - val_min) * 0.1
        if margem == 0: margem = 100 
        ax.set_ylim(max(0, val_min - margem), min(4095, val_max + margem))

    canvas.figure.subplots_adjust(left=0.12, bottom=0.12, right=0.95, top=0.90)
    canvas.draw()
    raiz.after(1000, atualizar_grafico, ax, canvas, raiz)

def fechar_aplicacao():
    if messagebox.askokcancel("Sair", "Tem certeza que deseja fechar o monitor?"):
        raiz.destroy()

def salvar_grafico(figura):
    arquivo = filedialog.asksaveasfilename(
        defaultextension=".png", 
        filetypes=[("Imagens PNG", "*.png"), ("Todos os Arquivos", "*.*")],
        title="Salvar Gráfico Como..."
    )
    if arquivo:
        figura.savefig(arquivo)
        print(f"Gráfico salvo em: {arquivo}")

# ==============================================================================
#  INTERFACE GRÁFICA (TKINTER)
# ==============================================================================
raiz = tk.Tk()
raiz.title("MONITOR LORA - LUMINOSIDADE (ESP32)")
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