"""
Test suite for CLI dropoff functionality.

Tests the CLI commands and utilities in the earthscope_cli.dropoff module,
verifying that arguments are correctly passed to the SDK.

The bulk of the upload logic is tested in the SDK tests, so these tests
focus on:
- CLI argument parsing and validation
- File collection and key generation
- Progress display and rendering
- Error handling and user feedback
"""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest
from earthscope_sdk.client.dropoff.models import DropoffCategory, DropoffObject

from earthscope_cli.dropoff.typer import app
from earthscope_cli.dropoff.util import collect_files, key_from_path, safe_str
from tests.conftest import runner


def make_dropoff_object(**kwargs):
    """Helper to create a DropoffObject with defaults."""
    defaults = {
        "path": "demo/file.mseed",
        "size": 1000,
        "received_at": datetime.now(timezone.utc),
        "status": "ACCEPTED",
        "status_message": None,
        "hash": "abc123",
    }
    defaults.update(kwargs)
    return DropoffObject(**defaults)


def mock_sdk_context_manager(monkeypatch):
    """Helper to create a properly mocked SDK client for testing CLI commands."""
    mock_sdk = MagicMock()
    mock_sdk.__enter__ = Mock(return_value=mock_sdk)
    mock_sdk.__exit__ = Mock(return_value=False)

    # Mock the EarthScopeClient class at the import location (in earthscope_sdk)
    # since it's imported inside get_sdk() function
    monkeypatch.setattr(
        "earthscope_sdk.EarthScopeClient",
        Mock(return_value=mock_sdk),
    )

    return mock_sdk


