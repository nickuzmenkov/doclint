"""Test introspects."""
import sys
import textwrap
from pathlib import Path
from unittest import mock

import pytest

from numpydoclint.introspection.introspectors import FileIntrospector, Introspector, ObjectIntrospector
from numpydoclint.introspection.object_infos import ClassInfo, FunctionInfo, ModuleInfo
from tests.utils import get_name


class TestFileIntrospector:
    """Test file introspector."""

    @pytest.fixture
    def file_introspector(self) -> FileIntrospector:
        return FileIntrospector()

    def test_empty_paths(self, file_introspector: FileIntrospector):
        """Test call with empty paths.

        Introspection must still succeed.
        """
        modules = file_introspector(paths=[])
        assert not modules

    def test_non_existent_path(self, file_introspector: FileIntrospector):
        """Test call with non-existent path.

        Introspector must raise exception.
        """
        non_existent_path = Path(get_name())

        with pytest.raises(FileNotFoundError, match=f"Not found files or directories") as exception:
            file_introspector(paths=[non_existent_path])

        assert str(non_existent_path) in str(exception.value)

    def test_call(self, file_introspector: FileIntrospector, tmp_path: Path):
        """Test call with nested paths, modules, and directories."""
        package = Path(tmp_path, get_name())
        module_1 = Path(tmp_path, get_name())
        module_2 = Path(package, get_name())

        package.mkdir()
        module_1.touch()
        module_2.touch()

        modules = file_introspector(paths=[package, module_1])
        assert set(modules) == {module_1, module_2}


class TestObjectIntrospector:
    """Test object introspector."""

    @pytest.fixture
    def object_introspector(self) -> ObjectIntrospector:
        return ObjectIntrospector()

    def test_path_not_in_sys_path(self, object_introspector: ObjectIntrospector, tmp_path: Path):
        """Test that an error is raised if the path is not in `sys.path`."""
        path = Path(tmp_path, get_name())
        path.touch()

        with pytest.raises(ValueError, match=f"Cannot find {path} in sys.path."):
            object_introspector(path=path)

    def test_empty_module(self, object_introspector: ObjectIntrospector, tmp_path: Path):
        """Test introspection of an empty module.

        Test that the first statement lineno is figured out correctly.
        """
        path = Path(tmp_path, get_name())
        path.touch()

        with mock.patch.object(sys, "path", [str(tmp_path)]):
            module_info = object_introspector(path=path)

        assert module_info.name == path.name
        assert module_info.lineno == 1
        assert module_info.first_statement_lineno == 1
        assert not module_info.function_infos
        assert not module_info.class_infos

    def test_first_statement_lineno(self, object_introspector: ObjectIntrospector, tmp_path: Path):
        """Test that the first statement lineno is figured out correctly when the module is not empty."""
        path = Path(tmp_path, get_name())
        with open(path, "w") as file:
            file.write("\n\nimport os")

        with mock.patch.object(sys, "path", [str(tmp_path)]):
            module_info = object_introspector(path=path)

        assert module_info.first_statement_lineno == 3

    def test_function(self, object_introspector: ObjectIntrospector, tmp_path: Path):
        """Test introspection of functions."""
        path = Path(tmp_path, get_name())
        with open(path, "w") as file:
            file.write(
                textwrap.dedent(
                    """
                    def foo():  # 2
                        print("Hello, world!")
                    """
                )
            )

        with mock.patch.object(sys, "path", [str(tmp_path)]):
            module_info = object_introspector(path=path)

        assert not module_info.class_infos
        assert len(module_info.function_infos) == 1

        function_info = module_info.function_infos[0]
        assert function_info.name == f"{path.name}.foo"
        assert function_info.lineno == 2

    def test_empty_class(self, object_introspector: ObjectIntrospector, tmp_path: Path):
        """Test introspection of an empty class."""
        path = Path(tmp_path, get_name())
        with open(path, "w") as file:
            file.write(
                textwrap.dedent(
                    """
                    class Foo:  # 2
                        foo = "Hello, World!"
                    """
                )
            )

        with mock.patch.object(sys, "path", [str(tmp_path)]):
            module_info = object_introspector(path=path)

        assert not module_info.function_infos
        assert len(module_info.class_infos) == 1

        class_info = module_info.class_infos[0]
        assert class_info.name == f"{path.name}.Foo"
        assert class_info.lineno == 2
        assert not class_info.function_infos

    def test_class_with_method(self, object_introspector: ObjectIntrospector, tmp_path: Path):
        """Test introspection of class with methods."""
        path = Path(tmp_path, get_name())
        with open(path, "w") as file:
            file.write(
                textwrap.dedent(
                    """
                    class Foo:  # 2
                        def foo(self):  # 3
                            print("Hello, world!")
                    """
                )
            )

        with mock.patch.object(sys, "path", [str(tmp_path)]):
            module_info = object_introspector(path=path)

        assert not module_info.function_infos
        assert len(module_info.class_infos) == 1

        class_info = module_info.class_infos[0]
        assert len(class_info.function_infos) == 1

        method_info = class_info.function_infos[0]
        assert method_info.name == f"{path.name}.Foo.foo"
        assert method_info.lineno == 3

    def test_nested_objects(self, object_introspector: ObjectIntrospector, tmp_path: Path):
        """Test that all nested objects are ignored and have no effect on introspection."""
        path = Path(tmp_path, get_name())
        with open(path, "w") as file:
            file.write(
                textwrap.dedent(
                    """
                    class Foo:  # 2
                        class Bar:  # 3
                            pass
                            
                        def foo(self):  # 6
                            class Bar:  # 7
                                pass
                            
                            def bar():  # 10
                                pass
                    
                    def foo():  # 13
                        class Bar:  # 14
                            pass
                        
                        def bar():  # 17
                            pass
                    """
                )
            )

        with mock.patch.object(sys, "path", [str(tmp_path)]):
            module_info = object_introspector(path=path)

        assert len(module_info.function_infos) == 1
        assert len(module_info.class_infos) == 1

        function_info = module_info.function_infos[0]
        assert function_info.name == f"{path.name}.foo"
        assert function_info.lineno == 13

        class_info = module_info.class_infos[0]
        assert class_info.name == f"{path.name}.Foo"
        assert class_info.lineno == 2
        assert len(class_info.function_infos) == 1

        method_info = class_info.function_infos[0]
        assert method_info.name == f"{path.name}.Foo.foo"
        assert method_info.lineno == 6


