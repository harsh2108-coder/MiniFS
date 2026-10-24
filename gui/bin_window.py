"""Recycle Bin window: restore items or empty the bin."""
import tkinter as tk
from tkinter import ttk, messagebox

from models.vfs import FSError


class BinWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        self.title("Recycle Bin")
        self.geometry("640x340")
        self.info = ttk.Label(self, text="")
        self.info.pack(anchor="w", padx=8, pady=8)
        self.tree = ttk.Treeview(self, columns=("orig", "time", "size"), selectmode="browse")
        for col, text, w in (("#0", "Name", 160), ("orig", "Original folder", 200),
                             ("time", "Deleted at", 150), ("size", "Size", 70)):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=8)
        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=8, pady=8)
        ttk.Button(bar, text="Restore", command=self.restore).pack(side="left")
        ttk.Button(bar, text="Empty Recycle Bin", command=self.empty).pack(side="left", padx=6)
        ttk.Button(bar, text="Close", command=self.destroy).pack(side="right")
        self.items = {}
        self.refresh()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        self.items = {}
        for item in self.app.fs.bin:
            node = item["node"]
            icon = "📁" if node.is_folder() else "📄"
            iid = self.tree.insert("", "end", text=f"{icon} {node.name}",
                                   values=(item["orig_path"], item["time"], f"{node.size:.2f} MB"))
            self.items[iid] = item
        total = sum(i["node"].size for i in self.app.fs.bin)
        self.info.config(text=f"{len(self.app.fs.bin)} item(s), {total:.2f} MB "
                              "(items in the bin still use disk space)")

    def restore(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Recycle Bin", "Select an item first.", parent=self)
            return
        try:
            node = self.app.fs.restore(self.items[sel[0]])
        except FSError as err:
            messagebox.showerror("MiniFS", str(err), parent=self)
            return
        self.app.status(f"Restored '{node.name}' to {node.path}")
        self.app.changed()

    def empty(self):
        if self.app.fs.bin and messagebox.askyesno(
                "Empty Recycle Bin", "Permanently delete everything in the bin?", parent=self):
            self.app.fs.empty_bin()
            self.app.changed()
