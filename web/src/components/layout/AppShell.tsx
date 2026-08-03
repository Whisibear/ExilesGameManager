import { Outlet } from "react-router-dom";
import { Sidebar } from "@/components/layout/Sidebar";
import { TopBar } from "@/components/layout/TopBar";
import { FirstServerPrompt } from "@/components/onboarding/FirstServerPrompt";
import { UniversityQuestTracker } from "@/components/university/UniversityQuestTracker";

export function AppShell() {
  return (
    <div className="relative min-h-screen overflow-x-hidden bg-noise">
      <FirstServerPrompt />
      <UniversityQuestTracker />
      <Sidebar />
      <div className="relative z-10 pl-[76px] lg:pl-64">
        <TopBar />
        <main className="mx-auto w-full max-w-[1780px] px-4 py-5 sm:px-6 lg:px-8 lg:py-7">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
