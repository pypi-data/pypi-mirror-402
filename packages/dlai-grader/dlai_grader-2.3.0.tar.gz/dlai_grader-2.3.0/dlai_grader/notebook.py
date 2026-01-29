import re
from typing import Callable
import jupytext
from nbformat.notebooknode import NotebookNode
from .config import Config


def notebook_to_script(
    notebook: NotebookNode,
) -> str:
    """Converts a notebook into a python script serialized as a string.
    Args:
        notebook (NotebookNode): Notebook to convert into script.
    Returns:
        str: Python script representation as string.
    """
    return jupytext.writes(notebook, fmt="py:percent")


def cut_notebook(
    regex_pattern: str = "(grade)(.|[ \t]*)(up)(.|[ \t]*)(to)(.|[ \t]*)(here)",
) -> Callable[[NotebookNode], NotebookNode]:
    """Cuts a notebook, this allows for partial grading. Written as a closure so it can be consumed as a functional option for notebooks.
    Args:
        regex_pattern (str): Regexp pattern to look for. Cells after match will be omitted.
    Returns:
        Callable[[NotebookNode], NotebookNode]: A function that cuts the notebook.
    """

    def inner(
        notebook: NotebookNode,
    ) -> NotebookNode:
        """Cuts a notebook by excluding all cells after a pattern is matched.
        Args:
            notebook (NotebookNode): Notebook to filter.
        Returns:
            NotebookNode: The filtered notebook.
        """
        filtered_cells = []

        for cell in notebook["cells"]:
            filtered_cells.append(cell)

            if cell["cell_type"] == "code" and re.search(regex_pattern, cell["source"]):
                break

        notebook["cells"] = filtered_cells
        return notebook

    return inner


def keep_tagged_cells(
    tag: str = "graded",
) -> Callable[[NotebookNode], NotebookNode]:
    """Keeps tagged cells from a notebook. Written as a closure so it can be consumed as a functional option for notebooks.
    Args:
        tag (str): Tag to look for within cell's metadata. Defaults to "graded".
    Returns:
        Callable[[NotebookNode], NotebookNode]: A function that filters the notebook.
    """

    def inner(
        notebook: NotebookNode,
    ) -> NotebookNode:
        """Filters a notebook by including tagged cells.
        Args:
            notebook (NotebookNode): Notebook to filter.
        Returns:
            NotebookNode: The notebook with tagged cells.
        """
        filtered_cells = []

        for cell in notebook["cells"]:
            if ("tags" not in cell["metadata"]) or (
                tag not in cell["metadata"].get("tags")
            ):
                continue
            filtered_cells.append(cell)

        notebook["cells"] = filtered_cells
        return notebook

    return inner


def omit_tagged_cells(
    tag: str = "omit",
) -> Callable[[NotebookNode], NotebookNode]:
    """Omits tagged cells from a notebook. Written as a closure so it can be consumed as a functional option for notebooks.
    Args:
        tag (str): Tag to look for within cell's metadata. Defaults to "omit".
    Returns:
        Callable[[NotebookNode], NotebookNode]: A function that filters the notebook.
    """

    def inner(
        notebook: NotebookNode,
    ) -> NotebookNode:
        """Filters a notebook by excluding tagged cells.
        Args:
            notebook (NotebookNode): Notebook to filter.
        Returns:
            NotebookNode: The notebook without omitted cells.
        """
        filtered_cells = []

        for cell in notebook["cells"]:
            if ("tags" in cell["metadata"]) and (tag in cell["metadata"].get("tags")):
                continue
            filtered_cells.append(cell)

        notebook["cells"] = filtered_cells
        return notebook

    return inner


def partial_grading_enabled(
    notebook: NotebookNode,
    regex_pattern: str = "(grade)(.|[ \t]*)(up)(.|[ \t]*)(to)(.|[ \t]*)(here)",
) -> bool:
    """Checks for the existence of the partial grading tag.

    Args:
        notebook (NotebookNode): The notebook from the learner.
        regex_pattern (str, optional): Pattern to check. Defaults to "(grade)(.|[ \t]*)(up)(.|[ \t]*)(to)(.|[ \t]*)(here)".

    Returns:
        bool: True if the pattern if found, False otherwise.
    """
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code" and re.search(regex_pattern, cell["source"]):
            return True
    return False


def get_named_cells(
    notebook: NotebookNode,
) -> dict:
    """Returns the named cells for cases when grading is done using cell's output.
    Args:
        notebook (NotebookNode): The notebook from the learner.
    Returns:
        dict: All named cells encoded as a dictionary.
    """
    named_cells = {}
    for cell in notebook["cells"]:
        metadata = cell["metadata"]
        if "name" not in metadata:
            continue
        named_cells.update({metadata.get("name"): cell})
    return named_cells


def tag_code_cells(
    notebook: NotebookNode,
    tag: str = "graded",
) -> NotebookNode:
    """Filters a notebook to exclude additional cells created by learners.
       Also used for partial grading if the tag has been provided.
    Args:
        notebook (NotebookNode): Notebook to filter.
        tag (str): The tag to include in the code cell's metadata. Defaults to "graded".
    Returns:
        NotebookNode: The filtered notebook.
    """
    filtered_cells = []

    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            if "tags" not in cell["metadata"]:
                cell["metadata"]["tags"] = []

            tags = cell["metadata"]["tags"]

            if tag not in tags:
                tags.append(tag)
                cell["metadata"]["tags"] = tags

        filtered_cells.append(cell)

    notebook["cells"] = filtered_cells

    return notebook


