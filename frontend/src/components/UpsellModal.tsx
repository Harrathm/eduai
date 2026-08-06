import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

interface UpsellModalProps {
  isOpen: boolean;
  onClose: () => void;
  requiredPack?: string;
  message?: string;
}

export default function UpsellModal({ isOpen, onClose, requiredPack = "Silver", message }: UpsellModalProps) {
  const navigate = useNavigate();

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
    }
    return () => {
      document.body.style.overflow = "unset";
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const handleUpgrade = () => {
    onClose();
    navigate("/dashboard/packs");
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="relative bg-white rounded-2xl shadow-2xl max-w-md w-full mx-4 overflow-hidden">
        {/* Header gradient */}
        <div className="bg-gradient-to-r from-orange to-orange-l p-6 text-white">
          <div className="flex items-center gap-3 mb-2">
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
            <h2 className="text-xl font-semibold">Contenu Premium</h2>
          </div>
        </div>
        
        {/* Content */}
        <div className="p-6">
          <p className="text-gray-700 text-center mb-6">
            {message || (
              <>
                Ce contenu nécessite le pack <strong className="text-orange">{requiredPack}</strong>.
                <br />
                Passez à l'offre supérieure pour y accéder.
              </>
            )}
          </p>
          
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-3 border border-gray-300 rounded-xl text-gray-700 font-medium hover:bg-gray-50 transition-colors"
            >
              Plus tard
            </button>
            <button
              onClick={handleUpgrade}
              className="flex-1 px-4 py-3 bg-gradient-to-r from-orange to-orange-l text-white rounded-xl font-medium hover:shadow-lg transition-all"
            >
              Voir les packs
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Global state for upsell modal
let globalUpsellHandler: ((message: string, pack?: string) => void) | null = null;

export function setUpsellHandler(handler: (message: string, pack?: string) => void) {
  globalUpsellHandler = handler;
}

export function triggerUpsell(message: string, pack?: string) {
  if (globalUpsellHandler) {
    globalUpsellHandler(message, pack);
  }
}
