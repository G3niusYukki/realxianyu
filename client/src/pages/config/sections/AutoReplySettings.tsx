import React, { useState, useEffect } from 'react';
import { Save, RefreshCw, FileText, Bot, MessageSquare, Sparkles } from 'lucide-react';
import { getSystemConfig, getConfigSections, saveSystemConfig } from '../../../api/config';
import { useStoreCategory } from '../../../contexts/StoreCategoryContext';
import { CATEGORY_DEFAULTS } from '../constants';
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

function AutoReplyConfig({ config, onChange, onSave, saving, isDirty }: ConfigSectionProps) {
  const { category } = useStoreCategory();
  const defaults = CATEGORY_DEFAULTS[category] || CATEGORY_DEFAULTS.express;
  const autoReply = config.auto_reply || {};

  const applyCategoryDefaults = () => {
    onChange('auto_reply', 'default_reply', defaults.auto_reply.default_reply);
    onChange('auto_reply', 'virtual_default_reply', defaults.auto_reply.virtual_default_reply);
    onChange('auto_reply', 'ai_intent_enabled', defaults.auto_reply.ai_intent_enabled);
    onChange('auto_reply', 'enabled', defaults.auto_reply.enabled);
    toast.success('已应用品类默认话术');
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-xy-text-primary">自动回复配置</h2>
          <p className="text-xy-text-secondary text-sm mt-1">配置自动回复话术和智能回复规则</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={applyCategoryDefaults}
            className="flex items-center gap-2 px-4 py-2 border border-xy-border rounded-lg font-medium hover:bg-gray-50 transition-colors"
          >
            <Sparkles className="w-4 h-4" />
            应用品类默认话术
          </button>
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
      </div>

      <div className="grid gap-6">
        <div className="bg-white rounded-xl border border-xy-border p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Bot className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <h3 className="font-semibold text-xy-text-primary">自动回复开关</h3>
                <p className="text-sm text-xy-text-secondary">开启后系统将自动回复买家消息</p>
              </div>
            </div>
            <ToggleSwitch 
              checked={autoReply.enabled !== false} 
              onChange={() => onChange('auto_reply', 'enabled', !(autoReply.enabled !== false))} 
            />
          </div>
        </div>

        <div className="bg-white rounded-xl border border-xy-border p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-green-100 rounded-lg">
              <MessageSquare className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <h3 className="font-semibold text-xy-text-primary">默认回复话术</h3>
              <p className="text-sm text-xy-text-secondary">当没有匹配到特定规则时的默认回复</p>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-xy-text-primary mb-1">
                普通商品默认回复
              </label>
              <textarea
                value={autoReply.default_reply || ''}
                onChange={(e) => onChange('auto_reply', 'default_reply', e.target.value)}
                rows={4}
                className="w-full px-3 py-2 border border-xy-border rounded-lg focus:outline-none focus:ring-2 focus:ring-xy-primary/20 focus:border-xy-primary resize-none"
                placeholder="您好！感谢您的咨询。请问有什么可以帮您的吗？"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-xy-text-primary mb-1">
                虚拟商品专用回复
              </label>
              <textarea
                value={autoReply.virtual_default_reply || ''}
                onChange={(e) => onChange('auto_reply', 'virtual_default_reply', e.target.value)}
                rows={4}
                className="w-full px-3 py-2 border border-xy-border rounded-lg focus:outline-none focus:ring-2 focus:ring-xy-primary/20 focus:border-xy-primary resize-none"
                placeholder="您好！本商品为虚拟商品，购买后自动发送。如有问题请联系客服。"
              />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-xy-border p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Sparkles className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <h3 className="font-semibold text-xy-text-primary">AI 智能回复</h3>
                <p className="text-sm text-xy-text-secondary">使用 AI 识别买家意图并生成回复</p>
              </div>
            </div>
            <ToggleSwitch 
              checked={!!autoReply.ai_intent_enabled} 
              onChange={() => onChange('auto_reply', 'ai_intent_enabled', !autoReply.ai_intent_enabled)} 
            />
          </div>

          {autoReply.ai_intent_enabled && (
            <div className="mt-4 p-4 bg-purple-50 rounded-lg">
              <p className="text-sm text-purple-800">
                AI 智能回复已启用。系统将使用配置的 AI 服务分析买家消息意图，并生成合适的回复。
              </p>
            </div>
          )}
        </div>

        <div className="bg-white rounded-xl border border-xy-border p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-orange-100 rounded-lg">
              <FileText className="w-5 h-5 text-orange-600" />
            </div>
            <div>
              <h3 className="font-semibold text-xy-text-primary">关键词回复</h3>
              <p className="text-sm text-xy-text-secondary">配置特定关键词触发的回复内容</p>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-xy-text-secondary mb-2">
              格式：关键词=回复内容（每行一条）
            </label>
            <textarea
              value={autoReply.keyword_replies_text || ''}
              onChange={(e) => onChange('auto_reply', 'keyword_replies_text', e.target.value)}
              rows={8}
              className="w-full px-3 py-2 border border-xy-border rounded-lg focus:outline-none focus:ring-2 focus:ring-xy-primary/20 focus:border-xy-primary resize-none font-mono text-sm"
              placeholder={`还在=在的亲，请问需要寄什么快递？
最低=价格已经尽量实在了，诚心要的话可以小刀。
包邮=默认不包邮，具体看地区可以商量。`}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AutoReplySettings() {
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
    <AutoReplyConfig
      config={config}
      onChange={handleChange}
      onSave={handleSave}
      saving={saving}
      isDirty={isDirty}
    />
  );
}
