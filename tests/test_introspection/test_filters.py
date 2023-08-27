"""Test filters."""
import textwrap
from collections import defaultdict
from pathlib import Path

import pytest

from numpydoclint.introspection.filters import FileFilter, FilterInfo, ObjectFilter
from numpydoclint.introspection.object_infos import ClassInfo, FunctionInfo, ModuleInfo
from tests.utils import get_name, get_number


class TestFileFilter:
    """Test file filter."""

    @pytest.fixture
    def file_filter(self) -> FileFilter:
        return FileFilter()

    def test_filter_empty_list(self, file_filter: FileFilter):
        """Test that file filter handles empty list."""
        assert file_filter(paths=set()) == set()

    def test_filter_by_default_pattern(self, file_filter: FileFilter, tmp_path: Path):
        """Test that filtering by default pattern returns only python files."""
        paths = [
            Path(tmp_path, get_name(extension=".py")),
            Path(tmp_path, get_name(extension=".pyi")),
            Path(tmp_path, get_name()),
        ]

        assert file_filter(paths=set(paths)) == {paths[0]}

    def test_filter_by_custom_pattern(self, file_filter: FileFilter, tmp_path: Path):
        """Test that filtering by custom pattern."""
        paths = [
            Path(tmp_path, get_name(extension=".py")),
            Path(tmp_path, get_name(prefix="__", extension=".py")),
            Path(tmp_path, get_name()),
        ]

        file_filter.filename_pattern = "^(?!__).+\\.py$"
        assert file_filter(paths=set(paths)) == {paths[0]}

    def test_filter_by_filename(self, file_filter: FileFilter, tmp_path: Path):
        """Test filtering by separate filenames."""
        paths = [
            Path(tmp_path, get_name(extension=".py")),
            Path(tmp_path, get_name(extension=".py")),
            Path(tmp_path, get_name(extension=".py")),
        ]

        file_filter.ignore_paths = paths[1:3]
        assert file_filter(paths=set(paths)) == {paths[0]}

    def test_filter_by_directory(self, file_filter: FileFilter, tmp_path: Path):
        """Test that filtering by directory filters out all nested files."""
        directory = Path(tmp_path, get_name())

        paths = [
            Path(tmp_path, get_name(extension=".py")),
            Path(directory, get_name(extension=".py")),
            Path(directory, get_name(extension=".py")),
        ]

        file_filter.ignore_paths = [directory]
        assert file_filter(paths=set(paths)) == {paths[0]}


