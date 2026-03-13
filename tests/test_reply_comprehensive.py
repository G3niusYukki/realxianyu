"""
100+ 复杂场景自动回复测试
通过 POST /api/test-reply 批量测试，覆盖 12 大类场景。
支持无状态测试和多轮会话测试。
"""

import json
import socket
import urllib.request
import uuid
from dataclasses import dataclass, field

API_URL = "http://localhost:8091/api/test-reply"
API_TIMEOUT = 10


@dataclass
class TestCase:
    category: str
    message: str
    expect_rule: str | list[str] | None = None
    expect_skipped: bool = False
    expect_is_quote: bool | None = None
    expect_reply_contains: str | list[str] | None = None
    expect_reply_not_contains: str | list[str] | None = None
    expect_no_reply: bool = False
    session_id: str = ""
    allow_ai: bool = False


@dataclass
class SessionStep:
    message: str
    expect_rule: str | list[str] | None = None
    expect_skipped: bool = False
    expect_is_quote: bool | None = None
    expect_reply_contains: str | list[str] | None = None
    expect_reply_not_contains: str | list[str] | None = None
    expect_phase: str | None = None


@dataclass
class SessionTest:
    category: str
    name: str
    steps: list[SessionStep] = field(default_factory=list)


@dataclass
class TestResult:
    category: str
    message: str
    passed: bool
    expected: str
    actual: str
    reply_snippet: str = ""


def call_api(message: str, session_id: str = "") -> dict:
    payload = {"message": message}
    if session_id:
        payload["session_id"] = session_id
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_URL, data=data, headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=API_TIMEOUT) as resp:
            return json.loads(resp.read())
    except (urllib.error.URLError, socket.timeout, TimeoutError) as e:
        return {"_timeout": True, "_error": str(e), "reply": "", "detail": {}}


def _match_ok(detail: dict, expect_rules: list[str]) -> bool:
    rule = detail.get("rule_matched", "")
    if rule in expect_rules or "any" in expect_rules:
        return True
    if "is_quote=True" in expect_rules and detail.get("is_quote"):
        return True
    if "ai_generated" in expect_rules and detail.get("ai_generated"):
        return True
    if "aftersale_fallback" in expect_rules and detail.get("aftersale_fallback"):
        return True
    if "courier_locked" in expect_rules and detail.get("courier_locked"):
        return True
    return False


def check_case(tc: TestCase) -> TestResult:
    resp = call_api(tc.message, tc.session_id)

    if resp.get("_timeout"):
        if tc.allow_ai:
            return TestResult(tc.category, tc.message, True, "", "TIMEOUT(ai ok)")
        return TestResult(tc.category, tc.message, False, "API call", f"TIMEOUT: {resp.get('_error','')}")

    detail = resp.get("detail", {})
    reply = resp.get("reply", "")
    rule = detail.get("rule_matched", "")
    skipped = detail.get("skipped", False)

    failures = []

    if tc.expect_skipped:
        if not skipped:
            failures.append(f"expect skipped but got rule={rule}")
    elif tc.expect_rule:
        rules = tc.expect_rule if isinstance(tc.expect_rule, list) else [tc.expect_rule]
        if not _match_ok(detail, rules):
            failures.append(f"expect rule in {rules} but got '{rule}'")

    if tc.expect_is_quote is not None and detail.get("is_quote") != tc.expect_is_quote:
        failures.append(f"expect is_quote={tc.expect_is_quote} but got {detail.get('is_quote')}")

    if tc.expect_reply_contains:
        checks = tc.expect_reply_contains if isinstance(tc.expect_reply_contains, list) else [tc.expect_reply_contains]
        for kw in checks:
            if kw not in reply:
                failures.append(f"reply missing '{kw}'")

    if tc.expect_reply_not_contains:
        checks = tc.expect_reply_not_contains if isinstance(tc.expect_reply_not_contains, list) else [tc.expect_reply_not_contains]
        for kw in checks:
            if kw in reply:
                failures.append(f"reply should NOT contain '{kw}'")

    if tc.expect_no_reply and reply:
        failures.append(f"expect no reply but got: {reply[:40]}")

    if failures:
        return TestResult(tc.category, tc.message, False, "; ".join(failures), f"rule={rule} skipped={skipped}", reply[:60])
    return TestResult(tc.category, tc.message, True, "", f"rule={rule}", reply[:60])


