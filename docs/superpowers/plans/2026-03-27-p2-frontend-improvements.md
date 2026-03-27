# P2: 前端 React 代码改进 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 提升 TypeScript 类型安全、消除代码重复、优化性能（代码分割和 memo）、引入前端工程化工具。

**Architecture:** 渐进式改进，不改变 UI 功能。每个 Task 独立可验证。

**Tech Stack:** React 18, TypeScript 5, Vite 5, Tailwind CSS 3

---

## Task 1: 开启 TypeScript strict 模式（渐进式）

**Files:**
- Modify: `client/tsconfig.json`
- Modify: `client/src/pages/Orders.tsx` (修复 any 类型)
- Modify: `client/src/pages/Dashboard.tsx` (修复 any 类型)
- Modify: `client/src/api/accounts.ts` (添加接口定义)
- Modify: `client/src/api/xianguanjia.ts` (添加接口定义)

**问题：** `tsconfig.json` 设置 `"strict": false`，禁用了所有类型安全检查。多个组件大量使用 `any`。

- [ ] **Step 1: 为 api/accounts.ts 添加类型定义**

```typescript
// client/src/api/accounts.ts
import api from './index'

export interface CookieAccount {
  id: string
  label: string
  status: 'valid' | 'expired' | 'unknown'
  last_checked: string | null
  source: string
  risk_level: 'low' | 'medium' | 'high'
}

export interface AccountListResponse {
  accounts: CookieAccount[]
  total: number
}

export async function getAccounts(): Promise<AccountListResponse> {
  const res = await api.get('/api/accounts')
  return res.data
}
```

- [ ] **Step 2: 为 api/xianguanjia.ts 添加类型定义**

为产品、订单等核心数据结构定义接口，替换所有 `Promise<AxiosResponse>` 返回类型。

- [ ] **Step 3: 逐步启用 strict 模式**

```json
// tsconfig.json — 先启用最关键的两个:
{
  "compilerOptions": {
    "strict": false,
    "strictNullChecks": true,
    "noImplicitAny": true,
    ...
  }
}
```

这会暴露现有的类型错误。逐文件修复 `any` 类型和 null 检查问题。

- [ ] **Step 4: 修复编译错误，运行构建确认**

Run: `cd client && npx tsc --noEmit`
然后修复所有报错。

- [ ] **Step 5: 提交**

```bash
git add client/tsconfig.json client/src/api/ client/src/pages/Orders.tsx client/src/pages/Dashboard.tsx
git commit -m "refactor(frontend): enable strictNullChecks + noImplicitAny, add type definitions"
```

---

## Task 2: 提取共享组件和工具函数

**Files:**
- Create: `client/src/components/CollapsibleSection.tsx`
- Create: `client/src/utils/format.ts`
- Create: `client/src/hooks/useAsyncData.ts`
- Modify: `client/src/pages/accounts/AccountList.tsx` (删除本地 CollapsibleSection)
- Modify: `client/src/pages/config/SystemConfig.tsx` (删除本地 CollapsibleSection)
- Modify: `client/src/pages/Orders.tsx` (使用共享 formatPrice)
- Modify: `client/src/pages/products/ProductList.tsx` (使用共享 formatPrice)

**问题：** `CollapsibleSection` 在 2 个文件重复；`formatPrice` 在 2 个文件重复；loading/error 状态模式在所有页面重复。

- [ ] **Step 1: 提取 CollapsibleSection**

从 `AccountList.tsx` 或 `SystemConfig.tsx` 中提取较为完整的那一个，创建 `client/src/components/CollapsibleSection.tsx`：

```tsx
import { useState, type ReactNode } from 'react'

interface Props {
  title: string
  defaultOpen?: boolean
  children: ReactNode
}

export default function CollapsibleSection({ title, defaultOpen = false, children }: Props) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="border rounded-lg">
      <button
        className="w-full flex items-center justify-between p-3 hover:bg-gray-50"
        onClick={() => setOpen(!open)}
      >
        <span className="font-medium">{title}</span>
        <span className={`transform transition-transform ${open ? 'rotate-180' : ''}`}>
          ▼
        </span>
      </button>
      {open && <div className="p-3 border-t">{children}</div>}
    </div>
  )
}
```

