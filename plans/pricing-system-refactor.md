# 三层定价体系改造实施方案

> 本文档由 Cursor 规划，交由 Roo Code 实施。请严格按照文档执行。

## 一、背景

### 当前系统问题

1. `data/quote_costs/` 中的 xlsx 存的是闲鱼报价价格（非真实成本）
2. 加价配置（`markup_rules`）只有单层，每运力只有 `normal_first_add` / `member_first_add` / `normal_extra_add` / `member_extra_add` 四个字段，当前全为 0
3. 系统无法区分"成本"、"加价"、"让利"三个层次
4. 不支持大件物流（30kg 首重）和多服务类别

### 目标

建立三层定价体系，仿照商达人后台，按 8 个服务类别组织：

```
成本表(xlsx) + 加价表(config) = 小程序价
小程序价 - 让利表(config) = 闲鱼报价
```

### 三层定价公式（用户已确认）

```
小程序价首重 = 成本首重 + 首重加价
小程序价续重 = 成本续重 + 续重加价
闲鱼报价首重 = 小程序价首重 - 首重让利    （只有首重让利，续重不让利）
闲鱼报价续重 = 小程序价续重

闲鱼最终价 = 闲鱼报价首重 + max(0, 计费重 - base_weight) × 闲鱼报价续重
```

**用户举例**（快递 1kg 首重）:
- 成本: 首重4, 续重2
- 加价: 首重+0.9, 续重+0.5 → 小程序价: 首重4.9, 续重2.5
- 让利: 首重1.9 → 闲鱼价: 首重3.0, 续重2.5

**用户举例**（物流 30kg 首重）:
- 成本: 首重50, 续重1
- 加价: 首重+10, 续重+0.5 → 小程序价: 首重60, 续重1.5
- 让利: 首重5 → 闲鱼价: 首重55, 续重1.5

### 8 个服务类别

线上快递 / 线下快递 / 线上快运 / 线下快运 / 同城寄 / 电动车 / 分销 / 商家寄件

---

## 二、已完成的改动（Cursor 已做）

### 2.1 `src/modules/quote/cost_table.py` — COURIER_ALIASES 扩展

已添加：
- 多版本快递别名：`韵达特惠版`→`韵达`, `圆通特定版`→`圆通`, `中通1`/`中通2`→`中通`, `极兔1`/`极兔2`→`极兔`, `申通1`/`申通2`/`申通No1`/`申通No2`→`申通`, `菜鸟裹裹1`/`菜鸟裹裹2`→`菜鸟裹裹`
- 物流运力别名：`百世快运`, `壹米滴答`, `安能`/`安能物流`/`安能快运`→`安能`, `顺心捷达`, `中通快运`, `圆通快运`, `德邦快运`/`德邦物流`→`德邦快运`
- 新增 `FREIGHT_COURIERS` 集合：标识物流运力

### 2.2 `src/modules/quote/cost_table.py` — CostRecord 新增字段

```python
@dataclass
class CostRecord:
    courier: str
    origin: str
    destination: str
    first_cost: float
    extra_cost: float
    throw_ratio: float | None = None
    base_weight: float = 1.0        # 新增: 首重公斤数（快递=1, 物流=30）
    service_type: str = "express"    # 新增: "express" | "freight"
    source_file: str = ""
    source_sheet: str = ""
```

---

## 三、待实施内容

### Phase 1: 成本表加载兼容升级

**文件**: `src/modules/quote/cost_table.py`

#### 1.1 扩展 `_HEADER_ALIASES`（约 L190）

在现有 aliases 基础上添加：

```python
_HEADER_ALIASES = {
    "courier": {"快递公司", "物流公司", "承运商"},
    "origin": {"始发地", "寄件地", "发件地", "发货地", "始发城市", "揽收地", "始发省份", "始发省", "发件城市"},
    "destination": {"目的地", "收件地", "收件地址", "收件城市", "到达地", "目的省份", "目的城市", "到达城市"},
    "first_cost": {"首重", "首重1kg", "首重价", "首重价格", "首重1kg价"},
    "extra_cost": {"续重", "续重1kg", "续重价", "续重价格", "续重1kg价"},
    "throw_ratio": {"抛比", "抛重比", "材积比", "体积系数"},
}
```

注意：`_resolve_header_map` 中已有 `"首重" in cell` 的 fuzzy 匹配，所以 `首重(元)/kg`、`易达首重` 等变体无需显式添加。

