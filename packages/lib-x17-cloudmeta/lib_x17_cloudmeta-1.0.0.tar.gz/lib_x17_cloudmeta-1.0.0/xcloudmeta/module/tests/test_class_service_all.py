from __future__ import annotations

import tempfile
from pathlib import Path

from xcloudmeta.base.modulekind import ModuleKind
from xcloudmeta.component.makefile import MakeFile
from xcloudmeta.component.metafile import MetaFile
from xcloudmeta.module.service import Service


def test_init_with_string_path_only():
    s = Service("/tmp/test-service")
    assert isinstance(s.path, Path)
    assert s.name == "test-service"
    assert s.kind == ModuleKind.SERVICE


def test_init_with_path_object():
    path = Path("/tmp/my-service")
    s = Service(path)
    assert isinstance(s.path, Path)
    assert s.name == "my-service"
    assert s.kind == ModuleKind.SERVICE


def test_kind_is_always_service():
    s = Service("/tmp/test-service")
    assert s.kind == ModuleKind.SERVICE
    assert s.kind.value == "service"


def test_init_with_metafile_string():
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[project]\nname = "test"\n')
        s = Service(tmp_dir, metafile="pyproject.toml")
        assert s.metafile is not None
        assert isinstance(s.metafile, MetaFile)


def test_init_with_makefile_string():
    with tempfile.TemporaryDirectory() as tmp_dir:
        make_file = Path(tmp_dir) / "Makefile"
        make_file.write_text('all:\n\techo "test"\n')
        s = Service(tmp_dir, makefile="Makefile")
        assert s.makefile is not None
        assert isinstance(s.makefile, MakeFile)


def test_init_with_both_metafile_and_makefile():
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[project]\nname = "test"\n')
        make_file = Path(tmp_dir) / "Makefile"
        make_file.write_text('all:\n\techo "test"\n')
        s = Service(tmp_dir, metafile="pyproject.toml", makefile="Makefile")
        assert s.metafile is not None
        assert s.makefile is not None


def test_metafile_has_service_kind():
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[project]\nname = "test"\n')
        s = Service(tmp_dir, metafile="pyproject.toml")
        assert s.metafile.kind == ModuleKind.SERVICE


def test_meta_returns_data_from_metafile():
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[project]\nname = "service-test"\n')
        s = Service(tmp_dir, metafile="pyproject.toml")
        assert "project" in s.meta
        assert s.meta["project"]["name"] == "service-test"


def test_meta_returns_empty_dict_when_no_metafile():
    s = Service("/tmp/test-service")
    assert s.meta == {}


def test_str_returns_service_name():
    s = Service("/tmp/my-service")
    assert str(s) == "my-service"


def test_repr_returns_class_and_path():
    s = Service("/tmp/test-service")
    repr_str = repr(s)
    assert "Service" in repr_str
    assert "path=" in repr_str


def test_describe_returns_service_kind():
    s = Service("/tmp/test-service")
    desc = s.describe()
    assert desc["kind"] == "service"


def test_describe_contains_metadata():
    s = Service("/tmp/test-service")
    desc = s.describe()
    assert "path" in desc
    assert "kind" in desc
    assert "meta" in desc


def test_inherits_from_module_class():
    s = Service("/tmp/test-service")
    assert hasattr(s, "is_exist")
    assert hasattr(s, "is_folder")
    assert hasattr(s, "describe")


def test_is_exist_returns_false_for_nonexistent():
    s = Service("/nonexistent/service")
    assert s.is_exist() is False


def test_is_exist_returns_true_for_existing_folder():
    with tempfile.TemporaryDirectory() as tmp_dir:
        s = Service(tmp_dir)
        assert s.is_exist() is True


def test_multiple_service_instances_independent():
    s1 = Service("/tmp/service1")
    s2 = Service("/tmp/service2")
    assert s1.name != s2.name
    assert s1.kind == s2.kind


