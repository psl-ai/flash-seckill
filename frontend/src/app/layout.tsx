import './globals.css';
import Nav from '@/components/Nav';
export default function RootLayout({ children }: { children: React.ReactNode }) { return <html lang="zh-CN"><body><Nav/><main className="shell">{children}</main><footer>秒抢 · 高并发活动报名与库存系统</footer></body></html> }
