import * as React from "react";
import type { AppNotification, NotificationKind } from "@/types/models";
import { NotificationStack } from "@/components/ui/notification-stack";

interface NotifyOptions {
  title: string;
  message?: string;
}

interface NotificationContextValue {
  notify: (kind: NotificationKind, options: NotifyOptions) => void;
  success: (options: NotifyOptions | string) => void;
  info: (options: NotifyOptions | string) => void;
  warning: (options: NotifyOptions | string) => void;
  error: (options: NotifyOptions | string) => void;
  dismiss: (id: string) => void;
}

const NotificationContext = React.createContext<NotificationContextValue | null>(null);

function normalize(opts: NotifyOptions | string): NotifyOptions {
  return typeof opts === "string" ? { title: opts } : opts;
}

export function NotificationProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = React.useState<AppNotification[]>([]);
  const recentRef = React.useRef<Map<string, number>>(new Map());

  const dismiss = React.useCallback((id: string) => {
    setItems((prev) => prev.filter((n) => n.id !== id));
  }, []);

  const notify = React.useCallback(
    (kind: NotificationKind, options: NotifyOptions) => {
      const now = Date.now();
      const signature = `${kind}\u0000${options.title}\u0000${options.message ?? ""}`;
      const lastShownAt = recentRef.current.get(signature) ?? 0;
      // React StrictMode and overlapping async callbacks can otherwise enqueue
      // the same result twice. Suppress only exact duplicates fired together.
      if (now - lastShownAt < 1500) return;
      recentRef.current.set(signature, now);
      for (const [key, shownAt] of recentRef.current) {
        if (now - shownAt > 10000) recentRef.current.delete(key);
      }

      const id = `n-${now}-${Math.random().toString(36).slice(2, 8)}`;
      const entry: AppNotification = {
        id,
        kind,
        title: options.title,
        message: options.message,
        createdAt: now,
      };
      setItems((prev) => [...prev, entry]);
      window.setTimeout(() => dismiss(id), 10_000);
    },
    [dismiss]
  );

  const value = React.useMemo<NotificationContextValue>(
    () => ({
      notify,
      success: (o) => notify("success", normalize(o)),
      info: (o) => notify("info", normalize(o)),
      warning: (o) => notify("warning", normalize(o)),
      error: (o) => notify("error", normalize(o)),
      dismiss,
    }),
    [notify, dismiss]
  );

  return (
    <NotificationContext.Provider value={value}>
      {children}
      <NotificationStack items={items} onDismiss={dismiss} />
    </NotificationContext.Provider>
  );
}

export function useNotifications() {
  const ctx = React.useContext(NotificationContext);
  if (!ctx) throw new Error("useNotifications must be used within NotificationProvider");
  return ctx;
}