#### 1.2 修改 `_rows_to_records`（约 L445-490）

**核心改动**：当表头缺少 `courier` 列时，从 `source_sheet` 推断运力名。

```python
def _rows_to_records(self, rows: list[list[str]], source_file: str, source_sheet: str) -> list[CostRecord]:
    if not rows:
        return []

    header_row_index = -1
    header_map: dict[str, int] = {}
    for idx, row in enumerate(rows):
        header_map = self._resolve_header_map(row)
        # 放宽要求: origin + destination + first_cost + extra_cost 即可
        required = {"origin", "destination", "first_cost", "extra_cost"}
        if required.issubset(set(header_map.keys())):
            header_row_index = idx
            break

    if header_row_index < 0:
        return []

    # 如果没有 courier 列，从 sheet 名推断
    has_courier_col = "courier" in header_map
    inferred_courier = ""
    if not has_courier_col:
        inferred_courier = normalize_courier_name(source_sheet)
        if not inferred_courier:
            return []

    records: list[CostRecord] = []
    for row in rows[header_row_index + 1:]:
        if has_courier_col:
            courier = self._cell_text(row, header_map.get("courier"))
        else:
            courier = inferred_courier
        origin = self._cell_text(row, header_map.get("origin"))
        destination = self._cell_text(row, header_map.get("destination"))
        first_cost = self._cell_float(row, header_map.get("first_cost"))
        extra_cost = self._cell_float(row, header_map.get("extra_cost"))
        throw_ratio = self._cell_float(row, header_map.get("throw_ratio"))

        if not courier or not origin or not destination:
            continue
        if first_cost is None or extra_cost is None:
            continue

        normalized_courier = normalize_courier_name(courier)
        is_freight = normalized_courier in FREIGHT_COURIERS

        records.append(
            CostRecord(
                courier=normalized_courier,
                origin=origin.strip(),
                destination=destination.strip(),
                first_cost=first_cost,
                extra_cost=extra_cost,
                throw_ratio=throw_ratio,
                base_weight=30.0 if is_freight else 1.0,
                service_type="freight" if is_freight else "express",
                source_file=source_file,
                source_sheet=source_sheet,
            )
        )
    return records
```

#### 1.3 验证

替换完后，运行以下 Python 验证新成本表能被正确加载：

```python
from src.modules.quote.cost_table import CostTableRepository
repo = CostTableRepository("data/quote_costs")
stats = repo.get_stats()
print(f"总记录数: {stats['total_records']}")
print(f"运力: {stats['unique_couriers']}")

# 测试大件运力表是否被加载
candidates = repo.find_candidates("北京", "浙江", courier="安能")
for c in candidates[:3]:
    print(f"  {c.courier} {c.origin}->{c.destination}: 首重{c.first_cost} 续重{c.extra_cost} base_weight={c.base_weight}")
```

---

### Phase 2: 三层定价配置模型

**文件**: `src/modules/quote/providers.py`, `config/config.yaml`

#### 2.1 新增配置结构

在 `config/config.yaml` 的 `quote:` 段中，新增（与旧 `markup_rules` 平行）：

```yaml
quote:
  # ... 现有字段 ...
  
  # 旧格式保留向后兼容（不删除）
  markup_rules:
    default:
      normal_first_add: 0.0
      member_first_add: 0.0
      normal_extra_add: 0.0
      member_extra_add: 0.0
  
  # 新格式: 按服务类别分组的加价表
  markup_categories:
    线上快递:
      default: { first_add: 0.0, extra_add: 0.0 }
    线上快运:
      default: { first_add: 0.0, extra_add: 0.0 }
    线下快递:
      default: { first_add: 0.0, extra_add: 0.0 }
    线下快运:
      default: { first_add: 0.0, extra_add: 0.0 }
    同城寄:
      default: { first_add: 0.0, extra_add: 0.0 }
    电动车:
      default: { first_add: 0.0, extra_add: 0.0 }
    分销:
      default: { first_add: 0.0, extra_add: 0.0 }
    商家寄件:
      default: { first_add: 0.0, extra_add: 0.0 }
  
  # 闲鱼让利表（仅首重让利，续重不让利）
  xianyu_discount:
    线上快递:
      default: { first_discount: 0.0 }
    线上快运:
      default: { first_discount: 0.0 }
    线下快递:
      default: { first_discount: 0.0 }
    线下快运:
      default: { first_discount: 0.0 }
    同城寄:
      default: { first_discount: 0.0 }
    电动车:
      default: { first_discount: 0.0 }
    分销:
      default: { first_discount: 0.0 }
    商家寄件:
      default: { first_discount: 0.0 }
```

