import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../../api/index';
import {
  MessageCircle, Send, Bot, User, Clock,
  RefreshCw, BarChart3, MessagesSquare, Zap,
  AlertCircle, Activity, FileText, Beaker, Save,
} from 'lucide-react';
import toast from 'react-hot-toast';

const MSG_TABS = [
  { key: 'logs', label: '回复日志' },
  { key: 'templates', label: '回复模板' },
  { key: 'sandbox', label: '测试沙盒' },
];

export default function Messages() {
  const [activeTab, setActiveTab] = useState('logs');
  const [stats, setStats] = useState(null);
  const [replies, setReplies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [template, setTemplate] = useState('');
  const [templateLoading, setTemplateLoading] = useState(false);
  const [templateSaving, setTemplateSaving] = useState(false);

  const [sandboxInput, setSandboxInput] = useState('');
  const [sandboxResult, setSandboxResult] = useState(null);
  const [sandboxTesting, setSandboxTesting] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [statusRes, repliesRes] = await Promise.all([
        api.get('/status'),
        api.get('/replies'),
      ]);
      setStats(statusRes.data.message_stats || null);
      setReplies(Array.isArray(repliesRes.data) ? repliesRes.data : []);
    } catch (err) {
      setError(err.message || '无法连接后端');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchTemplate = useCallback(async () => {
    setTemplateLoading(true);
    try {
      const res = await api.get('/get-template');
      setTemplate(res.data?.template || res.data?.content || '');
    } catch { /* ignore */ }
    finally { setTemplateLoading(false); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);
  useEffect(() => { if (activeTab === 'templates') fetchTemplate(); }, [activeTab, fetchTemplate]);

  const handleSaveTemplate = async () => {
    setTemplateSaving(true);
    try {
      const res = await api.post('/save-template', { template });
      if (res.data?.success || res.data?.ok) toast.success('模板保存成功');
      else toast.error(res.data?.error || '保存失败');
    } catch (e) { toast.error(e.message || '保存失败'); }
    finally { setTemplateSaving(false); }
  };

  const handleTestReply = async () => {
    if (!sandboxInput.trim()) return;
    setSandboxTesting(true);
    setSandboxResult(null);
    try {
      const res = await api.post('/test-reply', { message: sandboxInput });
      setSandboxResult(res.data);
    } catch (e) { setSandboxResult({ error: e.message }); }
    finally { setSandboxTesting(false); }
  };

  const statCards = stats ? [
    { label: '总会话数', value: stats.total_conversations ?? '-', icon: MessagesSquare, color: 'text-blue-600 bg-blue-50' },
    { label: '总消息量', value: stats.total_messages ?? '-', icon: BarChart3, color: 'text-indigo-600 bg-indigo-50' },
    { label: '今日自动回复', value: stats.today_replied ?? '-', icon: Zap, color: 'text-amber-600 bg-amber-50' },
    { label: '累计自动回复', value: stats.total_replied ?? '-', icon: Bot, color: 'text-green-600 bg-green-50' },
    { label: '近期回复', value: stats.recent_replied ?? '-', icon: Activity, color: 'text-purple-600 bg-purple-50' },
  ] : [];

  if (loading) {
    return (
      <div className="xy-page xy-enter max-w-6xl flex items-center justify-center h-[calc(100vh-100px)]">
        <div className="flex flex-col items-center gap-3 text-xy-text-muted">
          <RefreshCw className="w-8 h-8 animate-spin text-xy-brand-500" />
          <span>正在加载消息数据...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="xy-page xy-enter max-w-6xl flex items-center justify-center h-[calc(100vh-100px)]">
        <div className="xy-card p-8 flex flex-col items-center gap-4 max-w-md text-center">
          <AlertCircle className="w-10 h-10 text-red-500" />
          <p className="text-xy-text-primary font-medium">连接失败</p>
          <p className="text-sm text-xy-text-secondary">{error}</p>
          <button onClick={fetchData} className="xy-btn-primary mt-2 flex items-center gap-2">
            <RefreshCw className="w-4 h-4" /> 重试
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="xy-page xy-enter max-w-6xl">
      <div className="flex flex-col md:flex-row justify-between md:items-end gap-4 mb-6">
        <div>
          <h1 className="xy-title flex items-center gap-2">
            <MessageCircle className="w-6 h-6 text-xy-brand-500" /> 消息中心
          </h1>
          <p className="xy-subtitle mt-1">自动回复日志、模板管理和测试沙盒</p>
        </div>
        <div className="flex bg-xy-gray-100 p-1 rounded-xl">
          {MSG_TABS.map(t => (
            <button key={t.key} onClick={() => setActiveTab(t.key)}
              className={`px-4 py-1.5 text-sm font-medium rounded-lg transition-colors ${activeTab === t.key ? 'bg-white shadow-sm text-xy-text-primary' : 'text-xy-text-secondary hover:text-xy-text-primary'}`}>
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {activeTab === 'logs' && (
        <div className="xy-card flex h-[calc(100vh-200px)] overflow-hidden">
          {/* Left sidebar - stats */}
          <div className="w-1/3 min-w-[260px] max-w-[320px] border-r border-xy-border flex flex-col bg-xy-gray-50">
            <div className="p-4 border-b border-xy-border bg-white">
              <div className="flex items-center justify-between mb-1">
                <h2 className="font-bold text-lg flex items-center gap-2"><MessageCircle className="w-5 h-5 text-xy-brand-500" /> 消息概览</h2>
                <button onClick={fetchData} className="p-1.5 rounded-lg hover:bg-xy-gray-100 text-xy-text-muted transition-colors" title="刷新数据">
                  <RefreshCw className="w-4 h-4" />
                </button>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {statCards.map(card => (
                <div key={card.label} className="bg-white rounded-xl p-4 border border-xy-border shadow-sm">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${card.color}`}>
                      <card.icon className="w-5 h-5" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-xy-text-primary">{card.value}</p>
                      <p className="text-xs text-xy-text-secondary">{card.label}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right - reply logs */}
          <div className="flex-1 flex flex-col bg-white">
            <div className="px-6 py-4 border-b border-xy-border flex justify-between items-center bg-white shadow-sm z-10">
              <div>
                <h3 className="font-bold text-lg text-xy-text-primary">自动回复日志</h3>
                <p className="text-sm text-xy-text-secondary mt-0.5">共 <span className="text-xy-brand-600 font-medium">{replies.length}</span> 条记录</p>
              </div>
              <div className="flex items-center gap-2 text-xs font-medium px-3 py-1.5 bg-green-50 text-green-700 rounded-full border border-green-200">
                <Bot className="w-3.5 h-3.5" /> AI 自动回复
              </div>
            </div>
            <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-xy-gray-50/50">
              {replies.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-xy-text-muted">
                  <MessageCircle className="w-16 h-16 mb-4 text-xy-gray-200" />
                  <p>暂无自动回复记录</p>
                </div>
              ) : (
                replies.map((reply, idx) => (
                  <div key={reply.id || idx} className="bg-white rounded-xl border border-xy-border p-4 shadow-sm space-y-3">
                    {reply.buyer_message && (
                      <div className="flex gap-3">
                        <div className="w-8 h-8 rounded-full flex items-center justify-center bg-blue-100 text-blue-600 flex-shrink-0"><User className="w-4 h-4" /></div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1 text-xs text-xy-text-muted">
                            <span className="font-medium text-blue-600">买家</span>
                            {reply.item_title && <span className="bg-xy-gray-100 px-1.5 py-0.5 rounded truncate max-w-[200px]">{reply.item_title}</span>}
                          </div>
                          <div className="px-3 py-2 rounded-xl bg-xy-gray-50 border border-xy-border text-sm text-xy-text-primary rounded-tl-sm">{reply.buyer_message}</div>
                        </div>
                      </div>
                    )}
                    {reply.reply_text && (
                      <div className="flex gap-3 flex-row-reverse">
                        <div className="w-8 h-8 rounded-full flex items-center justify-center bg-orange-100 text-orange-600 flex-shrink-0"><Bot className="w-4 h-4" /></div>
                        <div className="flex flex-col items-end flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1 text-xs text-xy-text-muted">
                            <span className="font-medium text-orange-500">自动回复</span>
                            {reply.intent && <span className="bg-xy-gray-200 px-1.5 py-0.5 rounded text-xy-gray-600">意图: {reply.intent}</span>}
                            {reply.replied_at && <span>{new Date(reply.replied_at).toLocaleString()}</span>}
                          </div>
                          <div className="px-3 py-2 rounded-xl bg-orange-50 border border-orange-200 text-sm text-xy-text-primary rounded-tr-sm">{reply.reply_text}</div>
                        </div>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'templates' && (
        <div className="xy-card p-6 space-y-6 animate-in fade-in slide-in-from-right-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-xy-text-primary flex items-center gap-2"><FileText className="w-5 h-5" /> 回复模板</h2>
              <p className="text-sm text-xy-text-secondary mt-1">配置自动回复的话术模板，支持变量替换</p>
            </div>
            <button onClick={handleSaveTemplate} disabled={templateSaving} className="xy-btn-primary flex items-center gap-2">
              {templateSaving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              保存模板
            </button>
          </div>
          {templateLoading ? (
            <div className="py-12 text-center text-xy-text-muted"><RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2" />加载中...</div>
          ) : (
            <textarea
              className="xy-input px-4 py-3 h-80 font-mono text-sm resize-none"
              placeholder="输入自动回复模板内容..."
              value={template}
              onChange={e => setTemplate(e.target.value)}
            />
          )}
          <div className="p-4 bg-blue-50 rounded-lg border border-blue-200 text-sm text-blue-700">
            <p className="font-medium mb-2">模板变量说明</p>
            <ul className="list-disc list-inside space-y-1">
              <li><code className="bg-blue-100 px-1 rounded">{'{{buyer_name}}'}</code> — 买家昵称</li>
              <li><code className="bg-blue-100 px-1 rounded">{'{{item_title}}'}</code> — 商品标题</li>
              <li><code className="bg-blue-100 px-1 rounded">{'{{item_price}}'}</code> — 商品价格</li>
              <li><code className="bg-blue-100 px-1 rounded">{'{{order_id}}'}</code> — 订单号</li>
            </ul>
          </div>
        </div>
      )}

      {activeTab === 'sandbox' && (
        <div className="xy-card p-6 space-y-6 animate-in fade-in slide-in-from-right-4">
          <div>
            <h2 className="text-lg font-bold text-xy-text-primary flex items-center gap-2"><Beaker className="w-5 h-5" /> 测试沙盒</h2>
            <p className="text-sm text-xy-text-secondary mt-1">模拟买家消息，测试 AI 自动回复效果</p>
          </div>
          <div className="flex gap-3">
            <textarea
              className="flex-1 xy-input px-4 py-3 h-24 resize-none"
              placeholder='输入模拟的买家消息，如："这个怎么卖？还有货吗？"'
              value={sandboxInput}
              onChange={e => setSandboxInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleTestReply(); } }}
            />
            <button onClick={handleTestReply} disabled={sandboxTesting || !sandboxInput.trim()} className="xy-btn-primary px-6 self-end">
              {sandboxTesting ? <RefreshCw className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
            </button>
          </div>
          {sandboxResult && (
            <div className="space-y-4">
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center flex-shrink-0"><User className="w-4 h-4" /></div>
                <div className="px-4 py-3 rounded-xl bg-blue-50 border border-blue-200 text-sm flex-1">{sandboxInput}</div>
              </div>
              <div className="flex gap-3 flex-row-reverse">
                <div className="w-8 h-8 rounded-full bg-orange-100 text-orange-600 flex items-center justify-center flex-shrink-0"><Bot className="w-4 h-4" /></div>
                <div className="flex-1 min-w-0">
                  {sandboxResult.error ? (
                    <div className="px-4 py-3 rounded-xl bg-red-50 border border-red-200 text-sm text-red-700">{sandboxResult.error}</div>
                  ) : (
                    <div className="px-4 py-3 rounded-xl bg-orange-50 border border-orange-200 text-sm">
                      <p className="text-xy-text-primary">{sandboxResult.reply || sandboxResult.response || sandboxResult.text || JSON.stringify(sandboxResult)}</p>
                      {sandboxResult.intent && <p className="text-xs text-xy-text-muted mt-2">识别意图: {sandboxResult.intent}</p>}
                      {sandboxResult.latency_ms != null && <p className="text-xs text-xy-text-muted">延迟: {sandboxResult.latency_ms}ms</p>}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
