import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useAuthStore } from "../../../store/authStore";
import { api } from "../../../utils/apiClient";
import { PackConfiguratorModal } from "../components/pack/PackConfiguratorModal";
import { PageWrapper, Button } from "../../../components/ui";
import { Package } from "lucide-react";

interface Pack {
  id: number;
  nom: string;
  description: string | null;
  niveau_scolaire: string;
  matieres: string[] | null;
  prix_tnd: number;
  currency: string;
  validity_duration_days: number;
  tier: string;
  already_included_by_school: boolean;
  is_current: boolean;
  features: any;
}

function PackSkeleton() {
  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5 animate-pulse">
      <div className="h-5 w-48 bg-gray-200 rounded mb-3" />
      <div className="h-4 w-32 bg-gray-100 rounded mb-4" />
      <div className="h-16 bg-gray-50 rounded mb-4" />
      <div className="flex justify-between items-center">
        <div className="h-8 w-20 bg-gray-200 rounded" />
        <div className="h-8 w-24 bg-gray-100 rounded" />
      </div>
    </div>
  );
}

function PackCard({ pack, userNiveau, onBuy }: { pack: Pack; userNiveau?: string; onBuy: (pack: Pack) => void }) {
  const { t } = useTranslation();
  const isMatchingLevel = !userNiveau || pack.niveau_scolaire === userNiveau;

  return (
    <div
      className={`bg-white rounded-2xl p-6 shadow-sm border transition-all ${
        pack.already_included_by_school
          ? "border-green-200 bg-green-50/30"
          : pack.is_current
          ? "border-blue-300 bg-blue-50/30"
          : isMatchingLevel
          ? "border-orange/30 hover:shadow-md"
          : "border-black/5 opacity-60"
      }`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-navy">{pack.nom}</h3>
            {pack.tier && (
              <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium ${
                pack.tier === "golden" ? "bg-yellow-100 text-yellow-700" :
                pack.tier === "silver" ? "bg-gray-100 text-gray-600" :
                pack.tier === "basique" ? "bg-blue-100 text-blue-700" :
                "bg-green-100 text-green-700"
              }`}>
                {pack.tier.charAt(0).toUpperCase() + pack.tier.slice(1)}
              </span>
            )}
            {pack.is_current && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium bg-blue-100 text-blue-700">
                {t('packs.alreadyActive')}
              </span>
            )}
          </div>
          <p className="text-xs text-gray-400 mt-1">{pack.niveau_scolaire}</p>
        </div>
        {pack.already_included_by_school && (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
            {t('packs.includedViaSchool')}
          </span>
        )}
      </div>

      {/* Description */}
      {pack.description && (
        <p className="text-sm text-gray-600 mb-4 line-clamp-2">{pack.description}</p>
      )}

      {/* Matieres */}
      {pack.matieres && pack.matieres.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-4">
          {pack.matieres.map((m) => (
            <span key={m} className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full">
              {m}
            </span>
          ))}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-100">
        <div>
          <span className="text-2xl font-[300] text-navy">{pack.prix_tnd}</span>
          <span className="text-sm text-gray-400 ms-1">{pack.currency}</span>
          <p className="text-xs text-gray-400">
            {pack.validity_duration_days} {t('packs.daysValidity')}
          </p>
        </div>

        {pack.is_current ? (
          <div className="px-4 py-2 bg-blue-100 text-blue-700 text-sm font-medium rounded-xl">
            {t('packs.alreadyActive')}
          </div>
        ) : pack.already_included_by_school ? (
          <div className="px-4 py-2 bg-green-100 text-green-700 text-sm font-medium rounded-xl">
            {t('packs.alreadyActive')}
          </div>
        ) : (
          <Button
            variant="secondary"
            size="md"
            disabled={!isMatchingLevel}
            onClick={() => { if (isMatchingLevel) onBuy(pack); }}
          >
            {isMatchingLevel ? t('packs.buy') : t('packs.levelIncompatible')}
          </Button>
        )}
      </div>
    </div>
  );
}

export default function PacksPage() {
  const { t } = useTranslation();
  const { user } = useAuthStore();
  const [packs, setPacks] = useState<Pack[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [configPack, setConfigPack] = useState<Pack | null>(null);

  const userNiveau = user?.niveau_scolaire || "";

  useEffect(() => {
    if (!userNiveau) return;
    async function fetchPacks() {
      try {
        const url = `/api/abonnements/packs?niveau_scolaire=${encodeURIComponent(userNiveau)}`;
        const data = await api.get(url);
        setPacks(data.items || []);
      } catch (err: any) {
        setError(err.message || t('packs.loadingError'));
      } finally {
        setLoading(false);
      }
    }
    fetchPacks();
  }, [userNiveau]);

  return (
    <PageWrapper
      title={t('packs.title')}
      subtitle={
        userNiveau
          ? t('packs.niveauLabel') + " : " + userNiveau
          : t('packs.subtitle')
      }
      icon={<Package className="w-8 h-8" />}
    >
      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-2xl p-4 text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Packs Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <PackSkeleton key={i} />
          ))}
        </div>
      ) : packs.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 shadow-sm border border-black/5 text-center">
          <div className="text-4xl mb-4">📦</div>
          <h3 className="text-lg font-medium text-navy mb-2">{t('packs.noPacks')}</h3>
          <p className="text-sm text-gray-500">
            {userNiveau
              ? t('packs.noPacksForLevel', { level: userNiveau })
              : t('packs.noPacksPublished')}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {packs.map((pack) => (
            <PackCard key={pack.id} pack={pack} userNiveau={userNiveau} onBuy={setConfigPack} />
          ))}
        </div>
      )}

      {/* Pack Configurator Modal */}
      {configPack && (
        <PackConfiguratorModal
          isOpen={!!configPack}
          onClose={() => setConfigPack(null)}
          pack={{ id: configPack.id, tier: configPack.tier, name: configPack.nom, prix_tnd: configPack.prix_tnd, niveau_scolaire: configPack.niveau_scolaire }}
          userNiveau={userNiveau}
        />
      )}
    </PageWrapper>
  );
}
