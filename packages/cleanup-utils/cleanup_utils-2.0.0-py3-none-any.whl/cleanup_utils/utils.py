#!/usr/bin/env python3

from argparse import Namespace
import tempfile
from pathlib import Path
import sys

# from utils_tddschn.sync.utils import strtobool
from collections import deque
from .config import (
    read_config,
    library_cache_path,
    pypoetry_path,
    pypoetry_cache_path,
    vscode_user_workspaceStorage_dir,
    vscode_insiders_user_workspaceStorage_dir,
)


# def rmtree_os_walk(directory):
#     # this should be faster than rmtree:
#     # https://stackoverflow.com/a/52324968/11133602
#     for root, dirs, files in os.walk(directory, topdown=False):
#         for file in files:
#             os.remove(os.path.join(root, file))
#         for dir in dirs:
#             os.rmdir(os.path.join(root, dir))
#     # do not rmdir directory itself
#     # os.rmdir(directory)


def remove_tree_with_exceptions(
    tree_path: Path,
    exceptions: list[str] = [],
    dry_run: bool = False,
    ignore_filenotfounderror: bool = False,
    ignore_rmtree_error: bool = False,
) -> None:
    """rmtree tree_path, and do not touch the paths in exceptions.
    move the exceptions to a temp dir instead.

    Args:
        tree_path (Path): path to move
        exceptions (list[Path]): a list of paths to not touch
    """

    # only select those that exists
    # exceptions_existed = list(
    #     filter(lambda path: path.exists(),
    #            map(lambda exception: tree_path / exception, exceptions)))
    # check existence
    if not tree_path.exists():
        print(f"{tree_path} does not exist", file=sys.stderr)
        return

    def validate_exception(exception: str) -> bool:
        full_path = tree_path / exception
        return full_path.exists()

    exceptions_that_exists = list(filter(validate_exception, exceptions))

    # if not exceptions_existed:
    # no need to move thing to the temp dir
    #     print('N')
    if dry_run:
        print("Would remove all files in {}".format(tree_path))
        if exceptions_that_exists:
            print(f"With the following exceptions:")
            print("\n".join(str(tree_path / x) for x in exceptions_that_exists))
        return

    with tempfile.TemporaryDirectory() as tmpdir_name:
        # move exceptions to tempdir
        if exceptions_that_exists:
            print(
                "Moving {} in {} to a temp dir...".format(
                    exceptions_that_exists, tree_path
                ),
                file=sys.stderr,
            )
            from shutil import move

            deque(
                map(
                    lambda exception: move(tree_path / exception, tmpdir_name),
                    exceptions_that_exists,
                ),
                maxlen=0,
            )

        try:
            # remove tree
            # remove(tree_path)
            print(
                "Removing all files and dirs in {} with {}...".format(
                    tree_path, "rmtree"
                ),
                file=sys.stderr,
            )
            # rmtree_os_walk(tree_path)
            from shutil import rmtree, move

            # If we're ignoring *all* rmtree errors, we should also ignore FileNotFoundError
            # without requiring both flags.
            ignore_filenotfounderror = ignore_filenotfounderror or ignore_rmtree_error

            def _log_ignored(path: str, exc: BaseException) -> None:
                print(
                    f"Ignoring rmtree error while removing {tree_path}: {path} ({exc})",
                    file=sys.stderr,
                )

            def _onexc(func, path, exc: BaseException) -> None:
                if ignore_filenotfounderror and isinstance(exc, FileNotFoundError):
                    _log_ignored(str(path), exc)
                    return
                if ignore_rmtree_error and isinstance(exc, Exception):
                    _log_ignored(str(path), exc)
                    return
                raise exc

            def _onerror(func, path, exc_info) -> None:
                exc = exc_info[1]
                if ignore_filenotfounderror and isinstance(exc, FileNotFoundError):
                    _log_ignored(str(path), exc)
                    return
                if ignore_rmtree_error and isinstance(exc, Exception):
                    _log_ignored(str(path), exc)
                    return
                raise exc

            try:
                if ignore_filenotfounderror:
                    rmtree(tree_path, onexc=_onexc)
                else:
                    rmtree(tree_path)
            except TypeError:
                # Python < 3.12: no `onexc` param
                if ignore_filenotfounderror:
                    rmtree(tree_path, onerror=_onerror)
                elif ignore_rmtree_error:
                    rmtree(tree_path, onerror=_onerror)
                else:
                    rmtree(tree_path)
            except FileNotFoundError as exc:
                if ignore_filenotfounderror:
                    _log_ignored(str(tree_path), exc)
                else:
                    raise
            except Exception as exc:
                if ignore_rmtree_error:
                    _log_ignored(str(tree_path), exc)
                else:
                    raise

            # Ensure the root directory exists for restoring exceptions.
            tree_path.mkdir(parents=True, exist_ok=True)

            # recreate an empty dir
            # no need when using rmtree_os_walk !
            # tree_path.mkdir(exist_ok=True)

        finally:
            # move exceptions_existed back
            if exceptions_that_exists:
                print(
                    "Restoring {} from the temp dir...".format(exceptions_that_exists),
                    file=sys.stderr,
                )
                deque(
                    map(
                        lambda exception: move(
                            Path(tmpdir_name) / exception, tree_path
                        ),
                        exceptions_that_exists,
                    ),
                    maxlen=0,
                )


def clean_library_cache(args: Namespace) -> None:
    """
    Cleans library cache,
    with set exceptions
    """
    remove_tree_with_exceptions(
        tree_path=library_cache_path,
        exceptions=read_config().get("mac_cache_dir_exemptions_relative_path", []),
        dry_run=args.dry_run,
        ignore_filenotfounderror=getattr(args, "ignore_filenotfounderror", False),
        ignore_rmtree_error=getattr(args, "ignore_rmtree_error", False),
    )


def vscode_cleanup_workspace_storage(args: Namespace) -> None:
    """
    remove vscode workspace storage on mac
    """
    remove_tree_with_exceptions(
        tree_path=vscode_user_workspaceStorage_dir,
        dry_run=args.dry_run,
        ignore_filenotfounderror=getattr(args, "ignore_filenotfounderror", False),
        ignore_rmtree_error=getattr(args, "ignore_rmtree_error", False),
    )
    remove_tree_with_exceptions(
        tree_path=vscode_insiders_user_workspaceStorage_dir,
        dry_run=args.dry_run,
        ignore_filenotfounderror=getattr(args, "ignore_filenotfounderror", False),
        ignore_rmtree_error=getattr(args, "ignore_rmtree_error", False),
    )


def pypoetry_cache_cleanup(args: Namespace) -> None:
    """
    remove pypoetry cache on mac
    """
    remove_tree_with_exceptions(
        tree_path=pypoetry_cache_path,
        dry_run=args.dry_run,
        ignore_filenotfounderror=getattr(args, "ignore_filenotfounderror", False),
        ignore_rmtree_error=getattr(args, "ignore_rmtree_error", False),
    )


def pypoetry_cleanup(args: Namespace) -> None:
    """
    remove pypoetry on mac
    """
    remove_tree_with_exceptions(
        tree_path=pypoetry_path,
        dry_run=args.dry_run,
        ignore_filenotfounderror=getattr(args, "ignore_filenotfounderror", False),
        ignore_rmtree_error=getattr(args, "ignore_rmtree_error", False),
    )
