import { Database, RotateCcw } from 'lucide-react';
import { demoActions, useDemoStore } from '../../demo/demoStore';
import { Button } from '../ui/Button';

export function DemoStatusBar() {
  const state = useDemoStore();

  function reset() {
    if (window.confirm('Restaurar todos os dados da demonstração?')) {
      demoActions.reset();
    }
  }

  return <div className="mb-6 flex flex-col gap-3 rounded-3xl border border-brand-200 bg-brand-50/80 px-4 py-3 text-sm text-brand-950 dark:border-white/10 dark:bg-white/10 dark:text-purple-50 sm:flex-row sm:items-center sm:justify-between">
    <div className="flex items-center gap-3">
      <span className="grid h-9 w-9 place-items-center rounded-2xl bg-brand-800 text-white"><Database size={17} /></span>
      <div>
        <p className="font-black">Demo integrada e persistente</p>
        <p className="text-xs opacity-70">Alterações aparecem na assessoria, nos noivos e no convite deste navegador.</p>
      </div>
    </div>
    <div className="flex items-center gap-3">
      <span className="hidden text-xs opacity-60 md:inline">Atualizado {new Date(state.updatedAt).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}</span>
      <Button type="button" variant="secondary" onClick={reset}><RotateCcw size={15} /> Restaurar demo</Button>
    </div>
  </div>;
}
