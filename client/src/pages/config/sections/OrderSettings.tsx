import React, { useState, useEffect } from 'react';
import { Save, RefreshCw, Receipt, DollarSign, Truck, Package, TrendingUp } from 'lucide-react';
import { getSystemConfig, saveSystemConfig } from '../../../api/config';
import { useStoreCategory } from '../../../contexts/StoreCategoryContext';
import { CATEGORY_DEFAULTS, PRICING_PRESETS } from '../constants';
import toast from 'react-hot-toast';

interface ConfigSectionProps {
  config: Record<string, any>;
  onChange: (sectionKey: string, fieldKey: string, value: any) => void;
  onSave: () => Promise<void>;
  saving: boolean;
  isDirty: boolean;
}

function ToggleSwitch({ checked, onChange }: { checked: boolean; onChange: () => void }) {
  return (
    <button
      onClick={onChange}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
        checked ? 'bg-xy-primary' : 'bg-gray-200'
      }`}
    >
      <span
        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
          checked ? 'translate-x-6' : 'translate-x-1'
        }`}
      />
    </button>
  );
}

function OrderConfig({ config, onChange, onSave, saving, isDirty }: ConfigSectionProps) {
  const { category } = useStoreCategory();
  const defaults = CATEGORY_DEFAULTS[category] || CATEGORY_DEFAULTS.express;
  const pricing = config.pricing || {};
  const delivery = config.delivery || {};
  const orderReminder = config.order_reminder || {};
  const autoPriceModify = config.auto_price_modify || {};

  const applyPricingPreset = (presetKey: string) => {
    const preset = PRICING_PRESETS[presetKey];
    if (preset) {
      onChange('pricing', 'auto_adjust', preset.auto_adjust);
      onChange('pricing', 'min_margin_percent', preset.min_margin_percent);
      onChange('pricing', 'max_discount_percent', preset.max_discount_percent);
      toast.success(`已应用${preset.label}方案`);
    }
  };

  const isPresetActive = (presetKey: string) => {
    const preset = PRICING_PRESETS[presetKey];
    return (
      pricing.min_margin_percent === preset.min_margin_percent &&
      pricing.max_discount_percent === preset.max_discount_percent &&
      !!pricing.auto_adjust === preset.auto_adjust
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-xy-text-primary">订单管理配置</h2>
          <p className="text-xy-text-secondary text-sm mt-1">配置定价策略、发货规则和订单提醒</p>
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

      <div className="grid gap-6">
        <div className="bg-white rounded-xl border border-xy-border p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-green-100 rounded-lg">
              <DollarSign className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <h3 className="font-semibold text-xy-text-primary">定价策略</h3>
              <p className="text-sm text-xy-text-secondary">设置自动调价和利润保护规则</p>
            </div>
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-xy-text-primary mb-3">快速选择定价方案</label>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {Object.entries(PRICING_PRESETS).map(([key, preset]) => (
                <button
                  key={key}
                  onClick={() => applyPricingPreset(key)}
                  className={`p-3 rounded-lg border text-left transition-all ${
                    isPresetActive(key)
                      ? 'border-xy-primary bg-xy-primary/5 ring-1 ring-xy-primary'
                      : 'border-xy-border hover:border-xy-primary/50'
                  }`}
                >
                  <div className="font-medium text-xy-text-primary">{preset.label}</div>
                  <div className="text-xs text-xy-text-secondary mt-1">{preset.desc}</div>
                  <div className="flex gap-2 mt-2 text-xs">
                    <span className="px-1.5 py-0.5 bg-gray-100 rounded">利润{preset.min_margin_percent}%</span>
                    <span className="px-1.5 py-0.5 bg-gray-100 rounded">降幅{preset.max_discount_percent}%</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-xy-border">
            <div className="flex items-center justify-between">
              <div>
                <label className="font-medium text-xy-text-primary">自动调价</label>
                <p className="text-sm text-xy-text-secondary">根据市场自动调整售价</p>
              </div>
              <ToggleSwitch 
                checked={!!pricing.auto_adjust} 
                onChange={() => onChange('pricing', 'auto_adjust', !pricing.auto_adjust)} 
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-xy-text-primary mb-1">最低利润率 (%)</label>
              <input
                type="number"
                value={pricing.min_margin_percent ?? 10}
                onChange={(e) => onChange('pricing', 'min_margin_percent', Number(e.target.value))}
                className="w-full px-3 py-2 border border-xy-border rounded-lg focus:outline-none focus:ring-2 focus:ring-xy-primary/20 focus:border-xy-primary"
                min={0}
                max={100}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-xy-text-primary mb-1">最大降价幅度 (%)</label>
              <input
                type="number"
                value={pricing.max_discount_percent ?? 20}
                onChange={(e) => onChange('pricing', 'max_discount_percent', Number(e.target.value))}
                className="w-full px-3 py-2 border border-xy-border rounded-lg focus:outline-none focus:ring-2 focus:ring-xy-primary/20 focus:border-xy-primary"
                min={0}
                max={100}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-xy-text-primary mb-1">安全边距 (%)</label>
              <input
                type="number"
                value={pricing.safety_margin_percent ?? 0}
                onChange={(e) => onChange('pricing', 'safety_margin_percent', Number(e.target.value))}
                className="w-full px-3 py-2 border border-xy-border rounded-lg focus:outline-none focus:ring-2 focus:ring-xy-primary/20 focus:border-xy-primary"
                min={0}
                max={50}
              />
              <p className="text-xs text-xy-text-secondary mt-1">额外保留的利润空间</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-xy-border p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Truck className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <h3 className="font-semibold text-xy-text-primary">自动发货</h3>
                <p className="text-sm text-xy-text-secondary">虚拟商品自动发货设置</p>
              </div>
            </div>
            <ToggleSwitch 
              checked={delivery.auto_delivery !== false} 
              onChange={() => onChange('delivery', 'auto_delivery', !(delivery.auto_delivery !== false))} 
            />
          </div>

          {delivery.auto_delivery !== false && (
            <div className="mt-4 pt-4 border-t border-xy-border">
              <label className="block text-sm font-medium text-xy-text-primary mb-1">发货超时时间（分钟）</label>
              <input
                type="number"
                value={delivery.delivery_timeout_minutes ?? 30}
                onChange={(e) => onChange('delivery', 'delivery_timeout_minutes', Number(e.target.value))}
                className="w-full px-3 py-2 border border-xy-border rounded-lg focus:outline-none focus:ring-2 focus:ring-xy-primary/20 focus:border-xy-primary"
                min={1}
                max={1440}
              />
              <p className="text-xs text-xy-text-secondary mt-1">超过此时间未发货将触发告警</p>
            </div>
          )}
        </div>

        <div className="bg-white rounded-xl border border-xy-border p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-100 rounded-lg">
                <Receipt className="w-5 h-5 text-orange-600" />
              </div>
              <div>
                <h3 className="font-semibold text-xy-text-primary">订单催单提醒</h3>
                <p className="text-sm text-xy-text-secondary">自动提醒未处理订单</p>
              </div>
            </div>
            <ToggleSwitch 
              checked={orderReminder.enabled !== false} 
              onChange={() => onChange('order_reminder', 'enabled', !(orderReminder.enabled !== false))} 
            />
          </div>

          {orderReminder.enabled !== false && (
            <div className="mt-4 pt-4 border-t border-xy-border grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-xy-text-primary mb-1">每日最大提醒次数</label>
                <input
                  type="number"
                  value={orderReminder.max_daily ?? 2}
                  onChange={(e) => onChange('order_reminder', 'max_daily', Number(e.target.value))}
                  className="w-full px-3 py-2 border border-xy-border rounded-lg focus:outline-none focus:ring-2 focus:ring-xy-primary/20 focus:border-xy-primary"
                  min={1}
                  max={10}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-xy-text-primary mb-1">提醒间隔（分钟）</label>
                <input
                  type="number"
                  value={orderReminder.interval_minutes ?? 30}
                  onChange={(e) => onChange('order_reminder', 'interval_minutes', Number(e.target.value))}
                  className="w-full px-3 py-2 border border-xy-border rounded-lg focus:outline-none focus:ring-2 focus:ring-xy-primary/20 focus:border-xy-primary"
                  min={5}
                  max={240}
                />
              </div>
            </div>
          )}
        </div>

        <div className="bg-white rounded-xl border border-xy-border p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <TrendingUp className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <h3 className="font-semibold text-xy-text-primary">自动改价</h3>
                <p className="text-sm text-xy-text-secondary">买家拍下后自动修改价格</p>
              </div>
            </div>
            <ToggleSwitch 
              checked={!!autoPriceModify.enabled} 
              onChange={() => onChange('auto_price_modify', 'enabled', !autoPriceModify.enabled)} 
            />
          </div>

          {autoPriceModify.enabled && (
            <div className="mt-4 p-4 bg-purple-50 rounded-lg">
              <p className="text-sm text-purple-800">
                自动改价已启用。系统将根据报价引擎计算的价格自动修改订单金额。
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function OrderSettings() {
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
      const res = await saveSystemConfig(config);
      if (res.data?.ok) {
        toast.success('保存成功');
        setIsDirty(false);
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
    <OrderConfig
      config={config}
      onChange={handleChange}
      onSave={handleSave}
      saving={saving}
      isDirty={isDirty}
    />
  );
}
