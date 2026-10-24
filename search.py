"""Searching the tree: DFS (recursion / stack) and BFS (queue).

Both visit every node once -> O(n) time.
Each visit is recorded in `steps` so the GUI can show the traversal order.
"""
from collections import deque


def tree_search(root, query, method="dfs"):
    q = query.strip().lower()
    results = []      # nodes whose name contains the query
    steps = []        # (node, matched?) in the order they were visited

    def visit(node):
        matched = bool(q) and q in node.name.lower()
        steps.append((node, matched))
        if matched and node is not root:
            results.append(node)

    if method == "bfs":
        queue = deque([root])
        while queue:
            node = queue.popleft()
            visit(node)
            queue.extend(node.children)
    else:
        def dfs(node):
            visit(node)
            for child in node.children:
                dfs(child)
        dfs(root)

    return results, steps
