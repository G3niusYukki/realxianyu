# UI重构计划：配置模块拆分与初始化向导简化

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将SystemConfig.tsx (2156行) 拆分为独立的配置模块组件，简化SetupWizard.tsx (807行)，实现"快速设置"vs"高级设置"分层架构

**Architecture:** 采用分层配置架构，顶层为快速设置面板(核心配置)，下层为高级设置抽屉(详细配置)。按配置功能域拆分组件，保留现有设计系统和数据流模式。

**Tech Stack:** React + TypeScript + TailwindCSS + React Router + Lucide Icons

---

## 现状分析

### 当前问题

| 问题 | 影响 |
|------|------|
| SystemConfig.tsx: 2156行 | 单文件过大，维护困难，编译慢 |
| SetupWizard.tsx: 807行 | 初始化流程冗长，用户流失率高 |
| 所有配置混杂在一个页面 | 用户难以找到需要的配置项 |
| 无快速设置vs高级设置分层 | 新用户被复杂选项 overwhelm |

### 配置数据分析 (基于 config.yaml)

```yaml
配置类别映射:
├── 核心/基础设施类
│   ├── app (应用基础设置)
│   ├── ai (AI服务配置)
│   ├── database (数据库)
│   └── browser (浏览器设置)
├── 平台集成类
│   ├── xianguanjia (闲管家API)
│   ├── accounts (账号/Cookie)
│   └── cookie_cloud (Cookie同步)
├── 业务规则类
│   ├── messages (消息/自动回复)
│   ├── orders (订单管理)
│   ├── quote (报价引擎)
│   ├── listing (商品上架)
│   └── virtual_goods (虚拟商品)
├── 运营辅助类
│   ├── scheduler (定时任务)
│   ├── media (图片/媒体处理)
│   ├── notifications (告警通知)
│   └── content (内容模板)
```

### 当前 SystemConfig 结构

```
SystemConfig.tsx (2156行)
├── 类型定义 (CategoryDefaults, ChatMsg, BuiltinRule等)
├── 常量数据 (CATEGORY_DEFAULTS, PRICING_PRESETS, BUILTIN_RULES等)
├── 子组件 (ConversationSimulator, BuiltinRulesTable, CollapsibleSection等)
├── 主组件 SystemConfig
│   ├── 状态管理 (config, sectionMap, activeTab, loading等)
│   ├── API调用 (fetchConfig, handleSave, handleTest等)
│   ├── Tab渲染逻辑 (store_category, integrations, auto_reply, orders, products, notifications)
│   └── renderSectionFields (动态字段渲染)
```

### 当前 SetupWizard 结构

```
SetupWizard.tsx (807行)
├── STEPS 定义 (6步向导)
├── WizardData 接口
├── 主组件 SetupWizard
│   ├── 步骤状态管理
│   ├── 各步骤组件 (StepCookie, StepAI, StepXGJ, StepCookieCloud, StepNotify, StepCategory)
│   └── 步骤切换/保存逻辑
```

---

## 重构方案概览

### 设计原则

1. **单一职责**: 每个配置模块一个文件，<300行
2. **渐进式披露**: 快速设置展示核心配置，高级设置展开全部
3. **保留现有设计**: 继续使用 xianyu-theme.css 设计系统
4. **向后兼容**: 保持现有配置数据结构不变
5. **路由驱动**: 使用子路由组织配置类别

---

## 1. 新文件结构规划

### 目录结构

```
client/src/
├── pages/config/
│   ├── ConfigLayout.tsx              # 配置页面布局(侧边栏+内容区)
│   ├── ConfigOverview.tsx            # 配置概览/快速设置
│   ├── SystemConfig.tsx              # 原文件-精简为路由容器
│   │
│   ├── sections/                     # 配置模块目录
│   │   ├── IntegrationConfig.tsx     # 集成服务(闲管家/AI/OSS/CookieCloud)
│   │   ├── AutoReplyConfig.tsx       # 自动回复设置
│   │   ├── OrderConfig.tsx           # 订单管理设置
│   │   ├── ProductConfig.tsx         # 商品运营设置
│   │   ├── NotificationConfig.tsx    # 告警通知设置
│   │   └── StoreCategoryConfig.tsx   # 店铺品类选择
│   │
│   ├── components/                   # 配置专用组件
│   │   ├── ConfigSection.tsx         # 配置区块容器
│   │   ├── ConfigField.tsx           # 表单字段渲染器
│   │   ├── QuickSettingCard.tsx      # 快速设置卡片
│   │   ├── SectionNav.tsx            # 侧边栏导航
│   │   ├── ToggleField.tsx           # 开关字段组件
│   │   ├── TestConnectionButton.tsx  # 连接测试按钮
│   │   ├── PricingPresetSelector.tsx # 定价预设选择器
│   │   └── CategorySelector.tsx      # 品类选择器
│   │
│   ├── hooks/                        # 配置专用hooks
│   │   ├── useConfig.ts              # 配置数据管理
│   │   ├── useConfigSection.ts       # 单个配置节管理
│   │   └── useQuickSetup.ts          # 快速设置逻辑
│   │
│   └── constants/                    # 配置常量
│       ├── configCategories.ts       # 配置分类定义
│       ├── pricingPresets.ts         # 定价预设
│       ├── categoryDefaults.ts       # 品类默认配置
│       └── aiProviders.ts            # AI提供商配置
│
├── components/wizard/                # 初始化向导重构
│   ├── QuickSetupWizard.tsx          # 快速设置向导(精简版)
│   ├── WizardLayout.tsx              # 向导布局
│   ├── WizardStep.tsx                # 步骤组件基类
│   │
│   └── steps/                        # 向导步骤
│       ├── StepQuickStart.tsx        # 快速开始(合并核心步骤)
│       ├── StepAdvancedOptions.tsx   # 高级选项(可选)
│       └── StepReview.tsx            # 配置确认
│
└── contexts/
    └── ConfigContext.tsx             # 配置全局上下文(如需要)
```

