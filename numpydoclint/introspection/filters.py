"""Numpydoclint filters.

Filters do smart filtering of found objects and propagation of ignored errors. Filtering is performed solely with the built-in
[tokenize](https://docs.python.org/3/library/tokenize.html) module.
"""
import re
import tokenize
from collections import defaultdict
from pathlib import Path
from typing import DefaultDict, Optional, Set, Union

from numpydoclint.constants import DEFAULT_FILENAME_PATTERN, IGNORE_DIRECTIVE, R_IGNORE_DIRECTIVE
from numpydoclint.introspection.object_infos import ClassInfo, FunctionInfo, ModuleInfo
from numpydoclint.utils import parse_set


class FileFilter:
    """File filter.

    Filter paths based on ignore list and filename pattern.

    Parameters
    ----------
    filename_pattern : str, optional
        Filename pattern to include. Note that this is not a wildcard but a regex pattern, so for example `*.py` will not compile.
        The default is any file with a `.py` extension.
    ignore_paths : set of str or Path, optional
        Set of paths to ignore. Can be directories or files. If the path is a directory, all files in that directory will be ignored.
        If you need to ignore specific patterns in filenames, consider using `filename_pattern` instead.
    """

    def __init__(self, filename_pattern: Optional[str] = None, ignore_paths: Optional[Set[Path]] = None) -> None:
        self.filename_pattern = filename_pattern or DEFAULT_FILENAME_PATTERN
        self.ignore_paths = {x.resolve() for x in ignore_paths or []}

    def __call__(self, paths: Set[Path]) -> Set[Path]:
        """Filter files.

        Filter paths based on ignore list and filename pattern.

        Parameters
        ----------
        paths : set of Path
            Paths to filter.

        Returns
        -------
        set of Path
            Filtered paths.
        """
        paths = self._filter_by_path(paths=paths)
        return self._filter_by_pattern(paths=paths)

    def _filter_by_pattern(self, paths: Set[Path]) -> Set[Path]:
        """Filter files by pattern.

        Filter paths by filename pattern.

        Parameters
        ----------
        paths : set of Path
            Paths to filter.

        Returns
        -------
        set of Path
            Filtered paths.
        """
        return {path for path in paths if re.match(pattern=self.filename_pattern, string=path.name)}

    def _filter_by_path(self, paths: Set[Path]) -> Set[Path]:
        """Filter files by path.

        Filter paths based on ignore list.

        Parameters
        ----------
        paths : set of Path
            Paths to filter.

        Returns
        -------
        set of Path
            Filtered paths.
        """

        def ignored(path: Path) -> bool:
            path = path.resolve()
            return any(path == x or path.is_relative_to(x) for x in self.ignore_paths)

        return {x for x in paths if not ignored(x)}


class FilterInfo:
    """Filter info.

    Line numbers of the objects and error codes to filter.

    Parameters
    ----------
    ignore_objects : set of int
        Lines of objects to ignore.
    r_ignore_objects : set of int
        Lines of objects to ignore recursively (i.e. ignore the object itself and all child objects).
    ignore_errors : defaultdict
        Mapping between the lines of objects and set of error codes to ignore.
    r_ignore_errors : defaultdict
        Mapping between the lines of objects and set of error codes to ignore recursively (i.e. ignore errors for the object itself
        and all the child objects).
    """

    def __init__(
        self,
        ignore_objects: Optional[Set[int]] = None,
        r_ignore_objects: Optional[Set[int]] = None,
        ignore_errors: Optional[DefaultDict[int, Set[str]]] = None,
        r_ignore_errors: Optional[DefaultDict[int, Set[str]]] = None,
    ) -> None:
        self.ignore_objects = ignore_objects or set()
        self.r_ignore_objects = r_ignore_objects or set()
        self.ignore_errors = ignore_errors or defaultdict(set)
        self.r_ignore_errors = r_ignore_errors or defaultdict(set)


