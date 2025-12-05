import numpy as np
import matplotlib.pyplot as plt
import screeninfo
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox, Listbox, Canvas, Frame
from tkinter.colorchooser import askcolor
from django.utils.termcolors import background
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image
import sys
import copy
import pickle
import os

from bezier_curve import bezier_curve
from export import export_frames
from export_index import export_index_frames
from gif import create_gif
from save_project import save_project_to_file, load_project_from_file


########################################################################################################################
background = None
if_show_b = False

def on_click(event, curves, active_curve, ax, canvas, x, y, active_mode, move_point_data, curve_list, move_curve_data):
    if event.xdata is not None and event.ydata is not None:
        if active_mode.get() == "dodaj punkt kontrolny":

            # Dodaj punkt kontrolny do aktywnej krzywej
            if len(curves[active_curve[0]]['points']) == 0:
                # Jeśli to pierwszy punkt w nowej krzywej, dodaj ją do widocznej listy
                curve_list.insert(tk.END, f"Krzywa {active_curve[0]}")
                curve_list.selection_clear(0, tk.END)  # Usuń wcześniejsze zaznaczenie
                curve_list.selection_set(active_curve[0])  # Zaznacz nową krzywą
                curve_list.activate(active_curve[0])

            # Dodaj punkt do aktualnej krzywej
            update_curve_list(curve_list, curves, active_curve)
            curves[active_curve[0]]['points'].append((event.xdata, event.ydata))

        elif active_mode.get() == "usuń punkt kontrolny":
            # Sprawdź, czy kliknięto na któryś punkt kontrolny
            min_dist = 10
            best_point = -1
            for i, point in enumerate(curves[active_curve[0]]['points']):
                dist = np.sqrt((event.xdata - point[0]) ** 2 + (event.ydata - point[1]) ** 2)
                if dist < 5 and min_dist > dist:
                    best_point = i

            # Usuń punkt kontrolny, jeśli znaleziono
            if best_point > -1:
                del curves[active_curve[0]]['points'][best_point]

        elif active_mode.get() == "przesuń punkt kontrolny":
            # Sprawdź, czy kliknięto na któryś punkt kontrolny
            min_dist = 10
            best_point = -1
            for i, point in enumerate(curves[active_curve[0]]['points']):
                dist = np.sqrt((event.xdata - point[0]) ** 2 + (event.ydata - point[1]) ** 2)
                if dist < 5 and min_dist > dist:
                    best_point = i
            if best_point > -1:
                move_point_data['dragging'] = True
                move_point_data['selected_point'] = best_point

        elif active_mode.get() == "przesuń krzywą":
            # Rozpoczęcie przesuwania krzywej
            move_curve_data['dragging'] = True
            move_curve_data['start_x'] = event.xdata
            move_curve_data['start_y'] = event.ydata
            move_curve_data['start_points'] = list(curves[active_curve[0]]['points'])

        update_canvas(ax, canvas, curves, active_curve, x, y)


def interpolate(x1, y1, x2, y2, alpha):
    x_interp = x1 + alpha * (x2 - x1)
    y_interp = y1 + alpha * (y2 - y1)
    return x_interp, y_interp

def on_motion(event, curves, active_curve, ax, canvas, x, y, active_mode, move_point_data, move_curve_data):
    if event.xdata is not None and event.ydata is not None:
        if active_mode.get() == "przesuń punkt kontrolny" and move_point_data.get('dragging', False):
            # Przesuwaj wybrany punkt
            i = move_point_data['selected_point']
            curves[active_curve[0]]['points'][i] = (event.xdata, event.ydata)


        elif active_mode.get() == "przesuń krzywą" and move_curve_data.get('dragging', False):

            # Oblicz przesunięcie myszy
            dx = event.xdata - move_curve_data['start_x']
            dy = event.ydata - move_curve_data['start_y']

            # Interpolacja przesunięcia krzywej
            for i, point in enumerate(curves[active_curve[0]]['points']):
                x_old, y_old = point
                x_new = x_old + dx
                y_new = y_old + dy

                # Interpolacja pomiędzy starą a nową pozycją punktu
                x_interp, y_interp = interpolate(x_old, y_old, x_new, y_new, alpha=0.1)

                # Zaktualizuj punkt
                curves[active_curve[0]]['points'][i] = (x_interp, y_interp)

        update_canvas(ax, canvas, curves, active_curve, x, y)