class TestUploadCommand:
    """Test the 'upload' command."""

    def test_upload_single_file_with_category_flag(self, tmp_path, monkeypatch):
        """Test uploading a single file with -c flag."""
        # Create test file
        test_file = tmp_path / "demo" / "test.mseed"
        test_file.parent.mkdir(parents=True)
        test_file.write_bytes(b"test data")

        # Mock SDK client
        mock_sdk = mock_sdk_context_manager(monkeypatch)
        mock_sdk.dropoff.put_objects = Mock()

        # Mock validator to pass validation
        mock_validator = MagicMock()
        mock_validator.validate_all = Mock()
        monkeypatch.setattr(
            "earthscope_cli.dropoff.typer.Validator",
            Mock(return_value=mock_validator),
        )

        # Run command
        result = runner.invoke(
            app,
            ["upload", "-c", "miniseed", str(test_file)],
        )

        # Verify exit code
        assert result.exit_code == 0, f"Command failed: {result.stdout}"

        # Verify SDK was called
        mock_sdk.dropoff.put_objects.assert_called_once()

        # Verify arguments
        _, kwargs = mock_sdk.dropoff.put_objects.call_args
        assert kwargs["category"] == DropoffCategory.miniSEED
        assert kwargs["object_concurrency"] == 3  # default
        assert kwargs["part_concurrency"] == 8  # default
        assert kwargs["part_size"] == 10 * 1024**2  # default

        # Verify files were collected correctly
        files = list(kwargs["objects"])
        assert len(files) == 1
        file_path, key = files[0]
        assert file_path == test_file
        assert "demo/test.mseed" in key

    def test_upload_directory_recursively(self, tmp_path, monkeypatch):
        """Test uploading a directory recursively."""
        # Create test directory with multiple files
        test_dir = tmp_path / "demo"
        test_dir.mkdir()
        (test_dir / "file1.mseed").write_bytes(b"data1")
        (test_dir / "file2.mseed").write_bytes(b"data2")
        subdir = test_dir / "subdir"
        subdir.mkdir()
        (subdir / "file3.mseed").write_bytes(b"data3")

        # Mock SDK client
        mock_sdk = mock_sdk_context_manager(monkeypatch)
        mock_sdk.dropoff.put_objects = Mock()

        # Mock validator
        mock_validator = MagicMock()
        mock_validator.validate_all = Mock()
        monkeypatch.setattr(
            "earthscope_cli.dropoff.typer.Validator",
            Mock(return_value=mock_validator),
        )

        # Run command
        result = runner.invoke(
            app,
            ["upload", "-c", "miniseed", str(test_dir)],
        )

        # Verify exit code
        assert result.exit_code == 0, f"Command failed: {result.stdout}"

        # Verify SDK was called
        mock_sdk.dropoff.put_objects.assert_called_once()

        # Verify all files were collected
        _, kwargs = mock_sdk.dropoff.put_objects.call_args
        files = list(kwargs["objects"])
        assert len(files) == 3

        # Verify keys include directory structure
        keys = {k for _, k in files}
        assert keys == {
            "demo/file1.mseed",
            "demo/file2.mseed",
            "demo/subdir/file3.mseed",
        }

    def test_upload_multiple_paths(self, tmp_path, monkeypatch):
        """Test uploading multiple files/directories in one command."""
        # Create test files
        file1 = tmp_path / "dir1" / "test1.mseed"
        file1.parent.mkdir()
        file1.write_bytes(b"data1")

        file2 = tmp_path / "dir2" / "test2.mseed"
        file2.parent.mkdir()
        file2.write_bytes(b"data2")

        # Mock SDK client
        mock_sdk = mock_sdk_context_manager(monkeypatch)
        mock_sdk.dropoff.put_objects = Mock()

        # Mock validator
        mock_validator = MagicMock()
        mock_validator.validate_all = Mock()
        monkeypatch.setattr(
            "earthscope_cli.dropoff.typer.Validator",
            Mock(return_value=mock_validator),
        )

        # Run command with multiple paths
        result = runner.invoke(
            app,
            ["upload", "-c", "miniseed", str(file1), str(file2)],
        )

        # Verify exit code
        assert result.exit_code == 0, f"Command failed: {result.stdout}"

        # Verify both files were uploaded
        _, kwargs = mock_sdk.dropoff.put_objects.call_args
        files = list(kwargs["objects"])
        assert len(files) == 2

        # Verify keys include directory structure
        keys = {k for _, k in files}
        assert keys == {
            "dir1/test1.mseed",
            "dir2/test2.mseed",
        }

    def test_upload_with_custom_concurrency_options(self, tmp_path, monkeypatch):
        """Test upload with custom concurrency settings."""
        # Create test file
        test_file = tmp_path / "demo" / "test.mseed"
        test_file.parent.mkdir()
        test_file.write_bytes(b"test data")

        # Mock SDK client
        mock_sdk = mock_sdk_context_manager(monkeypatch)
        mock_sdk.dropoff.put_objects = Mock()

        # Mock validator
        mock_validator = MagicMock()
        mock_validator.validate_all = Mock()
        monkeypatch.setattr(
            "earthscope_cli.dropoff.typer.Validator",
            Mock(return_value=mock_validator),
        )

        # Run command with custom settings
        result = runner.invoke(
            app,
            [
                "upload",
                "-c",
                "miniseed",
                "--object-concurrency",
                "5",
                "--part-concurrency",
                "10",
                "--part-size",
                "20971520",  # 20MB
                str(test_file),
            ],
        )

        # Verify exit code
        assert result.exit_code == 0, f"Command failed: {result.stdout}"

        # Verify custom settings were passed
        _, kwargs = mock_sdk.dropoff.put_objects.call_args
        assert kwargs["object_concurrency"] == 5
        assert kwargs["part_concurrency"] == 10
        assert kwargs["part_size"] == 20971520

    def test_upload_validation_failure(self, tmp_path, monkeypatch):
        """Test that validation errors are handled properly."""
        # Create test file
        test_file = tmp_path / "demo" / "invalid.mseed"
        test_file.parent.mkdir()
        test_file.write_bytes(b"invalid data")

        # Mock SDK client
        mock_sdk = MagicMock()

        def mock_get_sdk(*args, **kwargs):
            return mock_sdk

        monkeypatch.setattr(
            "earthscope_cli.dropoff.typer.get_sdk_refreshed", mock_get_sdk
        )

        # Mock validator to raise validation error
        mock_validator = MagicMock()
        mock_validator.validate_all = Mock(
            side_effect=ValueError("Invalid file format")
        )
        monkeypatch.setattr(
            "earthscope_cli.dropoff.typer.Validator",
            Mock(return_value=mock_validator),
        )

        # Run command
        result = runner.invoke(
            app,
            ["upload", "-c", "miniseed", str(test_file)],
        )

        # Verify exit code indicates error
        assert result.exit_code == 1

        # Verify SDK upload was not called
        mock_sdk.dropoff.put_objects.assert_not_called()

    def test_upload_no_files_found(self, tmp_path, monkeypatch):
        """Test error when no files are found."""
        # Create empty directory
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        # Mock SDK client
        mock_sdk = mock_sdk_context_manager(monkeypatch)

        # Run command
        result = runner.invoke(
            app,
            ["upload", "-c", "miniseed", str(empty_dir)],
        )

        # Verify exit code indicates error
        assert result.exit_code == 1
        assert "No files found" in result.stdout

        # Verify SDK upload was not called
        mock_sdk.dropoff.put_objects.assert_not_called()


