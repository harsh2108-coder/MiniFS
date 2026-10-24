"""Mini terminal panel: type commands like ls, cd, mkdir ... on the virtual disk."""
import shlex
import tkinter as tk
from tkinter import ttk

from dsa.search import tree_search
from models.vfs import FSError

HELP = """Commands:
  ls                  list current folder
  cd <path|..|/>      change folder
  pwd                 show current path
  mkdir <name>        create folder
  touch <name> [MB]   create file
  cat <file>          show file text
  rename <old> <new>  rename item
  delete <name>       move to Recycle Bin (alias: rm)
  search <word>       DFS search of the whole tree
  tree                draw tree from here
  stats               disk + tree statistics
  clear               clear the screen
(use quotes for names with spaces: mkdir "My Photos")"""


class TerminalPanel(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.history, self.hpos = [], 0
        head = ttk.Frame(self)
        head.pack(fill="x")
        ttk.Label(head, text="MiniFS Terminal (type 'help')").pack(side="left", padx=6)
        ttk.Button(head, text="x", width=3, command=app.toggle_terminal).pack(side="right")
        self.out = tk.Text(self, height=9, bg="#0b1020", fg="#34d399", state="disabled",
                           font=("Consolas", 10), wrap="word")
        self.out.pack(fill="both", expand=True)
        row = ttk.Frame(self)
        row.pack(fill="x")
        self.prompt = ttk.Label(row, text="Root $")
        self.prompt.pack(side="left", padx=4)
        self.entry = ttk.Entry(row)
        self.entry.pack(side="left", fill="x", expand=True, pady=3)
        self.entry.bind("<Return>", self.on_enter)
        self.entry.bind("<Up>", self.on_up)
        self.entry.bind("<Down>", self.on_down)

    def print(self, text):
        self.out.config(state="normal")
        self.out.insert("end", text + "\n")
        self.out.see("end")
        self.out.config(state="disabled")

    def clear(self):
        self.out.config(state="normal")
        self.out.delete("1.0", "end")
        self.out.config(state="disabled")

    def set_prompt(self, name):
        self.prompt.config(text=f"{name} $")

    def on_up(self, _):
        if self.hpos > 0:
            self.hpos -= 1
            self.entry.delete(0, "end")
            self.entry.insert(0, self.history[self.hpos])
        return "break"

    def on_down(self, _):
        self.hpos = min(len(self.history), self.hpos + 1)
        self.entry.delete(0, "end")
        if self.hpos < len(self.history):
            self.entry.insert(0, self.history[self.hpos])
        return "break"

    def on_enter(self, _):
        line = self.entry.get().strip()
        self.entry.delete(0, "end")
        if not line:
            return
        self.history.append(line)
        self.hpos = len(self.history)
        self.print(f"{self.app.fs.cwd.name} $ {line}")
        try:
            result = self.execute(line)
            if result:
                self.print(result)
        except FSError as err:
            self.print(f"Error: {err}")
        except ValueError as err:
            self.print(f"Error: {err}")
        self.app.search_results = None
        self.app.changed()

    def execute(self, line):
        parts = shlex.split(line)
        cmd, args = parts[0].lower(), parts[1:]
        fs = self.app.fs
        if cmd == "help":
            return HELP
        if cmd == "pwd":
            return fs.cwd.path
        if cmd == "ls":
            if not fs.cwd.children:
                return "(empty folder)"
            rows = [f"{'<DIR>' if n.is_folder() else '     '}  {n.size:8.2f} MB  {n.modified}  {n.name}"
                    for n in fs.cwd.children]
            return "\n".join(rows)
        if cmd == "cd":
            fs.change_dir(fs.root) if not args else fs.change_dir_path(args[0])
            return f"Now in {fs.cwd.path}"
        if cmd == "mkdir":
            if not args:
                return "Usage: mkdir <name>"
            return f"Created folder {fs.mkdir(args[0]).path}"
        if cmd == "touch":
            if not args:
                return "Usage: touch <name> [MB]"
            size = float(args[1]) if len(args) > 1 else 1.0
            node = fs.create_file(args[0], size)
            return f"Created file {node.path} ({node.size} MB)"
        if cmd == "cat":
            node = fs.cwd.find_child(args[0]) if args else None
            if node is None:
                return "Usage: cat <file in this folder>"
            return "That is a folder." if node.is_folder() else (node.content or "(empty file)")
        if cmd == "rename":
            if len(args) < 2:
                return "Usage: rename <old> <new>"
            node = fs.cwd.find_child(args[0])
            if node is None:
                return f"'{args[0]}' not found here."
            fs.rename(node, args[1])
            return f"Renamed to {args[1]}"
        if cmd in ("delete", "rm"):
            node = fs.cwd.find_child(args[0]) if args else None
            if node is None:
                return "Usage: delete <name in this folder>"
            fs.delete(node)
            return f"Moved '{node.name}' to the Recycle Bin."
        if cmd == "search":
            if not args:
                return "Usage: search <word>"
            results, steps = tree_search(fs.root, args[0], "dfs")
            lines = [f"{len(results)} match(es), visited {len(steps)} nodes:"]
            lines += [f"  {n.path}  ({n.size} MB)" for n in results]
            return "\n".join(lines)
        if cmd == "tree":
            lines = [fs.cwd.name + "/"]

            def walk(node, prefix):
                for i, child in enumerate(node.children):
                    last = i == len(node.children) - 1
                    lines.append(prefix + ("`-- " if last else "|-- ") + child.name
                                 + ("/" if child.is_folder() else ""))
                    walk(child, prefix + ("    " if last else "|   "))

            walk(fs.cwd, "")
            return "\n".join(lines)
        if cmd == "stats":
            s = fs.stats()
            return (f"Files: {s['files']}  Folders: {s['folders']}  Tree height: {s['height']}\n"
                    f"Disk: {s['used']} / {s['capacity']} MB used, {s['free']} MB free\n"
                    f"Recycle Bin: {s['bin_count']} item(s), {s['bin_size']} MB")
        if cmd == "clear":
            self.clear()
            return ""
        return f"Unknown command '{cmd}'. Type 'help'."
