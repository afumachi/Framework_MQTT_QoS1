import tkinter as tk
from tkinter import messagebox, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.style as style

# Estilo visual
style.use("ggplot")

# Número máximo de pontos na tela
MAX_PONTOS = 100

# ===================== LEITURA DO ARQUIVO =====================
def ler_dados():
    pacotes = []
    rssi_down = []
    rssi_up = []

    try:
        with open("RESULTADO", "r") as f:
            for linha in f:
                linha = linha.strip()
                if not linha:
                    continue

                try:
                    partes = linha.split(";")

                    # Extrai os campos
                    pacote = int(partes[0])
                    down = float(partes[1].replace(",", "."))
                    up = float(partes[2].replace(",", "."))

                    pacotes.append(pacote)
                    rssi_down.append(down)
                    rssi_up.append(up)

                except (ValueError, IndexError):
                    # Ignora linha inválida
                    continue

    except FileNotFoundError:
        pass

    # Janela deslizante
    return (
        pacotes[-MAX_PONTOS:],
        rssi_down[-MAX_PONTOS:],
        rssi_up[-MAX_PONTOS:]
    )

# ===================== ATUALIZAÇÃO DO GRÁFICO =====================
def atualizar(ax, canvas, raiz):
    x, down, up = ler_dados()

    ax.clear()

    if len(x) > 0:
        # Plot Downlink
        ax.plot(
            x, down,
            label="RSSI Downlink (dBm)",
            linewidth=2,
            marker="o",
            markersize=4
        )

        # Plot Uplink
        ax.plot(
            x, up,
            label="RSSI Uplink (dBm)",
            linewidth=2,
            marker="s",
            markersize=4
        )

        # Legenda só se houver dados
        ax.legend(loc="upper right")

    ax.set_title("Monitor LoRa - RSSI Downlink vs Uplink")
    ax.set_xlabel("Número do Pacote")
    ax.set_ylabel("RSSI (dBm)")

    # Ajuste automático de escala
    if len(down) > 0 and len(up) > 0:
        val_min = min(min(down), min(up))
        val_max = max(max(down), max(up))

        margem = abs(val_max - val_min) * 0.1 or 5

        ax.set_ylim(
            max(-130, val_min - margem),
            min(0, val_max + margem)
        )

    canvas.draw()

    # Atualiza a cada 1 segundo
    raiz.after(1000, atualizar, ax, canvas, raiz)

# ===================== SALVAR GRÁFICO =====================
def salvar(fig):
    arquivo = filedialog.asksaveasfilename(
        defaultextension=".png",
        filetypes=[("PNG", "*.png")]
    )
    if arquivo:
        fig.savefig(arquivo)

# ===================== FECHAR =====================
def fechar():
    if messagebox.askokcancel("Sair", "Deseja sair?"):
        root.destroy()

# ===================== INTERFACE =====================
root = tk.Tk()
root.title("Monitor LoRa RSSI")
root.geometry("1000x600")

frame = tk.Frame(root)
frame.pack(fill="both", expand=True)

fig = Figure(figsize=(10, 5))
ax = fig.add_subplot(111)

canvas = FigureCanvasTkAgg(fig, master=frame)
canvas.get_tk_widget().pack(fill="both", expand=True)

btn = tk.Button(root, text="Salvar Gráfico", command=lambda: salvar(fig))
btn.pack(pady=5)

# Inicia atualização
atualizar(ax, canvas, root)

root.protocol("WM_DELETE_WINDOW", fechar)
root.mainloop()
