"""VirtualFileSystem: the 'brain' of MiniFS.

It owns the tree (Node), the navigation stacks, the hash index, the
recycle bin and the 100 MB virtual disk. Nothing here touches real files.
The GUI only calls these methods - so the logic can be tested without a GUI.
"""
from models.node import Node, now
from dsa.nav_stack import NavigationStack
from dsa.hash_index import HashIndex


class FSError(Exception):
    """Raised for any user mistake (bad name, duplicate, disk full ...)."""


INVALID_CHARS = set('/\\:*?"<>|')


def validate_name(name):
    name = (name or "").strip()
    if not name:
        raise FSError("Name cannot be empty.")
    if name in (".", ".."):
        raise FSError(f"'{name}' is not a valid name.")
    if len(name) > 255:
        raise FSError("Name is too long (max 255 characters).")
    for ch in name:
        if ch in INVALID_CHARS or ord(ch) < 32:
            raise FSError(f"Name cannot contain the character '{ch}'.")
    return name


def is_inside(ancestor, node):
    """True if `node` is `ancestor` itself or somewhere below it."""
    while node is not None:
        if node is ancestor:
            return True
        node = node.parent
    return False


class VirtualFileSystem:
    def __init__(self, capacity_mb=100):
        self.capacity = capacity_mb
        self.root = Node("Root")
        self.cwd = self.root                 # current working directory
        self.nav = NavigationStack()         # Back / Forward  (2 stacks)
        self.index = HashIndex()             # name -> nodes   (hash table)
        self.bin = []                        # recycle bin: dicts {node, orig_path, time}
        self.clipboard = None                # node for copy / cut
        self.clip_mode = None                # "copy" or "cut"
        self.nav.push("/")
        self.index.rebuild(self.root)

    # ------------------------------------------------------------ disk space
    @property
    def used(self):
        in_bin = sum(item["node"].size for item in self.bin)
        return round(self.root.size + in_bin, 2)     # bin items still use space

    @property
    def free(self):
        return round(max(0.0, self.capacity - self.used), 2)

    def _check_space(self, mb):
        if self.used + mb > self.capacity:
            raise FSError("Insufficient virtual storage (100 MB disk is full).")

    # ------------------------------------------------------------ finding paths
    def find(self, path):
        """Absolute path like /College/DSA -> Node (or None)."""
        node = self.root
        for part in [p for p in path.strip().split("/") if p.strip()]:
            if not node.is_folder():
                return None
            node = node.find_child(part)
            if node is None:
                return None
        return node

    def resolve(self, path):
        """Like find(), but also understands relative paths, '.' and '..'."""
        path = path.strip().replace("\\", "/")
        node = self.root if path.startswith("/") else self.cwd
        for part in path.split("/"):
            part = part.strip()
            if part in ("", "."):
                continue
            if part == "..":
                node = node.parent or self.root
                continue
            if not node.is_folder():
                return None
            node = node.find_child(part)
            if node is None:
                return None
        return node

    def is_attached(self, node):
        return is_inside(self.root, node)

    # ------------------------------------------------------------ navigation
    def change_dir(self, folder):
        if not folder.is_folder():
            raise FSError(f"'{folder.name}' is a file, not a folder.")
        self.cwd = folder
        self.nav.push(folder.path)

    def change_dir_path(self, path):
        node = self.resolve(path)
        if node is None:
            raise FSError(f"Folder '{path}' does not exist.")
        self.change_dir(node)

    def _jump(self, step):
        while True:                                   # skip folders that no longer exist
            path = step()
            if path is None:
                return None
            node = self.find(path)
            if node is not None and node.is_folder():
                self.cwd = node
                return node

    def go_back(self):
        return self._jump(self.nav.go_back)

    def go_forward(self):
        return self._jump(self.nav.go_forward)

    def breadcrumb(self):
        """[(name, path), ...] from Root down to the current folder."""
        trail, node = [], self.cwd
        while node is not None:
            trail.append((node.name, node.path))
            node = node.parent
        return list(reversed(trail))

    # ------------------------------------------------------------ create
    def _target(self, parent):
        target = parent or self.cwd
        if not target.is_folder():
            raise FSError("The target is not a folder.")
        return target

    def mkdir(self, name, parent=None):
        name = validate_name(name)
        target = self._target(parent)
        if target.find_child(name):
            raise FSError(f"'{name}' already exists in this folder.")
        node = Node(name, "folder")
        target.add_child(node)
        self.index.add(node)
        return node

    def create_file(self, name, size_mb=1.0, content="", parent=None):
        name = validate_name(name)
        target = self._target(parent)
        if target.find_child(name):
            raise FSError(f"'{name}' already exists in this folder.")
        try:
            size_mb = max(0.01, round(float(size_mb), 2))
        except (TypeError, ValueError):
            raise FSError("Size must be a number, for example 2.5")
        self._check_space(size_mb)
        node = Node(name, "file", size_mb, content)
        target.add_child(node)
        self.index.add(node)
        return node

    # ------------------------------------------------------------ rename
    def rename(self, node, new_name):
        new_name = validate_name(new_name)
        if node is self.root:
            raise FSError("The Root folder cannot be renamed.")
        clash = node.parent.find_child(new_name)
        if clash and clash is not node:
            raise FSError(f"'{new_name}' already exists in this folder.")
        old_path = node.path
        self.index.remove(node)
        node.name = new_name
        node.touch()
        self.index.add(node)
        if node.is_folder():
            self.nav.replace_prefix(old_path, node.path)

    # ------------------------------------------------------------ delete / restore
    def delete(self, node):
        """Soft delete: move to the recycle bin (still uses disk space)."""
        if node is self.root:
            raise FSError("The Root folder cannot be deleted.")
        parent = node.parent
        old_path = node.path
        if is_inside(node, self.cwd):          # we are standing inside what we delete
            self.cwd = parent
        if self.clipboard is not None and is_inside(node, self.clipboard):
            self.clipboard = self.clip_mode = None
        parent.remove_child(node)
        self.index.remove_subtree(node)
        self.nav.remove_prefix(old_path)
        self.nav.push(self.cwd.path)
        self.bin.append({"node": node, "orig_path": parent.path, "time": now()})

    def restore(self, item):
        dest = self.find(item["orig_path"])
        if dest is None or not dest.is_folder():
            dest = self.root                   # original folder gone -> use Root
        node = item["node"]
        node.name = self._unique_name(dest, node.name, node.is_file(), "restored")
        dest.add_child(node)
        self.index.add_subtree(node)
        self.bin.remove(item)
        return node

    def empty_bin(self):
        self.bin.clear()                       # frees the disk space

    # ------------------------------------------------------------ copy / move
    @staticmethod
    def _unique_name(folder, name, is_file, word):
        """notes.txt -> notes_copy_1.txt (if the name is already taken)."""
        if not folder.find_child(name):
            return name
        dot = name.rfind(".")
        stem, ext = (name[:dot], name[dot:]) if (is_file and dot > 0) else (name, "")
        i = 1
        while folder.find_child(f"{stem}_{word}_{i}{ext}"):
            i += 1
        return f"{stem}_{word}_{i}{ext}"

    def _clone(self, node):
        twin = Node(node.name, node.node_type, node._size, node.content)
        for child in node.children:
            kid = self._clone(child)
            kid.parent = twin
            twin.children.append(kid)
        return twin

    def copy(self, node, dest):
        if not dest.is_folder():
            raise FSError("Destination must be a folder.")
        if node is self.root:
            raise FSError("The Root folder cannot be copied.")
        self._check_space(node.size)
        twin = self._clone(node)
        twin.name = self._unique_name(dest, node.name, node.is_file(), "copy")
        dest.add_child(twin)
        self.index.add_subtree(twin)
        return twin

    def move(self, node, dest):
        if node is self.root:
            raise FSError("The Root folder cannot be moved.")
        if not dest.is_folder():
            raise FSError("Destination must be a folder.")
        if is_inside(node, dest):
            raise FSError("A folder cannot be moved into itself.")
        if node.parent is dest:
            raise FSError("The item is already in this folder.")
        if dest.find_child(node.name):
            raise FSError(f"'{node.name}' already exists in the destination.")
        old_path = node.path
        node.parent.remove_child(node)
        dest.add_child(node)
        if node.is_folder():
            self.nav.replace_prefix(old_path, node.path)

    def set_clipboard(self, node, mode):
        self.clipboard, self.clip_mode = node, mode

    def paste(self):
        node = self.clipboard
        if node is None or not self.is_attached(node):
            self.clipboard = self.clip_mode = None
            raise FSError("Clipboard is empty (or the item was deleted).")
        if self.clip_mode == "copy":
            self.copy(node, self.cwd)
        else:
            self.move(node, self.cwd)
            self.clipboard = self.clip_mode = None

    # ------------------------------------------------------------ statistics
    def stats(self):
        files, folders = self.root.count()

        def height(n):
            return 1 + max(height(c) for c in n.children) if n.children else 0

        return {"files": files, "folders": folders + 1, "nodes": files + folders + 1,
                "height": height(self.root), "capacity": self.capacity,
                "used": self.used, "free": self.free, "bin_count": len(self.bin),
                "bin_size": round(sum(i["node"].size for i in self.bin), 2)}

    # ------------------------------------------------------------ save / load
    def to_dict(self):
        return {"version": 1, "capacity_mb": self.capacity, "root": self.root.to_dict(),
                "recycle_bin": [{"node": i["node"].to_dict(), "orig_path": i["orig_path"],
                                 "time": i["time"]} for i in self.bin]}

    @staticmethod
    def from_dict(data):
        try:
            fs = VirtualFileSystem(float(data.get("capacity_mb", 100)))
            fs.root = Node.from_dict(data["root"])
            fs.cwd = fs.root
            fs.bin = [{"node": Node.from_dict(i["node"]), "orig_path": i.get("orig_path", "/"),
                       "time": i.get("time", now())} for i in data.get("recycle_bin", [])]
        except (KeyError, TypeError, ValueError, AttributeError) as err:
            raise FSError(f"Invalid MiniFS data: {err}")
        fs.nav.clear()
        fs.nav.push("/")
        fs.index.rebuild(fs.root)
        return fs

    @staticmethod
    def sample():
        fs = VirtualFileSystem(100)
        docs = fs.mkdir("Documents")
        fs.create_file("notes.txt", 1.5, "Welcome to MiniFS!\nThis is a simulated text file.\n"
                       "DSA concepts: Tree, Stack, Hashing, Recursion.", docs)
        fs.create_file("project.txt", 3.2, "MiniFS capstone project notes:\n- Tree of Nodes\n"
                       "- Back/Forward stacks\n- Hash index\n- DFS/BFS search", docs)
        pics = fs.mkdir("Pictures")
        fs.create_file("vacation.jpg", 12.4, "[simulated image data]", pics)
        fs.create_file("college.png", 8.6, "[simulated image data]", pics)
        college = fs.mkdir("College")
        python = fs.mkdir("Python", college)
        fs.create_file("assignment.py", 0.8, "print('Hello from MiniFS!')\n", python)
        dsa = fs.mkdir("DSA", college)
        fs.create_file("notes.txt", 2.1, "1. Tree = folders\n2. Hash = fast lookup\n"
                       "3. Stack = Back/Forward", dsa)
        fs.mkdir("Downloads")
        return fs
