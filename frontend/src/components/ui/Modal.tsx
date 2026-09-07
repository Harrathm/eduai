import { useEffect, useRef, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  maxWidth?: string;
}

export function Modal({ open, onClose, title, children, maxWidth = "max-w-md" }: ModalProps) {
  const overlayRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", handleKey);
      document.body.style.overflow = "";
    };
  }, [open, onClose]);

  if (!open) return null;

  return createPortal(
    <div
      ref={overlayRef}
      className="fixed inset-0 bg-black/50 z-50 overflow-y-auto"
      onClick={(e) => e.target === overlayRef.current && onClose()}
    >
      <div className="flex min-h-full items-center justify-center p-4">
        <div className={`bg-white rounded-3xl ${maxWidth} w-full p-8 relative my-auto`}>
          {title && (
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-semibold text-navy">{title}</h2>
              <button onClick={onClose} className="p-2 hover:bg-cream rounded-lg">
                <X className="w-5 h-5" />
              </button>
            </div>
          )}
          {children}
        </div>
      </div>
    </div>,
    document.body
  );
}

interface ConfirmModalProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmLabel?: string;
  loading?: boolean;
}

export function ConfirmModal({
  open,
  onClose,
  onConfirm,
  title,
  message,
  confirmLabel = "Confirmer",
  loading,
}: ConfirmModalProps) {
  return (
    <Modal open={open} onClose={onClose} title={title}>
      <p className="text-gray mb-6">{message}</p>
      <div className="flex gap-4">
        <button onClick={onClose} className="flex-1 py-3 bg-cream-m rounded-xl">
          Annuler
        </button>
        <button
          onClick={onConfirm}
          disabled={loading}
          className="flex-1 py-3 bg-orange text-white rounded-xl font-medium disabled:opacity-50"
        >
          {loading ? "Traitement..." : confirmLabel}
        </button>
      </div>
    </Modal>
  );
}
