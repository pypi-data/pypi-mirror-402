import sys
import textwrap
from textwrap import dedent
import shutil
import os
from pathlib import Path


def generate_copy_assignment_script(
    extra_file_required="n",
    assignment_name="C1M2_Assignment.ipynb",
    extra_file_name="foo.txt",
):
    """
    Copy the appropriate copy_assignment_to_submission.sh script from templates depending on whether an extra file is required.

    Template files should be named:
        extrafile_n   (no extra file)
        extrafile_y   (with extra file)

    Returns:
        str: The final shell script contents after variable substitution.

    """
    if extra_file_required not in ("y", "n"):
        raise ValueError(f"Invalid extra_file_required value: {extra_file_required!r}")

    # Define template name pattern
    template_name = f"extrafile_{extra_file_required}"

    # Paths
    base_dir = Path(__file__).parent
    src = base_dir / "templates" / "copy_assignment_sh" / template_name
    dst = Path("copy_assignment_to_submission.sh")

    # Validate existence
    if not src.exists():
        raise FileNotFoundError(f"Template not found: {src}")

    # Read and substitute placeholders
    content = src.read_text(encoding="utf-8")
    content = content.replace("{{ASSIGNMENT_NAME}}", assignment_name).replace(
        "{{EXTRA_FILE_NAME}}", extra_file_name
    )

    # Write output
    dst.write_text(content, encoding="utf-8")
    dst.chmod(0o755)  # make executable
    return content


def copy_entry_script(
    sol_dir_required: str,
    non_notebook_grading: str,
    extra_file_name="foo.txt",
) -> str:
    # Validate inputs
    if sol_dir_required not in ("y", "n"):
        raise ValueError(f"Invalid sol_dir_required value: {sol_dir_required!r}")
    if non_notebook_grading not in ("y", "n"):
        raise ValueError(
            f"Invalid non_notebook_grading value: {non_notebook_grading!r}"
        )

    template_name = f"solution_{sol_dir_required}_file_{non_notebook_grading}.py"

    base_dir = Path(__file__).parent
    src = base_dir / "templates" / "entry_py" / template_name
    content = src.read_text(encoding="utf-8")
    content = content.replace("{{EXTRA_FILE_NAME}}", extra_file_name)
    dst = Path("entry.py")

    if not src.exists():
        raise FileNotFoundError(f"Template not found: {src}")

    # shutil.copy(src, dst)
    return content


def generate_dockerfile(data_dir_required="n", sol_dir_required="n"):
    """
    Generate a Dockerfile with optional data and solution directories.

    Args:
        data_dir_required (str): Include data directory if "y"
        sol_dir_required (str): Include solution directory if "y"

    """
    # Validate inputs
    if data_dir_required not in ("y", "n"):
        raise ValueError(f"Invalid data_dir_required value: {data_dir_required!r}")
    if sol_dir_required not in ("y", "n"):
        raise ValueError(f"Invalid sol_dir_required value: {sol_dir_required!r}")

    template_name = f"data_{data_dir_required}_solution_{sol_dir_required}"

    # Define paths
    base_dir = Path(__file__).parent
    src = base_dir / "templates" / "dockerfile" / template_name
    dst = Path("Dockerfile")

    # Ensure the source exists
    if not src.exists():
        raise FileNotFoundError(f"Template not found: {src}")

    # Copy template to current directory
    # shutil.copy(src, dst)

    # Return the Dockerfile contents
    return src.read_text(encoding="utf-8")


def copy_makefile() -> str:
    base_dir = Path(__file__).parent
    src = base_dir / "templates" / "Makefile"
    # content = src.read_text(encoding="utf-8")
    # content = content.replace("{{HARD_MEMORY}}", hard_memory)
    # content = content.replace("{{CPUS}}", cpus)
    # content = content.replace("{{SOFT_MEMORY}}", soft_memory)
    dst = Path("Makefile")

    if not src.exists():
        raise FileNotFoundError(f"Template not found: {src}")

    # shutil.copy(src, dst)
    return src.read_text(encoding="utf-8")


def copy_grader_py() -> str:
    base_dir = Path(__file__).parent
    src = base_dir / "templates" / "grader.py"
    dst = Path("grader.py")

    if not src.exists():
        raise FileNotFoundError(f"Template not found: {src}")

    # shutil.copy(src, dst)
    return src.read_text(encoding="utf-8")


def copy_submission_ipynb() -> str:
    base_dir = Path(__file__).parent
    src = base_dir / "templates" / "submission.ipynb"

    if not src.exists():
        raise FileNotFoundError(f"Template not found: {src}")

    # shutil.copy(src, dst)
    return src.read_text(encoding="utf-8")


