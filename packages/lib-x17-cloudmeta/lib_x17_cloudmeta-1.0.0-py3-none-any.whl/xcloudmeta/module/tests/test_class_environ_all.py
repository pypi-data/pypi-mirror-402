from __future__ import annotations

import tempfile
from pathlib import Path

from xcloudmeta.base.modulekind import ModuleKind
from xcloudmeta.component.makefile import MakeFile
from xcloudmeta.component.metafile import MetaFile
from xcloudmeta.module.environ import Environ


def test_init_with_string_path_only():
    e = Environ("/tmp/test-environ")
    assert isinstance(e.path, Path)
    assert e.name == "test-environ"
    assert e.kind == ModuleKind.ENVIRON


def test_init_with_path_object():
    path = Path("/tmp/my-environ")
    e = Environ(path)
    assert isinstance(e.path, Path)
    assert e.name == "my-environ"
    assert e.kind == ModuleKind.ENVIRON


def test_kind_is_always_environ():
    e = Environ("/tmp/test-environ")
    assert e.kind == ModuleKind.ENVIRON
    assert e.kind.value == "environ"


def test_init_with_metafile_string():
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[project]\nname = "test"\n')
        e = Environ(tmp_dir, metafile="pyproject.toml")
        assert e.metafile is not None
        assert isinstance(e.metafile, MetaFile)


def test_init_with_makefile_string():
    with tempfile.TemporaryDirectory() as tmp_dir:
        make_file = Path(tmp_dir) / "Makefile"
        make_file.write_text('all:\n\techo "test"\n')
        e = Environ(tmp_dir, makefile="Makefile")
        assert e.makefile is not None
        assert isinstance(e.makefile, MakeFile)


def test_init_with_both_metafile_and_makefile():
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[project]\nname = "test"\n')
        make_file = Path(tmp_dir) / "Makefile"
        make_file.write_text('all:\n\techo "test"\n')
        e = Environ(tmp_dir, metafile="pyproject.toml", makefile="Makefile")
        assert e.metafile is not None
        assert e.makefile is not None


def test_metafile_has_environ_kind():
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[project]\nname = "test"\n')
        e = Environ(tmp_dir, metafile="pyproject.toml")
        assert e.metafile.kind == ModuleKind.ENVIRON


def test_meta_returns_data_from_metafile():
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[project]\nname = "environ-test"\n')
        e = Environ(tmp_dir, metafile="pyproject.toml")
        assert "project" in e.meta
        assert e.meta["project"]["name"] == "environ-test"


def test_meta_returns_empty_dict_when_no_metafile():
    e = Environ("/tmp/test-environ")
    assert e.meta == {}


def test_str_returns_environ_name():
    e = Environ("/tmp/my-environ")
    assert str(e) == "my-environ"


def test_repr_returns_class_and_path():
    e = Environ("/tmp/test-environ")
    repr_str = repr(e)
    assert "Environ" in repr_str
    assert "path=" in repr_str


def test_describe_returns_environ_kind():
    e = Environ("/tmp/test-environ")
    desc = e.describe()
    assert desc["kind"] == "environ"


def test_describe_contains_metadata():
    e = Environ("/tmp/test-environ")
    desc = e.describe()
    assert "path" in desc
    assert "kind" in desc
    assert "meta" in desc


def test_inherits_from_module_class():
    e = Environ("/tmp/test-environ")
    assert hasattr(e, "is_exist")
    assert hasattr(e, "is_folder")
    assert hasattr(e, "describe")


def test_is_exist_returns_false_for_nonexistent():
    e = Environ("/nonexistent/environ")
    assert e.is_exist() is False


def test_is_exist_returns_true_for_existing_folder():
    with tempfile.TemporaryDirectory() as tmp_dir:
        e = Environ(tmp_dir)
        assert e.is_exist() is True


def test_multiple_environ_instances_independent():
    e1 = Environ("/tmp/environ1")
    e2 = Environ("/tmp/environ2")
    assert e1.name != e2.name
    assert e1.kind == e2.kind


def test_metafile_path_is_relative_to_environ():
    with tempfile.TemporaryDirectory() as tmp_dir:
        e = Environ(tmp_dir, metafile="config.toml")
        expected_path = (Path(tmp_dir) / "config.toml").resolve()
        assert e.metafile.path == expected_path


def test_makefile_path_is_relative_to_environ():
    with tempfile.TemporaryDirectory() as tmp_dir:
        e = Environ(tmp_dir, makefile="Makefile")
        expected_path = (Path(tmp_dir) / "Makefile").resolve()
        assert e.makefile.path == expected_path


