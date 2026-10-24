"""Hash index: file name -> list of nodes with that name.

A Python dict IS a hash table, so lookup by exact name is O(1) on average
(instead of searching the whole tree, which is O(n)).
"""


class HashIndex:
    def __init__(self):
        self.table = {}

    @staticmethod
    def _key(name):
        return name.strip().lower()

    def add(self, node):
        bucket = self.table.setdefault(self._key(node.name), [])
        if node not in bucket:
            bucket.append(node)

    def remove(self, node):
        key = self._key(node.name)
        bucket = self.table.get(key)
        if bucket and node in bucket:
            bucket.remove(node)
            if not bucket:
                del self.table[key]

    def lookup(self, name):
        return list(self.table.get(self._key(name), []))

    def add_subtree(self, node):
        self.add(node)
        for child in node.children:
            self.add_subtree(child)

    def remove_subtree(self, node):
        self.remove(node)
        for child in node.children:
            self.remove_subtree(child)

    def rebuild(self, root):
        self.table.clear()
        self.add_subtree(root)

    def total_nodes(self):
        return sum(len(b) for b in self.table.values())
