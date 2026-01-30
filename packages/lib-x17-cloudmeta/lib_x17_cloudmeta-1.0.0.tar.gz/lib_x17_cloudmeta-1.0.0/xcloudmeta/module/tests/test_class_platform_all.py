from __future__ import annotations

import tempfile
from pathlib import Path

from xcloudmeta.base.modulekind import ModuleKind
from xcloudmeta.component.makefile import MakeFile
from xcloudmeta.component.metafile import MetaFile
from xcloudmeta.module.platform import Platform


def test_init_with_string_path_only():
    p = Platform("/tmp/test-platform")
    assert isinstance(p.path, Path)
    assert p.name == "test-platform"
    assert p.kind == ModuleKind.PLATFORM


def test_init_with_path_object():
    path = Path("/tmp/my-platform")
    p = Platform(path)
    assert isinstance(p.path, Path)
    assert p.name == "my-platform"
    assert p.kind == ModuleKind.PLATFORM


def test_kind_is_always_platform():
    p = Platform("/tmp/test-platform")
    assert p.kind == ModuleKind.PLATFORM
    assert p.kind.value == "platform"


def test_init_with_metafile_string():
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[project]\nname = "test"\n')
        p = Platform(tmp_dir, metafile="pyproject.toml")
        assert p.metafile is not None
        assert isinstance(p.metafile, MetaFile)


def test_init_with_makefile_string():
    with tempfile.TemporaryDirectory() as tmp_dir:
        make_file = Path(tmp_dir) / "Makefile"
        make_file.write_text('all:\n\techo "test"\n')
        p = Platform(tmp_dir, makefile="Makefile")
        assert p.makefile is not None
        assert isinstance(p.makefile, MakeFile)


def test_init_with_both_metafile_and_makefile():
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[project]\nname = "test"\n')
        make_file = Path(tmp_dir) / "Makefile"
        make_file.write_text('all:\n\techo "test"\n')
        p = Platform(tmp_dir, metafile="pyproject.toml", makefile="Makefile")
        assert p.metafile is not None
        assert p.makefile is not None


def test_metafile_has_platform_kind():
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[project]\nname = "test"\n')
        p = Platform(tmp_dir, metafile="pyproject.toml")
        assert p.metafile.kind == ModuleKind.PLATFORM


def test_meta_returns_data_from_metafile():
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[project]\nname = "platform-test"\n')
        p = Platform(tmp_dir, metafile="pyproject.toml")
        assert "project" in p.meta
        assert p.meta["project"]["name"] == "platform-test"


def test_meta_returns_empty_dict_when_no_metafile():
    p = Platform("/tmp/test-platform")
    assert p.meta == {}


def test_str_returns_platform_name():
    p = Platform("/tmp/my-platform")
    assert str(p) == "my-platform"


def test_repr_returns_class_and_path():
    p = Platform("/tmp/test-platform")
    repr_str = repr(p)
    assert "Platform" in repr_str
    assert "path=" in repr_str


def test_describe_returns_platform_kind():
    p = Platform("/tmp/test-platform")
    desc = p.describe()
    assert desc["kind"] == "platform"


def test_describe_contains_metadata():
    p = Platform("/tmp/test-platform")
    desc = p.describe()
    assert "path" in desc
    assert "kind" in desc
    assert "meta" in desc


def test_inherits_from_module_class():
    p = Platform("/tmp/test-platform")
    assert hasattr(p, "is_exist")
    assert hasattr(p, "is_folder")
    assert hasattr(p, "describe")


def test_is_exist_returns_false_for_nonexistent():
    p = Platform("/nonexistent/platform")
    assert p.is_exist() is False


def test_is_exist_returns_true_for_existing_folder():
    with tempfile.TemporaryDirectory() as tmp_dir:
        p = Platform(tmp_dir)
        assert p.is_exist() is True


def test_multiple_platform_instances_independent():
    p1 = Platform("/tmp/platform1")
    p2 = Platform("/tmp/platform2")
    assert p1.name != p2.name
    assert p1.kind == p2.kind


def test_metafile_path_is_relative_to_platform():
    with tempfile.TemporaryDirectory() as tmp_dir:
        p = Platform(tmp_dir, metafile="config.toml")
        expected_path = (Path(tmp_dir) / "config.toml").resolve()
        assert p.metafile.path == expected_path


def test_makefile_path_is_relative_to_platform():
    with tempfile.TemporaryDirectory() as tmp_dir:
        p = Platform(tmp_dir, makefile="Makefile")
        expected_path = (Path(tmp_dir) / "Makefile").resolve()
        assert p.makefile.path == expected_path