class TestObjectFilter:
    """Test object filter.

    Tests of auxiliary methods are organized into nested test classes.
    """

    @pytest.fixture
    def object_filter(self) -> ObjectFilter:
        return ObjectFilter()

    @pytest.fixture
    def empty_filter_info(self) -> FilterInfo:
        return FilterInfo()

    @pytest.fixture
    def empty_module_info(self) -> ModuleInfo:
        return ModuleInfo(name=get_name(), path=Path(get_name()), lineno=1)

    class TestGetFilterInfo:
        def test_get_filter_info_empty_file(self, object_filter: ObjectFilter, tmp_path: Path):
            """Test that filter info can be obtained from an empty file.

            Assert that this filter info is empty.
            """
            path = Path(tmp_path, get_name())
            path.touch()

            filter_info = object_filter._get_filter_info(path=path)
            assert filter_info.ignore_objects == set()
            assert filter_info.r_ignore_objects == set()
            assert filter_info.ignore_errors == {}
            assert filter_info.r_ignore_errors == {}

        def test_get_filter_info(self, object_filter: ObjectFilter, tmp_path: Path):
            """Test get filter info with all types of ignores.

            Test ignore directives parsing with extra whitespace and other characters.
            """
            path = Path(tmp_path, get_name())
            with open(path, "w") as file:
                file.write(
                    textwrap.dedent(
                        f"""
                        # 2 # numpydoclint:ignore
                        # 3 # numpydoclint: ignore  # noqa
                        # 4 # numpydoclint: ignore-all
                        # 5 # numpydoclint: ignore=A00,A01
                        # 6 # numpydoclint: ignore-all  B00,B01
                        # 7 # numpydoclint: ignore      C00
                        # 8 # numpydoclint:     ignore
                        """
                    )
                )

            filter_info = object_filter._get_filter_info(path=path)
            assert filter_info.ignore_objects == {2, 3, 8}
            assert filter_info.r_ignore_objects == {4}
            assert filter_info.ignore_errors == {5: {"A00", "A01"}, 7: {"C00"}}
            assert filter_info.r_ignore_errors == {6: {"B00", "B01"}}

    class TestFilterModuleInfo:
        def test_filter_module_info_ignore_objects(self, object_filter: ObjectFilter):
            """Test filter info with plain object ignoring.

            Test edge case with ignore comment coming after the first module statement.
            """
            module_info = ModuleInfo(name=get_name(), path=Path(get_name()), lineno=1, first_statement_lineno=10)

            object_filter._filter_module_info(module_info=module_info, filter_info=FilterInfo(ignore_objects={10}))
            assert not module_info.ignore_self

            object_filter._filter_module_info(module_info=module_info, filter_info=FilterInfo(ignore_objects={9}))
            assert module_info.ignore_self

        def test_filter_module_info_ignore_objects_recursive(self, object_filter: ObjectFilter):
            """Test filter info with recursive object ignoring.

            Test edge case with ignore comment coming after the first module statement.
            """
            module_info = ModuleInfo(name=get_name(), path=Path(get_name()), lineno=1, first_statement_lineno=10)

            object_filter._filter_module_info(module_info=module_info, filter_info=FilterInfo(r_ignore_objects={10}))
            assert not module_info.ignore_self

            object_filter._filter_module_info(module_info=module_info, filter_info=FilterInfo(r_ignore_objects={9}))
            assert module_info.ignore_self

        def test_filter_module_info_ignore_errors(self, object_filter: ObjectFilter):
            """Test filter info with plain error ignoring.

            Test edge case with ignore comment coming after the first module statement.
            """
            module_info = ModuleInfo(name=get_name(), path=Path(get_name()), lineno=1, first_statement_lineno=10)
            error_codes = {get_name() for _ in range(5)}

            object_filter._filter_module_info(
                module_info=module_info, filter_info=FilterInfo(ignore_errors=defaultdict(set, {10: error_codes}))
            )
            assert module_info.ignore_errors == set()

            object_filter._filter_module_info(
                module_info=module_info, filter_info=FilterInfo(ignore_errors=defaultdict(set, {9: error_codes}))
            )
            assert module_info.ignore_errors == error_codes

        def test_filter_module_info_ignore_errors_recursive(self, object_filter: ObjectFilter):
            """Test filter info with recursive error ignoring.

            Test edge case with ignore comment coming after the first module statement.
            """
            module_info = ModuleInfo(name=get_name(), path=Path(get_name()), lineno=1, first_statement_lineno=10)
            function_info = FunctionInfo(name=get_name(), path=Path(get_name()), lineno=10)
            class_info = ClassInfo(name=get_name(), path=Path(get_name()), lineno=11)
            method_info = FunctionInfo(name=get_name(), path=Path(get_name()), lineno=12)
            class_info.function_infos = [method_info]
            module_info.class_infos = [class_info]
            module_info.function_infos = [function_info]

            error_codes = {get_name() for _ in range(5)}

            object_filter._filter_module_info(
                module_info=module_info, filter_info=FilterInfo(r_ignore_errors=defaultdict(set, {10: error_codes}))
            )
            assert module_info.ignore_errors == set()
            assert class_info.ignore_errors == set()
            assert function_info.ignore_errors == set()
            assert method_info.ignore_errors == set()

            object_filter._filter_module_info(
                module_info=module_info, filter_info=FilterInfo(r_ignore_errors=defaultdict(set, {9: error_codes}))
            )
            assert module_info.ignore_errors == error_codes
            assert class_info.ignore_errors == error_codes
            assert function_info.ignore_errors == error_codes
            assert method_info.ignore_errors == error_codes

    class TestFilterFunctionInfos:
        def test_filter_function_infos_module(self, object_filter: ObjectFilter):
            """Test filter function infos in a module."""
            module_info = ModuleInfo(name=get_name(), path=Path(get_name()), lineno=1)
            function_info_1 = FunctionInfo(name=get_name(), path=Path(get_name()), lineno=2)
            function_info_2 = FunctionInfo(name=get_name(), path=Path(get_name()), lineno=3)
            function_info_3 = FunctionInfo(name=get_name(), path=Path(get_name()), lineno=4)
            module_info.function_infos = [function_info_1, function_info_2, function_info_3]

            filter_info = FilterInfo(ignore_objects={3}, r_ignore_objects={4})
            object_filter._filter_function_infos(parent_info=module_info, filter_info=filter_info)
            assert module_info.function_infos == [function_info_1]

        def test_filter_function_infos_class(self, object_filter: ObjectFilter):
            """Test filter function infos in a class.

            Additionally, test that filtering function infos in a class ignores constructor by default.
            """
            class_info = ClassInfo(name=get_name(), path=Path(get_name()), lineno=1)
            constructor_info = FunctionInfo(name=get_name() + ".__init__", path=Path(get_name()), lineno=2)
            function_info_1 = FunctionInfo(name=get_name(), path=Path(get_name()), lineno=2)
            function_info_2 = FunctionInfo(name=get_name(), path=Path(get_name()), lineno=3)
            function_info_3 = FunctionInfo(name=get_name(), path=Path(get_name()), lineno=4)
            class_info.function_infos = [constructor_info, function_info_1, function_info_2, function_info_3]

            filter_info = FilterInfo(ignore_objects={3}, r_ignore_objects={4})
            object_filter._filter_function_infos(parent_info=class_info, filter_info=filter_info)
            assert class_info.function_infos == [function_info_1]

        def test_filter_function_infos_no_ignore_constructor(self):
            """Test filter function infos in a class with ignore constructor set to False."""
            class_info = ClassInfo(name=get_name(), path=Path(get_name()), lineno=1)
            constructor_info = FunctionInfo(name=get_name() + ".__init__", path=Path(get_name()), lineno=2)
            class_info.function_infos = [constructor_info]

            filter_info = FilterInfo(ignore_objects={3}, r_ignore_objects={4})
            object_filter = ObjectFilter(ignore_constructor=False)
            object_filter._filter_function_infos(parent_info=class_info, filter_info=filter_info)
            assert class_info.function_infos == [constructor_info]

    class TestFilterClassInfos:
        def test_filter_class_infos_ignore_objects(self, object_filter: ObjectFilter):
            """Test filter class infos in a module.

            Test both plain and recursive ignore.
            """
            module_info = ModuleInfo(name=get_name(), path=Path(get_name()), lineno=1)
            class_info_1 = ClassInfo(name=get_name(), path=Path(get_name()), lineno=2)
            class_info_2 = ClassInfo(name=get_name(), path=Path(get_name()), lineno=3)
            class_info_3 = ClassInfo(name=get_name(), path=Path(get_name()), lineno=4)
            module_info.class_infos = [class_info_1, class_info_2, class_info_3]

            filter_info = FilterInfo(ignore_objects={3}, r_ignore_objects={4})
            object_filter._filter_class_infos(module_info=module_info, filter_info=filter_info)

            assert module_info.class_infos == [class_info_1, class_info_2]
            assert not class_info_1.ignore_self
            assert class_info_2.ignore_self

            assert class_info_1.ignore_errors == set()
            assert class_info_2.ignore_errors == set()

        def test_filter_class_infos_ignore_errors(self, object_filter: ObjectFilter):
            """Test propagate ignore errors to all class infos in a module.

            Test both plain and recursive ignore.
            """
            module_info = ModuleInfo(name=get_name(), path=Path(get_name()), lineno=1)
            class_info_1 = ClassInfo(name=get_name(), path=Path(get_name()), lineno=2)
            class_info_2 = ClassInfo(name=get_name(), path=Path(get_name()), lineno=3)
            module_info.class_infos = [class_info_1, class_info_2]

            error_codes_1 = {get_name() for _ in range(5)}
            error_codes_2 = {get_name() for _ in range(5)}
            filter_info = FilterInfo(
                ignore_errors=defaultdict(set, {2: error_codes_1}), r_ignore_errors=defaultdict(set, {3: error_codes_2})
            )
            object_filter._filter_class_infos(module_info=module_info, filter_info=filter_info)

            assert module_info.class_infos == [class_info_1, class_info_2]
            assert all(not x.ignore_self for x in module_info.class_infos)

            assert class_info_1.ignore_errors == error_codes_1
            assert class_info_2.ignore_errors == error_codes_2

    class TestIgnored:
        def test_empty_filter_info(self, object_filter: ObjectFilter, empty_filter_info: FilterInfo):
            function_info = FunctionInfo(name=get_name(), path=Path(get_name()), lineno=get_number())
            assert not object_filter._ignored(object_info=function_info, filter_info=empty_filter_info)

        def test_function_without_ignore_hidden(self, object_filter: ObjectFilter):
            """Test that the function infos are correctly ignored when the `ignore_hidden` flag is False."""
            lineno = get_number()
            function_info = FunctionInfo(name=get_name(), path=Path(get_name()), lineno=lineno)

            # function is not in the filter info
            filter_info = FilterInfo(ignore_objects={-1}, r_ignore_objects={-2})
            assert not object_filter._ignored(object_info=function_info, filter_info=filter_info)

            # function is in the ignored objects
            filter_info = FilterInfo(ignore_objects={lineno}, r_ignore_objects={-2})
            assert object_filter._ignored(object_info=function_info, filter_info=filter_info)

            # function is in the recursively ignored objects
            filter_info = FilterInfo(ignore_objects={-1}, r_ignore_objects={lineno})
            assert object_filter._ignored(object_info=function_info, filter_info=filter_info)

        def test_class_without_ignore_hidden(self, object_filter: ObjectFilter):
            """Test that the class infos are correctly ignored when the `ignore_hidden` flag is False."""
            lineno = get_number()
            class_info = ClassInfo(name=get_name(), path=Path(get_name()), lineno=lineno)

            # class info is not in the filter info
            filter_info = FilterInfo(ignore_objects={-1}, r_ignore_objects={-2})
            assert not object_filter._ignored(object_info=class_info, filter_info=filter_info)

            # class info is in the ignored objects
            filter_info = FilterInfo(ignore_objects={lineno}, r_ignore_objects={-2})
            assert not object_filter._ignored(object_info=class_info, filter_info=filter_info)

            # class info is in the recursively ignored objects
            filter_info = FilterInfo(ignore_objects={-1}, r_ignore_objects={lineno})
            assert object_filter._ignored(object_info=class_info, filter_info=filter_info)

        def test_function_with_ignore_hidden(self, empty_filter_info: FilterInfo):
            """Test that the function infos are correctly ignored when the `ignore_hidden` flag is True."""
            object_filter = ObjectFilter(directive=get_name(), r_directive=get_name(), ignore_hidden=True)

            # the object does not start with an underscore
            function_info = FunctionInfo(name=get_name(), path=Path(get_name()), lineno=get_number())
            assert not object_filter._ignored(object_info=function_info, filter_info=empty_filter_info)

            # the object starts with a single underscore
            function_info = FunctionInfo(name=get_name(prefix="_"), path=Path(get_name()), lineno=get_number())
            assert object_filter._ignored(object_info=function_info, filter_info=empty_filter_info)

            # the object starts with a multiple underscores
            function_info = FunctionInfo(name=get_name(prefix="___"), path=Path(get_name()), lineno=get_number())
            assert object_filter._ignored(object_info=function_info, filter_info=empty_filter_info)

        def test_class_with_ignore_hidden(self, empty_filter_info: FilterInfo):
            """Test that the class infos are correctly ignored when the `ignore_hidden` flag is True."""
            object_filter = ObjectFilter(directive=get_name(), r_directive=get_name(), ignore_hidden=True)

            # class info does not start with an underscore
            class_info = ClassInfo(name=get_name(), path=Path(get_name()), lineno=get_number())
            assert not object_filter._ignored(object_info=class_info, filter_info=empty_filter_info)

            # class info starts with a single underscore
            class_info = ClassInfo(name=get_name(prefix="_"), path=Path(get_name()), lineno=get_number())
            assert object_filter._ignored(object_info=class_info, filter_info=empty_filter_info)

            # class info starts with a multiple underscores
            class_info = ClassInfo(name=get_name(prefix="___"), path=Path(get_name()), lineno=get_number())
            assert object_filter._ignored(object_info=class_info, filter_info=empty_filter_info)

    def test_init_invalid(self):
        """Test that the constructor raises error if the parameter combination is invalid."""
        with pytest.raises(ValueError, match="Ignoring hidden objects while preserving class constructors is not allowed."):
            ObjectFilter(directive=get_name(), r_directive=get_name(), ignore_constructor=False, ignore_hidden=True)

    def test_init_with_ignore_errors(self, tmp_path: Path):
        """Test that ignore errors were passed to the constructor are recursively ignored everywhere."""
        path = Path(tmp_path, get_name())
        path.touch()

        module_info = ModuleInfo(name=get_name(), path=Path(get_name()), lineno=1)
        function_info = FunctionInfo(name=get_name(), path=Path(get_name()), lineno=2)
        class_info = ClassInfo(name=get_name(), path=Path(get_name()), lineno=3)
        method_info = FunctionInfo(name=get_name(), path=Path(get_name()), lineno=4)
        class_info.function_infos = [method_info]
        module_info.class_infos = [class_info]
        module_info.function_infos = [function_info]

        ignore_errors = {get_name() for _ in range(5)}
        object_filter = ObjectFilter(ignore_errors=ignore_errors)
        object_filter(path=path, module_info=module_info)
        assert module_info.ignore_errors == ignore_errors
        assert function_info.ignore_errors == ignore_errors
        assert class_info.ignore_errors == ignore_errors
        assert method_info.ignore_errors == ignore_errors

    def test_call(self, object_filter: ObjectFilter, tmp_path):
        """Test call with all types of ignore directives."""
        path = Path(tmp_path, get_name())
        with open(path, "w") as file:
            file.write(
                textwrap.dedent(
                    f"""
                    # 2 # numpydoclint: ignore
                    # 3 # numpydoclint: ignore=A00,A01
                    # 4 # numpydoclint: ignore-all=B00,B01

                    # 6 # numpydoclint: ignore-all
                    """
                )
            )

        module_info = ModuleInfo(name=get_name(), path=path, lineno=1, first_statement_lineno=3)
        function_info = FunctionInfo(name=get_name(), path=path, lineno=3)
        class_info_1 = ClassInfo(name=get_name(), path=path, lineno=4)
        method_info_1 = FunctionInfo(name=get_name(), path=path, lineno=5)
        class_info_2 = ClassInfo(name=get_name(), path=path, lineno=6)
        method_info_2 = FunctionInfo(name=get_name(), path=path, lineno=7)
        module_info.function_infos = [function_info]
        class_info_1.function_infos = [method_info_1]
        class_info_2.function_infos = [method_info_2]
        module_info.class_infos = [class_info_1, class_info_2]

        module_info = object_filter(path=path, module_info=module_info)
        assert module_info.ignore_self
        assert module_info.function_infos == [function_info]
        assert module_info.class_infos == [class_info_1]
        assert function_info.ignore_errors == {"A00", "A01"}
        assert class_info_1.ignore_errors == {"B00", "B01"}
        assert all(x.ignore_errors == {"B00", "B01"} for x in class_info_1.function_infos)

    def test_call_empty_module_info(self, empty_module_info: ModuleInfo, object_filter: ObjectFilter, tmp_path: Path):
        """Test call with empty module info and ignore directives."""
        path = Path(tmp_path, get_name())
        with open(path, "w") as file:
            file.write("# numpydoclint: ignore")

        empty_module_info.first_statement_lineno = 3
        empty_module_info = object_filter(path=path, module_info=empty_module_info)
        assert empty_module_info.ignore_self

    def test_call_empty(self, empty_module_info: ModuleInfo, object_filter: ObjectFilter, tmp_path: Path):
        """Test call with empty module info and no ignore directives.

        This is most likely for an empty file.
        """
        path = Path(tmp_path, get_name())
        path.touch()
        object_filter(path=path, module_info=empty_module_info)
