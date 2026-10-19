export function ErrorState({ message }: { message: string }) { return <div className="state error"><strong>请求未完成</strong><span>{message}</span></div> }
export function EmptyState({ text = '暂无记录' }: { text?: string }) { return <div className="state"><strong>{text}</strong></div> }
export function Loading() { return <div className="state"><span className="spinner" />加载中</div> }