### 文件拆分详情

| 原文件 | 新文件 | 说明 |
|--------|--------|------|
| SystemConfig.tsx (2156行) | ConfigLayout.tsx | 布局容器 (~150行) |
| | ConfigOverview.tsx | 快速设置面板 (~300行) |
| | sections/*.tsx (6个) | 各配置模块 (~200行/个) |
| | components/*.tsx (8个) | 复用组件 (~100行/个) |
| | constants/*.ts (4个) | 常量提取 |
| SetupWizard.tsx (807行) | QuickSetupWizard.tsx | 精简向导 (~250行) |
| | WizardLayout.tsx | 向导布局 (~100行) |
| | steps/*.tsx (3个) | 向导步骤 (~150行/个) |

---

## 2. 配置分类方案

### 分类原则

基于功能域和用户心智模型，将配置分为以下类别：

### 类别定义

```typescript
// configCategories.ts
export const CONFIG_CATEGORIES = [
  {
    id: 'quick',
    label: '快速设置',
    icon: 'Zap',
    description: '核心配置一站式完成',
    isQuick: true,
    items: ['category', 'xianguanjia', 'ai', 'notifications']
  },
  {
    id: 'integrations',
    label: '集成服务',
    icon: 'Plug',
    description: '连接第三方平台和服务',
    items: ['xianguanjia', 'ai', 'oss', 'cookie_cloud', 'slider_auto_solve']
  },
  {
    id: 'business',
    label: '业务规则',
    icon: 'Settings',
    description: '自动化业务处理规则',
    items: ['auto_reply', 'orders', 'delivery', 'pricing', 'auto_price_modify']
  },
  {
    id: 'products',
    label: '商品运营',
    icon: 'Package',
    description: '商品上架和运营策略',
    items: ['auto_publish', 'listing']
  },
  {
    id: 'notifications',
    label: '告警通知',
    icon: 'Bell',
    description: '消息推送和告警设置',
    items: ['notifications', 'order_reminder']
  },
  {
    id: 'advanced',
    label: '高级设置',
    icon: 'Sliders',
    description: '系统级高级配置',
    items: ['app', 'database', 'browser', 'scheduler', 'media', 'content'],
    isAdvanced: true
  }
] as const;
```

### 配置项映射

| 配置域 | YAML路径 | 所属类别 | 快速设置? | 复杂度 |
|--------|----------|----------|-----------|--------|
| 店铺品类 | store.category | quick | ✅ 是 | 低 |
| 闲管家 | xianguanjia | integrations | ✅ 是 | 中 |
| AI服务 | ai | integrations | ✅ 是 | 中 |
| 告警通知 | notifications | notifications | ✅ 是 | 低 |
| CookieCloud | cookie_cloud | integrations | ❌ 否 | 中 |
| OSS存储 | oss | integrations | ❌ 否 | 中 |
| 滑块验证 | slider_auto_solve | integrations | ❌ 否 | 高 |
| 自动回复 | messages.auto_reply | business | ❌ 否 | 高 |
| 意图规则 | messages.intent_rules | business | ❌ 否 | 高 |
| 定价规则 | pricing | business | ❌ 否 | 中 |
| 订单催付 | order_reminder | business | ❌ 否 | 低 |
| 自动改价 | auto_price_modify | business | ❌ 否 | 中 |
| 发货规则 | delivery | business | ❌ 否 | 低 |
| 自动上架 | auto_publish | products | ❌ 否 | 中 |
| 应用设置 | app | advanced | ❌ 否 | 低 |
| 数据库 | database | advanced | ❌ 否 | 高 |
| 浏览器 | browser | advanced | ❌ 否 | 中 |

---

## 3. 组件拆分策略

### 3.1 配置模块组件 (Config Sections)

每个配置模块是一个独立的Section组件：

```typescript
// sections/IntegrationConfig.tsx
interface IntegrationConfigProps {
  config: SystemConfig;
  onChange: (section: string, field: string, value: any) => void;
  onSave: () => Promise<void>;
  setupProgress?: SetupProgress;
}

export function IntegrationConfig({ config, onChange, onSave, setupProgress }: IntegrationConfigProps) {
  // 模块专属状态和逻辑
  const [xgjTesting, setXgjTesting] = useState(false);
  const [aiTesting, setAiTesting] = useState(false);
  
  return (
    <ConfigSection 
      title="集成服务" 
      icon={Plug}
      description="管理闲管家、AI服务和存储配置"
    >
      {/* 闲管家配置折叠面板 */}
      <CollapsibleSection 
        title="闲管家配置"
        isConfigured={isConfigured('xianguanjia')}
      >
        <ConfigField section="xianguanjia" field="app_key" ... />
        <ConfigField section="xianguanjia" field="app_secret" ... />
        <TestConnectionButton 
          type="xianguanjia"
          onTest={handleXgjTest}
          testing={xgjTesting}
        />
      </CollapsibleSection>
      
      {/* AI配置折叠面板 */}
      <CollapsibleSection title="AI配置" ...>
        ...
      </CollapsibleSection>
      
      {/* OSS配置折叠面板 */}
      <CollapsibleSection title="阿里云OSS" ...>
        ...
      </CollapsibleSection>
      
      {/* CookieCloud折叠面板 */}
      <CollapsibleSection title="CookieCloud" ...>
        ...
      </CollapsibleSection>
    </ConfigSection>
  );
}
```

### 3.2 通用配置组件

```typescript
// components/ConfigSection.tsx
interface ConfigSectionProps {
  title: string;
  icon: LucideIcon;
  description?: string;
  children: React.ReactNode;
  actions?: React.ReactNode;
}

