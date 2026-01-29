#!/usr/bin/env python3
"""
Author : Xinyuan Chen <45612704+tddschn@users.noreply.github.com>
Date   : 2022-06-26
Purpose: Clean ~/Library cache on macOS
"""

import argparse
from . import __version__
from .utils import (
    clean_library_cache,
    pypoetry_cache_cleanup,
    pypoetry_cleanup,
    vscode_cleanup_workspace_storage,
)

__app_name__ = "mac_clean_library_cache"


def get_args():
    """Get command-line arguments"""

    parser = argparse.ArgumentParser(
        prog=__app_name__,
        description="Clean ~/Library cache on macOS",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    sp = parser.add_subparsers()
    parser_clean_library_cache = sp.add_parser(
        "clean-library-cache",
        aliases=["clc"],
        help="Cleans library cache, with set exceptions",
    )
    parser_clean_library_cache.set_defaults(func=clean_library_cache)

    parser_vscode_cleanup_workspace_storage = sp.add_parser(
        "vscode-cleanup-workspace-storage",
        aliases=["vsc"],
        help="remove vscode workspace storage on mac",
    )
    parser_vscode_cleanup_workspace_storage.set_defaults(
        func=vscode_cleanup_workspace_storage
    )

    parser_pypoetry_cache_cleanup = sp.add_parser(
        "pypoetry-cache-cleanup", aliases=["pc"], help="remove pypoetry cache on mac"
    )
    parser_pypoetry_cache_cleanup.set_defaults(func=pypoetry_cache_cleanup)

    parser_pypoetry_cleanup = sp.add_parser(
        "pypoetry-cleanup", aliases=["poe"], help="remove pypoetry on mac"
    )
    parser_pypoetry_cleanup.set_defaults(func=pypoetry_cleanup)
    for p in set(sp.choices.values()):
        # print(p)
        # for every parser p registered on sp
        p.add_argument("-n", "--dry-run", action="store_true", help="dry run")
        p.add_argument(
            "--ignore-FileNotFoundError",
            dest="ignore_filenotfounderror",
            action="store_true",
            help=(
                "Ignore FileNotFoundError while removing directory trees (log to stderr and continue). Implied by --ignore-rmtree-error."
            ),
        )
        p.add_argument(
            "--ignore-rmtree-error",
            dest="ignore_rmtree_error",
            action="store_true",
            help=(
                "Ignore errors from shutil.rmtree (log to stderr and continue; may leave undeleted files)"
            ),
        )

    return parser, parser.parse_args()


def main() -> None:
    parser, args = get_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
