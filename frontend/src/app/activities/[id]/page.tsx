'use client';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { apiFetch } from '@/lib/api';
import { ErrorState, Loading } from '@/components/States';

export default function ActivityDetail() {
  const { id } = useParams<{ id: string }>();
  const [activity, setActivity] = useState<any>(null);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<any>(null);
  useEffect(() => { apiFetch<any>(`/api/v1/activities/${id}`).then(r => setActivity(r.data)).catch(e => setError(e.message)); }, [id]);
  async function register() {
    setSubmitting(true); setError('');
    try { const r = await apiFetch<any>(`/api/v1/activities/${id}/registrations`, { method: 'POST', headers: { 'Idempotency-Key': crypto.randomUUID() }, body: '{}' }); setResult(r.data); }
    catch (e: any) { setError(e.message); } finally { setSubmitting(false); }
  }
  if (!activity && !error) return <Loading />;
  if (!activity) return <ErrorState message={error} />;
  return <article className="detail"><div className="detail-top"><div><div className="eyebrow">ACTIVITY / {id}</div><h1>{activity.name}</h1><p className="lede">{activity.description}</p><div className="meta-row"><span>状态<br /><b>{activity.status}</b></span><span>剩余名额<br /><b className="stock">{activity.available_stock}</b></span></div></div><div className="detail-visual"><span>{activity.status}</span></div></div>{result ? <div className="success-panel"><div className="success-icon">✓</div><div><h2>报名请求已提交</h2><p>预约号：<code>{result.reservation_id}</code></p></div></div> : <div className="action-bar"><button className="primary large" disabled={submitting} onClick={register}>{submitting ? '提交中...' : '立即报名'}</button>{error && <div className="form-error">{error}</div>}</div>}</article>;
}