#### 2.2 修改 `providers.py` 加价解析逻辑

**常量定义**（替换 `DEFAULT_MARKUP_RULE`）：

```python
SERVICE_CATEGORIES = [
    "线上快递", "线下快递", "线上快运", "线下快运",
    "同城寄", "电动车", "分销", "商家寄件",
]

DEFAULT_MARKUP_RULE: dict[str, float] = {
    "normal_first_add": 0.50,
    "member_first_add": 0.25,
    "normal_extra_add": 0.50,
    "member_extra_add": 0.30,
}
```

**新增函数**：

```python
def _normalize_category_markup(raw: dict[str, Any]) -> dict[str, dict[str, dict[str, float]]]:
    """解析分类加价配置。
    
    返回: { category: { courier: { "first_add": x, "extra_add": y } } }
    """
    result: dict[str, dict[str, dict[str, float]]] = {}
    if not isinstance(raw, dict):
        return result
    for category, couriers in raw.items():
        cat = str(category).strip()
        if not cat or not isinstance(couriers, dict):
            continue
        cat_rules: dict[str, dict[str, float]] = {}
        for courier_key, rule in couriers.items():
            key = str(courier_key).strip()
            if not key or not isinstance(rule, dict):
                continue
            cat_rules[key if key == "default" else normalize_courier_name(key)] = {
                "first_add": float(rule.get("first_add", 0.0)),
                "extra_add": float(rule.get("extra_add", 0.0)),
            }
        if "default" not in cat_rules:
            cat_rules["default"] = {"first_add": 0.0, "extra_add": 0.0}
        result[cat] = cat_rules
    return result


def _normalize_xianyu_discount(raw: dict[str, Any]) -> dict[str, dict[str, dict[str, float]]]:
    """解析闲鱼让利配置。
    
    返回: { category: { courier: { "first_discount": x } } }
    """
    result: dict[str, dict[str, dict[str, float]]] = {}
    if not isinstance(raw, dict):
        return result
    for category, couriers in raw.items():
        cat = str(category).strip()
        if not cat or not isinstance(couriers, dict):
            continue
        cat_rules: dict[str, dict[str, float]] = {}
        for courier_key, rule in couriers.items():
            key = str(courier_key).strip()
            if not key or not isinstance(rule, dict):
                continue
            cat_rules[key if key == "default" else normalize_courier_name(key)] = {
                "first_discount": float(rule.get("first_discount", 0.0)),
            }
        if "default" not in cat_rules:
            cat_rules["default"] = {"first_discount": 0.0}
        result[cat] = cat_rules
    return result


def _resolve_category_markup(
    rules: dict[str, dict[str, dict[str, float]]],
    category: str,
    courier: str,
) -> tuple[float, float]:
    """根据服务类别和运力查找加价值，返回 (first_add, extra_add)。"""
    cat_rules = rules.get(category, {})
    courier_rule = cat_rules.get(courier) or cat_rules.get("default") or {}
    return (
        float(courier_rule.get("first_add", 0.0)),
        float(courier_rule.get("extra_add", 0.0)),
    )


def _resolve_xianyu_discount_value(
    rules: dict[str, dict[str, dict[str, float]]],
    category: str,
    courier: str,
) -> float:
    """根据服务类别和运力查找首重让利值。"""
    cat_rules = rules.get(category, {})
    courier_rule = cat_rules.get(courier) or cat_rules.get("default") or {}
    return float(courier_rule.get("first_discount", 0.0))
```

#### 2.3 修改 `CostTableMarkupQuoteProvider`

**`__init__` 增加新参数**：

```python
def __init__(
    self,
    *,
    table_dir: str = "data/quote_costs",
    include_patterns: list[str] | None = None,
    markup_rules: dict[str, Any] | None = None,
    pricing_profile: str = "normal",
    volume_divisor_default: float | None = None,
    # 新增参数
    markup_categories: dict[str, Any] | None = None,
    xianyu_discount: dict[str, Any] | None = None,
):
    # ... 现有初始化 ...
    self.category_markup = _normalize_category_markup(markup_categories or {})
    self.xianyu_discount_rules = _normalize_xianyu_discount(xianyu_discount or {})
```