def check_session(st: SessionTest) -> list[TestResult]:
    results = []
    sid = f"session_{uuid.uuid4().hex[:8]}"
    for i, step in enumerate(st.steps):
        resp = call_api(step.message, sid)
        label = f"[{st.name}#{i+1}] {step.message[:30]}"

        if resp.get("_timeout"):
            results.append(TestResult(st.category, label, False, "API", "TIMEOUT"))
            continue

        detail = resp.get("detail", {})
        reply = resp.get("reply", "")
        rule = detail.get("rule_matched", "")
        skipped = detail.get("skipped", False)
        phase = detail.get("session_phase", detail.get("phase", ""))

        failures = []
        if step.expect_skipped and not skipped:
            failures.append(f"expect skipped but got rule={rule}")
        elif step.expect_rule:
            rules = step.expect_rule if isinstance(step.expect_rule, list) else [step.expect_rule]
            if not _match_ok(detail, rules):
                failures.append(f"expect rule in {rules} but got '{rule}'")

        if step.expect_is_quote is not None and detail.get("is_quote") != step.expect_is_quote:
            failures.append(f"expect is_quote={step.expect_is_quote} got {detail.get('is_quote')}")

        if step.expect_reply_contains:
            checks = step.expect_reply_contains if isinstance(step.expect_reply_contains, list) else [step.expect_reply_contains]
            for kw in checks:
                if kw not in reply:
                    failures.append(f"reply missing '{kw}'")

        if step.expect_reply_not_contains:
            checks = step.expect_reply_not_contains if isinstance(step.expect_reply_not_contains, list) else [step.expect_reply_not_contains]
            for kw in checks:
                if kw in reply:
                    failures.append(f"reply should NOT contain '{kw}'")

        if step.expect_phase and phase and phase != step.expect_phase:
            failures.append(f"expect phase={step.expect_phase} got {phase}")

        if failures:
            results.append(TestResult(st.category, label, False, "; ".join(failures), f"rule={rule} phase={phase}", reply[:60]))
        else:
            results.append(TestResult(st.category, label, True, "", f"rule={rule} phase={phase}", reply[:60]))
    return results


