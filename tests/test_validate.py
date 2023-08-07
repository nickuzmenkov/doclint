"""Test validation."""
import sys
from pathlib import Path
from unittest import mock

from numpydoclint.validate import validate
from tests.utils import get_name


class TestValidate:
    """Test validate function.

    More specific cases and edge cases are tested in introspects and filters tests.

    Notes
    -----
    Tests with ignore paths and filename pattern are not on the list because unlike ignore errors, this filtering is done fully
    inside the introspector.
    """

    def test_empty_list(self):
        """Test call with empty paths.

        Validation must still succeed.
        """
        assert validate(paths=[]) == {}

    def test_single_path(self, tmp_path: Path):
        """Test call with a single `Path` argument."""
        module = Path(tmp_path, get_name(extension=".py"))
        module.touch()

        with mock.patch.object(sys, "path", [str(tmp_path)]):
            report = validate(paths=module)

        assert module.stem in report

    def test_single_string(self, tmp_path: Path):
        """Test call with a single string argument."""
        module = Path(tmp_path, get_name(extension=".py"))
        module.touch()

        with mock.patch.object(sys, "path", [str(tmp_path)]):
            report = validate(paths=str(module))

        assert module.stem in report

    def test_call(self, tmp_path: Path):
        """Test regular call.

        More specific cases and edge cases are tested in introspects and filters tests.
        """
        module = Path(tmp_path, get_name(extension=".py"))
        module.touch()

        with mock.patch.object(sys, "path", [str(tmp_path)]):
            report = validate(paths=[module])

        assert module.stem in report
        assert "link" in report[module.stem]
        assert report[module.stem]["errors"]

    def test_ignore_errors(self, tmp_path: Path):
        """Test that ignored errors are removed from the list."""
        module = Path(tmp_path, get_name(extension=".py"))
        module.touch()

        with mock.patch.object(sys, "path", [str(tmp_path)]):
            report = validate(paths=[module])
        assert "GL08" in [x[0] for x in report[module.stem]["errors"]]

        with mock.patch.object(sys, "path", [str(tmp_path)]):
            report = validate(paths=[module], ignore_errors={"GL08"})
        assert "GL08" not in [x[0] for x in report[module.stem]["errors"]]
