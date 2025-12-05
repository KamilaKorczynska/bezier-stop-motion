import os
import matplotlib.pyplot as plt
from tkinter import messagebox
from bezier_curve import bezier_curve

def export_frames(frames, canvas_width, canvas_height, file_path):
    if len(frames) == 0:
        messagebox.showerror("Błąd eksportu", "Brak klatek do eksportu.")
        return

    for frame_index, curves in enumerate(frames):
        # Tworzymy nową figurę dla każdej klatki
        plt.figure(figsize=(canvas_width / 100, canvas_height / 100), dpi=100)
        plt.xlim(0, canvas_width)
        plt.ylim(0, canvas_height)
        plt.gca().set_aspect('equal', adjustable='box')

        if len(curves) > 0:
            # Iterujemy przez krzywe w klatce i rysujemy je
            for curve in curves:
                if len(curve["points"]) > 1:
                    omega = [1.0] * len(curve["points"])
                    curve_points = bezier_curve(curve["points"], omega=omega)
                    plt.plot(curve_points[:, 0], curve_points[:, 1], curve["color"], lw=curve["thickness"])
        # Jeśli klatka jest pusta, zostawiamy ją pustą na rysunku


        plt.axis('off')

        file_name = f"klatka{frame_index}.png"
        file_full_path = os.path.join(file_path, file_name)

        plt.savefig(file_full_path, bbox_inches='tight', pad_inches=0, dpi=300)

        plt.close()

    messagebox.showinfo("Eksport ukończony", "Wszystkie klatki zostały wyeksportowane.")