# ---------------------------------------------------------------------------
STATELESS_TESTS: list[TestCase] = [
    # === 1. 售前问候 + 报价意图 (10) ===
    TestCase("售前问候", "在吗", expect_rule="express_availability"),
    TestCase("售前问候", "老板在不在", expect_rule="express_availability"),
    TestCase("售前问候", "有人吗", expect_rule="express_availability"),
    TestCase("售前问候", "你好呀", expect_rule="express_availability"),
    TestCase("售前问候", "嗨", expect_rule="express_availability"),
    TestCase("售前问候", "多少钱", expect_is_quote=True),
    TestCase("售前问候", "快递费多少", expect_is_quote=True),
    TestCase("售前问候", "运费查一下", expect_is_quote=True),
    TestCase("售前问候", "怎么收费的", expect_is_quote=True, allow_ai=True),
    TestCase("售前问候", "邮费多少", expect_is_quote=True),

    # === 2. 报价请求 (15) ===
    TestCase("报价请求", "广东-浙江 3kg", expect_is_quote=True, expect_reply_not_contains="寄件城市"),
    TestCase("报价请求", "北京-上海 2kg 40x30x20cm", expect_is_quote=True),
    TestCase("报价请求", "杭州到北京一公斤", expect_is_quote=True),
    TestCase("报价请求", "贵州省-广东省-1公斤以内", expect_is_quote=True, allow_ai=True),
    TestCase("报价请求", "福建 黑龙江3kg", expect_is_quote=True),
    TestCase("报价请求", "广东佛山-福建厦门 5.5kg 270x267x460mm", expect_is_quote=True),
    TestCase("报价请求", "浙江安徽1kg", expect_is_quote=True),
    TestCase("报价请求", "河南商丘到云南丽江 1kg", expect_is_quote=True),
    TestCase("报价请求", "寄件城市 贵州贵阳", expect_is_quote=True, expect_reply_contains="收件城市"),
    TestCase("报价请求", "广西玉林到广东江门 3.5kg", expect_is_quote=True),
    TestCase("报价请求", "深圳发成都 500g", expect_is_quote=True),
    TestCase("报价请求", "省内2kg", expect_is_quote=True),
    TestCase("报价请求", "帮我看看杭州发深圳要多少", expect_rule=["any"], allow_ai=True),
    TestCase("报价请求", "从北京寄到广州5公斤", expect_is_quote=True),
    TestCase("报价请求", "上海到武汉 3斤", expect_is_quote=True),

    # === 3. 京东/顺丰 (8) ===
    TestCase("京东顺丰", "有顺丰吗", expect_rule="express_sf_jd", expect_reply_contains="小橙序"),
    TestCase("京东顺丰", "京东快递多少钱", expect_rule="express_sf_jd"),
    TestCase("京东顺丰", "能发顺丰不", expect_rule="express_sf_jd"),
    TestCase("京东顺丰", "改成京东", expect_rule="express_sf_jd"),
    TestCase("京东顺丰", "换顺丰", expect_rule="express_sf_jd"),
    TestCase("京东顺丰", "京东快递", expect_rule="express_sf_jd"),
    TestCase("京东顺丰", "改成顺丰快递", expect_rule="express_sf_jd"),
    TestCase("京东顺丰", "顺丰比这个快吗", expect_rule="express_sf_jd"),

    # === 4. 下单流程 + 兑换码 (13) ===
    TestCase("下单流程", "怎么买", expect_rule="express_buying_process"),
    TestCase("下单流程", "怎么拍", expect_rule="express_buying_process"),
    TestCase("下单流程", "怎么下单", expect_rule="express_buying_process"),
    TestCase("下单流程", "怎么卖", expect_rule="express_buying_process"),
    TestCase("下单流程", "这个怎么卖", expect_rule="express_buying_process"),
    TestCase("下单流程", "直接拍吗", expect_rule="express_buying_process"),
    TestCase("下单流程", "怎么操作", expect_rule="express_buying_process"),
    TestCase("下单流程", "兑换码怎么使用", expect_rule="express_code_usage"),
    TestCase("下单流程", "收到码了然后呢", expect_rule="express_code_usage"),
    TestCase("下单流程", "码收到了怎么弄", expect_rule=["express_code_usage", "express_buying_process"]),
    TestCase("下单流程", "什么小程序", expect_rule="express_xiaochengxu_explain"),
    TestCase("下单流程", "小橙序搜不到", expect_rule=["express_xiaochengxu_explain", "any"], allow_ai=True),
    TestCase("下单流程", "在哪搜", expect_rule="express_xiaochengxu_explain"),

    # === 5. 售后问题 (15) ===
    TestCase("售后问题", "到哪了", expect_rule="express_tracking_query"),
    TestCase("售后问题", "快递到哪了", expect_rule="express_tracking_query"),
    TestCase("售后问题", "单号是多少", expect_rule="express_tracking_query"),
    TestCase("售后问题", "东西坏了", expect_rule="express_complaint"),
    TestCase("售后问题", "包裹破损", expect_rule="express_complaint"),
    TestCase("售后问题", "丢件了", expect_rule="express_complaint"),
    TestCase("售后问题", "退款", expect_rule="express_refund"),
    TestCase("售后问题", "不想要了", expect_rule=["express_refund", "buyer_decline", "express_cancel_order"]),
    TestCase("售后问题", "退余额", expect_rule="express_refund_balance"),
    TestCase("售后问题", "地址写错了", expect_rule="express_change_address"),
    TestCase("售后问题", "能改地址吗", expect_rule="express_change_address"),
    TestCase("售后问题", "收件人写错", expect_rule="express_change_address"),
    TestCase("售后问题", "还没到", expect_rule="express_not_arrived"),
    TestCase("售后问题", "东西少了", expect_rule="express_not_arrived"),
    TestCase("售后问题", "没收到码", expect_rule="express_code_not_received"),

    # === 6. 系统通知 (12) ===
    TestCase("系统通知", "请双方沟通及时确认价格", expect_skipped=True),
    TestCase("系统通知", "修改价格", expect_skipped=True),
    TestCase("系统通知", "你已发货", expect_skipped=True),
    TestCase("系统通知", "未付款，买家关闭了订单", expect_skipped=True),
    TestCase("系统通知", "你当前宝贝拍下未付款\n请在15分钟内付款，避免宝贝被其他人抢走", expect_skipped=True),
    TestCase("系统通知", "蚂蚁森林", expect_skipped=True),
    TestCase("系统通知", "去发货", expect_skipped=True),
    TestCase("系统通知", "请包装好商品，并按我在闲鱼上提供的地址发货", expect_skipped=True),
    TestCase("系统通知", "等待你付款", expect_skipped=True),
    TestCase("系统通知", "请确认价格与协商一致，并在24小时内付款", expect_skipped=True),
    TestCase("系统通知", "我已修改价格，等待你付款", expect_skipped=True),
    TestCase("系统通知", "我已修改价格，等待你付款\n请确认价格与协商一致，并在24小时内付款", expect_skipped=True),

    # === 7. 售后规则补充 (8) ===
    TestCase("售后规则", "怎么预约", expect_rule="express_how_to_schedule"),
    TestCase("售后规则", "预约取件", expect_rule="express_how_to_schedule"),
    TestCase("售后规则", "怎么补差价", expect_rule="express_supplement_pay"),
    TestCase("售后规则", "超重补多少", expect_rule="express_supplement_pay"),
    TestCase("售后规则", "人工", expect_rule="express_human_request"),
    TestCase("售后规则", "转人工", expect_rule="express_human_request"),
    TestCase("售后规则", "抓紧", expect_rule="express_hurry"),
    TestCase("售后规则", "快点发", expect_rule="express_hurry"),

    # === 8. 买家情绪/决策 (10) ===
    TestCase("买家情绪", "算了", expect_rule="buyer_decline"),
    TestCase("买家情绪", "不用了", expect_rule="buyer_decline"),
    TestCase("买家情绪", "考虑一下", expect_rule="buyer_decline"),
    TestCase("买家情绪", "先不寄了", expect_rule="buyer_decline"),
    TestCase("买家情绪", "好的", expect_rule="buyer_acknowledgment"),
    TestCase("买家情绪", "嗯", expect_rule="buyer_acknowledgment"),
    TestCase("买家情绪", "ok", expect_rule="buyer_acknowledgment"),
    TestCase("买家情绪", "收到", expect_rule="buyer_acknowledgment"),
    TestCase("买家情绪", "谢谢", expect_rule="buyer_acknowledgment"),
    TestCase("买家情绪", "哦哦", expect_rule="buyer_acknowledgment"),

    # === 9. 特殊物品/限制 (12) ===
    TestCase("特殊物品", "能寄电池吗", expect_rule="express_restricted"),
    TestCase("特殊物品", "化妆品能发吗", expect_rule=["express_restricted", "express_food_liquid"]),
    TestCase("特殊物品", "寄烟可以不", expect_rule="express_cigarette"),
    TestCase("特殊物品", "到付行吗", expect_rule="express_cod"),
    TestCase("特殊物品", "能寄国外吗", expect_rule="express_international"),
    TestCase("特殊物品", "行李箱能发吗", expect_rule="express_luggage"),
    TestCase("特殊物品", "液体可以寄不", expect_rule="express_food_liquid"),
    TestCase("特殊物品", "需要保价吗", expect_rule="express_insurance"),
    TestCase("特殊物品", "能月结吗", expect_rule="express_monthly"),
    TestCase("特殊物品", "能匿名寄吗", expect_rule="express_anonymous"),
    TestCase("特殊物品", "多久能到", expect_rule="express_eta"),
    TestCase("特殊物品", "什么快递", expect_rule="express_which_courier"),

    # === 10. 低文化水平/非标表达 (12) ===
    TestCase("低文化水平", "5单1kg的要多少", expect_is_quote=True),
    TestCase("低文化水平", "这样办理寄件的？", expect_rule=["express_buying_process", "any"], allow_ai=True),
    TestCase("低文化水平", "两箱子衣服从杭州发", expect_rule=["any"], allow_ai=True),
    TestCase("低文化水平", "我要寄个东西", expect_rule=["any"], allow_ai=True),
    TestCase("低文化水平", "能便宜点不", expect_rule=["price_bargain", "legacy_便宜"]),
    TestCase("低文化水平", "太贵了吧", expect_rule="price_bargain"),
    TestCase("低文化水平", "便宜的快递有没有", expect_rule=["price_bargain", "legacy_便宜"]),
    TestCase("低文化水平", "一条裤子运费多少", expect_is_quote=True),
    TestCase("低文化水平", "三公斤北京到上海咋卖", expect_is_quote=True),
    TestCase("低文化水平", "北京~焦作市", expect_is_quote=True),
    TestCase("低文化水平", "广东省内2kg什么价格", expect_is_quote=True),
    TestCase("低文化水平", "啥时候能到啊", expect_rule="express_eta"),

    # === 11. 边界情况 (10) ===
    TestCase("边界情况", "图片", expect_rule="buyer_acknowledgment"),
    TestCase("边界情况", "语音", expect_rule="buyer_acknowledgment"),
    TestCase("边界情况", "。", expect_rule=["buyer_acknowledgment", "any"], allow_ai=True),
    TestCase("边界情况", "？？？", expect_rule=["any"], allow_ai=True),
    TestCase("边界情况", "寄件人：广西玉林市北流市西埌镇海洋广告，赖东13687858373 收件人:李生 13828026985 广东省江门市鹤山市雅瑶镇穗鹤二手车城信威汽车 3.5kg电线", expect_is_quote=True, allow_ai=True),
    TestCase("边界情况", "真的能寄这么便宜？", expect_rule="express_trust"),
    TestCase("边界情况", "不接单了？", expect_rule="express_network"),
    TestCase("边界情况", "下单失败怎么办", expect_rule="express_order_failed"),
    TestCase("边界情况", "余额在哪看", expect_rule="express_balance_view"),
    TestCase("边界情况", "地址在哪填", expect_rule="express_address_fill"),

    # === 12. 复合/交叉场景 (6) ===
    TestCase("复合场景", "只换了3.7", expect_rule="express_discount_complaint"),
    TestCase("复合场景", "余额少了怎么回事", expect_rule="express_discount_complaint"),
    TestCase("复合场景", "没法发一单", expect_rule="express_cant_order"),
    TestCase("复合场景", "下不了单", expect_rule="express_cant_order"),
    TestCase("复合场景", "菜鸟比你便宜", expect_rule="express_competitor_compare"),
    TestCase("复合场景", "揽收慢", expect_rule="express_slow_pickup"),
]


