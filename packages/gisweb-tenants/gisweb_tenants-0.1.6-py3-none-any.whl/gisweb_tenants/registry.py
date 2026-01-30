from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

import hashlib
import yaml
from sqlalchemy.engine import make_url, URL

from .crypto import AeadBox, decrypt_field, coerce_key_to_bytes


# ---------------------------------------------------------------------
#  CACHE SNAPSHOT: version → (entries, aead_key)
# ---------------------------------------------------------------------

_REG_SNAPSHOTS: Dict[int, tuple[dict[str, "TenantRecord"], Optional[bytes]]] = {}
_MAX_SNAPSHOTS = 8


# ---------------------------------------------------------------------
#  Funzione LRU per decodificare triplet (dbname/user/password)
# ---------------------------------------------------------------------

@lru_cache(maxsize=512)
def _resolve_triplet_cached(version: int, tenant: str) -> Tuple[str, str, str]:
    entries, aead_key = _REG_SNAPSHOTS[version]
    tenant = tenant.strip().lower()

    rec = entries.get(tenant)
    if rec is None:
        raise KeyError(f"Tenant '{tenant}' non trovato")

    cfg = rec.config or {}

    db_name = cfg.get("db_name") or tenant
    db_user = cfg.get("db_user")
    db_password = cfg.get("db_password")

    # decrypt se cifrato
    if isinstance(db_user, dict) and db_user.get("$enc") == "aesgcm":
        if not aead_key:
            raise RuntimeError("Credenziali cifrate ma manca chiave AEAD")
        box = AeadBox(aead_key)
        db_user = decrypt_field(db_user, box, aad=f"{tenant}|db|user".encode())

    if isinstance(db_password, dict) and db_password.get("$enc") == "aesgcm":
        if not aead_key:
            raise RuntimeError("Credenziali cifrate ma manca chiave AEAD")
        box = AeadBox(aead_key)
        db_password = decrypt_field(db_password, box, aad=f"{tenant}|db|password".encode())

    if not db_user or not db_password:
        raise RuntimeError(f"Credenziali DB mancanti per tenant '{tenant}'")

    return db_name, db_user, db_password

