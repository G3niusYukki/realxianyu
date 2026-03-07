import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api } from '../api/index';

const CATEGORY_META = {
  express:      { label: '快递代发',     icon: '📦', desc: '转转、闲鱼代发快递包裹' },
  exchange:     { label: '兑换码/卡密', icon: '🔑', desc: '游戏兑换码、充值卡密等虚拟商品' },
  recharge:     { label: '充值代充',     icon: '💳', desc: '游戏代充、会员充值' },
  movie_ticket: { label: '电影票',       icon: '🎬', desc: '电影票代购' },
  account:      { label: '账号交易',     icon: '👤', desc: '游戏/平台账号交易' },
  game:         { label: '游戏道具',     icon: '🎮', desc: '游戏装备、皮肤、道具' },
};

const EXPRESS_FEATURES = new Set([
  'route-stats', 'export-routes', 'import-routes',
  'markup-rules', 'import-markup', 'pricing',
  'delivery', 'auto-ship',
]);

const VIRTUAL_FEATURES = new Set([
  'virtual-goods-metrics', 'virtual-goods-inspect',
  'exchange-templates', 'auto-delivery-code',
]);

const UNIVERSAL_FEATURES = new Set([
  'dashboard', 'cookie', 'ai', 'xgj', 'oss',
  'auto-reply', 'messages', 'notifications',
  'order-reminder', 'accounts', 'config',
  'analytics', 'products', 'orders',
  'auto-publish', 'listing',
]);

const StoreCategoryContext = createContext(null);

export function StoreCategoryProvider({ children }) {
  const [category, setCategory] = useState('express');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/config')
      .then(res => {
        const saved = res.data?.config?.store?.category;
        if (saved && CATEGORY_META[saved]) setCategory(saved);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const switchCategory = useCallback(async (newCat) => {
    if (!CATEGORY_META[newCat]) return;
    setCategory(newCat);
    try {
      await api.put('/config', { store: { category: newCat } });
    } catch {
      // persist failure is non-critical
    }
  }, []);

  const isFeatureVisible = useCallback((featureKey) => {
    if (UNIVERSAL_FEATURES.has(featureKey)) return true;
    if (category === 'express') return EXPRESS_FEATURES.has(featureKey);
    return VIRTUAL_FEATURES.has(featureKey);
  }, [category]);

  const meta = CATEGORY_META[category] || CATEGORY_META.express;

  return (
    <StoreCategoryContext.Provider value={{ category, meta, allCategories: CATEGORY_META, switchCategory, isFeatureVisible, loading }}>
      {children}
    </StoreCategoryContext.Provider>
  );
}

export function useStoreCategory() {
  const ctx = useContext(StoreCategoryContext);
  if (!ctx) throw new Error('useStoreCategory must be used within StoreCategoryProvider');
  return ctx;
}

export { CATEGORY_META };
