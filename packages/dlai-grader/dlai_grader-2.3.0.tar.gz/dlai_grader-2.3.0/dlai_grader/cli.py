import os
import argparse
from .io import (
    update_grader_and_notebook_version,
    update_notebook_version,
    tag_notebook,
    undeletable_notebook,
    uneditable_notebook,
    init_grader,
    generate_learner_version,
    grade_parts,
)
from .config import Config


def parse_dlai_grader_args() -> None:
    """Parses command line flags and performs desired actions"""
    parser = argparse.ArgumentParser(
        description="Helper library to build automatic graders for DLAI courses."
    )
    parser.add_argument(
        "-i",
        "--init",
        action="store_true",
        help="Initialize a grader workspace with common files and directories.",
    )
    parser.add_argument(
        "-u",
        "--upgrade",
        action="store_true",
        help="Upgrade the grader and notebook version.",
    )
    parser.add_argument(
        "-v",
        "--versioning",
        action="store_true",
        help="Add version to notebook metadata that matches current grader version.",
    )
    parser.add_argument(
        "-t",
        "--tag",
        action="store_true",
        help="Add graded tag to all code cells of notebook.",
    )
    parser.add_argument(
        "-ud",
        "--undeletable",
        action="store_true",
        help="Make all code cells of notebook not deletable.",
    )
    parser.add_argument(
        "-ue",
        "--uneditable",
        action="store_true",
        help="Make all non-graded code cells of notebook not editable.",
    )
    parser.add_argument(
        "-l",
        "--learner",
        action="store_true",
        help="Generate learner facing version.",
    )
    parser.add_argument(
        "-in",
        "--input_notebook",
        type=str,
        help="Path to input notebook to generate learner version from.",
    )
    parser.add_argument(
        "-out",
        "--output_notebook",
        type=str,
        help="Path to save the generated learner version to.",
    )
    parser.add_argument(
        "-g",
        "--grade",
        action="store_true",
        help="Grade using coursera_autograder tool.",
    )
    parser.add_argument(
        "-p",
        "--partids",
        type=str,
        help="Partids encoded as a single string separated by spaces.",
    )
    parser.add_argument(
        "-d",
        "--docker",
        type=str,
        help="Docker image to use for grading.",
    )
    parser.add_argument(
        "-m",
        "--memory",
        type=str,
        help="Memory to assign to the container.",
    )
    parser.add_argument(
        "-s",
        "--submission",
        type=str,
        help="Submission directory.",
    )
    args = parser.parse_args()
    c = Config()
    if args.init:
        init_grader()
    if args.upgrade:
        update_grader_and_notebook_version()
    if args.versioning:
        update_notebook_version(
            path="./mount/submission.ipynb", version=c.latest_version
        )
    if args.tag:
        tag_notebook("./mount/submission.ipynb")
    if args.undeletable:
        undeletable_notebook("./mount/submission.ipynb")
    if args.uneditable:
        uneditable_notebook("./mount/submission.ipynb")

    if args.learner:
        filename_source = "./mount/submission.ipynb"
        filename_target = f"./learner/{c.assignment_name}.ipynb"

        if not os.path.exists("./mount/") and (not args.input_notebook):
            print(
                "No mount/ directory found. Looking for .ipynb files in current directory.\n"
            )
            notebooks_current_directory = [
                f for f in os.listdir(".") if f.endswith(".ipynb")
            ]

            if len(notebooks_current_directory) > 1:
                print(
                    "More than one notebook found in current directory. Specify '--input_notebook' flag."
                )
                return

            filename_source = notebooks_current_directory[0]

        if args.input_notebook:
            filename_source = args.input_notebook

        filename_current_directory = filename_source.split("/")[-1]
        notebook_name_no_extension = filename_current_directory.split(".")[0]
        filename_target = f"./{notebook_name_no_extension}_learner.ipynb"

        if args.output_notebook:
            filename_target = args.output_notebook

        generate_learner_version(
            filename_source=filename_source,
            filename_target=filename_target,
        )
    if args.grade:
        if not args.partids:
            print("partids not provided")
            return
        if not args.docker:
            print("docker not provided")
            return
        if not args.memory:
            print("memory not provided")
            return
        if not args.submission:
            print("submission not provided")
            return

        grade_parts(args.partids, args.docker, args.submission, args.memory)
