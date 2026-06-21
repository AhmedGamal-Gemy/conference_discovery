"""
Service health checks for the conference discovery pipeline.

Checks every external dependency on startup and before pipeline runs:
- Scrapling MCP (port 8017, SSE-based)
- LiteLLM proxy (port 4000, HTTP)
- PostgreSQL (port 5432, via Docker network)
- Exa API key presence
- FreeTheAi API key presence

Returns structured HealthReport with per-service UP/DOWN status + latency.
"""

import asyncio
import json
import logging
import os
import socket
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class ServiceHealth:
    name: str
    status: str  # "UP" | "DOWN" | "UNKNOWN"
    latency_ms: float = 0.0
    detail: str = ""

    def ok(self) -> bool:
        return self.status == "UP"

    def __bool__(self) -> bool:
        return self.ok()


@dataclass
class HealthReport:
    services: list[ServiceHealth] = field(default_factory=list)
    all_up: bool = True

    def add(self, service: ServiceHealth) -> None:
        self.services.append(service)
        if not service.ok():
            self.all_up = False

    def summary(self) -> str:
        parts = []
        for s in self.services:
            icon = "[OK]" if s.ok() else "[DOWN]" if s.status == "DOWN" else "[?]"
            parts.append(f"{icon} {s.name}={s.status} ({s.latency_ms:.0f}ms)")
            
        return " | ".join(parts)

    def log(self, level: int = logging.INFO) -> None:
        for s in self.services:
            if s.ok():
                logger.log(level, "HEALTH  %s UP (%dms)  %s", s.name, s.latency_ms, s.detail)
            elif s.status == "DOWN":
                logger.log(level, "HEALTH  %s DOWN (%dms)  %s", s.name, s.latency_ms, s.detail)
            else:
                logger.log(level, "HEALTH  %s %s (%dms)  %s", s.name, s.status, s.latency_ms, s.detail)


async def check_scrapling_mcp(
    url: str = "http://localhost:8017/mcp",
    timeout: float = 5.0,
) -> ServiceHealth:
    """Check if the Scrapling MCP server is reachable.

    Sends a JSON-RPC ping. A 400 response is expected because the MCP
    protocol requires an ``initialize`` handshake first — any HTTP
    response (even 400) proves the server is running and accepting
    connections. Only connection-refused or timeout means DOWN.
    """
    name = "scrapling-mcp"
    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                url,
                headers={"Accept": "application/json, text/event-stream"},
                json={"jsonrpc": "2.0", "id": 1, "method": "ping"},
            )
        latency = (time.time() - t0) * 1000
        # Any HTTP response means the server is alive.
        # 400 is expected (no initialize handshake); 200 means ping worked.
        if resp.status_code < 500:
            return ServiceHealth(
                name=name, status="UP", latency_ms=latency,
                detail=f"HTTP {resp.status_code} - {url}",
            )
        return ServiceHealth(
            name=name, status="DOWN", latency_ms=latency,
            detail=f"HTTP {resp.status_code} - {url}",
        )
    except httpx.ConnectError:
        latency = (time.time() - t0) * 1000
        return ServiceHealth(
            name=name, status="DOWN", latency_ms=latency,
            detail=f"Connection refused - {url}",
        )
    except httpx.TimeoutException:
        latency = (time.time() - t0) * 1000
        return ServiceHealth(
            name=name, status="DOWN", latency_ms=latency,
            detail=f"Timeout ({timeout}s) - {url}",
        )
    except Exception as exc:
        latency = (time.time() - t0) * 1000
        return ServiceHealth(
            name=name, status="UNKNOWN", latency_ms=latency,
            detail=f"{type(exc).__name__}: {exc}",
        )


