import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import ErrorBoundary from './components/ErrorBoundary'
import Navbar from './components/Navbar'
import { StoreCategoryProvider } from './contexts/StoreCategoryContext'
import Dashboard from './pages/Dashboard'
import Orders from './pages/Orders'
import AutoPublish from './pages/products/AutoPublish'
import ProductList from './pages/products/ProductList'
import SystemConfig from './pages/config/SystemConfig'
import AccountList from './pages/accounts/AccountList'
import Messages from './pages/messages/Messages'
import LogTerminal from './pages/LogTerminal'
import ConfigLayout from './pages/config/ConfigLayout'
import ConfigOverview from './pages/config/sections/ConfigOverview'
import IntegrationSettings from './pages/config/sections/IntegrationSettings'

function App() {
  return (
    <ErrorBoundary>
      <StoreCategoryProvider>
        <Router>
          <div className="min-h-screen bg-xy-bg text-xy-text-primary">
            <Navbar />
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/products" element={<ProductList />} />
              <Route path="/products/auto-publish" element={<AutoPublish />} />
              <Route path="/orders" element={<Orders />} />
              <Route path="/messages" element={<Messages />} />
              <Route path="/logs" element={<LogTerminal />} />
              <Route path="/accounts" element={<AccountList />} />
              <Route path="/config" element={<ConfigLayout />}>
                <Route index element={<ConfigOverview />} />
                <Route path="store_category" element={<SystemConfig />} />
                <Route path="integrations" element={<IntegrationSettings />} />
                <Route path="auto_reply" element={<SystemConfig />} />
                <Route path="orders" element={<SystemConfig />} />
                <Route path="products" element={<SystemConfig />} />
                <Route path="notifications" element={<SystemConfig />} />
              </Route>
              <Route path="/analytics" element={<Navigate to="/dashboard" replace />} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
            <Toaster position="top-right" toastOptions={{ className: 'text-sm font-medium' }} />
          </div>
        </Router>
      </StoreCategoryProvider>
    </ErrorBoundary>
  )
}

export default App