def on_release(active_mode, move_point_data, move_curve_data):
    if active_mode.get() == "przesuń punkt kontrolny":
        move_point_data['dragging'] = False

    elif active_mode.get() == "przesuń krzywą":
        move_curve_data['dragging'] = False


previous_frame = None
background_color = "#FFFFFF"
def update_canvas(ax, canvas, curves, active_curve, x, y):
    ax.cla()

    # Ustawienie koloru tła
    ax.set_facecolor(background_color)

    # Rysowanie grafiki w tle, jeśli
    if background is not None and if_show_b:
        ax.imshow(background, extent=(0, x, 0, y), alpha=0.5)  # Dodanie przezroczystości

    # Rysowanie poprzedniej klatki
    if previous_frame is not None:
        ax.imshow(previous_frame, extent=(0, x, 0, y), alpha=0.25)  # Dodanie przezroczystości

    # Rysowanie krzywych
    for curve_index, curve in enumerate(curves):
        if len(curve["points"]) > 0:
            if len(curve["points"]) > 1:
                omega = [1.0] * len(curve["points"])
                curve_points = bezier_curve(curve["points"], omega=omega)
                ax.plot(curve_points[:, 0], curve_points[:, 1], curve["color"], lw=curve["thickness"])

            # Gdy ta klatka aktywna
            if curve_index == active_curve[0]:

                # Rysowanie linii przerywanej między punktami kontrolnymi
                control_points = np.array(curve["points"])
                for i in range(len(control_points)):
                    start_point = control_points[i]
                    end_point = control_points[(i + 1) % len(control_points)]  # Łączenie ostatniego z pierwszym
                    ax.plot(
                        [start_point[0], end_point[0]],
                        [start_point[1], end_point[1]],
                        'r--',
                        alpha=0.25
                    )

                # Rysowanie punktów kontrolnych
                control_points = np.array(curve["points"])
                ax.plot(control_points[:, 0], control_points[:, 1], 'ro')


    ax.set_xlim(0, x)
    ax.set_ylim(0, y)
    ax.set_aspect('equal', adjustable='box')
    canvas.draw()


def update_curve_list(curve_list, curves, active_curve):
    curve_list.delete(0, tk.END)  # Wyczyść listę
    for i, curve in enumerate(curves):
        curve_list.insert(tk.END, f"Krzywa {i}")

    if active_curve[0] < len(curves):  # Zaznacz aktywną krzywą, jeśli istnieje
        curve_list.selection_clear(0, tk.END)
        curve_list.selection_set(active_curve[0])
        curve_list.activate(active_curve[0])



# drugie okno #######################################################################################################################

# Inicjalizacja
color = "#000000"
thickness = 1

frames = [[]]  # Lista klatek, każda klatka to lista krzywych
active_frame = 0

curves = [{"points": [], "color": color, "thickness": thickness}]   # Lista krzywych, każda krzywa to zbiór punktów z 'cechami'
active_curve = [0]
active_curve[0] = 0
move_point_data = {}
move_curve_data = {}

canvas_width = None
canvas_height = None
is_new = True