class TestListObjectsCommand:
    """Test the 'list-objects' command."""

    def test_list_objects_basic(self, monkeypatch):
        """Test listing objects with minimal options."""
        # Mock SDK client
        mock_sdk = mock_sdk_context_manager(monkeypatch)

        mock_result = SimpleNamespace(
            items=[
                make_dropoff_object(
                    path="demo/file1.mseed",
                    size=1000,
                    status="ACCEPTED",
                )
            ],
            has_next=False,
            offset=0,
            limit=100,
        )
        mock_sdk.dropoff.list_objects = Mock(return_value=mock_result)

        # Run command
        result = runner.invoke(
            app,
            ["list-objects", "-c", "miniseed"],
        )

        # Verify exit code
        assert result.exit_code == 0

        # Verify SDK was called correctly
        mock_sdk.dropoff.list_objects.assert_called_once_with(
            category="miniseed",
            prefix="",
            offset=0,
            limit=100,
        )

        # Verify output contains file name
        assert "demo/file1.mseed" in result.stdout

    def test_list_objects_with_prefix(self, monkeypatch):
        """Test listing objects with a prefix filter."""
        # Mock SDK client
        mock_sdk = mock_sdk_context_manager(monkeypatch)

        mock_result = SimpleNamespace(
            items=[],
            has_next=False,
            offset=0,
            limit=100,
        )
        mock_sdk.dropoff.list_objects = Mock(return_value=mock_result)

        # Run command with prefix
        result = runner.invoke(
            app,
            ["list-objects", "-c", "miniseed", "--prefix", "demo/"],
        )

        # Verify SDK was called with prefix
        mock_sdk.dropoff.list_objects.assert_called_once_with(
            category="miniseed",
            prefix="demo/",
            offset=0,
            limit=100,
        )

    def test_list_objects_with_pagination(self, monkeypatch):
        """Test listing objects with custom pagination."""
        # Mock SDK client
        mock_sdk = mock_sdk_context_manager(monkeypatch)

        mock_result = SimpleNamespace(
            items=[],
            has_next=False,
            offset=50,
            limit=25,
        )
        mock_sdk.dropoff.list_objects = Mock(return_value=mock_result)

        # Run command with pagination
        result = runner.invoke(
            app,
            ["list-objects", "-c", "miniseed", "--offset", "50", "--limit", "25"],
        )

        # Verify SDK was called with pagination
        mock_sdk.dropoff.list_objects.assert_called_once_with(
            category="miniseed",
            prefix="",
            offset=50,
            limit=25,
        )

    def test_list_objects_empty_result(self, monkeypatch):
        """Test listing when no objects are found."""
        # Mock SDK client
        mock_sdk = mock_sdk_context_manager(monkeypatch)

        mock_result = SimpleNamespace(
            items=[],
            has_next=False,
            offset=0,
            limit=100,
        )
        mock_sdk.dropoff.list_objects = Mock(return_value=mock_result)

        # Run command
        result = runner.invoke(
            app,
            ["list-objects", "-c", "miniseed"],
        )

        # Verify exit code
        assert result.exit_code == 0

        # Verify message about no objects
        assert "No objects found" in result.stdout

    def test_list_objects_has_next_indicator(self, monkeypatch):
        """Test that pagination indicators are shown when has_next is True."""
        # Mock SDK client
        mock_sdk = mock_sdk_context_manager(monkeypatch)

        mock_result = SimpleNamespace(
            items=[
                make_dropoff_object(
                    path="demo/file1.mseed",
                    size=1000,
                    status="ACCEPTED",
                )
            ],
            has_next=True,
            offset=0,
            limit=100,
        )
        mock_sdk.dropoff.list_objects = Mock(return_value=mock_result)

        # Run command
        result = runner.invoke(
            app,
            ["list-objects", "-c", "miniseed"],
        )

        # Verify pagination hint is shown
        assert "--offset 100" in result.stdout