def test_metafile_path_is_relative_to_service():
    with tempfile.TemporaryDirectory() as tmp_dir:
        s = Service(tmp_dir, metafile="config.toml")
        expected_path = (Path(tmp_dir) / "config.toml").resolve()
        assert s.metafile.path == expected_path


def test_makefile_path_is_relative_to_service():
    with tempfile.TemporaryDirectory() as tmp_dir:
        s = Service(tmp_dir, makefile="Makefile")
        expected_path = (Path(tmp_dir) / "Makefile").resolve()
        assert s.makefile.path == expected_path


def test_validity_true_with_service_metadata():
    """Test validity is True when [service] section exists."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[service]\nname = "test-service"\n')
        s = Service(tmp_dir, metafile="pyproject.toml")
        assert s.validity is True


def test_validity_false_without_service_section():
    """Test validity is False when [service] section missing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[project]\nname = "test"\n')
        s = Service(tmp_dir, metafile="pyproject.toml")
        assert s.validity is False


def test_validity_false_without_metafile():
    """Test validity is False when no metafile."""
    s = Service("/tmp/test-service")
    assert s.validity is False


def test_metabase_extracts_service_section():
    """Test metabase returns [service] section from metadata."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[service]\nname = "svc"\ncode = "S001"\n')
        s = Service(tmp_dir, metafile="pyproject.toml")
        assert s.metabase == {"name": "svc", "code": "S001"}


def test_metabase_empty_when_no_service_section():
    """Test metabase is empty dict when no [service] section."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[project]\nname = "test"\n')
        s = Service(tmp_dir, metafile="pyproject.toml")
        assert s.metabase == {}


def test_service_name_extraction():
    """Test service name is extracted from metabase."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[service]\nname = "my-service"\n')
        s = Service(tmp_dir, metafile="pyproject.toml")
        assert s.service == "my-service"


def test_service_none_when_not_provided():
    """Test service is None when name not in metadata."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[service]\ncode = "S001"\n')
        s = Service(tmp_dir, metafile="pyproject.toml")
        assert s.service is None


def test_code_extraction():
    """Test code is extracted from metabase."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[service]\ncode = "SVC-123"\n')
        s = Service(tmp_dir, metafile="pyproject.toml")
        assert s.code == "SVC-123"


def test_code_none_when_not_provided():
    """Test code is None when not in metadata."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[service]\nname = "test"\n')
        s = Service(tmp_dir, metafile="pyproject.toml")
        assert s.code is None


def test_alias_extraction():
    """Test alias is extracted from metabase."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[service]\nalias = "srv"\n')
        s = Service(tmp_dir, metafile="pyproject.toml")
        assert s.alias == "srv"


def test_alias_none_when_not_provided():
    """Test alias is None when not in metadata."""
    s = Service("/tmp/test-service")
    assert s.alias is None


def test_get_name_returns_service():
    """Test get_name() returns service attribute."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[service]\nname = "test-svc"\n')
        s = Service(tmp_dir, metafile="pyproject.toml")
        assert s.get_name() == "test-svc"


def test_get_code_returns_code():
    """Test get_code() returns code attribute."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[service]\ncode = "C123"\n')
        s = Service(tmp_dir, metafile="pyproject.toml")
        assert s.get_code() == "C123"


def test_get_alias_returns_alias():
    """Test get_alias() returns alias attribute."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_file.write_text('[service]\nalias = "svc-alias"\n')
        s = Service(tmp_dir, metafile="pyproject.toml")
        assert s.get_alias() == "svc-alias"


def test_complete_service_configuration():
    """Test Service with complete configuration."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        toml_file = Path(tmp_dir) / "pyproject.toml"
        toml_content = """
[service]
name = "complete-service"
code = "SVC-999"
alias = "comp-svc"
"""
        toml_file.write_text(toml_content)
        s = Service(tmp_dir, metafile="pyproject.toml")
        assert s.validity is True
        assert s.service == "complete-service"
        assert s.code == "SVC-999"
        assert s.alias == "comp-svc"
        assert s.get_name() == "complete-service"
        assert s.get_code() == "SVC-999"
        assert s.get_alias() == "comp-svc"