**`get_quote` 方法修改计价逻辑**（核心改动）：

```python
async def get_quote(self, request: QuoteRequest) -> QuoteResult:
    # ... 现有 candidates 查找逻辑不变 ...

    row = candidates[0]
    
    # 根据运力确定服务类别
    category = "线上快运" if row.service_type == "freight" else "线上快递"
    
    # 新的三层计价
    if self.category_markup:
        first_add, extra_add = _resolve_category_markup(
            self.category_markup, category, row.courier
        )
        first_discount = _resolve_xianyu_discount_value(
            self.xianyu_discount_rules, category, row.courier
        )
    else:
        # 向后兼容旧格式
        markup = _resolve_markup(self.markup_rules, row.courier)
        first_add, extra_add = _profile_markup(markup, self.pricing_profile)
        first_discount = 0.0

    actual_weight = max(0.0, float(request.weight))
    divisor = _first_positive(row.throw_ratio, self.volume_divisor_default)
    volume_weight = _derive_volume_weight_kg(
        volume_cm3=float(request.volume or 0.0),
        explicit_volume_weight=float(request.volume_weight or 0.0),
        divisor=divisor,
    )
    billing_weight = max(actual_weight, volume_weight)
    
    # 使用 base_weight 而非硬编码 1.0
    extra_weight = max(0.0, billing_weight - row.base_weight)
    
    # 三层计算
    mini_first = float(row.first_cost) + first_add
    mini_extra = float(row.extra_cost) + extra_add
    xianyu_first = mini_first - first_discount
    xianyu_extra = mini_extra  # 续重不让利
    
    extra_fee = extra_weight * xianyu_extra

    surcharges: dict[str, float] = {}
    if extra_fee > 0:
        surcharges["续重"] = round(extra_fee, 2)

    return QuoteResult(
        provider="cost_table_markup",
        base_fee=round(xianyu_first, 2),
        surcharges=surcharges,
        total_fee=round(xianyu_first + extra_fee, 2),
        eta_minutes=_eta_by_service_level(request.service_level),
        confidence=0.92,
        source_excel=row.source_file,
        matched_route=f"{row.origin}-{row.destination}",
        explain={
            "pricing_profile": self.pricing_profile,
            "matched_courier": row.courier,
            "matched_origin": row.origin,
            "matched_destination": row.destination,
            "cost_first": row.first_cost,
            "cost_extra": row.extra_cost,
            "base_weight": row.base_weight,
            "service_type": row.service_type,
            "markup_category": category,
            "first_add": first_add,
            "extra_add": extra_add,
            "first_discount": first_discount,
            "mini_program_first": round(mini_first, 2),
            "mini_program_extra": round(mini_extra, 2),
            "xianyu_first": round(xianyu_first, 2),
            "xianyu_extra": round(xianyu_extra, 2),
            "actual_weight_kg": round(actual_weight, 3),
            "billing_weight_kg": round(billing_weight, 3),
            "volume_cm3": round(float(request.volume or 0.0), 3),
            "volume_weight_kg": round(volume_weight, 3),
            "volume_divisor": divisor if divisor > 0 else None,
            "source_file": row.source_file,
            "source_sheet": row.source_sheet,
        },
    )
```

#### 2.4 修改 `engine.py` 传递新参数

`QuoteEngine.__init__` 中创建 `CostTableMarkupQuoteProvider` 时，增加传入：

```python
self.cost_table_provider = CostTableMarkupQuoteProvider(
    table_dir=str(cfg.get("cost_table_dir", "data/quote_costs")),
    include_patterns=cfg.get("cost_table_patterns", ["*.xlsx", "*.csv"]),
    markup_rules=cfg.get("markup_rules", {}),
    pricing_profile=str(cfg.get("pricing_profile", "normal")),
    volume_divisor_default=self.volume_divisor_default,
    markup_categories=cfg.get("markup_categories", {}),    # 新增
    xianyu_discount=cfg.get("xianyu_discount", {}),         # 新增
)
```

---

### Phase 3: 回复展示适配

**文件**: `src/modules/messages/service.py`

#### 3.1 `_compose_multi_courier_quote_reply` 方法