export function ConfigSection({ title, icon: Icon, description, children, actions }: ConfigSectionProps) {
  return (
    <div className="space-y-4 animate-in fade-in slide-in-from-right-4">
      <div className="xy-card p-6 pb-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-xy-text-primary flex items-center gap-2">
              <Icon className="w-5 h-5" /> {title}
            </h2>
            {description && (
              <p className="text-sm text-xy-text-secondary mt-1">{description}</p>
            )}
          </div>
          {actions}
        </div>
      </div>
      {children}
    </div>
  );
}
```

```typescript
// components/ConfigField.tsx
interface ConfigFieldProps {
  section: string;
  field: string;
  config: any;
  onChange: (value: any) => void;
  sectionMap?: SectionMap;
}

export function ConfigField({ section, field, config, onChange, sectionMap }: ConfigFieldProps) {
  const fieldDef = sectionMap?.[section]?.fields?.find((f: any) => f.key === field);
  const value = config?.[field] ?? fieldDef?.default ?? '';
  
  // 根据 field.type 渲染不同输入控件
  switch (fieldDef?.type) {
    case 'textarea':
      return <textarea ... />;
    case 'select':
      return <select ... />;
    case 'toggle':
      return <ToggleField ... />;
    case 'number':
      return <input type="number" ... />;
    default:
      return <input type="text" ... />;
  }
}
```

```typescript
// components/QuickSettingCard.tsx
interface QuickSettingCardProps {
  title: string;
  description: string;
  icon: LucideIcon;
  status: 'configured' | 'pending' | 'optional';
  onClick: () => void;
  actionLabel?: string;
}

export function QuickSettingCard({ 
  title, description, icon: Icon, status, onClick, actionLabel 
}: QuickSettingCardProps) {
  const statusConfig = {
    configured: { color: 'green', label: '已配置', icon: CheckCircle2 },
    pending: { color: 'orange', label: '待配置', icon: AlertCircle },
    optional: { color: 'gray', label: '可选', icon: HelpCircle }
  };
  
  return (
    <div className="xy-card p-5 hover:shadow-md transition-shadow">
      <div className="flex items-start gap-4">
        <div className="p-3 rounded-xl bg-xy-brand-50">
          <Icon className="w-6 h-6 text-xy-brand-500" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-bold text-xy-text-primary">{title}</h3>
            <StatusBadge status={status} />
          </div>
          <p className="text-sm text-xy-text-secondary mt-1">{description}</p>
          <button onClick={onClick} className="xy-btn-primary mt-3">
            {actionLabel || '配置'}
          </button>
        </div>
      </div>
    </div>
  );
}
```

### 3.3 向导组件重构

```typescript
// components/wizard/QuickSetupWizard.tsx
const QUICK_STEPS = [
  { 
    id: 'essentials', 
    label: '核心配置', 
    icon: Zap,
    description: '配置闲管家、AI和店铺品类'
  },
  { 
    id: 'notifications', 
    label: '告警通知', 
    icon: Bell,
    description: '设置通知渠道(可选)',
    optional: true
  },
  { 
    id: 'review', 
    label: '确认', 
    icon: CheckCircle2,
    description: '检查配置并完成初始化'
  }
] as const;

