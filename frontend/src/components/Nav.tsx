'use client';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { logout } from '@/lib/api';
export default function Nav() {
  const [user, setUser] = useState<any>(null);
  useEffect(() => { try { setUser(JSON.parse(localStorage.getItem('user') || 'null')); } catch {} }, []);
  return <header className="nav"><Link href="/activities" className="brand">秒抢 <span>HIGH VELOCITY REGISTRATION</span></Link><nav><Link href="/activities">活动</Link>{user && <Link href="/registrations">我的报名</Link>}{user?.role === 'admin' && <Link href="/admin">管理台</Link>}</nav><div className="nav-user">{user ? <><span>{user.display_name || user.email}</span><button onClick={() => { logout(); location.href='/login'; }}>退出</button></> : <Link href="/login">登录</Link>}</div></header>
}