找到硬编码 `bw - 1.0` 的地方，改为从 `explain` 读取 `base_weight`：

```python
# 原代码（约 L376）:
extra_w = max(0.0, bw - 1.0)

# 改为:
base_w = float(exp.get("base_weight", 1.0))
extra_w = max(0.0, bw - base_w)
```

同样修改展示公式中的 "首重" 文案（如果 base_weight > 1，显示 "首重30kg" 而非 "首重"）：

```python
if base_w > 1:
    price_str += f"（首重{base_w:.0f}kg {float(result.base_fee):.2f} + 续重{extra_w:.1f}kg×{float(exp.get('xianyu_extra', 0)):.2f}）"
else:
    price_str += f"（首重{float(result.base_fee):.2f} + 续重{extra_w:.1f}kg×{float(exp.get('xianyu_extra', 0)):.2f}）"
```

#### 3.2 P0 Bug 修复

`_is_quote_request` 方法（约 L686），路由正则增加 `寄`：

```python
# 原:
r"[\u4e00-\u9fa5]{2,4}\s*(?:发(?![了的个件给过货到着]))\s*[\u4e00-\u9fa5]{2,4}"

# 改为:
r"[\u4e00-\u9fa5]{2,4}\s*(?:发(?![了的个件给过货到着])|寄(?![了的个件给过到着]))\s*[\u4e00-\u9fa5]{2,4}"
```

---

### Phase 4: Dashboard API 与 UI

#### 4.1 API 端点

**文件**: `src/dashboard/routes/quote.py`, `src/dashboard_server.py`

**新增端点**：

```python
@get("/api/get-pricing-config")
def handle_get_pricing_config(ctx: RouteContext) -> None:
    """返回三层定价完整配置。"""
    ctx.send_json(ctx.mimic_ops.get_pricing_config())

@post("/api/save-pricing-config")
def handle_save_pricing_config(ctx: RouteContext) -> None:
    """保存加价表 + 让利表。"""
    body = ctx.json_body()
    payload = ctx.mimic_ops.save_pricing_config(
        markup_categories=body.get("markup_categories"),
        xianyu_discount=body.get("xianyu_discount"),
    )
    ctx.send_json(payload, status=200 if payload.get("success") else 400)

@get("/api/get-cost-summary")
def handle_get_cost_summary(ctx: RouteContext) -> None:
    """返回成本表概览（只读）。"""
    ctx.send_json(ctx.mimic_ops.get_cost_summary())
```

**`MimicOps` 新增方法**（在 `src/dashboard_server.py`）：

```python
def get_pricing_config(self) -> dict[str, Any]:
    """读取 YAML 中的 markup_categories 和 xianyu_discount。"""
    setup = QuoteSetupService(config_path=str(self.config_path))
    data, _ = setup._load_yaml()
    quote_cfg = data.get("quote", {}) if isinstance(data, dict) else {}
    return {
        "success": True,
        "markup_categories": quote_cfg.get("markup_categories", {}),
        "xianyu_discount": quote_cfg.get("xianyu_discount", {}),
        "service_categories": [
            "线上快递", "线下快递", "线上快运", "线下快运",
            "同城寄", "电动车", "分销", "商家寄件",
        ],
        "updated_at": _now_iso(),
    }

def save_pricing_config(self, markup_categories: Any, xianyu_discount: Any) -> dict[str, Any]:
    """保存加价表和让利表到 YAML。"""
    setup = QuoteSetupService(config_path=str(self.config_path))
    data, existed = setup._load_yaml()
    quote_cfg = data.get("quote")
    if not isinstance(quote_cfg, dict):
        quote_cfg = {}
        data["quote"] = quote_cfg
    
    if isinstance(markup_categories, dict):
        quote_cfg["markup_categories"] = markup_categories
    if isinstance(xianyu_discount, dict):
        quote_cfg["xianyu_discount"] = xianyu_discount
    
    backup_path = setup._backup_existing_file() if existed else None
    setup._write_yaml(data)
    return {"success": True, "updated_at": _now_iso()}

def get_cost_summary(self) -> dict[str, Any]:
    """从成本表 xlsx 读取各运力概览数据（只读）。"""
    from src.modules.quote.cost_table import CostTableRepository
    repo = CostTableRepository("data/quote_costs")
    stats = repo.get_stats()
    
    # 按运力 + 路线聚合概览
    repo._reload_if_needed()
    courier_summary: dict[str, dict] = {}
    for record in repo._records:
        key = record.courier
        if key not in courier_summary:
            courier_summary[key] = {
                "courier": key,
                "service_type": record.service_type,
                "base_weight": record.base_weight,
                "route_count": 0,
                "first_cost_range": [float("inf"), 0],
                "extra_cost_range": [float("inf"), 0],
            }
        info = courier_summary[key]
        info["route_count"] += 1
        info["first_cost_range"][0] = min(info["first_cost_range"][0], record.first_cost)
        info["first_cost_range"][1] = max(info["first_cost_range"][1], record.first_cost)
        info["extra_cost_range"][0] = min(info["extra_cost_range"][0], record.extra_cost)
        info["extra_cost_range"][1] = max(info["extra_cost_range"][1], record.extra_cost)
    
    return {
        "success": True,
        "couriers": list(courier_summary.values()),
        "total_records": stats["total_records"],
        "total_files": stats["total_files"],
    }
```

