import React, { useState, useCallback } from 'react'
import { Zap } from 'lucide-react'
import toast from 'react-hot-toast'
import { api } from '../../api/index'

const XgjControlPanel = React.memo(function XgjControlPanel() {
  const [appKey, setAppKey] = useState('');
  const [appSecret, setAppSecret] = useState('');
  const [autoPrice, setAutoPrice] = useState(false);
  const [autoShip, setAutoShip] = useState(false);
  const [connected, setConnected] = useState<boolean | null>(null);
  const [testLoading, setTestLoading] = useState(false);
  const [saveLoading, setSaveLoading] = useState(false);
  const [retryPriceCount, setRetryPriceCount] = useState(0);
  const [retryShipCount, setRetryShipCount] = useState(0);

  const handleTest = useCallback(async () => {
    if (!appKey || !appSecret) { toast.error('请先填写 AppKey 和 AppSecret'); return; }
    setTestLoading(true);
    try {
      const res = await api.post('/xgj/test-connection', {
        app_key: appKey, app_secret: appSecret, mode: 'xianguanjia',
      });
      const ok = res.data?.ok ?? false;
      setConnected(ok);
      toast[ok ? 'success' : 'error'](res.data?.message || (ok ? '连接成功' : '连接失败'));
    } catch {
      setConnected(false);
      toast.error('连接测试失败');
    } finally {
      setTestLoading(false);
    }
  }, [appKey, appSecret]);

  const handleSave = useCallback(async () => {
    setSaveLoading(true);
    try {
      const res = await api.post('/xgj/settings', {
        app_key: appKey,
        app_secret: appSecret,
        auto_price_enabled: autoPrice,
        auto_ship_enabled: autoShip,
      });
      if (res.data?.success ?? res.data?.ok) {
        toast.success('闲管家配置已保存');
      } else {
        toast.error(res.data?.message || '保存失败');
      }
    } catch {
      toast.error('保存配置失败');
    } finally {
      setSaveLoading(false);
    }
  }, [appKey, appSecret, autoPrice, autoShip]);

  const handleRetryPrice = useCallback(async () => {
    try {
      const res = await api.post('/xgj/retry-price', {});
      toast.success(res.data?.message || '改价重试已触发');
    } catch { toast.error('改价重试失败'); }
  }, []);

  const handleRetryShip = useCallback(async () => {
    try {
      const res = await api.post('/xgj/retry-ship', {});
      toast.success(res.data?.message || '发货重试已触发');
    } catch { toast.error('发货重试失败'); }
  }, []);

  const connColor = connected === true ? 'bg-green-500' : connected === false ? 'bg-red-500' : 'bg-gray-300';
  const connLabel = connected === true ? '已连接' : connected === false ? '连接失败' : '未配置';

  return (
    <div className="xy-card p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-xy-text-primary flex items-center gap-2">
          <Zap className="w-4 h-4 text-blue-500" /> 闲管家控制面板
        </h3>
        <span className={`flex items-center gap-1.5 text-xs font-medium text-xy-text-secondary`}>
          <span className={`w-2 h-2 rounded-full ${connColor}`} />
          {connLabel}
        </span>
      </div>

      <div className="space-y-3">
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="text-xs text-xy-text-secondary mb-1 block">AppKey</label>
            <input
              className="xy-input w-full text-xs py-1.5"
              value={appKey}
              onChange={e => setAppKey(e.target.value)}
              placeholder="填写 AppKey"
            />
          </div>
          <div>
            <label className="text-xs text-xy-text-secondary mb-1 block">AppSecret</label>
            <input
              className="xy-input w-full text-xs py-1.5"
              type="password"
              value={appSecret}
              onChange={e => setAppSecret(e.target.value)}
              placeholder="填写 AppSecret"
            />
          </div>
        </div>

        <div className="flex gap-4">
          <label className="flex items-center gap-2 text-xs text-xy-text-secondary cursor-pointer">
            <input
              type="checkbox"
              className="accent-orange-500"
              checked={autoPrice}
              onChange={e => setAutoPrice(e.target.checked)}
            />
            自动改价
          </label>
          <label className="flex items-center gap-2 text-xs text-xy-text-secondary cursor-pointer">
            <input
              type="checkbox"
              className="accent-orange-500"
              checked={autoShip}
              onChange={e => setAutoShip(e.target.checked)}
            />
            支付后自动发货
          </label>
        </div>

        <div className="flex gap-2">
          <button
            onClick={handleTest}
            disabled={testLoading}
            className="flex-1 px-3 py-1.5 text-xs border border-xy-border rounded-lg hover:bg-xy-gray-50 disabled:opacity-50 transition-colors font-medium"
          >
            {testLoading ? '测试中...' : '测试连接'}
          </button>
          <button
            onClick={handleSave}
            disabled={saveLoading}
            className="flex-1 px-3 py-1.5 text-xs bg-orange-500 text-white rounded-lg hover:bg-orange-600 disabled:opacity-50 transition-colors font-medium"
          >
            {saveLoading ? '保存中...' : '保存配置'}
          </button>
        </div>

        {(retryPriceCount > 0 || retryShipCount > 0) && (
          <div className="flex gap-2 pt-1">
            {retryPriceCount > 0 && (
              <button onClick={handleRetryPrice} className="text-xs px-2 py-1 rounded border border-orange-200 text-orange-600 hover:bg-orange-50 transition-colors">
                重试改价 ({retryPriceCount})
              </button>
            )}
            {retryShipCount > 0 && (
              <button onClick={handleRetryShip} className="text-xs px-2 py-1 rounded border border-orange-200 text-orange-600 hover:bg-orange-50 transition-colors">
                重试发货 ({retryShipCount})
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
});

export default XgjControlPanel;
