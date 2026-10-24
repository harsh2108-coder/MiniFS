"""Capstone demo: click 'Next step' and MiniFS performs each feature for you."""
import tkinter as tk
from tkinter import ttk

from models.vfs import FSError

STEPS = [
    "Welcome! Click 'Next step' to see the main features one by one.",
    "Step 1: The DSA Visualizer shows the Tree, the Stacks, the Hash table and the Search.",
    "Step 2: Create the folder /College/Sem6 (a new node is added to the tree).",
    "Step 3: Create the file capstone_report.txt (3.5 MB) inside it.",
    "Step 4: Go into Sem6. Watch the Back stack (LIFO) grow.",
    "Step 5: Search 'notes.txt' with DFS and watch the visiting order.",
    "Step 6: Delete the report: it goes to the Recycle Bin (soft delete).",
    "Step 7: Disk usage still counts the deleted file (it is only in the bin).",
    "Step 8: The Recycle Bin remembers the original folder of the file.",
    "Step 9: Restore the file. The hash index is updated again.",
    "Demo finished. Ready for questions!",
]


class DemoWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app.root)
        self.app, self.i = app, 0
        self.title("Capstone Demo")
        self.geometry("520x190")
        self.counter = ttk.Label(self, text="Demo step 0 / 10", font=("Segoe UI", 11, "bold"))
        self.counter.pack(anchor="w", padx=12, pady=(12, 4))
        self.msg = ttk.Label(self, text=STEPS[0], wraplength=490, justify="left")
        self.msg.pack(anchor="w", padx=12)
        bar = ttk.Frame(self)
        bar.pack(side="bottom", fill="x", padx=12, pady=12)
        self.next_btn = ttk.Button(bar, text="Next step >", command=self.next)
        self.next_btn.pack(side="right")
        ttk.Button(bar, text="Close", command=self.destroy).pack(side="right", padx=6)

    def next(self):
        if self.i >= len(STEPS) - 1:
            self.destroy()
            return
        self.i += 1
        self.counter.config(text=f"Demo step {self.i} / 10")
        self.msg.config(text=STEPS[self.i])
        try:
            self.run_step(self.i)
        except FSError as err:
            self.msg.config(text=f"{STEPS[self.i]}\n(note: {err})")
        if self.i == len(STEPS) - 1:
            self.next_btn.config(text="Finish")

    def run_step(self, n):
        app, fs = self.app, self.app.fs
        report = "/College/Sem6/capstone_report.txt"
        if n == 1:
            app.open_dsa("tree")
        elif n == 2:
            college = fs.find("/College")
            if college and not college.find_child("Sem6"):
                fs.mkdir("Sem6", college)
            app.changed()
        elif n == 3:
            sem6 = fs.find("/College/Sem6")
            if sem6 and not sem6.find_child("capstone_report.txt"):
                fs.create_file("capstone_report.txt", 3.5, "MiniFS capstone report.", sem6)
            app.changed()
        elif n == 4:
            sem6 = fs.find("/College/Sem6")
            if sem6:
                app.search_results = None
                fs.change_dir(sem6)
            app.changed()
            app.open_dsa("stack")
        elif n == 5:
            dsa = app.open_dsa("search")
            dsa.start_trace("notes.txt", "dfs")
        elif n == 6:
            node = fs.find(report)
            if node:
                fs.delete(node)
            app.changed()
        elif n == 7:
            app.status(f"Disk used: {fs.used} MB (the Recycle Bin still counts)")
        elif n == 8:
            app.open_bin()
        elif n == 9:
            for item in fs.bin:
                if item["node"].name == "capstone_report.txt":
                    fs.restore(item)
                    break
            app.changed()
            app.open_dsa("hash")
