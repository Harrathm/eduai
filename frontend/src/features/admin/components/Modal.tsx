import { ReactNode } from "react";
import { X } from "lucide-react";
import { Button } from "@/components/ui";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  footer?: ReactNode;
  size?: "sm" | "md" | "lg";
}

const sizeMap = { sm: "max-w-sm", md: "max-w-lg", lg: "max-w-2xl" };

export function Modal({ open, onClose, title, children, footer, size = "md" }: ModalProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className={`relative bg-white rounded-3xl w-full ${sizeMap[size]} shadow-dp max-h-[90vh] overflow-y-auto`}>
        <div className="flex items-center justify-between p-6 border-b border-black/5">
          <h2 className="text-xl font-semibold text-navy font-display">{title}</h2>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="w-5 h-5 text-gray" />
          </Button>
        </div>
        <div className="p-6">{children}</div>
        {footer && <div className="flex gap-4 p-6 border-t border-black/5">{footer}</div>}
      </div>
    </div>
  );
}

interface ConfirmModalProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmLabel?: string;
  danger?: boolean;
  loading?: boolean;
}

export function ConfirmModal({ open, onClose, onConfirm, title, message, confirmLabel = "Confirmer", danger, loading }: ConfirmModalProps) {
  return (
    <Modal
      open={open}
      onClose={onClose}
      title={title}
      size="sm"
      footer={
        <>
          <Button variant="ghost" onClick={onClose} disabled={loading}>
            Annuler
          </Button>
          <Button
            variant="primary"
            onClick={onConfirm}
            disabled={loading}
          >
            {loading ? "Traitement..." : confirmLabel}
          </Button>
        </>
      }
    >
      <p className="text-gray">{message}</p>
    </Modal>
  );
}