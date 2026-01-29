from enum import StrEnum
from .command_line import git_clone, code, CommandException, get_clone_output
import re
from colorama import Fore

import os

DEFAULT_CLODE_USERNAME = os.environ.get("DEFAULT_CLODE_USERNAME")


class ShouldOpen(StrEnum):
    cloned = "cloned"
    always = "always"
    never = "never"


def clode(
    repository: str,
    output: str | None = None,
    should_open: ShouldOpen = ShouldOpen.cloned,
):
    # Resolve repository name only
    url = repository
    if re.match("^[a-zA-Z0-9._-]+$", url):
        if DEFAULT_CLODE_USERNAME is None:
            print(
                Fore.RED
                + "No username provided and DEFAULT_CLODE_USERNAME is not set"
                + Fore.RESET
            )
            exit()

        url = DEFAULT_CLODE_USERNAME + "/" + url

    if re.match("^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$", url):
        url = "https://github.com/" + url

    output_folder = get_clone_output(url) if output is None else output

    clone_success = False
    try:
        print(f"Cloning {Fore.YELLOW}{url}{Fore.LIGHTBLACK_EX}")
        git_clone(url, output_folder)
        clone_success = True
    except CommandException as e:
        print(Fore.RED + "git clone failed" + Fore.RESET)
        if e.returncode != 128:
            exit()

    do_open: bool
    if should_open == ShouldOpen.always:
        do_open = True
    elif should_open == ShouldOpen.never:
        do_open = False
    elif should_open == ShouldOpen.cloned:
        do_open = clone_success

    if do_open:
        print(f"{Fore.RESET}Opening {Fore.YELLOW}{output_folder}{Fore.RESET} in VSCode")
        code(output_folder)
