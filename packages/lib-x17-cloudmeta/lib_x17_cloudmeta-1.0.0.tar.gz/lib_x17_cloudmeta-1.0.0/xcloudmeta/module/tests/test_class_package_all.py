"""
Tests for the Package class in xcloudmeta.module.package module.
Using modern pytest function format.
"""

import tempfile
from pathlib import Path

import pytest

from xcloudmeta.base.modulekind import ModuleKind
from xcloudmeta.module.module import Module
from xcloudmeta.module.package import Package


def test_init_with_valid_package_metadata():
    """Test Package initialization with valid package metadata."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[package]\nname = "test-pkg"\nversion = "1.0.0"\n')
        pkg = Package(tmp_dir, metafile="pyproject.toml")
        assert pkg.kind == ModuleKind.PACKAGE
        assert pkg.package == "test-pkg"
        assert pkg.version == "1.0.0"
        assert pkg.validity is True


def test_init_without_metadata_fails():
    """Test Package initialization without metadata raises ValueError."""
    with pytest.raises(ValueError, match=r"\[package\].name is required"):
        Package("/tmp/test-package")


def test_validity_false_when_no_meta():
    """Test Package raises error when no metadata file exists."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        with pytest.raises(ValueError, match=r"\[package\].name is required"):
            Package(tmp_dir)


def test_validity_false_when_no_package_section():
    """Test validity is False when [package] section missing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[project]\nname = "test"\n')
        with pytest.raises(ValueError, match=r"\[package\].name is required"):
            Package(tmp_dir, metafile="pyproject.toml")


def test_package_name_extraction():
    """Test package name is correctly extracted from metadata."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[package]\nname = "awesome-package"\n')
        pkg = Package(tmp_dir, metafile="pyproject.toml")
        assert pkg.package == "awesome-package"


def test_package_name_required_raises_error():
    """Test missing package name raises ValueError."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[package]\nversion = "1.0.0"\n')
        with pytest.raises(ValueError, match=r"\[package\].name is required"):
            Package(tmp_dir, metafile="pyproject.toml")


def test_version_extraction_with_valid_version():
    """Test version is correctly extracted when provided."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[package]\nname = "pkg"\nversion = "2.5.3"\n')
        pkg = Package(tmp_dir, metafile="pyproject.toml")
        assert pkg.version == "2.5.3"


def test_version_none_when_not_provided():
    """Test version is None when not provided in metadata."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[package]\nname = "pkg"\n')
        pkg = Package(tmp_dir, metafile="pyproject.toml")
        assert pkg.version is None


def test_version_none_when_latest():
    """Test version is None when set to 'latest'."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[package]\nname = "pkg"\nversion = "latest"\n')
        pkg = Package(tmp_dir, metafile="pyproject.toml")
        assert pkg.version is None


def test_version_case_insensitive_latest():
    """Test version 'LATEST' (uppercase) is treated as None."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[package]\nname = "pkg"\nversion = "LATEST"\n')
        pkg = Package(tmp_dir, metafile="pyproject.toml")
        assert pkg.version is None


def test_version_invalid_type_raises_error():
    """Test non-string version raises ValueError."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[package]\nname = "pkg"\nversion = 123\n')
        with pytest.raises(ValueError, match=r"\[package\].version must be string"):
            Package(tmp_dir, metafile="pyproject.toml")


def test_where_none_when_not_provided():
    """Test where is None when not provided."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[package]\nname = "pkg"\n')
        pkg = Package(tmp_dir, metafile="pyproject.toml")
        assert pkg.where is None


def test_where_none_when_empty_string():
    """Test where is None when empty string."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[package]\nname = "pkg"\nwhere = ""\n')
        pkg = Package(tmp_dir, metafile="pyproject.toml")
        assert pkg.where is None


def test_where_resolves_relative_path():
    """Test where resolves relative paths correctly."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        src_dir = Path(tmp_dir) / "src"
        src_dir.mkdir()
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[package]\nname = "pkg"\nwhere = "src"\n')
        pkg = Package(tmp_dir, metafile="pyproject.toml")
        assert pkg.where == src_dir.resolve()


def test_where_resolves_absolute_path():
    """Test where handles absolute paths."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        another_dir = Path(tmp_dir) / "another"
        another_dir.mkdir()
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text(f'[package]\nname = "pkg"\nwhere = "{another_dir}"\n')
        pkg = Package(tmp_dir, metafile="pyproject.toml")
        assert pkg.where == another_dir


