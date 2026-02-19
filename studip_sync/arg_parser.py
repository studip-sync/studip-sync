import argparse


def parse_args():
    parser = argparse.ArgumentParser(description="Synchronize Stud.IP files")

    parser.add_argument("-c", "--config", metavar="DIR",
                        default=None,
                        help="set the path to the config dir (Default is "
                             "'~/.config/studip-sync/')")

    parser.add_argument("-d", "--destination", metavar="DIR", default=None,
                        help="synchronize files to the given destination directory (If no config "
                             "is present this argument implies --full)")

    parser.add_argument("-m", "--media", metavar="DIR", default=None,
                        help="synchronize media to the given destination directory")

    parser.add_argument("--init", action="store_true",
                        help="create new config file interactively")

    parser.add_argument("--full", action="store_true",
                        help="downloads all courses instead of only new ones")

    parser.add_argument("--recent", action="store_true",
                        help="only download the courses of the recent semester")

    parser.add_argument("--old", action="store_true",
                        help="use older sync client which downloads files in bulk")

    parser.add_argument("--disable-api", action="store_true",
                        help="don't use the StudIP API endpoint to download and discover files")

    parser.add_argument("--http-timeout", metavar="SECONDS", type=float, default=None,
                        help="HTTP request timeout in seconds (default from config/constants)")

    parser.add_argument("--http-retries", metavar="COUNT", type=int, default=None,
                        help="number of HTTP retries for transient failures")

    parser.add_argument("--http-retry-backoff", metavar="SECONDS", type=float, default=None,
                        help="backoff factor used between HTTP retries")

    parser.add_argument("--http-retry-status", metavar="CODES", default=None,
                        help="comma-separated HTTP status codes to retry, e.g. 429,500,502")

    # PLUGINS
    parser.add_argument("--enable-plugin", metavar="PLUGIN",
                        help="enables and configures a plugin")

    parser.add_argument("--reconfigure-plugin", metavar="PLUGIN",
                        help="reconfigures a already-enabled plugin")

    parser.add_argument("--disable-plugin", metavar="PLUGIN",
                        help="disables a plugin")

    parser.add_argument("-v", action="store_true",
                        help="show debug output")

    return parser.parse_known_args()[0]


ARGS = parse_args()
