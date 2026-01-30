import os
import shutil
import tempfile
from pathlib import Path

import numpy as np

from cosmic_toolbox.file_utils import (
    ensure_permissions,
    get_abs_path,
    is_remote,
    read_from_hdf,
    read_from_pickle,
    read_yaml,
    robust_copy,
    robust_makedirs,
    robust_remove,
    write_to_hdf,
    write_to_pickle,
)


# Helper function to create temporary directory for tests
def setup_temp_dir():
    temp_dir = tempfile.mkdtemp()
    return temp_dir


def test_robust_remove():
    temp_dir = setup_temp_dir()
    try:
        # Test with str path - file
        test_file = os.path.join(temp_dir, "test_file.txt")
        with open(test_file, "w") as f:
            f.write("test")
        assert os.path.exists(test_file)
        robust_remove(test_file)
        assert not os.path.exists(test_file)

        # Test with str path - directory
        test_dir = os.path.join(temp_dir, "test_dir")
        os.makedirs(test_dir)
        assert os.path.exists(test_dir)
        robust_remove(test_dir)
        assert not os.path.exists(test_dir)

        # Test with pathlib.Path - file
        test_file = Path(temp_dir) / "test_file.txt"
        test_file.write_text("test")
        assert test_file.exists()
        robust_remove(test_file)
        assert not test_file.exists()

        # Test with pathlib.Path - directory
        test_dir = Path(temp_dir) / "test_dir"
        test_dir.mkdir()
        assert test_dir.exists()
        robust_remove(test_dir)
        assert not test_dir.exists()

        # Test non-existent path
        non_existent = os.path.join(temp_dir, "non_existent")
        robust_remove(non_existent)  # Should not raise error
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_pickle_functions():
    temp_dir = setup_temp_dir()
    try:
        test_data = {"test": "data", "list": [1, 2, 3]}

        # Test with str path
        file_path = os.path.join(temp_dir, "test.pkl")
        write_to_pickle(file_path, test_data)
        loaded_data = read_from_pickle(file_path)
        assert loaded_data == test_data

        # Test with pathlib.Path
        file_path = Path(temp_dir) / "test_path.pkl"
        write_to_pickle(file_path, test_data)
        loaded_data = read_from_pickle(file_path)
        assert loaded_data == test_data
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_hdf_functions():
    temp_dir = setup_temp_dir()
    try:
        test_data = np.array([1, 2, 3, 4, 5])

        # Test with str path
        file_path = os.path.join(temp_dir, "test.h5")
        write_to_hdf(file_path, test_data)
        loaded_data = read_from_hdf(file_path)
        np.testing.assert_array_equal(loaded_data, test_data)

        # Test with pathlib.Path
        file_path = Path(temp_dir) / "test_path.h5"
        write_to_hdf(file_path, test_data)
        loaded_data = read_from_hdf(file_path)
        np.testing.assert_array_equal(loaded_data, test_data)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_robust_makedirs():
    temp_dir = setup_temp_dir()
    try:
        # Test with str path
        test_dir = os.path.join(temp_dir, "new_dir", "nested_dir")
        assert not os.path.exists(test_dir)
        robust_makedirs(test_dir)
        assert os.path.exists(test_dir)

        # Test idempotence - should not raise error
        robust_makedirs(test_dir)

        # Test with pathlib.Path
        test_dir_path = Path(temp_dir) / "new_dir_path" / "nested_dir"
        assert not test_dir_path.exists()

        robust_makedirs(test_dir_path)
        assert test_dir_path.exists()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_get_abs_path():
    temp_dir = setup_temp_dir()
    try:
        # Test with absolute str path
        abs_path = os.path.abspath(temp_dir)
        result = get_abs_path(abs_path)
        assert result == abs_path

        # Test with relative str path (will depend on current directory)
        rel_path = "relative/path"
        result = get_abs_path(rel_path)
        assert os.path.isabs(result)

        # Test with remote-like path
        remote_path = "user@host:/path/to/dir"
        result = get_abs_path(remote_path)
        assert result == remote_path

        # Test with absolute Path object
        abs_path_obj = Path(temp_dir).absolute()

        result = get_abs_path(abs_path_obj)
        assert str(result) == str(abs_path_obj)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_robust_copy():
    temp_dir = setup_temp_dir()
    try:
        # Setup source directory with files
        src_dir = os.path.join(temp_dir, "src_dir")
        os.makedirs(src_dir)
        src_file = os.path.join(src_dir, "test.txt")
        with open(src_file, "w") as f:
            f.write("test content")

        # Test copying to destination directory - str paths
        dst_dir = os.path.join(temp_dir, "dst_dir")
        robust_copy(src_dir, dst_dir)

        assert os.path.exists(dst_dir)
        assert os.path.exists(os.path.join(dst_dir, "test.txt"))

        # Test copying a file - str paths
        dst_file = os.path.join(temp_dir, "test_copy.txt")
        robust_copy(src_file, dst_file)

        assert os.path.exists(dst_file)
        with open(dst_file, "r") as f:
            assert f.read() == "test content"

        # Test with Path objects
        src_dir_path = Path(temp_dir) / "src_dir_path"
        src_dir_path.mkdir()
        src_file_path = src_dir_path / "test.txt"
        src_file_path.write_text("test content")

        dst_dir_path = Path(temp_dir) / "dst_dir_path"
        robust_copy(src_dir_path, dst_dir_path)  # Convert dst to str as required

        assert dst_dir_path.exists()
        assert (dst_dir_path / "test.txt").exists()

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_is_remote():
    # Test with str paths
    assert is_remote("user@host:/path/to/dir") is True
    assert is_remote("/local/path") is False
    assert is_remote("relative/path") is False

    result = is_remote(Path("/local/path"))
    assert result is False


def test_read_yaml():
    temp_dir = setup_temp_dir()
    try:
        yaml_content = "key: value\nlist:\n  - item1\n  - item2"

        # Test with str path
        yaml_file = os.path.join(temp_dir, "test.yaml")
        with open(yaml_file, "w") as f:
            f.write(yaml_content)

        result = read_yaml(yaml_file)
        assert result == {"key": "value", "list": ["item1", "item2"]}

        # Test with Path object
        yaml_file_path = Path(temp_dir) / "test_path.yaml"
        yaml_file_path.write_text(yaml_content)

        result = read_yaml(yaml_file_path)
        assert result == {"key": "value", "list": ["item1", "item2"]}
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_ensure_permissions():
    temp_dir = setup_temp_dir()
    try:
        # Test with str path
        test_file = os.path.join(temp_dir, "test_perms.txt")
        with open(test_file, "w") as f:
            f.write("test")

        ensure_permissions(test_file)
        # Check permissions - should have at least read/write
        assert os.access(test_file, os.R_OK)
        assert os.access(test_file, os.W_OK)

        # Test with Path object
        test_file_path = Path(temp_dir) / "test_perms_path.txt"
        test_file_path.write_text("test")

        ensure_permissions(test_file_path)
        # Check permissions - should have at least read/write
        assert os.access(test_file_path, os.R_OK)
        assert os.access(test_file_path, os.W_OK)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
