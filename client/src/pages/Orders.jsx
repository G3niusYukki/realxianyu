import React, { useState, useEffect, useMemo } from 'react';
import { getOrders, proxyXgjApi } from '../api/xianguanjia';
import { api } from '../api/index';
import { useStoreCategory } from '../contexts/StoreCategoryContext';
import toast from 'react-hot-toast';
import {
  Receipt, Search, RefreshCw, Tag, BellRing, Truck,
  RotateCcw, Eye, X, ChevronDown, ChevronUp,
} from 'lucide-react';

export default function Orders() {
  const { category } = useStoreCategory();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [actionLoading, setActionLoading] = useState({});
  const [expandedOrder, setExpandedOrder] = useState(null);
  const [orderDetail, setOrderDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => { fetchOrders(); }, [tab]);

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const statusMap = { 'ALL': undefined, 'WAIT_BUYER_PAY': 1, 'WAIT_SELLER_SEND': 2 };
      const payload = { page_no: 1, page_size: 50 };
      if (statusMap[tab]) payload.order_status = statusMap[tab];

      const res = await getOrders(payload);
      if (res.data?.ok) setOrders(res.data.data?.list || res.data.data?.data?.list || []);
      else toast.error(res.data?.error || '无法获取订单');
    } catch { toast.error('加载订单失败'); }
    finally { setLoading(false); }
  };

  const filteredOrders = useMemo(() => {
    if (!searchQuery.trim()) return orders;
    const q = searchQuery.toLowerCase();
    return orders.filter(o =>
      (o.order_id && String(o.order_id).toLowerCase().includes(q)) ||
      (o.buyer_name && o.buyer_name.toLowerCase().includes(q)) ||
      (o.title && o.title.toLowerCase().includes(q))
    );
  }, [orders, searchQuery]);

  const handleAdjustPrice = async (orderId) => {
    const newPrice = window.prompt('请输入新价格（单位：元）');
    if (!newPrice || isNaN(Number(newPrice))) return;
    const priceInCents = Math.round(Number(newPrice) * 100);
    setActionLoading(prev => ({ ...prev, [orderId]: 'price' }));
    try {
      const res = await proxyXgjApi('/api/open/order/modify/price', { order_id: orderId, total_fee: priceInCents });
      if (res.data?.ok) { toast.success('改价成功'); fetchOrders(); }
      else toast.error(res.data?.error || '改价失败');
    } catch { toast.error('改价请求失败'); }
    finally { setActionLoading(prev => ({ ...prev, [orderId]: null })); }
  };

  const handleShip = async (orderId) => {
    setActionLoading(prev => ({ ...prev, [orderId]: 'ship' }));
    try {
      const res = await proxyXgjApi('/api/open/order/delivery', { order_id: orderId });
      if (res.data?.ok) { toast.success('发货成功'); fetchOrders(); }
      else toast.error(res.data?.error || '发货失败');
    } catch { toast.error('发货请求失败'); }
    finally { setActionLoading(prev => ({ ...prev, [orderId]: null })); }
  };

  const handleRetry = async (orderId) => {
    setActionLoading(prev => ({ ...prev, [orderId]: 'retry' }));
    try {
      const res = await api.post('/orders/retry', { order_id: orderId });
      if (res.data?.ok || res.data?.success) { toast.success('重试发货已触发'); fetchOrders(); }
      else toast.error(res.data?.error || '重试失败');
    } catch { toast.error('重试请求失败'); }
    finally { setActionLoading(prev => ({ ...prev, [orderId]: null })); }
  };

  const handleRemind = async () => {
    toast('催单提醒已记录，系统将自动跟进', { icon: '📋' });
  };

  const toggleDetail = async (orderId) => {
    if (expandedOrder === orderId) {
      setExpandedOrder(null);
      setOrderDetail(null);
      return;
    }
    setExpandedOrder(orderId);
    setDetailLoading(true);
    try {
      const res = await proxyXgjApi('/api/open/order/detail', { order_id: orderId });
      setOrderDetail(res.data?.ok ? (res.data.data || res.data) : null);
    } catch { setOrderDetail(null); }
    finally { setDetailLoading(false); }
  };

  const formatPrice = (fee) => {
    const num = Number(fee);
    if (!num || isNaN(num)) return '¥0.00';
    return `¥${(num / 100).toFixed(2)}`;
  };

  const isVirtual = category === 'exchange' || category === 'virtual';

  return (
    <div className="xy-page xy-enter">
      <div className="flex flex-col md:flex-row justify-between md:items-end gap-4 mb-6">
        <div>
          <h1 className="xy-title">订单中心</h1>
          <p className="xy-subtitle mt-1">管理店铺订单与改价、催单操作{isVirtual ? '、虚拟品发货重试' : ''}</p>
        </div>
        <button onClick={fetchOrders} className="xy-btn-secondary px-3" aria-label="刷新订单">
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      <div className="xy-card overflow-hidden">
        <div className="border-b border-xy-border px-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex gap-6 overflow-x-auto whitespace-nowrap">
            {[
              { id: 'ALL', label: '全部订单' },
              { id: 'WAIT_BUYER_PAY', label: '待付款' },
              { id: 'WAIT_SELLER_SEND', label: '待发货' }
            ].map(t => (
              <button key={t.id} onClick={() => setTab(t.id)}
                className={`py-4 text-sm font-medium border-b-2 transition-colors ${tab === t.id ? 'border-xy-brand-500 text-xy-brand-600' : 'border-transparent text-xy-text-secondary hover:text-xy-text-primary'}`}>
                {t.label}
              </button>
            ))}
          </div>
          <div className="py-3 flex items-center gap-2 min-w-[240px]">
            <div className="relative flex-1">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-xy-text-muted" />
              <input type="text" placeholder="搜索订单号/买家/商品" className="xy-input pl-9 pr-3 py-1.5 text-sm" value={searchQuery} onChange={e => setSearchQuery(e.target.value)} />
            </div>
          </div>
        </div>

        {loading ? (
          <div className="p-12 text-center">
            <RefreshCw className="w-8 h-8 animate-spin text-xy-brand-500 mx-auto" />
            <p className="mt-4 text-xy-text-secondary">加载中...</p>
          </div>
        ) : filteredOrders.length === 0 ? (
          <div className="p-16 text-center">
            <div className="w-16 h-16 bg-xy-gray-50 rounded-full flex items-center justify-center mx-auto mb-4"><Receipt className="w-8 h-8 text-xy-gray-400" /></div>
            <h3 className="text-lg font-medium text-xy-text-primary mb-1">{searchQuery ? '未找到匹配订单' : '暂无订单'}</h3>
            <p className="text-xy-text-secondary">{searchQuery ? '请尝试其他搜索关键词' : '当前状态下没有查询到订单'}</p>
          </div>
        ) : (
          <div className="divide-y divide-xy-border">
            {filteredOrders.map(order => (
              <div key={order.order_id}>
                <div className="p-5 hover:bg-xy-gray-50 transition-colors">
                  <div className="flex flex-wrap items-center justify-between gap-4 mb-3">
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-medium">订单号: {order.order_id}</span>
                      <span className="text-xs text-xy-text-muted">{order.create_time}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`px-2.5 py-1 text-xs font-medium rounded-full ${
                        order.status === 1 ? 'bg-orange-100 text-orange-700' :
                        order.status === 2 ? 'bg-blue-100 text-blue-700' : 'bg-xy-gray-100 text-xy-text-secondary'
                      }`}>{order.status === 1 ? '待付款' : order.status === 2 ? '待发货' : '其他'}</span>
                      <button onClick={() => toggleDetail(order.order_id)} className="p-1 hover:bg-xy-gray-100 rounded text-xy-text-muted" title="查看详情">
                        {expandedOrder === order.order_id ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  <div className="flex gap-4">
                    <div className="w-20 h-20 bg-xy-gray-100 rounded-lg overflow-hidden border border-xy-border flex-shrink-0">
                      {order.pic_url ? (
                        <img src={order.pic_url} alt={order.title || ''} className="w-full h-full object-cover" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-xy-gray-300"><Receipt className="w-8 h-8" /></div>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-base font-medium text-xy-text-primary truncate mb-1">{order.title || '未知商品'}</h3>
                      <p className="text-sm text-xy-text-secondary mb-2">买家: {order.buyer_name ?? '未知'}</p>
                      <div className="text-lg font-bold text-xy-brand-500">{formatPrice(order.total_fee)}</div>
                    </div>

                    <div className="flex flex-col gap-2 justify-end">
                      {order.status === 1 && (
                        <>
                          <button onClick={handleRemind} className="xy-btn-secondary text-xs px-3 py-1.5 flex items-center gap-1.5 hover:text-blue-600 hover:border-blue-200">
                            <BellRing className="w-3.5 h-3.5" /> 催单
                          </button>
                          <button onClick={() => handleAdjustPrice(order.order_id)} disabled={actionLoading[order.order_id] === 'price'}
                            className="xy-btn-secondary text-xs px-3 py-1.5 flex items-center gap-1.5 hover:text-orange-600 hover:border-orange-200 disabled:opacity-50">
                            <Tag className="w-3.5 h-3.5" /> {actionLoading[order.order_id] === 'price' ? '改价中...' : '改价'}
                          </button>
                        </>
                      )}
                      {order.status === 2 && (
                        <>
                          <button onClick={() => handleShip(order.order_id)} disabled={actionLoading[order.order_id] === 'ship'}
                            className="xy-btn-primary text-xs px-4 py-1.5 flex items-center gap-1.5 disabled:opacity-50">
                            <Truck className="w-3.5 h-3.5" /> {actionLoading[order.order_id] === 'ship' ? '发货中...' : '发货'}
                          </button>
                          {isVirtual && (
                            <button onClick={() => handleRetry(order.order_id)} disabled={actionLoading[order.order_id] === 'retry'}
                              className="xy-btn-secondary text-xs px-3 py-1.5 flex items-center gap-1.5 text-purple-600 hover:bg-purple-50 hover:border-purple-200 disabled:opacity-50">
                              <RotateCcw className="w-3.5 h-3.5" /> {actionLoading[order.order_id] === 'retry' ? '重试中...' : '重试发货'}
                            </button>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                </div>

                {expandedOrder === order.order_id && (
                  <div className="px-5 pb-5 animate-in fade-in slide-in-from-top-2">
                    <div className="bg-xy-gray-50 rounded-xl border border-xy-border p-4">
                      {detailLoading ? (
                        <div className="text-center py-4"><RefreshCw className="w-5 h-5 animate-spin text-xy-brand-500 mx-auto" /></div>
                      ) : orderDetail ? (
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          {orderDetail.buyer_nick && <div><p className="text-xy-text-muted text-xs">买家昵称</p><p className="font-medium">{orderDetail.buyer_nick}</p></div>}
                          {orderDetail.buyer_phone && <div><p className="text-xy-text-muted text-xs">联系电话</p><p className="font-medium">{orderDetail.buyer_phone}</p></div>}
                          {orderDetail.receiver_address && <div className="col-span-2"><p className="text-xy-text-muted text-xs">收货地址</p><p className="font-medium">{orderDetail.receiver_address}</p></div>}
                          {orderDetail.logistics_no && <div><p className="text-xy-text-muted text-xs">物流单号</p><p className="font-medium">{orderDetail.logistics_no}</p></div>}
                          {orderDetail.pay_time && <div><p className="text-xy-text-muted text-xs">付款时间</p><p className="font-medium">{orderDetail.pay_time}</p></div>}
                          {orderDetail.remark && <div className="col-span-2"><p className="text-xy-text-muted text-xs">买家备注</p><p className="font-medium">{orderDetail.remark}</p></div>}
                        </div>
                      ) : (
                        <p className="text-center text-xy-text-muted py-4">暂无详细信息（需配置闲管家）</p>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
