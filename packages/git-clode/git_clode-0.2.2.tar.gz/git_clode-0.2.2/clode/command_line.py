import re
import subprocess
import platform


class CommandException(Exception):
    def __init__(self, returncode: int, command_args: list[str], stderr: str | None):
        self.returncode = returncode
        self.command_args = command_args
        self.stderr = stderr


def run_command(*args: str | None) -> str | None:
    """Run a console command and return stdout"""
    filtered_args: list[str] = [arg for arg in args if arg is not None]

    use_shell = platform.system() == "Windows"
    process = subprocess.run(
        filtered_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=use_shell
    )
    if process.returncode != 0:
        raise CommandException(
            process.returncode,
            filtered_args,
            process.stdout.decode() if process.stdout is not None else None,  # type: ignore
        )
    return process.stdout.decode() if process.stdout is not None else None  # type: ignore


def get_clone_output(url: str) -> str:
    m = re.search(r"(?<=\/)[^\/]+?(?=(\.git)?$)", url)
    if m is None:
        raise Exception(f"Invalid git repository url: {url}")
    return m.group(0)


def git_clone(url: str, path: str):
    """Clone a git repository from `url` into `path`"""
    run_command("git", "clone", url, path)


def code(path: str):
    """Open a directory in VSCode"""
    run_command("code", path)


def gh_search_repository(query: str) -> list[str]:
    """Search for a repository with the GitHub API"""

    stdout = run_command(
        "gh",
        "api",
        "search/repositories",
        "--method",
        "GET",
        "-f",
        f"q={query}",
        "-q .items[]|.full_name",
    )
    if stdout is None:
        raise Exception("Received no response from gh CLI")
    return [line for line in stdout.split("\n") if line.strip() != ""]
