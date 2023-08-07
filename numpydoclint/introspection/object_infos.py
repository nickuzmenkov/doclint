"""Numpydoclint object infos.

This module provides classes to store information about Python objects such as modules, functions, classes, and methods.
These classes include object-wise error filters and additional metadata. Higher-level classes like ClassInfo and ModuleInfo also provide
methods to operate on their child entities recursively.
"""
from pathlib import Path
from typing import List, Optional, Sequence, Set


class ObjectInfo:
    """Object info.

    This class encapsulates information about a Python object. This is a base class for other object information classes. It includes
    details such as the object's name, path, line number where it is defined, and a set of error codes to ignore during validation.

    Parameters
    ----------
    name : str
        The name of the object. This should always start with the module name (e.g., `thor` for a module, `thor.Mjolnir` for a class, and
        `thor.Mjolnir.strike` or `thor.disguise` for a method or function, respectively).
    path : Path
        The path of the module that contains the object. This is used to create a link to the object.
    lineno : int
        The line number where the object is defined. This is required to create a link to the object.
    ignore_errors : set of str, optional
        A set of error codes to ignore during validation (e.g., `{"ES01", "GL08"}`). Refer to the
        [Numpydoc Documentation](https://numpydoc.readthedocs.io/en/latest/validation.html#built-in-validation-checks)
        for a complete list of error codes.
    """

    def __init__(self, name: str, path: Path, lineno: int, ignore_errors: Optional[Set[str]] = None) -> None:
        self.name = name
        self.lineno = lineno
        self.link = f"{path}:{lineno}"
        self.ignore_errors = ignore_errors or set()


class FunctionInfo(ObjectInfo):
    """Function info.

    This class encapsulates information about a Python object. It includes details such as the object's name, path, line number where it is
    defined, and a set of error codes to ignore during validation.

    Parameters
    ----------
    name : str
        The name of the object. This should always start with the module name (e.g., `thor` for a module, `thor.Mjolnir` for a class, and
        `thor.Mjolnir.strike` or `thor.disguise` for a method or function, respectively).
    path : Path
        The path of the module that contains the object. This is used to create a link to the object.
    lineno : int
        The line number where the object is defined. This is required to create a link to the object.
    ignore_errors : set of str, optional
        A set of error codes to ignore during validation (e.g., `{"ES01", "GL08"}`). Refer to the
        [Numpydoc Documentation](https://numpydoc.readthedocs.io/en/latest/validation.html#built-in-validation-checks)
        for a complete list of error codes.
    """