- [ ] **Step 2: 提取 formatPrice**

创建 `client/src/utils/format.ts`：

```typescript
export function formatPrice(price: number | string | null | undefined): string {
  const num = Number(price)
  if (isNaN(num) || price === null || price === undefined) return '—'
  return `¥${num.toFixed(2)}`
}
```

- [ ] **Step 3: 提取 useAsyncData hook**

创建 `client/src/hooks/useAsyncData.ts`：

```typescript
import { useState, useEffect, useCallback } from 'react'

interface State<T> {
  data: T | null
  loading: boolean
  error: string | null
}

export function useAsyncData<T>(
  fetcher: () => Promise<T>,
  deps: unknown[] = [],
): State<T> & { refresh: () => void } {
  const [state, setState] = useState<State<T>>({ data: null, loading: true, error: null })

  const fetchData = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }))
    try {
      const data = await fetcher()
      setState({ data, loading: false, error: null })
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '加载失败'
      setState(prev => ({ ...prev, loading: false, error: message }))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  useEffect(() => { fetchData() }, [fetchData])

  return { ...state, refresh: fetchData }
}
```

- [ ] **Step 4: 替换所有消费方**

- `AccountList.tsx` 和 `SystemConfig.tsx`: 删除本地 `CollapsibleSection`，import 共享组件
- `Orders.tsx` 和 `ProductList.tsx`: 删除本地 `formatPrice`，import 共享函数
- 逐步在各页面中使用 `useAsyncData` 替换手动的 loading/error 状态

- [ ] **Step 5: 运行构建确认**

Run: `cd client && npm run build`

- [ ] **Step 6: 提交**

```bash
git add client/src/components/CollapsibleSection.tsx client/src/utils/format.ts client/src/hooks/useAsyncData.ts client/src/pages/
git commit -m "refactor(frontend): extract shared CollapsibleSection, formatPrice, useAsyncData"
```

---

## Task 3: 添加 React.lazy 代码分割

**Files:**
- Modify: `client/src/App.tsx`
- Modify: `client/vite.config.js`

**问题：** 所有路由同步加载，包括 ~2MB 的 Monaco Editor。无代码分割。

- [ ] **Step 1: 在 App.tsx 中使用 React.lazy**

```tsx
import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Navbar from './components/Navbar'
import ErrorBoundary from './components/ErrorBoundary'

// Lazy load all page components
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Orders = lazy(() => import('./pages/Orders'))
const Messages = lazy(() => import('./pages/Messages'))
const ProductList = lazy(() => import('./pages/products/ProductList'))
const AutoPublish = lazy(() => import('./pages/products/AutoPublish'))
const AccountList = lazy(() => import('./pages/accounts/AccountList'))
const SystemConfig = lazy(() => import('./pages/config/SystemConfig'))
const LogTerminal = lazy(() => import('./pages/LogTerminal'))

function LoadingFallback() {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-xy-brand-500" />
    </div>
  )
}

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Navbar />
        <Suspense fallback={<LoadingFallback />}>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/orders" element={<Orders />} />
            <Route path="/messages" element={<Messages />} />
            <Route path="/products" element={<ProductList />} />
            <Route path="/auto-publish" element={<AutoPublish />} />
            <Route path="/accounts" element={<AccountList />} />
            <Route path="/config" element={<SystemConfig />} />
            <Route path="/logs" element={<LogTerminal />} />
            <Route path="/analytics" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </ErrorBoundary>
  )
}
```

- [ ] **Step 2: 在 vite.config.js 添加 manualChunks**

```javascript
// vite.config.js
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { '/api': 'http://localhost:8091' },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          'vendor-charts': ['recharts'],
          'vendor-editor': ['@monaco-editor/react'],
        },
      },
    },
  },
})
```

- [ ] **Step 3: 运行构建确认分包效果**

Run: `cd client && npm run build`
Expected: 产出多个 chunk 文件，Monaco 单独一个 chunk。

- [ ] **Step 4: 提交**

```bash
git add client/src/App.tsx client/vite.config.js
git commit -m "perf(frontend): add React.lazy code splitting and Vite manual chunks"
```

---

## Task 4: 删除死代码 — Analytics 页面

