'use client';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { apiFetch } from '@/lib/api';
import { EmptyState, ErrorState, Loading } from '@/components/States';

export default function Activities() {
  const [items, setItems] = useState<any[]>([]); const [query, setQuery] = useState(''); const [loading, setLoading] = useState(true); const [error, setError] = useState('');
  async function load() { setLoading(true); try { const response = await apiFetch<any>(`/api/v1/activities${query ? `?keyword=${encodeURIComponent(query)}` : ''}`); const data = response.data; setItems(Array.isArray(data) ? data : data?.items || []); setError(''); } catch (exc: any) { setError(exc.message); } finally { setLoading(false); } }
  useEffect(() => { load(); }, []);
  return <><section className="hero"><div><div className="eyebrow">LIVE CAPACITY / 03</div><h1>把握当下，<em>立即入场</em></h1><p>实时库存、异步确认与高并发报名链路，所有名额状态透明可见。</p></div><div className="hero-mark">∞</div></section><section className="toolbar"><input placeholder="搜索活动名称或关键词" value={query} onChange={event => setQuery(event.target.value)} onKeyDown={event => event.key === 'Enter' && load()} /><button onClick={load}>搜索</button></section>{loading ? <Loading /> : error ? <ErrorState message={error} /> : items.length === 0 ? <EmptyState text="当前没有已发布活动" /> : <div className="activity-grid">{items.map(activity => <Link className="activity-card" href={`/activities/${activity.id}`} key={activity.id}><div className="card-image"><span>{activity.status || 'published'}</span></div><div className="card-body"><div className="card-kicker">开放报名</div><h2>{activity.name}</h2><p>{activity.description || '查看活动详情与实时剩余名额。'}</p><div className="card-foot"><b>{activity.available_stock ?? '--'}</b><small>剩余名额</small><span>查看 →</span></div></div></Link>)}</div>}</>;
}
