import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ChevronRight, ChevronLeft, Check, Cookie, Bot, Settings, 
  Store, Bell, Sparkles, ExternalLink 
} from 'lucide-react';
import { saveSystemConfig } from '../api/config';

import { CATEGORY_DEFAULTS } from '../pages/config/constants';
import toast from 'react-hot-toast';

interface WizardStep {
  key: string;
  label: string;
  icon: React.ElementType;
}

const STEPS: WizardStep[] = [
  { key: 'essentials', label: '核心配置', icon: Sparkles },
  { key: 'notifications', label: '告警通知', icon: Bell },
  { key: 'complete', label: '完成', icon: Check },
];

interface WizardData {
  cookie: string;
  aiProvider: string;
  aiApiKey: string;
  xgjAppKey: string;
  xgjAppSecret: string;
  storeCategory: string;
  feishuWebhook: string;
}

const AI_PROVIDERS = [
  { id: 'deepseek', name: 'DeepSeek', model: 'deepseek-chat', base_url: 'https://api.deepseek.com/v1' },
  { id: 'qwen', name: '百炼千问', model: 'qwen-plus-latest', base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1' },
];

const DEFAULT_DATA: WizardData = {
  cookie: '',
  aiProvider: 'deepseek',
  aiApiKey: '',
  xgjAppKey: '',
  xgjAppSecret: '',
  storeCategory: 'express',
  feishuWebhook: '',
};

export default function QuickSetupWizard() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [data, setData] = useState<WizardData>(DEFAULT_DATA);
  const [saving, setSaving] = useState(false);

  const updateData = (updates: Partial<WizardData>) => {
    setData(prev => ({ ...prev, ...updates }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const categoryDefaults = CATEGORY_DEFAULTS[data.storeCategory] || CATEGORY_DEFAULTS.express;
      
      const config = {
        accounts: [{
          id: 'account_1',
          name: '主账号',
          cookie: data.cookie,
          priority: 1,
          enabled: true,
        }],
        default_account: 'account_1',
        ai: {
          provider: data.aiProvider,
          api_key: data.aiApiKey,
          model: AI_PROVIDERS.find(p => p.id === data.aiProvider)?.model || 'deepseek-chat',
          base_url: AI_PROVIDERS.find(p => p.id === data.aiProvider)?.base_url || 'https://api.deepseek.com/v1',
          temperature: 0.7,
          max_tokens: 1000,
        },
        xianguanjia: {
          app_key: data.xgjAppKey,
          app_secret: data.xgjAppSecret,
          base_url: 'https://open.goofish.pro',
          mode: 'self_developed',
        },
        auto_reply: {
          default_reply: categoryDefaults.auto_reply.default_reply,
          virtual_default_reply: categoryDefaults.auto_reply.virtual_default_reply,
          ai_intent_enabled: categoryDefaults.auto_reply.ai_intent_enabled,
          enabled: categoryDefaults.auto_reply.enabled,
        },
        notifications: {
          feishu_enabled: !!data.feishuWebhook,
          feishu_webhook: data.feishuWebhook,
        },
        store: {
          category: data.storeCategory,
        },
      };

      const res = await saveSystemConfig(config);
      if (res.data?.ok) {
        toast.success('配置保存成功');
        setCurrentStep(2);
      } else {
        toast.error(res.data?.error || '保存失败');
      }
    } catch {
      toast.error('保存出错');
    } finally {
      setSaving(false);
    }
  };

  const canProceed = () => {
    if (currentStep === 0) {
      return data.cookie && data.aiApiKey && data.xgjAppKey && data.xgjAppSecret;
    }
    return true;
  };

  const renderStep = () => {
    switch (currentStep) {
      case 0:
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-xy-text-primary mb-2">核心配置</h2>
              <p className="text-xy-text-secondary">配置系统运行所需的基本信息</p>
            </div>

            <div className="space-y-4">
              <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Cookie className="w-5 h-5 text-orange-600" />
                  <span className="font-semibold text-orange-900">闲鱼 Cookie</span>
                </div>
                <textarea
                  value={data.cookie}
                  onChange={(e) => updateData({ cookie: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 border border-orange-200 rounded-lg text-sm font-mono resize-none"
                  placeholder="_tb_token_=xxx; cookie2=xxx; ..."
                />
                <p className="text-xs text-orange-700 mt-2">
                  从浏览器 F12 开发者工具中复制 Cookie
                </p>
              </div>

              <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Bot className="w-5 h-5 text-purple-600" />
                  <span className="font-semibold text-purple-900">AI 服务</span>
                </div>
                <div className="grid grid-cols-2 gap-3 mb-3">
                  <select
                    value={data.aiProvider}
                    onChange={(e) => updateData({ aiProvider: e.target.value })}
                    className="px-3 py-2 border border-purple-200 rounded-lg text-sm"
                  >
                    {AI_PROVIDERS.map(p => (
                      <option key={p.id} value={p.id}>{p.name}</option>
                    ))}
                  </select>
                  <input
                    type="password"
                    value={data.aiApiKey}
                    onChange={(e) => updateData({ aiApiKey: e.target.value })}
                    placeholder="API Key"
                    className="px-3 py-2 border border-purple-200 rounded-lg text-sm"
                  />
                </div>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Settings className="w-5 h-5 text-blue-600" />
                  <span className="font-semibold text-blue-900">闲管家</span>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <input
                    type="text"
                    value={data.xgjAppKey}
                    onChange={(e) => updateData({ xgjAppKey: e.target.value })}
                    placeholder="App Key"
                    className="px-3 py-2 border border-blue-200 rounded-lg text-sm"
                  />
                  <input
                    type="password"
                    value={data.xgjAppSecret}
                    onChange={(e) => updateData({ xgjAppSecret: e.target.value })}
                    placeholder="App Secret"
                    className="px-3 py-2 border border-blue-200 rounded-lg text-sm"
                  />
                </div>
              </div>

              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Store className="w-5 h-5 text-green-600" />
                  <span className="font-semibold text-green-900">店铺品类</span>
                </div>
                <select
                  value={data.storeCategory}
                  onChange={(e) => updateData({ storeCategory: e.target.value })}
                  className="w-full px-3 py-2 border border-green-200 rounded-lg text-sm"
                >
                  <option value="express">快递代发</option>
                  <option value="exchange">兑换码/卡密</option>
                  <option value="recharge">充值代充</option>
                  <option value="movie_ticket">电影票代购</option>
                  <option value="account">账号交易</option>
                  <option value="game">游戏道具</option>
                </select>
              </div>
            </div>
          </div>
        );

      case 1:
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-xy-text-primary mb-2">告警通知（可选）</h2>
              <p className="text-xy-text-secondary">配置异常告警通知，随时掌握系统状态</p>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <Bell className="w-5 h-5 text-blue-600" />
                <span className="font-semibold text-blue-900">飞书 webhook</span>
              </div>
              <input
                type="text"
                value={data.feishuWebhook}
                onChange={(e) => updateData({ feishuWebhook: e.target.value })}
                placeholder="https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
                className="w-full px-3 py-2 border border-blue-200 rounded-lg text-sm"
              />
              <p className="text-xs text-blue-700 mt-2">
                留空则不启用告警通知
              </p>
            </div>

            <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-600">
              <p>配置完成后，系统将在以下情况发送告警：</p>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>Cookie 过期或失效</li>
                <li>订单处理异常</li>
                <li>发货失败</li>
                <li>需要人工介入</li>
              </ul>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="text-center py-12">
            <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <Check className="w-10 h-10 text-green-600" />
            </div>
            <h2 className="text-2xl font-bold text-xy-text-primary mb-4">配置完成！</h2>
            <p className="text-xy-text-secondary mb-8 max-w-md mx-auto">
              系统已配置完成，将自动应用您设置的品类话术和业务规则。
            </p>

            <div className="flex justify-center gap-4">
              <button
                onClick={() => navigate('/dashboard')}
                className="flex items-center gap-2 px-6 py-3 bg-xy-primary text-white rounded-lg font-medium hover:bg-xy-primary/90 transition-colors"
              >
                进入工作台
                <ExternalLink className="w-4 h-4" />
              </button>
              <button
                onClick={() => navigate('/config')}
                className="px-6 py-3 border border-xy-border rounded-lg font-medium hover:bg-gray-50 transition-colors"
              >
                详细配置
              </button>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-xy-bg py-8">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-xl border border-xy-border shadow-sm overflow-hidden">
          <div className="bg-gradient-to-r from-xy-primary to-xy-primary/80 px-6 py-8 text-white">
            <h1 className="text-2xl font-bold mb-2">快速设置向导</h1>
            <p className="text-white/80">只需几步，即可完成系统基础配置</p>
          </div>

          <div className="px-6 py-4 border-b border-xy-border bg-gray-50">
            <div className="flex items-center justify-between">
              {STEPS.map((step, index) => {
                const Icon = step.icon;
                const isActive = index === currentStep;
                const isCompleted = index < currentStep;
                
                return (
                  <div key={step.key} className="flex items-center">
                    <div
                      className={`flex items-center gap-2 px-3 py-2 rounded-lg ${
                        isActive 
                          ? 'bg-xy-primary text-white' 
                          : isCompleted 
                            ? 'bg-green-100 text-green-700' 
                            : 'bg-gray-100 text-gray-500'
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                      <span className="text-sm font-medium">{step.label}</span>
                    </div>
                    {index < STEPS.length - 1 && (
                      <ChevronRight className="w-4 h-4 text-gray-300 mx-2" />
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          <div className="p-6">
            {renderStep()}
          </div>

          {currentStep < 2 && (
            <div className="px-6 py-4 border-t border-xy-border bg-gray-50 flex justify-between">
              <button
                onClick={() => setCurrentStep(prev => prev - 1)}
                disabled={currentStep === 0}
                className="flex items-center gap-2 px-4 py-2 rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-200 transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
                上一步
              </button>
              
              {currentStep === 1 ? (
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="flex items-center gap-2 px-6 py-2 bg-xy-primary text-white rounded-lg font-medium hover:bg-xy-primary/90 transition-colors disabled:opacity-50"
                >
                  {saving ? (
                    <>保存中...</>
                  ) : (
                    <>
                      完成配置
                      <Check className="w-4 h-4" />
                    </>
                  )}
                </button>
              ) : (
                <button
                  onClick={() => setCurrentStep(prev => prev + 1)}
                  disabled={!canProceed()}
                  className="flex items-center gap-2 px-4 py-2 bg-xy-primary text-white rounded-lg font-medium hover:bg-xy-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  下一步
                  <ChevronRight className="w-4 h-4" />
              </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