class ObjectFilter:
    """Object filter.

    Filter objects based on special comment directives in the code.

    Parameters
    ----------
    directive : str, optional
        Comment pattern to use as a directive.
    r_directive : str, optional
        Comment pattern to use as a recursive directive. Must be different from `directive`.
    ignore_errors : set of str, optional
        Set of errors to propagate to all objects regardless of the comment directives.
    ignore_constructor : bool, default True
        Whether to ignore class constructors. Default is True.
    ignore_hidden : bool, default False
        Whether to ignore hidden objects. Hidden objects are objects whose names begin with an underscore (`_`). Note that this includes all
        dunder methods of the classes, but not hidden modules. The default is False.

    Raises
    ------
    ValueError
        If `ignore_constructor` is False and `ignore_hidden` is True.
    """

    def __init__(
        self,
        directive: str = IGNORE_DIRECTIVE,
        r_directive: str = R_IGNORE_DIRECTIVE,
        ignore_errors: Optional[Set[str]] = None,
        ignore_constructor: bool = True,
        ignore_hidden: bool = False,
    ) -> None:
        self.ignore_errors = ignore_errors or set()
        self.directive = re.compile(directive)
        self.r_directive = re.compile(r_directive)
        if not ignore_constructor and ignore_hidden:
            raise ValueError("Ignoring hidden objects while preserving class constructors is not allowed.")
        self.ignore_constructor = ignore_constructor
        self.ignore_hidden = ignore_hidden

    def __call__(self, path: Path, module_info: ModuleInfo) -> ModuleInfo:
        """Filter objects.

        Filter objects from the module and propagate ignore errors based on comment directives parsed from the module.

        Parameters
        ----------
        path : Path
            Module path.
        module_info : ModuleInfo
            Module info.

        Returns
        -------
        ModuleInfo
            Module info with filtered objects and propagated ignore errors.
        """
        filter_info = self._get_filter_info(path=path)
        module_info.ignore_errors_recursive(ignore_errors=self.ignore_errors)

        self._filter_module_info(module_info=module_info, filter_info=filter_info)
        self._filter_function_infos(parent_info=module_info, filter_info=filter_info)
        self._filter_class_infos(module_info=module_info, filter_info=filter_info)

        return module_info

    def _get_filter_info(self, path: Path) -> FilterInfo:
        """Get filter info.

        Parse comment directives from the module and return filter info.

        Parameters
        ----------
        path : Path
            Module path.

        Returns
        -------
        FilterInfo
            Filter info.
        """
        with open(path, mode="rb") as file:
            comment_infos = [x for x in tokenize.tokenize(file.readline) if x.type == tokenize.COMMENT]

        ignore_objects = set()
        r_ignore_objects = set()
        ignore_errors = defaultdict(set)
        r_ignore_errors = defaultdict(set)

        for comment_info in comment_infos:
            lineno = comment_info.start[0]

            match = self.r_directive.search(comment_info.string)
            if match and match.group(1):
                r_ignore_errors[lineno] = parse_set(match.group(1))
                continue
            if match:
                r_ignore_objects.add(lineno)
                continue

            match = self.directive.search(comment_info.string)
            if match and match.group(1):
                ignore_errors[lineno] = parse_set(match.group(1))
            elif match:
                ignore_objects.add(lineno)

        return FilterInfo(
            ignore_objects=ignore_objects, r_ignore_objects=r_ignore_objects, ignore_errors=ignore_errors, r_ignore_errors=r_ignore_errors
        )

    @staticmethod
    def _filter_module_info(module_info: ModuleInfo, filter_info: FilterInfo) -> None:
        """Filter module info.

        Filter module info and propagate ignore errors based on the top-most directive.

        Parameters
        ----------
        module_info : ModuleInfo
            Module info.
        filter_info : FilterInfo
            Filter info.
        """
        if filter_info.r_ignore_objects and min(filter_info.r_ignore_objects) < module_info.first_statement_lineno:
            module_info.function_infos = []
            module_info.class_infos = []
            module_info.ignore_self = True
        elif filter_info.ignore_objects and min(filter_info.ignore_objects) < module_info.first_statement_lineno:
            module_info.ignore_self = True

        first_r_ignore_errors_lineno = min(filter_info.r_ignore_errors.keys()) if filter_info.r_ignore_errors else 1
        first_ignore_errors_lineno = min(filter_info.ignore_errors.keys()) if filter_info.ignore_errors else 1

        if first_r_ignore_errors_lineno < module_info.first_statement_lineno:
            module_info.ignore_errors_recursive(ignore_errors=filter_info.r_ignore_errors[first_r_ignore_errors_lineno])
        if first_ignore_errors_lineno < module_info.first_statement_lineno:
            module_info.ignore_errors.update(filter_info.ignore_errors[first_ignore_errors_lineno])

    def _filter_function_infos(self, parent_info: Union[ModuleInfo, ClassInfo], filter_info: FilterInfo) -> None:
        """Filter function infos.

        Filter functions and propagate ignore errors to functions of module info or class info based on filter info.

        Parameters
        ----------
        parent_info : ModuleInfo or ClassInfo
            Module or class info.
        filter_info : FilterInfo
            Filter info.
        """
        parent_info.function_infos = [x for x in parent_info.function_infos if not self._ignored(x, filter_info=filter_info)]
        if isinstance(parent_info, ClassInfo) and self.ignore_constructor:
            parent_info.function_infos = [x for x in parent_info.function_infos if x.name.split(".")[-1] != "__init__"]
        for function_info in parent_info.function_infos:
            function_info.ignore_errors.update(filter_info.r_ignore_errors[function_info.lineno])
            function_info.ignore_errors.update(filter_info.ignore_errors[function_info.lineno])

    def _filter_class_infos(self, module_info: ModuleInfo, filter_info: FilterInfo) -> None:
        """Filter class infos.

        Filter classes and propagate ignore errors to classes of module info based on the filter info.

        Parameters
        ----------
        module_info : ModuleInfo
            Module info.
        filter_info : FilterInfo
            Filter info.
        """
        module_info.class_infos = [x for x in module_info.class_infos if not self._ignored(x, filter_info=filter_info)]

        for class_info in module_info.class_infos:
            self._filter_function_infos(parent_info=class_info, filter_info=filter_info)

            if class_info.lineno in filter_info.ignore_objects:
                class_info.ignore_self = True
            class_info.ignore_errors.update(filter_info.ignore_errors[class_info.lineno])
            class_info.ignore_errors_recursive(ignore_errors=filter_info.r_ignore_errors[class_info.lineno])

    def _ignored(self, object_info: Union[FunctionInfo, ClassInfo], filter_info: FilterInfo) -> bool:
        """Return whether the object should be ignored.

        Class info is only ignored if it is in the recursively ignored objects.

        Parameters
        ----------
        object_info : FunctionInfo or ClassInfo
            Object info.
        filter_info : FilterInfo
            Filter info.

        Returns
        -------
        bool
            Whether the object should be ignored.
        """
        return (
            object_info.lineno in filter_info.r_ignore_objects
            or (isinstance(object_info, FunctionInfo) and object_info.lineno in filter_info.ignore_objects)
            or (self.ignore_hidden and object_info.name.split(".")[-1].startswith("_"))
        )
