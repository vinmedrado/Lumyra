import { EmptyState } from '../../components/ui/EmptyState';
import { PageHeader } from '../../components/ui/PageHeader';
export function GenericAdminPage({ title, subtitle }: { title: string; subtitle: string }) { return <><PageHeader title={title} subtitle={subtitle} /><EmptyState icon="📌" title={`${title} pronto para integração`} description="Esta tela moderna foi criada para consumir a FastAPI oficial. O Streamlit administrativo continua preservado para operação interna." actionLabel="Conectar endpoint" /></>; }
