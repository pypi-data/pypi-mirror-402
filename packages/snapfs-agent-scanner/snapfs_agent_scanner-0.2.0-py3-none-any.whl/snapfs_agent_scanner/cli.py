#!/usr/bin/env python3

import argparse
import asyncio
from typing import Tuple
from urllib.parse import urlparse

from . import __prog__, __version__
from .agent import ws_loop
from .config import settings


def _derive_gateway_urls(gateway: str) -> Tuple[str, str]:
    """
    Accept gateway as:
      - http://host[:port] or https://host[:port]
      - ws://host[:port] or wss://host[:port]

    Returns: (gateway_http, gateway_ws)
    """
    u = urlparse(gateway)

    if not u.scheme or not u.netloc:
        raise ValueError(f"Invalid --gateway URL: {gateway!r}")

    if u.scheme in ("http", "https"):
        gateway_http = f"{u.scheme}://{u.netloc}"
        ws_scheme = "wss" if u.scheme == "https" else "ws"
        gateway_ws = f"{ws_scheme}://{u.netloc}"
        return gateway_http, gateway_ws

    if u.scheme in ("ws", "wss"):
        gateway_ws = f"{u.scheme}://{u.netloc}"
        http_scheme = "https" if u.scheme == "wss" else "http"
        gateway_http = f"{http_scheme}://{u.netloc}"
        return gateway_http, gateway_ws

    raise ValueError(f"Unsupported --gateway scheme: {u.scheme!r}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog=__prog__,
        description="SnapFS scanner agent (WebSocket listener).",
    )

    p.add_argument(
        "--version",
        action="version",
        version=f"{__prog__} {__version__}",
        help="Show version and exit.",
    )

    # Convenience: a single gateway URL
    p.add_argument(
        "--gateway",
        default=None,
        help="Gateway base URL",
    )

    # Allow explicit overrides
    p.add_argument(
        "--gateway-ws",
        default=settings.gateway_ws,
        help=f"Gateway WS base URL (default: {settings.gateway_ws})",
    )
    p.add_argument(
        "--ws-path",
        default=settings.ws_path,
        help=f"Gateway WS control path (default: {settings.ws_path})",
    )
    p.add_argument(
        "--agent-id",
        default=settings.agent_id,
        help=f"Agent ID (default: {settings.agent_id})",
    )
    p.add_argument(
        "--scan-root",
        default=settings.scan_root,
        help=f"Default scan root (default: {settings.scan_root})",
    )

    return p


def main() -> None:
    args = build_parser().parse_args()

    gateway_ws = args.gateway_ws

    # If --gateway provided, derive ws/http and use derived ws.
    if args.gateway:
        try:
            _, gateway_ws = _derive_gateway_urls(args.gateway)
        except ValueError as e:
            raise SystemExit(f"[ERR] {e}")

    try:
        asyncio.run(
            ws_loop(
                gateway_ws=gateway_ws,
                ws_path=args.ws_path,
                agent_id=args.agent_id,
                scan_root=args.scan_root,
            )
        )
    except KeyboardInterrupt:
        raise SystemExit(0)


if __name__ == "__main__":
    main()
