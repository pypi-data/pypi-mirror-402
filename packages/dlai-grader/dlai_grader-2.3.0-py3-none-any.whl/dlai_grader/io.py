import json
import os
import shutil
import subprocess
import tarfile
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from os import devnull
from pathlib import Path
from textwrap import dedent
from zipfile import ZipFile

import jupytext
import nbformat
from nbformat.notebooknode import NotebookNode

from .notebook import (
    add_metadata_all_code_cells,
    add_metadata_code_cells_without_pattern,
    solution_to_learner_format,
    tag_code_cells,
)
from .templates import load_templates


@contextmanager
def suppress_stdout_stderr():
    """A context manager that redirects stdout and stderr to devnull."""
    with open(devnull, "w") as fnull:
        with redirect_stderr(fnull) as err, redirect_stdout(fnull) as out:
            yield (err, out)


def read_notebook(
    path: str,
) -> NotebookNode:
    """
    Reads a notebook found in the given path and returns a serialized version.

    Args:
        path (str): Path of the notebook file to read.

    Returns:
        NotebookNode: Representation of the notebook following nbformat convention.

    """
    return nbformat.read(path, as_version=nbformat.NO_CONVERT)


def tag_notebook(
    path: str,
) -> None:
    """
    Adds 'graded' tag to all code cells of a notebook.

    Args:
        path (str): Path to the notebook.

    """
    nb = read_notebook(path)
    nb = tag_code_cells(nb)
    jupytext.write(nb, path)


def undeletable_notebook(path: str) -> None:
    """
    Makes all code cells of a notebook non-deletable.

    Args:
        path (str): Path to the notebook.

    """
    nb = read_notebook(path)
    nb = add_metadata_all_code_cells(nb, {"deletable": False})
    jupytext.write(nb, path)


def uneditable_notebook(path: str) -> None:
    """
    Makes all non-graded code cells of a notebook non-editable.

    Args:
        path (str): Path to the notebook.

    """
    nb = read_notebook(path)
    nb = add_metadata_code_cells_without_pattern(
        nb, {"editable": False}, ignore_pattern="^# EDITABLE"
    )
    jupytext.write(nb, path)


def extract_tar(
    file_path: str,
    destination: str,
    post_cleanup: bool = True,
) -> None:
    """
    Extracts a tar file unto the desired destination.

    Args:
        file_path (str): Path to tar file.
        destination (str): Path where to save uncompressed files.
        post_cleanup (bool, optional): If true, deletes the compressed tar file. Defaults to True.

    """
    with tarfile.open(file_path, "r") as my_tar:
        my_tar.extractall(destination)

    if post_cleanup and os.path.exists(file_path):
        os.remove(file_path)


def extract_zip(
    file_path: str,
    destination: str,
    post_cleanup: bool = True,
) -> None:
    """Extracts a zip file unto the desired destination.

    Args:
        file_path (str): Path to zip file.
        destination (str): Path where to save uncompressed files.
        post_cleanup (bool, optional): If true, deletes the compressed zip file. Defaults to True.
    """
    with ZipFile(file_path, "r") as zip:
        zip.extractall(destination)

    if post_cleanup and os.path.exists(file_path):
        os.remove(file_path)


def send_feedback(
    score: float,
    msg: str,
    feedback_path: str = "/shared/feedback.json",
    err: bool = False,
) -> None:
    """
    Sends feedback to the learner.

    Args:
        score (float): Grading score to show on Coursera for the assignment.
        msg (str): Message providing additional feedback.
        feedback_path (str): Path where the json feedback will be saved. Defaults to /shared/feedback.json
        err (bool, optional): True if there was an error while grading. Defaults to False.

    """
    post = {"fractionalScore": score, "feedback": msg}
    print(json.dumps(post))

    with open(feedback_path, "w") as outfile:
        json.dump(post, outfile)

    if err:
        exit(1)

    exit(0)


def copy_submission_to_workdir(
    dir_origin: str = "/shared/submission/",
    dir_destination: str = "./submission/",
    file_name: str = "submission.ipynb",
) -> None:
    """Copies submission file from bind mount directory into working directory.
    Args:
        dir_origin (str): Origin directory.
        dir_destination (str): Target directory.
        file_name (str): Name of the file.
    """

    _from = os.path.join(dir_origin, file_name)
    _to = os.path.join(dir_destination, file_name)
    shutil.copyfile(_from, _to)


