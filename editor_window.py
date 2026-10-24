"""Small text editor window for the text inside a simulated file."""
import tkinter as tk
from tkinter import ttk, messagebox


class EditorWindow(tk.Toplevel):
    def __init__(self, app, node):
        super().__init__(app.root)
        self.app, self.node = app, node
        self.title(f"MiniFS Text Editor - {node.name}")
        self.geometry("620x420")
        self.info = ttk.Label(self, text=f"{node.path}   ({node.size:.2f} MB)")
        self.info.pack(anchor="w", padx=8, pady=(8, 2))
        self.text = tk.Text(self, wrap="word", undo=True, font=("Consolas", 11))
        self.text.pack(fill="both", expand=True, padx=8, pady=4)
        self.text.insert("1.0", node.content)
        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=8, pady=8)
        ttk.Button(bar, text="Save", command=self.save).pack(side="right")
        ttk.Button(bar, text="Close", command=self.destroy).pack(side="right", padx=6)

    def save(self):
        if not self.app.fs.is_attached(self.node):
            messagebox.showerror("MiniFS", "This file no longer exists.", parent=self)
            return
        self.node.content = self.text.get("1.0", "end-1c")
        self.node.touch()
        self.app.changed()
        self.info.config(text=f"Saved at {self.node.modified}")
