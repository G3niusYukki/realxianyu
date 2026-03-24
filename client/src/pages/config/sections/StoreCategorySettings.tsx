import React, { useState, useEffect } from 'react';
import { Save, RefreshCw, Store, ArrowRight, CheckCircle2 } from 'lucide-react';
import { getSystemConfig, saveSystemConfig } from '../../../api/config';
import { useStoreCategory, CATEGORY_META } from '../../../contexts/StoreCategoryContext';
import { CATEGORY_DEFAULTS } from '../constants';
import toast from 'react-hot-toast';

interface ConfigSectionProps {
  config: Record<string, any>;
  onChange: (sectionKey: string, fieldKey: string, value: any) => void;
  onSave: () => Promise<void>;
  saving: boolean;
  isDirty: boolean;
}

function StoreCategoryConfig({ config, onChange, onSave, saving, isDirty }: ConfigSectionProps) {
  const { category, switchCategory } = useStoreCategory();
  const [showApplyModal, setShowApplyModal] = useState(false);
  const [targetCategory, setTargetCategory] = useState('');

  const handleCategoryClick = (cat: string) => {
    if (cat === category) return;
    setTargetCategory(cat);
    setShowApplyModal(true);
  };

  const applyCategoryDefaults = async () => {
    const defaults = CATEGORY_DEFAULTS[targetCategory] || CATEGORY_DEFAULTS.express;
    onChange('auto_reply', 'default_reply', defaults.auto_reply.default_reply);
    onChange('auto_reply', 'virtual_default_reply', defaults.auto_reply.virtual_default_reply);
    onChange('auto_reply', 'ai_intent_enabled', defaults.auto_reply.ai_intent_enabled);
    onChange('auto_reply', 'enabled', defaults.auto_reply.enabled);
    onChange('pricing', 'auto_adjust', defaults.pricing.auto_adjust);
    onChange('pricing', 'min_margin_percent', defaults.pricing.min_margin_percent);
    onChange('pricing', 'max_discount_percent', defaults.pricing.max_discount_percent);
    onChange('delivery', 'auto_delivery', defaults.delivery.auto_delivery);
    onChange('delivery', 'delivery_timeout_minutes', defaults.delivery.delivery_timeout_minutes);
    
    await switchCategory(targetCategory);
    setShowApplyModal(false);
    toast.success(`已切换到 ${CATEGORY_META[targetCategory]?.label} 并应用默认配置`);
  };

  const switchOnly = async () => {
    await switchCategory(targetCategory);
    setShowApplyModal(false);
    toast.success(`已切换到 ${CATEGORY_META[targetCategory]?.label}`);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-xy-text-primary">店铺品类</h2>
          <p className="text-xy-text-secondary text-sm mt-1">选择主营品类，系统自动适配功能和话术模板</p>
        </div>
        <button
          onClick={onSave}
          disabled={!isDirty || saving}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
            isDirty 
              ? 'bg-xy-primary text-white hover:bg-xy-primary/90' 
              : 'bg-gray-100 text-gray-400 cursor-not-allowed'
          }`}
        >
          {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
          {saving ? '保存中...' : '保存配置'}
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {Object.entries(CATEGORY_META).map(([key, meta]) => (
          <button
            key={key}
            onClick={() => handleCategoryClick(key)}
            className={`text-left p-4 rounded-xl border-2 transition-all ${
              category === key
                ? 'border-xy-primary bg-orange-50 ring-2 ring-xy-primary/20'
                : 'border-xy-border hover:border-xy-primary/50 hover:bg-gray-50'
            }`}
          >
            <div className="flex items-center gap-3 mb-2">
              <span className="text-2xl">{meta.icon}</span>
              <span className="font-bold text-xy-text-primary">{meta.label}</span>
              {category === key && (
                <span className="ml-auto text-xs font-medium text-xy-primary bg-xy-primary/10 px-2 py-0.5 rounded-full">
                  当前
                </span>
              )}
            </div>
            <p className="text-sm text-xy-text-secondary">{meta.desc}</p>
          </button>
        ))}
      </div>

      <div className="p-4 bg-blue-50 rounded-xl border border-blue-200">
        <p className="text-sm text-blue-700">
          切换品类后可选择是否自动应用推荐的回复话术、定价和发货规则。
          已有的精细化配置（报价引擎、意图规则等）不受影响。
        </p>
      </div>

      {showApplyModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-xy-text-primary mb-2">
              切换至 {CATEGORY_META[targetCategory]?.label}
            </h3>
            <p className="text-xy-text-secondary mb-4">
              是否同时应用 {CATEGORY_META[targetCategory]?.label} 的默认配置？
            </p>
            
            <div className="bg-gray-50 rounded-lg p-3 mb-4 text-sm text-gray-600">
              <p>将应用：</p>
              <ul className="list-disc list-inside mt-1 space-y-1">
                <li>自动回复话术</li>
                <li>定价策略</li>
                <li>发货规则</li>
              </ul>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setShowApplyModal(false)}
                className="flex-1 px-4 py-2 border border-xy-border rounded-lg font-medium hover:bg-gray-50"
              >
                取消
              </button>
              <button
                onClick={switchOnly}
                className="flex-1 px-4 py-2 border border-xy-border rounded-lg font-medium hover:bg-gray-50"
              >
                仅切换
              </button>
              <button
                onClick={applyCategoryDefaults}
                className="flex-1 px-4 py-2 bg-xy-primary text-white rounded-lg font-medium hover:bg-xy-primary/90"
              >
                切换并应用
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function StoreCategorySettings() {
  const [config, setConfig] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [isDirty, setIsDirty] = useState(false);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const res = await getSystemConfig();
      if (res.data?.ok) {
        setConfig(res.data.config || {});
      }
    } catch {
      toast.error('加载配置失败');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (sectionKey: string, fieldKey: string, value: any) => {
    setConfig(prev => ({
      ...prev,
      [sectionKey]: { ...(prev[sectionKey] || {}), [fieldKey]: value },
    }));
    setIsDirty(true);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const currentRes = await getSystemConfig();
      const currentConfig = currentRes.data?.config || {};

      const configToSave = {
        ...currentConfig,
        store: config.store,
      };

      const res = await saveSystemConfig(configToSave);
      if (res.data?.ok) {
        toast.success('保存成功');
        setIsDirty(false);
        setConfig(configToSave);
      } else {
        toast.error(res.data?.error || '保存失败');
      }
    } catch {
      toast.error('保存出错');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="p-6">加载中...</div>;
  }

  return (
    <StoreCategoryConfig
      config={config}
      onChange={handleChange}
      onSave={handleSave}
      saving={saving}
      isDirty={isDirty}
    />
  );
}