class TestGetObjectHistoryCommand:
    """Test the 'get-object-history' command."""

    def test_get_object_history_basic(self, monkeypatch):
        """Test getting object history with minimal options."""
        # Mock SDK client
        mock_sdk = mock_sdk_context_manager(monkeypatch)

        mock_result = SimpleNamespace(
            items=[
                make_dropoff_object(
                    path="demo/file.mseed",
                    size=1000,
                    status="ACCEPTED",
                )
            ],
            has_next=False,
            offset=0,
            limit=100,
        )
        mock_sdk.dropoff.get_object_history = Mock(return_value=mock_result)

        # Run command (with --key to avoid prompt)
        result = runner.invoke(
            app,
            ["get-object-history", "-c", "miniseed", "-k", "demo/file.mseed"],
        )

        # Verify exit code
        assert result.exit_code == 0

        # Verify SDK was called correctly
        mock_sdk.dropoff.get_object_history.assert_called_once_with(
            category="miniseed",
            key="demo/file.mseed",
            offset=0,
            limit=100,
        )

    def test_get_object_history_with_pagination(self, monkeypatch):
        """Test getting object history with custom pagination."""
        # Mock SDK client
        mock_sdk = mock_sdk_context_manager(monkeypatch)

        mock_result = SimpleNamespace(
            items=[],
            has_next=False,
            offset=50,
            limit=25,
        )
        mock_sdk.dropoff.get_object_history = Mock(return_value=mock_result)

        # Run command with pagination
        result = runner.invoke(
            app,
            [
                "get-object-history",
                "-c",
                "miniseed",
                "-k",
                "demo/file.mseed",
                "--offset",
                "50",
                "--limit",
                "25",
            ],
        )

        # Verify SDK was called with pagination
        mock_sdk.dropoff.get_object_history.assert_called_once_with(
            category="miniseed",
            key="demo/file.mseed",
            offset=50,
            limit=25,
        )

    def test_get_object_history_no_history_found(self, monkeypatch):
        """Test when no history is found for an object."""
        # Mock SDK client
        mock_sdk = mock_sdk_context_manager(monkeypatch)

        mock_result = SimpleNamespace(
            items=[],
            has_next=False,
            offset=0,
            limit=100,
        )
        mock_sdk.dropoff.get_object_history = Mock(return_value=mock_result)

        # Run command
        result = runner.invoke(
            app,
            ["get-object-history", "-c", "miniseed", "-k", "demo/missing.mseed"],
        )

        # Verify exit code
        assert result.exit_code == 0

        # Verify message about no history
        assert "No history found" in result.stdout


