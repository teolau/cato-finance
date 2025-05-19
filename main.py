import tkinter as tk
from tkinter import messagebox, ttk
from gestione_conti import carica_conti, aggiungi_conto, rimuovi_conto, modifica_saldo
from utils.sfondo import scegli_sfondo_casuale, ridimensiona_sfondo
from gestione_transazioni import carica_transazioni, aggiungi_transazione
from datetime import datetime
from logica_transazioni import registra_transazione


def apri_popup_modifica_saldo(root, aggiorna_saldi_callback):
    conti = carica_conti()
    popup = tk.Toplevel(root)
    popup.title("Modifica Saldo")

    tk.Label(popup, text="Conto:").grid(row=0, column=0, padx=5, pady=5)
    entry_conto = ttk.Combobox(popup, values=list(conti.keys()))
    entry_conto.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(popup, text="Nuovo saldo:").grid(row=1, column=0, padx=5, pady=5)
    entry_saldo = tk.Entry(popup)
    entry_saldo.grid(row=1, column=1, padx=5, pady=5)

    def conferma():
        nome_conto = entry_conto.get()
        try:
            nuovo_saldo = float(entry_saldo.get())
        except ValueError:
            messagebox.showerror("Errore", "Inserisci un numero valido.")
            return

        try:
            modifica_saldo(nome_conto, nuovo_saldo, aggiungi_transazione)
        except Exception as e:
            messagebox.showerror("Errore", str(e))
            return

        popup.destroy()
        aggiorna_saldi_callback()

    tk.Button(popup, text="Conferma", command=conferma).grid(row=2, column=0, columnspan=2, pady=10)

def apri_finestra_gestione_conti(root=None, aggiorna_saldi_callback=None):
    finestra = tk.Toplevel()
    finestra.title("Gestione Conti")

    etichetta_saldi = tk.Label(finestra, text="")
    etichetta_saldi.pack(pady=10)

    if aggiorna_saldi_callback:
        aggiorna_saldi_callback()

    def aggiorna_saldi():
        conti = carica_conti()
        testo = "Saldi attuali:\n"
        for nome, saldo in conti.items():
            testo += f"{nome}: {saldo:.2f} €\n"
        etichetta_saldi.config(text=testo)

    def aggiungi():
        def conferma():
            nome = entry_nome.get()
            try:
                saldo = float(entry_saldo.get())
                aggiungi_conto(nome, saldo)
                aggiorna_saldi()
                popup.destroy()
            except Exception as e:
                messagebox.showerror("Errore", str(e))

        popup = tk.Toplevel(finestra)
        popup.title("Aggiungi Conto")
        tk.Label(popup, text="Nome:").grid(row=0, column=0)
        entry_nome = tk.Entry(popup)
        entry_nome.grid(row=0, column=1)

        tk.Label(popup, text="Saldo iniziale:").grid(row=1, column=0)
        entry_saldo = tk.Entry(popup)
        entry_saldo.grid(row=1, column=1)

        tk.Button(popup, text="Conferma", command=conferma).grid(row=2, columnspan=2, pady=10)

    def rimuovi():
        def conferma():
            nome = entry_nome.get()
            try:
                rimuovi_conto(nome)
                aggiorna_saldi()
                popup.destroy()
            except Exception as e:
                messagebox.showerror("Errore", str(e))

        popup = tk.Toplevel(finestra)
        popup.title("Rimuovi Conto")
        tk.Label(popup, text="Nome:").grid(row=0, column=0)
        entry_nome = tk.Entry(popup)
        entry_nome.grid(row=0, column=1)

        tk.Button(popup, text="Conferma", command=conferma).grid(row=1, columnspan=2, pady=10)

    frame_pulsanti = tk.Frame(finestra)
    frame_pulsanti.pack()

    tk.Button(frame_pulsanti, text="➕ Aggiungi Conto", command=aggiungi).pack(side=tk.LEFT, padx=5)
    tk.Button(frame_pulsanti, text="🗑️ Rimuovi Conto", command=rimuovi).pack(side=tk.LEFT, padx=5)
    tk.Button(frame_pulsanti, text="💰 Modifica Saldo", command=lambda: apri_popup_modifica_saldo(finestra, aggiorna_saldi)).pack(side=tk.LEFT, padx=5)

    aggiorna_saldi()

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