class TestIntrospector:
    """Test introspector.

    More specific cases and edge cases are tested in introspects and filters tests.
    """

    @pytest.fixture
    def introspector(self) -> Introspector:
        return Introspector()

    def test_empty_paths(self, introspector: Introspector):
        """Test call with empty paths."""
        assert introspector(paths=set()) == []

    def test_ignore_all_paths(self, tmp_path: Path):
        """Test ignore all paths the introspector is called with."""
        module = Path(tmp_path, get_name(extension=".py"))
        module.touch()

        introspector = Introspector(ignore_paths={module})
        assert introspector(paths={module}) == []

    def test_call(self, introspector: Introspector, tmp_path: Path):
        """Test call with both module and package paths.

        More specific cases and edge cases are tested in introspects and filters tests.
        """
        module_1 = Path(tmp_path, get_name(extension=".py"))
        package_1 = Path(tmp_path, get_name())
        module_2 = Path(package_1, get_name(extension=".py"))
        package_2 = Path(tmp_path, get_name())

        package_1.mkdir()
        package_2.mkdir()

        with open(module_1, "w") as file:
            file.write(
                textwrap.dedent(
                    """
                    # numpydoclint: ignore-all A00

                    def foo():  # 4
                        pass

                    class Foo:  # 7  # numpydoclint: ignore-all
                        def foo(self):  # 8
                            pass
                    """
                )
            )

        with open(module_2, "w") as file:
            file.write(
                textwrap.dedent(
                    """
                    def bar():  # 2  # numpydoclint: ignore
                        pass

                    class Bar:  # 5  # numpydoclint: ignore-all=B00,B01
                        def bar(self):  # 6  # numpydoclint: ignore=C00
                            pass
                    """
                )
            )

        with mock.patch.object(sys, "path", [tmp_path]):
            object_infos = introspector(paths={module_1, package_1, package_2})

        # module_1
        module_info = [x for x in object_infos if isinstance(x, ModuleInfo) and (x.name == module_1.stem)][0]
        assert module_info.lineno == 1
        assert module_info.link == f"{module_1}:1"
        assert module_info.ignore_errors == {"A00"}
        assert not module_info.ignore_self
        assert module_info.first_statement_lineno == 4

        # module_1.foo
        function_info = [x for x in object_infos if isinstance(x, FunctionInfo) and (x.name == f"{module_1.stem}.foo")][0]
        assert function_info.lineno == 4
        assert function_info.link == f"{module_1}:4"
        assert function_info.ignore_errors == {"A00"}

        # module_1.Foo
        assert not [x for x in object_infos if isinstance(x, ClassInfo) and (x.name == f"{module_1.stem}.Foo")]
        # module_1.Foo.foo
        assert not [x for x in object_infos if isinstance(x, FunctionInfo) and (x.name == f"{module_1.stem}.Foo.foo")]

        # package_1.module_2
        module_info = [x for x in object_infos if isinstance(x, ModuleInfo) and (x.name == f"{package_1.name}.{module_2.stem}")][0]
        assert module_info.lineno == 1
        assert module_info.link == f"{module_2}:1"
        assert not module_info.ignore_errors
        assert not module_info.ignore_self
        assert module_info.first_statement_lineno == 2

        # package_1.module_2.bar
        assert not [x for x in object_infos if isinstance(x, ClassInfo) and (x.name == f"{package_1.name}.{module_2.stem}.bar")]

        # package_1.module_2.Bar
        class_info = [x for x in object_infos if isinstance(x, ClassInfo) and (x.name == f"{package_1.name}.{module_2.stem}.Bar")][0]
        assert class_info.lineno == 5
        assert class_info.link == f"{module_2}:5"
        assert class_info.ignore_errors == {"B00", "B01"}
        assert not class_info.ignore_self

        # package_1.module_2.Bar.bar
        function_info = [
            x for x in object_infos if isinstance(x, FunctionInfo) and (x.name == f"{package_1.name}.{module_2.stem}.Bar.bar")
        ][0]
        assert function_info.lineno == 6
        assert function_info.link == f"{module_2}:6"
        assert function_info.ignore_errors == {"B00", "B01", "C00"}
