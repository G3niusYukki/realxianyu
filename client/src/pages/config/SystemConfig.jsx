import React, { useState, useEffect, useCallback, useRef } from 'react';
import { getSystemConfig, getConfigSections, saveSystemConfig } from '../../api/config';
import { api } from '../../api/index';
import { useStoreCategory, CATEGORY_META } from '../../contexts/StoreCategoryContext';
import toast from 'react-hot-toast';
import { Settings, Save, AlertCircle, RefreshCw, Send, Bell, Cookie, CheckCircle2, XCircle, ExternalLink, Info, ShieldAlert, ShieldCheck, Shield, Download, Plug, ChevronDown, ChevronUp, Activity, Timer } from 'lucide-react';

const RISK_LEVEL_CONFIG = {
  normal:  { label: '正常',     color: 'green',  icon: ShieldCheck, bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-800' },
  warning: { label: '风险预警', color: 'amber',  icon: Shield,      bg: 'bg-amber-50', border: 'border-amber-200', text: 'text-amber-800' },
  blocked: { label: '疑似封控', color: 'red',    icon: ShieldAlert,  bg: 'bg-red-50',   border: 'border-red-200',   text: 'text-red-800' },
  unknown: { label: '未检测',   color: 'gray',   icon: Shield,      bg: 'bg-gray-50',  border: 'border-gray-200',  text: 'text-gray-600' },
};

const RECOVERY_STAGE_LABELS = {
  monitoring: '监控中',
  healthy: '健康',
  recover_triggered: '恢复已触发',
  waiting_reconnect: '等待重连',
  waiting_cookie_update: '等待 Cookie 更新',
  inactive: '服务未运行',
  token_error: 'Token 异常',
};

function getRecoveryGuide(riskLevel, recoveryStage) {
  if (riskLevel === 'normal') return null;
  if (riskLevel === 'warning') {
    return {
      severity: 'warning',
      title: '风险预警',
      steps: [
        '系统检测到异常信号，建议密切观察',
        '提前准备新的 Cookie，以防需要更换',
        '如果自动回复功能正常，可暂时观察',
      ],
    };
  }
  if (riskLevel === 'blocked') {
    if (recoveryStage === 'recover_triggered' || recoveryStage === 'waiting_reconnect') {
      return {
        severity: 'info',
        title: '正在恢复中',
        steps: [
          '系统已自动触发恢复流程，请等待 20-30 秒',
          '如果超过 1 分钟仍未恢复，请尝试更新 Cookie',
          '更新后系统会自动再次尝试恢复连接',
        ],
      };
    }
    return {
      severity: 'error',
      title: '需要手动干预',
      steps: [
        '重新获取闲鱼 Cookie（使用下方的自动获取或手动复制）',
        '粘贴新 Cookie 并保存，系统会自动尝试恢复',
        '如果多次更换 Cookie 仍无法恢复，可能需要在闲鱼 App 完成安全验证',
        '验证后等待 5-10 分钟再重新获取 Cookie',
      ],
    };
  }
  return null;
}

const AI_PROVIDER_GUIDES = {
  qwen: {
    name: '百炼千问 (Qwen)',
    baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    model: 'qwen-plus-latest',
    applyUrl: 'https://bailian.console.aliyun.com/',
    tip: '推荐。兼容 OpenAI 接口，中文电商场景最稳定。支持联网搜索和多模态。',
    models: [
      { value: 'qwen-plus-latest', label: 'Qwen-Plus（推荐，性价比高）' },
      { value: 'qwen-max-latest', label: 'Qwen-Max（最强推理）' },
      { value: 'qwen-turbo-latest', label: 'Qwen-Turbo（最快速度）' },
      { value: 'qwen-flash', label: 'Qwen-Flash（极速低成本）' },
      { value: 'qwen3-max', label: 'Qwen3-Max（Qwen3 旗舰）' },
      { value: 'qwen3.5-plus', label: 'Qwen3.5-Plus（最新一代）' },
      { value: 'qwq-plus-latest', label: 'QwQ-Plus（深度思考）' },
      { value: 'qwen3-coder-plus', label: 'Qwen3-Coder-Plus（代码优化）' },
      { value: 'qwen3-235b-a22b', label: 'Qwen3-235B（开源免费）' },
      { value: 'qwen3-32b', label: 'Qwen3-32B（开源免费）' },
    ],
  },
  deepseek: {
    name: 'DeepSeek',
    baseUrl: 'https://api.deepseek.com/v1',
    model: 'deepseek-chat',
    applyUrl: 'https://platform.deepseek.com/',
    tip: '性价比高，长文本能力强，适合复杂商品描述场景。',
    models: [
      { value: 'deepseek-chat', label: 'DeepSeek-Chat（通用对话）' },
      { value: 'deepseek-reasoner', label: 'DeepSeek-Reasoner（深度推理）' },
    ],
  },
  openai: {
    name: 'OpenAI',
    baseUrl: 'https://api.openai.com/v1',
    model: 'gpt-4o-mini',
    applyUrl: 'https://platform.openai.com/',
    tip: '需海外网络，英文能力最强，中文电商场景建议搭配 System Prompt 优化。',
    models: [
      { value: 'gpt-4o-mini', label: 'GPT-4o Mini（经济实惠）' },
      { value: 'gpt-4o', label: 'GPT-4o（强力多模态）' },
      { value: 'gpt-4.1-mini', label: 'GPT-4.1 Mini（最新轻量）' },
      { value: 'gpt-4.1', label: 'GPT-4.1（最新旗舰）' },
    ],
  },
};

export default function SystemConfig() {
  const { category, switchCategory } = useStoreCategory();
  const [sections, setSections] = useState([]);
  const [config, setConfig] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('');

  const [cookieText, setCookieText] = useState('');
  const [cookieValidating, setCookieValidating] = useState(false);
  const [cookieResult, setCookieResult] = useState(null);
  const [currentCookieHealth, setCurrentCookieHealth] = useState(null);

  const [riskStatus, setRiskStatus] = useState(null);
  const [autoGrabbing, setAutoGrabbing] = useState(false);
  const [autoGrabProgress, setAutoGrabProgress] = useState(null);
  const [pluginGuideOpen, setPluginGuideOpen] = useState(false);
  const [pluginImporting, setPluginImporting] = useState(false);
  const [xgjTesting, setXgjTesting] = useState(false);
  const [xgjTestResult, setXgjTestResult] = useState(null);
  const [aiTesting, setAiTesting] = useState(false);
  const [aiTestResult, setAiTestResult] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(null);
  const eventSourceRef = useRef(null);
  const pluginFileRef = useRef(null);
  const refreshTimerRef = useRef(null);

  const fetchAutoRefreshStatus = useCallback(async () => {
    try {
      const res = await api.get('/cookie/auto-refresh/status');
      setAutoRefresh(res.data);
    } catch { setAutoRefresh(null); }
  }, []);

  useEffect(() => {
    fetchConfig();
    fetchAutoRefreshStatus();
    refreshTimerRef.current = setInterval(fetchAutoRefreshStatus, 30000);
    return () => {
      if (eventSourceRef.current) eventSourceRef.current.close();
      if (refreshTimerRef.current) clearInterval(refreshTimerRef.current);
    };
  }, [fetchAutoRefreshStatus]);

  const fetchConfig = async () => {
    setLoading(true);
    try {
      const [secRes, cfgRes] = await Promise.all([
        getConfigSections(),
        getSystemConfig()
      ]);
      
      if (secRes.data?.ok) {
        const secs = secRes.data.sections || [];
        const storeSection = { key: 'store_category', name: '店铺品类' };
        const cookieSection = { key: 'cookie', name: 'Cookie 配置' };
        setSections([storeSection, cookieSection, ...secs]);
        setActiveTab('store_category');
      }
      
      if (cfgRes.data?.ok) {
        setConfig(cfgRes.data.config || {});
      }

      try {
        const [healthRes, statusRes] = await Promise.all([
          api.get('/health/check'),
          api.get('/service-status').catch(() => null),
        ]);
        if (healthRes.data?.cookie) {
          setCurrentCookieHealth(healthRes.data.cookie);
        }
        if (statusRes?.data) {
          setRiskStatus({
            risk_control: statusRes.data.risk_control,
            recovery: statusRes.data.recovery,
            recovery_stage: statusRes.data.recovery_stage,
            token_error: statusRes.data.token_error,
            service_status: statusRes.data.service_status,
          });
        }
      } catch (_) {}
    } catch (e) {
      toast.error('加载配置失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const res = await saveSystemConfig(config);
      if (res.data?.ok) {
        toast.success('配置保存成功');
        setConfig(res.data.config || config);
      } else {
        toast.error(res.data?.error || '保存失败');
      }
    } catch (e) {
      toast.error('保存出错');
    } finally {
      setSaving(false);
    }
  };

  const [testingSend, setTestingSend] = useState(null);

  const handleChange = (sectionKey, fieldKey, value) => {
    setConfig(prev => ({
      ...prev,
      [sectionKey]: {
        ...(prev[sectionKey] || {}),
        [fieldKey]: value
      }
    }));
  };

  const handleTestNotification = async (channel) => {
    const notifyCfg = config.notifications || {};
    const webhookKey = channel === 'feishu' ? 'feishu_webhook' : 'wechat_webhook';
    const webhookUrl = notifyCfg[webhookKey] || '';
    if (!webhookUrl || webhookUrl.includes('****')) {
      toast.error('请先填写并保存 Webhook URL');
      return;
    }
    setTestingSend(channel);
    try {
      const res = await api.post('/notifications/test', { channel, webhook_url: webhookUrl });
      if (res.data?.ok) {
        toast.success(channel === 'feishu' ? '飞书测试消息发送成功' : '企业微信测试消息发送成功');
      } else {
        toast.error(res.data?.error || '发送失败');
      }
    } catch (err) {
      toast.error('发送失败: ' + (err?.response?.data?.error || err.message));
    } finally {
      setTestingSend(null);
    }
  };

  const handleCookieValidate = useCallback(async () => {
    if (!cookieText.trim()) {
      toast.error('请先粘贴 Cookie');
      return;
    }
    setCookieValidating(true);
    setCookieResult(null);
    try {
      const res = await api.post('/cookie/validate', { cookie: cookieText });
      setCookieResult(res.data);
    } catch (err) {
      setCookieResult({ ok: false, grade: 'F', message: err?.response?.data?.message || '验证失败' });
    } finally {
      setCookieValidating(false);
    }
  }, [cookieText]);

  const handleCookieSave = useCallback(async () => {
    if (!cookieText.trim()) return;
    setSaving(true);
    try {
      const res = await api.post('/update-cookie', { cookie: cookieText });
      if (res.data?.success) {
        toast.success('Cookie 更新成功');
        setCookieResult({ ok: true, grade: res.data.cookie_grade || 'A', message: 'Cookie 已保存并生效' });
        setCurrentCookieHealth({ ok: true, message: '刚刚更新' });
      } else {
        toast.error(res.data?.error || '保存失败');
      }
    } catch (err) {
      toast.error('保存出错');
    } finally {
      setSaving(false);
    }
  }, [cookieText]);

  const handleAutoGrab = useCallback(async () => {
    setAutoGrabbing(true);
    setAutoGrabProgress(null);
    try {
      await api.post('/cookie/auto-grab');
      const es = new EventSource('/api/cookie/auto-grab/status');
      eventSourceRef.current = es;
      es.onmessage = (evt) => {
        try {
          const data = JSON.parse(evt.data);
          setAutoGrabProgress(data);
          if (data.stage === 'done' || data.stage === 'error' || data.stage === 'cancelled') {
            es.close();
            eventSourceRef.current = null;
            setAutoGrabbing(false);
            if (data.stage === 'done') {
              toast.success('Cookie 自动获取成功');
              fetchConfig();
            } else if (data.error) {
              toast.error(`自动获取失败: ${data.error}`);
            }
          }
        } catch (_) {}
      };
      es.onerror = () => {
        es.close();
        eventSourceRef.current = null;
        setAutoGrabbing(false);
      };
    } catch (err) {
      toast.error('启动自动获取失败: ' + (err?.response?.data?.error || err.message));
      setAutoGrabbing(false);
    }
  }, []);

  const handleCancelAutoGrab = useCallback(async () => {
    try {
      await api.post('/cookie/auto-grab/cancel');
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      setAutoGrabbing(false);
      setAutoGrabProgress(null);
      toast.success('已取消自动获取');
    } catch (_) {}
  }, []);

  const handleDownloadPlugin = useCallback(() => {
    window.open('/api/download-cookie-plugin', '_blank');
  }, []);

  const handlePluginFileImport = useCallback(async (e) => {
    const files = e.target.files;
    if (!files?.length) return;
    setPluginImporting(true);
    const formData = new FormData();
    Array.from(files).forEach(f => formData.append('file', f));
    try {
      const res = await api.post('/import-cookie-plugin', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      if (res.data?.success) {
        toast.success('Cookie 导入成功');
        setCurrentCookieHealth({ ok: true, message: '插件导入更新' });
        fetchConfig();
      } else {
        toast.error(res.data?.error || '导入失败');
      }
    } catch (err) {
      toast.error('导入失败: ' + (err?.response?.data?.error || err.message));
    } finally {
      setPluginImporting(false);
      if (pluginFileRef.current) pluginFileRef.current.value = '';
    }
  }, []);

  const handleXgjTest = useCallback(async () => {
    setXgjTesting(true);
    setXgjTestResult(null);
    try {
      const res = await api.get('/health/check');
      const xgj = res.data?.xgj;
      if (xgj?.ok) {
        setXgjTestResult({ ok: true, message: `连接成功（延迟 ${xgj.latency_ms || '?'}ms）` });
        toast.success('闲管家连接测试成功');
      } else {
        setXgjTestResult({ ok: false, message: xgj?.message || '连接失败' });
        toast.error('闲管家连接失败: ' + (xgj?.message || '未知错误'));
      }
    } catch (err) {
      setXgjTestResult({ ok: false, message: err.message || '请求失败' });
      toast.error('连接测试异常');
    } finally {
      setXgjTesting(false);
    }
  }, []);

  const handleAiTest = useCallback(async () => {
    const aiCfg = config.ai || {};
    const provider = aiCfg.provider || 'qwen';
    const guide = AI_PROVIDER_GUIDES[provider];
    const api_key = aiCfg.api_key || '';
    const base_url = aiCfg.base_url || guide?.baseUrl || '';
    const model = aiCfg.model || guide?.model || 'qwen-plus';
    if (!api_key) {
      setAiTestResult({ ok: false, message: '请先填写 API Key' });
      toast.error('请先填写 API Key');
      return;
    }
    setAiTesting(true);
    setAiTestResult(null);
    try {
      const res = await api.post('/ai/test', { api_key, base_url, model });
      if (res.data?.ok) {
        setAiTestResult({ ok: true, message: res.data.message });
        toast.success('AI 连接测试成功');
      } else {
        setAiTestResult({ ok: false, message: res.data?.message || '连接失败' });
        toast.error('AI 连接失败: ' + (res.data?.message || '未知错误'));
      }
    } catch (err) {
      const msg = err?.response?.data?.message || err.message || '请求失败';
      setAiTestResult({ ok: false, message: msg });
      toast.error('AI 测试异常: ' + msg);
    } finally {
      setAiTesting(false);
    }
  }, [config.ai]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <RefreshCw className="w-8 h-8 animate-spin text-xy-brand-500" />
      </div>
    );
  }

  const currentSection = sections.find(s => s.key === activeTab);
  const selectedProvider = config.ai?.provider || 'qwen';
  const providerGuide = AI_PROVIDER_GUIDES[selectedProvider];

  const riskLevel = riskStatus?.risk_control?.level || 'unknown';
  const riskCfg = RISK_LEVEL_CONFIG[riskLevel] || RISK_LEVEL_CONFIG.unknown;
  const recoveryStage = riskStatus?.recovery_stage || 'monitoring';
  const recoveryGuide = getRecoveryGuide(riskLevel, recoveryStage);
  const RiskIcon = riskCfg.icon;

  const renderCookieSection = () => (
    <div className="xy-card p-6 animate-in fade-in slide-in-from-right-4">
      <h2 className="text-lg font-bold text-xy-text-primary mb-6 pb-4 border-b border-xy-border">
        Cookie 配置
      </h2>

      <div className="space-y-6 max-w-2xl">
        {/* Cookie 健康状态 */}
        <div className={`flex items-center gap-3 px-4 py-3 rounded-lg border ${
          currentCookieHealth?.ok 
            ? 'bg-green-50 border-green-200 text-green-800' 
            : 'bg-amber-50 border-amber-200 text-amber-800'
        }`}>
          {currentCookieHealth?.ok 
            ? <CheckCircle2 className="w-5 h-5 text-green-600" /> 
            : <AlertCircle className="w-5 h-5 text-amber-600" />}
          <div>
            <span className="font-medium">当前状态：</span>
            {currentCookieHealth?.ok ? '正常' : (currentCookieHealth?.message || '未配置或已过期')}
          </div>
        </div>

        {/* 风控状态面板 */}
        {riskStatus?.risk_control && (
          <div className={`px-4 py-3 rounded-lg border ${riskCfg.bg} ${riskCfg.border} ${riskCfg.text}`}>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <RiskIcon className="w-5 h-5" />
                <span className="font-medium">风控状态：{riskCfg.label}</span>
              </div>
              {riskStatus.risk_control.updated_at && (
                <span className="text-xs opacity-70">
                  {new Date(riskStatus.risk_control.updated_at).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                </span>
              )}
            </div>
            {riskStatus.risk_control.signals?.length > 0 && riskLevel !== 'normal' && (
              <div className="text-sm mb-2">
                <span className="font-medium">信号：</span>
                {riskStatus.risk_control.signals.join('、')}
              </div>
            )}
            {typeof riskStatus.risk_control.score === 'number' && riskLevel !== 'normal' && (
              <div className="flex items-center gap-2 text-sm">
                <span className="font-medium">风险分：</span>
                <div className="flex-1 h-2 bg-white/60 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${riskLevel === 'blocked' ? 'bg-red-500' : 'bg-amber-500'}`}
                    style={{ width: `${Math.min(riskStatus.risk_control.score, 100)}%` }}
                  />
                </div>
                <span className="text-xs font-mono">{riskStatus.risk_control.score}/100</span>
              </div>
            )}
          </div>
        )}

        {/* 自动恢复状态 */}
        {riskStatus?.recovery && riskLevel !== 'normal' && riskLevel !== 'unknown' && (
          <div className="px-4 py-3 rounded-lg border border-indigo-200 bg-indigo-50 text-indigo-800 text-sm">
            <div className="flex items-center gap-2 mb-1">
              <RefreshCw className={`w-4 h-4 ${recoveryStage === 'recover_triggered' ? 'animate-spin' : ''}`} />
              <span className="font-medium">
                恢复状态：{RECOVERY_STAGE_LABELS[recoveryStage] || recoveryStage}
              </span>
            </div>
            {riskStatus.recovery.advice && (
              <p className="ml-6 text-indigo-700">{riskStatus.recovery.advice}</p>
            )}
            <div className="ml-6 mt-1 flex gap-4 text-xs text-indigo-600">
              {riskStatus.recovery.last_auto_recover_at && (
                <span>上次恢复: {new Date(riskStatus.recovery.last_auto_recover_at).toLocaleTimeString('zh-CN')}</span>
              )}
              {riskStatus.recovery.auto_recover_triggered && (
                <span className="font-medium text-indigo-800">已自动触发恢复</span>
              )}
            </div>
          </div>
        )}

        {/* 恢复操作指南 */}
        {recoveryGuide && (
          <div className={`px-4 py-3 rounded-lg border text-sm ${
            recoveryGuide.severity === 'error' ? 'border-red-200 bg-red-50 text-red-800'
            : recoveryGuide.severity === 'warning' ? 'border-amber-200 bg-amber-50 text-amber-800'
            : 'border-blue-200 bg-blue-50 text-blue-800'
          }`}>
            <p className="font-medium mb-2 flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              {recoveryGuide.title}
            </p>
            <ol className="list-decimal list-inside space-y-1 ml-2">
              {recoveryGuide.steps.map((step, i) => <li key={i}>{step}</li>)}
            </ol>
          </div>
        )}

        {/* Cookie 输入 */}
        <div>
          <label className="xy-label">粘贴 Cookie</label>
          <textarea
            className="xy-input px-3 py-2 h-32 font-mono text-xs"
            placeholder={'支持以下格式：\n1. HTTP Header: cookie2=xxx; sgcookie=yyy; ...\n2. JSON: [{"name":"cookie2","value":"xxx"}, ...]\n3. Netscape cookies.txt\n4. DevTools 表格复制'}
            value={cookieText}
            onChange={e => { setCookieText(e.target.value); setCookieResult(null); }}
          />
        </div>

        {/* 操作按钮组 */}
        <div className="flex flex-wrap gap-3">
          <button
            onClick={handleCookieValidate}
            disabled={cookieValidating || !cookieText.trim()}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg border border-xy-brand-300 text-xy-brand-700 bg-xy-brand-50 hover:bg-xy-brand-100 transition-colors disabled:opacity-50"
          >
            {cookieValidating ? <RefreshCw className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
            验证 Cookie
          </button>
          <button
            onClick={handleCookieSave}
            disabled={saving || !cookieText.trim()}
            className="xy-btn-primary flex items-center gap-2"
          >
            {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            保存并生效
          </button>
          {!autoGrabbing ? (
            <button
              onClick={handleAutoGrab}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg border border-emerald-300 text-emerald-700 bg-emerald-50 hover:bg-emerald-100 transition-colors"
            >
              <Download className="w-4 h-4" />
              自动获取
            </button>
          ) : (
            <button
              onClick={handleCancelAutoGrab}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg border border-red-300 text-red-700 bg-red-50 hover:bg-red-100 transition-colors"
            >
              <XCircle className="w-4 h-4" />
              取消获取
            </button>
          )}
          <button
            onClick={() => setPluginGuideOpen(v => !v)}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg border transition-colors ${
              pluginGuideOpen
                ? 'border-purple-400 text-purple-800 bg-purple-100'
                : 'border-purple-300 text-purple-700 bg-purple-50 hover:bg-purple-100'
            }`}
          >
            <Plug className="w-4 h-4" />
            Cookie 插件
            {pluginGuideOpen ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </button>
        </div>

        {/* 插件引导面板 */}
        {pluginGuideOpen && (
          <div className="px-5 py-4 rounded-lg border border-purple-200 bg-gradient-to-b from-purple-50 to-white text-sm space-y-4">
            <h4 className="font-bold text-purple-900 flex items-center gap-2">
              <Plug className="w-4 h-4" />
              Cookie 插件获取引导
            </h4>

            <div className="space-y-3">
              <div className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-purple-600 text-white text-xs font-bold flex items-center justify-center">1</span>
                <div className="flex-1">
                  <p className="font-medium text-purple-900">下载插件包</p>
                  <p className="text-purple-700 mt-0.5">系统内置 Get cookies.txt LOCALLY 插件（开源安全，不会外传数据）</p>
                  <button
                    onClick={handleDownloadPlugin}
                    className="mt-2 flex items-center gap-2 px-3 py-1.5 text-xs font-medium rounded-md border border-purple-300 text-purple-700 bg-white hover:bg-purple-50 transition-colors"
                  >
                    <Download className="w-3.5 h-3.5" />
                    下载插件包 (.zip)
                  </button>
                </div>
              </div>

              <div className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-purple-600 text-white text-xs font-bold flex items-center justify-center">2</span>
                <div className="flex-1">
                  <p className="font-medium text-purple-900">安装到浏览器</p>
                  <ol className="text-purple-700 mt-0.5 list-decimal list-inside space-y-0.5">
                    <li>解压下载的 zip 文件</li>
                    <li>打开 Chrome，地址栏输入 <code className="text-xs bg-purple-100 px-1 rounded">chrome://extensions</code></li>
                    <li>右上角打开「开发者模式」开关</li>
                    <li>点击「加载已解压的扩展程序」，选择解压后的 <code className="text-xs bg-purple-100 px-1 rounded">src</code> 文件夹</li>
                  </ol>
                </div>
              </div>

              <div className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-purple-600 text-white text-xs font-bold flex items-center justify-center">3</span>
                <div className="flex-1">
                  <p className="font-medium text-purple-900">导出 Cookie</p>
                  <ol className="text-purple-700 mt-0.5 list-decimal list-inside space-y-0.5">
                    <li>打开 <a href="https://www.goofish.com" target="_blank" rel="noreferrer" className="underline">闲鱼网页版</a> 并登录账号</li>
                    <li>点击浏览器工具栏中的插件图标</li>
                    <li>选择导出格式（Netscape 或 JSON 均可），点击「Export」下载文件</li>
                  </ol>
                </div>
              </div>

              <div className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-purple-600 text-white text-xs font-bold flex items-center justify-center">4</span>
                <div className="flex-1">
                  <p className="font-medium text-purple-900">导入到系统</p>
                  <p className="text-purple-700 mt-0.5">选择导出的文件，系统自动解析并更新 Cookie</p>
                  <div className="mt-2 flex items-center gap-3">
                    <input
                      ref={pluginFileRef}
                      type="file"
                      accept=".txt,.json,.log,.cookies,.csv,.tsv,.har,.zip"
                      onChange={handlePluginFileImport}
                      className="hidden"
                      id="plugin-cookie-file"
                    />
                    <label
                      htmlFor="plugin-cookie-file"
                      className={`flex items-center gap-2 px-3 py-1.5 text-xs font-medium rounded-md border cursor-pointer transition-colors ${
                        pluginImporting
                          ? 'border-gray-300 text-gray-400 bg-gray-50 cursor-not-allowed'
                          : 'border-purple-300 text-purple-700 bg-white hover:bg-purple-50'
                      }`}
                    >
                      {pluginImporting ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
                      {pluginImporting ? '导入中...' : '选择文件并导入'}
                    </label>
                    <span className="text-xs text-purple-500">支持 .txt / .json / .zip 格式</span>
                  </div>
                </div>
              </div>
            </div>

            <p className="text-xs text-purple-500 border-t border-purple-100 pt-2">
              也可从 <a href="https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc" target="_blank" rel="noreferrer" className="underline">Chrome 应用商店</a> 直接安装，或将导出内容直接粘贴到上方输入框。
            </p>
          </div>
        )}

        {/* 自动获取进度 */}
        {autoGrabbing && autoGrabProgress && (
          <div className="px-4 py-3 rounded-lg border border-emerald-200 bg-emerald-50 text-emerald-800 text-sm">
            <div className="flex items-center gap-2 mb-2">
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span className="font-medium">{autoGrabProgress.message || '正在获取...'}</span>
            </div>
            {autoGrabProgress.hint && (
              <p className="text-emerald-700 ml-6">{autoGrabProgress.hint}</p>
            )}
            {typeof autoGrabProgress.progress === 'number' && autoGrabProgress.progress > 0 && (
              <div className="ml-6 mt-2 h-2 bg-emerald-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-emerald-500 rounded-full transition-all"
                  style={{ width: `${Math.min(autoGrabProgress.progress, 100)}%` }}
                />
              </div>
            )}
            {autoGrabProgress.error && (
              <p className="ml-6 mt-1 text-red-600">{autoGrabProgress.error}</p>
            )}
          </div>
        )}

        {/* 验证结果 */}
        {cookieResult && (
          <div className={`px-4 py-3 rounded-lg border text-sm ${
            cookieResult.ok 
              ? 'bg-green-50 border-green-200 text-green-800' 
              : 'bg-red-50 border-red-200 text-red-800'
          }`}>
            <div className="flex items-center gap-2 mb-1">
              {cookieResult.ok ? <CheckCircle2 className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
              <span className="font-medium">
                评级: {cookieResult.grade} — {cookieResult.ok ? 'Cookie 有效' : 'Cookie 无效'}
              </span>
            </div>
            {cookieResult.message && <p className="ml-6">{cookieResult.message}</p>}
            {cookieResult.actions?.length > 0 && (
              <ul className="ml-6 mt-1 list-disc list-inside">
                {cookieResult.actions.map((a, i) => <li key={i}>{a}</li>)}
              </ul>
            )}
            {cookieResult.required_missing?.length > 0 && (
              <p className="ml-6 mt-1">缺少字段：{cookieResult.required_missing.join(', ')}</p>
            )}
          </div>
        )}
      </div>

      {/* Cookie 自动刷新状态 */}
      {autoRefresh && (
        <div className="mt-6 p-4 rounded-lg border border-xy-border bg-xy-surface">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-xy-brand-500" />
              <h4 className="font-bold text-xy-text-primary text-sm">Cookie 自动刷新</h4>
            </div>
            <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${autoRefresh.enabled ? 'bg-green-50 text-green-700' : 'bg-xy-gray-100 text-xy-text-secondary'}`}>
              <span className={`w-1.5 h-1.5 rounded-full ${autoRefresh.enabled ? 'bg-green-500' : 'bg-xy-gray-400'}`} />
              {autoRefresh.enabled ? '已启用' : '未启用'}
            </span>
          </div>
          {autoRefresh.enabled ? (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
              <div className="p-3 bg-xy-gray-50 rounded-lg">
                <p className="text-xy-text-secondary text-xs mb-1">检查间隔</p>
                <p className="font-medium text-xy-text-primary">每 {autoRefresh.interval_minutes} 分钟</p>
              </div>
              <div className="p-3 bg-xy-gray-50 rounded-lg">
                <p className="text-xy-text-secondary text-xs mb-1">上次检查</p>
                <p className="font-medium text-xy-text-primary">
                  {autoRefresh.last_check_at > 0
                    ? new Date(autoRefresh.last_check_at * 1000).toLocaleTimeString()
                    : '尚未检查'}
                </p>
                {autoRefresh.last_check_ok !== null && (
                  <p className={`text-xs mt-0.5 ${autoRefresh.last_check_ok ? 'text-green-600' : 'text-orange-600'}`}>
                    {autoRefresh.last_check_message || (autoRefresh.last_check_ok ? '健康' : '异常')}
                  </p>
                )}
              </div>
              <div className="p-3 bg-xy-gray-50 rounded-lg">
                <p className="text-xy-text-secondary text-xs mb-1">下次检查</p>
                <p className="font-medium text-xy-text-primary flex items-center gap-1">
                  <Timer className="w-3.5 h-3.5" />
                  {autoRefresh.next_check_in_seconds > 0
                    ? `${Math.ceil(autoRefresh.next_check_in_seconds / 60)} 分钟后`
                    : '即将执行'}
                </p>
              </div>
              {autoRefresh.total_refreshes > 0 && (
                <div className="sm:col-span-3 p-3 bg-green-50 rounded-lg border border-green-200">
                  <p className="text-sm text-green-700">
                    <strong>上次静默刷新：</strong>
                    {new Date(autoRefresh.last_refresh_at * 1000).toLocaleString()}
                    {' — '}
                    {autoRefresh.last_refresh_ok ? '成功' : '失败'}
                    {autoRefresh.total_refreshes > 1 && ` (累计 ${autoRefresh.total_refreshes} 次)`}
                  </p>
                </div>
              )}
            </div>
          ) : (
            <p className="text-sm text-xy-text-secondary">
              {autoRefresh.message || '设置环境变量 COOKIE_AUTO_REFRESH=true 可启用自动刷新，系统将定期检查 Cookie 有效性并在失效时自动从浏览器获取新 Cookie。'}
            </p>
          )}
        </div>
      )}

      {/* Cookie 获取指南 */}
      <div className="mt-8 bg-blue-50 border border-blue-200 p-4 rounded-lg text-blue-800 text-sm">
        <div className="flex items-start gap-3">
          <Info className="w-5 h-5 flex-shrink-0 mt-0.5 text-blue-600" />
          <div>
            <p className="font-medium mb-2">Cookie 获取指南</p>
            <p className="text-blue-700 mb-2 font-medium">方式一：手动获取</p>
            <ol className="list-decimal list-inside space-y-1 text-blue-700">
              <li>使用 Chrome 浏览器打开 <a href="https://www.goofish.com" target="_blank" rel="noreferrer" className="underline">闲鱼网页版</a> 并登录</li>
              <li>按 F12 打开开发者工具，切换到「Network / 网络」标签</li>
              <li>刷新页面，选择任意请求，在 Headers 中找到 Cookie 字段</li>
              <li>右键「Copy value」，粘贴到上方输入框</li>
            </ol>
            <p className="mt-3 text-blue-700 font-medium">方式二：浏览器插件（推荐）</p>
            <ol className="list-decimal list-inside space-y-1 text-blue-700">
              <li>点击上方「Cookie 插件」按钮，按引导下载并安装内置插件</li>
              <li>打开闲鱼网页版并登录，点击插件图标导出 Cookie 文件</li>
              <li>在引导面板第 4 步选择文件导入，或将内容粘贴到上方输入框</li>
            </ol>
            <p className="mt-3 text-blue-700 font-medium">方式三：自动获取</p>
            <p className="text-blue-700">点击上方「自动获取」按钮，系统支持三种降级策略：浏览器数据库直读（零操作）、复用 Chrome 登录态（静默）、全新窗口扫码登录。</p>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="xy-page max-w-5xl xy-enter">
      <div className="flex flex-col md:flex-row justify-between md:items-end gap-4 mb-6">
        <div>
          <h1 className="xy-title flex items-center gap-2">
            <Settings className="w-6 h-6 text-xy-brand-500" /> 系统与店铺配置
          </h1>
          <p className="xy-subtitle mt-1">管理 Cookie、AI 提供商、告警通知以及自动化核心设置</p>
        </div>
        {activeTab !== 'cookie' && activeTab !== 'store_category' && (
          <button
            onClick={handleSave}
            disabled={saving}
            className="xy-btn-primary flex items-center gap-2"
          >
            {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            保存设置
          </button>
        )}
      </div>

      <div className="flex flex-col md:flex-row gap-6">
        <div className="md:w-64 flex-shrink-0">
          <div className="xy-card overflow-hidden">
            <div className="flex flex-col">
              {sections.map(sec => (
                <button
                  key={sec.key}
                  onClick={() => setActiveTab(sec.key)}
                  className={`text-left px-5 py-4 text-sm font-medium transition-colors border-l-4 ${
                    activeTab === sec.key 
                      ? 'border-l-xy-brand-500 bg-xy-brand-50 text-xy-brand-600' 
                      : 'border-l-transparent text-xy-text-secondary hover:bg-xy-gray-50'
                  }`}
                >
                  {sec.key === 'cookie' && <Cookie className="w-4 h-4 inline mr-2" />}
                  {sec.name}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="flex-1">
          {activeTab === 'store_category' && (
            <div className="xy-card p-6 animate-in fade-in slide-in-from-right-4">
              <h2 className="text-lg font-bold text-xy-text-primary mb-1">店铺品类</h2>
              <p className="text-sm text-xy-text-secondary mb-6">选择你的主营品类，系统将根据品类自动适配功能、话术模板和合规规则</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {Object.entries(CATEGORY_META).map(([key, meta]) => (
                  <button
                    key={key}
                    onClick={() => switchCategory(key)}
                    className={`text-left p-4 rounded-xl border-2 transition-all ${
                      category === key
                        ? 'border-xy-brand-500 bg-orange-50 ring-2 ring-xy-brand-200'
                        : 'border-xy-border hover:border-xy-brand-300 hover:bg-xy-gray-50'
                    }`}
                  >
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-2xl">{meta.icon}</span>
                      <span className="font-bold text-xy-text-primary">{meta.label}</span>
                      {category === key && (
                        <span className="ml-auto text-xs font-medium text-xy-brand-600 bg-xy-brand-100 px-2 py-0.5 rounded-full">当前</span>
                      )}
                    </div>
                    <p className="text-sm text-xy-text-secondary">{meta.desc}</p>
                  </button>
                ))}
              </div>
              <div className="mt-6 p-4 bg-blue-50 rounded-xl border border-blue-200">
                <p className="text-sm text-blue-700">
                  <strong>提示：</strong>切换品类后，导航栏和功能面板将自动显示/隐藏与该品类相关的功能模块。
                  快递代发品类包含路线管理、加价规则等；虚拟品类包含卡密管理、自动发货等。
                  通用功能（Cookie、AI、消息）始终可用。
                </p>
              </div>
            </div>
          )}

          {activeTab === 'cookie' && renderCookieSection()}

          {currentSection && currentSection.key !== 'cookie' && currentSection.key !== 'store_category' && (
            <div className="xy-card p-6 animate-in fade-in slide-in-from-right-4">
              <h2 className="text-lg font-bold text-xy-text-primary mb-6 pb-4 border-b border-xy-border">
                {currentSection.name}
              </h2>
              
              <div className="space-y-6 max-w-2xl">
                {currentSection.fields?.map(field => {
                  const sectionData = config[currentSection.key] || {};
                  const value = sectionData[field.key] !== undefined ? sectionData[field.key] : (field.default || '');

                  if (field.required_when) {
                    const [condKey, condVal] = Object.entries(field.required_when)[0];
                    const actual = sectionData[condKey] !== undefined ? sectionData[condKey] : (currentSection.fields.find(f => f.key === condKey)?.default || '');
                    if (actual !== condVal) return null;
                  }

                  const isConditionalRequired = field.required_when && (() => {
                    const [condKey, condVal] = Object.entries(field.required_when)[0];
                    const actual = sectionData[condKey] !== undefined ? sectionData[condKey] : '';
                    return actual === condVal;
                  })();

                  return (
                    <div key={field.key}>
                      <label className="xy-label flex items-center justify-between">
                        <span>
                          {field.label}
                          {(field.required || isConditionalRequired) && <span className="text-red-500 ml-1">*</span>}
                        </span>
                      </label>
                      
                      {field.type === 'textarea' ? (
                        <textarea
                          className="xy-input px-3 py-2 h-24"
                          value={value}
                          placeholder={field.placeholder || ''}
                          onChange={(e) => handleChange(currentSection.key, field.key, e.target.value)}
                        />
                      ) : field.type === 'select' ? (
                        <select
                          className="xy-input px-3 py-2"
                          value={value}
                          onChange={(e) => handleChange(currentSection.key, field.key, e.target.value)}
                        >
                          {field.options?.map(opt => (
                            <option key={opt} value={opt}>{field.labels?.[opt] || opt}</option>
                          ))}
                        </select>
                      ) : field.type === 'combobox' ? (() => {
                        const providerModels = currentSection.key === 'ai'
                          ? (AI_PROVIDER_GUIDES[sectionData.provider || 'qwen']?.models || [])
                          : (field.options || []).map(o => typeof o === 'string' ? { value: o, label: o } : o);
                        const optionValues = providerModels.map(m => m.value);
                        const isCustom = value && !optionValues.includes(value);
                        return (
                          <div className="space-y-2">
                            <select
                              className="xy-input px-3 py-2"
                              value={isCustom ? '__custom__' : value}
                              onChange={(e) => {
                                if (e.target.value === '__custom__') {
                                  handleChange(currentSection.key, field.key, '');
                                } else {
                                  handleChange(currentSection.key, field.key, e.target.value);
                                }
                              }}
                            >
                              {providerModels.map(m => (
                                <option key={m.value} value={m.value}>{m.label}</option>
                              ))}
                              <option value="__custom__">自定义模型...</option>
                            </select>
                            {isCustom && (
                              <input
                                type="text"
                                className="xy-input px-3 py-2"
                                value={value}
                                placeholder="输入自定义模型名称，如 qwen-plus-2025-01-25"
                                onChange={(e) => handleChange(currentSection.key, field.key, e.target.value)}
                              />
                            )}
                          </div>
                        );
                      })() : field.type === 'toggle' ? (
                        <button
                          className={`w-12 h-6 rounded-full transition-colors relative ${value ? 'bg-green-500' : 'bg-gray-300'}`}
                          onClick={() => handleChange(currentSection.key, field.key, !value)}
                        >
                          <div className={`absolute top-1 bg-white w-4 h-4 rounded-full transition-transform ${value ? 'left-7' : 'left-1'}`}></div>
                        </button>
                      ) : (
                        <input
                          type={field.type || 'text'}
                          className="xy-input px-3 py-2"
                          value={value}
                          placeholder={field.placeholder || ''}
                          onChange={(e) => handleChange(currentSection.key, field.key, e.target.value)}
                        />
                      )}
                      {field.hint && (
                        <p className="text-xs text-gray-400 mt-1">{field.hint}</p>
                      )}
                    </div>
                  );
                })}
              </div>
              
              {currentSection.key === 'xianguanjia' && (
                <div className="mt-8 space-y-4">
                  {/* 连接测试 */}
                  <div className="flex items-center gap-3">
                    <button
                      onClick={handleXgjTest}
                      disabled={xgjTesting}
                      className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg border border-orange-300 text-orange-700 bg-orange-50 hover:bg-orange-100 transition-colors disabled:opacity-50"
                    >
                      {xgjTesting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                      测试连接
                    </button>
                    {xgjTestResult && (
                      <span className={`text-sm flex items-center gap-1 ${xgjTestResult.ok ? 'text-green-600' : 'text-red-600'}`}>
                        {xgjTestResult.ok ? <CheckCircle2 className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                        {xgjTestResult.message}
                      </span>
                    )}
                  </div>

                  {/* 从零开始引导 */}
                  <div className="bg-gradient-to-r from-orange-50 to-amber-50 border border-orange-200 p-5 rounded-lg text-sm">
                    <h3 className="font-bold text-orange-900 mb-3 flex items-center gap-2">
                      <Info className="w-4 h-4" />
                      新手引导：从零配置闲管家
                    </h3>
                    <ol className="list-decimal list-inside space-y-2 text-orange-800">
                      <li>
                        <strong>注册开放平台账号</strong> — 前往
                        <a href="https://www.goofish.pro" target="_blank" rel="noreferrer" className="underline ml-1">闲管家官网</a>
                        ，使用闲鱼/淘宝账号登录
                      </li>
                      <li>
                        <strong>创建应用</strong> — 登录后在「我的应用」中新建应用，获取 <strong>AppKey</strong> 和 <strong>AppSecret</strong>
                      </li>
                      <li>
                        <strong>选择接入模式</strong>
                        <ul className="ml-6 mt-1 space-y-1 list-disc list-inside text-orange-700">
                          <li><strong>自研应用</strong>：个人卖家或自有系统直连，只需 AppKey + AppSecret</li>
                          <li><strong>商务对接</strong>：第三方服务商代运营，额外需要商家的 Seller ID</li>
                        </ul>
                      </li>
                      <li>
                        <strong>填入配置</strong> — 把上方字段填写完整后点击「保存设置」
                      </li>
                      <li>
                        <strong>测试连接</strong> — 点击上方「测试连接」按钮，确认显示绿色「连接成功」
                      </li>
                    </ol>
                    <div className="mt-4 pt-3 border-t border-orange-200/60">
                      <p className="text-xs text-orange-600">
                        <strong>API 网关</strong>默认为 <code className="bg-white/60 px-1 rounded">https://open.goofish.pro</code>，无需修改。
                        如遇问题，请参考
                        <a href="https://s.apifox.cn/3ac13d69-5a38-4536-ae9b-a54001854ef8" target="_blank" rel="noreferrer" className="underline ml-1">
                          开放平台文档 <ExternalLink className="w-3 h-3 inline" />
                        </a>
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {currentSection.key === 'ai' && (
                <div className="mt-8 space-y-4">
                  {/* AI 连接测试 */}
                  <div className="flex items-center gap-3">
                    <button
                      onClick={handleAiTest}
                      disabled={aiTesting}
                      className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg border border-blue-300 text-blue-700 bg-blue-50 hover:bg-blue-100 transition-colors disabled:opacity-50"
                    >
                      {aiTesting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                      测试 AI 连接
                    </button>
                    {aiTestResult && (
                      <span className={`text-sm flex items-center gap-1 ${aiTestResult.ok ? 'text-green-600' : 'text-red-600'}`}>
                        {aiTestResult.ok ? <CheckCircle2 className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                        {aiTestResult.message}
                      </span>
                    )}
                  </div>

                  {providerGuide && (
                    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 p-5 rounded-lg text-sm">
                      <h3 className="font-bold text-blue-900 mb-3 flex items-center gap-2">
                        <Info className="w-4 h-4" />
                        {providerGuide.name} 配置指南
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-blue-800">
                        <div>
                          <span className="text-blue-600 text-xs uppercase tracking-wide">API 地址</span>
                          <p className="font-mono text-xs bg-white/60 px-2 py-1 rounded mt-0.5 break-all">{providerGuide.baseUrl}</p>
                        </div>
                        <div>
                          <span className="text-blue-600 text-xs uppercase tracking-wide">推荐模型</span>
                          <p className="font-mono text-xs bg-white/60 px-2 py-1 rounded mt-0.5">{providerGuide.model}</p>
                        </div>
                      </div>
                      <p className="mt-3 text-blue-700">{providerGuide.tip}</p>
                      <a
                        href={providerGuide.applyUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 mt-3 text-blue-600 hover:text-blue-800 font-medium underline text-xs"
                      >
                        前往申请 API Key <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>
                  )}
                </div>
              )}

              {currentSection.key === 'notifications' && (
                <div className="mt-8 space-y-4">
                  <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg flex items-start gap-3 text-blue-800 text-sm">
                    <Bell className="w-5 h-5 flex-shrink-0 mt-0.5 text-blue-600" />
                    <div>
                      <p className="font-medium mb-1">告警通知说明</p>
                      <p>配置后，以下事件将自动推送通知：Cookie 过期、Cookie 刷新、售后介入、发货失败、虚拟商品发码失败、人工接管等。</p>
                      <p className="mt-1">飞书：使用<strong>自定义机器人</strong>的 Webhook 地址。企业微信：使用<strong>群机器人</strong>的 Webhook 地址。</p>
                    </div>
                  </div>

                  <div className="flex gap-3">
                    {(config.notifications?.feishu_enabled) && (
                      <button
                        onClick={() => handleTestNotification('feishu')}
                        disabled={testingSend === 'feishu'}
                        className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg border border-blue-300 text-blue-700 bg-blue-50 hover:bg-blue-100 transition-colors disabled:opacity-50"
                      >
                        {testingSend === 'feishu' ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                        测试飞书通知
                      </button>
                    )}
                    {(config.notifications?.wechat_enabled) && (
                      <button
                        onClick={() => handleTestNotification('wechat')}
                        disabled={testingSend === 'wechat'}
                        className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg border border-green-300 text-green-700 bg-green-50 hover:bg-green-100 transition-colors disabled:opacity-50"
                      >
                        {testingSend === 'wechat' ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                        测试企业微信通知
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
