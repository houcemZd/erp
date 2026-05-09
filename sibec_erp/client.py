import json
import os
from urllib.parse import urlparse
import webbrowser
import tkinter as tk
from tkinter import messagebox

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(APP_DIR, "client_config.json")
DEFAULT_SERVER_URL = "http://127.0.0.1:5000"


def load_server_url() -> str:
    if not os.path.exists(CONFIG_PATH):
        return DEFAULT_SERVER_URL

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data.get("server_url", DEFAULT_SERVER_URL)
    except (OSError, json.JSONDecodeError):
        return DEFAULT_SERVER_URL


def save_server_url(server_url: str) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as file:
        json.dump({"server_url": server_url.strip()}, file, ensure_ascii=False, indent=2)


root = tk.Tk()
root.title("SIBEC ERP Client")
root.geometry("500x320")
root.configure(bg="#e6e6e6")


title = tk.Label(
    root,
    text="SIBEC ERP",
    font=("Arial", 22, "bold"),
    bg="#e6e6e6",
    fg="#1f1f1f"
)
title.pack(pady=20)

info = tk.Label(
    root,
    text="Client multi-PC (URL serveur central)",
    font=("Arial", 11),
    bg="#e6e6e6"
)
info.pack()

url_var = tk.StringVar(value=load_server_url())

entry = tk.Entry(root, textvariable=url_var, width=50)
entry.pack(pady=10)


def open_erp() -> None:
    server_url = url_var.get().strip()
    parsed = urlparse(server_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        messagebox.showerror("URL invalide", "URL invalide. Exemple: http://192.168.1.10:5000")
        return
    webbrowser.open(server_url)


def persist_and_open() -> None:
    server_url = url_var.get().strip()
    if not server_url:
        messagebox.showerror("Erreur", "Veuillez saisir l'URL du serveur")
        return
    try:
        save_server_url(server_url)
    except OSError as exc:
        messagebox.showerror("Erreur", f"Impossible d'enregistrer la configuration: {exc}")
        return

    open_erp()


btn = tk.Button(
    root,
    text="ENREGISTRER ET OUVRIR ERP",
    command=persist_and_open,
    bg="#1f6feb",
    fg="white",
    font=("Arial", 11, "bold"),
    width=30,
    height=2,
    relief="flat",
    cursor="hand2"
)

btn.pack(pady=20)

note = tk.Label(
    root,
    text="Exemple: http://192.168.1.10:5000",
    font=("Arial", 10),
    bg="#e6e6e6"
)
note.pack()

root.mainloop()