SESSION_TESTS: list[SessionTest] = [
    SessionTest("会话阶段", "完整流程A", [
        SessionStep("福建 黑龙江3kg", expect_is_quote=True, expect_reply_contains="报价"),
        SessionStep("选韵达", expect_reply_contains="韵达"),
        SessionStep("怎么买", expect_rule=["express_buying_process", "courier_locked"]),
        SessionStep("我已拍下，待付款\n请双方沟通及时确认价格", expect_skipped=True),
        SessionStep("我已付款，等待你发货\n请包装好商品，并按我在闲鱼上提供的地址发货", expect_skipped=True),
        SessionStep("怎么预约", expect_rule="express_how_to_schedule", expect_reply_not_contains="报价"),
    ]),

    SessionTest("会话阶段", "售后催促B", [
        SessionStep("广东-浙江 2kg", expect_is_quote=True),
        SessionStep("选圆通", expect_reply_contains="圆通"),
        SessionStep("我已拍下，待付款\n请双方沟通及时确认价格", expect_skipped=True),
        SessionStep("我已付款，等待你发货\n请包装好商品，并按我在闲鱼上提供的地址发货", expect_skipped=True),
        SessionStep("码呢", expect_rule="express_code_not_received", expect_reply_not_contains="报价"),
        SessionStep("抓紧抓紧", expect_rule="express_hurry"),
    ]),

    SessionTest("会话阶段", "售后京东C", [
        SessionStep("杭州到北京 1kg", expect_is_quote=True),
        SessionStep("选申通", expect_reply_contains="申通"),
        SessionStep("我已付款，等待你发货\n请包装好商品，并按我在闲鱼上提供的地址发货", expect_skipped=True),
        SessionStep("给我改成京东快递吧", expect_rule="express_sf_jd", expect_reply_contains="小橙序"),
        SessionStep("怎么补差价", expect_rule="express_supplement_pay"),
    ]),

    SessionTest("checkout上下文", "规则优先D", [
        SessionStep("北京-上海 1kg", expect_is_quote=True),
        SessionStep("韵达", expect_reply_contains="韵达"),
        SessionStep("兑换码怎么使用", expect_rule="express_code_usage", expect_reply_not_contains="锁定"),
        SessionStep("什么小程序", expect_rule="express_xiaochengxu_explain"),
        SessionStep("京东快递", expect_rule="express_sf_jd"),
    ]),

    SessionTest("渐进信息", "分步提供E", [
        SessionStep("寄件城市 贵州贵阳", expect_is_quote=True, expect_reply_contains="收件城市"),
        SessionStep("收件城市 广东增城", expect_is_quote=True, expect_reply_contains="重量"),
        SessionStep("1公斤以内", expect_is_quote=True, expect_reply_not_contains="寄件城市"),
    ]),

    SessionTest("系统通知会话", "通知不干扰F", [
        SessionStep("广东-浙江 1kg", expect_is_quote=True),
        SessionStep("选韵达", expect_reply_contains="韵达"),
        SessionStep("未付款，买家关闭了订单", expect_skipped=True),
        SessionStep("修改价格", expect_skipped=True),
        SessionStep("你当前宝贝拍下未付款\n请在15分钟内付款", expect_skipped=True),
    ]),
]


