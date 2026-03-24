import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Save, RefreshCw, Settings, Plug, FileText, Receipt, Package, Bell, Loader2 } from 'lucide-react';
import { getSystemConfig, getConfigSections, saveSystemConfig } from '../../../api/config';
import { api } from '../../../api/index';
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

  const [testingXgj, setTestingXgj] = useState(false);
  const [testingAi, setTestingAi] = useState(false);

  const handleTestXgj = async () => {
    const appKey = xianguanjia.app_key || '';
    const appSecret = xianguanjia.app_secret || '';

    if (!appKey) {
      toast.error('请先填写 App Key');
      return;
    }
    if (!appSecret) {
      toast.error('请先填写 App Secret');
      return;
    }

    setTestingXgj(true);
    try {
      const res = await api.post('/xgj/test-connection', {
        app_key: appKey,
        app_secret: appSecret,
        base_url: xianguanjia.base_url || 'https://open.goofish.pro',
        mode: xianguanjia.mode || 'self_developed',
        seller_id: xianguanjia.seller_id || '',
      });
      if (res.data?.ok) {
        toast.success(`闲管家连接成功（延迟 ${res.data.latency_ms || '?'}ms）`);
      } else {
        toast.error('闲管家连接失败: ' + (res.data?.message || '未知错误'));
      }
    } catch (err: any) {
      const msg = err?.response?.data?.message || err.message || '请求失败';
      toast.error('连接测试异常: ' + msg);
    } finally {
      setTestingXgj(false);
    }
  };

  const handleTestAi = async () => {
    const apiKey = ai.api_key || '';
    const baseUrl = ai.base_url || '';
    const model = ai.model || 'qwen-plus';

    if (!apiKey) {
      toast.error('请先填写 API Key');
      return;
    }

    setTestingAi(true);
    try {
      const res = await api.post('/ai/test', { api_key: apiKey, base_url: baseUrl, model });
      if (res.data?.ok) {
        toast.success('AI 连接测试成功: ' + res.data.message);
      } else {
        toast.error('AI 连接失败: ' + (res.data?.message || '未知错误'));
      }
    } catch (err: any) {
      const msg = err?.response?.data?.message || err.message || '请求失败';
      toast.error('AI 测试异常: ' + msg);
    } finally {
      setTestingAi(false);
    }
  };

  return (
    <div className="space-y-6 px-6 py-6">
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
          
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-xy-text-primary mb-1">
                  接入模式 <span className="text-xs text-gray-400">(Mode)</span>
                </label>
                <select
                  value={xianguanjia.mode || 'self_developed'}
                  onChange={(e) => onChange('xianguanjia', 'mode', e.target.value)}
                  className="w-full px-3 py-2 border border-xy-border rounded-lg focus:outline-none focus:ring-2 focus:ring-xy-primary/20 focus:border-xy-primary"
                >
                  <option value="self_developed">自研应用</option>
                  <option value="business">商务对接</option>
                </select>
                <p className="text-xs text-gray-400 mt-1">自研：个人/自有ERP；商务：第三方代商家接入</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-xy-text-primary mb-1">
                  API 网关 <span className="text-xs text-gray-400">(Base URL)</span>
                </label>
                <input
                  type="text"
                  value={xianguanjia.base_url || 'https://open.goofish.pro'}
                  onChange={(e) => onChange('xianguanjia', 'base_url', e.target.value)}
                  className="w-full px-3 py-2 border border-xy-border rounded-lg focus:outline-none focus:ring-2 focus:ring-xy-primary/20 focus:border-xy-primary"
                  placeholder="https://open.goofish.pro"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-xy-text-primary mb-1">
                  App Key <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={xianguanjia.app_key || ''}
                  onChange={(e) => onChange('xianguanjia', 'app_key', e.target.value)}
                  className="w-full px-3 py-2 border border-xy-border rounded-lg focus:outline-none focus:ring-2 focus:ring-xy-primary/20 focus:border-xy-primary"
                  placeholder="输入闲管家 App Key"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-xy-text-primary mb-1">
                  App Secret <span className="text-red-500">*</span>
                </label>
                <input
                  type="password"
                  value={xianguanjia.app_secret || ''}
                  onChange={(e) => onChange('xianguanjia', 'app_secret', e.target.value)}
                  className="w-full px-3 py-2 border border-xy-border rounded-lg focus:outline-none focus:ring-2 focus:ring-xy-primary/20 focus:border-xy-primary"
                  placeholder="输入闲管家 App Secret"
                />
              </div>
            </div>

            {xianguanjia.mode === 'business' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-xy-text-primary mb-1">
                    商家 ID (Seller ID) <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={xianguanjia.seller_id || ''}
                    onChange={(e) => onChange('xianguanjia', 'seller_id', e.target.value)}
                    className="w-full px-3 py-2 border border-xy-border rounded-lg focus:outline-none focus:ring-2 focus:ring-xy-primary/20 focus:border-xy-primary"
                    placeholder="商务对接模式下必填"
                  />
                </div>
              </div>
            )}
          </div>

          <div className="mt-4 flex gap-2">
            <button
              onClick={handleTestXgj}
              disabled={testingXgj}
              className="px-4 py-2 border border-xy-border rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              {testingXgj ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
              {testingXgj ? '测试中...' : '测试连接'}
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
              disabled={testingAi}
              className="px-4 py-2 border border-xy-border rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              {testingAi ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
              {testingAi ? '测试中...' : '测试 AI 连接'}
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
      const currentRes = await getSystemConfig();
      const currentConfig = currentRes.data?.config || {};

      const configToSave = {
        ...currentConfig,
        xianguanjia: config.xianguanjia,
        ai: config.ai,
        oss: config.oss,
        cookie_cloud: config.cookie_cloud,
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
