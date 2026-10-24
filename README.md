# MiniFS — Virtual File System Simulator

MiniFS is a desktop application built with **Python and Tkinter** that simulates a file system inside the application. It demonstrates how file-system concepts and common data structures work together in a practical project.

> **Safety note:** MiniFS manages a virtual file system and stores its app data in `minifs_data.json`. It is not intended to manage or modify your computer's real files.

## Features

- Create, open, rename, copy, move, and delete virtual files and folders
- Navigate folders with Back, Forward, and Up controls
- Search using Depth-First Search (DFS) or Breadth-First Search (BFS)
- Recycle Bin with restore support
- Virtual disk capacity tracking
- Built-in text editor and mini terminal
- Data Structure and Algorithm (DSA) visualizer
- Import and export file-system data as JSON
- Sample/demo file system

## Requirements

- Python 3.8 or newer
- Tkinter (usually included with Python)

On Ubuntu/Debian, if Tkinter is missing, install it with:

```bash
sudo apt update
sudo apt install python3-tk
```

## Run the application

Clone the repository and open its folder:

```bash
git clone https://github.com/harsh2108-coder/MiniFS.git
cd MiniFS
python main.py
```

On some systems, use `python3 main.py` instead.

## Run the tests

From the repository root:

```bash
python -m unittest discover tests -v
```

The core tests do not require the GUI to be opened.

## Project structure

```text
MiniFS/
├── main.py                 # Application entry point
├── models/
│   ├── node.py             # File/folder nodes
│   └── vfs.py              # Virtual file-system operations
├── dsa/
│   ├── nav_stack.py        # Back/Forward navigation stacks
│   ├── hash_index.py       # Name lookup index
│   └── search.py           # DFS and BFS search
├── storage/
│   └── json_store.py       # JSON save/load and import/export support
├── gui/                    # Tkinter windows and interface
└── tests/
    └── test_core.py        # Automated core tests
```

## Data structures demonstrated

| Concept | Use in MiniFS |
|---|---|
| N-ary tree | Represents folders and their children |
| Stacks | Supports Back and Forward navigation |
| Hash table (`dict`) | Indexes nodes by name |
| Queue | Supports breadth-first search |
| Recursion | Traverses folders and calculates directory information |
| List | Stores items in the Recycle Bin |

## Learning goals

MiniFS is intended as a learning/capstone project for practicing Python, GUI development, object-oriented programming, data structures and algorithms, JSON persistence, and unit testing.

## License

No license has been specified yet. Add a `LICENSE` file if you want to grant others explicit permission to reuse or modify this project.
