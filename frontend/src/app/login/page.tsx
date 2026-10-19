'use client';
import { FormEvent, useState } from 'react';
import Link from 'next/link';
import { apiFetch, saveAuth } from '@/lib/api';
export default function Login() { const [email,setEmail]=useState(''); const [password,setPassword]=useState(''); const [error,setError]=useState(''); const [busy,setBusy]=useState(false);
  async function submit(e:FormEvent){e.preventDefault();setBusy(true);setError('');try{const r=await apiFetch<any>('/api/v1/auth/login',{method:'POST',body:JSON.stringify({email,password})});saveAuth(r);location.href='/activities';}catch(err:any){setError(err.message)}finally{setBusy(false)}}
  return <section className="auth"><div className="eyebrow">SECURE ACCESS / 01</div><h1>登录秒抢</h1><p className="muted">进入活动报名与库存工作台。</p><form onSubmit={submit}><label>邮箱<input type="email" value={email} onChange={e=>setEmail(e.target.value)} required /></label><label>密码<input type="password" value={password} onChange={e=>setPassword(e.target.value)} required minLength={6}/></label>{error&&<div className="form-error">{error}</div>}<button className="primary" disabled={busy}>{busy?'登录中…':'登录'}</button></form><p className="switch">没有账号？<Link href="/register">注册</Link></p></section> }
