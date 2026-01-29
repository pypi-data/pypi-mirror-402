import pytest
import winzy_get_the_file as w
import os
import time

from argparse import ArgumentParser


def test_create_parser():
    subparser = ArgumentParser().add_subparsers()
    parser = w.create_parser(subparser)
    assert parser is not None
    result = parser.parse_args(["-p", "*.txt"])
    assert result.folder == os.getcwd()
    assert result.pattern == "*.txt"
    assert result.type == "latest"


def test_plugin(capsys):
    w.gtf_plugin.hello(None)
    captured = capsys.readouterr()
    assert "Hello! This is an example ``winzy`` plugin." in captured.out


def test_last_modified_file(tmp_path):
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file1.touch()
    time.sleep(0.01)
    file2.touch()
    assert w.app.last_modified_file(os.path.join(tmp_path, "*.txt")) == str(file2)


def test_last_created_file(tmp_path):
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file1.touch()
    time.sleep(0.01)
    file2.touch()
    assert w.app.last_created_file(os.path.join(tmp_path, "*.txt")) == str(file2)


def test_oldest_file(tmp_path):
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file1.touch()
    time.sleep(0.01)
    file2.touch()
    assert w.app.oldest_file(os.path.join(tmp_path, "*.txt")) == str(file1)


def test_random_file(tmp_path):
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file3 = tmp_path / "file3.txt"
    file1.touch()
    time.sleep(0.01)
    file2.touch()
    time.sleep(0.01)
    file3.touch()
    result = w.app.random_file(os.path.join(tmp_path, "*.txt"))
    assert os.path.exists(result)