def test_validity_true_with_environ_metadata():
    """Test validity is True when [environ] section exists."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[environ]\nname = "dev"\n')
        e = Environ(tmp_dir, metafile="pyproject.toml")
        assert e.validity is True


def test_validity_false_without_environ_section():
    """Test validity is False when [environ] section missing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[project]\nname = "test"\n')
        e = Environ(tmp_dir, metafile="pyproject.toml")
        assert e.validity is False


def test_validity_false_without_metafile():
    """Test validity is False when no metafile."""
    e = Environ("/tmp/test-environ")
    assert e.validity is False


def test_metabase_extracts_environ_section():
    """Test metabase returns [environ] section from metadata."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[environ]\nname = "prod"\naccount = "999888"\n')
        e = Environ(tmp_dir, metafile="pyproject.toml")
        assert e.metabase == {"name": "prod", "account": "999888"}


def test_metabase_empty_when_no_environ_section():
    """Test metabase is empty dict when no [environ] section."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[project]\nname = "test"\n')
        e = Environ(tmp_dir, metafile="pyproject.toml")
        assert e.metabase == {}


def test_environ_name_extraction():
    """Test environ name is extracted from metabase."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[environ]\nname = "staging"\n')
        e = Environ(tmp_dir, metafile="pyproject.toml")
        assert e.environ == "staging"


def test_environ_none_when_not_provided():
    """Test environ is None when name not in metadata."""
    e = Environ("/tmp/test-environ")
    assert e.environ is None


def test_account_extraction():
    """Test account is extracted from metabase."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[environ]\naccount = "555666777"\n')
        e = Environ(tmp_dir, metafile="pyproject.toml")
        assert e.account == "555666777"


def test_account_none_when_not_provided():
    """Test account is None when not in metadata."""
    e = Environ("/tmp/test-environ")
    assert e.account is None


def test_region_extraction():
    """Test region is extracted from metabase."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[environ]\nregion = "ap-southeast-1"\n')
        e = Environ(tmp_dir, metafile="pyproject.toml")
        assert e.region == "ap-southeast-1"


def test_region_none_when_not_provided():
    """Test region is None when not in metadata."""
    e = Environ("/tmp/test-environ")
    assert e.region is None


def test_alias_extraction():
    """Test alias is extracted from metabase."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[environ]\nalias = "dev-env"\n')
        e = Environ(tmp_dir, metafile="pyproject.toml")
        assert e.alias == "dev-env"


def test_alias_none_when_not_provided():
    """Test alias is None when not in metadata."""
    e = Environ("/tmp/test-environ")
    assert e.alias is None


def test_code_extraction():
    """Test code is extracted from metabase."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[environ]\ncode = "E-001"\n')
        e = Environ(tmp_dir, metafile="pyproject.toml")
        assert e.code == "E-001"


def test_code_none_when_not_provided():
    """Test code is None when not in metadata."""
    e = Environ("/tmp/test-environ")
    assert e.code is None


def test_get_name_returns_environ():
    """Test get_name() returns environ attribute."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[environ]\nname = "production"\n')
        e = Environ(tmp_dir, metafile="pyproject.toml")
        assert e.get_name() == "production"


def test_get_account_returns_account():
    """Test get_account() returns account attribute."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[environ]\naccount = "444555666"\n')
        e = Environ(tmp_dir, metafile="pyproject.toml")
        assert e.get_account() == "444555666"


def test_get_region_returns_region():
    """Test get_region() returns region attribute."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[environ]\nregion = "ca-central-1"\n')
        e = Environ(tmp_dir, metafile="pyproject.toml")
        assert e.get_region() == "ca-central-1"


def test_get_alias_returns_alias():
    """Test get_alias() returns alias attribute."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[environ]\nalias = "staging-env"\n')
        e = Environ(tmp_dir, metafile="pyproject.toml")
        assert e.get_alias() == "staging-env"


def test_get_code_returns_code():
    """Test get_code() returns code attribute."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[environ]\ncode = "ENV-999"\n')
        e = Environ(tmp_dir, metafile="pyproject.toml")
        assert e.get_code() == "ENV-999"


def test_complete_environ_configuration():
    """Test Environ with complete configuration."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_content = """
[environ]
name = "production"
account = "111222333444"
region = "us-east-1"
alias = "prod"
code = "PROD-ENV"
"""
        toml_file.write_text(toml_content)
        e = Environ(tmp_dir, metafile="pyproject.toml")
        assert e.validity is True
        assert e.environ == "production"
        assert e.account == "111222333444"
        assert e.region == "us-east-1"
        assert e.alias == "prod"
        assert e.code == "PROD-ENV"
        assert e.get_name() == "production"
        assert e.get_account() == "111222333444"
        assert e.get_region() == "us-east-1"
        assert e.get_alias() == "prod"
        assert e.get_code() == "PROD-ENV"
