"""Tests for CLI testing utilities."""

import pytest
from typer import Typer
from typer.testing import CliRunner

from scp_sdk import CLITestHelper, MockConfig, create_mock_client, GraphFixture


# Create a simple test CLI app
app = Typer()


@app.command()
def hello(name: str = "World"):
    """Say hello."""
    print(f"Hello, {name}!")


@app.command()
def fail():
    """Command that fails."""
    print("Error occurred")
    raise SystemExit(1)


class TestCLITestHelper:
    """Tests for CLITestHelper class."""

    def test_initialization(self):
        """Should initialize with Typer app."""
        helper = CLITestHelper(app)
        assert helper.app == app
        assert isinstance(helper.runner, CliRunner)

    def test_run_success(self):
        """Should run command successfully."""
        helper = CLITestHelper(app)
        result = helper.run(["hello"])
        assert result.exit_code == 0
        assert "Hello, World!" in result.stdout

    def test_run_with_args(self):
        """Should pass arguments to command."""
        helper = CLITestHelper(app)
        result = helper.run(["hello", "--name", "Alice"])
        assert result.exit_code == 0
        assert "Hello, Alice!" in result.stdout

    def test_run_failure(self):
        """Should handle command failure."""
        helper = CLITestHelper(app)
        result = helper.run(["fail"])
        assert result.exit_code == 1

    def test_run_with_temp_files(self):
        """Should create temporary files for command."""
        helper = CLITestHelper(app)
        files = {"test.txt": "Hello from file"}

        result, tmpdir = helper.run_with_temp_files(["hello"], files)

        # Test that result is returned
        assert result.exit_code == 0
        # Temp dir object is returned
        assert tmpdir is not None

        # Verify file was created
        test_file = tmpdir / "test.txt"
        assert test_file.exists()
        assert test_file.read_text() == "Hello from file"

    def test_mock_graph_load(self):
        """Should provide context manager for mocking Graph.from_file."""
        helper = CLITestHelper(app)
        mock_graph = GraphFixture.simple_graph()

        with helper.mock_graph_load(mock_graph) as mock:
            # Mock should be callable
            assert mock is not None

    def test_assert_success(self):
        """Should assert command success."""
        helper = CLITestHelper(app)
        result = helper.run(["hello"])

        # Should not raise
        helper.assert_success(result)
        helper.assert_success(result, "Hello")

    def test_assert_success_fails_on_error(self):
        """Should raise when command fails."""
        helper = CLITestHelper(app)
        result = helper.run(["fail"])

        with pytest.raises(AssertionError, match="Command failed"):
            helper.assert_success(result)

    def test_assert_success_fails_on_missing_output(self):
        """Should raise when expected output missing."""
        helper = CLITestHelper(app)
        result = helper.run(["hello"])

        with pytest.raises(AssertionError, match="Expected"):
            helper.assert_success(result, "Goodbye")

    def test_assert_failure(self):
        """Should assert command failure."""
        helper = CLITestHelper(app)
        result = helper.run(["fail"])

        # Should not raise
        helper.assert_failure(result)
        helper.assert_failure(result, "Error")

    def test_assert_failure_fails_on_success(self):
        """Should raise when command succeeds."""
        helper = CLITestHelper(app)
        result = helper.run(["hello"])

        with pytest.raises(AssertionError, match="Expected exit code"):
            helper.assert_failure(result)


class TestMockConfig:
    """Tests for MockConfig class."""

    def test_initialization(self):
        """Should initialize with kwargs."""
        config = MockConfig(api_key="test", endpoint="https://api.test")
        assert config.api_key == "test"
        assert config.endpoint == "https://api.test"

    def test_from_dict(self):
        """Should create from dictionary."""
        data = {"api_key": "test", "endpoint": "https://api.test"}
        config = MockConfig.from_dict(data)
        assert config.api_key == "test"
        assert config.endpoint == "https://api.test"


class TestCreateMockClient:
    """Tests for create_mock_client function."""

    def test_creates_mock_with_methods(self):
        """Should create mock client with configured methods."""
        client = create_mock_client(
            get_user=lambda user_id: {"id": user_id, "name": "Test User"},
            list_users=lambda: [{"id": 1}, {"id": 2}],
        )

        # Test methods work
        user = client.get_user(123)
        assert user["id"] == 123
        assert user["name"] == "Test User"

        users = client.list_users()
        assert len(users) == 2

    def test_mock_tracks_calls(self):
        """Should track method calls."""
        client = create_mock_client(get_user=lambda user_id: {"id": user_id})

        client.get_user(1)
        client.get_user(2)

        assert client.get_user.call_count == 2
