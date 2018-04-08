import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Synchronize Stud.IP files")

    parser.add_argument("-i", "--interactive", action="store_true",
                        help="read username and password from stdin (and not from config "
                        "file)")

    parser.add_argument("-c", "--config", type=argparse.FileType('r'), metavar="FILE",
                        default=None,
                        help="set the path to the config file (Default is "
                        "'~/.config/studip-sync/config.json')")

    parser.add_argument("destination", nargs="?", metavar="DIR", default=None,
                        help="synchronize the files to the given destination directory")

    parser.add_argument("--init", action="store_true",
                        help="create new config file interactively")

    return parser.parse_args()


ARGS = parse_args()
