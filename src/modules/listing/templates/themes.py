"""品类配色主题定义。"""

from __future__ import annotations

import random

THEMES: dict[str, dict] = {
    "express": {
        "primary": "#dc2626",
        "primary_light": "#f87171",
        "primary_dark": "#b91c1c",
        "accent": "#f59e0b",
        "bg": "#fef2f2",
        "bg_alt": "#fee2e2",
        "text": "#7f1d1d",
        "text_light": "#ffffff",
        "badge": "快递代发",
        "headline": "首重3元起寄件",
        "sub_headline": "全国免费上门取件",
        "labels": "个人/商家/退换货/可用",
        "tagline": "秒出单号 · 操作简单 · 价格实惠",
        "variants": [
            {
                "headline": "8折+4元无门槛",
                "sub_headline": "快递券可叠加使用",
                "labels": "中通/圆通/申通/韵达/顺丰",
                "tagline": "全国通用 · 不限新老 · 秒出单号",
            },
            {
                "headline": "下单五折",
                "sub_headline": "全国通用 无门槛 下单秒发",
                "labels": "大小件可用/不满意包退",
                "tagline": "全国接单 · 上门取件 · 价格实惠",
            },
            {
                "headline": "首重3元起",
                "sub_headline": "全国免费上门取件",
                "labels": "个人/商家/退换货/可用",
                "tagline": "秒出单号 · 操作简单 · 价格实惠",
            },
            {
                "headline": "2元寄全国",
                "sub_headline": "上门取件 全国接单",
                "labels": "支持退换货/个人/商家寄件",
                "tagline": "不限重量 · 大件超划算 · 免费上门",
            },
            {
                "headline": "快递优惠券",
                "sub_headline": "5折通用快递券 不限新老",
                "labels": "5折券x1/7折券x3/10元无门槛x1",
                "tagline": "到付/寄付均可 · 全国通用",
            },
        ],
    },
    "recharge": {
        "primary": "#d97706",
        "primary_light": "#fbbf24",
        "primary_dark": "#b45309",
        "accent": "#ef4444",
        "bg": "#fef3c7",
        "bg_alt": "#fde68a",
        "text": "#78350f",
        "text_light": "#ffffff",
        "badge": "充值代充",
        "headline": "话费充值低至9折",
        "sub_headline": "三网通充 秒到账",
        "labels": "移动/联通/电信/通用",
        "tagline": "官方渠道 · 安全快速 · 到账迅速",
    },
    "exchange": {
        "primary": "#7c3aed",
        "primary_light": "#a78bfa",
        "primary_dark": "#6d28d9",
        "accent": "#06b6d4",
        "bg": "#ede9fe",
        "bg_alt": "#ddd6fe",
        "text": "#4c1d95",
        "text_light": "#ffffff",
        "badge": "兑换码/卡密",
        "headline": "正版兑换码即买即发",
        "sub_headline": "付款秒发 安全可靠",
        "labels": "游戏/视频/会员/通用",
        "tagline": "正版授权 · 秒发卡密 · 售后无忧",
    },
    "account": {
        "primary": "#16a34a",
        "primary_light": "#4ade80",
        "primary_dark": "#15803d",
        "accent": "#3b82f6",
        "bg": "#dcfce7",
        "bg_alt": "#bbf7d0",
        "text": "#14532d",
        "text_light": "#ffffff",
        "badge": "账号交易",
        "headline": "优质账号出售",
        "sub_headline": "资料齐全 支持验号",
        "labels": "游戏/社交/工具/会员",
        "tagline": "安全换绑 · 售后保障 · 资料齐全",
    },
    "movie_ticket": {
        "primary": "#db2777",
        "primary_light": "#f472b6",
        "primary_dark": "#be185d",
        "accent": "#8b5cf6",
        "bg": "#fce7f3",
        "bg_alt": "#fbcfe8",
        "text": "#831843",
        "text_light": "#ffffff",
        "badge": "电影票代购",
        "headline": "电影票低价代购",
        "sub_headline": "全国影院覆盖",
        "labels": "万达/CGV/金逸/通用",
        "tagline": "低于平台价 · 在线选座 · 出票快速",
    },
    "game": {
        "primary": "#dc2626",
        "primary_light": "#f87171",
        "primary_dark": "#b91c1c",
        "accent": "#f59e0b",
        "bg": "#fee2e2",
        "bg_alt": "#fecaca",
        "text": "#7f1d1d",
        "text_light": "#ffffff",
        "badge": "游戏道具",
        "headline": "游戏充值代购",
        "sub_headline": "正规渠道 快速到账",
        "labels": "手游/端游/Steam/通用",
        "tagline": "正规渠道 · 快速到账 · 专业客服",
    },
    "freight": {
        "primary": "#1d4ed8",
        "primary_light": "#60a5fa",
        "primary_dark": "#1e40af",
        "accent": "#f59e0b",
        "bg": "#eff6ff",
        "bg_alt": "#dbeafe",
        "text": "#1e3a5f",
        "text_light": "#ffffff",
        "badge": "大件快运",
        "headline": "大件物流 越重越便宜",
        "sub_headline": "全国上门取件 30kg起",
        "labels": "家具/电器/行李/搬家",
        "tagline": "上门取件 · 越重越划算 · 大件专属",
        "variants": [
            {
                "headline": "家具电器 全国可寄",
                "sub_headline": "大件物流 免费上门取件",
                "labels": "沙发/床垫/冰箱/洗衣机/空调",
                "tagline": "30kg起步 · 越重越划算 · 全国可寄",
            },
            {
                "headline": "搬家行李 上门取件",
                "sub_headline": "毕业寄 搬家寄 全国可发",
                "labels": "行李箱/打包袋/纸箱/家具",
                "tagline": "免费上门 · 安全送达 · 价格实惠",
            },
            {
                "headline": "大件低至1元/公斤",
                "sub_headline": "越重越划算 全国上门取件",
                "labels": "家具/电器/健身器材/行李",
                "tagline": "30kg起 · 上门取件 · 大件专属",
            },
            {
                "headline": "健身器材 大件运输",
                "sub_headline": "跑步机椭圆机 全国可寄",
                "labels": "跑步机/椭圆机/哑铃/器械",
                "tagline": "专业物流 · 上门取件 · 安全送达",
            },
            {
                "headline": "寄大件 找我们",
                "sub_headline": "30kg起步 越重单价越低",
                "labels": "家具/家电/行李/搬家/器材",
                "tagline": "全国可寄 · 免费上门 · 在线秒回",
            },
        ],
    },
}


def get_theme(category: str) -> dict[str, str]:
    return THEMES.get(category, THEMES["express"])


def get_random_variant(category: str) -> dict[str, str]:
    """从主题的 variants 列表中随机选一套文案，覆盖到基础主题上返回。

    若无 variants 则直接返回基础主题副本。
    """
    theme = dict(get_theme(category))
    variants = theme.pop("variants", None)
    if variants:
        chosen = random.choice(variants)
        theme.update(chosen)
    return theme
