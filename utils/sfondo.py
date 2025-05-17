import os
import random
from PIL import Image, ImageTk

def scegli_sfondo_casuale(cartella_sfondi: str):
    immagini = [f for f in os.listdir(cartella_sfondi) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
    if not immagini:
        raise FileNotFoundError("Nessuna immagine trovata nella cartella sfondi.")
    return os.path.join(cartella_sfondi, random.choice(immagini))


def ridimensiona_sfondo(percorso, dimensione):
    img = Image.open(percorso).convert("RGBA")
    img = img.resize(dimensione, Image.Resampling.LANCZOS)

    # Applica trasparenza al 50%
    alpha = img.getchannel("A")
    alpha = alpha.point(lambda p: int(p * 0.5))
    img.putalpha(alpha)

    return ImageTk.PhotoImage(img)
