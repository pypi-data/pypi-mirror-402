# Copyright (c) 2024 Matthew Baker.  All rights reserved.  Licenced under the
# Apache Licence 2.0.  See LICENSE file
import argparse
import sys
import os
import re
import shutil
from typing import Mapping, List, Dict
from dotenv import dotenv_values

MAX_ITERATIONS = 10


def get_var_names(conffile: str) -> List[str]:
    varnames: List[str] = []
    with open(conffile, "r") as f:
        incl = re.compile(r"^[A-Za-z_][A-Za-z0-9_]+\s*=")
        for line in f:
            line = line.strip()
            if (line == "" or not incl.match(line)):
                continue
            parts = line.split("=", 2)
            varnames.append(parts[0])
    return varnames


def get_filenames(listfile: str) -> List[str]:
    """
    Splits input file into an array, one value per row.
    Leading and trailing whitespacve are ignored as are any lines
    that start in # (after stripping whitespace)
    """
    files: List[str] = []
    incl = re.compile(r"^\s*[^#]")
    with open(listfile, "r") as f:
        for line in f:
            line = line.strip()
            if (line != "" and incl.match(line)):
                files.append(line)
    return files


def find_all(a_str, sub):
    positions: List[int] = []
    start = 0
    while True:
        start = a_str.find(sub, start)
        if start == -1:
            return positions
        positions.append(start)
        start += len(sub)


def append_fragments(fragments: List[str],
                     line: str,
                     templates: Mapping[str, str],
                     start: int,
                     pos: int):
    end = pos
    fragment1 = line[start:pos]
    fragment2 = None
    for name in templates:
        if fragment1.startswith(name):
            end = len(name)
            if (end < len(fragment1)):
                fragment2 = fragment1[end:]
                fragment1 = fragment1[:end]
            break
    fragments.append(fragment1)
    if (fragment2 is not None):
        fragments.append(fragment2)


def splitOnVariables(line: str, templates: Mapping[str, str]):
    positions: List[int] = []
    for name in templates:
        positions = [*positions, *find_all(line, name)]
    positions.sort()
    start = 0
    fragments: List[str] = []
    for pos in positions:
        if pos == start:
            continue
        append_fragments(fragments, line, templates, start, pos)
        start = pos
    if (start < len(line)):
        append_fragments(fragments, line, templates, start, len(line))
    return fragments


def replace(filename: str,
            variables: Mapping[str, str | None],
            templates: Mapping[str, str],
            args: argparse.Namespace):

    basename = os.path.basename(filename)
    dirname = os.path.dirname(filename)
    if (dirname == ""):
        template_filename = args.prefix + basename
    else:
        template_filename = os.path.join(dirname, args.prefix + basename)
    output_filename = os.path.join(args.outdir, filename)
    backup_filename = output_filename + args.backup_ext
    output_exists = os.path.isfile(output_filename)

    if (output_exists and args.backup_ext != ""):
        shutil.copyfile(output_filename, backup_filename)

    os.makedirs(os.path.dirname(output_filename), exist_ok=True)

    with open(output_filename, "w") as outfile, \
            open(template_filename, "r") as infile:
        for line in infile:
            replaced = False
            first = True
            count = 0
            while (first or (args.recursive and replaced)):
                count += 1
                if (count >= MAX_ITERATIONS):
                    break  # otherwise we may have an infinite loop
                first = False
                replaced = False
                fragments = splitOnVariables(line, templates)
                new_fragments: List[str] = []
                for frag in fragments:
                    if (frag in templates):
                        replaced = True
                        name = templates[frag]
                        val = ""
                        val_or_none = variables[name]
                        if (val_or_none is not None):
                            val = val_or_none
                        frag = val
                    new_fragments.append(frag)
                newline = "".join(new_fragments)
                line = newline
            outfile.write(newline)


def configure(files: List[str], args: argparse.Namespace):
    vars = dotenv_values(args.conf_file)
    varnames = get_var_names(args.conf_file)
    templates: Dict[str, str] = {}
    for name in varnames:
        templates[args.delimeter+name+args.delimeter] = name

    for file in files:
        if (not args.silent):
            print(file, "...")
        replace(file, vars, templates, args)


def main():

    parser = argparse.ArgumentParser(
        prog='configurematic',
        description='Put configuration from one file into multiple files',
    )
    parser.add_argument('filenames', nargs='*',
                        help='Template files (without prefix)')
    parser.add_argument('-c', '--conf-file', default="config.env",
                        help='Env file with variable settings')
    parser.add_argument('-p', '--prefix', default="example-",
                        help='Template files begin with this')
    parser.add_argument('-f', '--files', default="files.txt",
                        help='List of template files (without prefix)')
    parser.add_argument('-o', '--outdir', nargs='?', default=".",
                        help='Where to write output files')
    parser.add_argument('-b', '--backup-ext', default=".old",
                        help='For previous version of output files')
    parser.add_argument('-q', '--silent', action='store_true',
                        help="Don't print anything to stdout")
    parser.add_argument('-r', '--recursive', action='store_true',
                        help="Allow template variable to reference others")
    parser.add_argument('-d', '--delimeter', default="__",
                        help="Variable instances have this prefis and suffix")
    args = parser.parse_args()
    if (len(args.filenames) == 0 and args.files is None):
        print("Please either specify filenames or -f", file=sys.stderr)
        parser.print_usage()
        sys.exit(1)

    files = args.filenames if len(args.filenames) > 0 \
        else get_filenames(args.files)

    configure(files, args)


if __name__ == "__main__":
    main()