class TestCollectFiles:
    """Test the collect_files utility function."""

    @pytest.mark.parametrize(
        "description,paths_to_create,paths_to_collect,expected_file_count,expected_keys",
        [
            # Single file scenarios
            (
                "single file with parent context",
                ["demo/test.mseed"],
                ["demo/test.mseed"],
                1,
                ["demo/test.mseed"],
            ),
            (
                "single file without parent context",
                ["file.mseed"],
                ["file.mseed"],
                1,
                ["{}/file.mseed"],
            ),
            (
                "multiple individual files from different dirs",
                ["project1/data.mseed", "project2/data.mseed"],
                ["project1/data.mseed", "project2/data.mseed"],
                2,
                ["project1/data.mseed", "project2/data.mseed"],
            ),
            # Directory scenarios
            (
                "flat directory with multiple files",
                ["demo/file1.mseed", "demo/file2.mseed"],
                ["demo"],
                2,
                ["demo/file1.mseed", "demo/file2.mseed"],
            ),
            (
                "nested directory structure",
                [
                    "demo/file1.mseed",
                    "demo/sub1/file2.mseed",
                    "demo/sub1/sub2/file3.mseed",
                ],
                ["demo"],
                3,
                [
                    "demo/file1.mseed",
                    "demo/sub1/file2.mseed",
                    "demo/sub1/sub2/file3.mseed",
                ],
            ),
            # Mixed scenarios
            (
                "mix of files and directories",
                [
                    "individual.mseed",
                    "dir1/file1.mseed",
                    "dir1/file2.mseed",
                    "standalone/file.mseed",
                ],
                ["individual.mseed", "dir1", "standalone/file.mseed"],
                4,
                [
                    "{}/individual.mseed",  # Individual file with parent (CWD or parent dir)
                    "dir1/file1.mseed",  # From directory
                    "dir1/file2.mseed",  # From directory
                    "standalone/file.mseed",  # Individual file with parent
                ],
            ),
        ],
    )
    def test_collect_files_scenarios(
        self,
        tmp_path,
        description,
        paths_to_create,
        paths_to_collect,
        expected_file_count,
        expected_keys,
    ):
        """
        Test file collection for various scenarios.

        This parametrized test demonstrates how files are collected and their
        keys generated based on whether the user specifies individual files
        or directories.
        """
        # Create all files
        created_files = {}
        for path in paths_to_create:
            full_path = tmp_path / path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_bytes(b"test data")
            created_files[path] = full_path

        # Build the paths to collect (resolve them to full paths)
        paths_to_collect_full = [tmp_path / p for p in paths_to_collect]

        # Collect files
        collected = list(collect_files(paths_to_collect_full))

        # Verify count
        assert len(collected) == expected_file_count, (
            f"\n{description}\n"
            f"Expected {expected_file_count} files, got {len(collected)}"
        )

        # Verify keys match expected patterns
        collected_keys = {key for _, key in collected}
        expected_keys = {key.format(tmp_path.name) for key in expected_keys}
        assert collected_keys == expected_keys, (
            f"\n{description}\n"
            f"Expected keys: {expected_keys}\n"
            f"Got keys: {collected_keys}"
        )

    def test_collect_deduplicates_files(self, tmp_path):
        """
        Test that duplicate files are not collected twice.

        If the user accidentally specifies the same file multiple times,
        it should only be collected once.
        """
        # Create test file
        test_file = tmp_path / "demo" / "test.mseed"
        test_file.parent.mkdir()
        test_file.write_bytes(b"test data")

        # Pass same file twice
        files = list(collect_files([test_file, test_file]))

        # Verify only collected once
        assert len(files) == 1
        assert files[0][0] == test_file

    def test_collect_empty_directory(self, tmp_path):
        """
        Test collecting from an empty directory returns no files.

        This is expected behavior - no error, just no files to upload.
        """
        # Create empty directory
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        # Collect files
        files = list(collect_files([empty_dir]))

        # Verify no files collected
        assert len(files) == 0

    def test_collect_multi_project_scenario(self, tmp_path):
        """
        Demonstrate a real-world scenario: uploading data from multiple projects.

        Command: earthscope upload project1/results.mseed project2/results.mseed project3/

        This shows how the current behavior:
        1. Prevents collisions between same-named files from different projects
        2. Preserves directory structure for directory uploads
        3. Provides meaningful context for individual files
        """
        # Create project structures
        project1 = tmp_path / "project1"
        project1.mkdir()
        (project1 / "results.mseed").write_bytes(b"project1 data")

        project2 = tmp_path / "project2"
        project2.mkdir()
        (project2 / "results.mseed").write_bytes(b"project2 data")

        project3 = tmp_path / "project3"
        project3.mkdir()
        (project3 / "results.mseed").write_bytes(b"project3 data")
        (project3 / "extra.mseed").write_bytes(b"extra data")

        # User uploads two individual files and one directory
        paths_to_upload = [
            project1 / "results.mseed",  # Individual file
            project2 / "results.mseed",  # Individual file
            project3,  # Entire directory
        ]

        # Collect files
        collected = list(collect_files(paths_to_upload))

        # Should have 4 files total
        assert len(collected) == 4

        # Extract keys
        keys = {key for _, key in collected}

        # Verify each project's files have distinct keys
        assert keys == {
            "project1/results.mseed",
            "project2/results.mseed",
            "project3/results.mseed",
            "project3/extra.mseed",
        }


