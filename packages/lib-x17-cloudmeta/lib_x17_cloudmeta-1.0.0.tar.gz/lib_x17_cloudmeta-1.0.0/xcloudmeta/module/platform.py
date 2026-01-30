from __future__ import annotations

from pathlib import Path
from typing import Optional

from xcloudmeta.base.modulekind import ModuleKind
from xcloudmeta.module.module import Module


class Platform(Module):
    """
    Desc:
        Represents a cloud platform module (e.g., AWS, GCP, Azure).

    Params:
        path: str | Path: Path to the platform directory
        metafile: Optional[str]: Name of the platform metadata file
        makefile: Optional[str]: Name of the platform makefile

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
            kind=ModuleKind.PLATFORM,
            metafile=metafile,
            makefile=makefile,
        )
        self.validity = self._resolve_validity()
        self.metabase = self._resolve_metabase()
        self.platform = self._resolve_platform()
        self.account = self._resolve_account()
        self.region = self._resolve_region()
        self.alias = self._resolve_alias()
        self.code = self._resolve_code()

    def _resolve_validity(
        self,
    ) -> bool:
        if not self.meta:
            return False
        if not isinstance(self.meta, dict):
            return False
        if not self.meta.get("platform"):
            return False
        return True

    def _resolve_metabase(
        self,
    ) -> Optional[dict]:
        return self.meta.get("platform", {})

    def _resolve_platform(
        self,
    ) -> Optional[str]:
        return self.metabase.get("name")

    def _resolve_account(
        self,
    ) -> Optional[str]:
        return self.metabase.get("account")

    def _resolve_region(
        self,
    ) -> Optional[str]:
        return self.metabase.get("region")

    def _resolve_alias(
        self,
    ) -> Optional[str]:
        return self.metabase.get("alias")

    def _resolve_code(
        self,
    ) -> Optional[str]:
        return self.metabase.get("code")

    def get_name(self) -> Optional[str]:
        return self.platform

    def get_account(self) -> Optional[str]:
        return self.account

    def get_region(self) -> Optional[str]:
        return self.region

    def get_alias(self) -> Optional[str]:
        return self.alias

    def get_code(self) -> Optional[str]:
        return self.code
