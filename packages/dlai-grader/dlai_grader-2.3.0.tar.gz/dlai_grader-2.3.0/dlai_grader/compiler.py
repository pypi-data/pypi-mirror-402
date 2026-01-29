import ast
from types import ModuleType
from contextlib import nullcontext
from nbformat.notebooknode import NotebookNode
from .io import suppress_stdout_stderr


def compile_module(
    code_as_str: str,
    module_name: str,
    wipe_global_state: bool = False,
    verbose: bool = True,
) -> ModuleType:
    """Compiles the string representation of some code and returns a compiled module.
    Args:
        code_as_str (str): Code represented as string.
        module_name (str): Name of the module.
        wipe_global_state (bool): If true then no global state is compiled. Defaults to False.
        verbose (bool): Whether to print out streams as a result of compilation. Defaults to True.
    Returns:
        ModuleType: The actual module that can be used to call functions/variables/etc.
    """
    code_ast = ast.parse(code_as_str)

    if wipe_global_state:
        for node in code_ast.body[:]:
            if not isinstance(
                node, (ast.FunctionDef, ast.Import, ast.ImportFrom, ast.ClassDef)
            ):
                code_ast.body.remove(node)

    with nullcontext() if verbose else suppress_stdout_stderr():
        module = ModuleType(module_name)
        code = compile(code_ast, f"{module_name}.py", "exec")
        exec(code, module.__dict__)
        return module


def compile_partial_module(
    notebook: NotebookNode,
    module_name: str,
    verbose: bool = True,
    exit_on_error: bool = False,
    debug_mode: bool = False,
) -> ModuleType:
    """Iterates over the code cells of a notebook and includes the ones that run to the compiled module.
    Args:
        notebook (NotebookNode): Notebook from learner.
        module_name (str): Name of the module.
        verbose (bool): Whether to print out streams as a result of compilation. Defaults to True.
        exit_on_error (bool): Whether to stop compilation if an exception is found. Defaults to False.
        debug_mode (bool): Whether to print out cells where exceptions occurred. Defaults to False.
    Returns:
        ModuleType: The actual module that can be used to call functions/variables/etc.
    """
    code_cells = [cell.source for cell in notebook.cells if cell.cell_type == "code"]
    module = ModuleType(module_name)

    for i, cell_code in enumerate(code_cells):
        try:
            compiled_code = compile(cell_code, f"<cell {i}>", "exec")

            with nullcontext() if verbose else suppress_stdout_stderr():
                exec(compiled_code, module.__dict__)

        except Exception as e:
            if exit_on_error:
                if debug_mode:
                    print(
                        f"Error during execution of cell. Aborting full compilation.\n\nContents:\n\n{cell_code}\n\nException:\n\n{e}\n"
                    )
                break

            if debug_mode:
                print(
                    f"Error during execution of cell but kept going.\n\nContents:\n\n{cell_code}\n\nException:\n\n{e}\n"
                )
            continue

    return module