保留旧端点 `get-markup-rules` / `save-markup-rules` 不删除，确保向后兼容。

#### 4.2 前端 UI

**文件**: `client/src/pages/products/ProductList.tsx`

将现有 `markup` tab 改造为三表管理：

**UI 结构**：

```
加价规则 (tab)
├── 第一层: 服务类别 tabs (线上快递 | 线下快递 | 线上快运 | ...)
│   ├── 成本表 (只读区域)
│   │   └── table: 运力 | 成本首重 | 成本续重 | base_weight | 路线数
│   ├── 加价表 (可编辑)
│   │   └── table: 运力 | 首重加价 | 续重加价 | 小程序首重价(自动算) | 小程序续重价(自动算)
│   └── 让利表 (可编辑)
│       └── table: 运力 | 首重让利 | 闲鱼首重价(自动算) | 闲鱼续重价(自动算)
└── 保存按钮
```

**关键要点**：
- "小程序首重价" = 成本首重的中间值 + 首重加价（计算列，只读）
- "闲鱼首重价" = 小程序首重价 - 首重让利（计算列，只读）
- 成本表数据来自 `GET /api/get-cost-summary`
- 加价表 + 让利表数据来自 `GET /api/get-pricing-config`
- 保存调用 `POST /api/save-pricing-config`
- 首重加价和续重加价允许任意值（包括负数，但一般不应为负）
- 首重让利只有一个值 `first_discount`，续重不让利
- `PRODUCT_TABS` 中的 `markup` tab 的 `visible` 条件去掉 `cat === 'express'` 限制，改为始终显示

---

### Phase 5: 多件报价（优先级较低，可后续实施）

参见之前的方案文档 `.cursor/plans/多件快递报价优化_b71daf0b.plan.md`，核心改动：

1. `_extract_multi_packages` — findall 提取多组重量/体积
2. `_generate_reply_with_quote` — 多件检测 → 多次报价 → 合并回复
3. `_compose_multi_package_reply` — 多件合并展示 + 合计最低价
4. `reply_engine.py` — `express_multi_pkg` 关键词补全

---

## 四、测试策略

1. **单元测试**：确保 `CostTableRepository` 能正确加载无 `courier` 列的 xlsx
2. **集成测试**：验证三层计价公式正确（成本+加价-让利=闲鱼价）
3. **回归测试**：旧格式 `markup_rules` 配置仍然工作
4. **手动测试**：Dashboard UI 能正确展示和编辑三表

关键测试用例：
- 快递（1kg 首重）：北京→浙江 圆通，5kg 件
- 物流（30kg 首重）：北京→浙江 安能，50kg 件
- 无加价配置时（全为 0），闲鱼报价 = 成本价（向后兼容）
- 配置加价+让利后，闲鱼报价 = 成本+加价-让利

---

## 五、小件（快递）与大件（快运）的核心区别

这是整个定价体系最关键的区分，来自商达人后台的实际结构。

### 5.1 两类服务对照

