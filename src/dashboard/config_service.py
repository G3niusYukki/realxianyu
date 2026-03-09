"""Configuration CRUD service — system_config.json management."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_SYS_CONFIG_FILE = Path(__file__).resolve().parents[2] / "server" / "data" / "system_config.json"

_ALLOWED_CONFIG_SECTIONS = {
    "xianguanjia",
    "ai",
    "oss",
    "auto_reply",
    "auto_publish",
    "order_reminder",
    "pricing",
    "delivery",
    "notifications",
    "store",
    "auto_price_modify",
}

_SENSITIVE_CONFIG_KEYS = ["app_secret", "api_key", "access_key_secret", "mch_secret", "webhook"]


def read_system_config() -> dict[str, Any]:
    try:
        if _SYS_CONFIG_FILE.exists():
            return json.loads(_SYS_CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error("Failed to read system config: %s", e)
    return {}


def write_system_config(data: dict[str, Any]) -> None:
    _SYS_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = _SYS_CONFIG_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.rename(_SYS_CONFIG_FILE)


CONFIG_SECTIONS: list[dict[str, Any]] = [
    {
        "key": "xianguanjia",
        "name": "闲管家配置",
        "fields": [
            {
                "key": "mode",
                "label": "接入模式",
                "type": "select",
                "options": ["self_developed", "business"],
                "default": "self_developed",
                "labels": {"self_developed": "自研应用", "business": "商务对接"},
                "hint": "自研应用：个人或自有 ERP 直连；商务对接：第三方代商家接入",
            },
            {
                "key": "app_key",
                "label": "AppKey",
                "type": "text",
                "required": True,
                "hint": "在闲管家开放平台创建应用后获取",
            },
            {
                "key": "app_secret",
                "label": "AppSecret",
                "type": "password",
                "required": True,
                "hint": "应用密钥，请妥善保管不要泄露",
            },
            {
                "key": "seller_id",
                "label": "商家 ID (Seller ID)",
                "type": "text",
                "required_when": {"mode": "business"},
                "hint": "商务对接模式下的商家标识，自研模式无需填写",
            },
            {
                "key": "base_url",
                "label": "API 网关",
                "type": "text",
                "default": "https://open.goofish.pro",
                "hint": "默认无需修改，仅在私有化部署时更改",
            },
            {
                "key": "default_channel_cat_id",
                "label": "默认闲鱼类目ID",
                "type": "text",
                "hint": "通过查询类目接口获取，上架商品时必填",
            },
            {
                "key": "default_item_biz_type",
                "label": "商品类型",
                "type": "number",
                "default": 2,
                "hint": "2=普通商品（默认）",
            },
            {
                "key": "default_sp_biz_type",
                "label": "发布类型",
                "type": "number",
                "default": 2,
                "hint": "2=全新（默认）",
            },
            {
                "key": "default_stuff_status",
                "label": "成色",
                "type": "select",
                "options": ["1", "2", "3", "4", "5", "6"],
                "default": "1",
                "labels": {
                    "1": "全新",
                    "2": "几乎全新",
                    "3": "轻微使用痕迹",
                    "4": "明显使用痕迹",
                    "5": "大部分功能正常",
                    "6": "无法正常使用",
                },
                "hint": "商品成色，默认全新",
            },
            {"key": "default_express_fee", "label": "默认运费(分)", "type": "number", "default": 0, "hint": "0=包邮"},
            {"key": "default_stock", "label": "默认库存", "type": "number", "default": 1},
            {"key": "default_province", "label": "发货省份编码", "type": "number", "default": 0, "hint": "行政区划编码，如 440000(广东)、310000(上海)、110000(北京)"},
            {"key": "default_city", "label": "发货城市编码", "type": "number", "default": 0, "hint": "行政区划编码，如 440300(深圳)、310100(上海)、110100(北京)"},
            {"key": "default_district", "label": "发货地区编码", "type": "number", "default": 0, "hint": "行政区划编码，如 440305(南山)、310115(浦东)、110101(东城)"},
            {
                "key": "product_callback_url",
                "label": "商品回调地址",
                "type": "text",
                "hint": "填入闲管家开放平台后台，用于接收上架结果通知",
            },
        ],
    },
    {
        "key": "ai",
        "name": "AI 配置",
        "fields": [
            {
                "key": "provider",
                "label": "提供商",
                "type": "select",
                "options": ["qwen", "deepseek", "openai"],
                "default": "qwen",
                "labels": {"qwen": "百炼千问 (Qwen)", "deepseek": "DeepSeek", "openai": "OpenAI"},
            },
            {"key": "api_key", "label": "API Key", "type": "text", "required": True},
            {
                "key": "model",
                "label": "模型",
                "type": "combobox",
                "default": "qwen-plus-latest",
                "options": [
                    "qwen-plus-latest",
                    "qwen-max-latest",
                    "qwen-turbo-latest",
                    "qwen-flash",
                    "qwen3-max",
                    "qwen3.5-plus",
                    "qwq-plus-latest",
                ],
            },
            {
                "key": "base_url",
                "label": "API 地址",
                "type": "text",
                "placeholder": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            },
        ],
    },
    {
        "key": "oss",
        "name": "阿里云 OSS",
        "fields": [
            {"key": "access_key_id", "label": "Access Key ID", "type": "text", "required": True},
            {"key": "access_key_secret", "label": "Access Key Secret", "type": "password", "required": True},
            {"key": "bucket", "label": "Bucket", "type": "text", "required": True},
            {"key": "endpoint", "label": "Endpoint", "type": "text", "required": True},
            {"key": "prefix", "label": "路径前缀", "type": "text", "default": "xianyu/listing/"},
            {"key": "custom_domain", "label": "自定义域名", "type": "text"},
        ],
    },
    {
        "key": "auto_reply",
        "name": "自动回复",
        "fields": [
            {
                "key": "enabled",
                "label": "启用",
                "type": "toggle",
                "default": True,
                "hint": "关闭后系统不再自动回复买家消息",
            },
            {
                "key": "ai_intent_enabled",
                "label": "AI意图识别",
                "type": "toggle",
                "default": False,
                "hint": "使用 AI 分析买家消息意图后生成针对性回复",
            },
            {
                "key": "default_reply",
                "label": "默认回复",
                "type": "textarea",
                "hint": "所有规则均未匹配时的通用兜底回复",
            },
            {
                "key": "virtual_default_reply",
                "label": "虚拟商品默认回复",
                "type": "textarea",
                "hint": "虚拟商品（兑换码/卡密）场景的默认回复",
            },
            {
                "key": "quote_missing_template",
                "label": "报价引导话术",
                "type": "textarea",
                "default": "为了给你报最准确的价格，麻烦提供一下：{fields}\n格式示例：广东省 - 浙江省 - 3kg 30x20x15cm",
                "hint": "买家信息不完整时的引导回复，{fields} 自动替换为缺失信息",
            },
            {
                "key": "strict_format_reply_enabled",
                "label": "严格格式引导",
                "type": "toggle",
                "default": True,
                "hint": "开启后非报价消息也会引导买家按标准格式提供信息",
            },
            {
                "key": "force_non_empty_reply",
                "label": "强制非空回复",
                "type": "toggle",
                "default": True,
                "hint": "避免发送空内容，无匹配时使用兜底话术",
            },
            {
                "key": "non_empty_reply_fallback",
                "label": "兜底话术",
                "type": "textarea",
                "hint": "所有规则均未匹配且 AI 无返回时的最后兜底回复",
            },
            {
                "key": "quote_failed_template",
                "label": "报价失败话术",
                "type": "textarea",
                "default": "报价服务暂时繁忙，我先帮您转人工确认，确保价格准确。",
                "hint": "报价服务异常时的降级回复",
            },
            {
                "key": "quote_reply_max_couriers",
                "label": "报价最多展示快递数",
                "type": "number",
                "default": 10,
                "hint": "报价回复中最多展示多少家快递公司",
            },
            {
                "key": "keyword_replies_text",
                "label": "关键词快捷回复",
                "type": "textarea",
                "hint": "每行一条：关键词=回复内容",
            },
        ],
    },
    {
        "key": "auto_publish",
        "name": "自动上架",
        "fields": [
            {
                "key": "enabled",
                "label": "启用",
                "type": "toggle",
                "default": False,
                "hint": "开启后系统按策略自动上架新商品",
            },
            {
                "key": "default_category",
                "label": "默认品类",
                "type": "select",
                "options": ["express", "recharge", "exchange", "account", "movie_ticket", "game"],
                "default": "exchange",
                "hint": "新上架商品的默认品类归属",
            },
            {
                "key": "auto_compliance",
                "label": "自动合规检查",
                "type": "toggle",
                "default": True,
                "hint": "上架前自动检测违规关键词和敏感内容",
            },
            {
                "key": "cold_start_days",
                "label": "冷启动天数",
                "type": "number",
                "default": 2,
                "hint": "新店前 N 天为冷启动期，每天批量上架新链接",
            },
            {
                "key": "cold_start_daily_count",
                "label": "每日新建链接数",
                "type": "number",
                "default": 5,
                "hint": "冷启动期每天自动上架的链接数量",
            },
            {
                "key": "steady_replace_count",
                "label": "每日替换链接数",
                "type": "number",
                "default": 1,
                "hint": "稳定期每天替换流量最差的链接数量",
            },
            {
                "key": "max_active_listings",
                "label": "最大活跃链接数",
                "type": "number",
                "default": 10,
                "hint": "店铺同时存在的最大商品链接数上限",
            },
            {
                "key": "steady_replace_metric",
                "label": "替换依据",
                "type": "select",
                "options": ["views", "sales"],
                "default": "views",
                "hint": "按什么指标判断需要替换的最差链接（浏览量/销量）",
            },
        ],
    },
    {
        "key": "order_reminder",
        "name": "催单设置",
        "fields": [
            {"key": "enabled", "label": "启用催单", "type": "toggle", "default": True},
            {
                "key": "max_daily",
                "label": "每日最大次数",
                "type": "number",
                "default": 2,
                "hint": "单个买家每日最多收到几次催单",
            },
            {
                "key": "min_interval_hours",
                "label": "最小间隔(小时)",
                "type": "number",
                "default": 4,
                "hint": "两次催单之间至少间隔的小时数",
            },
            {
                "key": "silent_start",
                "label": "静默开始(时)",
                "type": "number",
                "default": 22,
                "hint": "静默时段内不发送催单",
            },
            {"key": "silent_end", "label": "静默结束(时)", "type": "number", "default": 8},
            {
                "key": "templates",
                "label": "催单话术模板",
                "type": "textarea",
                "default": "您好，您的订单还没有完成支付哦~ 如有疑问可以随时问我，确认需要的话请尽快支付，我好给您安排发货。\n---\n提醒一下，您有一笔待支付订单，商品已为您预留，请在规定时间内完成支付，以免影响发货哦~\n---\n最后提醒：您的订单即将超时关闭，如果还需要请尽快支付。若已不需要请忽略此消息。",
                "hint": "每条话术用 --- 分隔，按催单次数依次发送",
            },
        ],
    },
    {
        "key": "pricing",
        "name": "定价规则",
        "fields": [
            {
                "key": "auto_adjust",
                "label": "自动调价",
                "type": "toggle",
                "default": False,
                "hint": "开启后系统根据市场行情和库存自动调整价格",
            },
            {
                "key": "min_margin_percent",
                "label": "最低利润率(%)",
                "type": "number",
                "default": 10,
                "hint": "低于此利润率的价格不会被采用",
            },
            {
                "key": "max_discount_percent",
                "label": "最大降价幅度(%)",
                "type": "number",
                "default": 20,
                "hint": "单次调价不超过此幅度，防止价格波动过大",
            },
        ],
    },
    {
        "key": "delivery",
        "name": "发货规则",
        "fields": [
            {
                "key": "auto_delivery",
                "label": "自动发货",
                "type": "toggle",
                "default": True,
                "hint": "开启后，订单支付成功自动触发闲管家发货",
            },
            {
                "key": "delivery_timeout_minutes",
                "label": "发货超时(分钟)",
                "type": "number",
                "default": 30,
                "hint": "超过设定时长未发货将触发告警通知（需配置告警 Webhook）",
            },
            {
                "key": "notify_on_delivery",
                "label": "发货通知",
                "type": "toggle",
                "default": True,
                "hint": "（规划中）发货成功后通知买家，需配合闲管家消息通道",
            },
        ],
    },
    {
        "key": "auto_price_modify",
        "name": "自动改价",
        "fields": [
            {
                "key": "enabled",
                "label": "启用",
                "type": "toggle",
                "default": False,
                "hint": "买家下单未付款时，自动匹配聊天中的报价并修改订单价格",
            },
            {
                "key": "max_quote_age_seconds",
                "label": "报价有效期(秒)",
                "type": "number",
                "default": 7200,
                "hint": "超过此时间的报价不再用于自动改价",
            },
            {
                "key": "fallback_action",
                "label": "无匹配报价时",
                "type": "select",
                "options": ["skip", "use_listing_price"],
                "default": "skip",
                "labels": {"skip": "跳过不改价", "use_listing_price": "使用上架价格"},
                "hint": "找不到聊天报价时的处理策略",
            },
            {
                "key": "default_express_fee",
                "label": "默认运费(分)",
                "type": "number",
                "default": 0,
                "hint": "改价时的运费，0=包邮",
            },
            {
                "key": "notify_on_modify",
                "label": "改价通知",
                "type": "toggle",
                "default": True,
                "hint": "改价成功后发送通知",
            },
        ],
    },
    {
        "key": "notifications",
        "name": "告警通知",
        "fields": [
            {"key": "feishu_enabled", "label": "飞书通知", "type": "toggle", "default": False},
            {
                "key": "feishu_webhook",
                "label": "飞书 Webhook URL",
                "type": "password",
                "placeholder": "https://open.feishu.cn/open-apis/bot/v2/hook/xxx",
            },
            {"key": "wechat_enabled", "label": "企业微信通知", "type": "toggle", "default": False},
            {
                "key": "wechat_webhook",
                "label": "企业微信 Webhook URL",
                "type": "password",
                "placeholder": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx",
            },
            {"key": "notify_cookie_expire", "label": "Cookie 过期告警", "type": "toggle", "default": True},
            {"key": "notify_cookie_refresh", "label": "Cookie 刷新成功通知", "type": "toggle", "default": True},
            {"key": "notify_sla_alert", "label": "SLA 异常告警", "type": "toggle", "default": True},
            {"key": "notify_order_fail", "label": "订单异常告警", "type": "toggle", "default": True},
            {"key": "notify_after_sales", "label": "售后介入告警", "type": "toggle", "default": True},
            {"key": "notify_ship_fail", "label": "发货失败告警", "type": "toggle", "default": True},
            {"key": "notify_manual_takeover", "label": "人工接管告警", "type": "toggle", "default": True},
        ],
    },
]


def mask_sensitive(config: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of config with sensitive values masked."""
    masked = {}
    for section_key, section_val in config.items():
        if isinstance(section_val, dict):
            masked[section_key] = {}
            for k, v in section_val.items():
                if any(sk in k for sk in _SENSITIVE_CONFIG_KEYS) and v:
                    masked[section_key][k] = str(v)[:4] + "****"
                else:
                    masked[section_key][k] = v
        else:
            masked[section_key] = section_val
    return masked


def update_config(updates: dict[str, Any]) -> dict[str, Any]:
    """Merge updates into system config, return updated config."""
    current = read_system_config()
    for section, values in updates.items():
        if section not in _ALLOWED_CONFIG_SECTIONS:
            continue
        if not isinstance(values, dict):
            current[section] = values
            continue
        if section not in current:
            current[section] = {}
        for k, v in values.items():
            if any(sk in k for sk in _SENSITIVE_CONFIG_KEYS) and isinstance(v, str) and v.endswith("****"):
                continue
            current[section][k] = v
    write_system_config(current)
    return current