export function QuickSetupWizard() {
  const [step, setStep] = useState(0);
  const [config, setConfig] = useState<QuickSetupConfig>({
    xianguanjia: { app_key: '', app_secret: '', mode: 'self_developed' },
    ai: { provider: 'qwen', api_key: '', model: 'qwen-plus-latest' },
    category: 'express',
    notifications: { enabled: false }
  });
  
  // 向导状态管理...
  
  return (
    <WizardLayout 
      steps={QUICK_STEPS}
      currentStep={step}
      onStepChange={setStep}
    >
      {step === 0 && (
        <StepQuickStart 
          config={config}
          onChange={setConfig}
        />
      )}
      {step === 1 && (
        <StepNotifications 
          config={config}
          onChange={setConfig}
        />
      )}
      {step === 2 && (
        <StepReview 
          config={config}
          onComplete={handleComplete}
        />
      )}
    </WizardLayout>
  );
}
```

---

## 4. 路由调整建议

### 新路由结构

```typescript
// App.tsx 路由更新
<Routes>
  {/* 现有路由保持不变 */}
  <Route path="/config" element={<ConfigLayout />}>
    {/* 默认显示快速设置/概览 */}
    <Route index element={<Navigate to="/config/overview" replace />} />
    
    {/* 快速设置 */}
    <Route path="overview" element={<ConfigOverview />} />
    
    {/* 配置类别路由 */}
    <Route path="integrations" element={<IntegrationConfig />} />
    <Route path="business" element={<BusinessConfig />} />
    <Route path="products" element={<ProductConfig />} />
    <Route path="notifications" element={<NotificationConfig />} />
    <Route path="advanced" element={<AdvancedConfig />} />
    
    {/* 向后兼容：旧路由重定向 */}
    <Route path="legacy" element={<SystemConfigLegacy />} />
  </Route>
</Routes>
```

### 路由导航结构

```
/config
├── /overview (快速设置/配置概览) ⭐ 默认页
├── /integrations (集成服务)
│   ├── ?section=xianguanjia (锚点到指定折叠面板)
│   ├── ?section=ai
│   ├── ?section=oss
│   └── ?section=cookiecloud
├── /business (业务规则)
│   ├── ?section=auto_reply
│   ├── ?section=orders
│   └── ?section=pricing
├── /products (商品运营)
│   └── ?section=auto_publish
├── /notifications (告警通知)
└── /advanced (高级设置)
```

### 侧边栏导航设计

```typescript
// components/SectionNav.tsx
const NAV_ITEMS = [
  { 
    category: 'quick',
    items: [
      { path: '/config/overview', label: '快速设置', icon: Zap, isDefault: true }
    ]
  },
  {
    category: 'config',
    label: '配置类别',
    items: [
      { path: '/config/integrations', label: '集成服务', icon: Plug },
      { path: '/config/business', label: '业务规则', icon: Settings },
      { path: '/config/products', label: '商品运营', icon: Package },
      { path: '/config/notifications', label: '告警通知', icon: Bell },
    ]
  },
  {
    category: 'advanced',
    items: [
      { path: '/config/advanced', label: '高级设置', icon: Sliders }
    ]
  }
];
```

---

## 5. 数据流设计

### 配置状态管理

```typescript
// hooks/useConfig.ts
export function useConfig() {
  const [config, setConfig] = useState<SystemConfig>({});
  const [sectionMap, setSectionMap] = useState<SectionMap>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [isDirty, setIsDirty] = useState(false);
  
  // 加载配置
  const fetchConfig = useCallback(async () => {
    setLoading(true);
    try {
      const [sectionsRes, configRes] = await Promise.all([
        getConfigSections(),
        getSystemConfig()
      ]);
      setSectionMap(sectionsRes.data.sections);
      setConfig(configRes.data.config);
    } finally {
      setLoading(false);
    }
  }, []);
  
  // 保存配置
  const saveConfig = useCallback(async (updates?: Partial<SystemConfig>) => {
    setSaving(true);
    try {
      const toSave = updates || config;
      const res = await saveSystemConfig(toSave);
      if (res.data.ok) {
        setConfig(res.data.config);
        setIsDirty(false);
        toast.success('配置保存成功');
      }
    } finally {
      setSaving(false);
    }
  }, [config]);
  
  // 更新字段
  const updateField = useCallback((section: string, field: string, value: any) => {
    setConfig(prev => ({
      ...prev,
      [section]: { ...prev[section], [field]: value }
    }));
    setIsDirty(true);
  }, []);
  
  return {
    config,
    sectionMap,
    loading,
    saving,
    isDirty,
    fetchConfig,
    saveConfig,
    updateField
  };
}
```

### ConfigContext (可选)

```typescript
// contexts/ConfigContext.tsx
interface ConfigContextValue {
  config: SystemConfig;
  sectionMap: SectionMap;
  loading: boolean;
  updateField: (section: string, field: string, value: any) => void;
  saveConfig: () => Promise<void>;
}

const ConfigContext = createContext<ConfigContextValue | null>(null);