def mostra_transazioni(cont_transactions, titolo="Transazioni"):
    """Mostra una finestra con una lista delle transazioni passate."""
    finestra = tk.Toplevel()
    finestra.title(titolo)
    finestra.geometry("600x400")

    tree = ttk.Treeview(finestra, columns=("Data", "Conto", "Categoria", "Importo", "Descrizione"), show="headings")
    for col in tree["columns"]:
        tree.heading(col, text=col)
        tree.column(col, width=100)
    tree.pack(fill=tk.BOTH, expand=True)

    for tr in cont_transactions:
        tree.insert("", "end", values=(
            tr["data"], tr["conto"], tr["categoria"], f'{tr["importo"]:.2f}', tr["descrizione"]
        ))

def aggiungi_transazione_popup(root, conti):
    def conferma():
        try:
            conto = conto_var.get()
            tipo = tipo_var.get()
            categoria = categoria_entry.get()
            importo = float(importo_entry.get())
            descrizione = descrizione_entry.get()
            data = data_entry.get()
            datetime.strptime(data, "%Y-%m-%d")  # valida formato data
            if conto not in conti:
                messagebox.showerror("Errore", "Conto non valido.")
                return
            if tipo not in ["Entrata", "Uscita", "Giroconto"]:
                messagebox.showerror("Errore", "Tipo non valido.")
                return
            registra_transazione(importo, conto, categoria, descrizione, data=None)
            messagebox.showinfo("Successo", "Transazione aggiunta.")
            finestra.destroy()
        except Exception as e:
            messagebox.showerror("Errore", f"Errore: {e}")

    finestra = tk.Toplevel(root)
    finestra.title("Aggiungi Transazione")
    finestra.geometry("350x300")

    conto_var = tk.StringVar()
    tipo_var = tk.StringVar(value="Entrata")

    tk.Label(finestra, text="Conto:").pack(anchor="w")
    conto_combo = ttk.Combobox(finestra, textvariable=conto_var, values=list(conti.keys()))
    conto_combo.pack(fill="x")

    tk.Label(finestra, text="Tipo:").pack(anchor="w")
    tipo_combo = ttk.Combobox(finestra, textvariable=tipo_var, values=["Entrata", "Uscita", "Giroconto"])
    tipo_combo.pack(fill="x")

    tk.Label(finestra, text="Categoria:").pack(anchor="w")
    categoria_entry = tk.Entry(finestra)
    categoria_entry.pack(fill="x")

    tk.Label(finestra, text="Importo:").pack(anchor="w")
    importo_entry = tk.Entry(finestra)
    importo_entry.pack(fill="x")

    tk.Label(finestra, text="Descrizione:").pack(anchor="w")
    descrizione_entry = tk.Entry(finestra)
    descrizione_entry.pack(fill="x")

    tk.Label(finestra, text="Data (YYYY-MM-DD):").pack(anchor="w")
    data_entry = tk.Entry(finestra)
    data_entry.insert(0, datetime.today().strftime("%Y-%m-%d"))
    data_entry.pack(fill="x")

    tk.Button(finestra, text="Conferma", command=conferma).pack(pady=10)


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

   # frame_saldi = tk.Frame(root, bg="white")
   # frame_saldi.pack(pady=10)

    frame_conti = tk.Frame(root, bg="white")
    frame_conti.pack(pady=15)

   # mostra_saldi(frame_saldi, conti)

    for nome_conto in conti:
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
