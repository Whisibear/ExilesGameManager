import { ExternalLink, Heart, Download } from "lucide-react";
import type { SteamWorkshopResult } from "@/types/models";
import { ActionButton } from "@/components/ui/egm-button";
import { useTranslation } from "react-i18next";

interface Props { mod: SteamWorkshopResult; wishlisted: boolean; busy: boolean; onWishlist: () => void; }
export function SteamWorkshopCard({ mod, wishlisted, busy, onWishlist }: Props) {
  const { t } = useTranslation();
  return <div className="rounded-xl border border-stone-700/70 bg-abyss-900/55 p-4">
    <div className="flex gap-3">
      {mod.pictureUrl && <img src={mod.pictureUrl} alt="" className="h-14 w-14 rounded-md object-cover" />}
      <div className="min-w-0 flex-1"><h3 className="font-display text-lg text-parchment-100">{mod.name}</h3><p className="text-xs text-parchment-300/55">{t("mods.steamBrowser.byAuthor", { defaultValue: "by {{author}}", author: mod.author })}</p></div>
      <span className="rounded-full border border-life-600/40 bg-life-500/10 px-2 py-1 text-[10px] uppercase text-life-300">{mod.categoryName}</span>
    </div>
    <p className="mt-3 line-clamp-5 text-sm leading-relaxed text-parchment-300/70">{mod.summary}</p>
    <div className="mt-3 flex gap-4 text-xs text-parchment-300/45"><span className="flex items-center gap-1"><Download className="h-3 w-3" />{mod.subscriptions.toLocaleString()}</span><span className="flex items-center gap-1"><Heart className="h-3 w-3" />{mod.favorites.toLocaleString()}</span></div>
    <div className="mt-4 grid grid-cols-2 gap-2">
      <ActionButton variant="ghost" size="sm" icon={<ExternalLink />} onClick={() => window.open(mod.steamUrl, "_blank")}>{t("mods.steamBrowser.view", { defaultValue: "View on Steam" })}</ActionButton>
      <ActionButton variant="gold" size="sm" icon={<Heart />} disabled={wishlisted || busy} onClick={onWishlist}>{wishlisted ? t("mods.steamBrowser.added", { defaultValue: "Wishlisted" }) : t("mods.steamBrowser.add", { defaultValue: "Add to Wishlist" })}</ActionButton>
    </div>
  </div>;
}