class ClassInfo(ObjectInfo):
    """Class info.

    This class encapsulates information about a Python class. It includes details such as the class's name, path, line number where it is
    defined, and information about its methods. It also provides methods to list all object information and propagate ignored errors
    recursively.

    Parameters
    ----------
    name : str
        The name of the class. This should always start with the module name (e.g., `thor` for a module, `thor.Mjolnir` for a class, and
        `thor.Mjolnir.strike` or `thor.disguise` for a method or function, respectively).
    path : Path
        The path of the module that contains the class. This is used to create a link to the class.
    lineno : int
        The line number where the class is defined. This is required to create a link to the class.
    ignore_errors : set of str, optional
        A set of error codes to ignore (e.g., `{"ES01", "GL08"}`). Refer to the
        [Numpydoc Documentation](https://numpydoc.readthedocs.io/en/latest/validation.html#built-in-validation-checks)
        for a complete list of error codes.
    function_infos : list of FunctionInfo, optional
        A list of FunctionInfo objects representing the methods in the class.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        name: str,
        path: Path,
        lineno: int,
        ignore_errors: Optional[Set[str]] = None,
        function_infos: Optional[List[FunctionInfo]] = None,
    ) -> None:
        super().__init__(name=name, path=path, lineno=lineno, ignore_errors=ignore_errors)
        self.function_infos = function_infos or []
        self.ignore_self = False

    def list_object_infos(self) -> Sequence[ObjectInfo]:
        """Return a list of all ObjectInfo objects associated with the class.

        This includes the class itself (unless it's ignored) and all its methods.

        Returns
        -------
        list of ObjectInfo
            A list of ObjectInfo objects representing the class and its methods.
        """
        if self.ignore_self:
            return self.function_infos
        return [self] + self.function_infos  # type: ignore

    def ignore_errors_recursive(self, ignore_errors: Set[str]) -> None:
        """Propagate a set of ignored error codes to all methods in the class.

        This method updates the `ignore_errors` attribute of the class and its methods.

        Parameters
        ----------
        ignore_errors : set of str
            A set of error codes to propagate (e.g., `{"ES01", "GL08"}`). Refer to the
            [Numpydoc Documentation](https://numpydoc.readthedocs.io/en/latest/validation.html#built-in-validation-checks)
            for a complete list of error codes.
        """
        self.ignore_errors.update(ignore_errors)

        for method_info in self.function_infos:
            method_info.ignore_errors.update(ignore_errors)


class ModuleInfo(ObjectInfo):
    """Module info.

    This class encapsulates information about a Python module. It includes details such as the module's name, path,
    line number where it is defined, and information about its functions and classes. It also provides methods to list all object
    information and propagate ignored errors recursively.

    Parameters
    ----------
    name : str
        The name of the module. This should always start with the module name (e.g., `thor` for a module, `thor.Mjolnir` for a class, and
        `thor.Mjolnir.strike` or `thor.disguise` for a method or function, respectively).
    path : Path
        The path of the module. This is used to create a link to the module.
    lineno : int
        The line number where the module is defined. This is required to create a link to the module.
    ignore_errors : set of str, optional
        A set of error codes to ignore (e.g., `{"ES01", "GL08"}`). Refer to the
        [Numpydoc Documentation](https://numpydoc.readthedocs.io/en/latest/validation.html#built-in-validation-checks)
        for a complete list of error codes.
    function_infos : list of FunctionInfo, optional
        A list of FunctionInfo objects representing the functions in the module.
    class_infos : list of ClassInfo, optional
        A list of ClassInfo objects representing the classes in the module.
    first_statement_lineno : int, optional
        The line number of the first statement in the module. This can be different from 1 if the module starts with whitespace, a
        docstring, or a comment. If None, 1 is used.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        name: str,
        path: Path,
        lineno: int,
        ignore_errors: Optional[Set[str]] = None,
        function_infos: Optional[List[FunctionInfo]] = None,
        class_infos: Optional[List[ClassInfo]] = None,
        first_statement_lineno: Optional[int] = None,
    ) -> None:
        super().__init__(name=name, path=path, lineno=lineno, ignore_errors=ignore_errors)
        self.function_infos = function_infos or []
        self.class_infos = class_infos or []
        self.ignore_self = False
        self.first_statement_lineno = first_statement_lineno or 1

    def list_object_infos(self) -> Sequence[ObjectInfo]:
        """Return a list of all ObjectInfo objects associated with the module.

        This includes the module itself (unless it's ignored), all its functions, and all the functions and methods of its classes.

        Returns
        -------
        list of ObjectInfo
            A list of ObjectInfo objects representing the module and its functions and classes.
        """
        if self.ignore_self:
            object_infos = []
        else:
            object_infos = [self]
        object_infos += self.function_infos  # type: ignore

        for class_info in self.class_infos:
            object_infos += class_info.list_object_infos()  # type: ignore

        return object_infos

    def ignore_errors_recursive(self, ignore_errors: Set[str]) -> None:
        """Propagate a set of ignored error codes to all functions and classes in the module.

        This method updates the `ignore_errors` attribute of the module, its functions, and its classes.

        Parameters
        ----------
        ignore_errors : set of str
            A set of error codes to propagate (e.g., `{"ES01", "GL08"}`). Refer to the
            [Numpydoc Documentation](https://numpydoc.readthedocs.io/en/latest/validation.html#built-in-validation-checks)
            for a complete list of error codes.
        """
        self.ignore_errors.update(ignore_errors)

        for class_info in self.class_infos:
            class_info.ignore_errors_recursive(ignore_errors=ignore_errors)
        for function_info in self.function_infos:
            function_info.ignore_errors.update(ignore_errors)