def load_templates() -> dict[str, str]:
    specialization = input("Name of the specialization: ")
    course = input("Number of the course: ")
    module = input("Number of the module: ")

    grader_mvp = input(
        "Use minimum grader (no extra config)? y/n (leave empty for n): ",
    )

    grader_mvp = grader_mvp if grader_mvp else "n"
    if grader_mvp not in ["y", "n"]:
        print("invalid option selected")
        sys.exit(1)

    if grader_mvp == "n":
        unit_test_filename = input(
            "Filename for unit tests (leave empty for unittests): "
        )
        unit_test_filename = unit_test_filename if unit_test_filename else "unittests"
        # version = input("Version of the grader (leave empty for version 1): ")
        version = "1"

        data_dir_required = ""
        while data_dir_required not in ["y", "n"]:
            data_dir_required = input(
                "Do you require a data dir? y/n (leave empty for n): ",
            )
            if data_dir_required == "":
                data_dir_required = "n"
            # data_dir_required = data_dir_required if data_dir_required else "n"

        sol_dir_required = ""
        while sol_dir_required not in ["y", "n"]:
            sol_dir_required = input(
                "Do you require a solution file? y/n (leave empty for n): ",
            )
            if sol_dir_required == "":
                sol_dir_required = "n"

        non_notebook_grading = ""
        while non_notebook_grading not in ["y", "n"]:
            non_notebook_grading = input(
                "Will you grade a file different from a notebook? y/n (leave empty for n): ",
            )
            if non_notebook_grading == "":
                non_notebook_grading = "n"

        extra_file_name = ""
        if non_notebook_grading == "y":
            extra_file_name = input(
                "Name of the extra file to grade: ",
            )

        cpus = ""
        while cpus not in ["0.25", "0.5", "0.75", "1"]:
            cpus = input("CPU Units (leave empty for 0.25): ")
            if cpus == "":
                cpus = "0.25"

            if cpus not in ["0.25", "0.5", "0.75", "1"]:
                print(f"Options are: {['0.25', '0.5', '0.75', '1']}")

        soft_memory = ""
        soft_memory_options = [
            "512m",
            "768m",
            "1024m",
            "2048m",
            "4096m",
            "8192m",
            "1g",
            "2g",
            "4g",
            "8g",
        ]
        while soft_memory not in soft_memory_options:
            soft_memory = input("Memory Reservation (leave empty for 512m): ")
            if soft_memory == "":
                soft_memory = "512m"

            if soft_memory not in soft_memory_options:
                print(f"Options are: {soft_memory_options}")

        hard_memory = ""
        hard_memory_options = [
            "1024m",
            "2048m",
            "4096m",
            "8192m",
            "15000m",
            "1g",
            "2g",
            "4g",
            "8g",
            "15g",
        ]
        while hard_memory not in hard_memory_options:
            hard_memory = input("Memory Limit (leave empty for 1g): ")
            if hard_memory == "":
                hard_memory = "1g"

            if hard_memory not in hard_memory_options:
                print(f"Options are: {hard_memory_options}")

    if grader_mvp == "y":
        unit_test_filename = "unittests"
        version = "1"
        data_dir_required = "n"
        sol_dir_required = "n"
        non_notebook_grading = "n"
        extra_file_name = ""
        cpus = "0.25"
        soft_memory = "512m"
        hard_memory = "1g"

    dockerfile = generate_dockerfile(
        data_dir_required=data_dir_required,
        sol_dir_required=sol_dir_required,
    )

    conf = f"""
    ASSIGNMENT_NAME=C{course}M{module}_Assignment
    UNIT_TESTS_NAME={unit_test_filename}
    IMAGE_NAME={specialization}c{course}m{module}-grader
    GRADER_VERSION={version}
    TAG_ID=V$(GRADER_VERSION)
    SUB_DIR=mount
    MEMORY_LIMIT=4096
    CPUS={cpus}
    SOFT_MEMORY={soft_memory}
    HARD_MEMORY={hard_memory}
    """

    assignment_name = f"C{course}M{module}_Assignment.ipynb"

    copy_assignment_to_submission_sh = generate_copy_assignment_script(
        extra_file_required=non_notebook_grading,
        assignment_name=assignment_name,
        extra_file_name=extra_file_name,
    )

    makefile = copy_makefile()

    grader_py = copy_grader_py()

    submission_ipynb = copy_submission_ipynb()

    entry_py = copy_entry_script(
        sol_dir_required=sol_dir_required,
        non_notebook_grading=non_notebook_grading,
        extra_file_name=extra_file_name,
    )

    template_dict = {
        "dockerfile": dedent(dockerfile),
        "makefile": dedent(makefile),
        "conf": dedent(conf[1:]),
        "grader_py": dedent(grader_py),
        "entry_py": dedent(entry_py),
        "extra_file_name": extra_file_name,
        "submission_ipynb": submission_ipynb,
        # "copy_assignment_to_submission_sh": dedent(copy_assignment_to_submission_sh),
    }

    if extra_file_name:
        template_dict.update({"extra_file_name": extra_file_name})

    return template_dict