def update_grader_version() -> str:
    """Updates the grader version by 1 unit.

    Returns:
        str: New version of the grader.
    """
    with open("./.conf", "r") as f:
        lines = f.readlines()

    new_lines = []
    for l in lines:
        if ("GRADER_VERSION" in l) and ("TAG_ID" not in l):
            _, v = l.split("=")
            num_v = int(v)
            new_v = num_v + 1
            new_l = f"GRADER_VERSION={new_v}\n"
            new_lines.append(new_l)
            continue
        new_lines.append(l)

    with open("./.conf", "w") as f:
        f.writelines(new_lines)

    return str(new_v)


def update_notebook_version(
    path: str,
    version: str,
) -> None:
    """Updates notebook version to match the latest version of the grader.

    Args:
        path (str): Path to the notebook.
        version (str): Latest version of the grader to update the notebook to.
    """
    nb = read_notebook(path)
    metadata = nb.get("metadata")
    metadata.update({"grader_version": version})
    nb["metadata"] = metadata
    jupytext.write(nb, path)


def update_grader_and_notebook_version() -> None:
    """Updates the notebook and the grader at the same time."""
    latest_version = update_grader_version()
    update_notebook_version("./mount/submission.ipynb", latest_version)


def write_file_from_template(
    filename: str,
    template: str,
) -> None:
    """Writes the contents of a template unto a file.

    Args:
        filename (str): Name of the file.
        template (str): Template.
    """
    with open(filename, "w") as f:
        f.write(template)


def init_grader() -> None:
    """Initializes a grader directory."""

    template_dict = load_templates()
    write_file_from_template("./Dockerfile", template_dict["dockerfile"])
    write_file_from_template("./grader.py", template_dict["grader_py"])
    write_file_from_template("./Makefile", template_dict["makefile"])
    write_file_from_template("./.conf", template_dict["conf"])
    write_file_from_template("./entry.py", template_dict["entry_py"])
    # write_file_from_template(
    #     "./copy_assignment_to_submission.sh",
    #     template_dict["copy_assignment_to_submission_sh"],
    # )
    write_file_from_template("./requirements.txt", "dlai-grader")
    write_file_from_template("./.env", "")

    os.makedirs("learner")
    os.makedirs("mount")
    os.makedirs("submission")

    extra_file_name = template_dict["extra_file_name"]
    if extra_file_name:
        write_file_from_template(f"./learner/{extra_file_name}", "")
        write_file_from_template(f"./mount/{extra_file_name}", "")

    write_file_from_template(
        "./mount/submission.ipynb", template_dict["submission_ipynb"]
    )

    if "COPY data/ /grader/data/" in template_dict["dockerfile"]:
        os.makedirs("data")

    if "COPY solution/ /grader/solution/" in template_dict["dockerfile"]:
        os.makedirs("solution")


def generate_learner_version(
    filename_source: str,
    filename_target: str,
) -> None:
    """Generates the learning facing version of an assignment.

    Args:
        filename_source (str): Path to original notebook.
        filename_target (str): Path where to save reformatted notebook.
    """
    notebook = read_notebook(filename_source)

    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            cell_code = cell["source"]
            fmt_code = solution_to_learner_format(cell_code)
            cell["source"] = fmt_code

    jupytext.write(notebook, filename_target)


def grade_parts(
    partids: str,
    image: str,
    sub_dir: str,
    mem: str,
) -> None:
    """Grades all parts using coursera_autograder tool.

    Args:
        partids (str): String encoding all part_ids separated by spaces.
        image (str): Name of the docker image to use.
        sub_dir (str): Directory including the submission.
        mem (str): Amount of memory to allocate for the container.
    """

    for p in partids.split(" "):
        print(f"\nGrading part_id: {p}\n")
        cmd = """coursera_autograder grade local $2 $3 '{"partId": "$1", "fileName": "submission.ipynb"}' --mem-limit $4"""

        cmd = cmd.replace("$1", f"{p}")
        cmd = cmd.replace("$2", image)
        cmd = cmd.replace("$3", sub_dir)
        cmd = cmd.replace("$4", mem)
        cmd = dedent(cmd)

        try:
            subprocess.run(cmd, shell=True, executable="/bin/bash")
        except Exception as e:
            print(f"There was an error grading with coursera_autograder. Details: {e}")


def generate_learner_file(
    filename_source: str,
    filename_target: str,
) -> None:
    """
    Generates the learning facing version of any file.

    Args:
        filename_source (str): Path to original notebook.
        filename_target (str): Path where to save reformatted notebook.

    """
    solution_code = Path(filename_source).read_text()

    # format the code to replace with placeholders
    fmt_code = solution_to_learner_format(solution_code)

    # save the learner files
    Path(filename_target).write_text(fmt_code, encoding="utf-8")
