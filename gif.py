from PIL import Image
import glob
from tkinter import messagebox
import os


def create_gif(input_pattern="klatka*.png", output_filename="output.gif", duration=200, file_path=None):

    if file_path is None:
        file_path = os.getcwd()  # Pobierz aktualny katalog roboczy (gdzie uruchomiono skrypt)

    if not os.path.exists(file_path):
        try:
            os.makedirs(file_path)
        except Exception as e:
            messagebox.showerror("Błąd tworzenia folderu", f"Nie udało się utworzyć folderu: {e}")
            return

    # Pobranie listy plików pasujących do wzorca z tego samego folderu
    files = sorted(glob.glob(os.path.join(file_path, input_pattern)), key=lambda x: int(x.split('klatka')[1].split('.png')[0]))

    if not files:
        print("Brak pasujących plików do utworzenia GIF-a.")
        return

    frames = [Image.open(file) for file in files]

    output_path = os.path.join(file_path, output_filename)

    # Tworzenie i zapis GIF-a
    try:
        frames[0].save(
            output_path,
            save_all=True,
            append_images=frames[1:],
            duration=duration,
            loop=0  # Powtarzanie GIF-a w nieskończoność
        )
        print(f"GIF zapisany jako {output_path}")
    except Exception as e:
        print(f"Wystąpił błąd podczas tworzenia GIF-a: {e}")

