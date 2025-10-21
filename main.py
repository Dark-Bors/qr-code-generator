import tkinter as tk
from tkinter import messagebox
from gui import QRCodeApp
from paths import data_path
import yaml

def load_config():
    cfg_path = data_path("config.yaml")
    if not cfg_path.exists():
        messagebox.showwarning("Missing config.yaml",
                               f"Couldn't find {cfg_path.name} next to the app.\nUsing defaults.")
        return {}
    with open(cfg_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

if __name__ == "__main__":
    cfg = load_config()
    app = QRCodeApp(cfg)  # pass config into your GUI (recommended)
    app.mainloop()
