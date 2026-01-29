# winzy-get-the-file

[![PyPI](https://img.shields.io/pypi/v/winzy-get-the-file.svg)](https://pypi.org/project/winzy-get-the-file/)
[![Changelog](https://img.shields.io/github/v/release/sukhbinder/winzy-get-the-file?include_prereleases&label=changelog)](https://github.com/sukhbinder/winzy-get-the-file/releases)
[![Tests](https://github.com/sukhbinder/winzy-get-the-file/workflows/Test/badge.svg)](https://github.com/sukhbinder/winzy-get-the-file/actions?query=workflow%3ATest)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/sukhbinder/winzy-get-the-file/blob/main/LICENSE)

Get files from a folder 

## Installation

First [install winzy](https://github.com/sukhbinder/winzy) by typing

```bash
pip install winzy
```

Then install this plugin in the same environment as your winzy application.
```bash
winzy install winzy-get-the-file
```
## Usage

To get help type ``winzy  gtf --help``

### Command Line Options

```
usage: winzy gtf [-h] [-f FOLDER] -p PATTERN
                 [-t {latest,oldest,random,lastcreated}] [-s]

Get files from a folder

optional arguments:
  -h, --help            show this help message and exit
  -f FOLDER, --folder FOLDER
                        Folder path to search. Defaults to the current
                        directory.
  -p PATTERN, --pattern PATTERN
                        Pattern to match files.
  -t {latest,oldest,random,lastcreated}, --type {latest,oldest,random,lastcreated}
                        Type of file to return. Defaults to "latest".
  -s, --include-subfolder
                        Include subfolders
```

### Examples

Get the latest file matching a pattern:
```bash
winzy gtf -p "*.txt"
```

Get the oldest file from a specific folder:
```bash
winzy gtf -f /path/to/folder -p "*.py" -t oldest
```

Get a random file including subfolders:
```bash
winzy gtf -p "*.md" -t random -s
```

## Development

To set up this plugin locally, first checkout the code. Then create a new virtual environment:
```bash
cd winzy-get-the-file
python -m venv venv
source venv/bin/activate
```
Now install the dependencies and test dependencies:
```bash
pip install -e '.[test]'
```
To run the tests:
```bash
python -m pytest
```
