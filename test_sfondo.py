import tkinter as tk
from PIL import Image, ImageTk
import os
import random

def scegli_sfondo_casuale(cartella):
    immagini = [f for f in os.listdir(cartella) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
    if not immagini:
        raise FileNotFoundError("Nessuna immagine trovata nella cartella degli sfondi.")
    return os.path.join(cartella, random.choice(immagini))

def ridimensiona_sfondo(percorso, dimensione):
    img = Image.open(percorso).convert("RGBA")
    img = img.resize(dimensione, Image.Resampling.LANCZOS)

    # Applica trasparenza al 50%
    alpha = img.getchannel("A")
    alpha = alpha.point(lambda p: int(p * 0.5))
    img.putalpha(alpha)

    return ImageTk.PhotoImage(img)

def main():
    root = tk.Tk()
    root.title("TEST SFONDO")
    larghezza, altezza = 600, 400
    root.geometry(f"{larghezza}x{altezza}")

    sfondo_path = scegli_sfondo_casuale("sfondi")
    sfondo_img = ridimensiona_sfondo(sfondo_path, (larghezza, altezza))

    sfondo_label = tk.Label(root, image=sfondo_img)
    sfondo_label.image = sfondo_img
    sfondo_label.place(x=0, y=0, relwidth=1, relheight=1)

    # Etichetta sopra lo sfondo per test visibilità
    label_test = tk.Label(root, text="Test Sfondo Visibile?", font=("Arial", 20), bg="white")
    label_test.pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    main()
