import { useTranslation } from "react-i18next";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { SteamWorkshopBrowser } from "./SteamWorkshopBrowser";
interface Props { open:boolean; onOpenChange:(open:boolean)=>void; onInstalled:(mods:any[])=>void; }
export function WorkshopInstallDialog({open,onOpenChange}:Props){const {t}=useTranslation(); return <Dialog open={open} onOpenChange={onOpenChange}><DialogContent className="max-w-3xl"><DialogHeader><DialogTitle>{t("mods.steamBrowser.title", {defaultValue:"Browse Steam Workshop"})}</DialogTitle><DialogDescription>{t("mods.steamBrowser.description", {defaultValue:"Search Palworld Workshop mods and add any of them to the server wishlist for the super admin to review."})}</DialogDescription></DialogHeader><SteamWorkshopBrowser/></DialogContent></Dialog>}
