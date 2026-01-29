"""CLI testing utilities for Typer applications.

Provides helpers for testing CLI commands with mocked dependencies,
simplifying integration tests for CLI-based tools.

Note: Requires 'typer' to be installed. Install with: pip install typer
"""

from pathlib import Path
from typing import Any, Callable
from unittest.mock import MagicMock, patch

try:
    from typer.testing import CliRunner

    TYPER_AVAILABLE = True
except ImportError:
    TYPER_AVAILABLE = False
    CliRunner = None  # type: ignore


class CLITestHelper:
    """Helper for testing Typer CLI applications.

    Provides convenient methods for running CLI commands with mocked
    dependencies and temporary files. Wraps `typer.testing.CliRunner`.

    Example:
        >>> app = typer.Typer()
        >>> @app.command()
        >>> def hello(name: str):
        >>>     print(f"Hello {name}")
        >>>
        >>> helper = CLITestHelper(app)
        >>> result = helper.run(["hello", "World"])
        >>> helper.assert_success(result, "Hello World")
    """

    def __init__(self, app: Any):
        """Initialize CLI test helper.

        Args:
            app: Typer application instance

        Raises:
            ImportError: If typer is not installed
        """
        if not TYPER_AVAILABLE:
            raise ImportError(
                "typer is required for CLI testing utilities. "
                "Install with: pip install typer"
            )
        self.app = app
        self.runner = CliRunner()

    def run(self, args: list[str], **kwargs: Any) -> Any:
        """Run CLI command with arguments.

        Args:
            args: Command arguments list
            **kwargs: Additional arguments for runner.invoke()

        Returns:
            Result object with exit_code, stdout, stderr

        Example:
            >>> result = helper.run(["sync", "--dry-run"])
            >>> assert result.exit_code == 0
        """
        return self.runner.invoke(self.app, args, **kwargs)

    def run_with_temp_files(
        self, args: list[str], files: dict[str, str], **kwargs: Any
    ) -> tuple[Any, Path]:
        """Run CLI command with temporary files.

        Creates a temporary directory with specified files and runs
        the command. Caller is responsible for cleanup.

        Args:
            args: Command arguments
            files: Dict mapping filenames to content
            **kwargs: Additional arguments for runner.invoke()

        Returns:
            Tuple of (result, temp_dir_path)

        Example:
            >>> files = {"config.yaml": "api_key: test"}
            >>> result, tmpdir = helper.run_with_temp_files(
            ...     ["sync"], files
            ... )
            >>> # Use tmpdir...
            >>> import shutil
            >>> shutil.rmtree(tmpdir)  # Manual cleanup
        """
        import tempfile

        tmp_path = Path(tempfile.mkdtemp())

        # Create files
        for filename, content in files.items():
            file_path = tmp_path / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)

        # Update args to use temp dir if needed
        updated_args = [
            str(tmp_path / arg) if Path(arg).exists() or "/" in arg else arg
            for arg in args
        ]

        result = self.runner.invoke(self.app, updated_args, **kwargs)
        return result, tmp_path

    def mock_graph_load(self, mock_graph: Any) -> Any:
        """Context manager to mock Graph.from_file().

        Args:
            mock_graph: Mock Graph object to return

        Returns:
            Mock context manager

        Example:
            >>> graph = GraphFixture.simple_graph()
            >>> with helper.mock_graph_load(graph):
            ...     result = helper.run(["validate", "graph.json"])
        """
        return patch("scp_sdk.Graph.from_file", return_value=mock_graph)

    def assert_success(self, result: Any, expected_output: str | None = None) -> None:
        """Assert command succeeded.

        Args:
            result: CLI result object
            expected_output: Optional expected output substring

        Raises:
            AssertionError: If command failed or output doesn't match
        """
        assert result.exit_code == 0, f"Command failed: {result.stdout}"
        if expected_output:
            assert expected_output in result.stdout, (
                f"Expected '{expected_output}' in output"
            )

    def assert_failure(
        self, result: Any, expected_error: str | None = None, exit_code: int = 1
    ) -> None:
        """Assert command failed.

        Args:
            result: CLI result object
            expected_error: Optional expected error substring
            exit_code: Expected exit code (default: 1)

        Raises:
            AssertionError: If command succeeded or error doesn't match
        """
        assert result.exit_code == exit_code, (
            f"Expected exit code {exit_code}, got {result.exit_code}"
        )
        if expected_error:
            output = result.stdout + result.stderr
            assert expected_error in output, f"Expected '{expected_error}' in output"


class MockConfig:
    """Mock configuration for testing.

    Provides a simple mock config object that can be customized
    for testing different configuration scenarios.

    Example:
        >>> config = MockConfig(api_key="test", endpoint="https://api.test")
        >>> assert config.api_key == "test"
    """

    def __init__(self, **kwargs: Any):
        """Initialize mock config.

        Args:
            **kwargs: Config attributes
        """
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MockConfig":
        """Create mock config from dictionary.

        Args:
            data: Config data

        Returns:
            MockConfig instance
        """
        return cls(**data)


def create_mock_client(**methods: Callable) -> MagicMock:
    """Create a mock client with specified methods.

    Useful for mocking API clients in CLI tests.

    Args:
        **methods: Method name -> callable mapping

    Returns:
        MagicMock with configured methods

    Example:
        >>> client = create_mock_client(
        ...     get_user=lambda id: {"id": id, "name": "Test"},
        ...     list_users=lambda: [{"id": 1}]
        ... )
        >>> assert client.get_user(1)["name"] == "Test"
    """
    mock = MagicMock()
    for method_name, method_impl in methods.items():
        setattr(mock, method_name, MagicMock(side_effect=method_impl))
    return mock
