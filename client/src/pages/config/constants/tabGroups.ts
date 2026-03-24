import { Store, Plug, FileText, Receipt, Package, Bell } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

export interface TabInfo {
  key: string;
  name: string;
  icon: LucideIcon;
}

export interface TabGroup {
  group: string;
  tabs: TabInfo[];
}

export const TAB_GROUPS: TabGroup[] = [
  { 
    group: '基础设置', 
    tabs: [
      { key: 'store_category', name: '店铺品类', icon: Store },
      { key: 'integrations', name: '集成服务', icon: Plug },
    ]
  },
  { 
    group: '业务规则', 
    tabs: [
      { key: 'auto_reply', name: '自动回复', icon: FileText },
      { key: 'orders', name: '订单管理', icon: Receipt },
      { key: 'products', name: '商品运营', icon: Package },
    ]
  },
  { 
    group: '系统', 
    tabs: [
      { key: 'notifications', name: '告警通知', icon: Bell },
    ]
  },
];

export const ALL_TABS = TAB_GROUPS.flatMap(g => g.tabs);

export const TAB_COMPAT: Record<string, string> = {
  xianguanjia: 'integrations',
  ai: 'integrations',
  oss: 'integrations',
  cookie_cloud: 'integrations',
  auto_publish: 'products',
  order_reminder: 'orders',
  pricing: 'orders',
  delivery: 'orders',
  automation: 'orders',
  auto_price_modify: 'orders',
};

export const SECTION_LABELS: Record<string, string> = {
  store_category: '店铺品类',
  integrations: '集成服务',
  auto_reply: '自动回复',
  orders: '订单管理',
  products: '商品运营',
  notifications: '告警通知',
};