| 维度 | 小件（普通快递） | 大件（快运/物流） |
|------|-----------------|------------------|
| **商达人 tab** | 线上快递 / 线下快递 | 线上快运 / 线下快运 |
| **首重公斤数** | **1 kg** | **30 kg**（商达人后台标注"30件kg起"） |
| **运力举例** | 圆通、韵达、中通、申通、菜鸟裹裹、极兔、德邦、京东、邮政 | 百世快运、壹米滴答、安能、顺心捷达、中通快运、圆通快运、德邦快运、四合易运、星汉运营、万象、美地、省无忧运 |
| **成本表来源** | 易达云管家渠道价格.xlsx | 大件运力表.xlsx |
| **计费公式** | `首重价 + max(0, 计费重-1) × 续重价` | `首重价 + max(0, 计费重-30) × 续重价` |
| **线下情况** | 线下快递目前仅顺丰 | 线下物流暂未开通 |

### 5.2 商达人后台截图结构对应关系

商达人后台的 tab 结构（已与用户确认）：

```
线上快递 → 快递运力列表（圆通/韵达/中通...），首重1kg
线下快递 → 同上，线下渠道
线上快运 → 物流运力列表（百世快运/安能...），首重30kg，标注"3件kg起"
线下快运 → 同上，线下渠道
同城寄   → 同城配送
电动车   → 电动车寄送
分销     → 分销渠道
商家寄件 → 商家直发
```

### 5.3 代码中的区分方式

已在 `cost_table.py` 中定义：

```python
FREIGHT_COURIERS: set[str] = {
    "百世快运", "壹米滴答", "安能", "顺心捷达",
    "中通快运", "圆通快运", "德邦快运",
}
```

**注意：中通快运 ≠ 中通，德邦快运 ≠ 德邦**。快运和快递是不同服务，即使来自同一公司。

创建 `CostRecord` 时自动设置：
- 运力名在 `FREIGHT_COURIERS` 中 → `base_weight=30.0, service_type="freight"`
- 否则 → `base_weight=1.0, service_type="express"`

### 5.4 定价公式中 base_weight 的影响

```
# 快递 5kg 件（base_weight=1）
续重公斤 = max(0, 5 - 1) = 4kg
总价 = 首重价 + 4 × 续重价

# 快运 50kg 件（base_weight=30）
续重公斤 = max(0, 50 - 30) = 20kg
总价 = 首重价 + 20 × 续重价

# 快运 25kg 件（base_weight=30，不足首重）
续重公斤 = max(0, 25 - 30) = 0kg
总价 = 首重价（只收首重，不计续重）
```

### 5.5 加价表和让利表也要按类别区分

```yaml
markup_categories:
  线上快递:   # 快递运力，base_weight=1
    圆通: { first_add: 0.9, extra_add: 0.5 }
  线上快运:   # 快运运力，base_weight=30
    安能: { first_add: 10.0, extra_add: 0.5 }

xianyu_discount:
  线上快递:
    圆通: { first_discount: 1.9 }
  线上快运:
    安能: { first_discount: 5.0 }
```

快递首重让利 1-2 元，快运首重让利 5-10 元（因为基数大）。

---

## 六、路由迁移路径修复

Roo 之前做路由迁移（dashboard_server.py → routes/*.py）时，有一处路径计算错误：

**已修复**: `src/dashboard/routes/system.py` L101
- 原: `Path(__file__).resolve().parents[2]` → 指向 `src/`（错误）
- 改: `Path(__file__).resolve().parents[3]` → 指向项目根（正确）

新增的 API 端点如果需要访问 `data/` 或 `config/` 目录，请使用 `ctx.mimic_ops` 提供的路径，或用 `Path(__file__).resolve().parents[3]` 定位项目根。

---

## 七、注意事项

1. **不要删除旧的 `markup_rules` 和 `DEFAULT_MARKUP_RULE`**，保留向后兼容
2. **不要删除旧 API 端点** `get-markup-rules` / `save-markup-rules`
3. 成本表 xlsx 由用户手动替换，代码只需支持新旧格式
4. `FREIGHT_COURIERS` 集合和 `COURIER_ALIASES` 已在 `cost_table.py` 中定义好，直接引用即可
5. 前端的 "小程序价" 和 "闲鱼价" 是**计算列**，不存储，实时根据成本+加价-让利计算
6. `config.yaml` 中的默认值全为 0（用户逐步在 Dashboard 中填入实际值）
7. **中通快运 ≠ 中通**，**德邦快运 ≠ 德邦** — 快运和快递必须作为不同运力处理
8. 快递运力归入 `线上快递`/`线下快递` category，快运运力归入 `线上快运`/`线下快运` category