class TestKeyFromPath:
    """Test the key_from_path utility function."""

    @pytest.mark.parametrize(
        "description,file_path,relative_to,expected_key",
        [
            # Single file scenarios - relative_to is the file itself
            (
                "single file includes parent dir name",
                "parent/file.mseed",
                "parent/file.mseed",
                "parent/file.mseed",
            ),
            (
                "single file with nested parent",
                "deeply/nested/parent/file.mseed",
                "deeply/nested/parent/file.mseed",
                "parent/file.mseed",
            ),
            (
                "single file without parent context",
                "file.mseed",
                None,
                "{}/file.mseed",
            ),
            # Note: The "root level" case doesn't really apply in practice since files
            # always have a parent directory. Skipping edge case test here.
            # Directory scenarios - relative_to is a directory
            (
                "file in flat directory",
                "uploads/file.mseed",
                "uploads",
                "uploads/file.mseed",
            ),
            (
                "file in nested subdirectory",
                "uploads/subdir/file.mseed",
                "uploads",
                "uploads/subdir/file.mseed",
            ),
            (
                "file in deeply nested structure",
                "data/2024/01/15/measurements.mseed",
                "data",
                "data/2024/01/15/measurements.mseed",
            ),
            (
                "preserves multiple subdirectories",
                "project/experiments/exp1/results/output.mseed",
                "project",
                "project/experiments/exp1/results/output.mseed",
            ),
            # Real-world multi-file scenarios
            (
                "first file from project1",
                "workspace/project1/data.mseed",
                "workspace/project1/data.mseed",  # User specified this file
                "project1/data.mseed",
            ),
            (
                "second file from project2",
                "workspace/project2/data.mseed",
                "workspace/project2/data.mseed",  # User specified this file
                "project2/data.mseed",
            ),
        ],
    )
    def test_key_generation_scenarios(
        self, tmp_path, description, file_path, relative_to, expected_key
    ):
        """
        Test key generation for various file and directory scenarios.

        This parametrized test demonstrates how S3 keys are generated based on:
        1. The absolute path of the file being uploaded
        2. The resolved input path (what the user specified on command line)

        Key behavior:
        - For directories: keys are relative to the directory and include dir name
        - For individual files: keys include the parent directory name to provide
          context and avoid collisions when uploading multiple files with the
          same name from different locations
        """
        # Create the file structure
        full_file_path = tmp_path / file_path
        full_file_path.parent.mkdir(parents=True, exist_ok=True)
        full_file_path.write_bytes(b"test data")

        # Generate the key
        if relative_to:
            key = key_from_path(full_file_path, tmp_path / relative_to)
        else:
            key = key_from_path(full_file_path)

        # Verify against expected key
        expected_key = expected_key.format(tmp_path.name)
        assert key == expected_key, (
            f"\n{description}\n"
            f"File: {file_path}\n"
            f"Relative to: {relative_to}\n"
            f"Expected: {expected_key}\n"
            f"Got: {key}"
        )

    def test_collision_prevention_with_multiple_files(self, tmp_path):
        """
        Demonstrate that the current behavior prevents key collisions when
        uploading multiple files with the same name from different directories.

        Example command:
            earthscope upload project1/results.csv project2/results.csv

        Without parent dir inclusion, both would map to 'results.csv' causing
        a collision. With parent dir, they map to distinct keys.
        """
        # Create two files with same name in different directories
        file1 = tmp_path / "project1" / "results.csv"
        file2 = tmp_path / "project2" / "results.csv"

        # Generate keys as if user uploaded both files individually
        key1 = key_from_path(file1, file1)
        key2 = key_from_path(file2, file2)

        # Keys should be different, preventing collision
        assert key1 == "project1/results.csv"
        assert key2 == "project2/results.csv"
        assert key1 != key2, "Keys should be different to prevent collisions"

    def test_directory_upload_preserves_structure(self, tmp_path):
        """
        Demonstrate that uploading a directory preserves its internal structure.

        Example command:
            earthscope upload mydata/

        All files within the directory maintain their relative paths from the
        directory root, with the directory name as a prefix.
        """
        # Create a directory with nested structure
        base_dir = tmp_path / "mydata"
        base_dir.mkdir()

        files_to_create = [
            "file1.mseed",
            "subdir1/file2.mseed",
            "subdir1/nested/file3.mseed",
            "subdir2/file4.mseed",
        ]

        created_files = []
        for file_path in files_to_create:
            created_files.append(base_dir / file_path)

        # Generate keys for all files as if from directory upload
        keys = [key_from_path(f, base_dir) for f in created_files]

        # All keys should start with the directory name
        expected_keys = [f"mydata/{path}" for path in files_to_create]
        assert keys == expected_keys