def add_metadata_all_code_cells(
    notebook: NotebookNode,
    metadata: dict,
) -> NotebookNode:
    """Adds metadata to all code cells of a notebook.
    Args:
        notebook (NotebookNode): Notebook to filter.
        metadata (dict): The metadata which should be a key-value pair.
    Returns:
        NotebookNode: The notebook with the new metadata.
    """
    filtered_cells = []

    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            current_metadata = cell["metadata"]
            current_metadata.update(metadata)
            cell["metadata"] = current_metadata

        filtered_cells.append(cell)

    notebook["cells"] = filtered_cells

    return notebook


def add_metadata_code_cells_with_pattern(
    notebook: NotebookNode, metadata: dict, regex_pattern: str = "w[1-9]_unittest"
) -> NotebookNode:
    """Adds metadata to code cells of a notebook that match a regexp pattern.
    Args:
        notebook (NotebookNode): Notebook to filter.
        metadata (dict): The metadata which should be a key-value pair.
        regex_pattern (str, optional): Pattern to check. Defaults to "w[1-9]_unittest".
    Returns:
        NotebookNode: The notebook with the new metadata.
    """
    filtered_cells = []

    for cell in notebook["cells"]:
        if cell["cell_type"] == "code" and re.search(regex_pattern, cell["source"]):
            current_metadata = cell["metadata"]
            current_metadata.update(metadata)
            cell["metadata"] = current_metadata

        filtered_cells.append(cell)

    notebook["cells"] = filtered_cells

    return notebook


def add_metadata_code_cells_without_pattern(
    notebook: NotebookNode,
    metadata: dict,
    match_pattern: str = "^# GRADED",
    ignore_pattern: str = None,
) -> NotebookNode:
    """Adds metadata to code cells of a notebook that don't match a regexp pattern and aren't ignored by another pattern.

    Args:
        notebook (NotebookNode): Notebook to filter.
        metadata (dict): The metadata which should be a key-value pair.
        match_pattern (str, optional): Pattern to check which cells to add metadata to. Defaults to "^# GRADED ".
        ignore_pattern (str, optional): Pattern to check which cells to ignore. If a cell matches this pattern, it will be skipped.

    Returns:
        NotebookNode: The notebook with the new metadata.
    """
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            if ignore_pattern and re.search(ignore_pattern, cell["source"]):
                continue

            if not re.search(match_pattern, cell["source"]):
                current_metadata = cell.get("metadata", {})
                current_metadata.update(metadata)
                cell["metadata"] = current_metadata

    return notebook


def notebook_version(
    notebook: NotebookNode,
) -> str:
    """Returns dlai version of a notebook.

    Args:
        notebook (NotebookNode): A notebook.

    Returns:
        str: Version encoded as string.
    """
    return notebook.get("metadata").get("grader_version")


def notebook_is_up_to_date(
    notebook: NotebookNode,
) -> bool:
    """Determines if a notebook is up-to-date with latest grader version.

    Args:
        notebook (NotebookNode): A notebook.

    Returns:
        bool: True if both versions match, False otherwise.
    """
    version = notebook_version(notebook)
    c = Config()
    if version != c.latest_version:
        return False
    return True


def get_indentation(
    line: str,
) -> str:
    """Gets the indentation of a string.

    Args:
        line (str): A line of code.

    Returns:
        str: The indentation of that line.
    """
    spaces = []

    for char in line:
        if not char.isspace():
            break
        spaces.append(char)

    return "".join(spaces)


def solution_to_learner_format(
    cell_code: str,
    tag_start: str = "START CODE HERE",
    tag_end: str = "END CODE HERE",
) -> str:
    """Reformats the code in a cell by applying the rules defined by tags.

    Args:
        cell_code (str): The code of a notebook's cell represented as a string.
        tag_start (str, optional): Tag of start of code section. Defaults to "START CODE HERE".
        tag_end (str, optional): Tag of end of code section. Defaults to "END CODE HERE".

    Returns:
        str: Reformatted code.
    """

    tag_start_omit_block = "START OMIT BLOCK"
    tag_end_omit_block = "END OMIT BLOCK"
    tag_omit = "@OMIT"
    tag_keep = "@KEEP"
    tag_replace_equals = "@REPLACE EQUALS"
    tag_replace = "@REPLACE"

    code_block = False
    omit_block = False

    formatted_lines = []

    for ln in cell_code.splitlines():
        if tag_start in ln:
            code_block = True

        if tag_end in ln:
            code_block = False

        if tag_start_omit_block in ln:
            omit_block = True
            continue

        if tag_end_omit_block in ln:
            omit_block = False
            continue

        if (tag_omit in ln) or omit_block:
            continue

        code = ln.strip()
        first_cmd = code.split(" ")[0]

        if (tag_replace not in ln) and (
            first_cmd == "if" or first_cmd == "for" or first_cmd == "while"
        ):
            formatted_lines.append(ln)
            continue

        if tag_keep in ln:
            splitted = ln.split(f"# {tag_keep}")
            new_ln = splitted[0]
            formatted_lines.append(new_ln)
            continue

        if (tag_start not in ln) and code_block:
            if tag_replace_equals in ln:
                splitted = ln.split(tag_replace_equals)
                new_val = splitted[1]
                splitted_eq = splitted[0].split("=")
                new_ln = splitted_eq[0] + "=" + new_val
                formatted_lines.append(new_ln)
                continue

            if tag_replace in ln:
                ind = get_indentation(ln)
                splitted = ln.split(tag_replace)
                new_ln = ind + splitted[1].strip()
                formatted_lines.append(new_ln)
                continue

            if (" = " in ln) or (" += " in ln):
                splitted = ln.split("=")
                new_ln = splitted[0] + "= None"
                formatted_lines.append(new_ln)
                continue

        formatted_lines.append(ln)

    return "\n".join(formatted_lines)
