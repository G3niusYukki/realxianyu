import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

interface CollapsibleSectionProps {
  title: string;
  summary?: React.ReactNode;
  guide?: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
  icon?: React.ReactNode;
  badge?: React.ReactNode;
}

export default function CollapsibleSection({
  title,
  summary,
  guide,
  defaultOpen = false,
  children,
  icon,
  badge,
}: CollapsibleSectionProps) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-xy-border rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-5 py-4 bg-xy-gray-50 hover:bg-xy-gray-100 transition-colors text-left"
        type="button"
      >
        <div className="flex items-center gap-2 min-w-0">
          {icon}
          <span className="font-bold text-xy-text-primary text-sm">{title}</span>
          {badge}
        </div>
        <div className="flex items-center gap-3 flex-shrink-0">
          {!open && summary && (
            <div className="hidden sm:flex items-center gap-1.5 text-xs text-xy-text-secondary">
              {summary}
            </div>
          )}
          {open ? <ChevronUp className="w-4 h-4 text-xy-text-muted" /> : <ChevronDown className="w-4 h-4 text-xy-text-muted" />}
        </div>
      </button>
      {open && (
        <div className="px-5 py-5 space-y-6">
          {guide && <p className="text-sm text-xy-text-secondary pb-4 border-b border-xy-border">{guide}</p>}
          {children}
        </div>
      )}
    </div>
  );
}
