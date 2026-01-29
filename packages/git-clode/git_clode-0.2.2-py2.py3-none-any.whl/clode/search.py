import re
import inquirer as inq

from colorama import Fore

from .errors import NoUsernameProvidedException

from .clode import DEFAULT_CLODE_USERNAME

from .command_line import gh_search_repository


def search_repository(query: str) -> str:
    repositories: list[str] = gh_search_repository(query)

    if len(repositories) == 0:
        print(Fore.RED + "No repositories found" + Fore.RESET)
        exit()
    if len(repositories) == 1:
        return repositories[0]

    question = inq.List(
        "repo", message="Select repository to clone", choices=repositories
    )
    answers = inq.prompt([question])
    if answers is None:
        raise KeyboardInterrupt

    return answers["repo"]


LAZY_REPOSITORY_PATTERN = re.compile(r"^([\w.-]+\/)?[\w. -]+$")


def resolve_lazy(repository: str) -> str:
    if not re.match(LAZY_REPOSITORY_PATTERN, repository):
        print(Fore.RED + "Invalid lazy pattern" + Fore.RESET)
        exit()

    owner: str
    name: str
    if "/" in repository:
        owner, name = repository.split("/")
    else:
        if not DEFAULT_CLODE_USERNAME:
            raise NoUsernameProvidedException()
        owner = DEFAULT_CLODE_USERNAME
        name = repository

    return search_repository(f"owner:{owner} in:name fork:true sort:updated {name}")
