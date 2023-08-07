import sys
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from numpydoclint.cli import echo_errors, echo_success, validate
from numpydoclint.constants import __version__
from tests.utils import get_name


@pytest.fixture
def report() -> Dict[str, Dict[str, Any]]:
    return {get_name(): {"link": get_name(), "type": get_name(), "errors": [(get_name(), get_name()) for _ in range(5)]} for _ in range(5)}


class TestEchoErrors:
    """Test echo errors function."""

    def test_empty_report(self, capsys: pytest.CaptureFixture):
        """Test echo errors with empty report.

        This case is impossible by design, but function must still handle it.
        """
        echo_errors(report={}, verbose=1)
        assert "Errors found in 0 out of 0 objects checked." in capsys.readouterr().err

    def test_no_errors(self, capsys: pytest.CaptureFixture):
        """Test echo errors with no errors.

        This case is impossible by design, but function must still handle it.
        """
        report = {get_name(): {"link": get_name(), "type": get_name(), "errors": []}}

        echo_errors(report=report, verbose=1)
        assert "Errors found in 0 out of 1 objects checked." in capsys.readouterr().err

    def test_verbose_0(self, report: Dict[str, Dict[str, Any]], capsys: pytest.CaptureFixture):
        """Test echo errors with verbose level 0.

        Nothing but the number of errors and objects checked must be shown.
        """
        echo_errors(report=report, verbose=0)

        output = capsys.readouterr().err
        assert f"Errors found in {len(report)} out of {len(report)} objects checked." in output
        for name in report.keys():
            assert not any(x[0] in output for x in report[name]["errors"])
            assert not any(x[1] in output for x in report[name]["errors"])

    def test_verbose_1(self, report: Dict[str, Dict[str, Any]], capsys: pytest.CaptureFixture):
        """Test echo errors with verbose level 1.

        Only the error codes should be shown.
        """
        echo_errors(report=report, verbose=1)

        output = capsys.readouterr().err
        assert f"Errors found in {len(report)} out of {len(report)} objects checked." in output
        for name in report.keys():
            assert all(x[0] in output for x in report[name]["errors"])

    def test_verbose_2(self, report: Dict[str, Dict[str, Any]], capsys: pytest.CaptureFixture):
        """Test echo errors with verbose level 2.

        Error codes and descriptions must be shown.
        """
        echo_errors(report=report, verbose=2)

        output = capsys.readouterr().err
        assert f"Errors found in {len(report)} out of {len(report)} objects checked." in output
        for name in report.keys():
            assert all(x[0] in output for x in report[name]["errors"])
            assert all(x[1] in output for x in report[name]["errors"])

    def test_verbose_greater_than_2(self, report: Dict[str, Dict[str, Any]], capsys: pytest.CaptureFixture):
        """Test echo errors with verbose level greater than 2.

        Output must be the same as at level 2.
        """
        echo_errors(report=report, verbose=100)

        output = capsys.readouterr().err
        assert f"Errors found in {len(report)} out of {len(report)} objects checked." in output
        for name in report.keys():
            assert all(x[0] in output for x in report[name]["errors"])
            assert all(x[1] in output for x in report[name]["errors"])


class TestEchoSuccess:
    """Test echo success function."""

    def test_empty_report(self, capsys: pytest.CaptureFixture):
        """Test with empty report.

        This case is impossible by design, but function must still handle it.
        """
        echo_success(report={})
        assert "Success: No errors found in 0 objects checked" in capsys.readouterr().out

    def test_call(self, report: Dict[str, Dict[str, Any]], capsys: pytest.CaptureFixture):
        """Test with regular report."""
        echo_success(report=report)
        assert f"Success: No errors found in {len(report)} objects checked" in capsys.readouterr().out


class TestValidate:
    """Test the validate command.

    More specific cases and edge cases are tested in introspects and filters tests.
    """

    @pytest.fixture
    def runner(self) -> CliRunner:
        return CliRunner()

    def test_help(self, runner: CliRunner):
        """Test command in help mode."""
        result = runner.invoke(validate, ["--help"])
        assert result.exit_code == 0
        assert result.output

    def test_version(self, runner: CliRunner):
        """Test command in version mode."""
        result = runner.invoke(validate, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.output

    def test_no_paths(self, runner: CliRunner):
        """Test that the command raises error if called with no paths."""
        result = runner.invoke(validate)
        assert result.exit_code == 2
        assert "You must provide at least one source to validate." in result.output

    def test_success(self, runner: CliRunner, tmp_path: Path):
        """Test simple success case."""
        module = Path(tmp_path, get_name(extension=".py"))
        module.touch()

        with patch.object(sys, "path", [str(tmp_path)]):
            result = runner.invoke(validate, [str(module), "--ignore-errors", "GL08", "-vv"])
            assert result.exit_code == 0

    def test_errors(self, runner: CliRunner, tmp_path: Path):
        """Test simple error case."""
        module = Path(tmp_path, get_name(extension=".py"))
        module.touch()

        with patch.object(sys, "path", [str(tmp_path)]):
            result = runner.invoke(validate, args=[str(module), "-vv"])
            assert result.exit_code == 1
