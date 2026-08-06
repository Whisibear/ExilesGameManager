import * as React from "react";
import { useTranslation } from "react-i18next";
import { KeyRound, LockKeyhole, Server, ShieldCheck, UserRound, Workflow } from "lucide-react";
import { authApi } from "@/api";
import type { AuthUser } from "@/types/models";
import { Input } from "@/components/ui/input";
import { PasswordInput } from "@/components/ui/password-input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { PublicLanguageSwitcher } from "@/components/layout/PublicLanguageSwitcher";
import { PUBLIC_LANGUAGE_SELECTION_KEY } from "@/i18n";
import { getLanguageOption } from "@/i18n/languages";

interface LoginScreenProps {
  onDone: (user: AuthUser) => void;
}

type Mode = "login" | "register";

export function LoginScreen({ onDone }: LoginScreenProps) {
  const { t, i18n } = useTranslation();
  const [mode, setMode] = React.useState<Mode>("login");
  const [username, setUsername] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [inviteCode, setInviteCode] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);
  const [submitting, setSubmitting] = React.useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      let user =
        mode === "login"
          ? await authApi.login(username.trim(), password)
          : await authApi.register(username.trim(), password, inviteCode.trim());

      const selectedPublicLanguage = window.sessionStorage.getItem(PUBLIC_LANGUAGE_SELECTION_KEY);
      if (selectedPublicLanguage) {
        const language = getLanguageOption(i18n.resolvedLanguage ?? i18n.language).code;
        if (user.language !== language) {
          user = await authApi.setLanguage(language);
        }
        window.sessionStorage.removeItem(PUBLIC_LANGUAGE_SELECTION_KEY);
      }

      onDone(user);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("auth.common.genericError"));
    } finally {
      setSubmitting(false);
    }
  }

  function switchMode(next: Mode) {
    setMode(next);
    setError(null);
  }

  const features = [
    { icon: Server, title: t("auth.login.features.servers"), text: t("auth.login.features.serversText") },
    { icon: Workflow, title: t("auth.login.features.automation"), text: t("auth.login.features.automationText") },
    { icon: ShieldCheck, title: t("auth.login.features.secure"), text: t("auth.login.features.secureText") },
  ];

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#0D1117] text-[#F1F5F9]">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_18%_18%,rgba(124,252,0,0.11),transparent_28rem),radial-gradient(circle_at_80%_20%,rgba(0,212,255,0.13),transparent_34rem),radial-gradient(circle_at_68%_86%,rgba(139,92,246,0.09),transparent_28rem)]" />
      <div className="pointer-events-none absolute inset-0 opacity-[0.14] [background-image:linear-gradient(rgba(0,212,255,0.08)_1px,transparent_1px),linear-gradient(90deg,rgba(0,212,255,0.08)_1px,transparent_1px)] [background-size:48px_48px]" />

      <div className="absolute right-4 top-4 z-30 sm:right-6 sm:top-6">
        <PublicLanguageSwitcher />
      </div>

      <div className="relative z-10 mx-auto grid min-h-screen w-full max-w-[1500px] lg:grid-cols-[1.08fr_0.92fr]">
        <section className="hidden min-h-screen flex-col justify-between border-r border-[#27303A]/80 px-12 py-12 lg:flex xl:px-20">
          <div>
            <div className="flex items-center gap-4">
              <img
                src="/branding/egm-icon-128.png"
                alt="Exiles Game Manager"
                className="h-16 w-16 rounded-2xl shadow-[0_0_38px_rgba(0,212,255,0.25)] ring-1 ring-[#00D4FF]/35"
              />
              <div>
                <p className="font-display text-xl font-bold uppercase tracking-[0.09em]">
                  <span className="text-[#F1F5F9]">Exiles </span>
                  <span className="text-[#7CFC00]">Game </span>
                  <span className="text-[#00D4FF]">Manager</span>
                </p>
                <p className="mt-1 text-[10px] uppercase tracking-[0.22em] text-[#00D4FF]/70">
                  {t("auth.brandTagline")}
                </p>
              </div>
            </div>

            <div className="mt-24 max-w-2xl">
              <p className="mb-4 inline-flex items-center gap-2 rounded-full border border-[#00D4FF]/25 bg-[#00D4FF]/[0.07] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-[#00D4FF]">
                <LockKeyhole className="h-3.5 w-3.5" />
                {t("auth.login.privateAccess")}
              </p>
              <h1 className="font-display text-5xl font-bold leading-[1.08] tracking-[-0.03em] xl:text-6xl">
                {t("auth.login.heroTitle")}
              </h1>
              <p className="mt-6 max-w-xl text-base leading-7 text-[#F1F5F9]/58">
                {t("auth.login.heroText")}
              </p>

              <div className="mt-10 grid gap-4">
                {features.map(({ icon: Icon, title, text }) => (
                  <div
                    key={title}
                    className="group flex items-start gap-4 rounded-2xl border border-[#27303A] bg-[#161B22]/72 p-4 backdrop-blur transition-all duration-200 hover:-translate-y-0.5 hover:border-[#00D4FF]/35 hover:bg-[#161B22]"
                  >
                    <div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl border border-[#00D4FF]/25 bg-[#00D4FF]/[0.07] text-[#00D4FF] shadow-[0_0_24px_rgba(0,212,255,0.08)]">
                      <Icon className="h-5 w-5" />
                    </div>
                    <div>
                      <p className="font-semibold text-[#F1F5F9]">{title}</p>
                      <p className="mt-1 text-sm leading-5 text-[#F1F5F9]/48">{text}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <p className="text-xs text-[#F1F5F9]/34">{t("auth.login.footer")}</p>
        </section>

        <section className="flex min-h-screen items-center justify-center px-5 py-10 sm:px-8 lg:px-12 xl:px-20">
          <div className="w-full max-w-md">
            <div className="mb-8 flex flex-col items-center text-center lg:hidden">
              <img
                src="/branding/egm-icon-128.png"
                alt="Exiles Game Manager"
                className="mb-4 h-20 w-20 rounded-2xl shadow-[0_0_34px_rgba(0,212,255,0.23)] ring-1 ring-[#00D4FF]/30"
              />
              <h1 className="font-display text-xl font-bold uppercase tracking-[0.08em]">
                <span className="text-[#F1F5F9]">Exiles </span>
                <span className="text-[#7CFC00]">Game </span>
                <span className="text-[#00D4FF]">Manager</span>
              </h1>
            </div>

            <div className="overflow-hidden rounded-3xl border border-[#27303A] bg-[#161B22]/92 shadow-[0_28px_90px_rgba(0,0,0,0.42),0_0_40px_rgba(0,212,255,0.055)] backdrop-blur-xl">
              <div className="border-b border-[#27303A] px-6 py-6 sm:px-7">
                <div className="flex items-start gap-4">
                  <div className="grid h-12 w-12 place-items-center rounded-2xl border border-[#00D4FF]/30 bg-[#00D4FF]/[0.08] text-[#00D4FF]">
                    <KeyRound className="h-5 w-5" />
                  </div>
                  <div>
                    <h2 className="font-display text-lg font-semibold tracking-wide text-[#F1F5F9]">
                      {mode === "login" ? t("auth.login.title") : t("auth.register.title")}
                    </h2>
                    <p className="mt-1 text-sm text-[#F1F5F9]/45">
                      {mode === "login" ? t("auth.login.subtitle") : t("auth.register.subtitle")}
                    </p>
                  </div>
                </div>
              </div>

              <div className="p-6 sm:p-7">
                <div className="mb-6 grid grid-cols-2 rounded-xl border border-[#27303A] bg-[#0D1117]/70 p-1">
                  <button
                    type="button"
                    onClick={() => switchMode("login")}
                    className={cn(
                      "rounded-lg px-3 py-2.5 text-sm font-semibold transition-all duration-200",
                      mode === "login"
                        ? "bg-[#00D4FF]/12 text-[#00D4FF] shadow-[inset_0_0_0_1px_rgba(0,212,255,0.25)]"
                        : "text-[#F1F5F9]/42 hover:text-[#F1F5F9]/75"
                    )}
                  >
                    {t("auth.login.tab")}
                  </button>
                  <button
                    type="button"
                    onClick={() => switchMode("register")}
                    className={cn(
                      "rounded-lg px-3 py-2.5 text-sm font-semibold transition-all duration-200",
                      mode === "register"
                        ? "bg-[#8B5CF6]/14 text-[#B69AFF] shadow-[inset_0_0_0_1px_rgba(139,92,246,0.28)]"
                        : "text-[#F1F5F9]/42 hover:text-[#F1F5F9]/75"
                    )}
                  >
                    {t("auth.register.tab")}
                  </button>
                </div>

                <form onSubmit={handleSubmit} className="space-y-5">
                  <div className="space-y-2">
                    <Label htmlFor="auth-username" className="text-xs uppercase tracking-[0.1em] text-[#F1F5F9]/52">
                      {t("auth.common.username")}
                    </Label>
                    <div className="relative">
                      <UserRound className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#00D4FF]/55" />
                      <Input
                        id="auth-username"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        autoComplete="username"
                        className="h-12 border-[#27303A] bg-[#0D1117]/80 pl-10 text-[#F1F5F9] placeholder:text-[#F1F5F9]/22 focus-visible:border-[#00D4FF]/60"
                        autoFocus
                        required
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="auth-password" className="text-xs uppercase tracking-[0.1em] text-[#F1F5F9]/52">
                      {t("auth.common.password")}
                    </Label>
                    <PasswordInput
                      id="auth-password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      autoComplete={mode === "login" ? "current-password" : "new-password"}
                      className="h-12 border-[#27303A] bg-[#0D1117]/80 text-[#F1F5F9] focus-visible:border-[#00D4FF]/60"
                      required
                      minLength={mode === "register" ? 8 : undefined}
                    />
                  </div>

                  {mode === "register" && (
                    <div className="space-y-2">
                      <Label htmlFor="auth-invite" className="text-xs uppercase tracking-[0.1em] text-[#F1F5F9]/52">
                        {t("auth.register.inviteCode")}
                      </Label>
                      <Input
                        id="auth-invite"
                        value={inviteCode}
                        onChange={(e) => setInviteCode(e.target.value)}
                        placeholder={t("auth.register.invitePlaceholder")}
                        className="h-12 border-[#27303A] bg-[#0D1117]/80 text-[#F1F5F9] placeholder:text-[#F1F5F9]/22 focus-visible:border-[#8B5CF6]/60"
                        required
                      />
                    </div>
                  )}

                  {error && (
                    <div role="alert" className="rounded-xl border border-red-500/30 bg-red-500/[0.08] px-4 py-3 text-sm text-red-300">
                      {error}
                    </div>
                  )}

                  <Button
                    type="submit"
                    className="h-12 w-full border border-[#7CFC00]/40 bg-[#7CFC00]/12 text-[#B7FF69] shadow-[0_0_26px_rgba(124,252,0,0.08)] hover:border-[#7CFC00]/70 hover:bg-[#7CFC00]/18"
                    disabled={submitting}
                  >
                    {submitting
                      ? t("auth.common.working")
                      : mode === "login"
                        ? t("auth.login.submit")
                        : t("auth.register.submit")}
                  </Button>
                </form>
              </div>
            </div>

            <p className="mt-5 text-center text-xs text-[#F1F5F9]/30">{t("auth.login.localNotice")}</p>
          </div>
        </section>
      </div>
    </main>
  );
}
