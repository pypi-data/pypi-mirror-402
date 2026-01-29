import traceback
from pathlib import Path

from grader import handle_part_id

from dlai_grader.compiler import compile_partial_module
from dlai_grader.config import Config, get_part_id
from dlai_grader.grading import (
    LearnerSubmission,
    compute_grading_score,
    graded_obj_missing,
)
from dlai_grader.io import copy_submission_to_workdir, read_notebook, send_feedback
from dlai_grader.notebook import keep_tagged_cells


def notebook_grading(config, compile_solution=False):
    try:
        nb = read_notebook(config.submission_file_path)
    except Exception as e:
        msg = f"There was a problem reading your notebook. Details:\n{e!s}"
        send_feedback(0.0, msg, err=True)

    transformations = [keep_tagged_cells()]

    for t in transformations:
        nb = t(nb)

    try:
        learner_mod = compile_partial_module(nb, "learner_mod", verbose=False)
    except Exception as e:
        msg = f"There was a problem compiling the code from your notebook, please check that you saved before submitting. Details:\n{e!s}"
        send_feedback(0.0, msg, err=True)

    solution_mod = None
    if compile_solution:
        solution_nb = read_notebook(config.solution_file_path)

        for t in transformations:
            solution_nb = t(solution_nb)

        solution_mod = compile_partial_module(
            solution_nb,
            "solution_mod",
            verbose=False,
        )

    return learner_mod, solution_mod


def non_notebook_grading(config):
    if Path(config.submission_file_path).stat().st_size == 0:
        msg = "Dummy file detected. Make sure you saved the correct file before submitting."
        send_feedback(0.0, msg, err=True)

    try:
        with open(config.submission_file_path, "r") as file:
            contents = file.read()
    except Exception as e:
        msg = f"There was an error reading your submission. Details:\n{e!s}"
        send_feedback(0.0, msg, err=True)

    return LearnerSubmission(submission=contents)


def main() -> None:
    part_id = get_part_id()

    match part_id:
        case "456":
            try:
                copy_submission_to_workdir(file_name="{{EXTRA_FILE_NAME}}")
            except FileNotFoundError as e:
                msg = f"""File {{EXTRA_FILE_NAME}} required for grading not found.
                This can happen if the file was deleted or you submitted without editing it.
                Details:\n{e!s}"""
                send_feedback(0.0, msg, err=True)
            except Exception as e:
                msg = f"There was an issue handling your submission. Details:\n{e!s}"
            c = Config(submission_file="{{EXTRA_FILE_NAME}}")
            learner_mod, solution_mod = non_notebook_grading(c), None
        case _:
            try:
                copy_submission_to_workdir()
            except FileNotFoundError as e:
                msg = f"""Notebook required for grading not found.
                This can happen if the file was deleted or you submitted without editing it.
                Details:\n{e!s}"""
                send_feedback(0.0, msg, err=True)
            except Exception as e:
                msg = f"There was an issue handling your submission. Details:\n{e!s}"
                send_feedback(0.0, msg, err=True)
            c = Config()
            learner_mod, solution_mod = notebook_grading(c, compile_solution=True)

    g_func = handle_part_id(part_id)(learner_mod, solution_mod)

    try:
        cases = g_func()
    except Exception as e:
        msg = f"There was an error grading your submission. Details:\n{e!s}"
        send_feedback(0.0, msg, err=True)

    if graded_obj_missing(cases):
        msg = "Object required for grading not found. If you haven't completed the exercise this might be expected. Otherwise, check your solution as grader omits cells that throw errors."
        send_feedback(0.0, msg, err=True)

    score, feedback = compute_grading_score(cases)
    send_feedback(score, feedback)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        msg = f"There was an error with the program. Exception:\n{e!s}.\nTraceback:\n{traceback.format_exc()}"
        send_feedback(0.0, msg, err=True)
