import * as React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import Dashboard from "@/pages/Dashboard";
import ServerSelection from "@/pages/ServerSelection";
import { useAuth } from "@/hooks/useAuth";

// Lazy-loaded so the initial bundle only ships Dashboard (the index route) -
// every other page becomes its own chunk, fetched on first navigation to it.
const Mods = React.lazy(() => import("@/pages/Mods"));
const ServerControl = React.lazy(() => import("@/pages/ServerControl"));
const WorldSettings = React.lazy(() => import("@/pages/WorldSettings"));
const LauncherFlags = React.lazy(() => import("@/pages/LauncherFlags"));
const Logs = React.lazy(() => import("@/pages/Logs"));
const Settings = React.lazy(() => import("@/pages/Settings"));
const SuperAdmin = React.lazy(() => import("@/pages/SuperAdmin"));
const ModWishlist = React.lazy(() => import("@/pages/ModWishlist"));
const University = React.lazy(() => import("@/pages/University"));
const Firewall = React.lazy(() => import("@/pages/Firewall"));
const BackupCenter = React.lazy(() => import("@/pages/BackupCenter"));
const Performance = React.lazy(() => import("@/pages/Performance"));
const TaskQueue = React.lazy(() => import("@/pages/TaskQueue"));
const ActivityCenter = React.lazy(() => import("@/pages/ActivityCenter"));

function RequireSuperAdmin({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  return user.role === "super_admin" ? <>{children}</> : <Navigate to="/" replace />;
}

function PageFallback() {
  return (
    <div className="flex h-64 items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-mana-600/25 border-t-mana-400" />
    </div>
  );
}

function App() {
  return (
    <Routes>
      <Route index element={<Navigate to="/servers" replace />} />
      <Route path="servers" element={<ServerSelection />} />
      <Route element={<AppShell />}>
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="players" element={<Navigate to="/dashboard" replace />} />
        <Route
          path="mods"
          element={
            <React.Suspense fallback={<PageFallback />}>
              <Mods />
            </React.Suspense>
          }
        />
        <Route
          path="control"
          element={
            <React.Suspense fallback={<PageFallback />}>
              <ServerControl />
            </React.Suspense>
          }
        />
        <Route
          path="world-settings"
          element={
            <React.Suspense fallback={<PageFallback />}>
              <WorldSettings />
            </React.Suspense>
          }
        />
        <Route path="launcher-flags" element={<Navigate to="/launcher-options" replace />} />
        <Route
          path="launcher-options"
          element={
            <RequireSuperAdmin>
              <React.Suspense fallback={<PageFallback />}>
                <LauncherFlags />
              </React.Suspense>
            </RequireSuperAdmin>
          }
        />
        <Route
          path="performance"
          element={<React.Suspense fallback={<PageFallback />}><Performance /></React.Suspense>}
        />
        <Route
          path="activity"
          element={<React.Suspense fallback={<PageFallback />}><ActivityCenter /></React.Suspense>}
        />
        <Route
          path="tasks"
          element={<RequireSuperAdmin><React.Suspense fallback={<PageFallback />}><TaskQueue /></React.Suspense></RequireSuperAdmin>}
        />
        <Route
          path="backup-center"
          element={<RequireSuperAdmin><React.Suspense fallback={<PageFallback />}><BackupCenter /></React.Suspense></RequireSuperAdmin>}
        />
        <Route
          path="firewall"
          element={<RequireSuperAdmin><React.Suspense fallback={<PageFallback />}><Firewall /></React.Suspense></RequireSuperAdmin>}
        />
        <Route
          path="logs"
          element={
            <React.Suspense fallback={<PageFallback />}>
              <Logs />
            </React.Suspense>
          }
        />
        <Route
          path="university"
          element={
            <React.Suspense fallback={<PageFallback />}>
              <University />
            </React.Suspense>
          }
        />
        <Route
          path="settings"
          element={
            <RequireSuperAdmin>
              <React.Suspense fallback={<PageFallback />}>
                <Settings />
              </React.Suspense>
            </RequireSuperAdmin>
          }
        />
        <Route
          path="super-admin"
          element={
            <RequireSuperAdmin>
              <React.Suspense fallback={<PageFallback />}>
                <SuperAdmin />
              </React.Suspense>
            </RequireSuperAdmin>
          }
        />
        <Route
          path="mod-wishlist"
          element={
            <RequireSuperAdmin>
              <React.Suspense fallback={<PageFallback />}>
                <ModWishlist />
              </React.Suspense>
            </RequireSuperAdmin>
          }
        />
      </Route>
    </Routes>
  );
}

export default App;
