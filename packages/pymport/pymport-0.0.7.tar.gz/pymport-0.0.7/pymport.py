# -*- coding: utf-8 -*-

# Based on "importchecker"
# https://github.com/zopefoundation/importchecker.git

import ast
import contextlib
import functools
import itertools
import linecache
import logging
import multiprocessing
import operator
import os
import pathlib
import re
import sys

# Ignore, at least, these directory basenames (default directories to ignore).
default_ignore_dirs = (
    # Common virtual environment directories
    "venv",
    "env",
    ".venv",
    ".env",
    # Common build directories
    ".git",  # Git
    ".hg",  # Mercurial
    ".pytest_cache",  # Pytest cache
    ".ruff_cache",  # Ruff cache
    "__pycache__",  # Python cache
)


def uniques(function, /):

    @functools.wraps(function)
    def worker(*args, **kwargs):
        bag = set()
        for obj in function(*args, **kwargs):
            if obj not in bag:
                bag.add(obj)
                yield obj

    return worker


def _make_noqa(filename: str, /):

    def worker(lineno: int, /) -> bool:
        line = linecache.getline(filename, lineno)
        return machine(line) is not None

    # Use same error code as Pyflakes, Ruff.
    machine = re.compile("#\\s+noqa(?::\\s+F401)?\\s*$").search
    return worker


@uniques
def find_dotted_names(root: ast.AST, /):
    """Find dotted names in an AST tree."""

    if isinstance(root, ast.Attribute):
        dotted = list()
        node = root
        while isinstance(node, ast.Attribute):
            dotted.append(node.attr)
            node = node.value

        if isinstance(node, ast.Name):
            joiner = ".".join
            dotted.append(node.id)
            dotted.reverse()
            parts = itertools.chain(
                (joiner(dotted[:i]) for i in range(1, len(dotted))),
                (joiner(dotted),),
            )
            yield tuple(parts)
            return
    elif isinstance(root, ast.Name):
        yield (root.id,)
        return

    for child in ast.iter_child_nodes(root):
        yield from find_dotted_names(child)


class ImportFinder(ast.NodeVisitor):

    def __init__(self, /):
        self._map = list()

    def __iter__(self, /):
        yield from self._map

    def visit_ImportFrom(self, stmt, /):
        module_name = stmt.module
        if module_name == "__future__":
            # we don't care what's imported from the future
            return
        names = list()
        for alias in stmt.names:
            # we don't care about from import *
            orig_name, as_name = alias.name, alias.asname
            if orig_name == "*":
                continue

            name = as_name or orig_name
            names.append(name)
        self._map.append(
            (
                module_name,
                {
                    "names": tuple(names),
                    "lineno": stmt.lineno,
                },
            ),
        )

        for child_node in ast.iter_child_nodes(stmt):
            self.generic_visit(child_node)

    def visit_Import(self, stmt, /):
        for alias in stmt.names:
            orig_name, as_name = alias.name, alias.asname
            name = as_name or orig_name
            self._map.append(
                (
                    orig_name,
                    {
                        "names": (name,),
                        "lineno": stmt.lineno,
                    },
                ),
            )

        for child_node in ast.iter_child_nodes(stmt):
            self.generic_visit(child_node)


def find_imports(tree: ast.AST, /):
    """Find import statements in module and put the result in a mapping."""

    finder = ImportFinder()
    finder.visit(tree)
    for _, info in finder:
        lineno = info["lineno"]
        for name in info["names"]:
            yield (name, lineno)


def unused_imports(filename: pathlib.Path, /) -> tuple:

    def found_candidates(root: ast.AST, /):
        mapper = dict(find_imports(root))
        modules = dict.fromkeys(mapper, 0)
        for stmt in find_dotted_names(root):
            for attempt in reversed(stmt):
                if attempt in mapper:
                    modules[attempt] += 1
                    break
        return (modules, mapper.items())

    def worker(root: ast.AST, /):
        modules, candidates = found_candidates(root)
        name = str(filename)
        ignored = _make_noqa(name)
        getter = operator.itemgetter(1)  # sort by "lineno"
        for key, lineno in sorted(candidates, key=getter):
            if not modules[key] and not ignored(lineno):
                yield name, lineno, key

    try:
        tree = ast.parse(filename.read_bytes(), filename=str(filename))
    except SyntaxError:
        result = None
    else:
        result = tuple(worker(tree))
    return result or None


def walker(ignore_dirs, filenames, quiet, /):
    """Generator yielding python source file names."""

    suffixes = (".py", "pyw")
    ignore = frozenset(ignore_dirs).intersection
    valid = operator.methodcaller("endswith", suffixes)
    for root in filenames:
        if root.is_dir():
            for parent, dirs, files in os.walk(root):
                source = pathlib.Path(parent)
                yield from (source / name for name in filter(valid, files))
                for name in ignore(dirs):
                    dirs.remove(name)
        elif root.is_file():
            # Accept user input, do not filter out by extension
            yield root
        elif not quiet:
            logging.warning("Unknown file: %s", root)


def dump_results(quiet, results, /) -> int:
    fmt = "{}:{}: {}".format
    result = 0
    errors = filter(None, itertools.chain(results))
    for info in itertools.chain.from_iterable(errors):
        result = 1
        if not quiet:
            print(fmt(*info))

    if not quiet and not result:
        print("All checks passed!")
    return result


def main(context, /) -> int:
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    pool = multiprocessing.Pool()
    with contextlib.closing(pool):
        chunksize = os.cpu_count() or 1
        items = walker(context["ignore"], context["files"], context["quiet"])
        results = pool.imap(unused_imports, sorted(items), chunksize=chunksize)
    pool.join()
    return dump_results(context["quiet"], results)


def do_help(*, header=None):
    filename = pathlib.Path(__file__).name
    lines = (
        "%s v.%s" % (filename, "1.0"),
        "Detect unused imports.",
        "Use a comment like '# noqa: unused-import' to ignore the line.",
        "",
        "Usage: %s [--help] [--quiet] [--ignore=DIR] [FILE]..." % filename,
        "",
        "--quiet Decrease verbosity.",
        "",
        "DIR:    Directory basename to ignore. This option can be",
        "        specified multiple times. Defaults to:",
        "        {}".format(", ".join(default_ignore_dirs)),
        "FILE:   File or directory.",
    )

    for line in itertools.chain(header or "", lines):
        print(line)

    sys.exit(1)


def do_get_arguments(arguments: list, /) -> dict:
    files = list()
    context = {
        "quiet": False,
        "files": files,
        "ignore": list(default_ignore_dirs),
    }
    for arg in arguments:
        if arg == "--help":
            do_help()
        elif arg == "--quiet":
            context["quiet"] = True
        elif arg.startswith("--ignore="):
            context["ignore"].append(arg.split("=", maxsplit=1)[1])
        else:
            files.append(pathlib.Path(arg).expanduser())

    if not files:
        header = (
            "Need at least one file or directory to check.",
            "",
        )
        do_help(header=header)

    return context


def entrypoint():
    return main(do_get_arguments(sys.argv[1:]))


if __name__ == "__main__":
    sys.exit(entrypoint())
