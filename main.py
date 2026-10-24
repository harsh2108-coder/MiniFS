"""Start MiniFS:   python main.py"""
import os
import tkinter as tk

from gui.app import MiniFSApp
from storage.json_store import JsonStore


def main():
    folder = os.path.dirname(os.path.abspath(__file__))
    store = JsonStore(os.path.join(folder, "minifs_data.json"))
    root = tk.Tk()
    MiniFSApp(root, store)
    root.mainloop()


if __name__ == "__main__":
    main()
