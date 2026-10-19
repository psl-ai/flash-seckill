export type ApiEnvelope<T> = { code: string; message: string; request_id?: string; data: T };
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<ApiEnvelope<T>> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
  const headers = new Headers(init.headers);
  headers.set('Content-Type', 'application/json');
  if (token) headers.set('Authorization', `Bearer ${token}`);
  let response = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (response.status === 401 && typeof window !== 'undefined') {
    const refresh = localStorage.getItem('refresh_token');
    if (refresh) {
      const refreshed = await fetch(`${API_BASE}/api/v1/auth/refresh`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({refresh_token: refresh}) });
      if (refreshed.ok) {
        const body = await refreshed.json();
        const next = body.data?.access_token || body.access_token;
        if (next) { localStorage.setItem('access_token', next); headers.set('Authorization', `Bearer ${next}`); response = await fetch(`${API_BASE}${path}`, { ...init, headers }); }
      }
    }
  }
  const body = await response.json().catch(() => ({ code: 'HTTP_ERROR', message: response.statusText, data: null }));
  if (!response.ok || (body.code && body.code !== 'SUCCESS')) throw Object.assign(new Error(body.message || '请求失败'), { code: body.code, status: response.status });
  return body;
}

export function saveAuth(data: any) {
  if (typeof window === 'undefined') return;
  const source = data?.data || data;
  if (source?.access_token) localStorage.setItem('access_token', source.access_token);
  if (source?.refresh_token) localStorage.setItem('refresh_token', source.refresh_token);
  if (source?.user) localStorage.setItem('user', JSON.stringify(source.user));
}
export function logout() { if (typeof window !== 'undefined') { localStorage.removeItem('access_token'); localStorage.removeItem('refresh_token'); localStorage.removeItem('user'); } }
