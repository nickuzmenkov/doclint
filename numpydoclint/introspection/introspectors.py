"""Numpydoclint introspectors.

Introspectors search for files and objects within files. The main introspector also applies filters to the resulting set of objects.
Object introspection is performed solely with the built-in [ast](https://docs.python.org/3/library/ast.html) module.
"""
import ast
import sys
from pathlib import Path
from typing import List, Optional, Sequence, Set, Union

from numpydoclint.introspection.filters import FileFilter, ObjectFilter
from numpydoclint.introspection.object_infos import ClassInfo, FunctionInfo, ModuleInfo, ObjectInfo


class Introspector:
    """Main introspector.

    This class is responsible for introspecting all modules, functions, classes, and methods within specified files and directories
    end-to-end. It uses filters to exclude ignored objects and errors, and returns a list of object information.

    Parameters
    ----------
    ignore_errors : set of str, optional
        Set of error codes to ignore (for example, `{"ES01", "GL08"}`). See the Numpydoc documentation for a complete reference.
    ignore_paths : set of str or Path, optional
        Set of paths to ignore. Can be directories or files. If the path is a directory, all files in that directory will be ignored.
        If you need to ignore specific patterns in filenames, consider using `filename_pattern` instead.
    ignore_hidden : bool, default False
        Whether to ignore hidden objects. Hidden objects are objects whose names begin with an underscore (`_`). Note that this includes all
        dunder methods of the classes, but not hidden modules. The default is False.
    filename_pattern : str, optional
        Filename pattern to include. Note that this is not a wildcard but a regex pattern, so for example `*.py` will not compile.
        The default is any file with a `.py` extension.
    """

    def __init__(
        self,
        ignore_errors: Optional[Set[str]] = None,
        ignore_paths: Optional[Set[Path]] = None,
        ignore_hidden: bool = False,
        filename_pattern: Optional[str] = None,
    ) -> None:
        self._file_introspector = FileIntrospector()
        self._file_filter = FileFilter(filename_pattern=filename_pattern, ignore_paths=ignore_paths)
        self._object_introspector = ObjectIntrospector()
        self._object_filter = ObjectFilter(ignore_errors=ignore_errors, ignore_hidden=ignore_hidden)

    def __call__(self, paths: Set[Path]) -> Sequence[ObjectInfo]:
        """Perform introspection on the given paths.

        This method returns a list of object information for all modules found under the given paths.

        Parameters
        ----------
        paths : set of Path
            The paths to introspect. These can be either folders or modules. If a path is a directory, all modules within it that match
            the `filename_pattern` will be introspected. All paths must be in `sys.path`.

        Returns
        -------
        list of ObjectInfo
            A list of object information for all introspected objects.
        """
        module_paths = self._file_introspector(paths=paths)
        module_paths = self._file_filter(paths=module_paths)

        object_infos: Sequence[ObjectInfo] = []

        for module_path in sorted(module_paths):
            module_info = self._object_introspector(path=module_path)
            module = self._object_filter(path=module_path, module_info=module_info)
            object_infos += module.list_object_infos()  # type: ignore

        return object_infos


class FileIntrospector:
    """File introspector.

    File introspector is responsible for introspecting a set of paths. It recursively searches for all files under the given paths and
    returns a set of all discovered files, regardless of their extension or other conditions.
    """

    def __call__(self, paths: Set[Path]) -> Set[Path]:
        """Introspect given paths.

        Return set of all paths under the given paths.

        Parameters
        ----------
        paths : set of Path
            The paths to introspect. These can be either folders or files. If a path is a directory, the method will recursively search for
            all files under it. If a path is a file, it will be added directly to the resulting set.

        Returns
        -------
        set of Path
            A set of all discovered file paths.

        Raises
        ------
        FileNotFoundError
            If at least one of the provided paths does not exist.
        """
        self._validate_paths(paths=paths)
        module_paths = []

        for path in paths:
            if path.is_file():
                module_paths.append(path)
            else:
                module_paths += path.rglob("*")

        return set(module_paths)

    @staticmethod
    def _validate_paths(paths: Set[Path]) -> None:
        """Validate paths.

        Check that all provided paths exist.

        Parameters
        ----------
        paths : set of Path
            The paths to validate. Each path must exist.

        Raises
        ------
        FileNotFoundError
            If at least one of the provided paths does not exist.
        """
        non_existent = [x for x in paths if not x.exists()]
        if non_existent:
            raise FileNotFoundError(f"Not found files or directories: {[str(x) for x in non_existent]}.")


