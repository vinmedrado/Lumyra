import type { ReactNode } from 'react';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
export function ClientLayout({ children }: { children: ReactNode }) { return <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-rose-50 lg:flex"><Sidebar mode="client" /><main className="min-w-0 flex-1"><Topbar /><div className="mx-auto max-w-6xl p-4 lg:p-8">{children}</div></main></div>; }
