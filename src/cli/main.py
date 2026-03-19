"""
CLI entry point — assembles all subcommand parsers and dispatches to handlers.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from importlib import import_module
from typing import Any, Callable, Coroutine

# Import command modules by explicit dotted name to avoid shadowing when
# a module exports a function with the same local name (e.g. cmd_main.cmd_main).
_cmd_main_mod = import_module("src.cli.cmd_main")
_cmd_orders_mod = import_module("src.cli.cmd_orders")
_cmd_module_mod = import_module("src.cli.cmd_module")
_cmd_quote_mod = import_module("src.cli.cmd_quote")


# ---------------------------------------------------------------------------
# Parser builder
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="xianyu-cli",
        description="闲鱼自动化工具 CLI",
    )
    sub = parser.add_subparsers(dest="command", help="可用命令")

    _cmd_main_mod.add_parser(sub)
    _cmd_orders_mod.add_parser(sub)
    _cmd_module_mod.add_parser(sub)
    _cmd_quote_mod.add_parser(sub)

    return parser


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def _get_cmd(name: str) -> Callable[..., Coroutine[Any, Any, None]]:
    """Look up a command function from src.cli at call time.

    This ensures that tests patching ``src.cli.cmd_*`` always see the patched
    version, even when the patch is applied after this module is loaded.
    """
    import src as _src_mod

    return getattr(_src_mod.cli, name)


def main() -> None:
    # Look up build_parser from src.cli at call time so that tests patching
    # src.cli.build_parser always see the correct (possibly-patched) version.
    import src as _src_mod

    parser = _src_mod.cli.build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Look up each command dynamically so that monkeypatched src.cli.cmd_* functions
    # (patched after module load) are always picked up correctly.
    dispatch: dict[str, Callable[..., Coroutine[Any, Any, None]]] = {
        "publish": _get_cmd("cmd_publish"),
        "polish": _get_cmd("cmd_polish"),
        "price": _get_cmd("cmd_price"),
        "delist": _get_cmd("cmd_delist"),
        "relist": _get_cmd("cmd_relist"),
        "analytics": _get_cmd("cmd_analytics"),
        "accounts": _get_cmd("cmd_accounts"),
        "messages": _get_cmd("cmd_messages"),
        "orders": _get_cmd("cmd_orders"),
        "compliance": _get_cmd("cmd_compliance"),
        "ai": _get_cmd("cmd_ai"),
        "doctor": _get_cmd("cmd_doctor"),
        "automation": _get_cmd("cmd_automation"),
        "module": _get_cmd("cmd_module"),
        "quote": _get_cmd("cmd_quote"),
        "growth": _get_cmd("cmd_growth"),
        "virtual-goods": _get_cmd("cmd_virtual_goods"),
    }

    handler = dispatch.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(1)

    try:
        asyncio.run(handler(args))
    except KeyboardInterrupt:
        pass
    except Exception as e:
        # Dynamic lookup so tests patching src.cli._json_out always intercept.
        import src as _src_mod

        _src_mod.cli._json_out({"error": str(e)})
        sys.exit(1)


if __name__ == "__main__":
    main()
