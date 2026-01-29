import os
import glob
from random import choice
import argparse


def last_modified_file(pathpattern) -> str:
    """Returns the last modified file in the specified folder."""
    files = glob.glob(pathpattern)
    if not files:
        return None

    # Find the latest modified time and corresponding file
    latest_time = 0
    latest_file = None
    for file in files:
        mtime = os.path.getmtime(file)
        if mtime > latest_time:
            latest_time = mtime
            latest_file = file

    return latest_file


def last_created_file(pathpattern) -> str:
    """Returns the last created file (or accessed) in the specified folder."""
    files = glob.glob(pathpattern)
    if not files:
        return None

    # Find the latest access time and corresponding file
    latest_time = 0
    latest_file = None
    for file in files:
        atime = os.path.getatime(file)
        if atime > latest_time:
            latest_time = atime
            latest_file = file

    return latest_file


def oldest_file(pathpattern) -> str:
    """Returns the oldest file in the specified folder."""
    files = glob.glob(pathpattern)
    if not files:
        return None

    # Find the earliest modified time and corresponding file
    earliest_time = float("inf")
    earliest_file = None
    for file in files:
        mtime = os.path.getmtime(file)
        if mtime < earliest_time:
            earliest_time = mtime
            earliest_file = file

    return earliest_file


def random_file(pathpattern) -> str:
    """Returns a random file from the specified folder."""
    files = glob.glob(pathpattern)
    if not files:
        return None

    # Return a random file
    return choice(files)
