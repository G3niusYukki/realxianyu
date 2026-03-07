import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { getProducts, unpublishProduct, publishProduct } from '../../api/xianguanjia';
import { api } from '../../api/index';
import { useStoreCategory } from '../../contexts/StoreCategoryContext';
import toast from 'react-hot-toast';
import {
  Package, Search, Plus, RefreshCw, PowerOff, Play, ExternalLink,
  MapPin, DollarSign, Upload, Download, Save, Trash2,
} from 'lucide-react';
import { Link } from 'react-router-dom';

const PRODUCT_TABS = [
  { key: 'list', label: '商品列表', visible: () => true },
  { key: 'routes', label: '路线数据', visible: (cat) => cat === 'express' },
  { key: 'markup', label: '加价规则', visible: (cat) => cat === 'express' },
];

export default function ProductList() {
  const { category } = useStoreCategory();
  const [activeTab, setActiveTab] = useState('list');
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');

  const [routeStats, setRouteStats] = useState(null);
  const [routeLoading, setRouteLoading] = useState(false);

  const [markupRules, setMarkupRules] = useState([]);
  const [markupLoading, setMarkupLoading] = useState(false);
  const [markupSaving, setMarkupSaving] = useState(false);

  const visibleTabs = useMemo(() => PRODUCT_TABS.filter(t => t.visible(category)), [category]);

  useEffect(() => { fetchProducts(); }, [page]);
  useEffect(() => {
    if (activeTab === 'routes') fetchRouteStats();
    if (activeTab === 'markup') fetchMarkupRules();
  }, [activeTab]);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const res = await getProducts(page, 20);
      if (res.data?.ok) setProducts(res.data.data?.list || []);
      else toast.error(res.data?.error || '无法获取商品列表');
    } catch { toast.error('加载失败'); }
    finally { setLoading(false); }
  };

  const fetchRouteStats = async () => {
    setRouteLoading(true);
    try {
      const res = await api.get('/route-stats');
      setRouteStats(res.data);
    } catch { toast.error('加载路线数据失败'); }
    finally { setRouteLoading(false); }
  };

  const fetchMarkupRules = async () => {
    setMarkupLoading(true);
    try {
      const res = await api.get('/get-markup-rules');
      setMarkupRules(res.data?.rules || []);
    } catch { toast.error('加载加价规则失败'); }
    finally { setMarkupLoading(false); }
  };

  const handleSaveMarkup = async () => {
    setMarkupSaving(true);
    try {
      const res = await api.post('/save-markup-rules', { rules: markupRules });
      if (res.data?.ok || res.data?.success) toast.success('加价规则已保存');
      else toast.error(res.data?.error || '保存失败');
    } catch (e) { toast.error(e.message || '保存失败'); }
    finally { setMarkupSaving(false); }
  };

  const handleImportRoutes = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const fd = new FormData();
    fd.append('file', file);
    try {
      const res = await api.post('/import-routes', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      if (res.data?.ok) { toast.success(`导入成功：${res.data.count || 0} 条路线`); fetchRouteStats(); }
      else toast.error(res.data?.error || '导入失败');
    } catch { toast.error('导入路线失败'); }
    e.target.value = '';
  };

  const handleImportMarkup = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const fd = new FormData();
    fd.append('file', file);
    try {
      const res = await api.post('/import-markup', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      if (res.data?.ok) { toast.success('加价规则导入成功'); fetchMarkupRules(); }
      else toast.error(res.data?.error || '导入失败');
    } catch { toast.error('导入加价规则失败'); }
    e.target.value = '';
  };

  const filteredProducts = useMemo(() => {
    if (!searchQuery.trim()) return products;
    const q = searchQuery.toLowerCase();
    return products.filter(p =>
      (p.title && p.title.toLowerCase().includes(q)) ||
      (p.product_id && String(p.product_id).toLowerCase().includes(q))
    );
  }, [products, searchQuery]);

  const toggleStatus = async (product) => {
    const isOnline = product.status === 1 || product.status === '1' || product.status === 'on_sale';
    const actionStr = isOnline ? '下架' : '重新上架';
    try {
      toast.loading(`正在${actionStr}...`, { id: 'status_toggle' });
      const res = isOnline ? await unpublishProduct(product.product_id) : await publishProduct(product.product_id);
      if (res.data?.ok) { toast.success(`${actionStr}成功`, { id: 'status_toggle' }); fetchProducts(); }
      else toast.error(res.data?.error || `${actionStr}失败`, { id: 'status_toggle' });
    } catch { toast.error(`${actionStr}出错`, { id: 'status_toggle' }); }
  };

  const formatPrice = (price) => {
    const num = Number(price);
    if (!num || isNaN(num)) return '¥0.00';
    return `¥${(num / 100).toFixed(2)}`;
  };

  const updateMarkupRule = (idx, field, value) => {
    setMarkupRules(prev => prev.map((r, i) => i === idx ? { ...r, [field]: value } : r));
  };

  const removeMarkupRule = (idx) => {
    setMarkupRules(prev => prev.filter((_, i) => i !== idx));
  };

  const addMarkupRule = () => {
    setMarkupRules(prev => [...prev, { min_weight: '', max_weight: '', markup: '', name: '' }]);
  };

  return (
    <div className="xy-page xy-enter">
      <div className="flex flex-col md:flex-row justify-between md:items-end gap-4 mb-6">
        <div>
          <h1 className="xy-title">商品管理</h1>
          <p className="xy-subtitle mt-1">管理闲鱼在售商品，或使用 AI 辅助发布新商品</p>
        </div>
        <div className="flex gap-3">
          <button onClick={() => { if (activeTab === 'list') fetchProducts(); else if (activeTab === 'routes') fetchRouteStats(); else fetchMarkupRules(); }} className="xy-btn-secondary px-3" aria-label="刷新">
            <RefreshCw className="w-4 h-4" />
          </button>
          <Link to="/products/auto-publish" className="xy-btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" /> 自动上架
          </Link>
        </div>
      </div>

      {visibleTabs.length > 1 && (
        <div className="flex bg-xy-gray-100 p-1 rounded-xl mb-6 w-fit">
          {visibleTabs.map(t => (
            <button key={t.key} onClick={() => setActiveTab(t.key)}
              className={`px-5 py-2 text-sm font-medium rounded-lg transition-colors ${activeTab === t.key ? 'bg-white shadow-sm text-xy-text-primary' : 'text-xy-text-secondary hover:text-xy-text-primary'}`}>
              {t.label}
            </button>
          ))}
        </div>
      )}

      {activeTab === 'list' && (
        <div className="xy-card overflow-hidden">
          <div className="border-b border-xy-border px-4 py-3 bg-xy-gray-50 flex items-center gap-2">
            <div className="relative flex-1 max-w-sm">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-xy-text-muted" />
              <input type="text" placeholder="搜索商品标题或 ID" className="xy-input pl-9 pr-3 py-1.5 text-sm" value={searchQuery} onChange={e => setSearchQuery(e.target.value)} />
            </div>
          </div>

          {loading ? (
            <div className="p-12 text-center">
              <RefreshCw className="w-8 h-8 animate-spin text-xy-brand-500 mx-auto" />
              <p className="mt-4 text-xy-text-secondary">正在同步数据...</p>
            </div>
          ) : filteredProducts.length === 0 ? (
            <div className="p-16 text-center">
              <div className="w-16 h-16 bg-xy-gray-50 rounded-full flex items-center justify-center mx-auto mb-4"><Package className="w-8 h-8 text-xy-gray-400" /></div>
              <h3 className="text-lg font-medium text-xy-text-primary mb-1">{searchQuery ? '未找到匹配商品' : '还没有商品'}</h3>
              <p className="text-xy-text-secondary mb-6">{searchQuery ? '请尝试其他搜索关键词' : '点击右上角按钮开始 AI 智能上架'}</p>
              {!searchQuery && <Link to="/products/auto-publish" className="xy-btn-primary">去发布商品</Link>}
            </div>
          ) : (
            <div className="divide-y divide-xy-border">
              {filteredProducts.map(p => {
                const isOnline = p.status === 1 || p.status === '1' || p.status === 'on_sale';
                return (
                  <div key={p.product_id} className="p-5 hover:bg-xy-gray-50 transition-colors flex flex-col md:flex-row gap-5">
                    <div className="w-24 h-24 bg-xy-gray-100 rounded-lg overflow-hidden border border-xy-border flex-shrink-0 relative">
                      <img src={p.pic_url || (Array.isArray(p.images) && p.images[0]) || ''} alt={p.title || ''} className="w-full h-full object-cover" />
                      {!isOnline && <div className="absolute inset-0 bg-black/40 flex items-center justify-center"><span className="text-white text-xs font-bold px-2 py-1 bg-black/50 rounded">已下架</span></div>}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <h3 className="text-base font-medium text-xy-text-primary mb-2 line-clamp-2 leading-snug">{p.title}</h3>
                          <div className="flex flex-wrap items-center gap-4 text-sm text-xy-text-secondary mb-2">
                            <span className="text-lg font-bold text-xy-brand-500">{formatPrice(p.price)}</span>
                            <span className="bg-xy-gray-100 px-2 py-0.5 rounded text-xs">库存: {p.stock ?? 1}</span>
                            {p.view_count != null && <span>浏览 {p.view_count}</span>}
                            {p.want_count != null && <span>想要 {p.want_count}</span>}
                          </div>
                          <p className="text-xs text-xy-text-muted">ID: {p.product_id}</p>
                        </div>
                        <div className="flex flex-col items-end gap-2 flex-shrink-0">
                          {isOnline ? (
                            <button onClick={() => toggleStatus(p)} className="xy-btn-secondary text-xs px-3 py-1.5 flex items-center gap-1.5 text-red-600 hover:bg-red-50 hover:border-red-200">
                              <PowerOff className="w-3.5 h-3.5" /> 下架
                            </button>
                          ) : (
                            <button onClick={() => toggleStatus(p)} className="xy-btn-secondary text-xs px-3 py-1.5 flex items-center gap-1.5 text-green-600 hover:bg-green-50 hover:border-green-200">
                              <Play className="w-3.5 h-3.5" /> 上架
                            </button>
                          )}
                          <a href={`https://h5.m.goofish.com/app/idleFish-F2e/fish-mini-item/pages/detail?id=${p.product_id}`} target="_blank" rel="noreferrer" className="text-xs text-blue-500 hover:text-blue-600 flex items-center gap-1 mt-1">
                            查看闲鱼详情 <ExternalLink className="w-3 h-3" />
                          </a>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {activeTab === 'routes' && (
        <div className="space-y-6 animate-in fade-in slide-in-from-right-4">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-bold text-xy-text-primary flex items-center gap-2"><MapPin className="w-5 h-5 text-green-500" /> 快递路线数据</h2>
            <div className="flex gap-2">
              <label className="xy-btn-secondary text-sm px-3 py-1.5 flex items-center gap-1.5 cursor-pointer">
                <Upload className="w-4 h-4" /> 导入路线
                <input type="file" accept=".csv,.xlsx,.zip" className="hidden" onChange={handleImportRoutes} />
              </label>
              <a href="/api/export-routes" download className="xy-btn-secondary text-sm px-3 py-1.5 flex items-center gap-1.5">
                <Download className="w-4 h-4" /> 导出路线
              </a>
            </div>
          </div>

          {routeLoading ? (
            <div className="xy-card p-12 text-center"><RefreshCw className="w-6 h-6 animate-spin text-xy-brand-500 mx-auto" /></div>
          ) : routeStats ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: '总路线数', value: routeStats.total_routes ?? routeStats.count ?? 0 },
                { label: '快递公司', value: routeStats.companies ?? routeStats.carriers ?? 0 },
                { label: '始发城市', value: routeStats.origins ?? 0 },
                { label: '目的城市', value: routeStats.destinations ?? 0 },
              ].map(s => (
                <div key={s.label} className="xy-card p-5 text-center">
                  <p className="text-2xl font-bold text-xy-text-primary">{s.value}</p>
                  <p className="text-sm text-xy-text-secondary mt-1">{s.label}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="xy-card p-12 text-center text-xy-text-muted">
              <MapPin className="w-12 h-12 mx-auto mb-3 text-xy-gray-300" />
              <p>暂无路线数据，请先导入路线文件</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'markup' && (
        <div className="space-y-6 animate-in fade-in slide-in-from-right-4">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-bold text-xy-text-primary flex items-center gap-2"><DollarSign className="w-5 h-5 text-amber-500" /> 加价规则</h2>
            <div className="flex gap-2">
              <label className="xy-btn-secondary text-sm px-3 py-1.5 flex items-center gap-1.5 cursor-pointer">
                <Upload className="w-4 h-4" /> 导入
                <input type="file" accept=".csv,.xlsx,.json" className="hidden" onChange={handleImportMarkup} />
              </label>
              <button onClick={addMarkupRule} className="xy-btn-secondary text-sm px-3 py-1.5 flex items-center gap-1.5">
                <Plus className="w-4 h-4" /> 添加规则
              </button>
              <button onClick={handleSaveMarkup} disabled={markupSaving} className="xy-btn-primary text-sm px-4 py-1.5 flex items-center gap-1.5">
                {markupSaving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                保存
              </button>
            </div>
          </div>

          {markupLoading ? (
            <div className="xy-card p-12 text-center"><RefreshCw className="w-6 h-6 animate-spin text-xy-brand-500 mx-auto" /></div>
          ) : markupRules.length === 0 ? (
            <div className="xy-card p-12 text-center text-xy-text-muted">
              <DollarSign className="w-12 h-12 mx-auto mb-3 text-xy-gray-300" />
              <p>暂无加价规则，请添加或导入</p>
            </div>
          ) : (
            <div className="xy-card overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-xy-gray-50 border-b border-xy-border">
                    <th className="text-left px-4 py-3 font-medium text-xy-text-secondary">规则名称</th>
                    <th className="text-left px-4 py-3 font-medium text-xy-text-secondary">最小重量(kg)</th>
                    <th className="text-left px-4 py-3 font-medium text-xy-text-secondary">最大重量(kg)</th>
                    <th className="text-left px-4 py-3 font-medium text-xy-text-secondary">加价(元)</th>
                    <th className="text-right px-4 py-3 font-medium text-xy-text-secondary">操作</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-xy-border">
                  {markupRules.map((rule, idx) => (
                    <tr key={idx} className="hover:bg-xy-gray-50 transition-colors">
                      <td className="px-4 py-2"><input className="xy-input px-2 py-1 text-sm w-full" value={rule.name || ''} onChange={e => updateMarkupRule(idx, 'name', e.target.value)} placeholder="规则名" /></td>
                      <td className="px-4 py-2"><input type="number" className="xy-input px-2 py-1 text-sm w-20" value={rule.min_weight ?? ''} onChange={e => updateMarkupRule(idx, 'min_weight', e.target.value)} /></td>
                      <td className="px-4 py-2"><input type="number" className="xy-input px-2 py-1 text-sm w-20" value={rule.max_weight ?? ''} onChange={e => updateMarkupRule(idx, 'max_weight', e.target.value)} /></td>
                      <td className="px-4 py-2"><input type="number" className="xy-input px-2 py-1 text-sm w-20" value={rule.markup ?? ''} onChange={e => updateMarkupRule(idx, 'markup', e.target.value)} /></td>
                      <td className="px-4 py-2 text-right">
                        <button onClick={() => removeMarkupRule(idx)} className="p-1 text-red-500 hover:bg-red-50 rounded"><Trash2 className="w-4 h-4" /></button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
