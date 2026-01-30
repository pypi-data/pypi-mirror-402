from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from sqlalchemy.engine import make_url

from .crypto import coerce_key_to_bytes

Mode = Literal["development", "testing", "production"]

@dataclass(frozen=True, slots=True)
class TenantsConfig:
    tenants_file: Path
    mode: Mode = "development"
    app_name_prefix: str = "fastapi"
    async_database_uri: str = "postgresql+psycopg://@host.docker.internal:6432/postgres"
    echo_sql: bool = False
    pool_size: int = 10
    tenant_header: str = "X-Tenant"
    default_tenant: str = "istanze"
    allowed_tenants_csv: str = ""
    strict_whitelist: bool = False

    def drivername(self) -> str:
        return make_url(self.async_database_uri).drivername


@dataclass(frozen=True, slots=True)
class CryptoConfig:
    encrypt_key: str | bytes

    @property
    def key_bytes(self) -> bytes:
        return coerce_key_to_bytes(self.encrypt_key)
