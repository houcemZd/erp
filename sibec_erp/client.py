import webbrowser
import tkinter as tk

SERVER_URL = "http://127.0.0.1:5000"

root = tk.Tk()
root.title("SIBEC ERP")
root.geometry("400x250")
root.configure(bg="#e6e6e6")

title = tk.Label(
    root,
    text="SIBEC ERP",
    font=("Arial", 22, "bold"),
    bg="#e6e6e6",
    fg="#1f1f1f"
)
title.pack(pady=30)

info = tk.Label(
    root,
    text="ERP Industriel SIBEC",
    font=("Arial", 12),
    bg="#e6e6e6"
)
info.pack()

def open_erp():
    webbrowser.open(SERVER_URL)

btn = tk.Button(
    root,
    text="OUVRIR ERP",
    command=open_erp,
    bg="#1f6feb",
    fg="white",
    font=("Arial", 12, "bold"),
    width=20,
    height=2,
    relief="flat",
    cursor="hand2"
)

btn.pack(pady=30)

root.mainloop()