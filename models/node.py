"""Node: one item (file or folder) in the virtual file system.

The whole file system is an N-ary TREE made of Node objects:
a folder keeps a list of children, a file has no children.
"""
from datetime import datetime


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class Node:
    def __init__(self, name, node_type="folder", size=0.0, content=""):
        self.name = name
        self.node_type = node_type            # "folder" or "file"
        self._size = round(float(size), 2) if node_type == "file" else 0.0
        self.content = content
        self.created = now()
        self.modified = self.created
        self.parent = None
        self.children = []

    # ---- basic info ----
    def is_folder(self):
        return self.node_type == "folder"

    def is_file(self):
        return self.node_type == "file"

    @property
    def size(self):
        """File: its own size. Folder: sum of everything inside (recursion)."""
        if self.is_file():
            return round(self._size, 2)
        return round(sum(child.size for child in self.children), 2)

    @property
    def path(self):
        """Walk up through parents to build e.g. /College/DSA/notes.txt"""
        if self.parent is None:
            return "/"
        parts = []
        node = self
        while node.parent is not None:
            parts.append(node.name)
            node = node.parent
        return "/" + "/".join(reversed(parts))

    def extension(self):
        if self.is_folder():
            return "folder"
        dot = self.name.rfind(".")
        return self.name[dot:].lower() if dot > 0 else "file"

    def touch(self):
        self.modified = now()
        if self.parent:
            self.parent.modified = self.modified

    # ---- tree operations ----
    def find_child(self, name):
        """Look for a direct child by name (not case sensitive)."""
        wanted = name.strip().lower()
        for child in self.children:
            if child.name.lower() == wanted:
                return child
        return None

    def add_child(self, node):
        if not self.is_folder():
            raise ValueError("Cannot add an item inside a file.")
        node.parent = self
        self.children.append(node)
        self.touch()

    def remove_child(self, node):
        self.children.remove(node)
        node.parent = None
        self.touch()

    def count(self):
        """Return (files, folders) inside this node, using recursion."""
        files = folders = 0
        for child in self.children:
            if child.is_folder():
                folders += 1
                f, d = child.count()
                files += f
                folders += d
            else:
                files += 1
        return files, folders

    # ---- JSON conversion ----
    def to_dict(self):
        return {
            "name": self.name, "type": self.node_type, "size": self._size,
            "content": self.content, "created": self.created, "modified": self.modified,
            "children": [c.to_dict() for c in self.children],
        }

    @staticmethod
    def from_dict(data):
        node = Node(data["name"], data.get("type", "folder"), data.get("size", 0),
                    data.get("content", ""))
        node.created = data.get("created", node.created)
        node.modified = data.get("modified", node.modified)
        for child_data in data.get("children", []):
            child = Node.from_dict(child_data)
            child.parent = node
            node.children.append(child)
        return node
