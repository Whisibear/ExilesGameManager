import * as React from "react";
import { useTranslation } from "react-i18next";
import { CheckCircle2, LockKeyhole, ServerCog, ShieldCheck, UserRound } from "lucide-react";
import { authApi } from "@/api";
import type { AuthUser } from "@/types/models";
import { Input } from "@/components/ui/input";
import { PasswordInput } from "@/components/ui/password-input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { PublicLanguageSwitcher } from "@/components/layout/PublicLanguageSwitcher";

interface SetupScreenProps {
  onDone: (user: AuthUser) => void;
}

export function SetupScreen({ onDone }: SetupScreenProps) {
  const { t } = useTranslation();
  const [username, setUsername] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [confirm, setConfirm] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);
  const [submitting, setSubmitting] = React.useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (password !== confirm) {
      setError(t("auth.setup.passwordMismatch"));
      return;
    }
    setSubmitting(true);
    try {
      const user = await authApi.setup(username.trim(), password);
      onDone(user);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("auth.setup.createError"));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#0D1117] text-[#F1F5F9]">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_16%_14%,rgba(124,252,0,0.10),transparent_28rem),radial-gradient(circle_at_80%_18%,rgba(0,212,255,0.14),transparent_34rem),radial-gradient(circle_at_70%_88%,rgba(139,92,246,0.08),transparent_28rem)]" />
      <div className="pointer-events-none absolute inset-0 opacity-[0.14] [background-image:linear-gradient(rgba(0,212,255,0.08)_1px,transparent_1px),linear-gradient(90deg,rgba(0,212,255,0.08)_1px,transparent_1px)] [background-size:48px_48px]" />

      <div className="absolute right-4 top-4 z-30 sm:right-6 sm:top-6">
        <PublicLanguageSwitcher />
      </div>

      <div className="relative z-10 mx-auto grid min-h-screen w-full max-w-[1500px] lg:grid-cols-[1fr_1fr]">
        <section className="hidden min-h-screen flex-col justify-between border-r border-[#27303A]/80 px-12 py-12 lg:flex xl:px-20">
          <div>
            <div className="flex items-center gap-4">
              <img src="/branding/egm-icon-128.png" alt="Exiles Game Manager" className="h-16 w-16 rounded-2xl shadow-[0_0_38px_rgba(0,212,255,0.25)] ring-1 ring-[#00D4FF]/35" />
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

            <div className="mt-24 max-w-xl">
              <p className="mb-4 inline-flex items-center gap-2 rounded-full border border-[#7CFC00]/25 bg-[#7CFC00]/[0.07] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-[#B7FF69]">
                <ServerCog className="h-3.5 w-3.5" />
                {t("auth.setup.firstRun")}
              </p>
              <h1 className="font-display text-5xl font-bold leading-[1.08] tracking-[-0.03em]">
                {t("auth.setup.heroTitle")}
              </h1>
              <p className="mt-6 text-base leading-7 text-[#F1F5F9]/58">{t("auth.setup.heroText")}</p>

              <div className="mt-10 space-y-4">
                {[t("auth.setup.points.local"), t("auth.setup.points.superAdmin"), t("auth.setup.points.ready")].map((item) => (
                  <div key={item} className="flex items-center gap-3 text-sm text-[#F1F5F9]/62">
                    <CheckCircle2 className="h-5 w-5 text-[#7CFC00]" />
                    {item}
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
              <img src="/branding/egm-icon-128.png" alt="Exiles Game Manager" className="mb-4 h-20 w-20 rounded-2xl shadow-[0_0_34px_rgba(0,212,255,0.23)] ring-1 ring-[#00D4FF]/30" />
              <h1 className="font-display text-xl font-bold uppercase tracking-[0.08em]">
                <span className="text-[#F1F5F9]">Exiles </span>
                <span className="text-[#7CFC00]">Game </span>
                <span className="text-[#00D4FF]">Manager</span>
              </h1>
            </div>

            <div className="overflow-hidden rounded-3xl border border-[#27303A] bg-[#161B22]/92 shadow-[0_28px_90px_rgba(0,0,0,0.42),0_0_40px_rgba(0,212,255,0.055)] backdrop-blur-xl">
              <div className="border-b border-[#27303A] px-6 py-6 sm:px-7">
                <div className="flex items-start gap-4">
                  <div className="grid h-12 w-12 place-items-center rounded-2xl border border-[#7CFC00]/30 bg-[#7CFC00]/[0.08] text-[#B7FF69]">
                    <ShieldCheck className="h-5 w-5" />
                  </div>
                  <div>
                    <h2 className="font-display text-lg font-semibold tracking-wide text-[#F1F5F9]">{t("auth.setup.title")}</h2>
                    <p className="mt-1 text-sm text-[#F1F5F9]/45">{t("auth.setup.subtitle")}</p>
                  </div>
                </div>
              </div>

              <div className="p-6 sm:p-7">
                <div className="mb-6 rounded-2xl border border-[#00D4FF]/20 bg-[#00D4FF]/[0.045] p-4 text-sm leading-6 text-[#F1F5F9]/55">
                  <div className="mb-2 flex items-center gap-2 font-semibold text-[#00D4FF]">
                    <LockKeyhole className="h-4 w-4" />
                    {t("auth.setup.securityTitle")}
                  </div>
                  {t("auth.setup.description")}
                </div>

                <form onSubmit={handleSubmit} className="space-y-5">
                  <div className="space-y-2">
                    <Label htmlFor="setup-username" className="text-xs uppercase tracking-[0.1em] text-[#F1F5F9]/52">
                      {t("auth.common.username")}
                    </Label>
                    <div className="relative">
                      <UserRound className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#00D4FF]/55" />
                      <Input id="setup-username" value={username} onChange={(e) => setUsername(e.target.value)} className="h-12 border-[#27303A] bg-[#0D1117]/80 pl-10 text-[#F1F5F9] focus-visible:border-[#00D4FF]/60" autoFocus required minLength={3} />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="setup-password" className="text-xs uppercase tracking-[0.1em] text-[#F1F5F9]/52">
                      {t("auth.common.password")}
                    </Label>
                    <PasswordInput id="setup-password" value={password} onChange={(e) => setPassword(e.target.value)} className="h-12 border-[#27303A] bg-[#0D1117]/80 text-[#F1F5F9] focus-visible:border-[#00D4FF]/60" required minLength={8} />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="setup-confirm" className="text-xs uppercase tracking-[0.1em] text-[#F1F5F9]/52">
                      {t("auth.setup.confirmPassword")}
                    </Label>
                    <PasswordInput id="setup-confirm" value={confirm} onChange={(e) => setConfirm(e.target.value)} className="h-12 border-[#27303A] bg-[#0D1117]/80 text-[#F1F5F9] focus-visible:border-[#7CFC00]/60" required minLength={8} />
                  </div>

                  {error && <div role="alert" className="rounded-xl border border-red-500/30 bg-red-500/[0.08] px-4 py-3 text-sm text-red-300">{error}</div>}

                  <Button type="submit" className="h-12 w-full border border-[#7CFC00]/40 bg-[#7CFC00]/12 text-[#B7FF69] shadow-[0_0_26px_rgba(124,252,0,0.08)] hover:border-[#7CFC00]/70 hover:bg-[#7CFC00]/18" disabled={submitting}>
                    {submitting ? t("auth.setup.creating") : t("auth.setup.submit")}
                  </Button>
                </form>
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
