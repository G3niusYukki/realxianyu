export interface CategoryDefaults {
  auto_reply: {
    default_reply: string;
    virtual_default_reply: string;
    ai_intent_enabled: boolean;
    enabled: boolean;
  };
  pricing: {
    auto_adjust: boolean;
    min_margin_percent: number;
    max_discount_percent: number;
    safety_margin_percent?: number;
  };
  delivery: {
    auto_delivery: boolean;
    delivery_timeout_minutes: number;
  };
  summary: string[];
}

export const GENERIC_DEFAULTS: CategoryDefaults = {
  auto_reply: {
    default_reply: '您好！感谢您的咨询。请问有什么可以帮您的吗？',
    virtual_default_reply: '您好！本商品为虚拟商品，购买后自动发送。如有问题请联系客服。',
    ai_intent_enabled: true,
    enabled: true,
  },
  pricing: { auto_adjust: true, min_margin_percent: 10, max_discount_percent: 20, safety_margin_percent: 0 },
  delivery: { auto_delivery: true, delivery_timeout_minutes: 30 },
  summary: ['自动回复 → 通用话术', '定价 → 均衡方案', '发货 → 自动发货'],
};

export const CATEGORY_DEFAULTS: Record<string, CategoryDefaults> = {
  express: {
    auto_reply: {
      default_reply: '直接拍就行拍完给您兑换码',
      virtual_default_reply: '兑换码是兑换余额的，点下单使用余额支付即可',
      ai_intent_enabled: true,
      enabled: true,
    },
    pricing: { auto_adjust: false, min_margin_percent: 15, max_discount_percent: 15, safety_margin_percent: 0 },
    delivery: { auto_delivery: false, delivery_timeout_minutes: 60 },
    summary: ['自动回复 → 快递兑换码业务话术', '定价 → 保守方案（利润率 15%）', '发货 → 手动发货（需填快递单号）'],
  },
  exchange: {
    auto_reply: {
      default_reply: '您好！本商品为兑换码/卡密，购买后系统自动发送到聊天窗口。\n如遇兑换问题请联系客服，我们会第一时间协助处理。',
      virtual_default_reply: '【自动发货】您的兑换码已发送，请查收聊天消息。\n使用方法：复制兑换码 → 打开对应平台 → 兑换/充值\n如有问题请随时联系我们。',
      ai_intent_enabled: true,
      enabled: true,
    },
    pricing: { auto_adjust: true, min_margin_percent: 5, max_discount_percent: 10, safety_margin_percent: 0 },
    delivery: { auto_delivery: true, delivery_timeout_minutes: 5 },
    summary: ['自动回复 → 兑换码/卡密专用话术', '定价 → 激进方案（利润率 5%）', '发货 → 自动发码（付款后 5 秒）'],
  },
  recharge: {
    ...GENERIC_DEFAULTS,
    auto_reply: {
      default_reply: '您好！支持三网话费/流量充值，下单时请留下手机号，充值后到账通知您。',
      virtual_default_reply: '您的充值已提交处理，预计几分钟内到账。如有问题请联系客服。',
      ai_intent_enabled: true,
      enabled: true,
    },
    summary: ['自动回复 → 充值代充话术', '定价 → 均衡方案', '发货 → 自动发货'],
  },
  movie_ticket: {
    ...GENERIC_DEFAULTS,
    auto_reply: {
      default_reply: '您好！支持全国影院电影票代购，请告诉我影片、影院和场次，我帮您查询低价票。',
      virtual_default_reply: '您的电影票已出票，请查收聊天消息中的取票码。',
      ai_intent_enabled: true,
      enabled: true,
    },
    summary: ['自动回复 → 电影票代购话术', '定价 → 均衡方案', '发货 → 自动发货'],
  },
  account: {
    ...GENERIC_DEFAULTS,
    auto_reply: {
      default_reply: '您好！本店出售优质账号，支持验号。下单前请先咨询确认账号详情。',
      virtual_default_reply: '账号信息已发送到聊天窗口，请及时修改密码和绑定信息。',
      ai_intent_enabled: true,
      enabled: true,
    },
    delivery: { auto_delivery: false, delivery_timeout_minutes: 30 },
    summary: ['自动回复 → 账号交易话术', '定价 → 均衡方案', '发货 → 手动发货（需验号）'],
  },
  game: {
    ...GENERIC_DEFAULTS,
    auto_reply: {
      default_reply: '您好！支持多款游戏道具/点券代购，请告诉我游戏名称、区服和需求，我帮您报价。',
      virtual_default_reply: '您的游戏道具已处理完成，请登录游戏查收。如有问题请联系客服。',
      ai_intent_enabled: true,
      enabled: true,
    },
    summary: ['自动回复 → 游戏道具话术', '定价 → 均衡方案', '发货 → 自动发货'],
  },
};
