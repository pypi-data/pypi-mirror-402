# Copyright (c) 2024 Matthew Baker.  All rights reserved.  Licenced under the
# Apache Licence 2.0.  See LICENSE file
import unittest
import shutil
import os
from typing import List
from argparse import Namespace
import configurematic


def read_file(filename):
    lines: List[str] = []
    with open(filename, "r") as f:
        for line in f:
            lines.append(line)
    return lines


class TypedDictConfigurematic(unittest.TestCase):

    def check(self, resursive: bool):
        self.assertTrue(os.path.isfile("out/testdata/dir1/file1"))
        self.assertTrue(os.path.isfile("out/testdata/dir1/dir2/file2"))
        self.assertTrue(os.path.isfile("out/testdata/dir1/dir2/file3"))
        self.assertFalse(os.path.isfile("out/testdata/dir1/dir2/file4"))

        self.assertFalse(os.path.isfile("out/testdata/dir1/file1.old"))
        self.assertFalse(os.path.isfile("out/testdata/dir1/dir2/file2.old"))
        self.assertFalse(os.path.isfile("out/testdata/dir1/dir2/file3.old"))

        file1 = read_file("out/testdata/dir1/file1")
        self.assertEqual(len(file1), 6)
        self.assertEqual(file1[0].strip(), 'ABC')
        self.assertEqual(file1[1].strip(), 'XXX="abc"')
        self.assertEqual(file1[2].strip(), 'YYY=true')
        self.assertEqual(file1[3].strip(), 'XXXYYY="abctrue"')
        self.assertEqual(file1[4].strip(), 'XXXsYYY="abc true"')
        if (resursive):
            self.assertEqual(file1[5].strip(), 'AAA=abc')
        else:
            self.assertEqual(file1[5].strip(), 'AAA=__VAR1__')

        file2 = read_file("out/testdata/dir1/dir2/file2")
        self.assertEqual(len(file2), 3)
        self.assertEqual(file2[0].strip(), 'ABC')
        self.assertEqual(file2[1].strip(), 'XXX="abc"')
        self.assertEqual(file2[2].strip(), 'ZZZ=123')

        file3 = read_file("out/testdata/dir1/dir2/file3")
        self.assertEqual(len(file3), 3)
        self.assertEqual(file3[0].strip(), 'ABC')
        self.assertEqual(file3[1].strip(), 'YYY=true')
        self.assertEqual(file3[2].strip(), 'ZZZ=123')

    def test_nonrecursive(self):
        if (os.path.isdir("out")):
            shutil.rmtree("out")
        args = Namespace()
        args.files = "testdata/files.txt"
        args.conf_file = "testdata/conf1.txt"
        args.outdir = "out"
        args.prefix = "example-"
        args.backup_ext = ".old"
        args.delimeter = "__"
        args.silent = True
        args.recursive = False
        files = configurematic.get_filenames(args.files)

        configurematic.configure(files, args)

        self.check(False)

        configurematic.configure(files, args)
        self.assertTrue(os.path.isfile("out/testdata/dir1/file1.old"))
        self.assertTrue(os.path.isfile("out/testdata/dir1/dir2/file2.old"))
        self.assertTrue(os.path.isfile("out/testdata/dir1/dir2/file3.old"))

        if (os.path.isdir("out")):
            shutil.rmtree("out")

    def test_recursive(self):
        if (os.path.isdir("out")):
            shutil.rmtree("out")
        args = Namespace()
        args.files = "testdata/files.txt"
        args.conf_file = "testdata/conf1.txt"
        args.outdir = "out"
        args.prefix = "example-"
        args.backup_ext = ".old"
        args.delimeter = "__"
        args.silent = True
        args.recursive = True
        files = configurematic.get_filenames(args.files)

        configurematic.configure(files, args)

        self.check(True)

        configurematic.configure(files, args)
        self.assertTrue(os.path.isfile("out/testdata/dir1/file1.old"))
        self.assertTrue(os.path.isfile("out/testdata/dir1/dir2/file2.old"))
        self.assertTrue(os.path.isfile("out/testdata/dir1/dir2/file3.old"))

        if (os.path.isdir("out")):
            shutil.rmtree("out")
