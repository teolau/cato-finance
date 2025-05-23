import tkinter as tk
from gestione_conti import apri_finestra_gestione_conti
from utils.sfondo import scegli_sfondo_casuale, ridimensiona_sfondo
from gestione_transazioni import mostra_transazioni, aggiungi_transazione_popup
from gestione_investimenti import apri_finestra_investimenti
from storage import carica_conti, carica_transazioni




def mostra_saldi(frame, conti):
    for widget in frame.winfo_children():
        widget.destroy()  # pulisce il frame per aggiornare

    for nome, saldo in conti.items():
        testo = f"{nome}: € {saldo:.2f}"
        label = tk.Label(frame, text=testo, font=("Arial", 14))
        label.pack(anchor="w")

def centra_finestra(finestra, larghezza, altezza):
    finestra.update_idletasks()
    screen_width = finestra.winfo_screenwidth()
    screen_height = finestra.winfo_screenheight()
    x = (screen_width - larghezza) // 2
    y = (screen_height - altezza) // 2
    finestra.geometry(f"{larghezza}x{altezza}+{x}+{y}")

def main():
    root = tk.Tk()
    root.title("Cato Finance :)")

    larghezza = 400
    altezza = 400
    centra_finestra(root, larghezza, altezza)
    root.resizable(False, False)        #todo: quando lo sfondo diventa responsive eliminare questa riga

    conti = carica_conti()
    transazioni = carica_transazioni()

    # Carica sfondo
    root.sfondo_path = scegli_sfondo_casuale("sfondi")
    root.sfondo_img = ridimensiona_sfondo(root.sfondo_path, (larghezza, altezza))

    #label sfondo
    root.sfondo_label = tk.Label(root, image=root.sfondo_img)
    root.sfondo_label.image = root.sfondo_img
    root.sfondo_label.place(x=0, y=0, relwidth=1, relheight=1)
    root.sfondo_label.lower()  # Manda lo sfondo dietro

    # todo: Aggiorna sfondo al resize, per ora con questa funzione lo sfondo scompare all'apertura (problema con "root."?)
#    def aggiorna_sfondo(event):
#        nuovo = ridimensiona_sfondo(root.sfondo_path, (event.width, event.height))
#        root.sfondo_label.configure(image=nuovo)
#        root.sfondo_label.image = nuovo

#    root.bind("<Configure>", aggiorna_sfondo)


    tk.Label(root, text="Cato Finance :)", font=("Arial", 16), bg="white").pack(pady=10)

    frame_conti = tk.Frame(root, bg="white")
    frame_conti.pack(pady=15)

    btn_gestisci_investimenti = tk.Button(root, text="Gestisci Investimenti", bg="lightblue",
                                          command=apri_finestra_investimenti)
    btn_gestisci_investimenti.pack(pady=(0, 10))

    for nome_conto in conti:
        if nome_conto == "Investimenti":
            continue
        tk.Button(frame_conti, text=f"{nome_conto} ({conti[nome_conto]:.2f} €)",
                  command=lambda c=nome_conto: mostra_transazioni([tr for tr in transazioni if tr["conto"] == c],
                                                                  f"Transazioni - {c}")).pack(pady=5)

    btn_tutte = tk.Button(root, text="📜 Visualizza tutte le transazioni",
                          command=lambda: mostra_transazioni(transazioni, "Tutte le transazioni"))
    btn_tutte.pack(pady=5)

    btn_aggiungi = tk.Button(root, text="➕ Aggiungi transazione",
                             command=lambda: aggiungi_transazione_popup(root, conti))
    btn_aggiungi.pack(pady=5)

    tk.Button(root, text="💼 Gestione Conti",
              command=lambda: apri_finestra_gestione_conti(root, lambda: print("TODO aggiorna saldi"))).pack(pady=5)

    root.mainloop()


if __name__ == "__main__":
    main()
