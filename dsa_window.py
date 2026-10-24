"""DSA Visualizer: shows the data structures working live (great for the viva)."""
import tkinter as tk
from tkinter import ttk

from dsa.search import tree_search

COMPLEXITY = """\
TREE (N-ary tree of Nodes)
  create / delete item ........ O(k)    k = items in the folder (duplicate check)
  folder size ................. O(m)    m = items below it (recursion)
  open a path (cd) ............ O(d*k)  d = depth

STACK (Back / Forward)
  push, pop, back, forward .... O(1)

HASH INDEX (Python dict)
  lookup by exact name ........ O(1) average, O(n) worst case
  rebuild index ............... O(n)

SEARCH
  DFS (recursion) ............. O(n) time, O(depth) memory
  BFS (queue) ................. O(n) time, O(width) memory
"""


class DsaWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        self.title("DSA Visualizer")
        self.geometry("560x560")
        self.trace_job = None
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=6, pady=6)
        self.tab_tree = ttk.Frame(self.notebook)
        self.tab_stack = ttk.Frame(self.notebook)
        self.tab_search = ttk.Frame(self.notebook)
        self.tab_hash = ttk.Frame(self.notebook)
        self.tab_cx = ttk.Frame(self.notebook)
        for tab, name in ((self.tab_tree, "Tree"), (self.tab_stack, "Stacks"),
                          (self.tab_search, "Search"), (self.tab_hash, "Hash"),
                          (self.tab_cx, "Complexity")):
            self.notebook.add(tab, text=name)
        self._build_tree()
        self._build_stacks()
        self._build_search()
        self._build_hash()
        txt = tk.Text(self.tab_cx, font=("Consolas", 10), wrap="none")
        txt.insert("1.0", COMPLEXITY)
        txt.config(state="disabled")
        txt.pack(fill="both", expand=True)
        self.bind("<Destroy>", self._on_destroy)
        self.refresh()

    def _on_destroy(self, event):
        if event.widget is self and self.trace_job:
            self.after_cancel(self.trace_job)

    def show_tab(self, name):
        tabs = {"tree": self.tab_tree, "stack": self.tab_stack, "search": self.tab_search,
                "hash": self.tab_hash, "complexity": self.tab_cx}
        self.notebook.select(tabs[name])

    # ---------------------------------------------------------------- tree tab
    def _build_tree(self):
        ttk.Label(self.tab_tree, text="Parent-child hierarchy. Blue = current folder.").pack(
            anchor="w", padx=6, pady=4)
        self.tv = ttk.Treeview(self.tab_tree, show="tree")
        self.tv.tag_configure("cwd", background="#3b82f6", foreground="white")
        self.tv.pack(fill="both", expand=True, padx=6, pady=4)

    def _fill_tree(self):
        self.tv.delete(*self.tv.get_children())
        fs = self.app.fs

        def add(parent_iid, node):
            icon = "📁" if node.is_folder() else "📄"
            tags = ("cwd",) if node is fs.cwd else ()
            iid = self.tv.insert(parent_iid, "end", text=f"{icon} {node.name}  [{node.size:.2f} MB]",
                                 open=True, tags=tags)
            for child in node.children:
                add(iid, child)

        add("", fs.root)

    # ------------------------------------------------------------- stacks tab
    def _build_stacks(self):
        frame = ttk.Frame(self.tab_stack)
        frame.pack(fill="both", expand=True, padx=6, pady=6)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(1, weight=1)
        ttk.Label(frame, text="Back stack (top first)").grid(row=0, column=0, sticky="w")
        ttk.Label(frame, text="Forward stack (top first)").grid(row=0, column=1, sticky="w")
        self.back_list = tk.Listbox(frame, exportselection=False)
        self.fwd_list = tk.Listbox(frame, exportselection=False)
        self.back_list.grid(row=1, column=0, sticky="nsew", padx=(0, 4))
        self.fwd_list.grid(row=1, column=1, sticky="nsew", padx=(4, 0))
        ttk.Label(frame, wraplength=500, text=(
            "Back = pop from the Back stack and push onto Forward (O(1)).\n"
            "Opening a new folder pushes on Back and clears Forward.")).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=6)

    def _fill_stacks(self):
        nav = self.app.fs.nav
        for box, items in ((self.back_list, nav.back), (self.fwd_list, nav.forward)):
            box.delete(0, "end")
            for i, path in enumerate(reversed(items)):
                box.insert("end", ("TOP > " if i == 0 else "      ") + path)

    # ------------------------------------------------------------ search tab
    def _build_search(self):
        bar = ttk.Frame(self.tab_search)
        bar.pack(fill="x", padx=6, pady=6)
        self.q_var = tk.StringVar()
        self.algo_var = tk.StringVar(value="dfs")
        entry = ttk.Entry(bar, textvariable=self.q_var, width=22)
        entry.pack(side="left")
        entry.bind("<Return>", lambda e: self.start_trace())
        ttk.Combobox(bar, textvariable=self.algo_var, values=("dfs", "bfs"),
                     width=5, state="readonly").pack(side="left", padx=4)
        ttk.Button(bar, text="Start trace", command=self.start_trace).pack(side="left")
        self.trace_status = ttk.Label(self.tab_search, text="Type a name and press Start trace.")
        self.trace_status.pack(anchor="w", padx=6)
        self.trace_list = tk.Listbox(self.tab_search, exportselection=False)
        self.trace_list.pack(fill="both", expand=True, padx=6, pady=6)

    def start_trace(self, query=None, method=None):
        if query is not None:
            self.q_var.set(query)
        if method is not None:
            self.algo_var.set(method)
        query = self.q_var.get().strip()
        if not query:
            self.trace_status.config(text="Please type a name to search for.")
            return
        if self.trace_job:
            self.after_cancel(self.trace_job)
            self.trace_job = None
        results, steps = tree_search(self.app.fs.root, query, self.algo_var.get())
        self.trace_list.delete(0, "end")
        self.trace_status.config(text=f"{self.algo_var.get().upper()}: visiting {len(steps)} nodes...")
        self._animate(steps, results, 0)

    def _animate(self, steps, results, i):
        if i >= len(steps):
            self.trace_status.config(text=f"Done: {len(results)} match(es) in {len(steps)} steps.")
            self.trace_job = None
            return
        node, matched = steps[i]
        icon = "📁" if node.is_folder() else "📄"
        self.trace_list.insert("end", f"Step {i + 1}: {icon} {node.path}  ->  "
                                      f"{'MATCH' if matched else 'checking'}")
        if matched:
            self.trace_list.itemconfig("end", background="#bbf7d0")
        self.trace_list.see("end")
        self.trace_job = self.after(150, self._animate, steps, results, i + 1)

    # -------------------------------------------------------------- hash tab
    def _build_hash(self):
        self.hash_info = ttk.Label(self.tab_hash, text="")
        self.hash_info.pack(anchor="w", padx=6, pady=4)
        bar = ttk.Frame(self.tab_hash)
        bar.pack(fill="x", padx=6)
        self.h_var = tk.StringVar()
        entry = ttk.Entry(bar, textvariable=self.h_var, width=24)
        entry.pack(side="left")
        entry.bind("<Return>", lambda e: self.lookup())
        ttk.Button(bar, text="O(1) lookup", command=self.lookup).pack(side="left", padx=4)
        self.h_result = ttk.Label(self.tab_hash, text="", wraplength=500)
        self.h_result.pack(anchor="w", padx=6, pady=4)
        self.h_list = tk.Listbox(self.tab_hash, exportselection=False)
        self.h_list.pack(fill="both", expand=True, padx=6, pady=6)

    def lookup(self):
        name = self.h_var.get().strip()
        found = self.app.fs.index.lookup(name) if name else []
        self.h_result.config(text=("Found: " + ", ".join(n.path for n in found)) if found
                             else "No exact match.")

    def _fill_hash(self):
        index = self.app.fs.index
        self.hash_info.config(text=f"{len(index.table)} keys, {index.total_nodes()} nodes stored")
        self.h_list.delete(0, "end")
        for key in sorted(index.table):
            paths = ", ".join(n.path for n in index.table[key])
            self.h_list.insert("end", f"hash('{key}')  ->  {paths}")

    # ---------------------------------------------------------------- refresh
    def refresh(self):
        self._fill_tree()
        self._fill_stacks()
        self._fill_hash()
