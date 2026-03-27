import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Send } from 'lucide-react'
import { getPublishQueue } from '../../api/listing'

const PublishQueueCard = React.memo(function PublishQueueCard() {
  const [count, setCount] = useState(0);
  useEffect(() => {
    const today = new Date().toISOString().split('T')[0];
    getPublishQueue(today)
      .then(res => {
        if (res.data?.ok) {
          const pending = (res.data.items || []).filter(
            (it: any) => it.status === 'draft' || it.status === 'ready'
          );
          setCount(pending.length);
        }
      })
      .catch(() => {});
  }, []);

  return (
    <Link to="/products/auto-publish?tab=queue" className="flex items-center justify-between p-3 rounded-xl border border-xy-border hover:border-emerald-500 hover:bg-emerald-50 transition-colors group">
      <div className="flex items-center gap-3">
        <div className="bg-emerald-100 p-2 rounded-lg group-hover:bg-emerald-200 transition-colors"><Send className="w-5 h-5 text-emerald-600" /></div>
        <div>
          <span className="font-medium text-xy-text-primary">今日待发布</span>
          {count > 0 && <span className="ml-2 px-1.5 py-0.5 rounded-full bg-emerald-100 text-emerald-700 text-[11px] font-medium">{count} 条</span>}
        </div>
      </div>
      <span className="text-emerald-500">&rarr;</span>
    </Link>
  );
});

export default PublishQueueCard;
