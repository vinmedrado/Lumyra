import { lazy, Suspense, type ReactNode } from 'react';
import { Redirect, Route, Switch } from 'wouter';
import { AdminLayout } from '../components/layouts/AdminLayout';
import { ClientLayout } from '../components/layouts/ClientLayout';
import { LoadingState } from '../components/ui/LoadingState';
import { GenericAdminPage } from '../pages/admin/GenericAdminPage';
import { GuestsPage } from '../pages/admin/GuestsPage';
import { GenericClientPage } from '../pages/client/GenericClientPage';
import { GuestPortal } from '../pages/guest/GuestPortal';
import { LandingPage } from '../pages/LandingPage';
import { Login } from '../pages/Login';
import { ProtectedRoute } from './routes';

const AdminDashboard = lazy(() => import('../pages/admin/AdminDashboard').then(module => ({ default: module.AdminDashboard })));
const AnalyticsPage = lazy(() => import('../pages/admin/AnalyticsPage').then(module => ({ default: module.AnalyticsPage })));
const ClientDashboard = lazy(() => import('../pages/client/ClientDashboard').then(module => ({ default: module.ClientDashboard })));
const PlaylistPage = lazy(() => import('../pages/client/PlaylistPage').then(module => ({ default: module.PlaylistPage })));
const PlaylistAdminPage = lazy(() => import('../pages/admin/PlaylistAdminPage').then(module => ({ default: module.PlaylistAdminPage })));
const NotificationsPage = lazy(() => import('../pages/admin/NotificationsPage').then(module => ({ default: module.NotificationsPage })));
const ActivityFeedPage = lazy(() => import('../pages/admin/ActivityFeedPage').then(module => ({ default: module.ActivityFeedPage })));
const CommandCenterRealtime = lazy(() => import('../pages/admin/CommandCenterRealtime').then(module => ({ default: module.CommandCenterRealtime })));

function PageShell({ children }: { children: ReactNode }) {
  return <Suspense fallback={<LoadingState label="Carregando experiência premium..." />}>{children}</Suspense>;
}

function AdminPage({ children }: { children: ReactNode }) {
  return <ProtectedRoute roles={['ADMIN']}><AdminLayout>{children}</AdminLayout></ProtectedRoute>;
}

function ClientPage({ children }: { children: ReactNode }) {
  return <ProtectedRoute roles={['CLIENT']}><ClientLayout>{children}</ClientLayout></ProtectedRoute>;
}

export function App() {
  return <Switch>
    <Route path="/" component={LandingPage} />
    <Route path="/login" component={Login} />
    <Route path="/guest/:token" component={GuestPortal} />

    <Route path="/admin"><Redirect to="/admin/dashboard" replace /></Route>
    <Route path="/admin/dashboard"><AdminPage><PageShell><AdminDashboard /></PageShell></AdminPage></Route>
    <Route path="/admin/events"><AdminPage><GenericAdminPage title="Eventos" subtitle="Cadastro e operação de eventos por tenant." /></AdminPage></Route>
    <Route path="/admin/guests"><AdminPage><GuestsPage /></AdminPage></Route>
    <Route path="/admin/tables"><AdminPage><GenericAdminPage title="Mesas" subtitle="Mapa de mesas com ocupação, conflitos e exportação." /></AdminPage></Route>
    <Route path="/admin/forms"><AdminPage><GenericAdminPage title="Formulários" subtitle="Crie formulários dinâmicos e acompanhe respostas." /></AdminPage></Route>
    <Route path="/admin/campaigns"><AdminPage><GenericAdminPage title="Campanhas" subtitle="Envio, preview, timeline e reenfileiramento de mensagens." /></AdminPage></Route>
    <Route path="/admin/whatsapp"><AdminPage><GenericAdminPage title="WhatsApp" subtitle="Logs, tentativas, erros e auditoria por convidado." /></AdminPage></Route>
    <Route path="/admin/playlist"><AdminPage><PageShell><PlaylistAdminPage /></PageShell></AdminPage></Route>
    <Route path="/admin/financial"><AdminPage><GenericAdminPage title="Financeiro" subtitle="Fornecedores, despesas, pagamentos e KPIs." /></AdminPage></Route>
    <Route path="/admin/documents"><AdminPage><GenericAdminPage title="Documentos" subtitle="Contratos, listas, comprovantes e download seguro." /></AdminPage></Route>
    <Route path="/admin/analytics"><AdminPage><PageShell><AnalyticsPage /></PageShell></AdminPage></Route>
    <Route path="/admin/insights"><AdminPage><GenericAdminPage title="Insights" subtitle="Alertas automáticos por severidade e ação recomendada." /></AdminPage></Route>
    <Route path="/admin/notifications"><AdminPage><PageShell><NotificationsPage /></PageShell></AdminPage></Route>
    <Route path="/admin/activity"><AdminPage><PageShell><ActivityFeedPage /></PageShell></AdminPage></Route>
    <Route path="/admin/command-center"><AdminPage><PageShell><CommandCenterRealtime /></PageShell></AdminPage></Route>
    <Route path="/admin/audit"><AdminPage><GenericAdminPage title="Auditoria" subtitle="Logs por usuário, ação, entidade e severidade." /></AdminPage></Route>
    <Route path="/admin/settings"><AdminPage><GenericAdminPage title="Configurações" subtitle="Tenant, usuários, integrações e preferências." /></AdminPage></Route>

    <Route path="/client"><Redirect to="/client/dashboard" replace /></Route>
    <Route path="/client/dashboard"><ClientPage><PageShell><ClientDashboard /></PageShell></ClientPage></Route>
    <Route path="/client/guests"><ClientPage><GenericClientPage title="Convidados" subtitle="Acompanhe sua lista sem telas técnicas." /></ClientPage></Route>
    <Route path="/client/rsvp"><ClientPage><GenericClientPage title="RSVP" subtitle="Veja confirmações, pendências e recusas de forma simples." /></ClientPage></Route>
    <Route path="/client/tables"><ClientPage><GenericClientPage title="Mesas" subtitle="Confira como os convidados estão sendo organizados." /></ClientPage></Route>
    <Route path="/client/timeline"><ClientPage><GenericClientPage title="Timeline" subtitle="Próximas etapas até o grande dia." /></ClientPage></Route>
    <Route path="/client/documents"><ClientPage><GenericClientPage title="Documentos" subtitle="Arquivos importantes compartilhados pela assessoria." /></ClientPage></Route>
    <Route path="/client/financial"><ClientPage><GenericClientPage title="Financeiro" subtitle="Resumo financeiro simplificado do evento." /></ClientPage></Route>
    <Route path="/client/messages"><ClientPage><GenericClientPage title="Mensagens" subtitle="Histórico de comunicados enviados aos convidados." /></ClientPage></Route>
    <Route path="/client/playlist"><ClientPage><PageShell><PlaylistPage /></PageShell></ClientPage></Route>

    <Route><Redirect to="/" replace /></Route>
  </Switch>;
}
