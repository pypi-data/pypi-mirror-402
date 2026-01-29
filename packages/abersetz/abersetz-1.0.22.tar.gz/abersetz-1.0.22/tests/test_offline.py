"""Offline smoke tests to verify basic installation without network."""
# this_file: tests/test_offline.py

import tempfile
from pathlib import Path

import pytest

from abersetz.cli import AbersetzCLI
from abersetz.pipeline import TranslatorOptions, translate_path


def test_cli_help_works_offline() -> None:
    """Verify CLI help can be accessed without network."""
    cli = AbersetzCLI()
    version = cli.version()
    assert version
    assert "." in version  # Basic version format check


def test_config_commands_work_offline() -> None:
    """Verify config commands work without network."""
    cli = AbersetzCLI()
    config_path = cli.config().path()
    assert config_path
    assert "config.toml" in config_path


def test_dry_run_works_offline() -> None:
    """Verify dry run mode works without network access."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("Hello world")

        options = TranslatorOptions(
            to_lang="es",
            engine="tr/google",
            dry_run=True,  # Dry run mode should work offline
            output_dir=Path(tmpdir) / "output",
        )

        results = translate_path(test_file, options)
        assert len(results) == 1
        assert results[0].source.name == test_file.name


def test_input_validation_works_offline() -> None:
    """Verify input validation works without network."""
    from abersetz.pipeline import PipelineError

    options = TranslatorOptions(to_lang="es", dry_run=True)

    # Non-existent path should fail immediately without network
    with pytest.raises(PipelineError, match="Path does not exist"):
        translate_path("/path/that/does/not/exist", options)


def test_empty_file_handling_works_offline() -> None:
    """Verify empty file handling works without network."""
    with tempfile.TemporaryDirectory() as tmpdir:
        empty_file = Path(tmpdir) / "empty.txt"
        empty_file.write_text("")

        options = TranslatorOptions(
            to_lang="fr",
            engine="tr/google",
            dry_run=True,
            output_dir=Path(tmpdir) / "output",
        )

        results = translate_path(empty_file, options)
        assert len(results) == 1
        assert results[0].chunks == 0  # Empty file has 0 chunks


def test_import_works_offline() -> None:
    """Verify basic imports work without network."""
    # These imports should work without network access
    import abersetz
    from abersetz import TranslatorOptions, translate_path
    from abersetz.cli import AbersetzCLI
    from abersetz.config import AbersetzConfig
    from abersetz.pipeline import PipelineError, TranslationResult

    # Basic assertions to verify imports worked
    assert isinstance(abersetz.__version__, str) and abersetz.__version__
    assert isinstance(TranslatorOptions, type)
    assert callable(translate_path)
    assert isinstance(AbersetzCLI, type)
    assert isinstance(AbersetzConfig, type)
    assert isinstance(PipelineError, type)
    assert isinstance(TranslationResult, type)


@pytest.mark.parametrize(
    "file_content",
    [
        "",  # Empty file
        " ",  # Whitespace only
        "\n\n\n",  # Newlines only
    ],
)
def test_edge_case_files_offline(file_content: str) -> None:
    """Verify edge case files are handled offline."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "edge_case.txt"
        test_file.write_text(file_content)

        options = TranslatorOptions(
            to_lang="de",
            dry_run=True,
            output_dir=Path(tmpdir) / "output",
        )

        results = translate_path(test_file, options)
        assert len(results) == 1
        # Empty or whitespace files should be handled gracefully
        assert results[0].chunks == 0
