import { useTranslation } from "react-i18next";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { ActionButton } from "@/components/ui/egm-button";

interface BroadcastDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  text: string;
  onTextChange: (text: string) => void;
  onSend: () => void;
  sending: boolean;
}

export function BroadcastDialog({ open, onOpenChange, text, onTextChange, onSend, sending }: BroadcastDialogProps) {
  const { t } = useTranslation();
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("serverControl.broadcastDialog.title", { defaultValue: "Broadcast a Message" })}</DialogTitle>
          <DialogDescription>
            {t("serverControl.broadcastDialog.description", {
              defaultValue: "Sent instantly to every player currently connected to this server.",
            })}
          </DialogDescription>
        </DialogHeader>
        <Input
          value={text}
          onChange={(e) => onTextChange(e.target.value)}
          placeholder={t("serverControl.broadcastDialog.placeholder", { defaultValue: "Type your announcement..." })}
          autoFocus
        />
        <DialogFooter>
          <ActionButton variant="ghost" onClick={() => onOpenChange(false)} disabled={sending}>
            {t("serverControl.cancel", { defaultValue: "Cancel" })}
          </ActionButton>
          <ActionButton variant="arcane" onClick={onSend} disabled={sending || !text.trim()}>
            {sending
              ? t("serverControl.broadcastDialog.sending", { defaultValue: "Sending..." })
              : t("serverControl.broadcastDialog.send", { defaultValue: "Broadcast" })}
          </ActionButton>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
