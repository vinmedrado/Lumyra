import { EmptyState } from '../../components/ui/EmptyState';
import { PageHeader } from '../../components/ui/PageHeader';
export function GenericClientPage({ title, subtitle }: { title: string; subtitle: string }) { return <><PageHeader title={title} subtitle={subtitle} /><EmptyState icon="💍" title="Tudo aparecerá aqui quando a assessoria atualizar" description="A experiência dos noivos foi desenhada para ser simples, emocional e sem telas técnicas." /></>; }