def test_where_invalid_path_raises_error():
    """Test where with non-existent path raises ValueError."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[package]\nname = "pkg"\nwhere = "nonexistent"\n')
        with pytest.raises(ValueError, match=r"\[package\].where invalid source"):
            Package(tmp_dir, metafile="pyproject.toml")


def test_where_invalid_type_raises_error():
    """Test where with non-string value raises ValueError."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[package]\nname = "pkg"\nwhere = 123\n')
        with pytest.raises(ValueError, match=r"\[package\].where must be string"):
            Package(tmp_dir, metafile="pyproject.toml")


def test_editable_false_by_default():
    """Test editable defaults to False."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[package]\nname = "pkg"\n')
        pkg = Package(tmp_dir, metafile="pyproject.toml")
        assert pkg.editable is False


def test_editable_true_when_set():
    """Test editable can be set to True."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[package]\nname = "pkg"\neditable = true\n')
        pkg = Package(tmp_dir, metafile="pyproject.toml")
        assert pkg.editable is True


def test_editable_invalid_type_raises_error():
    """Test editable with non-bool value raises ValueError."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[package]\nname = "pkg"\neditable = "yes"\n')
        with pytest.raises(ValueError, match=r"\[package\].editable must be bool"):
            Package(tmp_dir, metafile="pyproject.toml")


def test_mode_remote_when_no_where():
    """Test mode is 'remote' when where is not set."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[package]\nname = "pkg"\n')
        pkg = Package(tmp_dir, metafile="pyproject.toml")
        assert pkg.mode == "remote"


def test_mode_local_when_where_set():
    """Test mode is 'local' when where is set."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        src_dir = Path(tmp_dir) / "src"
        src_dir.mkdir()
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[package]\nname = "pkg"\nwhere = "src"\n')
        pkg = Package(tmp_dir, metafile="pyproject.toml")
        assert pkg.mode == "local"


def test_inherits_from_module_class():
    """Test Package inherits from Module."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[package]\nname = "pkg"\n')
        pkg = Package(tmp_dir, metafile="pyproject.toml")
        assert isinstance(pkg, Module)
        assert isinstance(pkg, Package)


def test_kind_is_always_package():
    """Test kind is always PACKAGE."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[package]\nname = "pkg"\n')
        pkg = Package(tmp_dir, metafile="pyproject.toml")
        assert pkg.kind == ModuleKind.PACKAGE


def test_str_returns_folder_name():
    """Test __str__ returns folder name."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[package]\nname = "pkg"\n')
        pkg = Package(tmp_dir, metafile="pyproject.toml")
        folder_name = Path(tmp_dir).name
        assert str(pkg) == folder_name


def test_repr_contains_class_and_path():
    """Test __repr__ contains class name and path."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[package]\nname = "pkg"\n')
        pkg = Package(tmp_dir, metafile="pyproject.toml")
        repr_str = repr(pkg)
        assert "Package" in repr_str
        assert "path=" in repr_str


def test_with_makefile():
    """Test Package with makefile."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[package]\nname = "pkg"\n')
        make_file = Path(tmp_dir) / "Makefile"
        make_file.write_text('all:\n\techo "test"\n')
        pkg = Package(tmp_dir, metafile="pyproject.toml", makefile="Makefile")
        assert pkg.makefile is not None


def test_metabase_contains_package_section():
    """Test metabase extracts [package] section."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[package]\nname = "pkg"\nversion = "1.0"\n')
        pkg = Package(tmp_dir, metafile="pyproject.toml")
        assert isinstance(pkg.metabase, dict)
        assert pkg.metabase.get("name") == "pkg"
        assert pkg.metabase.get("version") == "1.0"


def test_complete_package_configuration():
    """Test Package with complete configuration."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        src_dir = Path(tmp_dir) / "src"
        src_dir.mkdir()
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_content = """
[package]
name = "complete-pkg"
version = "3.2.1"
where = "src"
editable = true
"""
        toml_file.write_text(toml_content)
        pkg = Package(tmp_dir, metafile="pyproject.toml")
        assert pkg.package == "complete-pkg"
        assert pkg.version == "3.2.1"
        assert pkg.where == src_dir.resolve()
        assert pkg.editable is True
        assert pkg.mode == "local"
        assert pkg.validity is True
