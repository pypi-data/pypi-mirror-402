import argparse

from .errors import NoUsernameProvidedException


from .search import search_repository, resolve_lazy
from .clode import clode, ShouldOpen
import colorama
from colorama import Fore

colorama.init()


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="clode",
        description="CLI tool to open git repositories quickly",
    )
    parser.add_argument(
        "repository", type=str, help="url or name of repository to clone"
    )
    parser.add_argument(
        "directory",
        type=str,
        nargs="?",
        help="the name of a new directory to clone into",
    )

    # Flags
    should_open_group = parser.add_mutually_exclusive_group()
    should_open_group.add_argument(
        "-n",
        "--never-open",
        action="store_true",
        help="don't open after cloning",
    )
    should_open_group.add_argument(
        "-a", "--always-open", action="store_true", help="open even if already cloned"
    )

    search_group = parser.add_mutually_exclusive_group()
    search_group.add_argument(
        "-q", "--search", action="store_true", help="search for a repository on GitHub"
    )
    search_group.add_argument(
        "-l",
        "--lazy",
        action="store_true",
        help="lazy search for a repository on GitHub",
    )

    return parser.parse_args()


def print_error(message: str):
    print(Fore.RED + message + Fore.RESET)


def main():
    try:
        args = parse_arguments()
        should_open = (
            ShouldOpen.always
            if args.always_open
            else (ShouldOpen.never if args.never_open else ShouldOpen.cloned)
        )

        if args.search:
            repository = search_repository(args.repository)
        elif args.lazy:
            repository = resolve_lazy(args.repository)
        else:
            repository = args.repository

        clode(repository, args.directory, should_open=should_open)
    except KeyboardInterrupt:
        pass
    except NoUsernameProvidedException:
        print_error("No username provided and DEFAULT_CLODE_USERNAME is not set")


if __name__ == "__main__":
    main()
