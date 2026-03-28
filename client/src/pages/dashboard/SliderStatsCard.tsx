import React, { useState, useEffect } from 'react'
import { Shield, ShieldCheck, ShieldAlert, ShieldX } from 'lucide-react'
import { getSliderStats, type SliderStats } from '../../api/dashboard'

const SliderStatsCard = React.memo(function SliderStatsCard() {
  const [stats, setStats] = useState<SliderStats | null>(null);
  const [hours, setHours] = useState(24);

  useEffect(() => {
    getSliderStats(hours)
      .then(res => { if (res.data?.ok) setStats(res.data); })
      .catch(() => {});
  }, [hours]);

  if (!stats || stats.total_triggers === 0) return null;

  const rateColor = (rate: number) =>
    rate >= 80 ? 'text-green-600' : rate >= 50 ? 'text-yellow-600' : 'text-red-600';
  const rateBg = (rate: number) =>
    rate >= 80 ? 'bg-green-100' : rate >= 50 ? 'bg-yellow-100' : 'bg-red-100';

  const ttlText = stats.avg_cookie_ttl_seconds != null
    ? stats.avg_cookie_ttl_seconds > 3600
      ? `${(stats.avg_cookie_ttl_seconds / 3600).toFixed(1)}h`
      : `${Math.round(stats.avg_cookie_ttl_seconds / 60)}min`
    : '--';

  return (
    <div className="xy-card p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base font-semibold text-xy-text-primary flex items-center gap-2">
          <Shield className="w-4 h-4 text-blue-500" /> 滑块验证
        </h3>
        <select
          className="text-xs border border-xy-border rounded-lg px-2 py-1 bg-white"
          value={hours}
          onChange={e => setHours(Number(e.target.value))}
        >
          <option value={6}>6h</option>
          <option value={24}>24h</option>
          <option value={72}>3天</option>
          <option value={168}>7天</option>
        </select>
      </div>

      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="text-center">
          <div className={`text-xl font-bold ${rateColor(stats.success_rate)}`}>
            {stats.success_rate}%
          </div>
          <div className="text-[11px] text-xy-text-secondary">总成功率</div>
        </div>
        <div className="text-center">
          <div className="text-xl font-bold text-xy-text-primary">{stats.total_triggers}</div>
          <div className="text-[11px] text-xy-text-secondary">触发次数</div>
        </div>
        <div className="text-center">
          <div className="text-xl font-bold text-xy-text-primary">{ttlText}</div>
          <div className="text-[11px] text-xy-text-secondary">Cookie均寿</div>
        </div>
      </div>

      <div className="space-y-2">
        {stats.nc_attempts > 0 && (
          <div className="flex items-center justify-between text-sm">
            <span className="flex items-center gap-1.5">
              {stats.nc_success_rate >= 50
                ? <ShieldCheck className="w-3.5 h-3.5 text-green-500" />
                : <ShieldAlert className="w-3.5 h-3.5 text-yellow-500" />}
              NC 滑块
            </span>
            <span>
              <span className={`font-medium ${rateColor(stats.nc_success_rate)}`}>
                {stats.nc_passed}/{stats.nc_attempts}
              </span>
              <span className={`ml-1 px-1.5 py-0.5 rounded text-[10px] font-medium ${rateBg(stats.nc_success_rate)} ${rateColor(stats.nc_success_rate)}`}>
                {stats.nc_success_rate}%
              </span>
            </span>
          </div>
        )}
        {stats.puzzle_attempts > 0 && (
          <div className="flex items-center justify-between text-sm">
            <span className="flex items-center gap-1.5">
              {stats.puzzle_success_rate >= 50
                ? <ShieldCheck className="w-3.5 h-3.5 text-green-500" />
                : <ShieldX className="w-3.5 h-3.5 text-red-500" />}
              拼图滑块
            </span>
            <span>
              <span className={`font-medium ${rateColor(stats.puzzle_success_rate)}`}>
                {stats.puzzle_passed}/{stats.puzzle_attempts}
              </span>
              <span className={`ml-1 px-1.5 py-0.5 rounded text-[10px] font-medium ${rateBg(stats.puzzle_success_rate)} ${rateColor(stats.puzzle_success_rate)}`}>
                {stats.puzzle_success_rate}%
              </span>
            </span>
          </div>
        )}
      </div>

      {(stats.screenshots?.length ?? 0) > 0 && (
        <details className="mt-3">
          <summary className="text-xs text-xy-text-secondary cursor-pointer hover:text-xy-text-primary">
            查看失败截图 ({stats.screenshots.length})
          </summary>
          <div className="mt-2 grid grid-cols-2 gap-2">
            {stats.screenshots.slice(0, 4).map((s, i) => (
              <div key={i} className="relative group">
                <img
                  src={`/api/slider/screenshot/${s.path.split('/').pop()}`}
                  alt={`${s.type} ${s.result}`}
                  className="w-full h-20 object-cover rounded border border-xy-border"
                  loading="lazy"
                />
                <div className="absolute bottom-0 left-0 right-0 bg-black/60 text-white text-[10px] px-1 py-0.5 rounded-b">
                  {s.type} · {s.result}
                </div>
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  );
});

export default SliderStatsCard;
