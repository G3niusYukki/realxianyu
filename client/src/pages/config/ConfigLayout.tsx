import React from 'react';
import { Outlet, useLocation, useNavigate, Link } from 'react-router-dom';
import { ChevronLeft, Settings } from 'lucide-react';
import { TAB_GROUPS, SECTION_LABELS } from '../constants';

export default function ConfigLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  
  const currentSection = location.pathname.split('/').pop() || 'overview';

  return (
    <div className="min-h-screen bg-xy-bg">
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="flex items-center gap-4 mb-6">
          <button 
            onClick={() => navigate('/')}
            className="flex items-center gap-2 text-xy-text-secondary hover:text-xy-primary transition-colors"
          >
            <ChevronLeft className="w-5 h-5" />
            <span>返回概览</span>
          </button>
          <h1 className="text-2xl font-bold text-xy-text-primary flex items-center gap-2">
            <Settings className="w-6 h-6" />
            系统配置
          </h1>
        </div>

        <div className="flex gap-6">
          <aside className="w-64 flex-shrink-0">
            <nav className="bg-white rounded-xl border border-xy-border shadow-sm overflow-hidden">
              <Link
                to="/config"
                className={`block px-4 py-3 text-sm font-medium border-b border-xy-border transition-colors ${
                  currentSection === 'config' || currentSection === '' 
                    ? 'bg-xy-primary/5 text-xy-primary border-l-4 border-l-xy-primary' 
                    : 'text-xy-text-primary hover:bg-gray-50'
                }`}
              >
                配置概览
              </Link>
              
              {TAB_GROUPS.map((group) => (
                <div key={group.group} className="border-b border-xy-border last:border-b-0">
                  <div className="px-4 py-2 text-xs font-semibold text-xy-text-secondary bg-gray-50">
                    {group.group}
                  </div>
                  {group.tabs.map((tab) => {
                    const isActive = currentSection === tab.key;
                    return (
                      <Link
                        key={tab.key}
                        to={`/config/${tab.key}`}
                        className={`block px-4 py-2.5 text-sm transition-colors flex items-center gap-2 ${
                          isActive 
                            ? 'bg-xy-primary/5 text-xy-primary border-l-4 border-l-xy-primary' 
                            : 'text-xy-text-primary hover:bg-gray-50'
                        }`}
                      >
                        <tab.icon className="w-4 h-4" />
                        {tab.name}
                      </Link>
                    );
                  })}
                </div>
              ))}
            </nav>
          </aside>

          <main className="flex-1 min-w-0">
            <div className="bg-white rounded-xl border border-xy-border shadow-sm">
              <Outlet />
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
