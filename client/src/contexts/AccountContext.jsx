import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { nodeApi } from '../api';

const AccountContext = createContext(null);

export function AccountProvider({ children }) {
  const [currentAccountId] = useState('default');
  const [configLoaded, setConfigLoaded] = useState(false);
  const [xgjConfigured, setXgjConfigured] = useState(false);

  const checkConfig = useCallback(async () => {
    try {
      const res = await nodeApi.get('/config');
      const cfg = res.data?.config || {};
      const xgj = cfg.xianguanjia || {};
      setXgjConfigured(!!(xgj.app_key && xgj.app_secret && !xgj.app_key.includes('****')));
      setConfigLoaded(true);
    } catch {
      setConfigLoaded(true);
    }
  }, []);

  useEffect(() => {
    checkConfig();
    const handler = () => checkConfig();
    window.addEventListener('configUpdated', handler);
    return () => window.removeEventListener('configUpdated', handler);
  }, [checkConfig]);

  const currentAccount = { id: 'default', name: '默认店铺', enabled: true };

  return (
    <AccountContext.Provider
      value={{
        accounts: [currentAccount],
        currentAccount,
        currentAccountId,
        switchAccount: () => {},
        refreshAccounts: checkConfig,
        loading: !configLoaded,
        xgjConfigured,
      }}
    >
      {children}
    </AccountContext.Provider>
  );
}

export function useCurrentAccount() {
  const context = useContext(AccountContext);
  if (!context) {
    throw new Error('useCurrentAccount must be used within an AccountProvider');
  }
  return context;
}
