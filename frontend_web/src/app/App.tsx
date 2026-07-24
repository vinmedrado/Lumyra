import { lazy, Suspense, type ReactNode } from 'react';
import { Redirect, Route, Switch } from 'wouter';
import { AdminLayout } from '../components/layouts/AdminLayout';
import { ClientLayout } from '../components/layouts/ClientLayout';
import { LoadingState } from '../components/ui/LoadingState';
import { DemoAdminPage } from '../pages/admin/DemoAdminPage';
import { GuestsPage } from '../pages/admin/GuestsPage';
import { DemoClientPage } from '../pages/client/DemoClientPage';
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
    <Route path="/admin/events"><AdminPage><DemoAdminPage module="events" /></AdminPage></Route>
    <Route path="/admin/guests"><AdminPage><GuestsPage /></AdminPage></Route>
    <Route path="/admin/tables"><AdminPage><DemoAdminPage module="tables" /></AdminPage></Route>
    <Route path="/admin/forms"><AdminPage><DemoAdminPage module="forms" /></AdminPage></Route>
    <Route path="/admin/campaigns"><AdminPage><DemoAdminPage module="campaigns" /></AdminPage></Route>
    <Route path="/admin/whatsapp"><AdminPage><DemoAdminPage module="whatsapp" /></AdminPage></Route>
    <Route path="/admin/playlist"><AdminPage><PageShell><PlaylistAdminPage /></PageShell></AdminPage></Route>
    <Route path="/admin/financial"><AdminPage><DemoAdminPage module="financial" /></AdminPage></Route>
    <Route path="/admin/documents"><AdminPage><DemoAdminPage module="documents" /></AdminPage></Route>
    <Route path="/admin/analytics"><AdminPage><PageShell><AnalyticsPage /></PageShell></AdminPage></Route>
    <Route path="/admin/insights"><AdminPage><DemoAdminPage module="insights" /></AdminPage></Route>
    <Route path="/admin/notifications"><AdminPage><PageShell><NotificationsPage /></PageShell></AdminPage></Route>
    <Route path="/admin/activity"><AdminPage><PageShell><ActivityFeedPage /></PageShell></AdminPage></Route>
    <Route path="/admin/command-center"><AdminPage><PageShell><CommandCenterRealtime /></PageShell></AdminPage></Route>
    <Route path="/admin/audit"><AdminPage><DemoAdminPage module="audit" /></AdminPage></Route>
    <Route path="/admin/settings"><AdminPage><DemoAdminPage module="settings" /></AdminPage></Route>

    <Route path="/client"><Redirect to="/client/dashboard" replace /></Route>
    <Route path="/client/dashboard"><ClientPage><PageShell><ClientDashboard /></PageShell></ClientPage></Route>
    <Route path="/client/guests"><ClientPage><DemoClientPage module="guests" /></ClientPage></Route>
    <Route path="/client/rsvp"><ClientPage><DemoClientPage module="rsvp" /></ClientPage></Route>
    <Route path="/client/tables"><ClientPage><DemoClientPage module="tables" /></ClientPage></Route>
    <Route path="/client/timeline"><ClientPage><DemoClientPage module="timeline" /></ClientPage></Route>
    <Route path="/client/documents"><ClientPage><DemoClientPage module="documents" /></ClientPage></Route>
    <Route path="/client/financial"><ClientPage><DemoClientPage module="financial" /></ClientPage></Route>
    <Route path="/client/messages"><ClientPage><DemoClientPage module="messages" /></ClientPage></Route>
    <Route path="/client/playlist"><ClientPage><PageShell><PlaylistPage /></PageShell></ClientPage></Route>

    <Route><Redirect to="/" replace /></Route>
  </Switch>;
}
