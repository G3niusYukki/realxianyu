"""
Quote / cost-table commands.
"""

from __future__ import annotations

import argparse

# _json_out is looked up dynamically inside cmd_quote (via a local import from src.cli)
# so that tests patching src.cli._json_out always intercept the correct binding.


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------


async def cmd_quote(args: argparse.Namespace) -> None:
    from src.cli import _json_out
    from src.core.config import get_config
    from src.modules.quote import CostTableRepository, QuoteSetupService

    action = args.action
    config = get_config()
    quote_cfg = config.get_section("quote", {})

    if action == "health":
        repo = CostTableRepository(
            table_dir=quote_cfg.get("cost_table_dir", "data/quote_costs"),
            include_patterns=quote_cfg.get("cost_table_patterns", ["*.xlsx", "*.csv"]),
        )
        stats = repo.get_stats(max_files=30)
        _json_out(
            {
                "mode": quote_cfg.get("mode", "rule_only"),
                "cost_table": stats,
                "api_cost_ready": bool(quote_cfg.get("cost_api_url", "")),
            }
        )
        return

    if action == "candidates":
        if not args.origin_city or not args.destination_city:
            _json_out({"error": "Specify --origin-city and --destination-city"})
            return
        repo = CostTableRepository(
            table_dir=quote_cfg.get("cost_table_dir", "data/quote_costs"),
            include_patterns=quote_cfg.get("cost_table_patterns", ["*.xlsx", "*.csv"]),
        )
        records = repo.find_candidates(
            origin=args.origin_city,
            destination=args.destination_city,
            courier=args.courier,
            limit=max(args.limit or 20, 1),
        )
        _json_out(
            {
                "total": len(records),
                "origin_city": args.origin_city,
                "destination_city": args.destination_city,
                "courier": args.courier or "",
                "candidates": [
                    {
                        "courier": r.courier,
                        "origin": r.origin,
                        "destination": r.destination,
                        "first_cost": r.first_cost,
                        "extra_cost": r.extra_cost,
                    }
                    for r in records
                ],
            }
        )
        return

    if action == "setup":
        setup_service = QuoteSetupService(config_path=args.config_path or "config/config.yaml")
        patterns = []
        raw_patterns = str(args.cost_table_patterns or "*.xlsx,*.csv")
        for item in raw_patterns.split(","):
            text = item.strip()
            if text:
                patterns.append(text)

        result = setup_service.apply(
            mode=args.mode or "cost_table_plus_markup",
            origin_city=args.origin_city or "杭州",
            pricing_profile=args.pricing_profile or "normal",
            cost_table_dir=args.cost_table_dir or "data/quote_costs",
            cost_table_patterns=patterns,
            api_cost_url=args.cost_api_url or "",
            cost_api_key_env=args.cost_api_key_env or "QUOTE_COST_API_KEY",
        )
        _json_out(result)
        return

    _json_out({"error": f"Unknown quote action: {action}"})


# ---------------------------------------------------------------------------
# Argument parser registration
# ---------------------------------------------------------------------------


def add_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("quote", help="自动报价诊断与配置")
    p.add_argument("--action", required=True, choices=["health", "candidates", "setup"])
    p.add_argument("--origin-city", default=None, help="始发地城市")
    p.add_argument("--destination-city", default=None, help="目的地城市")
    p.add_argument("--courier", default=None, help="快递公司")
    p.add_argument("--limit", type=int, default=20, help="候选数量上限")
    p.add_argument("--mode", default=None, help="报价模式（setup）")
    p.add_argument("--pricing-profile", default="normal", help="加价档位 normal/member（setup）")
    p.add_argument("--cost-table-dir", default="data/quote_costs", help="成本价表目录（setup）")
    p.add_argument("--cost-table-patterns", default="*.xlsx,*.csv", help="成本表匹配规则（setup）")
    p.add_argument("--cost-api-url", default="", help="成本价接口 URL（setup）")
    p.add_argument("--cost-api-key-env", default="QUOTE_COST_API_KEY", help="成本接口 Key 环境变量名（setup）")
    p.add_argument("--config-path", default="config/config.yaml", help="配置文件路径（setup）")
