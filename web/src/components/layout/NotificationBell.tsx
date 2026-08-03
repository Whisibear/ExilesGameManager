import * as React from "react";
import { Bell, CheckCheck, ExternalLink, Trash2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { notificationsApi } from "@/api";
import type { PersistentNotification } from "@/types/models";
import { DropdownMenu, DropdownMenuContent, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";

export function NotificationBell() {
 const {t,i18n}=useTranslation(); const navigate=useNavigate();
 const [items,setItems]=React.useState<PersistentNotification[]>([]); const [count,setCount]=React.useState(0); const [open,setOpen]=React.useState(false);
 const load=React.useCallback(async()=>{try{const r=await notificationsApi.list(false,20);setItems(r.notifications);setCount(r.unreadCount);}catch{}},[]);
 React.useEffect(()=>{void load(); const tick=()=>{if(document.visibilityState==="visible")void load();}; const timer=window.setInterval(tick,15000); document.addEventListener("visibilitychange",tick); return()=>{window.clearInterval(timer);document.removeEventListener("visibilitychange",tick);};},[load]);
 async function select(item:PersistentNotification){if(!item.read){try{await notificationsApi.markRead(item.id);}catch{} } setOpen(false); if(item.actionUrl) navigate(item.actionUrl); else navigate("/activity"); void load();}
 const title=(item:PersistentNotification)=>t(item.titleKey,{...item.params,defaultValue:item.fallbackTitle});
 const message=(item:PersistentNotification)=>item.messageKey?t(item.messageKey,{...item.params,defaultValue:item.fallbackMessage}):item.fallbackMessage;
 return <DropdownMenu open={open} onOpenChange={(value)=>{setOpen(value);if(value)void load();}}>
  <DropdownMenuTrigger asChild><button className="relative flex h-9 w-9 items-center justify-center rounded-lg border border-stone-700/80 bg-stone-900/55 text-parchment-200 transition hover:border-mana-500/50 hover:text-mana-300" aria-label={t("notifications.open")}><Bell className="h-4 w-4"/>{count>0&&<span className="absolute -right-1.5 -top-1.5 min-w-5 rounded-full bg-blood-500 px-1 text-center text-[10px] font-bold leading-5 text-white shadow-lg">{count>99?"99+":count}</span>}</button></DropdownMenuTrigger>
  <DropdownMenuContent align="end" className="w-[min(26rem,calc(100vw-2rem))] p-0">
   <div className="flex items-center justify-between p-3"><div><p className="font-semibold text-parchment-100">{t("notifications.title")}</p><p className="text-xs text-parchment-300/55">{t("notifications.unread",{count})}</p></div><div className="flex gap-1"><button title={t("notifications.markAllRead")} onClick={()=>void notificationsApi.markAllRead().then(load)} className="rounded p-2 hover:bg-mana-500/10"><CheckCheck className="h-4 w-4"/></button><button title={t("notifications.clearRead")} onClick={()=>void notificationsApi.clearRead().then(load)} className="rounded p-2 hover:bg-blood-500/10"><Trash2 className="h-4 w-4"/></button></div></div>
   <DropdownMenuSeparator/>
   <div className="max-h-96 overflow-auto">{items.length===0?<p className="p-6 text-center text-sm text-parchment-300/55">{t("notifications.empty")}</p>:items.map(item=><button key={item.id} onClick={()=>void select(item)} className={`block w-full border-b border-stone-700/50 p-3 text-left hover:bg-mana-500/[0.04] ${item.read?"opacity-60":"bg-mana-500/[0.025]"}`}><div className="flex gap-2"><span className={`mt-1 h-2 w-2 shrink-0 rounded-full ${item.kind==="error"?"bg-blood-400":item.kind==="warning"?"bg-yellow-400":item.kind==="success"?"bg-life-400":"bg-mana-400"}`}/><div className="min-w-0"><p className="truncate text-sm font-medium text-parchment-100">{title(item)}</p><p className="mt-0.5 line-clamp-2 text-xs text-parchment-300/65">{message(item)}</p><p className="mt-1 text-[10px] text-parchment-300/40">{new Date(item.createdAt*1000).toLocaleString(i18n.language)}</p></div></div></button>)}</div>
   <button onClick={()=>{setOpen(false);navigate("/activity");}} className="flex w-full items-center justify-center gap-2 p-3 text-xs font-semibold text-mana-300 hover:bg-mana-500/[0.06]">{t("notifications.viewAll")}<ExternalLink className="h-3.5 w-3.5"/></button>
  </DropdownMenuContent>
 </DropdownMenu>;
}
