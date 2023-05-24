# ========================================
# FileName: cache.py
# Date: 24 mai 2023 - 10:34
# Author: Ammar Mian
# Email: ammar.mian@univ-smb.fr
# GitHub: https://github.com/ammarmian
# Brief: Cache management
# =========================================

import os
import pathlib
import shutil

import rich
from rich.filesize import decimal
from rich.markup import escape
from rich.text import Text
from rich.tree import Tree


def walk_directory(directory: pathlib.Path, tree: Tree) -> None:
    """Recursively build a Tree with directory contents.
    From: https://github.com/Textualize/rich/blob/master/examples/tree.py
    Acessed: 24 mai 2023 - 10:34

    :param directory: The directory to walk
    :type directory: pathlib.Path

    :param tree: The tree to build
    :type tree: Tree
    """
    # Sort dirs first then by filename
    paths = sorted(
        pathlib.Path(directory).iterdir(),
        key=lambda path: (path.is_file(), path.name.lower()),
    )
    for path in paths:
        # Remove hidden files
        if path.name.startswith("."):
            continue
        if path.is_dir():
            style = "dim" if path.name.startswith("__") else ""
            branch = tree.add(
                f"[bold magenta]:open_file_folder: "
                f"[link file://{path}]{escape(path.name)}",
                style=style,
                guide_style=style,
            )
            walk_directory(path, branch)
        else:
            text_filename = Text(path.name, "green")
            text_filename.highlight_regex(r"\..*$", "bold red")
            text_filename.stylize(f"link file://{path}")
            file_size = path.stat().st_size
            text_filename.append(f" ({decimal(file_size)})", "blue")
            icon = "🐍 " if path.suffix == ".py" else "📄 "
            tree.add(Text(icon) + text_filename)


def cache_list():
    """List the cache contents
    """
    cache_directory = pathlib.Path(".qanat/cache")
    tree = Tree(
            f"[bold blue]:open_file_folder: "
            f"[link file://{cache_directory}]{escape(cache_directory.name)}",
            guide_style="bold bright_blue")
    walk_directory(cache_directory, tree)
    rich.print(tree)


def command_clean():
    """Clean the cache
    """
    cache_directory = pathlib.Path(".qanat/cache")
    shutil.rmtree(cache_directory)
    os.mkdir(cache_directory)
    rich.print("Cache cleaned.")


def command_status():
    """Print the status of the cache
    """

    cache_directory = pathlib.Path(".qanat/cache")
    cache_size = sum(
            f.stat().st_size for f in cache_directory.glob("**/*")
            if f.is_file())
    rich.print(f"Cache size: {decimal(cache_size)}")
    rich.print(f"Cache location: {cache_directory}")

    if cache_size > 0:
        rich.print("Cache contents:")
        cache_list()