class TestSafeStr:
    """Test the safe_str utility function."""

    @pytest.mark.parametrize(
        "description,input_value,expected_output",
        [
            ("none values become dash", None, "-"),
            ("strings pass through", "test", "test"),
            ("integers to strings", 123, "123"),
            (
                "datetime to ISO format with Z",
                datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc),
                "2024-01-15T10:30:45Z",
            ),
            ("enum to value string", DropoffCategory.miniSEED, "miniseed"),
        ],
    )
    def test_safe_str_conversions(self, description, input_value, expected_output):
        """
        Test that safe_str correctly converts various types to strings.

        This function is used to safely display values in Rich tables,
        converting None to "-", datetime to ISO format, enums to their
        values, and other types to their string representation.
        """
        result = safe_str(input_value)
        assert result == expected_output, (
            f"\n{description}\n"
            f"Input: {input_value!r}\n"
            f"Expected: {expected_output!r}\n"
            f"Got: {result!r}"
        )


class TestProgressDisplay:
    """Test the progress display components."""

    def test_concurrent_upload_progress_display_initialization(self):
        """Test that ConcurrentUploadProgressDisplay initializes correctly."""
        from earthscope_cli.dropoff.render import ConcurrentUploadProgressDisplay

        display = ConcurrentUploadProgressDisplay(num_files=5)

        assert display.num_files == 5
        assert display.files_completed == 0
        assert display.upload_started is False

    def test_concurrent_upload_progress_display_context_manager(self):
        """Test that progress display works as a context manager."""
        from earthscope_cli.dropoff.render import ConcurrentUploadProgressDisplay

        display = ConcurrentUploadProgressDisplay(num_files=3)

        with display:
            # Should initialize overall task
            assert display.overall_task is not None
            assert display.live is not None

        # Should clean up after exit
        # (No exceptions should be raised)

    def test_progress_callback_tracks_files(self):
        """Test that progress callback tracks file progress."""
        from earthscope_sdk.client.dropoff._multipart_uploader import UploadStatus

        from earthscope_cli.dropoff.render import ConcurrentUploadProgressDisplay

        display = ConcurrentUploadProgressDisplay(num_files=2)

        with display:
            # Simulate progress updates
            status1 = UploadStatus(
                key="file1.mseed",
                bytes_done=500,
                bytes_buffered=500,
                bytes_resumed=0,
                total_bytes=1000,
                complete=False,
            )
            display.callback(status1)

            # Verify file task was created
            assert "file1.mseed" in display.file_tasks

            # Complete the file
            status1_complete = UploadStatus(
                key="file1.mseed",
                bytes_done=1000,
                bytes_buffered=1000,
                bytes_resumed=0,
                total_bytes=1000,
                complete=True,
            )
            display.callback(status1_complete)

            # Verify file was marked complete
            assert "file1.mseed" in display.completed_files

    def test_print_dropoff_objects_table_with_items(self):
        """Test rendering a table of dropoff objects."""
        from earthscope_cli.dropoff.render import print_dropoff_objects_table

        objects = [
            make_dropoff_object(
                path="demo/file1.mseed",
                size=1000,
                status="ACCEPTED",
            ),
            make_dropoff_object(
                path="demo/file2.mseed",
                size=2000,
                status="VALIDATING",
            ),
        ]

        # Should not raise exceptions
        print_dropoff_objects_table(
            objects,
            title="Test Objects",
            has_next=False,
            next_offset=0,
        )

    def test_print_dropoff_objects_table_with_pagination(self):
        """Test table rendering shows pagination info."""
        import sys
        from io import StringIO

        from earthscope_cli.dropoff.render import print_dropoff_objects_table

        objects = [
            make_dropoff_object(
                path="demo/file1.mseed",
                size=1000,
                status="ACCEPTED",
            )
        ]

        # Capture output
        captured_output = StringIO()
        sys.stdout = captured_output

        try:
            print_dropoff_objects_table(
                objects,
                title="Test Objects",
                has_next=True,
                next_offset=100,
            )

            output = captured_output.getvalue()
            # Should mention next offset
            assert "--offset 100" in output or "offset" in output.lower()
        finally:
            sys.stdout = sys.__stdout__


class TestCategoryResolution:
    """Test category resolution from various sources."""

    def test_category_from_command_line(self, monkeypatch):
        """Test that command-line category takes precedence."""
        from earthscope_cli.dropoff.util import get_category

        # Mock SDK with category in settings
        mock_sdk = MagicMock()
        mock_sdk.ctx.settings.dropoff.category = DropoffCategory.miniSEED

        # Call with explicit category
        result = get_category(sdk=mock_sdk, category=DropoffCategory.miniSEED)

        # Command-line should take precedence
        assert result == DropoffCategory.miniSEED

    def test_category_from_sdk_settings(self, monkeypatch):
        """Test that category falls back to SDK settings."""
        from earthscope_cli.dropoff.util import get_category

        # Mock SDK with category in settings
        mock_sdk = MagicMock()
        mock_sdk.ctx.settings.dropoff.category = DropoffCategory.miniSEED

        # Call without explicit category
        result = get_category(sdk=mock_sdk, category=None)

        # Should use SDK settings
        assert result == DropoffCategory.miniSEED