**Files:**
- Delete: `client/src/pages/analytics/Analytics.tsx`

**问题：** `Analytics.tsx` (145行) 被 App.tsx 路由重定向到 `/dashboard`，完全不可达。

- [ ] **Step 1: 删除文件并确认路由已重定向**

确认 `App.tsx` 中已有 `<Route path="/analytics" element={<Navigate to="/dashboard" replace />} />`。

- [ ] **Step 2: 删除 Analytics.tsx**

Run: `rm client/src/pages/analytics/Analytics.tsx`

如果 `analytics/` 目录为空，也删除目录。

- [ ] **Step 3: 运行构建确认**

Run: `cd client && npm run build`

- [ ] **Step 4: 提交**

```bash
git rm client/src/pages/analytics/Analytics.tsx
git commit -m "chore(frontend): remove unreachable Analytics page (dead code)"
```

---

## Task 5: 修复 API 错误处理的类型安全

**Files:**
- Modify: `client/src/api/index.ts`

**问题：** 错误拦截器使用 `(error as any).message = userMsg.msg` 来修改错误对象。

- [ ] **Step 1: 用自定义属性替代直接修改 error**

```typescript
// api/index.ts — 响应拦截器中:
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const userMsg = mapStatusToMessage(error.response?.status)
    // 不直接修改 error.message，而是附加自定义属性
    error.userMessage = userMsg.msg
    error.isUserFriendly = true
    return Promise.reject(error)
  }
)

// 消费方使用:
// toast.error(err.userMessage || err.message || '操作失败')
```

- [ ] **Step 2: 添加 AxiosError 类型扩展**

```typescript
// client/src/types/axios.d.ts
import 'axios'

declare module 'axios' {
  interface AxiosError {
    userMessage?: string
    isUserFriendly?: boolean
  }
}
```

- [ ] **Step 3: 运行构建确认**

Run: `cd client && npm run build`

- [ ] **Step 4: 提交**

```bash
git add client/src/api/index.ts client/src/types/
git commit -m "fix(frontend): type-safe error handling, avoid mutating AxiosError"
```

---

## Task 6: 配置 ESLint + Prettier

**Files:**
- Create: `client/.eslintrc.cjs`
- Create: `client/.prettierrc`
- Modify: `client/package.json` (添加 devDependencies 和 scripts)

- [ ] **Step 1: 安装依赖**

Run: `cd client && npm install -D eslint @eslint/js typescript-eslint eslint-plugin-react-hooks prettier`

- [ ] **Step 2: 创建 ESLint 配置**

```javascript
// client/.eslintrc.cjs
module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react-hooks/recommended',
  ],
  parser: '@typescript-eslint/parser',
  parserOptions: { ecmaVersion: 'latest', sourceType: 'module' },
  rules: {
    '@typescript-eslint/no-explicit-any': 'warn',
    '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
  },
}
```

- [ ] **Step 3: 创建 Prettier 配置**

```json
// client/.prettierrc
{
  "semi": false,
  "singleQuote": true,
  "trailingComma": "all",
  "printWidth": 100,
  "tabWidth": 2
}
```

- [ ] **Step 4: 添加 npm scripts**

```json
{
  "scripts": {
    "lint": "eslint src/",
    "lint:fix": "eslint src/ --fix",
    "format": "prettier --write 'src/**/*.{ts,tsx}'"
  }
}
```

- [ ] **Step 5: 运行 lint 查看当前状态**

Run: `cd client && npm run lint`

不要求立即修复所有问题，先建立基线。

- [ ] **Step 6: 提交**

```bash
git add client/.eslintrc.cjs client/.prettierrc client/package.json client/package-lock.json
git commit -m "chore(frontend): add ESLint + Prettier configuration"
```

---

## 完成标准

- [ ] TypeScript `strictNullChecks` + `noImplicitAny` 已启用
- [ ] 共享组件 (`CollapsibleSection`, `formatPrice`, `useAsyncData`) 已提取
- [ ] 路由级代码分割已实现（React.lazy + manual chunks）
- [ ] 死代码已清理
- [ ] API 错误处理类型安全
- [ ] ESLint + Prettier 已配置
- [ ] `npm run build` 成功，无 TypeScript 错误
