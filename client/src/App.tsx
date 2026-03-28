import React, { lazy, Suspense } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import ErrorBoundary from './components/ErrorBoundary'
import Navbar from './components/Navbar'
import { StoreCategoryProvider } from './contexts/StoreCategoryContext'

const Dashboard = lazy(() => import('./pages/Dashboard'))
const Orders = lazy(() => import('./pages/Orders'))
const AutoPublish = lazy(() => import('./pages/products/AutoPublish'))
const ProductList = lazy(() => import('./pages/products/ProductList'))
const SystemConfig = lazy(() => import('./pages/config/SystemConfig'))
const AccountList = lazy(() => import('./pages/accounts/AccountList'))
const Messages = lazy(() => import('./pages/messages/Messages'))
const LogTerminal = lazy(() => import('./pages/LogTerminal'))

function PageLoader() {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500" />
    </div>
  )
}

function App() {
  return (
    <ErrorBoundary>
      <StoreCategoryProvider>
        <Router>
          <div className="min-h-screen bg-xy-bg text-xy-text-primary">
            <Navbar />
            <Suspense fallback={<PageLoader />}>
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/products" element={<ProductList />} />
                <Route path="/products/auto-publish" element={<AutoPublish />} />
                <Route path="/orders" element={<Orders />} />
                <Route path="/messages" element={<Messages />} />
                <Route path="/logs" element={<LogTerminal />} />
                <Route path="/accounts" element={<AccountList />} />
                <Route path="/config" element={<SystemConfig />} />
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </Routes>
            </Suspense>
            <Toaster position="top-right" toastOptions={{ className: 'text-sm font-medium' }} />
          </div>
        </Router>
      </StoreCategoryProvider>
    </ErrorBoundary>
  )
}

export default App
