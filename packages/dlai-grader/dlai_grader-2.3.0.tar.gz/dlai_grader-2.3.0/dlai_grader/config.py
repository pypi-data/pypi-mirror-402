import os
import re
import csv
from dataclasses import dataclass


def parse_conf(
    path: str = "./.conf",
) -> dict[str, str]:
    """Parses variables from .conf file

    Args:
        path (str): Path to file to parse. Defaults to ./.conf

    Returns:
        Dict[str, str]: Dictionary containing keys and value pairs of vars in file.
    """
    with open(path) as stream:
        contents = stream.read().strip()

    var_declarations = re.findall(r"^[a-zA-Z0-9_]+=.*$", contents, flags=re.MULTILINE)
    reader = csv.reader(var_declarations, delimiter="=")
    bash_vars = dict(reader)

    return bash_vars


def get_part_id() -> str:
    """Get part id from environment variable.
    Returns:
        str: The part id.
    """
    part_id = os.getenv("partId")
    if part_id is None:
        return ""
    return part_id


@dataclass
class Config:
    """Class that holds configuration values for the grader."""

    bind_mount: str = "/shared/submission/"
    submission_workdir: str = "./submission/"
    solution_workdir: str = "./solution/"
    solution_file: str = "solution.ipynb"
    solution_file_path: str = ""
    submission_file: str = "submission.ipynb"
    submission_file_path: str = ""
    part_id: str = get_part_id()
    latest_version: str = (
        parse_conf()["GRADER_VERSION"] if os.path.exists("./.conf") else ""
    )
    assignment_name: str = (
        parse_conf()["ASSIGNMENT_NAME"] if os.path.exists("./.conf") else ""
    )

    def __post_init__(self):
        # This is where we set the file paths after the instance variables are initialized
        self.solution_file_path = os.path.join(
            self.solution_workdir, self.solution_file
        )
        self.submission_file_path = os.path.join(
            self.submission_workdir, self.submission_file
        )
