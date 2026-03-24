import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Save, RefreshCw, Settings, Plug, FileText, Receipt, Package, Bell } from 'lucide-react';
import { getSystemConfig, getConfigSections, saveSystemConfig } from '../../../api/config';
import toast from 'react-hot-toast';

interface ConfigSectionProps {
  config: Record<string, any>;
  sections: any[];
  onChange: (sectionKey: string, fieldKey: string, value: any) => void;
  onSave: () => Promise<void>;
  saving: boolean;
  isDirty: boolean;
}

// Integration Configuration (xianguanjia, AI, OSS, CookieCloud)
function IntegrationConfig({ config, sections, onChange, onSave, saving, isDirty }: ConfigSectionProps) {
  const xianguanjia = config.xianguanjia || {};
  const ai = config.ai || {};
  const oss = config.oss || {};
  const cookieCloud = config.cookie_cloud || {};

  const handleTestXgj = async () => {
    // Test connection logic
    toast.success('连接测试功能开发中');
  };

  const handleTestAi = async () => {
    toast.success('AI 测试功能开发中');
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-xy-text-primary">集成服务配置</h2>
          <p className="text-xy-text-secondary text-sm mt-1">配置第三方服务接入，包括闲管家、AI、OSS等</p>
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
        {/* 闲管家配置 */}
        <div className="bg-white rounded-xl border border-xy-border p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-orange-100 rounded-lg">
              <Settings className="w-5 h-5 text-orange-600" />
            </div>
            <div>
              <h3 className="font-semibold text-xy-text-primary">闲管家开放平台</h3>
              <p className="text-sm text-xy-text-secondary">连接闲鱼平台，实现订单和商品管理</p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-xy-text-primary mb-1">App Key</label>
              <input
                type="text"
                value={xianguanjia.app_key || ''}
                onChange={(e) => onChange('xianguanjia', 'app_key', e.target.value)}
                className="w-full px-3 py-2 border border-xy-border rounded-lg focus:outline-none focus:ring-2 focus:ring-xy-primary/20 focus:border-xy-primary"
                placeholder="输入闲管家 App Key"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-xy-text-primary mb-1">App Secret</label>
              <input
                type="password"
                value={xianguanjia.app_secret || ''}
                onChange={(e) => onChange('xianguanjia', 'app_secret', e.target.value)}
                className="w-full px-3 py-2 border border-xy-border rounded-lg focus:outline-none focus:ring-2 focus:ring-xy-primary/20 focus:border-xy-primary"
                placeholder="输入闲管家 App Secret"
              />
            </div>
          </div>

          <div className="mt-4 flex gap-2">
            <button
              onClick={handleTestXgj}
              className="px-4 py-2 border border-xy-border rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors"
            >
              测试连接
            </button>
          </div>
        </div>

        {/* AI 配置 */}
        <div className="bg-white rounded-xl border border-xy-border p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Plug className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <h3 className="font-semibold text-xy-text-primary">AI 服务</h3>
              <p className="text-sm text-xy-text-secondary">配置智能回复、意图识别等 AI 功能</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-xy-text-primary mb-1">提供商</label>
              <select
                value={ai.provider || 'deepseek'}
                onChange={(e) => onChange('ai', 'provider', e.target.value)}
                className="w-full px-3 py-2 border border-xy-border rounded-lg focus:outline-none focus:ring-2 focus:ring-xy-primary/20 focus:border-xy-primary"
              >
                <option value="deepseek">DeepSeek</option>
                <option value="qwen">阿里云百炼 (Qwen)</option>
                <option value="openai">OpenAI</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-xy-text-primary mb-1">API Key</label>
              <input
                type="password"
                value={ai.api_key || ''}
                onChange={(e) => onChange('ai', 'api_key', e.target.value)}
                className="w-full px-3 py-2 border border-xy-border rounded-lg focus:outline-none focus:ring-2 focus:ring-xy-primary/20 focus:border-xy-primary"
                placeholder="输入 AI API Key"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-xy-text-primary mb-1">模型</label>
              <input
                type="text"
                value={ai.model || ''}
                onChange={(e) => onChange('ai', 'model', e.target.value)}
                className="w-full px-3 py-2 border border-xy-border rounded-lg focus:outline-none focus:ring-2 focus:ring-xy-primary/20 focus:border-xy-primary"
                placeholder="例如：deepseek-chat"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-xy-text-primary mb-1">Base URL</label>
              <input
                type="text"
                value={ai.base_url || ''}
                onChange={(e) => onChange('ai', 'base_url', e.target.value)}
                className="w-full px-3 py-2 border border-xy-border rounded-lg focus:outline-none focus:ring-2 focus:ring-xy-primary/20 focus:border-xy-primary"
                placeholder="https://api.example.com/v1"
              />
            </div>
          </div>

          <div className="mt-4 flex gap-2">
            <button
              onClick={handleTestAi}
              className="px-4 py-2 border border-xy-border rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors"
            >
              测试 AI 连接
            </button>
          </div>
        </div>

        {/* CookieCloud 配置 */}
        <div className="bg-white rounded-xl border border-xy-border p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Plug className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h3 className="font-semibold text-xy-text-primary">CookieCloud 同步</h3>
              <p className="text-sm text-xy-text-secondary">自动同步浏览器 Cookie，防止登录失效</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-xy-text-primary mb-1">服务器地址</label>
              <input
                type="text"
                value={cookieCloud.cookie_cloud_host || ''}
                onChange={(e) => onChange('cookie_cloud', 'cookie_cloud_host', e.target.value)}
                className="w-full px-3 py-2 border border-xy-border rounded-lg focus:outline-none focus:ring-2 focus:ring-xy-primary/20 focus:border-xy-primary"
                placeholder="http://localhost:8080"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-xy-text-primary mb-1">UUID</label>
              <input
                type="text"
                value={cookieCloud.cookie_cloud_uuid || ''}
                onChange={(e) => onChange('cookie_cloud', 'cookie_cloud_uuid', e.target.value)}
                className="w-full px-3 py-2 border border-xy-border rounded-lg focus:outline-none focus:ring-2 focus:ring-xy-primary/20 focus:border-xy-primary"
                placeholder="CookieCloud UUID"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-xy-text-primary mb-1">密码</label>
              <input
                type="password"
                value={cookieCloud.cookie_cloud_password || ''}
                onChange={(e) => onChange('cookie_cloud', 'cookie_cloud_password', e.target.value)}
                className="w-full px-3 py-2 border border-xy-border rounded-lg focus:outline-none focus:ring-2 focus:ring-xy-primary/20 focus:border-xy-primary"
                placeholder="CookieCloud 密码"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Placeholder for other sections
function PlaceholderSection({ title }: { title: string }) {
  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold text-xy-text-primary mb-4">{title}</h2>
      <p className="text-xy-text-secondary">此配置页面正在重构中，请使用旧版配置页面。{/* TODO: Implement */}</p>
    </div>
  );
}

// Main wrapper that provides data management
export default function IntegrationSettings() {
  const { section = 'integrations' } = useParams();
  const [config, setConfig] = useState<Record<string, any>>({});
  const [sections, setSections] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [isDirty, setIsDirty] = useState(false);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const [configRes, sectionsRes] = await Promise.all([
        getSystemConfig(),
        getConfigSections(),
      ]);
      if (configRes.data?.ok) {
        setConfig(configRes.data.config || {});
      }
      if (sectionsRes.data?.ok) {
        setSections(sectionsRes.data.sections || []);
      }
    } catch (err) {
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
    <IntegrationConfig
      config={config}
      sections={sections}
      onChange={handleChange}
      onSave={handleSave}
      saving={saving}
      isDirty={isDirty}
    />
  );
}
