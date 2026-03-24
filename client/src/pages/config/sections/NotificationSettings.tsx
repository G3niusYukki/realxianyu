import React, { useState, useEffect } from 'react';
import { Save, RefreshCw, Bell, Send, MessageCircle, AlertTriangle, CheckCircle } from 'lucide-react';
import { getSystemConfig, saveSystemConfig } from '../../../api/config';
import { api } from '../../../api/index';
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

const NOTIFICATION_EVENTS = [
  { key: 'notify_cookie_expire', label: 'Cookie 过期告警', desc: 'Cookie 即将过期或已失效时发送通知' },
  { key: 'notify_cookie_refresh', label: 'Cookie 刷新成功', desc: 'Cookie 自动刷新成功时发送通知' },
  { key: 'notify_sla_alert', label: 'SLA 异常告警', desc: '消息回复超时或订单处理超时时发送通知' },
  { key: 'notify_order_fail', label: '订单异常告警', desc: '订单处理失败时发送通知' },
  { key: 'notify_ship_fail', label: '发货失败告警', desc: '自动发货失败时发送通知' },
  { key: 'notify_manual_takeover', label: '人工接管告警', desc: '需要人工介入处理时发送通知' },
];

function NotificationConfig({ config, onChange, onSave, saving, isDirty }: ConfigSectionProps) {
  const notifications = config.notifications || {};
  const [testingChannel, setTestingChannel] = useState<string | null>(null);

  const handleTest = async (channel: string) => {
    const webhookKey = channel === 'feishu' ? 'feishu_webhook' : 'wechat_webhook';
    const webhookUrl = notifications[webhookKey] || '';
    
    if (!webhookUrl || webhookUrl.includes('****')) {
      toast.error('请先填写并保存 Webhook URL');
      return;
    }

    setTestingChannel(channel);
    try {
      const res = await api.post('/notifications/test', { 
        channel, 
        webhook_url: webhookUrl 
      });
      if (res.data?.ok) {
        toast.success(channel === 'feishu' ? '飞书测试消息发送成功' : '企业微信测试消息发送成功');
      } else {
        toast.error(res.data?.error || '发送失败');
      }
    } catch (err: any) {
      toast.error('发送失败: ' + (err?.response?.data?.error || err.message));
    } finally {
      setTestingChannel(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-xy-text-primary">告警通知配置</h2>
          <p className="text-xy-text-secondary text-sm mt-1">配置异常告警通知渠道和触发条件</p>
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
            <div className="p-2 bg-blue-100 rounded-lg">
              <Send className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h3 className="font-semibold text-xy-text-primary">飞书通知</h3>
              <p className="text-sm text-xy-text-secondary">通过飞书机器人发送告警消息</p>
            </div>
          </div>

          <div className="flex items-center justify-between mb-4">
            <span className="font-medium text-xy-text-primary">启用飞书通知</span>
            <ToggleSwitch 
              checked={!!notifications.feishu_enabled} 
              onChange={() => onChange('notifications', 'feishu_enabled', !notifications.feishu_enabled)} 
            />
          </div>

          {notifications.feishu_enabled && (
            <>
              <div className="mt-4">
                <label className="block text-sm font-medium text-xy-text-primary mb-1">Webhook URL</label>
                <input
                  type="text"
                  value={notifications.feishu_webhook || ''}
                  onChange={(e) => onChange('notifications', 'feishu_webhook', e.target.value)}
                  className="w-full px-3 py-2 border border-xy-border rounded-lg focus:outline-none focus:ring-2 focus:ring-xy-primary/20 focus:border-xy-primary"
                  placeholder="https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
                />
                <p className="text-xs text-xy-text-secondary mt-1">
                  在飞书群设置中添加机器人，复制 Webhook 地址
                </p>
              </div>

              <div className="mt-4 flex gap-2">
                <a
                  href="https://open.feishu.cn/document/client-docs/bot-v3/add-custom-bot"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-xy-primary hover:underline"
                >
                  如何获取 Webhook？
                </a>
                <button
                  onClick={() => handleTest('feishu')}
                  disabled={testingChannel === 'feishu'}
                  className="ml-auto px-4 py-2 border border-xy-border rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors disabled:opacity-50"
                >
                  {testingChannel === 'feishu' ? '测试中...' : '发送测试消息'}
                </button>
              </div>
            </>
          )}
        </div>

        <div className="bg-white rounded-xl border border-xy-border p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-green-100 rounded-lg">
              <MessageCircle className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <h3 className="font-semibold text-xy-text-primary">企业微信通知</h3>
              <p className="text-sm text-xy-text-secondary">通过企业微信机器人发送告警消息</p>
            </div>
          </div>

          <div className="flex items-center justify-between mb-4">
            <span className="font-medium text-xy-text-primary">启用企业微信通知</span>
            <ToggleSwitch 
              checked={!!notifications.wechat_enabled} 
              onChange={() => onChange('notifications', 'wechat_enabled', !notifications.wechat_enabled)} 
            />
          </div>

          {notifications.wechat_enabled && (
            <>
              <div className="mt-4">
                <label className="block text-sm font-medium text-xy-text-primary mb-1">Webhook URL</label>
                <input
                  type="text"
                  value={notifications.wechat_webhook || ''}
                  onChange={(e) => onChange('notifications', 'wechat_webhook', e.target.value)}
                  className="w-full px-3 py-2 border border-xy-border rounded-lg focus:outline-none focus:ring-2 focus:ring-xy-primary/20 focus:border-xy-primary"
                  placeholder="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"
                />
                <p className="text-xs text-xy-text-secondary mt-1">
                  在企业微信群中添加机器人，复制 Webhook 地址
                </p>
              </div>

              <div className="mt-4 flex gap-2">
                <a
                  href="https://work.weixin.qq.com/help?doc_id=13376"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-xy-primary hover:underline"
                >
                  如何获取 Webhook？
                </a>
                <button
                  onClick={() => handleTest('wechat')}
                  disabled={testingChannel === 'wechat'}
                  className="ml-auto px-4 py-2 border border-xy-border rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors disabled:opacity-50"
                >
                  {testingChannel === 'wechat' ? '测试中...' : '发送测试消息'}
                </button>
              </div>
            </>
          )}
        </div>

        <div className="bg-white rounded-xl border border-xy-border p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-orange-100 rounded-lg">
              <Bell className="w-5 h-5 text-orange-600" />
            </div>
            <div>
              <h3 className="font-semibold text-xy-text-primary">告警事件</h3>
              <p className="text-sm text-xy-text-secondary">选择需要发送通知的事件类型</p>
            </div>
          </div>

          <div className="space-y-3">
            {NOTIFICATION_EVENTS.map((event) => (
              <div 
                key={event.key}
                className="flex items-start justify-between p-3 rounded-lg border border-xy-border hover:border-xy-primary/30 transition-colors"
              >
                <div className="flex items-start gap-3">
                  <div className="mt-0.5">
                    {event.key.includes('fail') || event.key.includes('alert') ? (
                      <AlertTriangle className="w-4 h-4 text-orange-500" />
                    ) : event.key.includes('expire') ? (
                      <AlertTriangle className="w-4 h-4 text-red-500" />
                    ) : (
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    )}
                  </div>
                  <div>
                    <div className="font-medium text-xy-text-primary">{event.label}</div>
                    <div className="text-sm text-xy-text-secondary">{event.desc}</div>
                  </div>
                </div>
                <ToggleSwitch 
                  checked={notifications[event.key] !== false} 
                  onChange={() => onChange('notifications', event.key, !(notifications[event.key] !== false))} 
                />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function NotificationSettings() {
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
    <NotificationConfig
      config={config}
      onChange={handleChange}
      onSave={handleSave}
      saving={saving}
      isDirty={isDirty}
    />
  );
}
