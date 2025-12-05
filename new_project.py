import numpy as np
import matplotlib.pyplot as plt
import screeninfo
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox, Listbox
from tkinter.colorchooser import askcolor
from django.utils.termcolors import background
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image
import sys
import pickle
import os

from bezier_curve import bezier_curve
from export import export_frames
from tkinter import Canvas, Frame
from gif import create_gif



def save_project_to_file(project_path, frames, canvas_width, canvas_height, is_new):
    project_file = os.path.join(project_path, "project_data.pkl")
    project_data = {
        "canvas_width": canvas_width,
        "canvas_height": canvas_height,
        "is_new": is_new,
        "frames": frames,
    }
    with open(project_file, "wb") as file:
        pickle.dump(project_data, file)
    print(f"Projekt zapisany w: {project_file}")



def load_project_from_file(project_path):
    project_file = os.path.join(project_path, "project_data.pkl")
    try:
        with open(project_file, "rb") as file:
            project_data = pickle.load(file)

        canvas_width = project_data.get("canvas_width", 800)
        canvas_height = project_data.get("canvas_height", 600)
        is_new = project_data.get("is_new", False)
        frames = project_data.get("frames", [[]])

        print("Projekt wczytany pomyślnie")
        return frames, canvas_width, canvas_height, is_new
    except Exception as e:
        print(f"Błąd podczas wczytywania projektu: {e}")
        return [[]], 800, 600, True  # Domyślne wartości


def save_current_project():
    global frames, canvas_width, canvas_height
    project_path = "sciezka_do_projektu"
    save_project_to_file(project_path, frames, canvas_width, canvas_height, is_new)