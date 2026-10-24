"""Navigation history using TWO STACKS (LIFO) - works like a browser's Back / Forward.

back stack    : folders we visited. The TOP is the current folder.
forward stack : folders we went Back from.
"""


class NavigationStack:
    def __init__(self, limit=50):
        self.back = []
        self.forward = []
        self.limit = limit

    def push(self, path):
        """Visit a new folder: push on back stack, clear forward stack. O(1)"""
        if self.back and self.back[-1] == path:
            return
        self.back.append(path)
        if len(self.back) > self.limit:
            self.back.pop(0)
        self.forward.clear()

    def can_back(self):
        return len(self.back) > 1

    def can_forward(self):
        return len(self.forward) > 0

    def go_back(self):
        """Pop from back, push to forward. O(1)"""
        if not self.can_back():
            return None
        self.forward.append(self.back.pop())
        return self.back[-1]

    def go_forward(self):
        """Pop from forward, push to back. O(1)"""
        if not self.can_forward():
            return None
        path = self.forward.pop()
        self.back.append(path)
        return path

    def clear(self):
        self.back.clear()
        self.forward.clear()

    # keep history valid when folders are deleted / renamed
    @staticmethod
    def _under(path, prefix):
        return prefix == "/" or path == prefix or path.startswith(prefix + "/")

    def remove_prefix(self, prefix):
        self.back = [p for p in self.back if not self._under(p, prefix)]
        self.forward = [p for p in self.forward if not self._under(p, prefix)]

    def replace_prefix(self, old, new):
        fix = lambda p: new + p[len(old):] if self._under(p, old) else p
        self.back = [fix(p) for p in self.back]
        self.forward = [fix(p) for p in self.forward]
