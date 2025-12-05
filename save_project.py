import pickle
import os

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