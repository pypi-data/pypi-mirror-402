import winzy
import os

from winzy_get_the_file.app import (
    last_modified_file,
    oldest_file,
    random_file,
    last_created_file,
)


def create_parser(subparser):
    parser = subparser.add_parser("gtf", description="Get files from a folder ")
    # Add subprser arguments here.
    parser.add_argument(
        "-f",
        "--folder",
        type=str,
        default=os.getcwd(),
        help="Folder path to search. Defaults to the current directory.",
    )
    parser.add_argument(
        "-p", "--pattern", type=str, required=True, help="Pattern to match files."
    )
    parser.add_argument(
        "-t",
        "--type",
        choices=["latest", "oldest", "random", "lastcreated"],
        default="latest",
        help='Type of file to return. Defaults to "latest".',
        type=str,
    )
    parser.add_argument(
        "-s", "--include-subfolder", help="Include subfolders", action="store_true"
    )
    return parser


class WinzyPlugin:
    """Get files from a folder"""

    __name__ = "gtf"

    @winzy.hookimpl
    def register_commands(self, subparser):
        self.parser = create_parser(subparser)
        self.parser.set_defaults(func=self.run)

    def run(self, args):
        # add actual call here
        folder_path = args.folder
        pattern = args.pattern
        file_type = args.type
        include_subfolder = args.include_subfolder

        if include_subfolder:
            filepattern = os.path.join(folder_path, "*", pattern)
        else:
            filepattern = os.path.join(folder_path, pattern)

        if file_type == "latest":
            result = last_modified_file(filepattern)
        elif file_type == "oldest":
            result = oldest_file(filepattern)
        elif file_type == "random":
            result = random_file(filepattern)
        else:  # file_type == 'lastcreated'
            result = last_created_file(filepattern)

        if result:
            print(result)
        else:
            print(f"No files matching the pattern '{pattern}' found in {folder_path}")

    def hello(self, args):
        # this routine will be called when 'winzy gtf' is called.
        print("Hello! This is an example ``winzy`` plugin.")


gtf_plugin = WinzyPlugin()
