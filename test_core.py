"""Run with:  python -m unittest discover tests -v   (no GUI needed)"""
import os
import tempfile
import unittest

from models.vfs import VirtualFileSystem, FSError
from dsa.search import tree_search
from storage.json_store import JsonStore


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.fs = VirtualFileSystem.sample()

    def test_tree_and_paths(self):
        node = self.fs.find("/College/DSA/notes.txt")
        self.assertEqual(node.path, "/College/DSA/notes.txt")
        self.assertEqual(self.fs.find("/College").size, 2.9)

    def test_duplicate_and_invalid_names(self):
        with self.assertRaises(FSError):
            self.fs.mkdir("documents")            # same name, different case
        with self.assertRaises(FSError):
            self.fs.mkdir("bad/name")
        with self.assertRaises(FSError):
            self.fs.mkdir("   ")

    def test_disk_quota(self):
        with self.assertRaises(FSError):
            self.fs.create_file("huge.bin", 500)

    def test_back_forward_stacks(self):
        self.fs.change_dir_path("/College")
        self.fs.change_dir_path("/College/DSA")
        self.assertEqual(self.fs.go_back().path, "/College")
        self.assertEqual(self.fs.go_back().path, "/")
        self.assertEqual(self.fs.go_forward().path, "/College")
        self.fs.change_dir_path("/Pictures")           # new visit clears forward
        self.assertFalse(self.fs.nav.can_forward())

    def test_hash_lookup(self):
        self.assertEqual(len(self.fs.index.lookup("NOTES.TXT")), 2)

    def test_dfs_bfs_find_same_items_in_different_order(self):
        dfs, dsteps = tree_search(self.fs.root, "notes", "dfs")
        bfs, bsteps = tree_search(self.fs.root, "notes", "bfs")
        self.assertEqual({n.path for n in dfs}, {n.path for n in bfs})
        self.assertEqual(len(dsteps), len(bsteps))
        self.assertNotEqual([s[0].path for s in dsteps], [s[0].path for s in bsteps])

    def test_recycle_bin_keeps_space_until_emptied(self):
        used = self.fs.used
        node = self.fs.find("/Pictures/vacation.jpg")
        self.fs.delete(node)
        self.assertIsNone(self.fs.find("/Pictures/vacation.jpg"))
        self.assertEqual(self.fs.used, used)           # still counted
        self.assertEqual(self.fs.index.lookup("vacation.jpg"), [])
        item = self.fs.bin[0]
        self.fs.restore(item)
        self.assertIsNotNone(self.fs.find("/Pictures/vacation.jpg"))
        self.assertEqual(len(self.fs.index.lookup("vacation.jpg")), 1)
        self.fs.delete(self.fs.find("/Pictures/vacation.jpg"))
        self.fs.empty_bin()
        self.assertLess(self.fs.used, used)

    def test_delete_current_folder_moves_up(self):
        self.fs.change_dir_path("/College/DSA")
        self.fs.delete(self.fs.find("/College"))
        self.assertEqual(self.fs.cwd.path, "/")

    def test_copy_and_move(self):
        notes = self.fs.find("/Documents/notes.txt")
        self.fs.copy(notes, self.fs.find("/Documents"))
        self.assertIsNotNone(self.fs.find("/Documents/notes_copy_1.txt"))
        self.fs.move(self.fs.find("/Documents/project.txt"), self.fs.find("/Downloads"))
        self.assertIsNotNone(self.fs.find("/Downloads/project.txt"))
        with self.assertRaises(FSError):
            self.fs.move(self.fs.find("/College"), self.fs.find("/College/DSA"))

    def test_rename_updates_hash_and_history(self):
        self.fs.change_dir_path("/College/DSA")
        self.fs.rename(self.fs.find("/College"), "Uni")
        self.assertEqual(self.fs.cwd.path, "/Uni/DSA")
        self.assertEqual(self.fs.index.lookup("college"), [])
        self.assertEqual(len(self.fs.index.lookup("uni")), 1)
        self.assertTrue(all(p.startswith("/Uni") or p == "/" for p in self.fs.nav.back))

    def test_json_round_trip(self):
        self.fs.delete(self.fs.find("/Pictures/college.png"))
        with tempfile.TemporaryDirectory() as d:
            store = JsonStore(os.path.join(d, "fs.json"))
            store.save(self.fs)
            again = store.load()
        self.assertEqual(again.used, self.fs.used)
        self.assertEqual(len(again.bin), 1)
        self.assertIsNotNone(again.find("/College/DSA/notes.txt"))

    def test_corrupt_save_file_is_handled(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "fs.json")
            with open(path, "w") as f:
                f.write("{ not json")
            self.assertIsNone(JsonStore(path).load())
            self.assertTrue(os.path.exists(path + ".corrupt.bak"))


if __name__ == "__main__":
    unittest.main()
