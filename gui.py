import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, scrolledtext
from dotenv import load_dotenv
from endpoints import PlantNetEndpoints


class GuiOutput:
    def __init__(self, text_widget):
        self.text_widget = text_widget
    def write(self, message):
        self.text_widget.configure(state=tk.NORMAL)
        self.text_widget.insert(tk.END, message)
        self.text_widget.see(tk.END)
        self.text_widget.update_idletasks()  # force update for every message
        self.text_widget.configure(state=tk.DISABLED)
    def flush(self):
        pass


def create_log_widget(root):
    log_frame = tk.Frame(root)
    log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=10, state=tk.DISABLED)
    log_text.pack(fill=tk.BOTH, expand=True)
    return log_text


def docs():
    items = [
        "Set API Key: Save your API key here",
        "Reset API Key: Remove the saved API key",
        "Identify Images: Select the directory with images to identify",
        "Rename Images: Be sure that you reviewed results. Rename images based on species, select CSV and directory"
        "and enter your initials (first letter of your name and surname)",
        "Group by Species: Group images by species in the selected directory",
        "Transform Results: Refactor results from CSV, new file will be renamed to results_transformed.csv",
    ]
    content = "\n".join(items)
    top = tk.Toplevel()
    top.title(r"Information List")
    top.geometry("800x600")
    text_area = scrolledtext.ScrolledText(top, wrap=tk.WORD)
    text_area.pack(expand=True, fill="both")
    text_area.insert("1.0", content)
    text_area.config(state=tk.DISABLED)


def set_api_key():
    api_key = simpledialog.askstring(r"API Key", r"Enter your API key:")
    if api_key:
        with open("api.env", "w", encoding="utf-8") as f:
            f.write(f"Plant_Net_API={api_key}")
        print(r"API key saved as api.env")
    else:
        print(r"No API key provided.")


def reset_api_key():
    if os.path.exists("api.env"):
        os.remove("api.env")
        messagebox.showinfo(r"Success", r"API key has been reset.")
    else:
        messagebox.showerror(r"Error", r"No API key file found to reset.")


def run_identify_images():
    def task():
        load_dotenv("api.env")
        api_key = os.environ.get("Plant_Net_API")
        if not api_key:
            print("API key not found in api.env")
            return
        from utils import identify_images_api
        pne = PlantNetEndpoints(api_key)
        identify_images_api(pne)
    threading.Thread(target=task, daemon=True).start()


def run_rename_to_species():
    csv_file = filedialog.askopenfilename(title=r"Select results.csv file", filetypes=[(r"CSV Files", r"*.csv")])
    if not csv_file:
        return
    directory = filedialog.askdirectory(title=r"Select image directory")
    if not directory:
        return
    suffix = simpledialog.askstring(r"Enter prefix", r"Enter prefix for renaming:")
    if not suffix:
        print(r"No prefix provided.")
        return
    from utils import rename_to_species
    rename_to_species(csv_file, directory, suffix)


def run_group_by_species():
    directory = filedialog.askdirectory(title=r"Select image directory")
    if not directory:
        return
    from utils import group_by_species
    group_by_species(directory)


def run_refactor_results():
    input_file = filedialog.askopenfilename(title=r"Select input CSV file", filetypes=[(r"CSV Files", r"*.csv")])
    if not input_file:
        return
    from utils import refactor_results
    refactor_results(input_file)


root = tk.Tk()
root.title(r"Flora Project - GUI")
root.geometry("1200x600")

top_frame = tk.Frame(root)
top_frame.pack(pady=20)

btn_question = tk.Button(top_frame, text="?", command=docs, width=4, padx=5, pady=5)
btn_question.pack(side=tk.LEFT, padx=10)

btn_set_api = tk.Button(top_frame, text="Set API Key", command=set_api_key, width=12, padx=5, pady=5)
btn_set_api.pack(side=tk.LEFT, padx=10)

btn_reset_api = tk.Button(top_frame, text="Reset API Key", command=reset_api_key, width=12, padx=5, pady=5)
btn_reset_api.pack(side=tk.LEFT, padx=10)

button_frame = tk.Frame(top_frame)
button_frame.pack(side=tk.LEFT, padx=10)

btn_main = tk.Button(button_frame, text="Identify Images", command=run_identify_images, width=20, padx=5, pady=5)
btn_main.pack(side=tk.LEFT, padx=10)

btn_rename = tk.Button(button_frame, text="Rename Images", command=run_rename_to_species, width=20, padx=5, pady=5)
btn_rename.pack(side=tk.LEFT, padx=10)

btn_move = tk.Button(button_frame, text="Group by Species", command=run_group_by_species, width=20, padx=5, pady=5)
btn_move.pack(side=tk.LEFT, padx=10)

btn_transposed = tk.Button(button_frame, text="Transform Results", command=run_refactor_results, width=20, padx=5, pady=5)
btn_transposed.pack(side=tk.LEFT, padx=10)

log_text = create_log_widget(root)
sys.stdout = GuiOutput(log_text)
sys.stderr = GuiOutput(log_text)
root.mainloop()
