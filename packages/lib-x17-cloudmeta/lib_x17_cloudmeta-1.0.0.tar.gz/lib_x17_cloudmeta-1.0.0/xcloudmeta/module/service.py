from __future__ import annotations

from pathlib import Path
from typing import Optional

from xcloudmeta.base.modulekind import ModuleKind
from xcloudmeta.module.module import Module


class Service(Module):
    """
    Desc:
        Represents a service module (e.g., API, web app, worker).

    Params:
        path: str | Path: Path to the service directory
        metafile: Optional[str]: Name of the service metadata file
        makefile: Optional[str]: Name of the service makefile

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
            kind=ModuleKind.SERVICE,
            metafile=metafile,
            makefile=makefile,
        )
        self.validity = self._resolve_validity()
        self.metabase = self._resolve_metabase()
        self.code = self._resolve_code()
        self.service = self._resolve_service()
        self.alias = self._resolve_alias()

    def _resolve_validity(
        self,
    ) -> bool:
        if not self.meta:
            return False
        if not isinstance(self.meta, dict):
            return False
        if not self.meta.get("service"):
            return False
        return True

    def _resolve_metabase(
        self,
    ) -> Optional[dict]:
        return self.meta.get("service", {})

    def _resolve_code(
        self,
    ) -> Optional[str]:
        return self.metabase.get("code")

    def _resolve_service(
        self,
    ) -> Optional[str]:
        return self.metabase.get("name")

    def _resolve_alias(
        self,
    ) -> Optional[str]:
        return self.metabase.get("alias")

    def get_code(self) -> Optional[str]:
        return self.code

    def get_name(self) -> Optional[str]:
        return self.service

    def get_alias(self) -> Optional[str]:
        return self.alias
