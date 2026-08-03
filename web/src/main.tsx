import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import "./index.css";
import "@/i18n";
import App from "./App.tsx";
import { NotificationProvider } from "@/hooks/useNotifications";
import { AuthProvider } from "@/hooks/useAuth";
import { TooltipProvider } from "@/components/ui/tooltip";


function reportFrontendError(message: string, source: string, stack?: string) {
  void fetch("/api/logs/frontend-event", {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ level: "error", message, source, stack, url: window.location.href }),
  }).catch(() => undefined);
}

window.addEventListener("error", (event) => {
  reportFrontendError(event.message || "Unhandled browser error", "window.error", event.error?.stack);
});
window.addEventListener("unhandledrejection", (event) => {
  const reason = event.reason;
  reportFrontendError(
    reason instanceof Error ? reason.message : String(reason),
    "unhandledrejection",
    reason instanceof Error ? reason.stack : undefined,
  );
});
createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <TooltipProvider delayDuration={200}>
        <NotificationProvider>
          <AuthProvider>
            <App />
          </AuthProvider>
        </NotificationProvider>
      </TooltipProvider>
    </BrowserRouter>
  </StrictMode>
);
