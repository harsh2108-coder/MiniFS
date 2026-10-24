"""Main window of MiniFS (Tkinter).

The GUI only *displays* things and calls methods of VirtualFileSystem.
All the real work (tree, stacks, hash, search ...) is in models/ and dsa/.
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog

from dsa.search import tree_search
from models.vfs import VirtualFileSystem, FSError
from gui.bin_window import BinWindow
from gui.demo import DemoWindow
from gui.dsa_window import DsaWindow
from gui.editor_window import EditorWindow
from gui.terminal import TerminalPanel


class MiniFSApp:
    def __init__(self, root, store):
        self.root = root
        self.store = store
        self.fs = store.load() or VirtualFileSystem.sample()
        self.row_nodes = {}          # Treeview row id -> Node
        self.search_results = None   # None = normal folder view
        self.search_info = ""
        self.windows = {}            # open tool windows (DSA, bin ...)
        self.terminal_visible = False

        root.title("MiniFS - Virtual File System Simulator (Python)")
        root.geometry("1100x660")
        root.minsize(900, 520)
        self._build_style()
        self._build_sidebar()
        self._build_main()
        self._build_statusbar()
        root.columnconfigure(1, weight=1)
        root.rowconfigure(0, weight=1)
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.terminal.print("MiniFS terminal ready. Type 'help' for commands.")
        self.refresh()

    # ============================================================ building the UI
    def _build_style(self):
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Treeview", rowheight=26)
        style.configure("Brand.TLabel", font=("Segoe UI", 16, "bold"))
        style.configure("Section.TLabel", foreground="#64748b", font=("Segoe UI", 8, "bold"))

    def _build_sidebar(self):
        side = ttk.Frame(self.root, padding=8)
        side.grid(row=0, column=0, rowspan=2, sticky="ns")
        ttk.Label(side, text="MiniFS", style="Brand.TLabel").pack(anchor="w")
        ttk.Label(side, text="Virtual OS File System").pack(anchor="w", pady=(0, 8))

        def section(text):
            ttk.Label(side, text=text, style="Section.TLabel").pack(anchor="w", pady=(10, 2))

        def button(text, command):
            ttk.Button(side, text=text, command=command).pack(fill="x", pady=1)

        section("QUICK ACCESS")
        for label, path in (("Root Home", "/"), ("Documents", "/Documents"), ("Pictures", "/Pictures"),
                            ("College", "/College"), ("Downloads", "/Downloads")):
            button(label, lambda p=path: self.go_to(p))
        self.bin_button = ttk.Button(side, text="Recycle Bin", command=self.open_bin)
        self.bin_button.pack(fill="x", pady=1)
        section("TOOLS & DSA")
        button("DSA Visualizer", lambda: self.open_dsa())
        button("Mini Terminal", self.toggle_terminal)
        button("Capstone Demo", lambda: self.open_window("demo", DemoWindow))
        section("DATA")
        button("Export JSON", self.export_json)
        button("Import JSON", self.import_json)
        button("Reset to sample", self.reset)

        box = ttk.LabelFrame(side, text="Virtual disk", padding=6)
        box.pack(side="bottom", fill="x", pady=(16, 0))
        self.disk_bar = ttk.Progressbar(box, maximum=100, length=170)
        self.disk_bar.pack(fill="x")
        self.disk_label = ttk.Label(box, text="")
        self.disk_label.pack(anchor="w", pady=(4, 0))

    def _build_main(self):
        main = ttk.Frame(self.root)
        main.grid(row=0, column=1, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(2, weight=1)

        # --- navigation bar
        nav = ttk.Frame(main, padding=6)
        nav.grid(row=0, column=0, sticky="ew")
        self.btn_back = ttk.Button(nav, text="< Back", width=7, command=self.go_back)
        self.btn_fwd = ttk.Button(nav, text="Forward >", width=9, command=self.go_forward)
        self.btn_up = ttk.Button(nav, text="Up", width=5, command=self.go_up)
        for b in (self.btn_back, self.btn_fwd, self.btn_up):
            b.pack(side="left", padx=2)
        self.crumbs = ttk.Frame(nav)
        self.crumbs.pack(side="left", fill="x", expand=True, padx=8)
        self.search_var = tk.StringVar()
        self.algo_var = tk.StringVar(value="dfs")
        entry = ttk.Entry(nav, textvariable=self.search_var, width=18)
        entry.pack(side="left")
        entry.bind("<Return>", lambda e: self.do_search())
        ttk.Combobox(nav, textvariable=self.algo_var, values=("dfs", "bfs"), width=5,
                     state="readonly").pack(side="left", padx=3)
        ttk.Button(nav, text="Search", command=self.do_search).pack(side="left")

        # --- action bar
        bar = ttk.Frame(main, padding=(6, 0, 6, 6))
        bar.grid(row=1, column=0, sticky="ew")
        ttk.Button(bar, text="New Folder", command=self.new_folder).pack(side="left", padx=2)
        ttk.Button(bar, text="New File", command=self.new_file).pack(side="left", padx=2)
        self.btn_paste = ttk.Button(bar, text="Paste", command=self.paste)
        self.btn_paste.pack(side="left", padx=2)
        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y", padx=6)
        self.item_buttons = []
        for text, command in (("Open", self.open_selected), ("Rename", self.rename_selected),
                              ("Copy", self.copy_selected), ("Cut", self.cut_selected),
                              ("Delete", self.delete_selected), ("Properties", self.properties_selected)):
            b = ttk.Button(bar, text=text, command=command)
            b.pack(side="left", padx=2)
            self.item_buttons.append(b)
        self.count_label = ttk.Label(bar, text="")
        self.count_label.pack(side="right", padx=6)

        # --- file list
        frame = ttk.Frame(main)
        frame.grid(row=2, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(frame, columns=("type", "size", "modified"), selectmode="browse")
        for col, text, width, anchor in (("#0", "Name", 300, "w"), ("type", "Type", 230, "w"),
                                         ("size", "Size", 90, "e"), ("modified", "Modified", 150, "w")):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor=anchor)
        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        self.tree.bind("<<TreeviewSelect>>", lambda e: self._update_buttons())
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Button-3>", self._on_right_click)
        self.tree.bind("<Button-2>", self._on_right_click)       # right-click on macOS
        self.tree.bind("<Return>", lambda e: self.open_selected())
        self.tree.bind("<Delete>", lambda e: self.delete_selected())
        self.tree.bind("<F2>", lambda e: self.rename_selected())
        self.tree.bind("<BackSpace>", lambda e: self.go_up())
        self.tree.bind("<Control-c>", lambda e: self.copy_selected())
        self.tree.bind("<Control-x>", lambda e: self.cut_selected())
        self.tree.bind("<Control-v>", lambda e: self.paste())
        self.root.bind("<Alt-Left>", lambda e: self.go_back())
        self.root.bind("<Alt-Right>", lambda e: self.go_forward())

        self.menu = tk.Menu(self.root, tearoff=0)
        for entry in (("Open", self.open_selected), ("Rename", self.rename_selected), None,
                      ("Copy", self.copy_selected), ("Cut / Move", self.cut_selected), None,
                      ("Delete", self.delete_selected), None,
                      ("Properties", self.properties_selected)):
            if entry is None:
                self.menu.add_separator()
            else:
                self.menu.add_command(label=entry[0], command=entry[1])

        # --- terminal (hidden until opened)
        self.terminal = TerminalPanel(main, self)
        self.terminal.grid(row=3, column=0, sticky="ew")
        self.terminal.grid_remove()

    def _build_statusbar(self):
        bar = ttk.Frame(self.root, padding=(8, 2))
        bar.grid(row=1, column=1, sticky="ew")
        self.status_left = ttk.Label(bar, text="")
        self.status_left.pack(side="left")
        self.status_right = ttk.Label(bar, text="")
        self.status_right.pack(side="right")

    # ============================================================ refreshing the screen
    def changed(self):
        """Call after any change: auto-save, then redraw."""
        try:
            self.store.save(self.fs)
        except FSError as err:
            self.status(str(err))
        self.refresh()

    def status(self, text):
        self.status_left.config(text=text)

    def refresh(self):
        fs = self.fs
        if self.search_results is not None:
            self.search_results = [n for n in self.search_results if fs.is_attached(n)]
        self._draw_breadcrumb()
        self._draw_rows()
        self._update_buttons()
        s = fs.stats()
        self.disk_bar.config(maximum=max(1, s["capacity"]), value=min(s["used"], s["capacity"]))
        self.disk_label.config(text=f"{s['used']:.1f} / {s['capacity']:.0f} MB used\n{s['free']:.1f} MB free")
        self.bin_button.config(text=f"Recycle Bin ({s['bin_count']})" if s["bin_count"] else "Recycle Bin")
        self.status_left.config(text=f"Folders: {s['folders']}  |  Files: {s['files']}  |  Path: {fs.cwd.path}")
        self.status_right.config(text=f"Nodes: {s['nodes']}  |  Tree height: {s['height']}")
        self.terminal.set_prompt(fs.cwd.name)
        for window in list(self.windows.values()):
            if window.winfo_exists() and hasattr(window, "refresh"):
                window.refresh()

    def _draw_breadcrumb(self):
        for child in self.crumbs.winfo_children():
            child.destroy()
        trail = self.fs.breadcrumb()
        for i, (name, path) in enumerate(trail):
            ttk.Button(self.crumbs, text=name, width=max(4, len(name) + 1),
                       command=lambda p=path: self.go_to(p)).pack(side="left")
            if i < len(trail) - 1:
                ttk.Label(self.crumbs, text=">").pack(side="left")

    def _draw_rows(self):
        self.tree.delete(*self.tree.get_children())
        self.row_nodes = {}
        searching = self.search_results is not None
        if searching:
            nodes = self.search_results
        else:   # folders first, then A-Z
            nodes = sorted(self.fs.cwd.children, key=lambda n: (not n.is_folder(), n.name.lower()))
        for node in nodes:
            icon = "📁" if node.is_folder() else "📄"
            kind = (f"Match in {node.path}" if searching
                    else "Folder" if node.is_folder() else f"{node.extension()} file")
            iid = self.tree.insert("", "end", text=f"{icon} {node.name}",
                                   values=(kind, f"{node.size:.2f} MB", node.modified))
            self.row_nodes[iid] = node
        self.count_label.config(text=self.search_info if searching
                                else f"{len(nodes)} item(s) in {self.fs.cwd.name}")

    def _update_buttons(self):
        fs = self.fs
        self.btn_back.state(["!disabled"] if fs.nav.can_back() else ["disabled"])
        self.btn_fwd.state(["!disabled"] if fs.nav.can_forward() else ["disabled"])
        self.btn_up.state(["!disabled"] if fs.cwd.parent else ["disabled"])
        self.btn_paste.state(["!disabled"] if fs.clipboard else ["disabled"])
        state = ["!disabled"] if self.selected() else ["disabled"]
        for button in self.item_buttons:
            button.state(state)

    # ============================================================ helpers
    def selected(self):
        sel = self.tree.selection()
        return self.row_nodes.get(sel[0]) if sel else None

    def run(self, action, *args):
        """Run a file-system action; show a message box if the user made a mistake."""
        try:
            result = action(*args)
        except FSError as err:
            messagebox.showerror("MiniFS", str(err), parent=self.root)
            return None
        self.changed()
        return result

    def open_window(self, key, window_class):
        window = self.windows.get(key)
        if window is not None and window.winfo_exists():
            window.lift()
            return window
        window = window_class(self)
        self.windows[key] = window
        return window

    def open_dsa(self, tab=None):
        window = self.open_window("dsa", DsaWindow)
        if tab:
            window.show_tab(tab)
        return window

    def open_bin(self):
        return self.open_window("bin", BinWindow)

    def toggle_terminal(self):
        self.terminal_visible = not self.terminal_visible
        if self.terminal_visible:
            self.terminal.grid()
            self.terminal.entry.focus_set()
        else:
            self.terminal.grid_remove()

    # ============================================================ navigation
    def _leave_search(self):
        self.search_results = None
        self.search_var.set("")

    def go_to(self, path):
        node = self.fs.find(path)
        if node is None or not node.is_folder():
            messagebox.showerror("MiniFS", f"Folder '{path}' does not exist.", parent=self.root)
            return
        self._leave_search()
        self.fs.change_dir(node)
        self.refresh()

    def go_back(self):
        if self.fs.go_back():
            self._leave_search()
            self.refresh()

    def go_forward(self):
        if self.fs.go_forward():
            self._leave_search()
            self.refresh()

    def go_up(self):
        if self.fs.cwd.parent:
            self._leave_search()
            self.fs.change_dir(self.fs.cwd.parent)
            self.refresh()

    def do_search(self):
        query = self.search_var.get().strip()
        if not query:
            self.search_results = None
            self.refresh()
            return
        method = self.algo_var.get()
        results, steps = tree_search(self.fs.root, query, method)
        self.search_results = results
        self.search_info = (f"{len(results)} match(es) for '{query}' "
                            f"({method.upper()}, {len(steps)} nodes visited)")
        self.refresh()

    # ============================================================ file actions
    def new_folder(self):
        name = simpledialog.askstring("New Folder", "Folder name:", parent=self.root)
        if name is not None:
            self._leave_search()
            self.run(self.fs.mkdir, name)

    def new_file(self):
        name = simpledialog.askstring("New File", "File name (e.g. test.txt):", parent=self.root)
        if name is None:
            return
        size = simpledialog.askfloat("New File", "Simulated size in MB:", initialvalue=1.0,
                                     minvalue=0.0, parent=self.root)
        if size is None:
            return
        self._leave_search()
        self.run(self.fs.create_file, name, size, f"Created {name.strip()} in MiniFS.")

    def open_selected(self):
        node = self.selected()
        if node is None:
            return
        if node.is_folder():
            self._leave_search()
            self.fs.change_dir(node)
            self.refresh()
        else:
            EditorWindow(self, node)

    def rename_selected(self):
        node = self.selected()
        if node is None:
            return
        name = simpledialog.askstring("Rename", f"New name for '{node.name}':",
                                      initialvalue=node.name, parent=self.root)
        if name is not None and name != node.name:
            self.run(self.fs.rename, node, name)

    def copy_selected(self):
        node = self.selected()
        if node:
            self.fs.set_clipboard(node, "copy")
            self.status(f"'{node.name}' copied. Open a folder and click Paste.")
            self._update_buttons()

    def cut_selected(self):
        node = self.selected()
        if node:
            self.fs.set_clipboard(node, "cut")
            self.status(f"'{node.name}' cut. Open a folder and click Paste to move it.")
            self._update_buttons()

    def paste(self):
        if not self.fs.clipboard:
            return
        self._leave_search()
        self.run(self.fs.paste)

    def delete_selected(self):
        node = self.selected()
        if node and messagebox.askyesno("Delete", f"Move '{node.name}' to the Recycle Bin?",
                                        parent=self.root):
            self.run(self.fs.delete, node)

    def properties_selected(self):
        node = self.selected()
        if node is None:
            return
        lines = [f"Type: {'Folder' if node.is_folder() else 'File (' + node.extension() + ')'}",
                 f"Size: {node.size:.2f} MB", f"Path: {node.path}", f"Created: {node.created}",
                 f"Modified: {node.modified}",
                 f"Parent: {node.parent.name if node.parent else 'none (root node)'}"]
        if node.is_folder():
            files, folders = node.count()
            lines += [f"Direct children: {len(node.children)}", f"Files inside: {files}",
                      f"Folders inside: {folders}"]
        else:
            lines.append(f"Characters: {len(node.content)}")
        messagebox.showinfo(node.name, "\n".join(lines), parent=self.root)

    # ============================================================ mouse
    def _on_double_click(self, event):
        if self.tree.identify_row(event.y):
            self.open_selected()

    def _on_right_click(self, event):
        row = self.tree.identify_row(event.y)
        if row:
            self.tree.selection_set(row)
            self.menu.tk_popup(event.x_root, event.y_root)

    # ============================================================ data tools
    def export_json(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", initialfile="minifs-filesystem.json",
                                            filetypes=[("JSON", "*.json")], parent=self.root)
        if path:
            try:
                self.store.save(self.fs, path)
                self.status(f"Exported to {path}")
            except FSError as err:
                messagebox.showerror("MiniFS", str(err), parent=self.root)

    def import_json(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")], parent=self.root)
        if not path:
            return
        try:
            self.fs = self.store.import_from(path)
        except FSError as err:
            messagebox.showerror("MiniFS", str(err), parent=self.root)
            return
        self._leave_search()
        self.changed()

    def reset(self):
        if messagebox.askyesno("Reset", "Discard everything and restore the sample file system?",
                               parent=self.root):
            self.fs = VirtualFileSystem.sample()
            self._leave_search()
            self.changed()

    def on_close(self):
        try:
            self.store.save(self.fs)
        except FSError:
            pass
        self.root.destroy()
