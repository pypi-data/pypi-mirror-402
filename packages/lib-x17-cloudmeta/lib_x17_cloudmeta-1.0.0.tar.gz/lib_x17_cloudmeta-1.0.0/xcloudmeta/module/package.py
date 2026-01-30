from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from xcloudmeta.base.modulekind import ModuleKind
from xcloudmeta.module.module import Module


class Package(Module):
    """
    Desc:
        Represents a package module for shared libraries or dependencies.

    Params:
        path: str | Path: Path to the package directory
        metafile: Optional[str]: Name of the package metadata file
        makefile: Optional[str]: Name of the package makefile

    Methods:
        Inherits all methods from Module class
    """

    def __init__(
        self,
        path: str | Path,
        metafile: Optional[str] = None,
        makefile: Optional[str] = None,
    ) -> None:
        super().__init__(
            path,
            kind=ModuleKind.PACKAGE,
            metafile=metafile,
            makefile=makefile,
        )
        self.validity = self._resolve_validity()
        self.metabase = self._resolve_metabase()
        self.package = self._resolve_package()
        self.version = self._resolve_version()
        self.where = self._resolve_where()
        self.editable = self._resolve_editable()
        self.mode = self._resolve_mode()

    def _resolve_validity(
        self,
    ) -> bool:
        if not self.meta:
            return False
        if not isinstance(self.meta, dict):
            return False
        if not self.meta.get("package"):
            return False
        return True

    def _resolve_metabase(
        self,
    ) -> Dict[str, Any]:
        if self.validity is False:
            return {}
        return self.meta.get("package", {})

    def _resolve_package(
        self,
    ) -> Optional[str]:
        package = self.metabase.get("name")
        if not package or not isinstance(package, str):
            raise ValueError(f"[package].name is required: {self.path}")
        return package

    def _resolve_version(
        self,
    ) -> Optional[str]:
        version = self.metabase.get("version")
        if not version:
            return None
        if not isinstance(version, str):
            raise ValueError(f"[package].version must be string: {self.path}")
        if version.lower() == "latest":
            return None
        else:
            return version

    def _resolve_where(
        self,
    ) -> Optional[Path]:
        where = self.metabase.get("where")
        if where is None or where == "":
            return None

        if not isinstance(where, str):
            raise ValueError(f"[package].where must be string: {self.path}")

        p = Path(where)
        if p.is_absolute():
            resolved = p
        else:
            resolved = (self.path / p).resolve()

        if not resolved.exists() or not resolved.is_dir():
            raise ValueError(f"[package].where invalid source: {resolved}")
        return resolved

    def _resolve_editable(
        self,
    ) -> bool:
        editable = self.metabase.get("editable", False)
        if isinstance(editable, bool):
            return editable
        raise ValueError(f"[package].editable must be bool: {self.path}")

    def _resolve_mode(
        self,
    ) -> str:
        if self.where and self.where.exists():
            return "local"
        else:
            return "remote"

    def vend(
        self,
    ) -> None:
        """
        Desc:
            Placeholder method for vendoring the package.
        """
        pass
