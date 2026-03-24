import React, { useState, useEffect } from 'react';
import { Save, RefreshCw, Package, Store, TrendingUp, ArrowUpRight } from 'lucide-react';
import { getSystemConfig, saveSystemConfig } from '../../../api/config';
import { CATEGORY_META } from '../../../contexts/StoreCategoryContext';
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

function ProductConfig({ config, onChange, onSave, saving, isDirty }: ConfigSectionProps) {
  const autoPublish = config.auto_publish || {};

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-xy-text-primary">商品运营配置</h2>
          <p className="text-xy-text-secondary text-sm mt-1">自动上架策略和商品管理设置</p>
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

      <div className="bg-white rounded-xl border border-xy-border p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-emerald-100 rounded-lg">
              <Store className="w-5 h-5 text-emerald-600" />
            </div>
            <div>
              <h3 className="font-semibold text-xy-text-primary">自动上架</h3>
              <p className="text-sm text-xy-text-secondary">系统自动按策略上架和替换商品链接</p>
            </div>
          </div>
          <ToggleSwitch 
            checked={!!autoPublish.enabled} 
            onChange={() => onChange('auto_publish', 'enabled', !autoPublish.enabled)} 
          />
        </div>

        {autoPublish.enabled && (
          <>
            <div className="mb-6 p-4 bg-gradient-to-r from-emerald-50 to-blue-50 rounded-xl border border-emerald-200">
              <h4 className="text-sm font-bold text-xy-text-primary mb-3 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-emerald-500" />
                上架策略概览
              </h4>
              
              <div className="flex items-center gap-2 mb-3">
                <div className="flex-1 text-center">
                  <div className="bg-emerald-500 text-white text-xs font-bold py-2 px-3 rounded-l-lg">
                    D1 ~ D{autoPublish.cold_start_days ?? 2}
                  </div>
                  <p className="text-xs text-emerald-700 mt-1.5 font-medium">冷启动期</p>
                  <p className="text-[11px] text-emerald-600">每天新建 {autoPublish.cold_start_daily_count ?? 5} 条</p>
                </div>
                <div className="text-emerald-400 text-lg font-bold">→</div>
                <div className="flex-1 text-center">
                  <div className="bg-blue-500 text-white text-xs font-bold py-2 px-3 rounded-r-lg">
                    D{(autoPublish.cold_start_days ?? 2) + 1}+
                  </div>
                  <p className="text-xs text-blue-700 mt-1.5 font-medium">稳定运营</p>
                  <p className="text-[11px] text-blue-600">每天替换 {autoPublish.steady_replace_count ?? 1} 条</p>
                </div>
              </div>
              
              <p className="text-[11px] text-gray-500 text-center">
                最大活跃链接 {autoPublish.max_active_listings ?? 10} 条 · 
                替换依据：{(autoPublish.steady_replace_metric ?? 'views') === 'views' ? '浏览量' : '销量'}
              </p>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-xy-text-primary mb-1">冷启动天数</label>
                <input
                  type="number"
                  min={1}
                  max={14}
                  value={autoPublish.cold_start_days ?? 2}
                  onChange={(e) => onChange('auto_publish', 'cold_start_days', Math.max(1, Number(e.target.value)))}
                  className="w-full px-3 py-2 border border-xy-border rounded-lg focus:outline-none focus:ring-2 focus:ring-xy-primary/20 focus:border-xy-primary"
                />
                <p className="text-xs text-xy-text-secondary mt-1">前 N 天批量上架</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-xy-text-primary mb-1">每日新建链接数</label>
                <input
                  type="number"
                  min={1}
                  max={20}
                  value={autoPublish.cold_start_daily_count ?? 5}
                  onChange={(e) => onChange('auto_publish', 'cold_start_daily_count', Math.max(1, Number(e.target.value)))}
                  className="w-full px-3 py-2 border border-xy-border rounded-lg focus:outline-none focus:ring-2 focus:ring-xy-primary/20 focus:border-xy-primary"
                />
                <p className="text-xs text-xy-text-secondary mt-1">冷启动期每天</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-xy-text-primary mb-1">每日替换链接数</label>
                <input
                  type="number"
                  min={1}
                  max={10}
                  value={autoPublish.steady_replace_count ?? 1}
                  onChange={(e) => onChange('auto_publish', 'steady_replace_count', Math.max(1, Number(e.target.value)))}
                  className="w-full px-3 py-2 border border-xy-border rounded-lg focus:outline-none focus:ring-2 focus:ring-xy-primary/20 focus:border-xy-primary"
                />
                <p className="text-xs text-xy-text-secondary mt-1">稳定期每天</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-xy-text-primary mb-1">最大活跃链接数</label>
                <input
                  type="number"
                  min={1}
                  max={50}
                  value={autoPublish.max_active_listings ?? 10}
                  onChange={(e) => onChange('auto_publish', 'max_active_listings', Math.max(1, Number(e.target.value)))}
                  className="w-full px-3 py-2 border border-xy-border rounded-lg focus:outline-none focus:ring-2 focus:ring-xy-primary/20 focus:border-xy-primary"
                />
                <p className="text-xs text-xy-text-secondary mt-1">店铺上限</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-xy-text-primary mb-1">替换依据</label>
                <select
                  value={autoPublish.steady_replace_metric ?? 'views'}
                  onChange={(e) => onChange('auto_publish', 'steady_replace_metric', e.target.value)}
                  className="w-full px-3 py-2 border border-xy-border rounded-lg focus:outline-none focus:ring-2 focus:ring-xy-primary/20 focus:border-xy-primary"
                >
                  <option value="views">浏览量最低</option>
                  <option value="sales">销量最低</option>
                </select>
                <p className="text-xs text-xy-text-secondary mt-1">判断最差链接</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-xy-text-primary mb-1">默认品类</label>
                <select
                  value={autoPublish.default_category ?? 'exchange'}
                  onChange={(e) => onChange('auto_publish', 'default_category', e.target.value)}
                  className="w-full px-3 py-2 border border-xy-border rounded-lg focus:outline-none focus:ring-2 focus:ring-xy-primary/20 focus:border-xy-primary"
                >
                  {Object.entries(CATEGORY_META).map(([k, m]) => (
                    <option key={k} value={k}>
                      {m.label}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-xy-text-secondary mt-1">新商品默认归属</p>
              </div>
            </div>

            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl border border-xy-border">
              <div>
                <p className="font-medium text-xy-text-primary">自动合规检查</p>
                <p className="text-sm text-xy-text-secondary">上架前自动检测违规关键词和敏感内容</p>
              </div>
              <ToggleSwitch 
                checked={autoPublish.auto_compliance !== false} 
                onChange={() => onChange('auto_publish', 'auto_compliance', !(autoPublish.auto_compliance !== false))} 
              />
            </div>
          </>
        )}
      </div>

      <div className="bg-violet-50 border border-violet-200 rounded-xl p-4 flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-violet-800">品牌素材库 & 模板管理</p>
          <p className="text-xs text-violet-600 mt-0.5">管理品牌图片和商品主图模板</p>
        </div>
        <a 
          href="/products/auto-publish?tab=assets" 
          className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium bg-violet-600 text-white rounded-lg hover:bg-violet-700 transition-colors"
        >
          前往管理
          <ArrowUpRight className="w-3 h-3" />
        </a>
      </div>
    </div>
  );
}

export default function ProductSettings() {
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
    <ProductConfig
      config={config}
      onChange={handleChange}
      onSave={handleSave}
      saving={saving}
      isDirty={isDirty}
    />
  );
}