class ObjectIntrospector:
    """Object introspector.

    Object introspector is responsible for introspecting a Python module and extracting information about its structure. It identifies all
    functions, classes, and methods within the given module and encapsulates this information into a ModuleInfo object.
    """

    def __call__(self, path: Path) -> ModuleInfo:
        """Introspect given module.

        Return module info containing information about all functions, classes, and methods of the module.

        Parameters
        ----------
        path : Path
            The path of the Python module to introspect. The file must be a valid Python module with correct syntax and must be present in
            `sys.path`.

        Returns
        -------
        ModuleInfo
            A ModuleInfo object containing information about all functions, classes, and methods of the module.
        """
        with open(path, mode="r", encoding="utf-8") as file:
            content = file.read()
            tree = ast.parse(content)

        first_statement_lineno = tree.body[0].lineno if tree.body else len(content.split("\n"))
        module_info = ModuleInfo(
            name=self._get_fully_qualified_name(path=path), path=path, lineno=1, first_statement_lineno=first_statement_lineno
        )

        function_defs = self._list_function_defs(tree=tree)
        class_defs = self._list_class_defs(tree=tree)

        for function_def in function_defs:
            module_info.function_infos.append(
                FunctionInfo(name=module_info.name + f".{function_def.name}", path=path, lineno=function_def.lineno)
            )
        for class_def in class_defs:
            class_info = ClassInfo(name=module_info.name + f".{class_def.name}", path=path, lineno=class_def.lineno)
            method_defs = self._list_function_defs(tree=class_def)
            class_info.function_infos = [
                FunctionInfo(name=module_info.name + f".{class_def.name}.{x.name}", path=path, lineno=x.lineno) for x in method_defs
            ]
            module_info.class_infos.append(class_info)
        return module_info

    @staticmethod
    def _get_fully_qualified_name(path: Path) -> str:
        """Return fully qualified name of the module.

        Refer to the examples section for more information.

        Parameters
        ----------
        path : Path
            The path of the Python module. The module must be present in `sys.path`.

        Returns
        -------
        str
            The fully qualified name of the module.

        Raises
        ------
        ValueError
            If the module is not found in `sys.path`.

        Examples
        --------
        ``` py
        >>> ObjectIntrospector._get_fully_qualified_name(Path("midgard", "thor.py"))
        midgard.thor
        ```
        """
        abs_path = path.resolve()
        for sys_path in map(Path, sys.path):
            try:
                relative_path = abs_path.relative_to(sys_path.resolve())
            except ValueError:
                continue
            else:
                return str(relative_path.with_suffix("")).replace("/", ".")
        raise ValueError(f"Cannot find {path} in sys.path.")

    @staticmethod
    def _list_function_defs(tree: Union[ast.Module, ast.ClassDef]) -> List[ast.FunctionDef]:  # numpydoclint: ignore=ES01
        """Extract all function definitions from the given AST tree.

        Parameters
        ----------
        tree : ast.Module or ast.ClassDef
            An AST tree representing a Python module or class.

        Returns
        -------
        list of ast.FunctionDef
            A list of AST nodes representing function definitions.
        """
        return [x for x in tree.body if isinstance(x, ast.FunctionDef)]

    @staticmethod
    def _list_class_defs(tree: ast.Module) -> List[ast.ClassDef]:  # numpydoclint: ignore=ES01
        """Extract all class definitions from the given AST tree.

        Parameters
        ----------
        tree : ast.Module
            An AST tree representing a Python module.

        Returns
        -------
        list of ast.ClassDef
            A list of AST nodes representing class definitions.
        """
        return [x for x in tree.body if isinstance(x, ast.ClassDef)]
