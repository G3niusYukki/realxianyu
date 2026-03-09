import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../../api/index';
import {
  getBrandAssets, getBrandAssetsGrouped, uploadBrandAsset, deleteBrandAsset,
  getFrames, previewFrame,
  getPublishQueue, generateDailyQueue, updateQueueItem, deleteQueueItem,
  regenerateQueueImages, publishQueueItem, publishQueueBatch,
  getCompositionLayers, previewComposition,
  type BrandAsset, type QueueItem, type FrameMeta, type LayerOption,
} from '../../api/listing';
import { useStoreCategory, CATEGORY_META } from '../../contexts/StoreCategoryContext';
import toast from 'react-hot-toast';
import {
  Calendar, RefreshCw, Upload, Trash2, Image as ImageIcon,
  ChevronDown, ChevronUp, Edit3, Play, Layers, Clock,
  CheckCircle2, XCircle, AlertTriangle, Package, Eye, Send,
} from 'lucide-react';

// ─── Scheduler Panel ─────────────────────────────
function SchedulerPanel() {
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/auto-publish/status')
      .then(res => { if (res.data?.ok) setStatus(res.data); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="xy-card p-6 mb-4"><div className="h-16 bg-xy-gray-100 rounded-xl animate-pulse" /></div>;
  if (!status) return null;

  const { schedule, state, today_plan } = status;
  const actionLabels: Record<string, string> = {
    cold_start: '冷启动 — 新建链接',
    steady_replace: '稳定运营 — 替换最差链接',
    skip: '今日已执行',
  };

  return (
    <div className="xy-card p-5 mb-4 animate-in fade-in slide-in-from-top-2">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-bold text-xy-text-primary flex items-center gap-2">
          <Calendar className="w-4 h-4 text-emerald-500" /> 自动上架调度
        </h2>
        <span className="text-[11px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-medium">全品类统一策略</span>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        <div className="bg-xy-gray-50 rounded-lg p-2.5 text-center border border-xy-border">
          <p className="text-[11px] text-xy-text-muted">运营天数</p>
          <p className="text-lg font-bold text-xy-text-primary">{state.total_days_active}</p>
        </div>
        <div className="bg-xy-gray-50 rounded-lg p-2.5 text-center border border-xy-border">
          <p className="text-[11px] text-xy-text-muted">活跃链接</p>
          <p className="text-lg font-bold text-emerald-600">{state.active_listings}/{schedule.max_active_listings}</p>
        </div>
        <div className="bg-xy-gray-50 rounded-lg p-2.5 text-center border border-xy-border">
          <p className="text-[11px] text-xy-text-muted">今日计划</p>
          <p className="text-xs font-medium text-xy-brand-600 mt-0.5">{actionLabels[today_plan?.action] || '无'}</p>
        </div>
        <div className="bg-xy-gray-50 rounded-lg p-2.5 text-center border border-xy-border">
          <p className="text-[11px] text-xy-text-muted">上次执行</p>
          <p className="text-xs font-medium text-xy-text-primary mt-0.5">{state.last_run_date || '从未'}</p>
        </div>
      </div>
    </div>
  );
}

// ─── Brand Assets Tab ─────────────────────────────
function BrandAssetsTab({ category }: { category: string }) {
  const [brands, setBrands] = useState<Record<string, BrandAsset[]>>({});
  const [allAssets, setAllAssets] = useState<BrandAsset[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [newName, setNewName] = useState('');
  const fileRef = useRef<HTMLInputElement>(null);
  const [frames, setFrames] = useState<FrameMeta[]>([]);

  const fetchData = useCallback(async () => {
    try {
      const [groupedRes, assetsRes, framesRes] = await Promise.all([
        getBrandAssetsGrouped(category),
        getBrandAssets(category),
        getFrames(),
      ]);
      if (groupedRes.data?.ok) setBrands(groupedRes.data.brands || {});
      if (assetsRes.data?.ok) setAllAssets(assetsRes.data.assets || []);
      if (framesRes.data?.ok) setFrames(framesRes.data.frames || []);
    } catch {}
    setLoading(false);
  }, [category]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleUpload = async () => {
    const file = fileRef.current?.files?.[0];
    if (!file) { toast.error('请选择图片文件'); return; }
    if (!newName.trim()) { toast.error('请输入品牌名称'); return; }
    setUploading(true);
    try {
      const res = await uploadBrandAsset(file, newName.trim(), category);
      if (res.data?.ok) {
        toast.success(`已上传「${newName.trim()}」`);
        setNewName('');
        if (fileRef.current) fileRef.current.value = '';
        fetchData();
      }
    } catch (err: any) {
      toast.error('上传失败: ' + (err?.response?.data?.error || err.message));
    }
    setUploading(false);
  };

  const handleDelete = async (id: string, name: string) => {
    try {
      const res = await deleteBrandAsset(id);
      if (res.data?.ok) {
        toast.success(`已删除「${name}」`);
        fetchData();
      }
    } catch { toast.error('删除失败'); }
  };

  const brandNames = Object.keys(brands);
  const meta = CATEGORY_META[category];

  return (
    <div className="space-y-6 animate-in fade-in">
      {/* Upload */}
      <div className="xy-card p-5">
        <h3 className="text-sm font-bold text-xy-text-primary mb-3 flex items-center gap-2">
          <Upload className="w-4 h-4 text-violet-500" /> 上传品牌图片
        </h3>
        <p className="text-xs text-xy-text-secondary mb-3">
          上传 {meta?.icon} {meta?.label || category} 品类的品牌 Logo 图片，同一品牌可上传多张不同样式
        </p>
        <div className="flex items-end gap-3">
          <div className="flex-1 max-w-xs">
            <label className="xy-label text-xs">品牌名称</label>
            <input type="text" className="xy-input px-3 py-2 text-sm" placeholder="如：顺丰、中通" value={newName} onChange={e => setNewName(e.target.value)} list="brand-names" />
            <datalist id="brand-names">
              {brandNames.map(n => <option key={n} value={n} />)}
            </datalist>
          </div>
          <div className="flex-1 max-w-xs">
            <label className="xy-label text-xs">Logo 图片</label>
            <input ref={fileRef} type="file" accept="image/png,image/jpeg,image/webp,image/svg+xml" className="xy-input px-3 py-1.5 text-sm file:mr-3 file:py-1 file:px-3 file:rounded-lg file:border-0 file:bg-violet-50 file:text-violet-600 file:font-medium file:text-xs" />
          </div>
          <button onClick={handleUpload} disabled={uploading} className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-violet-50 border border-violet-300 text-violet-700 hover:bg-violet-100 transition-colors disabled:opacity-50">
            {uploading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />} 上传
          </button>
        </div>
      </div>

      {/* Grouped Brand Display */}
      <div className="xy-card p-5">
        <h3 className="text-sm font-bold text-xy-text-primary mb-3 flex items-center gap-2">
          <ImageIcon className="w-4 h-4 text-violet-500" /> 品牌素材库
          <span className="text-[11px] font-normal text-xy-text-muted">({allAssets.length} 张)</span>
        </h3>
        {loading ? (
          <div className="grid grid-cols-3 gap-3">{[1,2,3].map(i => <div key={i} className="h-24 bg-xy-gray-100 rounded-xl animate-pulse" />)}</div>
        ) : brandNames.length === 0 ? (
          <div className="text-center py-8 text-xy-text-muted text-sm border-2 border-dashed border-xy-border rounded-xl">
            暂无品牌素材，请上传 {meta?.label || ''} 品类的品牌 Logo
          </div>
        ) : (
          <div className="space-y-4">
            {brandNames.map(brandName => (
              <div key={brandName} className="border border-xy-border rounded-xl p-3">
                <h4 className="text-sm font-medium text-xy-text-primary mb-2">{brandName} <span className="text-[11px] text-xy-text-muted">({brands[brandName].length} 张)</span></h4>
                <div className="flex flex-wrap gap-3">
                  {brands[brandName].map(asset => (
                    <div key={asset.id} className="group relative w-20 h-20 rounded-xl overflow-hidden border border-xy-border bg-white">
                      <img src={`/api/brand-assets/file/${asset.filename}`} alt={asset.name} className="w-full h-full object-contain p-1" onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                      <button onClick={() => handleDelete(asset.id, asset.name)} className="absolute top-0.5 right-0.5 p-0.5 bg-white/80 rounded opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-50">
                        <Trash2 className="w-3 h-3 text-red-500" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Template Preview */}
      <div className="xy-card p-5">
        <h3 className="text-sm font-bold text-xy-text-primary mb-3 flex items-center gap-2">
          <Layers className="w-4 h-4 text-blue-500" /> 可用模板
          <span className="text-[11px] font-normal text-xy-text-muted">({frames.length} 套)</span>
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
          {frames.map(f => (
            <div key={f.id} className="border border-xy-border rounded-xl p-2 text-center hover:border-xy-brand-400 transition-colors">
              <div className="w-full aspect-square bg-xy-gray-50 rounded-lg mb-1.5 flex items-center justify-center overflow-hidden">
                <FrameThumb frameId={f.id} category={category} brandAssetIds={allAssets.map(a => a.id)} />
              </div>
              <p className="text-xs font-medium text-xy-text-primary truncate">{f.name}</p>
              <p className="text-[10px] text-xy-text-muted truncate">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function FrameThumb({ frameId, category, brandAssetIds }: { frameId: string; category: string; brandAssetIds: string[] }) {
  const [url, setUrl] = useState<string>('');
  useEffect(() => {
    const params = new URLSearchParams({ frame_id: frameId, category });
    if (brandAssetIds.length > 0) params.set('brand_asset_ids', brandAssetIds.join(','));
    api.get(`/listing/preview-frame?${params}`)
      .then(res => { if (res.data?.ok) setUrl(res.data.image_url); })
      .catch(() => {});
  }, [frameId, category, brandAssetIds]);

  if (!url) return <div className="w-full h-full animate-pulse bg-xy-gray-100 rounded-lg" />;
  return <img src={url} alt={frameId} className="w-full h-full object-cover rounded-lg" />;
}

// ─── Queue Tab ──────────────────────────────────
const STATUS_LABELS: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
  draft: { label: '草稿', color: 'bg-gray-100 text-gray-600', icon: <Edit3 className="w-3 h-3" /> },
  ready: { label: '就绪', color: 'bg-blue-100 text-blue-700', icon: <CheckCircle2 className="w-3 h-3" /> },
  publishing: { label: '发布中', color: 'bg-amber-100 text-amber-700', icon: <RefreshCw className="w-3 h-3 animate-spin" /> },
  published: { label: '已发布', color: 'bg-green-100 text-green-700', icon: <CheckCircle2 className="w-3 h-3" /> },
  failed: { label: '失败', color: 'bg-red-100 text-red-700', icon: <XCircle className="w-3 h-3" /> },
};

function QueueTab({ category }: { category: string }) {
  const [items, setItems] = useState<QueueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [batchInterval, setBatchInterval] = useState(30);
  const [publishing, setPublishing] = useState(false);

  const today = new Date().toLocaleDateString('en-CA');

  const fetchQueue = useCallback(async () => {
    try {
      const res = await getPublishQueue(today);
      if (res.data?.ok) setItems(res.data.items || []);
    } catch {}
    setLoading(false);
  }, [today]);

  useEffect(() => {
    fetchQueue();
  }, [fetchQueue]);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const res = await generateDailyQueue(category);
      if (res.data?.ok) {
        setItems(res.data.items || []);
        toast.success(`已生成 ${res.data.items?.length || 0} 条待发布内容`);
      }
    } catch (err: any) {
      toast.error('生成失败: ' + (err?.response?.data?.error || err.message));
    }
    setGenerating(false);
  };

  const handlePublishOne = async (id: string) => {
    try {
      const res = await publishQueueItem(id);
      if (res.data?.ok) {
        toast.success('发布成功');
      } else {
        toast.error('发布失败: ' + (res.data?.error || '未知错误'));
      }
      fetchQueue();
    } catch (err: any) {
      const serverError = err?.response?.data?.error || err?.message || '未知错误';
      toast.error('发布失败: ' + serverError);
      fetchQueue();
    }
  };

  const handlePublishBatch = async () => {
    const readyItems = items.filter(it => it.status === 'draft' || it.status === 'ready');
    if (readyItems.length === 0) { toast.error('没有可发布的内容'); return; }
    setPublishing(true);
    try {
      const result = await publishQueueBatch(
        readyItems.map(it => it.id),
        batchInterval,
        (done, total) => toast(`发布进度：${done}/${total}`, { id: 'batch-progress' }),
      );
      if (result.failures.length === 0) {
        toast.success(`全部 ${result.successes.length} 条发布成功`);
      } else {
        const firstError = result.failures[0]?.error || '未知错误';
        toast.error(`${result.successes.length} 成功，${result.failures.length} 失败: ${firstError}`);
      }
      fetchQueue();
    } catch (err: any) {
      const serverError = err?.response?.data?.error || err?.message || '未知错误';
      toast.error('批量发布失败: ' + serverError);
    }
    setPublishing(false);
  };

  const handleDeleteItem = async (id: string) => {
    try {
      await deleteQueueItem(id);
      toast.success('已删除');
      fetchQueue();
    } catch { toast.error('删除失败'); }
  };

  const handleRegenerate = async (id: string) => {
    try {
      const res = await regenerateQueueImages(id);
      if (res.data?.ok) {
        toast.success('图片已重新生成');
        fetchQueue();
      }
    } catch { toast.error('重新生成失败'); }
  };

  const pendingCount = items.filter(it => it.status === 'draft' || it.status === 'ready').length;

  return (
    <div className="space-y-4 animate-in fade-in">
      {/* Generate or empty state */}
      {loading ? (
        <div className="xy-card p-6"><div className="h-32 bg-xy-gray-100 rounded-xl animate-pulse" /></div>
      ) : items.length === 0 ? (
        <div className="xy-card p-8 text-center">
          <Package className="w-12 h-12 text-xy-text-muted mx-auto mb-3 opacity-50" />
          <p className="text-xy-text-secondary mb-4">今日暂无待发布内容</p>
          <button onClick={handleGenerate} disabled={generating} className="xy-btn-primary px-6 py-2.5 text-sm">
            {generating ? <><RefreshCw className="w-4 h-4 animate-spin mr-2" /> 生成中...</> : '生成今日发布任务'}
          </button>
        </div>
      ) : (
        <>
          <div className="flex items-center justify-between">
            <p className="text-sm text-xy-text-secondary">
              今日 {items.length} 条，{pendingCount} 条待发布
            </p>
            <button onClick={fetchQueue} className="text-xs text-xy-brand-600 hover:underline flex items-center gap-1">
              <RefreshCw className="w-3 h-3" /> 刷新
            </button>
          </div>

          {/* Queue Items */}
          <div className="space-y-3">
            {items.map(item => {
              const st = STATUS_LABELS[item.status] || STATUS_LABELS.draft;
              const isExpanded = expandedId === item.id;
              return (
                <div key={item.id} className="xy-card overflow-hidden">
                  <div className="p-4 flex items-start gap-4">
                    {/* Thumbnail */}
                    <div className="w-20 h-20 flex-shrink-0 rounded-lg overflow-hidden bg-xy-gray-50 border border-xy-border">
                      {item.generated_images?.[0] ? (
                        <img src={`/api/generated-image?path=${encodeURIComponent(item.generated_images[0])}`} alt="" className="w-full h-full object-cover" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-xy-text-muted">
                          <ImageIcon className="w-6 h-6 opacity-30" />
                        </div>
                      )}
                    </div>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium ${st.color}`}>
                          {st.icon} {st.label}
                        </span>
                        {item.action === 'steady_replace' && (
                          <span className="px-1.5 py-0.5 rounded bg-amber-50 text-amber-600 text-[10px]">替换</span>
                        )}
                      </div>
                      <p className="text-sm font-medium text-xy-text-primary truncate">{item.title || '未命名'}</p>
                      <p className="text-[11px] text-xy-text-muted mt-0.5">
                        {item.composition && Object.keys(item.composition).length > 0
                          ? `组合: ${Object.values(item.composition).join('·')}`
                          : `模板: ${item.frame_id}`
                        } · {item.brand_asset_ids?.length || 0} 张品牌图
                        {item.scheduled_time && <span className="ml-2 text-indigo-500 font-medium">⏰ {item.scheduled_time}</span>}
                      </p>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-1.5 flex-shrink-0">
                      <button onClick={() => setExpandedId(isExpanded ? null : item.id)} className="p-1.5 rounded-lg hover:bg-xy-gray-50 text-xy-text-muted" title="编辑">
                        {isExpanded ? <ChevronUp className="w-4 h-4" /> : <Edit3 className="w-4 h-4" />}
                      </button>
                      <button onClick={() => handleRegenerate(item.id)} className="p-1.5 rounded-lg hover:bg-xy-gray-50 text-xy-text-muted" title="重新生图">
                        <RefreshCw className="w-4 h-4" />
                      </button>
                      {(item.status === 'draft' || item.status === 'ready') && (
                        <button onClick={() => handlePublishOne(item.id)} className="p-1.5 rounded-lg hover:bg-emerald-50 text-emerald-600" title="发布">
                          <Send className="w-4 h-4" />
                        </button>
                      )}
                      <button onClick={() => handleDeleteItem(item.id)} className="p-1.5 rounded-lg hover:bg-red-50 text-red-400" title="删除">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  {/* Expanded Editor */}
                  {isExpanded && (
                    <QueueItemEditor item={item} onSave={fetchQueue} category={category} />
                  )}

                  {item.error && (
                    <div className="px-4 pb-3">
                      <p className="text-xs text-red-500 flex items-center gap-1">
                        <AlertTriangle className="w-3 h-3" /> {item.error}
                      </p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Batch Publish */}
          {pendingCount > 0 && (
            <div className="xy-card p-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-sm text-xy-text-primary font-medium">一键发布全部 ({pendingCount} 条)</span>
                <div className="flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5 text-xy-text-muted" />
                  <input type="number" min={5} max={300} className="xy-input px-2 py-1 w-16 text-sm text-center" value={batchInterval} onChange={e => setBatchInterval(Math.max(5, Number(e.target.value)))} />
                  <span className="text-[11px] text-xy-text-muted">秒间隔</span>
                </div>
              </div>
              <button onClick={handlePublishBatch} disabled={publishing} className="xy-btn-primary px-5 py-2 text-sm">
                {publishing ? <><RefreshCw className="w-4 h-4 animate-spin mr-1" /> 发布中...</> : '开始发布'}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

const LAYER_LABELS: Record<string, string> = {
  layout: '布局',
  color_scheme: '配色',
  decoration: '装饰',
  title_style: '标题样式',
};

function QueueItemEditor({ item, onSave, category }: { item: QueueItem; onSave: () => void; category: string }) {
  const [title, setTitle] = useState(item.title);
  const [desc, setDesc] = useState(item.description);
  const [price, setPrice] = useState(item.price ?? '');
  const [frameId, setFrameId] = useState(item.frame_id);
  const [frames, setFrames] = useState<FrameMeta[]>([]);
  const [saving, setSaving] = useState(false);
  const [allAssets, setAllAssets] = useState<BrandAsset[]>([]);
  const [selectedAssetIds, setSelectedAssetIds] = useState<Set<string>>(new Set(item.brand_asset_ids || []));
  const [assetsChanged, setAssetsChanged] = useState(false);
  const [regenerating, setRegenerating] = useState(false);

  const [layerOptions, setLayerOptions] = useState<Record<string, LayerOption[]>>({});
  const [composition, setComposition] = useState<Record<string, string>>(item.composition || {});
  const isCompositionMode = Object.keys(composition).length > 0;
  const [previewUrl, setPreviewUrl] = useState<string>('');
  const [previewing, setPreviewing] = useState(false);

  useEffect(() => {
    Promise.all([
      getFrames(),
      getBrandAssets(category),
      getCompositionLayers(),
    ]).then(([framesRes, assetsRes, layersRes]) => {
      if (framesRes.data?.ok) setFrames(framesRes.data.frames || []);
      if (assetsRes.data?.ok) setAllAssets(assetsRes.data.assets || []);
      if (layersRes.data?.ok) {
        const { layout, color_scheme, decoration, title_style } = layersRes.data;
        setLayerOptions({ layout: layout || [], color_scheme: color_scheme || [], decoration: decoration || [], title_style: title_style || [] });
      }
    }).catch(() => {});
  }, [category]);

  const selectAllAssets = () => {
    setSelectedAssetIds(new Set(allAssets.map(a => a.id)));
    setAssetsChanged(true);
  };

  const deselectAllAssets = () => {
    setSelectedAssetIds(new Set());
    setAssetsChanged(true);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const updates: Record<string, any> = { title, description: desc, price: price || null, frame_id: frameId };
      if (assetsChanged) updates.brand_asset_ids = Array.from(selectedAssetIds);
      if (isCompositionMode) updates.composition = composition;
      await updateQueueItem(item.id, updates);
      toast.success('已保存');
      setAssetsChanged(false);
    } catch { toast.error('保存失败'); }
    setSaving(false);
  };

  const handleRegenWithFrame = async (newFrameId: string) => {
    setFrameId(newFrameId);
    try {
      const updates: Record<string, any> = { frame_id: newFrameId, composition: {} };
      if (assetsChanged) updates.brand_asset_ids = Array.from(selectedAssetIds);
      await updateQueueItem(item.id, updates);
      await regenerateQueueImages(item.id);
      toast.success('模板已切换并重新生成');
      setComposition({});
      setAssetsChanged(false);
    } catch { toast.error('切换失败'); }
  };

  const handleRegenWithAssets = async () => {
    setRegenerating(true);
    try {
      await updateQueueItem(item.id, { brand_asset_ids: Array.from(selectedAssetIds) });
      await regenerateQueueImages(item.id);
      toast.success('素材已更新并重新生成图片');
      setAssetsChanged(false);
    } catch { toast.error('重新生成失败'); }
    setRegenerating(false);
  };

  const handleLayerChange = (key: string, value: string) => {
    setComposition(prev => ({ ...prev, [key]: value }));
  };

  const handleRandomComposition = () => {
    const rand: Record<string, string> = {};
    for (const [key, opts] of Object.entries(layerOptions)) {
      if (opts.length > 0) {
        rand[key] = opts[Math.floor(Math.random() * opts.length)].id;
      }
    }
    setComposition(rand);
  };

  const handleCompositionRegenerate = async () => {
    setRegenerating(true);
    try {
      const updates: Record<string, any> = { composition, frame_id: '' };
      if (assetsChanged) updates.brand_asset_ids = Array.from(selectedAssetIds);
      await updateQueueItem(item.id, updates);
      await regenerateQueueImages(item.id);
      toast.success('组合图片已重新生成');
      setAssetsChanged(false);
    } catch { toast.error('重新生成失败'); }
    setRegenerating(false);
  };

  const handlePreviewComposition = async () => {
    setPreviewing(true);
    try {
      const res = await previewComposition(category, composition, Array.from(selectedAssetIds));
      if (res.data?.ok) {
        setPreviewUrl(res.data.image_url);
        setComposition(res.data.composition || composition);
      }
    } catch { toast.error('预览失败'); }
    setPreviewing(false);
  };

  const groupedAssets = allAssets.reduce<Record<string, BrandAsset[]>>((acc, a) => {
    (acc[a.name] = acc[a.name] || []).push(a);
    return acc;
  }, {});

  return (
    <div className="border-t border-xy-border p-4 bg-xy-gray-50 space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="xy-label text-xs">标题</label>
          <input type="text" className="xy-input px-3 py-2 text-sm" value={title} onChange={e => setTitle(e.target.value)} />
        </div>
        <div>
          <label className="xy-label text-xs">价格</label>
          <input type="number" step="0.01" className="xy-input px-3 py-2 text-sm" placeholder="留空自动" value={price} onChange={e => setPrice(e.target.value ? Number(e.target.value) : '')} />
        </div>
      </div>
      <div>
        <label className="xy-label text-xs">描述</label>
        <textarea className="xy-input px-3 py-2 text-sm h-20 resize-none" value={desc} onChange={e => setDesc(e.target.value)} />
      </div>

      {/* Brand Asset Selector */}
      <div>
        <div className="flex items-center justify-between mb-1.5">
          <label className="xy-label text-xs">品牌素材（勾选参与图片生成的品牌）</label>
          <div className="flex gap-2">
            <button onClick={selectAllAssets} className="text-[11px] text-xy-brand-600 hover:underline">全选</button>
            <button onClick={deselectAllAssets} className="text-[11px] text-red-500 hover:underline">全不选</button>
          </div>
        </div>
        {Object.keys(groupedAssets).length === 0 ? (
          <p className="text-xs text-xy-text-muted py-2">暂无品牌素材，请先在「素材管理」中上传</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {Object.entries(groupedAssets).map(([brandName, assets]) => {
              const allSelected = assets.every(a => selectedAssetIds.has(a.id));
              const someSelected = assets.some(a => selectedAssetIds.has(a.id));
              return (
                <button
                  key={brandName}
                  onClick={() => {
                    const ids = assets.map(a => a.id);
                    setSelectedAssetIds(prev => {
                      const next = new Set(prev);
                      if (allSelected) ids.forEach(id => next.delete(id));
                      else ids.forEach(id => next.add(id));
                      return next;
                    });
                    setAssetsChanged(true);
                  }}
                  className={`flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg border transition-colors ${
                    allSelected
                      ? 'border-emerald-500 bg-emerald-50 text-emerald-700 font-medium'
                      : someSelected
                        ? 'border-amber-400 bg-amber-50 text-amber-700'
                        : 'border-xy-border text-xy-text-muted hover:border-xy-brand-300'
                  }`}
                >
                  <span className={`w-3.5 h-3.5 rounded border flex items-center justify-center text-[10px] ${
                    allSelected ? 'bg-emerald-500 border-emerald-500 text-white' : someSelected ? 'bg-amber-400 border-amber-400 text-white' : 'border-gray-300'
                  }`}>
                    {allSelected ? '✓' : someSelected ? '−' : ''}
                  </span>
                  {brandName}
                  <span className="text-[10px] opacity-60">({assets.length})</span>
                </button>
              );
            })}
          </div>
        )}
        {assetsChanged && !isCompositionMode && (
          <div className="mt-2 flex items-center gap-2">
            <button
              onClick={handleRegenWithAssets}
              disabled={regenerating || selectedAssetIds.size === 0}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg bg-violet-50 border border-violet-300 text-violet-700 hover:bg-violet-100 transition-colors disabled:opacity-50"
            >
              {regenerating ? <RefreshCw className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />}
              更新素材并重新生成图片
            </button>
            <span className="text-[11px] text-xy-text-muted">已选 {selectedAssetIds.size} / {allAssets.length} 张</span>
          </div>
        )}
      </div>

      {/* Composition Layer Selector */}
      {Object.keys(layerOptions).length > 0 && (
        <div className="border border-indigo-200 rounded-xl p-4 bg-indigo-50/50">
          <div className="flex items-center justify-between mb-3">
            <label className="text-xs font-bold text-indigo-700 flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5" /> 组合式模版引擎
              <span className="font-normal text-[10px] text-indigo-400">4x4x5x3 = 240 种变体</span>
            </label>
            <div className="flex gap-2">
              <button onClick={handleRandomComposition} className="text-[11px] px-2.5 py-1 rounded-lg bg-indigo-100 text-indigo-700 hover:bg-indigo-200 transition-colors font-medium">
                随机组合
              </button>
              <button
                onClick={handlePreviewComposition}
                disabled={previewing || Object.keys(composition).length === 0}
                className="text-[11px] px-2.5 py-1 rounded-lg bg-indigo-500 text-white hover:bg-indigo-600 transition-colors font-medium disabled:opacity-50 flex items-center gap-1"
              >
                {previewing ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Eye className="w-3 h-3" />}
                预览
              </button>
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {(['layout', 'color_scheme', 'decoration', 'title_style'] as const).map(key => (
              <div key={key}>
                <label className="text-[11px] text-indigo-600 font-medium mb-1 block">{LAYER_LABELS[key]}</label>
                <select
                  className="xy-input px-2 py-1.5 text-xs w-full"
                  value={composition[key] || ''}
                  onChange={e => handleLayerChange(key, e.target.value)}
                >
                  <option value="">随机</option>
                  {(layerOptions[key] || []).map(opt => (
                    <option key={opt.id} value={opt.id}>{opt.name}</option>
                  ))}
                </select>
              </div>
            ))}
          </div>
          {Object.keys(composition).length > 0 && (
            <div className="mt-3 flex items-center gap-2">
              <button
                onClick={handleCompositionRegenerate}
                disabled={regenerating}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg bg-indigo-500 text-white hover:bg-indigo-600 transition-colors disabled:opacity-50"
              >
                {regenerating ? <RefreshCw className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />}
                应用组合并重新生成
              </button>
              <span className="text-[10px] text-indigo-400">
                {Object.entries(composition).map(([k, v]) => `${LAYER_LABELS[k]}:${v}`).join(' · ')}
              </span>
            </div>
          )}
          {previewUrl && (
            <div className="mt-3">
              <img src={previewUrl} alt="composition preview" className="w-60 h-60 object-cover rounded-xl border border-indigo-200" />
            </div>
          )}
        </div>
      )}

      {/* Frame Quick Switch (legacy) */}
      {!isCompositionMode && (
        <div>
          <label className="xy-label text-xs">固定模板（点击切换并重新生成图片）</label>
          <div className="flex flex-wrap gap-2 mt-1">
            {frames.map(f => (
              <button key={f.id} onClick={() => handleRegenWithFrame(f.id)} className={`px-3 py-1.5 text-xs rounded-lg border transition-colors ${
                f.id === frameId ? 'border-xy-brand-500 bg-xy-brand-50 text-xy-brand-700 font-medium' : 'border-xy-border hover:border-xy-brand-300'
              }`}>
                {f.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Preview */}
      {item.generated_images?.[0] && !previewUrl && (
        <div>
          <label className="xy-label text-xs">当前图片</label>
          <img src={`/api/generated-image?path=${encodeURIComponent(item.generated_images[0])}`} alt="preview" className="w-60 h-60 object-cover rounded-xl border border-xy-border mt-1" />
        </div>
      )}

      <div className="flex justify-end gap-2">
        <button onClick={handleSave} disabled={saving} className="xy-btn-primary px-4 py-2 text-sm">
          {saving ? '保存中...' : '保存修改'}
        </button>
      </div>
    </div>
  );
}

// ─── History Tab ─────────────────────────────────
function HistoryTab() {
  const [items, setItems] = useState<QueueItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getPublishQueue()
      .then(res => {
        if (res.data?.ok) {
          const all = res.data.items || [];
          setItems(all.filter(it => it.status === 'published' || it.status === 'failed').reverse());
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="xy-card p-6"><div className="h-32 bg-xy-gray-100 rounded-xl animate-pulse" /></div>;

  if (items.length === 0) {
    return (
      <div className="xy-card p-8 text-center text-xy-text-muted text-sm">
        暂无发布记录
      </div>
    );
  }

  return (
    <div className="space-y-2 animate-in fade-in">
      {items.map(item => {
        const ok = item.status === 'published';
        return (
          <div key={item.id} className="xy-card p-4 flex items-center gap-4">
            <div className="w-12 h-12 rounded-lg overflow-hidden bg-xy-gray-50 flex-shrink-0">
              {item.generated_images?.[0] ? (
                <img src={`/api/generated-image?path=${encodeURIComponent(item.generated_images[0])}`} alt="" className="w-full h-full object-cover" />
              ) : <div className="w-full h-full" />}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-xy-text-primary truncate">{item.title}</p>
              <p className="text-[11px] text-xy-text-muted">{item.scheduled_date} · {item.frame_id}</p>
            </div>
            <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${ok ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
              {ok ? '已发布' : '失败'}
            </span>
          </div>
        );
      })}
    </div>
  );
}

// ─── Main Page ──────────────────────────────────
const TABS = [
  { key: 'queue', label: '今日待发布', icon: <Send className="w-4 h-4" /> },
  { key: 'assets', label: '素材管理', icon: <ImageIcon className="w-4 h-4" /> },
  { key: 'history', label: '发布历史', icon: <Clock className="w-4 h-4" /> },
] as const;

type TabKey = typeof TABS[number]['key'];

export default function AutoPublish() {
  const [searchParams, setSearchParams] = useSearchParams();
  const { category } = useStoreCategory();
  const initialTab = (searchParams.get('tab') as TabKey) || 'queue';
  const [activeTab, setActiveTab] = useState<TabKey>(initialTab);
  const meta = CATEGORY_META[category];

  const handleTabChange = (tab: TabKey) => {
    setActiveTab(tab);
    setSearchParams({ tab });
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-6">
      <div className="mb-4">
        <h1 className="text-xl font-bold text-xy-text-primary flex items-center gap-2">
          <Package className="w-6 h-6" /> 自动上架
        </h1>
        <p className="text-sm text-xy-text-secondary mt-1">
          管理 {meta?.icon} {meta?.label || category} 品类的品牌素材、图片模板和发布计划
        </p>
      </div>

      <SchedulerPanel />

      {/* Tabs */}
      <div className="flex gap-1 mb-4 bg-xy-gray-50 p-1 rounded-xl">
        {TABS.map(tab => (
          <button key={tab.key} onClick={() => handleTabChange(tab.key)} className={`flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-sm font-medium transition-colors ${
            activeTab === tab.key ? 'bg-white text-xy-brand-600 shadow-sm' : 'text-xy-text-muted hover:text-xy-text-primary'
          }`}>
            {tab.icon} {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'queue' && <QueueTab category={category} />}
      {activeTab === 'assets' && <BrandAssetsTab category={category} />}
      {activeTab === 'history' && <HistoryTab />}
    </div>
  );
}
