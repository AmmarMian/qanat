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
from rich.tree import Tree
from ..utils.misc import walk_directory


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