export function ConfigProvider({ children }: { children: React.ReactNode }) {
  const configState = useConfig();
  
  return (
    <ConfigContext.Provider value={configState}>
      {children}
    </ConfigContext.Provider>
  );
}
```

---

## 6. 实施步骤 (按优先级排序)

### Phase 1: 基础设施和常量提取 (低风险)

**目标:** 准备重构基础，零行为变更

#### Task 1.1: 创建配置常量文件

**Files:**
- Create: `client/src/pages/config/constants/categoryDefaults.ts`
- Create: `client/src/pages/config/constants/pricingPresets.ts`
- Create: `client/src/pages/config/constants/aiProviders.ts`
- Create: `client/src/pages/config/constants/configCategories.ts`

**Steps:**

- [ ] **Step 1: 提取品类默认配置**

```typescript
// constants/categoryDefaults.ts
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
  };
  delivery: {
    auto_delivery: boolean;
    delivery_timeout_minutes: number;
  };
  summary: string[];
}

export const GENERIC_DEFAULTS: CategoryDefaults = { ... };
export const CATEGORY_DEFAULTS: Record<string, CategoryDefaults> = { ... };
```

- [ ] **Step 2: 提取定价预设**

```typescript
// constants/pricingPresets.ts
export const PRICING_PRESETS = {
  conservative: { ... },
  balanced: { ... },
  aggressive: { ... }
};
```

- [ ] **Step 3: 提取AI提供商配置**

```typescript
// constants/aiProviders.ts
export const AI_PROVIDER_GUIDES: Record<string, AIProviderGuide> = { ... };
export const AI_PROVIDERS = ['qwen', 'deepseek', 'openai'];
```

- [ ] **Step 4: 验证提取的常量与原文件一致**

Run: `grep -n "CATEGORY_DEFAULTS" client/src/pages/config/SystemConfig.tsx`
Expected: Lines showing the original definitions

- [ ] **Step 5: Commit**

```bash
git add client/src/pages/config/constants/
git commit -m "refactor(config): extract configuration constants to dedicated files"
```

#### Task 1.2: 创建基础组件

**Files:**
- Create: `client/src/pages/config/components/ConfigSection.tsx`
- Create: `client/src/pages/config/components/CollapsibleSection.tsx`
- Create: `client/src/pages/config/components/ToggleField.tsx`

**Steps:**

- [ ] **Step 1: 从 SystemConfig.tsx 提取 CollapsibleSection 组件**

```typescript
// components/CollapsibleSection.tsx
// 直接复制现有实现，仅调整 import 路径
```

- [ ] **Step 2: 创建 ConfigSection 组件**

```typescript
// components/ConfigSection.tsx
// 包装 CollapsibleSection，添加统一的头部样式
```

- [ ] **Step 3: 验证组件可正常导入**

Add a test import in SystemConfig.tsx temporarily, run build.

- [ ] **Step 4: Commit**

```bash
git add client/src/pages/config/components/
git commit -m "refactor(config): extract reusable config section components"
```

### Phase 2: 创建新的配置布局 (中风险)

**目标:** 建立新的页面结构，但保持旧路由可用

#### Task 2.1: 创建 ConfigLayout

**Files:**
- Create: `client/src/pages/config/ConfigLayout.tsx`
- Modify: `client/src/App.tsx:30-35` (添加嵌套路由)

**Steps:**

- [ ] **Step 1: 创建布局组件**

```typescript
// ConfigLayout.tsx
import { Outlet, NavLink } from 'react-router-dom';
import { SectionNav } from './components/SectionNav';

