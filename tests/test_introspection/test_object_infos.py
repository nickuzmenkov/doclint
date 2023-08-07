"""Test object infos."""
from pathlib import Path

import pytest

from numpydoclint.introspection.object_infos import ClassInfo, FunctionInfo, ModuleInfo, ObjectInfo
from tests.utils import get_name, get_number


class TestObjectInfo:
    """Test object info."""

    def test_link(self):
        """Test that the link to the object info is created at construction."""
        lineno = get_number()
        path = Path(get_name())
        object_info = ObjectInfo(name=get_name(), path=path, lineno=lineno)
        assert object_info.link == f"{path}:{lineno}"

    def test_with_ignore_errors(self):
        """Test construction with ignore erorrs."""
        ignore_errors = {get_name() for _ in range(5)}
        object_info = ObjectInfo(name=get_name(), path=Path(get_name()), lineno=1, ignore_errors=ignore_errors)
        assert object_info.ignore_errors == ignore_errors


class TestFunctionInfo:
    """Test function info.

    This is a placeholder because function info is alias for object info.
    """


class TestClassInfo:
    """Test class info."""

    @pytest.fixture
    def class_info(self) -> ClassInfo:
        function_infos = [FunctionInfo(name=get_name(), path=Path(get_name()), lineno=get_number()) for _ in range(5)]
        return ClassInfo(name=get_name(), path=Path(get_name()), lineno=get_number(), function_infos=function_infos)

    def test_list_object_infos(self, class_info: ClassInfo):
        """Test list object infos."""
        object_infos = class_info.list_object_infos()
        assert class_info in object_infos
        assert all(x in object_infos for x in class_info.function_infos)

    def test_list_object_infos_no_methods(self, class_info: ClassInfo):
        """Test list object infos when the class has no methods"""
        class_info.function_infos = []
        object_infos = class_info.list_object_infos()
        assert object_infos == [class_info]

    def test_list_object_infos_ignore_self(self, class_info: ClassInfo):
        """Test list object infos when ignore self flag is True."""
        class_info.ignore_self = True
        object_infos = class_info.list_object_infos()
        assert class_info not in object_infos

    def test_list_object_infos_no_objects(self, class_info: ClassInfo):
        """Test list object infos when there are no child objects."""
        class_info.function_infos = []
        class_info.ignore_self = True
        assert not class_info.list_object_infos()

    def test_ignore_errors_recursive(self, class_info: ClassInfo):
        """Test propagate ignore errors to all child objects."""
        ignore_errors = {get_name() for _ in range(5)}
        class_info.ignore_errors_recursive(ignore_errors=ignore_errors)
        assert class_info.ignore_errors == ignore_errors
        assert all(x.ignore_errors == ignore_errors for x in class_info.function_infos)

    def test_ignore_errors_recursive_no_objects(self, class_info: ClassInfo):
        """Test propagate ignore errors when there are no child objects."""
        class_info.function_infos = []
        ignore_errors = {get_name() for _ in range(5)}
        class_info.ignore_errors_recursive(ignore_errors=ignore_errors)
        assert class_info.ignore_errors == ignore_errors


class TestModuleInfo:
    """Test module info."""

    @pytest.fixture
    def module_info(self) -> ModuleInfo:
        class_infos = [ClassInfo(name=get_name(), path=Path(get_name()), lineno=get_number()) for _ in range(5)]
        for class_info in class_infos:
            class_info.function_infos = [FunctionInfo(name=get_name(), path=Path(get_name()), lineno=get_number()) for _ in range(5)]
        function_infos = [FunctionInfo(name=get_name(), path=Path(get_name()), lineno=get_number()) for _ in range(5)]
        return ModuleInfo(
            name=get_name(), path=Path(get_name()), lineno=get_number(), class_infos=class_infos, function_infos=function_infos
        )

    def test_list_object_infos(self, module_info: ModuleInfo):
        """Test list object infos."""
        object_infos = module_info.list_object_infos()
        assert module_info in object_infos
        assert all(x in object_infos for x in module_info.function_infos)
        assert all(x in object_infos for x in module_info.class_infos)
        for class_info in module_info.class_infos:
            assert all(x in object_infos for x in class_info.function_infos)

    def test_list_object_infos_ignore_self(self, module_info: ModuleInfo):
        """Test list object infos when ignore self flag is True."""
        module_info.ignore_self = True
        object_infos = module_info.list_object_infos()
        assert module_info not in object_infos

    def test_list_object_infos_no_objects(self, module_info: ModuleInfo):
        """Test list object infos when there are no child objects."""
        module_info.ignore_self = True
        module_info.class_infos = []
        module_info.function_infos = []
        assert not module_info.list_object_infos()

    def test_ignore_errors_recursive(self, module_info: ModuleInfo):
        """Test propagate ignore errors to all child objects."""
        ignore_errors = {get_name() for _ in range(5)}
        module_info.ignore_errors_recursive(ignore_errors=ignore_errors)
        assert module_info.ignore_errors == ignore_errors
        assert all(x.ignore_errors == ignore_errors for x in module_info.function_infos)
        assert all(x.ignore_errors == ignore_errors for x in module_info.function_infos)
        for class_info in module_info.class_infos:
            assert all(x.ignore_errors == ignore_errors for x in class_info.function_infos)

    def test_ignore_errors_recursive_no_objects(self, module_info: ModuleInfo):
        """Test propagate ignore errors when there are no child objects."""
        module_info.class_infos = []
        module_info.function_infos = []
        ignore_errors = {get_name() for _ in range(5)}
        module_info.ignore_errors_recursive(ignore_errors=ignore_errors)
        assert module_info.ignore_errors == ignore_errors
