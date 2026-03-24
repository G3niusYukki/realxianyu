import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Save, RefreshCw, Settings, Plug, FileText, Receipt, Package, Bell, Loader2, Shield } from 'lucide-react';
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

        <div className="bg-white rounded-xl border border-xy-border p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-amber-100 rounded-lg">
              <Shield className="w-5 h-5 text-amber-600" />
            </div>
            <div>
              <h3 className="font-semibold text-xy-text-primary">风控滑块自动验证</h3>
              <p className="text-sm text-xy-text-secondary">RGV587 风控触发时自动尝试滑块验证</p>
            </div>
          </div>

          <div className="space-y-4">
            <div className="bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 p-4 rounded-lg">
              <p className="text-sm text-amber-900 font-medium flex items-center gap-2">
                <Shield className="w-4 h-4" /> 风险提示
              </p>
              <p className="text-xs text-amber-800 mt-1">
                自动过滑块使用 Playwright 模拟浏览器操作，存在一定的账号封控风险。建议在了解风险后再开启。
              </p>
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl border border-xy-border">
              <div>
                <p className="font-medium text-xy-text-primary">启用自动滑块验证</p>
                <p className="text-xs text-xy-text-secondary mt-0.5">RGV587 触发后自动尝试过滑块</p>
              </div>
              <button
                onClick={() => onChange('slider_auto_solve', 'enabled', !config.slider_auto_solve?.enabled)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  config.slider_auto_solve?.enabled ? 'bg-xy-primary' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    config.slider_auto_solve?.enabled ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            {config.slider_auto_solve?.enabled && (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-xy-text-primary mb-1">最大尝试次数</label>
                    <input
                      type="number"
                      min={1}
                      max={5}
                      value={config.slider_auto_solve?.max_attempts ?? 2}
                      onChange={(e) => onChange('slider_auto_solve', 'max_attempts', Number(e.target.value))}
                      className="w-full px-3 py-2 border border-xy-border rounded-lg focus:outline-none focus:ring-2 focus:ring-xy-primary/20 focus:border-xy-primary"
                    />
                    <p className="text-xs text-gray-400 mt-1">每轮 RGV587 最多自动尝试次数（建议 1-3）</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-xy-text-primary mb-1">冷却间隔（秒）</label>
                    <input
                      type="number"
                      min={60}
                      max={3600}
                      value={config.slider_auto_solve?.cooldown_seconds ?? 300}
                      onChange={(e) => onChange('slider_auto_solve', 'cooldown_seconds', Number(e.target.value))}
                      className="w-full px-3 py-2 border border-xy-border rounded-lg focus:outline-none focus:ring-2 focus:ring-xy-primary/20 focus:border-xy-primary"
                    />
                    <p className="text-xs text-gray-400 mt-1">两次尝试之间的等待时间</p>
                  </div>
                </div>

                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl border border-xy-border">
                  <div>
                    <p className="font-medium text-xy-text-primary text-sm">无头模式</p>
                    <p className="text-xs text-xy-text-secondary mt-0.5">后台静默运行浏览器（关闭后可看到浏览器窗口）</p>
                  </div>
                  <button
                    onClick={() => onChange('slider_auto_solve', 'headless', !config.slider_auto_solve?.headless)}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      config.slider_auto_solve?.headless ? 'bg-xy-primary' : 'bg-gray-200'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        config.slider_auto_solve?.headless ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>

                <div className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-200">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <p className="font-medium text-xy-text-primary text-sm">指纹浏览器（BitBrowser）</p>
                      <p className="text-xs text-xy-text-secondary mt-0.5">通过 BitBrowser 指纹浏览器接管已登录的浏览器实例</p>
                    </div>
                    <button
                      onClick={() => onChange('slider_auto_solve', 'fingerprint_browser', {
                        ...(config.slider_auto_solve?.fingerprint_browser || {}),
                        enabled: !config.slider_auto_solve?.fingerprint_browser?.enabled,
                      })}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                        config.slider_auto_solve?.fingerprint_browser?.enabled ? 'bg-xy-primary' : 'bg-gray-200'
                      }`}
                    >
                      <span
                        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                          config.slider_auto_solve?.fingerprint_browser?.enabled ? 'translate-x-6' : 'translate-x-1'
                        }`}
                      />
                    </button>
                  </div>
                  {config.slider_auto_solve?.fingerprint_browser?.enabled && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3">
                      <div>
                        <label className="block text-sm font-medium text-xy-text-primary mb-1">API 地址</label>
                        <input
                          type="text"
                          value={config.slider_auto_solve?.fingerprint_browser?.api_url ?? 'http://127.0.0.1:54345'}
                          onChange={(e) => onChange('slider_auto_solve', 'fingerprint_browser', {
                            ...(config.slider_auto_solve?.fingerprint_browser || {}),
                            api_url: e.target.value,
                          })}
                          className="w-full px-3 py-2 border border-xy-border rounded-lg focus:outline-none focus:ring-2 focus:ring-xy-primary/20 focus:border-xy-primary"
                          placeholder="http://127.0.0.1:54345"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-xy-text-primary mb-1">浏览器 ID</label>
                        <input
                          type="text"
                          value={config.slider_auto_solve?.fingerprint_browser?.browser_id ?? ''}
                          onChange={(e) => onChange('slider_auto_solve', 'fingerprint_browser', {
                            ...(config.slider_auto_solve?.fingerprint_browser || {}),
                            browser_id: e.target.value,
                          })}
                          className="w-full px-3 py-2 border border-xy-border rounded-lg focus:outline-none focus:ring-2 focus:ring-xy-primary/20 focus:border-xy-primary"
                          placeholder="BitBrowser 浏览器 ID"
                        />
                      </div>
                    </div>
                  )}
                </div>
              </>
            )}
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
        slider_auto_solve: config.slider_auto_solve,
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