def test_validity_true_with_platform_metadata():
    """Test validity is True when [platform] section exists."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[platform]\nname = "aws"\n')
        p = Platform(tmp_dir, metafile="pyproject.toml")
        assert p.validity is True


def test_validity_false_without_platform_section():
    """Test validity is False when [platform] section missing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[project]\nname = "test"\n')
        p = Platform(tmp_dir, metafile="pyproject.toml")
        assert p.validity is False


def test_validity_false_without_metafile():
    """Test validity is False when no metafile."""
    p = Platform("/tmp/test-platform")
    assert p.validity is False


def test_metabase_extracts_platform_section():
    """Test metabase returns [platform] section from metadata."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[platform]\nname = "aws"\naccount = "123456"\n')
        p = Platform(tmp_dir, metafile="pyproject.toml")
        assert p.metabase == {"name": "aws", "account": "123456"}


def test_metabase_empty_when_no_platform_section():
    """Test metabase is empty dict when no [platform] section."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[project]\nname = "test"\n')
        p = Platform(tmp_dir, metafile="pyproject.toml")
        assert p.metabase == {}


def test_platform_name_extraction():
    """Test platform name is extracted from metabase."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[platform]\nname = "gcp"\n')
        p = Platform(tmp_dir, metafile="pyproject.toml")
        assert p.platform == "gcp"


def test_platform_none_when_not_provided():
    """Test platform is None when name not in metadata."""
    p = Platform("/tmp/test-platform")
    assert p.platform is None


def test_account_extraction():
    """Test account is extracted from metabase."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[platform]\naccount = "987654321"\n')
        p = Platform(tmp_dir, metafile="pyproject.toml")
        assert p.account == "987654321"


def test_account_none_when_not_provided():
    """Test account is None when not in metadata."""
    p = Platform("/tmp/test-platform")
    assert p.account is None


def test_region_extraction():
    """Test region is extracted from metabase."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[platform]\nregion = "us-east-1"\n')
        p = Platform(tmp_dir, metafile="pyproject.toml")
        assert p.region == "us-east-1"


def test_region_none_when_not_provided():
    """Test region is None when not in metadata."""
    p = Platform("/tmp/test-platform")
    assert p.region is None


def test_alias_extraction():
    """Test alias is extracted from metabase."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[platform]\nalias = "prod-aws"\n')
        p = Platform(tmp_dir, metafile="pyproject.toml")
        assert p.alias == "prod-aws"


def test_alias_none_when_not_provided():
    """Test alias is None when not in metadata."""
    p = Platform("/tmp/test-platform")
    assert p.alias is None


def test_code_extraction():
    """Test code is extracted from metabase."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[platform]\ncode = "P-001"\n')
        p = Platform(tmp_dir, metafile="pyproject.toml")
        assert p.code == "P-001"


def test_code_none_when_not_provided():
    """Test code is None when not in metadata."""
    p = Platform("/tmp/test-platform")
    assert p.code is None


def test_get_name_returns_platform():
    """Test get_name() returns platform attribute."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[platform]\nname = "azure"\n')
        p = Platform(tmp_dir, metafile="pyproject.toml")
        assert p.get_name() == "azure"


def test_get_account_returns_account():
    """Test get_account() returns account attribute."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[platform]\naccount = "111222333"\n')
        p = Platform(tmp_dir, metafile="pyproject.toml")
        assert p.get_account() == "111222333"


def test_get_region_returns_region():
    """Test get_region() returns region attribute."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[platform]\nregion = "eu-west-1"\n')
        p = Platform(tmp_dir, metafile="pyproject.toml")
        assert p.get_region() == "eu-west-1"


def test_get_alias_returns_alias():
    """Test get_alias() returns alias attribute."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[platform]\nalias = "dev-platform"\n')
        p = Platform(tmp_dir, metafile="pyproject.toml")
        assert p.get_alias() == "dev-platform"


def test_get_code_returns_code():
    """Test get_code() returns code attribute."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[platform]\ncode = "PLT-999"\n')
        p = Platform(tmp_dir, metafile="pyproject.toml")
        assert p.get_code() == "PLT-999"


def test_complete_platform_configuration():
    """Test Platform with complete configuration."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_content = """
[platform]
name = "aws"
account = "123456789012"
region = "us-west-2"
alias = "production"
code = "AWS-PROD"
"""
        toml_file.write_text(toml_content)
        p = Platform(tmp_dir, metafile="pyproject.toml")
        assert p.validity is True
        assert p.platform == "aws"
        assert p.account == "123456789012"
        assert p.region == "us-west-2"
        assert p.alias == "production"
        assert p.code == "AWS-PROD"
        assert p.get_name() == "aws"
        assert p.get_account() == "123456789012"
        assert p.get_region() == "us-west-2"
        assert p.get_alias() == "production"
        assert p.get_code() == "AWS-PROD"