# ---------------------------------------------------------------------
#  Funzione LRU per decodificare creenziali pagopa (tenant/pagopa/user)
# ---------------------------------------------------------------------
@lru_cache(maxsize=512)
def _resolve_pagopa_cached(version: int, tenant: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
    entries, aead_key = _REG_SNAPSHOTS[version]
    tenant = tenant.strip().lower()

    rec = entries.get(tenant)
    if rec is None:
        raise KeyError(f"Tenant '{tenant}' non trovato")

    cfg = rec.config or {}

    user = cfg.get("pagopa_user")
    pwd = cfg.get("pagopa_password")
    printpwd = cfg.get("pagopa_print_password")

    def maybe_decrypt(val, aad_suffix):
        if isinstance(val, dict) and val.get("$enc") == "aesgcm":
            if not aead_key:
                raise RuntimeError("Credenziali PagoPA cifrate ma manca chiave AEAD")
            box = AeadBox(aead_key)
            return decrypt_field(val, box, aad=f"{tenant}|{aad_suffix}".encode())
        return val

    user = maybe_decrypt(user, "pagopa|user")
    pwd = maybe_decrypt(pwd, "pagopa|password")
    printpwd = maybe_decrypt(printpwd, "pagopa|printpwd")

    return user or None, pwd or None, printpwd or None


# ---------------------------------------------------------------------
#  MODELLO SINGOLO TENANT
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class TenantRecord:
    name: str
    config: Dict[str, Any]


# ---------------------------------------------------------------------
#  REGISTRY PRINCIPALE
# ---------------------------------------------------------------------

class TenantsRegistry:
    """
    Registry dei tenant con snapshot caching.

    - Con `path=...` il registry si ricarica se cambia il mtime del file YAML.
    - Con `text=...` il registry si ricarica se cambia l’hash(text + key).
    """

    # -----------------------
    #  Costruttori
    # -----------------------

    def __init__(
        self,
        *,
        text: Optional[str] = None,
        path: Optional[Path] = None,
        aead_key: Optional[str | bytes] = None,
    ):
        if not text and not path:
            raise ValueError("Serve 'text' YAML oppure 'path' al file del registry")

        self._text = text
        self._path = Path(path) if path else None
        self._aead_key = coerce_key_to_bytes(aead_key) if aead_key else None
        self._version: Optional[int] = None

        self._ensure_loaded()

    @classmethod
    def from_file(cls, path: str | Path, *, aead_key: str | bytes | None = None):
        return cls(path=Path(path), aead_key=aead_key)

    @classmethod
    def from_text(cls, text: str, *, aead_key: str | bytes | None = None):
        return cls(text=text, aead_key=aead_key)

    # -----------------------
    #  API pubblico
    # -----------------------

    def exists(self, tenant: str) -> bool:
        self._ensure_loaded()
        tenant = tenant.strip().lower()
        entries, _ = _REG_SNAPSHOTS[self._version]  # type: ignore[arg-type]
        return tenant in entries

    def get(self, tenant: str) -> TenantRecord:
        self._ensure_loaded()
        tenant = tenant.strip().lower()
        entries, _ = _REG_SNAPSHOTS[self._version]  # type: ignore[arg-type]
        rec = entries.get(tenant)
        if not rec:
            raise KeyError(f"Tenant '{tenant}' non trovato")
        return rec
    
    def resolve_pagopa(self, tenant: str):
        self._ensure_loaded()
        return _resolve_pagopa_cached(self._version, tenant.strip().lower())

    def resolve_triplet(self, tenant: str) -> Tuple[str, str, str]:
        self._ensure_loaded()
        return _resolve_triplet_cached(self._version, tenant.strip().lower())  # type: ignore[arg-type]

    def build_dsn(self, base_dsn: str, tenant: str) -> URL:
        """
        Costruisce DSN specifico del tenant basandosi sul DSN base.
        """
        db_name, db_user, db_password = self.resolve_triplet(tenant)
        base: URL = make_url(base_dsn)
        #db_name="ddddddddd"  prova errore su connessione
        return base.set(database=db_name, username=db_user, password=db_password)

    @property
    def names(self) -> list[str]:
        self._ensure_loaded()
        entries, _ = _REG_SNAPSHOTS[self._version]  # type: ignore[arg-type]
        return list(entries.keys())

    def invalidate(self) -> None:
        """
        Forza il ricaricamento del registry alla prossima richiesta.
        """
        self._version = None

    # -----------------------
    #  PRIVATE
    # -----------------------

    def _ensure_loaded(self) -> None:
        """
        Determina se bisogna ricaricare lo snapshot:
        - file: version = mtime
        - testo: version = hash(text + key)
        """
        # Fonte: file
        if self._path:
            try:
                mtime = int(self._path.stat().st_mtime)
            except FileNotFoundError:
                raise RuntimeError(f"Registry file non trovato: {self._path}")

            if self._version != mtime:
                text = self._path.read_text(encoding="utf-8")
                self._load_snapshot(text, version=mtime)
                self._version = mtime
            return

        # Fonte: testo
        text = self._text or ""
        h = hashlib.sha1()
        h.update(text.encode("utf-8"))
        if self._aead_key:
            h.update(self._aead_key)

        ver = int.from_bytes(h.digest()[:4], "big")

        if self._version != ver:
            self._load_snapshot(text, version=ver)
            self._version = ver

    def _load_snapshot(self, yaml_text: str, *, version: int) -> None:
        """
        Carica e salva lo snapshot (entries + aead_key) per una data versione.
        """
        data = yaml.safe_load(yaml_text) or {}
        tenants = data.get("tenants") or {}

        entries: dict[str, TenantRecord] = {
            str(name).strip().lower(): TenantRecord(
                name=str(name).strip().lower(),
                config=cfg or {},
            )
            for name, cfg in tenants.items()
        }

        _REG_SNAPSHOTS[version] = (entries, self._aead_key)

        # tieni massimo N snapshot
        while len(_REG_SNAPSHOTS) > _MAX_SNAPSHOTS:
            _REG_SNAPSHOTS.pop(next(iter(_REG_SNAPSHOTS)))