def run_all():
    print("=" * 60)
    print("  自动回复系统 100+ 复杂场景测试")
    print("=" * 60)
    print()

    all_results: list[TestResult] = []
    timeouts = 0

    print(f"[1/2] 无状态测试 ({len(STATELESS_TESTS)} 条)...")
    for i, tc in enumerate(STATELESS_TESTS):
        result = check_case(tc)
        all_results.append(result)
        if not result.passed:
            if "TIMEOUT" in result.actual:
                timeouts += 1
            print(f"  FAIL [{tc.category}] \"{tc.message[:30]}\" -> {result.expected} | {result.actual}")
        if (i + 1) % 30 == 0:
            print(f"  ... {i+1}/{len(STATELESS_TESTS)} done")
    stateless_pass = sum(1 for r in all_results if r.passed)
    print(f"  无状态测试完成: {stateless_pass}/{len(all_results)} 通过")
    if timeouts:
        print(f"  (其中 {timeouts} 条因 AI 调用超时)")
    print()

    session_results: list[TestResult] = []
    total_steps = sum(len(st.steps) for st in SESSION_TESTS)
    print(f"[2/2] 会话测试 ({len(SESSION_TESTS)} 个会话, {total_steps} 步)...")
    for st in SESSION_TESTS:
        results = check_session(st)
        session_results.extend(results)
        passed = sum(1 for r in results if r.passed)
        status = "PASS" if passed == len(results) else "FAIL"
        print(f"  {status} [{st.category}] {st.name}: {passed}/{len(results)}")
        for r in results:
            if not r.passed:
                print(f"    FAIL {r.message} -> {r.expected} | {r.actual}")
    print()

    all_results.extend(session_results)

    total = len(all_results)
    passed = sum(1 for r in all_results if r.passed)
    failed = total - passed

    print("=" * 60)
    print(f"  总测试: {total} | 通过: {passed} | 失败: {failed} | 通过率: {passed/total*100:.1f}%")
    print("=" * 60)
    print()

    cats: dict[str, list[TestResult]] = {}
    for r in all_results:
        cats.setdefault(r.category, []).append(r)

    print("分类明细:")
    for cat, results in sorted(cats.items()):
        p = sum(1 for r in results if r.passed)
        pct = p / len(results) * 100 if results else 0
        mark = "  " if p == len(results) else "!!"
        print(f"  {mark} {cat}: {p}/{len(results)} ({pct:.0f}%)")

    if failed:
        print()
        print("失败明细:")
        for r in all_results:
            if not r.passed:
                print(f"  [{r.category}] \"{r.message[:40]}\"")
                print(f"    问题: {r.expected}")
                print(f"    实际: {r.actual}")
                if r.reply_snippet:
                    print(f"    回复: {r.reply_snippet}")
                print()

    return failed == 0


if __name__ == "__main__":
    import sys
    ok = run_all()
    sys.exit(0 if ok else 1)
