"""
Building OS REST API クライアント (IF-BUILDING-001)
参照: gutp-bim/building_OS_test

エンドポイント:
  GET /buildings                           — ビル一覧
  GET /floors?buildingDtId={dtId}          — フロア一覧
  GET /spaces                              — スペース一覧
  GET /device-details?buildingDtId={dtId}  — デバイス詳細（フロア・スペース文脈付き）

認証:
  Authorization: Bearer {token}
  BUILDING_OS_TOKEN 環境変数または BuildingOSClient(token=...) で指定する。
  Azure AD JWT (本番) / TestAuthenticationHandler (開発) 両対応。
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from ..schemas.building import Building, DeviceDetail, Floor, Space


class BuildingOSClient:
    """Building OS REST API への非同期クライアント。

    使用例:
        async with BuildingOSClient() as client:
            buildings = await client.get_buildings()
            details = await client.get_device_details(buildings[0].dt_id)
    """

    def __init__(
        self,
        base_url: str | None = None,
        token: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._base_url = (base_url or os.getenv("BUILDING_OS_URL", "http://localhost:5000")).rstrip("/")
        self._token = token or os.getenv("BUILDING_OS_TOKEN", "")
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "BuildingOSClient":
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={"Authorization": f"Bearer {self._token}"},
            timeout=self._timeout,
        )
        return self

    async def __aexit__(self, *_: Any) -> None:
        if self._client:
            await self._client.aclose()

    def _c(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("BuildingOSClient must be used as async context manager")
        return self._client

    async def get_buildings(self) -> list[Building]:
        """GET /buildings — ビル一覧を取得する。"""
        resp = self._c().get("/buildings")
        resp = await resp
        resp.raise_for_status()
        return [Building.model_validate(item) for item in resp.json()]

    async def get_floors(self, building_dt_id: str) -> list[Floor]:
        """GET /floors?buildingDtId={dtId} — フロア一覧を取得する。"""
        resp = await self._c().get("/floors", params={"buildingDtId": building_dt_id})
        resp.raise_for_status()
        return [Floor.model_validate(item) for item in resp.json()]

    async def get_spaces(self) -> list[Space]:
        """GET /spaces — スペース一覧を取得する。"""
        resp = await self._c().get("/spaces")
        resp.raise_for_status()
        return [Space.model_validate(item) for item in resp.json()]

    async def get_device_details(self, building_dt_id: str) -> list[DeviceDetail]:
        """GET /device-details?buildingDtId={dtId} — デバイス詳細（フロア・スペース文脈付き）を取得する。"""
        resp = await self._c().get("/device-details", params={"buildingDtId": building_dt_id})
        resp.raise_for_status()
        return [DeviceDetail.model_validate(item) for item in resp.json()]