def setup_main_interface(project_path):
    global frames, canvas_width, canvas_height, is_new

    frames, canvas_width, canvas_height, is_new = load_project_from_file(project_path)

    # Ustawienie głównego okna
    main_window = ctk.CTk()
    main_window.title("Edytor Animacji Poklatkowej")

    screens = screeninfo.get_monitors()
    window_width = screens[0].width
    window_height = screens[0].height
    main_window.geometry(f"{window_width}x{window_height}+{0}+{0}")

    # Funkcja obsługująca zamknięcie okna
    def on_closing():
        if messagebox.askokcancel("Zamknij", "Czy na pewno chcesz zamknąć aplikację?"):
            main_window.quit()  # Kończy pętlę mainloop
            main_window.destroy()  # Zamyka okno
            sys.exit()

    main_window.protocol("WM_DELETE_WINDOW", on_closing)

    # Menu frame    #####################################################################
    menu_frame = ctk.CTkFrame(main_window)
    menu_frame.pack(side="top", fill="x")

    # Przyciski menu
    ctk.CTkButton(menu_frame, text="Nowy projekt", command=new_project, fg_color="gray20").pack(side="left", padx=5)
    ctk.CTkButton(
        menu_frame,
        text="Zapisz",
        fg_color="gray20",
        command=lambda: save_project_to_file(project_path, frames, canvas_width, canvas_height, is_new)
    ).pack(side="left", padx=5)

    # Tool frame    ####################################################################
    tool_frame = ctk.CTkFrame(main_window)
    tool_frame.pack(pady=5, side="top",  fill="x")

    # Wczytanie obrazów strzałek przy użyciu PIL
    undo_image_pil = Image.open("left.png")  # Ścieżka do obrazu "undo"
    redo_image_pil = Image.open("right.png")  # Ścieżka do obrazu "redo"

    # Utworzenie CTkImage z obrazów PIL
    undo_image = ctk.CTkImage(light_image=undo_image_pil, dark_image=undo_image_pil, size=(24, 24))
    redo_image = ctk.CTkImage(light_image=redo_image_pil, dark_image=redo_image_pil, size=(24, 24))

    # Przyciski "Undo" i "Redo" z grafikami
    undo_button = ctk.CTkButton(tool_frame, image=undo_image, text="", command=lambda: print("Cofnij"), fg_color="gray20", width=30, height=30)
    undo_button.pack(side="left", padx=5)

    redo_button = ctk.CTkButton(tool_frame, image=redo_image, text="", command=lambda: print("Ponów"), fg_color="gray20", width=30, height=30)
    redo_button.pack(side="left", padx=5)

    # Kwadraciki na kolory
    color_preview_frame = ctk.CTkFrame(tool_frame, width=50, height=50)
    color_preview_frame.pack(side="left", padx=5)

    # Kwadrat dla koloru tła
    background_color_frame = ctk.CTkFrame(color_preview_frame, width=20, height=20, fg_color="white")
    background_color_frame.place(relx=0.4, rely=0.5)

    # Kwadrat dla koloru rysowania
    draw_color_frame = ctk.CTkFrame(color_preview_frame, width=20, height=20, fg_color="black")
    draw_color_frame.place(relx=0.2, rely=0.3)

    # Funkcja do zmiany kolorów
    def change_draw_color(event):
        color_code = askcolor(title="Wybierz kolor rysowania")[1]
        if color_code:
            draw_color_frame.configure(fg_color=color_code)
            curves[active_curve[0]]["color"] = color_code
            update_canvas(ax, canvas, curves, active_curve, canvas_width, canvas_height)  # Zaktualizowanie widoku

    def change_background_color(event):
        color_code = askcolor(title="Wybierz kolor tła")[1]
        if color_code:
            background_color_frame.configure(fg_color=color_code)
            global background_color
            background_color = color_code
            update_canvas(ax, canvas, curves, active_curve, canvas_width, canvas_height)

    # Powiązanie kliknięcia z kwadratami
    draw_color_frame.bind("<Button-1>", change_draw_color)
    background_color_frame.bind("<Button-1>", change_background_color)

    # Gróbość
    ctk.CTkLabel(tool_frame, text="Grubość pędzla:").pack(side="left", padx=5)

    # Pole do ręcznego wpisania grubości
    brush_size_entry = ctk.CTkEntry(tool_frame, width=50)
    brush_size_entry.pack(side="left", padx=5)

    # Suwak do zmiany grubości pędzla
    brush_size_slider = ctk.CTkSlider(tool_frame, from_=1, to=20, number_of_steps=19)
    brush_size_slider.pack(side="left", padx=5)


    # Funkcja synchronizująca wartość w suwaku i polu tekstowym
    def update_brush_size_from_slider(val):
        brush_size_entry.delete(0, ctk.END)
        brush_size_entry.insert(0, str(int(val)))
        curves[active_curve[0]]['thickness'] = val
        global thickness
        thickness = val
        update_canvas(ax, canvas, curves, active_curve, canvas_width, canvas_height)

    def update_brush_size_from_entry(event):
            value = int(brush_size_entry.get())
            if 1 <= value <= 20:
                brush_size_slider.set(value)
            else:
                brush_size_entry.delete(0, ctk.END)
                if 20 <= value:
                    value = 20
                else:
                    value = 1
                brush_size_slider.set(value)
                brush_size_entry.insert(0, str(value))

            curves[active_curve[0]]['thickness'] = value
            global thickness
            thickness = value
            update_canvas(ax, canvas, curves, active_curve, canvas_width, canvas_height)

    brush_size_slider.configure(command=update_brush_size_from_slider)
    brush_size_entry.bind("<Return>", update_brush_size_from_entry)

    # Edycja krzywej frame  ##############################################################
    options_frame = ctk.CTkFrame(tool_frame, height=40, width=520)
    options_frame.pack(side="left", padx=5, pady=5, fill="both")
    options_frame.pack_propagate(False)

    ctk.CTkLabel(options_frame, text="Edycja krzywej:").pack(side="left", padx=10)

    active_mode = ctk.StringVar(value="")

    def set_mode(mode):
        # Jeśli aktualnie kliknięty tryb jest już aktywny, odkliknij go
        if active_mode.get() == mode:
            active_mode.set("")  # Ustaw pustą wartość (nic nie zaznaczone)
        else:
            active_mode.set(mode)

    # Przycisk "Dodaj punkt kontrolny"
    add_point_button = ctk.CTkButton(
        options_frame,
        text="Dodaj punkt",
        fg_color="gray20",
        command=lambda: set_mode("dodaj punkt kontrolny"),
        width=50
    )
    add_point_button.pack(side="left", padx=5)

    # Przycisk "Usuń punkt kontrolny"
    remove_point_button = ctk.CTkButton(
        options_frame,
        text="Usuń punkt",
        fg_color="gray20",
        command=lambda: set_mode("usuń punkt kontrolny"),
        width=50
    )
    remove_point_button.pack(side="left", padx=5)

    # Przycisk "Przesuń punkt kontrolny"
    move_point_button = ctk.CTkButton(
        options_frame,
        text="Przesuń punkt",
        fg_color="gray20",
        command=lambda: set_mode("przesuń punkt kontrolny"),
        width=50
    )
    move_point_button.pack(side="left", padx=5)

    # Przycisk "Przesuń krzywą"
    move_curve_button = ctk.CTkButton(
        options_frame,
        text="Przesuń krzywą",
        fg_color="gray20",
        command=lambda: set_mode("przesuń krzywą"),
        width=50
    )
    move_curve_button.pack(side="left", padx=5)

    # Aktualizacja wizualna aktywnego trybu
    def update_button_states(*args):
        buttons = {
            "dodaj punkt kontrolny": add_point_button,
            "usuń punkt kontrolny": remove_point_button,
            "przesuń punkt kontrolny": move_point_button,
            "przesuń krzywą": move_curve_button,
        }

        for mode, button in buttons.items():
            if active_mode.get() == mode:
                button.configure(fg_color="#1f6aa5")  # Kolor aktywnego trybu
            else:
                button.configure(fg_color="gray20")  # Kolor nieaktywnego przycisku

    active_mode.trace_add("write", update_button_states)

    # Dodanie przycisku "Eksportuj klatki"
    export_button = ctk.CTkButton(
        menu_frame,
        text="Eksportuj klatki",
        command=lambda: export_frames(frames, canvas_width, canvas_height, project_path),
        fg_color="gray20"
    )
    export_button.pack(side="left", padx=5)

    # Dodanie przycisku "Eksportuj jako gif"
    export_button = ctk.CTkButton(
        menu_frame,
        text="Eksportuj jako gif",
        command=lambda: (export_frames(frames, canvas_width, canvas_height, project_path),
                         create_gif(input_pattern="klatka*.png", output_filename="animacja.gif", duration=200,
                                    file_path=project_path)),
        fg_color="gray20"
    )
    export_button.pack(side="left", padx=5)

    # Panel klatek animacji     ########################################################
    frame_panel = ctk.CTkFrame(main_window)
    frame_panel.pack(side="left", fill="y")

    ctk.CTkLabel(frame_panel, text="Klatki animacji").pack(padx=window_width // 40, pady=10)

    make_frame = ctk.CTkFrame(frame_panel)
    make_frame.pack(pady=5, side="top", fill="x")

    # Panel krzywych        #############################################################
    curve_panel = ctk.CTkFrame(main_window)
    curve_panel.pack(side="right", fill="y")

    ctk.CTkLabel(curve_panel, text="Krzywe").pack(padx=window_width // 80, pady=10)

    options_curve = ctk.CTkFrame(curve_panel)
    options_curve.pack(pady=5, side="top",  fill="x")

    def new_curve():
        curve_index = len(curves)

        if curve_index == 0:
            curves.append({"points": [], "color": color, "thickness": thickness})
            active_curve[0] = curve_index
            update_curve_list(curve_list, curves, active_curve)
            update_canvas(ax, canvas, curves, active_curve, canvas_width, canvas_height)

        elif len(curves[curve_index - 1]["points"]) > 0:
            curves.append({"points": [], "color": color, "thickness": thickness})
            active_curve[0] = curve_index
            update_curve_list(curve_list, curves, active_curve)
            update_canvas(ax, canvas, curves, active_curve, canvas_width, canvas_height)

    def select_curve(event):
        selection = curve_list.curselection()
        if selection:
            active_curve[0] = selection[0]
            update_canvas(ax, canvas, curves, active_curve, canvas_width, canvas_height)


    # Przycisk "Nowa krzywa"
    new_curve_button = ctk.CTkButton(
        options_curve,
        text="Nowa krzywa",
        fg_color="gray20",
        command=new_curve,
        width=50
    )
    new_curve_button.pack(side="left", pady=5)

    def delete_curve():
        selection = curve_list.curselection()  # Pobierz indeks zaznaczonej krzywej
        if selection:  # Jeśli jest zaznaczenie
            curve_index = selection[0]
            del curves[curve_index]  # Usuń krzywą z listy danych

            # Zaktualizuj aktywną krzywą
            if len(curves) > 0:
                active_curve[0] = max(0, curve_index - 1)  # Ustaw poprzednią krzywą jako aktywną
            else:
                active_curve[0] = 0  # Jeśli nie ma krzywych, resetuj aktywną

            update_curve_list(curve_list, curves, active_curve)  # Aktualizuj widoczną listę krzywych
            update_canvas(ax, canvas, curves, active_curve, canvas_width, canvas_height)  # Aktualizuj rysunek

    # Przycisk "Usuń krzywą"
    new_curve_button = ctk.CTkButton(
        options_curve,
        text="Usuń krzywą",
        fg_color="gray20",
        command=delete_curve,
        width=50
    )
    new_curve_button.pack(side="right", pady=5)

    # Lista krzywych
    curve_list = Listbox(curve_panel)
    curve_list.pack(expand=True, fill="both", padx=5, pady=5)
    curve_list.configure(background="gray20", fg="white", font=("Arial", 22))  # Kolor tekstu na biały, większa czcionka i wyższe elementy

    # Powiązanie listy z funkcją obsługi kliknięcia
    curve_list.bind("<<ListboxSelect>>", select_curve)

    # Obszar roboczy płótna     #######################################################################
    bezier_frame = ctk.CTkFrame(main_window, height=300)
    bezier_frame.pack(fill="both", expand=True, padx=10, pady=10)

    fig, ax = plt.subplots()
    ax.set_xlim(0, canvas_width)
    ax.set_ylim(0, canvas_height)
    ax.set_aspect('equal', adjustable='box')

    canvas = FigureCanvasTkAgg(fig, master=bezier_frame)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(fill="both", expand=True)

    # Tworzenie przewijalnego panelu klatek     ###########################################################
    frame_canvas = Canvas(frame_panel, bg="gray10", highlightthickness=0)
    frame_scrollbar = ctk.CTkScrollbar(frame_panel, command=frame_canvas.yview, width=15,
                                       button_color="gray20")  # Ciemniejszy scrollbar
    frame_scrollable = Frame(frame_canvas, bg="gray10")  # Kontener na przyciski

    frame_scrollable_id = frame_canvas.create_window((0, 0), window=frame_scrollable, anchor="nw")
    frame_canvas.configure(yscrollcommand=frame_scrollbar.set)

    frame_canvas.pack(side="left", fill="both", expand=True)
    frame_scrollbar.pack(side="right", fill="y")

    def update_scrollable_area():
        frame_scrollable.update_idletasks()
        frame_canvas.config(scrollregion=frame_canvas.bbox("all"))

    def configure_scrollable(event):
        if frame_scrollable.winfo_reqwidth() != frame_canvas.winfo_width():
            frame_canvas.itemconfigure(frame_scrollable_id, width=frame_canvas.winfo_width())

    frame_scrollable.bind("<Configure>", configure_scrollable)

    frame_buttons = []  # Przechowuje przyciski dla każdej klatki

    update_scrollable_area()

    def create_new_frame():
        save_current_frame()

        frame_index = len(frames)
        new_frame_curves = copy.deepcopy(frames[-1])
        frames.append(new_frame_curves)

        # Tworzenie przycisku dla nowej klatki
        frame_button = ctk.CTkButton(
            frame_scrollable,
            text=f"Klatka {frame_index}",
            command=lambda idx=frame_index: activate_frame(idx),
            fg_color="gray20",
            width=100
        )
        frame_button.pack(pady=5)

        frame_buttons.append(frame_button)

        update_frame_buttons()

        activate_frame(frame_index)

        update_scrollable_area()

    def update_frame_buttons():
        for i, button in enumerate(frame_buttons):
            button.configure(text=f"Klatka {i}")

            button.configure(command=lambda idx=i: activate_frame(idx))

    def activate_frame(frame_index):
        global active_frame, active_curve
        active_frame = frame_index  # Ustaw aktywną klatkę

        # Przełączenie zbioru krzywych na krzywe przypisane do wybranej klatki
        curves.clear()
        curves.extend(frames[frame_index])
        if not curves:
            curves.append({"points": [], "color": color, "thickness": thickness})

        if active_frame != 0:
            frames_path = os.path.join(project_path, "klatki")
            frame_path = os.path.join(frames_path, f"klatka{active_frame - 1}.png")
            export_index_frames(frames, canvas_width, canvas_height, frames_path, active_frame - 1)

            frame_image = Image.open(frame_path)

            global previous_frame
            previous_frame = frame_image

        active_curve[0] = 0
        update_curve_list(curve_list, curves, active_curve)
        update_canvas(ax, canvas, curves, active_curve, canvas_width, canvas_height)

        # Aktualizacja wyglądu przycisków klatek
        for i, button in enumerate(frame_buttons):
            if i == frame_index:
                button.configure(fg_color="#1f6aa5")  # Kolor aktywnej klatki
            else:
                button.configure(fg_color="gray20")


    # Przycisk "Nowa klatka" w panelu klatek
    new_frame_button = ctk.CTkButton(
        make_frame,
        text="Nowa klatka",
        command=create_new_frame,
        fg_color="gray20"
    )
    new_frame_button.pack(side="left", pady=5)

    def remove_frame():
        global active_frame

        if len(frames) > 1:  # Nie pozwól na usunięcie ostatniej klatki
            # Usuń bieżącą klatkę z listy
            del frames[active_frame]

            # Usuń przycisk odpowiadający tej klatce
            frame_buttons[active_frame].destroy()
            del frame_buttons[active_frame]

            # Automatycznie przełącz na poprzednią lub następną klatkę
            if active_frame >= len(frames):
                active_frame = len(frames) - 1

            # Napraw numery i funkcje związane z klatkami
            for i, button in enumerate(frame_buttons):
                button.configure(text=f"Klatka {i + 1}")
                button.configure(command=lambda index=i: activate_frame(index))

            update_frame_buttons()

            activate_frame(active_frame)

            update_scrollable_area()

        else:
            print("Nie można usunąć ostatniej klatki!")

    # Przycisk "Usuń klatka" w panelu klatek
    remove_frame_button = ctk.CTkButton(
        make_frame,
        text="Usuń klatkę",
        command=remove_frame,
        fg_color="gray20"
    )
    remove_frame_button.pack(side="right", pady=5)


    # Tworzenie listy klatek i ustawienie aktywnej
    frame_buttons.clear()
    for i in range(len(frames)):
        frame_button = ctk.CTkButton(
            frame_scrollable,
            text=f"Klatka {i}",
            command=lambda idx=i: activate_frame(idx),
            fg_color="gray20",
            width=100
        )
        frame_button.pack(pady=5)
        frame_buttons.append(frame_button)

    activate_frame(0)
    update_scrollable_area()

    def save_current_frame():
        frames[active_frame] = [curve.copy() for curve in curves]

    fig.canvas.mpl_connect(
        'button_press_event',
        lambda event: (on_click(event, curves, active_curve, ax, canvas, canvas_width, canvas_height, active_mode,
                               move_point_data, curve_list, move_curve_data), save_current_frame())
    )

    fig.canvas.mpl_connect(
        'motion_notify_event',
        lambda event: (on_motion(event, curves, active_curve, ax, canvas, canvas_width, canvas_height, active_mode,
                                move_point_data, move_curve_data), save_current_frame())
    )

    fig.canvas.mpl_connect(
        'button_release_event',
        lambda event: (on_release(active_mode, move_point_data, move_curve_data), save_current_frame())
    )




    # Panel dla opcji tła i grafiki ##########################################################
    image_panel = ctk.CTkFrame(tool_frame)
    image_panel.pack(side="left", padx=10)

    background_image = None
    show_background = tk.BooleanVar(value=False)

    def load_background_image():
        global background
        file_path = filedialog.askopenfilename(
            title="Wybierz plik graficzny",
            filetypes=[("Pliki graficzne", "*.png *.jpg *.jpeg *.bmp *.gif"), ("Wszystkie pliki", "*.*")]
        )
        if file_path:
            try:
                # Wczytaj obraz przy użyciu PIL i zapisz jako globalne tło
                img = Image.open(file_path)
                background = np.array(img)
                show_background.set(True)
                global if_show_b
                if_show_b = show_background.get()
                update_canvas(ax, canvas, curves, active_curve, canvas_width, canvas_height)

                messagebox.showinfo("Sukces", "Obraz został pomyślnie załadowany jako tło.")
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie udało się wczytać obrazu: {e}")

    load_image_button = ctk.CTkButton(
        image_panel,
        text="Wgraj grafikę",
        command=load_background_image
    )

    load_image_button.pack(side="left", padx=5)

    def toggle_background_visibility():
        global if_show_b
        if_show_b = show_background.get()
        update_canvas(ax, canvas, curves, active_curve, canvas_width, canvas_height)

    show_image_check = ctk.CTkCheckBox(
        image_panel,
        text="Pokaż grafikę w tle",
        variable=show_background,
        command=toggle_background_visibility
    )
    show_image_check.pack(side="left", padx=5)


    main_window.mainloop()

# pierwsze okno #######################################################################################################################
def new_project():
    def create_project():
        project_name = entry_project_name.get()
        save_location = entry_save_location.get()
        canvas_width = entry_canvas_width.get()
        canvas_height = entry_canvas_height.get()

        if not project_name or not save_location or not canvas_width or not canvas_height:
            messagebox.showerror("Błąd", "Wszystkie pola muszą być wypełnione!")
            return

        try:
            canvas_width = int(canvas_width)
            canvas_height = int(canvas_height)

            if canvas_width <= 0 or canvas_height <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Błąd", "Rozmiar płótna musi być liczbą większą od 0!")
            return

        try:
            # Tworzenie katalogu projektu
            project_path = os.path.join(save_location, project_name)
            if not os.path.exists(project_path):
                os.makedirs(project_path)

            # Tworzenie folderu "klatki"
            frames_path = os.path.join(project_path, "klatki")
            if not os.path.exists(frames_path):
                os.makedirs(frames_path)

            # Tworzenie pliku projektu (pickle)
            project_file = os.path.join(project_path, "project_data.pkl")
            project_data = {
                "canvas_width": canvas_width,
                "canvas_height": canvas_height,
                "is_new": True,
                "frames": [[]],
            }
            with open(project_file, "wb") as file:
                pickle.dump(project_data, file)

        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się zapisać pliku projektu: {e}")
            return

        project_window.quit()
        project_window.destroy()
        setup_main_interface(project_path)

    # Funkcja otwierania istniejącego projektu
    def open_existing_project():
        project_path = filedialog.askdirectory(title="Wybierz folder projektu")
        if not project_path:
            return
        project_file = os.path.join(project_path, "project_data.pkl")
        if not os.path.exists(project_file):
            messagebox.showerror("Błąd", "Nie znaleziono pliku projektu.")
            return

        project_window.quit()
        project_window.destroy()
        setup_main_interface(project_path)

    # Initializing project window
    project_window = ctk.CTk()
    project_window.title("Stwórz nowy projekt")

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")

    project_window.geometry(f"650x350")

    #Frame
    frame = ctk.CTkFrame(master=project_window)
    frame.pack(pady=20, padx=20, fill="both", expand=True)

    # Project name
    frame_project_name = ctk.CTkFrame(master=frame)
    frame_project_name.pack(pady=10)
    label_project_name = ctk.CTkLabel(master=frame_project_name, text="Nazwa projektu", font=("Roboto", 14))
    label_project_name.pack(side="left", padx=10)
    entry_project_name = ctk.CTkEntry(master=frame_project_name, width=300)
    entry_project_name.pack(side="left", padx=10)

    # Save location
    frame_save_location = ctk.CTkFrame(master=frame)
    frame_save_location.pack(pady=10)
    label_save_location = ctk.CTkLabel(master=frame_save_location, text="Lokalizacja zapisu", font=("Roboto", 14))
    label_save_location.pack(side="left", padx=10)
    entry_save_location = ctk.CTkEntry(master=frame_save_location, width=220)
    entry_save_location.pack(side="left", padx=10)

    def select_save_location():
        path = filedialog.askdirectory()
        if path:
            entry_save_location.delete(0, ctk.END)
            entry_save_location.insert(0, path)

    button_select_location = ctk.CTkButton(master=frame_save_location, text="Wybierz...", command=select_save_location,
                                           fg_color="gray20")
    button_select_location.pack(side="left", padx=10)

    # Canvas size
    frame_canvas_size = ctk.CTkFrame(master=frame)
    frame_canvas_size.pack(pady=10)
    label_canvas_size = ctk.CTkLabel(master=frame_canvas_size, text="Rozmiar", font=("Roboto", 14))
    label_canvas_size.pack(side="left", padx=10)
    entry_canvas_width = ctk.CTkEntry(master=frame_canvas_size, placeholder_text="szerokość", width=80)
    entry_canvas_width.pack(side="left", padx=5)
    label_x = ctk.CTkLabel(master=frame_canvas_size, text="x", font=("Roboto", 14))
    label_x.pack(side="left", padx=5)
    entry_canvas_height = ctk.CTkEntry(master=frame_canvas_size, placeholder_text="wysokość", width=80)
    entry_canvas_height.pack(side="left", padx=5)

    button_create_project = ctk.CTkButton(master=frame, text="Stwórz projekt", command=create_project)
    button_create_project.pack(pady=20)

    button_open_project = ctk.CTkButton(master=frame, text="Otwórz istniejący projekt", command=open_existing_project)
    button_open_project.pack(pady=10)

    project_window.mainloop()


# Start aplikacji
new_project()
