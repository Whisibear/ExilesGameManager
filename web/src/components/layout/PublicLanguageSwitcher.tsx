import { useTranslation } from "react-i18next";
import { Check, ChevronDown, Languages } from "lucide-react";
import { SUPPORTED_LANGUAGES, getLanguageOption } from "@/i18n/languages";
import { PUBLIC_LANGUAGE_SELECTION_KEY, setLanguage } from "@/i18n";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";

interface PublicLanguageSwitcherProps { className?: string; compact?: boolean; }

export function PublicLanguageSwitcher({ className, compact = false }: PublicLanguageSwitcherProps) {
  const { i18n, t } = useTranslation();
  const active = getLanguageOption(i18n.resolvedLanguage ?? i18n.language);
  function selectLanguage(code: string) {
    setLanguage(code);
    window.sessionStorage.setItem(PUBLIC_LANGUAGE_SELECTION_KEY, code);
  }
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button type="button" aria-label={t("topbar.languageSwitcher.label")} title={t("topbar.languageSwitcher.label")} className={cn("inline-flex h-10 items-center gap-2 rounded-xl border border-[#27303A] bg-[#161B22]/90 px-3 text-sm text-[#F1F5F9]/75 shadow-[0_12px_32px_rgba(0,0,0,0.25)] backdrop-blur-xl transition-all hover:border-[#00D4FF]/45 hover:text-[#00D4FF] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#00D4FF]/40", className)}>
          <Languages className="h-4 w-4 text-[#00D4FF]"/><span className="text-base leading-none" aria-hidden="true">{active.flag}</span>{!compact && <span className="hidden max-w-32 truncate sm:inline">{active.nativeName}</span>}<ChevronDown className="h-3.5 w-3.5 opacity-60"/>
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="min-w-56 border-[#27303A] bg-[#161B22] text-[#F1F5F9]">
        {SUPPORTED_LANGUAGES.map((language) => { const selected=language.code===active.code; return <DropdownMenuItem key={language.code} onSelect={()=>selectLanguage(language.code)} className="gap-3 focus:bg-[#00D4FF]/10 focus:text-[#00D4FF]"><span className="text-base leading-none" aria-hidden="true">{language.flag}</span><span className="min-w-0 flex-1 truncate">{language.nativeName}</span><span className="text-xs text-[#F1F5F9]/35">{language.englishName}</span>{selected&&<Check className="h-4 w-4 text-[#7CFC00]"/>}</DropdownMenuItem>; })}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
