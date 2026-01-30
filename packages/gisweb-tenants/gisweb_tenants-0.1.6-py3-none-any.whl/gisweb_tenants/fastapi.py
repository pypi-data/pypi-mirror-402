# gisweb_tenants/fastapi.py

from __future__ import annotations
from contextlib import asynccontextmanager
from typing import AsyncIterator, Mapping

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import DBAPIError, OperationalError, StatementError

import psycopg

from .config import TenantsConfig
from .registry import TenantsRegistry
from .db import tenant_session, dispose_all_engines


# -------------------------------------------------------------------
#  Risoluzione del tenant (già esistente)
# -------------------------------------------------------------------

def resolve_tenant_name(config: TenantsConfig, registry: TenantsRegistry, headers: Mapping[str, str]) -> str:
    tenant = (headers.get(config.tenant_header) or config.default_tenant).strip().lower()
    if not tenant:
        tenant = config.default_tenant

    # Whitelist
    if config.allowed_tenants_csv:
        allowed = {x.strip().lower() for x in config.allowed_tenants_csv.split(",") if x.strip()}
        if config.strict_whitelist and tenant not in allowed:
            raise HTTPException(status_code=403, detail="Tenant non consentito")

    # Check registry
    if not registry.exists(tenant):
        raise HTTPException(status_code=404, detail=f"Tenant '{tenant}' non trovato")

    return tenant


# -------------------------------------------------------------------
#  Dependency per ottenere una sessione tenant-safe
# -------------------------------------------------------------------

def make_tenant_session_dep(config: TenantsConfig, registry: TenantsRegistry):
    """
    Restituisce una dipendenza FastAPI:
    async def dep(request) -> AsyncSession
    con gestione integrata degli errori DB.
    """

    @asynccontextmanager
    async def _dep(request: Request) -> AsyncIterator[AsyncSession]:
        tenant = resolve_tenant_name(config, registry, request.headers)

        try:
            async with tenant_session(config, tenant, registry) as session:
                yield session

        except psycopg.OperationalError:
            raise HTTPException(status_code=503, detail="Database non disponibile")

        except psycopg.InterfaceError:
            raise HTTPException(status_code=503, detail="Errore di connessione al database")

        except (OperationalError, DBAPIError, StatementError):
            raise HTTPException(status_code=503, detail="Errore nel database")

    return _dep


# -------------------------------------------------------------------
#  Middleware globale pronto da montare
# -------------------------------------------------------------------

async def database_error_middleware(request: Request, call_next):
    """
    Middleware pronto all'uso che uniforma gli errori DB provenienti
    da qualsiasi punto dell'applicazione.
    Utile per casi NON coperti dalla dependency (stream, background task, ecc.).
    """
    try:
        return await call_next(request)

    except psycopg.OperationalError:
        return JSONResponse(status_code=503, content={"detail": "Database non disponibile"})

    except psycopg.InterfaceError:
        return JSONResponse(status_code=503, content={"detail": "Errore di connessione al database"})

    except (OperationalError, DBAPIError, StatementError):
        return JSONResponse(status_code=503, content={"detail": "Errore nel database"})


# -------------------------------------------------------------------
#  Shutdown per pulizia engines
# -------------------------------------------------------------------

async def shutdown_tenants():
    await dispose_all_engines()