async def check_litellm_proxy(
    url: str = "http://localhost:4000/",
    timeout: float = 5.0,
) -> ServiceHealth:
    """Check if the LiteLLM proxy is reachable."""
    name = "litellm-proxy"
    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url)
        latency = (time.time() - t0) * 1000
        if resp.status_code < 500:
            return ServiceHealth(
                name=name, status="UP", latency_ms=latency,
                detail=f"HTTP {resp.status_code} - {url}",
            )
        return ServiceHealth(
            name=name, status="DOWN", latency_ms=latency,
            detail=f"HTTP {resp.status_code} - {url}",
        )
    except httpx.ConnectError:
        latency = (time.time() - t0) * 1000
        return ServiceHealth(
            name=name, status="DOWN", latency_ms=latency,
            detail=f"Connection refused - {url}",
        )
    except httpx.TimeoutException:
        latency = (time.time() - t0) * 1000
        return ServiceHealth(
            name=name, status="DOWN", latency_ms=latency,
            detail=f"Timeout ({timeout}s) - {url}",
        )
    except Exception as exc:
        latency = (time.time() - t0) * 1000
        return ServiceHealth(
            name=name, status="UNKNOWN", latency_ms=latency,
            detail=f"{type(exc).__name__}: {exc}",
        )


async def check_postgres(
    host: str = "localhost",
    port: int = 5432,
    timeout: float = 3.0,
) -> ServiceHealth:
    """Check if PostgreSQL port is open (TCP connect)."""
    name = "postgresql"
    t0 = time.time()
    try:
        loop = asyncio.get_event_loop()
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout,
        )
        writer.close()
        await writer.wait_closed()
        latency = (time.time() - t0) * 1000
        return ServiceHealth(
            name=name, status="UP", latency_ms=latency,
            detail=f"TCP connected - {host}:{port}",
        )
    except (ConnectionRefusedError, OSError):
        latency = (time.time() - t0) * 1000
        return ServiceHealth(
            name=name, status="DOWN", latency_ms=latency,
            detail=f"Connection refused - {host}:{port}",
        )
    except asyncio.TimeoutError:
        latency = (time.time() - t0) * 1000
        return ServiceHealth(
            name=name, status="DOWN", latency_ms=latency,
            detail=f"Timeout ({timeout}s) - {host}:{port}",
        )
    except Exception as exc:
        latency = (time.time() - t0) * 1000
        return ServiceHealth(
            name=name, status="UNKNOWN", latency_ms=latency,
            detail=f"{type(exc).__name__}: {exc}",
        )


def check_env_var(name: str, label: Optional[str] = None) -> ServiceHealth:
    """Check if a required environment variable is set."""
    t0 = time.time()
    display = label or name
    value = os.environ.get(name)
    latency = (time.time() - t0) * 1000
    if value:
        masked = value[:6] + "..." if len(value) > 8 else "***"
        return ServiceHealth(
            name=display, status="UP", latency_ms=latency,
            detail=f"Found ({masked})",
        )
    return ServiceHealth(
        name=display, status="DOWN", latency_ms=latency,
        detail=f"Missing env var: {name}",
    )


async def run_all_checks(
    scrapling_url: str = "http://localhost:8017/mcp",
    proxy_url: str = "http://localhost:4000/",
) -> HealthReport:
    """Run all service health checks in parallel and return a report."""
    t0 = time.time()
    report = HealthReport()

    # Run checks in parallel
    scrapling, proxy, pg = await asyncio.gather(
        check_scrapling_mcp(url=scrapling_url),
        check_litellm_proxy(url=proxy_url),
        check_postgres(),
    )

    # Env var checks are synchronous - run after
    exa_api = check_env_var("EXA_API_KEY", "exa-api-key")
    freetheai_api = check_env_var("FREETHEAI_API_KEY", "freetheai-api-key")

    report.add(scrapling)
    report.add(proxy)
    report.add(pg)
    report.add(exa_api)
    report.add(freetheai_api)

    logger.info(
        "HEALTH  All checks complete - %d UP, %d DOWN (total %.0fms)  %s",
        sum(1 for s in report.services if s.ok()),
        sum(1 for s in report.services if s.status == "DOWN"),
        (time.time() - t0) * 1000,
        report.summary(),
    )
    return report


def log_service_or_skip(report: HealthReport, required: set[str]) -> bool:
    """Log health report and return True if all required services are UP.

    Logs warnings for non-required services that are DOWN.
    """
    all_ok = True
    for s in report.services:
        if not s.ok():
            if s.name in required:
                logger.error("HEALTH [FAIL] Required service DOWN: %s - %s", s.name, s.detail)
                all_ok = False
            else:
                logger.warning("HEALTH [WARN] Non-required service DOWN: %s - %s", s.name, s.detail)
    return all_ok
