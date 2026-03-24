import React from 'react';
import { Link } from 'react-router-dom';
import { 
  Store, Plug, FileText, Receipt, Package, Bell,
  ChevronRight, CheckCircle2, AlertCircle 
} from 'lucide-react';
import { TAB_GROUPS } from '../constants';

interface ConfigCardProps {
  icon: React.ElementType;
  title: string;
  description: string;
  to: string;
  status?: 'configured' | 'pending' | 'optional';
}

function ConfigCard({ icon: Icon, title, description, to, status = 'optional' }: ConfigCardProps) {
  const statusColors = {
    configured: 'text-green-500',
    pending: 'text-yellow-500',
    optional: 'text-gray-400',
  };

  return (
    <Link
      to={to}
      className="block p-4 border border-xy-border rounded-lg hover:border-xy-primary hover:shadow-sm transition-all group"
    >
      <div className="flex items-start gap-3">
        <div className="p-2 bg-gray-50 rounded-lg group-hover:bg-xy-primary/10 transition-colors">
          <Icon className="w-5 h-5 text-xy-text-secondary group-hover:text-xy-primary" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <h3 className="font-medium text-xy-text-primary">{title}</h3>
            {status === 'configured' && <CheckCircle2 className={`w-4 h-4 ${statusColors[status]}`} />}
            {status === 'pending' && <AlertCircle className={`w-4 h-4 ${statusColors[status]}`} />}
          </div>
          <p className="text-sm text-xy-text-secondary mt-1">{description}</p>
        </div>
        <ChevronRight className="w-5 h-5 text-gray-300 group-hover:text-xy-primary transition-colors" />
      </div>
    </Link>
  );
}

export default function ConfigOverview() {
  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-xy-text-primary mb-2">配置概览</h2>
        <p className="text-xy-text-secondary">
          管理您的系统配置。点击卡片进入详细配置页面。
        </p>
      </div>

      <div className="space-y-6">
        {TAB_GROUPS.map((group) => (
          <div key={group.group}>
            <h3 className="text-sm font-semibold text-xy-text-secondary uppercase tracking-wide mb-3">
              {group.group}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {group.tabs.map((tab) => (
                <ConfigCard
                  key={tab.key}
                  icon={tab.icon}
                  title={tab.name}
                  description={getTabDescription(tab.key)}
                  to={`/config/${tab.key}`}
                  status={getTabStatus(tab.key)}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function getTabDescription(key: string): string {
  const descriptions: Record<string, string> = {
    store_category: '设置店铺主营品类，系统将自动适配对应的运营策略',
    integrations: '配置闲管家、AI服务、OSS等第三方集成',
    auto_reply: '设置自动回复话术、关键词匹配规则',
    orders: '配置订单定价、催单、改价、发货规则',
    products: '配置商品自动上架、库存管理策略',
    notifications: '设置飞书、企业微信告警通知',
  };
  return descriptions[key] || '';
}

function getTabStatus(key: string): 'configured' | 'pending' | 'optional' {
  const required = ['store_category', 'integrations'];
  return required.includes(key) ? 'pending' : 'optional';
}
