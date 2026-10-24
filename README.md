# MiniFS - A Python-Based Virtual File System Simulator

A desktop app (Python + Tkinter) that simulates a file system **inside memory**.
It never touches your real files. Data is saved in `minifs_data.json`.

## Run it
```
python main.py
```
Needs only Python 3.8+ (Tkinter comes with Python; on Linux: `sudo apt install python3-tk`).
Run the tests (no GUI needed): `python -m unittest discover tests -v`

## What you can do
Create / rename / copy / cut / paste / delete folders and files, open a text editor,
Back / Forward / Up navigation, search (DFS or BFS), Recycle Bin with restore,
100 MB virtual disk, DSA Visualizer, mini terminal, JSON export/import, demo mode.

## Project layout (explain it in this order)
```
main.py                 starts the app
models/node.py          Node  -> one file/folder (the TREE)
models/vfs.py           VirtualFileSystem -> all the rules (create, delete, copy, quota ...)
dsa/nav_stack.py        Back/Forward using 2 STACKS
dsa/hash_index.py       name -> nodes using a HASH TABLE (dict)
dsa/search.py           DFS (recursion) and BFS (queue)
storage/json_store.py   save / load JSON
gui/                    windows only (no logic): app, dsa_window, bin_window, editor, terminal, demo
tests/test_core.py      12 automatic tests of the logic
```
Idea to say in the viva: **GUI = screen, models + dsa = brain.** The GUI just calls the brain.

## Data structures used
| Structure | Where | Why |
|---|---|---|
| N-ary Tree | `Node.children` | folders contain files/folders |
| Stack (x2) | `NavigationStack` | Back / Forward (LIFO) |
| Hash table | `HashIndex` (dict) | find a name in O(1) average |
| Queue | BFS in `search.py` | visit level by level |
| Recursion | size, count, DFS, path | tree is naturally recursive |
| List | recycle bin | items wait to be restored |

## Viva questions (short answers)
1. **Why a tree?** Folders inside folders is a parent-child hierarchy, exactly a tree.
2. **How is a path found?** Split `/a/b/c` and move down one child per part: O(d*k).
3. **Why two stacks for Back/Forward?** Back pops from one and pushes to the other, both O(1).
4. **Why clear Forward on a new folder?** Same as a browser: a new visit starts a new future.
5. **What is the hash index for?** Exact name lookup in O(1) average instead of scanning O(n).
6. **Is a Python dict a hash table?** Yes: the key is hashed to find its bucket.
7. **DFS vs BFS?** DFS goes deep first (recursion/stack), BFS goes level by level (queue). Both O(n).
8. **How is folder size computed?** Recursively: sum of the sizes of its children.
9. **What does delete do?** Soft delete: node moves to the Recycle Bin, removed from the hash index, still uses disk space.
10. **How does restore work?** Goes back to the saved original folder (or Root if it no longer exists); renames if the name is taken.
11. **How is the 100 MB limit enforced?** `used = tree size + bin size`; creating/copying checks `used + new <= capacity`.
12. **How do you stop a folder moving into itself?** Walk up the parents of the destination; if we meet the moved folder, refuse.
13. **How is data saved?** The tree is turned into nested dicts (`to_dict`) and written as JSON; loading rebuilds Nodes (`from_dict`).
14. **What if the save file is corrupt?** It is renamed to `.corrupt.bak` and a fresh sample file system starts.
15. **Why separate GUI and logic?** Easier to test and explain; the logic runs without any window.