export default function ConfigLayout() {
  return (
    <div className="xy-page max-w-5xl xy-enter">
      <div className="flex flex-col md:flex-row gap-6">
        <aside className="md:w-56 flex-shrink-0">
          <SectionNav />
        </aside>
        <main className="flex-1 min-w-0">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: 更新 App.tsx 路由**

```typescript
<Route path="/config" element={<ConfigLayout />}>
  <Route index element={<Navigate to="/config/legacy" replace />} />
  <Route path="legacy" element={<SystemConfig />} />
</Route>
```

- [ ] **Step 3: 验证布局渲染正常**

访问 `/config`，确认侧边栏和 outlet 区域显示正常。

- [ ] **Step 4: Commit**

```bash
git add client/src/pages/config/ConfigLayout.tsx client/src/App.tsx
git commit -m "feat(config): add ConfigLayout with nested routing structure"
```

#### Task 2.2: 创建配置概览页面 (快速设置)

**Files:**
- Create: `client/src/pages/config/ConfigOverview.tsx`
- Create: `client/src/pages/config/components/QuickSettingCard.tsx`

**Steps:**

- [ ] **Step 1: 创建 QuickSettingCard 组件**

```typescript
// components/QuickSettingCard.tsx
// 实现见上文设计
```

- [ ] **Step 2: 创建 ConfigOverview 页面**

```typescript
// ConfigOverview.tsx
export default function ConfigOverview() {
  const { config, setupProgress } = useConfig();
  const navigate = useNavigate();
  
  return (
    <div className="space-y-6">
      {/* 配置完成度 */}
      <SetupProgressCard progress={setupProgress} />
      
      {/* 快速设置网格 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <QuickSettingCard
          title="闲管家连接"
          description="连接闲鱼开放平台API"
          icon={Settings}
          status={isConfigured('xianguanjia') ? 'configured' : 'pending'}
          onClick={() => navigate('/config/integrations?section=xianguanjia')}
        />
        <QuickSettingCard
          title="AI服务"
          description="配置智能回复和意图识别"
          icon={Zap}
          status={isConfigured('ai') ? 'configured' : 'pending'}
          onClick={() => navigate('/config/integrations?section=ai')}
        />
        {/* 更多卡片... */}
      </div>
      
      {/* 下一步引导 */}
      <NextStepsPanel setupProgress={setupProgress} />
    </div>
  );
}
```

- [ ] **Step 3: 添加路由**

```typescript
// App.tsx
<Route path="/config">
  <Route path="overview" element={<ConfigOverview />} />
  <Route path="legacy" element={<SystemConfig />} />
</Route>
```

- [ ] **Step 4: 验证页面渲染**

访问 `/config/overview`，确认快速设置卡片显示正常。

- [ ] **Step 5: Commit**

```bash
git add client/src/pages/config/ConfigOverview.tsx
git commit -m "feat(config): add quick setup overview page"
```

### Phase 3: 拆分配置模块 (中风险)

**目标:** 逐步将 SystemConfig 的内容迁移到独立的 section 组件

#### Task 3.1: 创建 IntegrationConfig

**Files:**
- Create: `client/src/pages/config/sections/IntegrationConfig.tsx`
- Modify: `client/src/pages/config/SystemConfig.tsx` (可选: 添加重定向)

**Steps:**

- [ ] **Step 1: 复制并重构集成服务相关代码**

从 SystemConfig.tsx 提取以下内容到新文件：
- `SECTION_GUIDES.xianguanjia/ai/oss`
- `CollapsibleSection` for xianguanjia/ai/oss/cookie_cloud
- `handleXgjTest` / `handleAiTest` 逻辑
- `PushUrlDisplay` 组件

- [ ] **Step 2: 创建 useIntegrationConfig hook**

```typescript
// hooks/useIntegrationConfig.ts
export function useIntegrationConfig(config: SystemConfig, onChange: Function) {
  const [testing, setTesting] = useState({ xianguanjia: false, ai: false });
  const [testResults, setTestResults] = useState({});
  
  const testConnection = async (type: 'xianguanjia' | 'ai') => { ... };
  
  return { testing, testResults, testConnection };
}
```

- [ ] **Step 3: 添加路由**

```typescript
// App.tsx
<Route path="integrations" element={<IntegrationConfig />} />
```

- [ ] **Step 4: 验证功能完整性**

在 `/config/integrations` 测试：
- 闲管家配置表单
- 连接测试按钮
- AI配置表单
- 连接测试

- [ ] **Step 5: Commit**

```bash
git add client/src/pages/config/sections/IntegrationConfig.tsx
git commit -m "feat(config): add IntegrationConfig section component"
```

#### Task 3.2: 创建其他 Section 组件 (并行任务)

按照 Task 3.1 的模式，依次创建：

- [ ] **Task 3.2.1:** AutoReplyConfig (自动回复)
- [ ] **Task 3.2.2:** OrderConfig (订单管理)
- [ ] **Task 3.2.3:** ProductConfig (商品运营)
- [ ] **Task 3.2.4:** NotificationConfig (告警通知)

每个任务完成后提交一次 commit。

### Phase 4: 简化初始化向导 (中风险)

**目标:** 将 6步向导简化为 3步快速向导

#### Task 4.1: 创建新的 QuickSetupWizard

**Files:**
- Create: `client/src/components/wizard/QuickSetupWizard.tsx`
- Create: `client/src/components/wizard/WizardLayout.tsx`
- Create: `client/src/components/wizard/steps/StepQuickStart.tsx`
- Create: `client/src/components/wizard/steps/StepNotifications.tsx`
- Create: `client/src/components/wizard/steps/StepReview.tsx`

**Steps:**

- [ ] **Step 1: 创建 WizardLayout**

```typescript
// components/wizard/WizardLayout.tsx
interface WizardLayoutProps {
  steps: WizardStep[];
  currentStep: number;
  children: React.ReactNode;
  onNext: () => void;
  onBack: () => void;
  onSkip?: () => void;
}

export function WizardLayout({ steps, currentStep, children, onNext, onBack, onSkip }: WizardLayoutProps) {
  return (
    <div className="fixed inset-0 z-50 bg-xy-bg flex flex-col">
      {/* 头部进度条 */}
      <WizardHeader steps={steps} currentStep={currentStep} />
      
      {/* 内容区 */}
      <div className="flex-1 overflow-y-auto px-6 py-8">
        <div className="max-w-2xl mx-auto">
          {children}
        </div>
      </div>
      
      {/* 底部导航 */}
      <WizardFooter 
        currentStep={currentStep} 
        totalSteps={steps.length}
        onNext={onNext}
        onBack={onBack}
        onSkip={onSkip}
      />
    </div>
  );
}
```

- [ ] **Step 2: 创建 StepQuickStart 组件**

合并原有的 StepCookie + StepAI + StepXGJ + StepCategory 的核心字段：
- Cookie 输入 (简化)
- AI 提供商 + API Key
- 闲管家 AppKey + AppSecret
- 店铺品类选择

```typescript
// components/wizard/steps/StepQuickStart.tsx
export function StepQuickStart({ config, onChange }: StepProps) {
  return (
    <div className="space-y-6">
      <SectionTitle>核心配置</SectionTitle>
      <SectionDesc>配置系统运行的必要设置</SectionDesc>
      
      {/* Cookie 区域 */}
      <div className="bg-xy-gray-50 rounded-xl p-4">
        <h3 className="font-bold text-xy-text-primary mb-3">闲鱼账号</h3>
        <textarea ... />
      </div>
      
      {/* AI 区域 */}
      <div className="bg-xy-gray-50 rounded-xl p-4">
        <h3 className="font-bold text-xy-text-primary mb-3">AI服务</h3>
        {/* 简化的 AI 配置 */}
      </div>
      
      {/* 闲管家区域 */}
      <div className="bg-xy-gray-50 rounded-xl p-4">
        <h3 className="font-bold text-xy-text-primary mb-3">闲管家</h3>
        {/* 简化的 XGJ 配置 */}
      </div>
      
      {/* 品类选择 */}
      <div className="bg-xy-gray-50 rounded-xl p-4">
        <h3 className="font-bold text-xy-text-primary mb-3">店铺品类</h3>
        <CategorySelector ... />
      </div>
    </div>
  );
}
```

- [ ] **Step 3: 创建 QuickSetupWizard 主组件**

```typescript
// components/wizard/QuickSetupWizard.tsx
export function QuickSetupWizard() {
  // 与原 SetupWizard 类似，但只有 3 个步骤
  // 数据模型简化
}
```

- [ ] **Step 4: 更新 setup_wizard.py 后端 (如需要)**

检查后端是否需要调整以支持新的快速向导数据结构。

- [ ] **Step 5: Commit**

```bash
git add client/src/components/wizard/
git commit -m "feat(wizard): add simplified QuickSetupWizard with 3-step flow"
```

#### Task 4.2: 切换向导实现

**Files:**
- Modify: `client/src/App.tsx` (更新向导引用)
- Modify: `client/src/components/SetupWizard.tsx` (重命名为 SetupWizard.legacy.tsx 或删除)

**Steps:**

- [ ] **Step 1: 更新 App.tsx 中的向导引用**

```typescript
import { QuickSetupWizard } from './components/wizard/QuickSetupWizard';

function App() {
  return (
    <>
      <QuickSetupWizard />
      {/* ... */}
    </>
  );
}
```

- [ ] **Step 2: 保留旧向导作为备份**

```bash
mv client/src/components/SetupWizard.tsx client/src/components/SetupWizard.legacy.tsx
```

- [ ] **Step 3: 验证新向导流程**

清除浏览器数据，访问应用，验证：
- 新向导正常显示
- 3步流程正常工作
- 配置保存正确

- [ ] **Step 4: Commit**

```bash
git add client/src/components/
git commit -m "feat(wizard): switch to QuickSetupWizard, keep legacy as backup"
```

### Phase 5: 清理和优化 (低风险)

**目标:** 移除旧代码，优化性能

#### Task 5.1: 清理 SystemConfig.tsx

**Files:**
- Modify: `client/src/pages/config/SystemConfig.tsx`

**Steps:**

- [ ] **Step 1: 精简 SystemConfig.tsx**

移除已提取到 sections/ 的代码，保留：
- 基本的路由处理
- 对旧路由的兼容性支持（重定向到新路由）

```typescript
// SystemConfig.tsx - 精简版
export default function SystemConfig() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  
  useEffect(() => {
    // 将旧 tab 参数映射到新路由
    const tab = searchParams.get('tab');
    const routeMap: Record<string, string> = {
      'store_category': '/config/overview',
      'integrations': '/config/integrations',
      'auto_reply': '/config/business?section=auto_reply',
      'orders': '/config/business?section=orders',
      'products': '/config/products',
      'notifications': '/config/notifications',
    };
    
    if (tab && routeMap[tab]) {
      navigate(routeMap[tab], { replace: true });
    }
  }, [searchParams, navigate]);
  
  // 渲染占位或加载状态
  return <div className="xy-loading">正在跳转...</div>;
}
```

- [ ] **Step 2: 更新路由**

```typescript
// App.tsx
<Route path="/config">
  <Route index element={<Navigate to="/config/overview" replace />} />
  <Route path="overview" element={<ConfigOverview />} />
  <Route path="integrations" element={<IntegrationConfig />} />
  {/* ... 其他路由 ... */}
  <Route path="legacy" element={<SystemConfig />} /> {/* 保留用于旧链接兼容 */}
</Route>
```

- [ ] **Step 3: 验证旧链接兼容性**

访问 `/config?tab=integrations`，确认正确重定向到新路由。

- [ ] **Step 4: Commit**

```bash
git add client/src/pages/config/SystemConfig.tsx
git commit -m "refactor(config): simplify SystemConfig to legacy redirect handler"
```

#### Task 5.2: 删除备份文件

**Files:**
- Delete: `client/src/components/SetupWizard.legacy.tsx`

**Steps:**

- [ ] **Step 1: 确认新向导稳定运行一段时间后**

- [ ] **Step 2: 删除备份文件**

```bash
rm client/src/components/SetupWizard.legacy.tsx
git add client/src/components/SetupWizard.legacy.tsx
git commit -m "chore: remove SetupWizard legacy backup"
```

#### Task 5.3: 性能优化

**Files:**
- Modify: `client/src/pages/config/sections/*.tsx`

**Steps:**

- [ ] **Step 1: 添加 React.memo 优化**

```typescript
export const IntegrationConfig = memo(function IntegrationConfig({ ... }) {
  // ...
});
```

- [ ] **Step 2: 使用 useMemo 缓存计算结果**

```typescript
const isConfigured = useMemo(() => {
  return /* 计算逻辑 */;
}, [config]);
```

- [ ] **Step 3: 验证性能提升**

使用 React DevTools Profiler 检查重渲染情况。

- [ ] **Step 4: Commit**

```bash
git add client/src/pages/config/sections/
git commit -m "perf(config): add memoization to section components"
```

---

## 7. 测试策略

### 单元测试

```typescript
// __tests__/ConfigSection.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { IntegrationConfig } from '../pages/config/sections/IntegrationConfig';

describe('IntegrationConfig', () => {
  it('renders all integration sections', () => {
    render(<IntegrationConfig config={{}} onChange={jest.fn()} onSave={jest.fn()} />);
    
    expect(screen.getByText('闲管家配置')).toBeInTheDocument();
    expect(screen.getByText('AI配置')).toBeInTheDocument();
  });
  
  it('handles connection test', async () => {
    const onSave = jest.fn();
    render(<IntegrationConfig config={{}} onChange={jest.fn()} onSave={onSave} />);
    
    fireEvent.click(screen.getByText('测试连接'));
    
    await waitFor(() => {
      expect(screen.getByText(/连接/)).toBeInTheDocument();
    });
  });
});
```

### 集成测试

```typescript
// __tests__/config-flow.test.tsx
describe('Config Flow', () => {
  it('navigates between config sections', async () => {
    render(<App />);
    
    // 访问配置页
    await userEvent.click(screen.getByText('配置'));
    
    // 点击集成服务
    await userEvent.click(screen.getByText('集成服务'));
    
    // 验证 URL 变化
    expect(window.location.pathname).toBe('/config/integrations');
  });
});
```

### E2E 测试场景

1. **快速设置流程**: 访问 `/config/overview`，点击各个快速设置卡片，验证正确导航
2. **配置保存**: 在每个配置页面修改配置，保存后刷新验证持久化
3. **向导流程**: 清除数据，验证新向导3步流程正常工作
4. **旧链接兼容**: 访问旧链接 `/config?tab=integrations`，验证正确跳转

---

## 8. 回滚计划

如果重构过程中出现严重问题：

1. **代码回滚**: 
   ```bash
   git log --oneline -10  # 找到重构前的 commit
   git revert <commit-hash>..HEAD  # 回滚到重构前
   ```

2. **路由回滚**: 恢复 App.tsx 中的原始路由配置

3. **数据回滚**: 配置数据结构保持不变，无需数据迁移

---

## 9. 检查清单

### 实施前
- [ ] 备份当前代码 `git branch backup/pre-config-refactor`
- [ ] 确保所有测试通过 `npm test`
- [ ] 通知团队成员重构计划

### 实施后
- [ ] 所有新路由可访问
- [ ] 配置保存/加载正常工作
- [ ] 向导流程完整测试
- [ ] 旧链接兼容性验证
- [ ] 性能无显著下降
- [ ] 文档更新 (如有需要)

---

## 附录: 文件变更汇总

### 新增文件 (约 20 个)
```
client/src/pages/config/
├── ConfigLayout.tsx
├── ConfigOverview.tsx
├── constants/
│   ├── categoryDefaults.ts
│   ├── pricingPresets.ts
│   ├── aiProviders.ts
│   └── configCategories.ts
├── sections/
│   ├── IntegrationConfig.tsx
│   ├── AutoReplyConfig.tsx
│   ├── OrderConfig.tsx
│   ├── ProductConfig.tsx
│   └── NotificationConfig.tsx
├── components/
│   ├── ConfigSection.tsx
│   ├── ConfigField.tsx
│   ├── QuickSettingCard.tsx
│   ├── SectionNav.tsx
│   └── ToggleField.tsx
└── hooks/
    └── useConfig.ts

client/src/components/wizard/
├── QuickSetupWizard.tsx
├── WizardLayout.tsx
└── steps/
    ├── StepQuickStart.tsx
    ├── StepNotifications.tsx
    └── StepReview.tsx
```

### 修改文件 (约 3 个)
```
client/src/App.tsx (路由更新)
client/src/pages/config/SystemConfig.tsx (精简为兼容性层)
```

### 删除文件 (最终)
```
client/src/components/SetupWizard.tsx (由 QuickSetupWizard 替代)
```

---

## 相关文档

- [Design System](./xianyu-theme.css)
- [API 文档](./docs/API.md)
- [配置规范](./config/config.yaml)
