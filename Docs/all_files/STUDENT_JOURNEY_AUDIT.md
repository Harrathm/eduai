# STUDENT_JOURNEY_AUDIT.md — Conformité Parcours Élève vs Frontend React

> **Date :** 05 Août 2026
> **Référence :** `eleve.md` (Parcours idéal élève)
> **Scope :** `frontend/src/` — Routes, Pages, Hooks, API, Design System

---

## 1. MATRICE DE CONFORMITÉ

### Légende

| Symbole | Signification |
|---------|--------------|
| ✅ | Page/Logique **existe et fonctionne** conformément au parcours idéal |
| ⚠️ | Page/Logique **existe mais est incomplète** (manque une fonctionnalité clé) |
| ❌ | Page/Logique **n'existe pas du tout** |

---

### Étape 1 : Inscription, Onboarding & Assignation Automatique

| # | Élément du parcours idéal | Status | Fichier existant | Écart |
|---|--------------------------|--------|-----------------|-------|
| 1.1 | Page d'accueil publique (`/`) | ⚠️ | Aucune `LandingPage` dédiée — le `/` redirige vers `/login` | Pas de page marketing/catalogue publique |
| 1.2 | Page d'inscription (`/register`) avec sélection du niveau d'étude | ✅ | `RegisterPage.tsx` + `OnboardingPage.tsx` | L'inscription existe, le onboarding (language + niveau) existe |
| 1.3 | Assignation automatique du Pack Gratuit | ⚠️ | Le backend assigne un pack au register, mais le frontend ne l'affiche pas | Le student ne voit pas de confirmation "Votre pack Gratuit a été activé" |
| 1.4 | Redirection immédiate vers Dashboard | ✅ | `OnboardingPage` → `navigate("/dashboard")` | Conforme |

### Étape 2 : Découverte du Dashboard & Déblocage du Quota Gratuit

| # | Élément du parcours idéal | Status | Fichier existant | Écart |
|---|--------------------------|--------|-----------------|-------|
| 2.1 | Aperçu des 3 leçons gratuites disponibles | ⚠️ | `StudentDashboard.tsx` affiche les stats globales (cours inscrits, progression) mais PAS la jauge "X/3 leçons gratuites utilisées" | La jauge de quota Gratuit n'est pas visible |
| 2.2 | Navigation dans les leçons autorisées | ✅ | `CatalogPage.tsx`, `CoursePlayerPage.tsx` | Le catalogue et le lecteur existent |
| 2.3 | **Trigger Conversion** : Modale "Fin du quota gratuit" | ❌ | Aucun composant, aucun hook, aucun listener | Le déclencheur "3 lecons consommées → modale upsell" n'existe pas |
| 2.4 | Bouton direct vers la boutique depuis la modale | ❌ | Dépend de 2.3 | Non implémenté |

### Étape 3 : Découverte de la Boutique & Configuration d'un Pack Payant

| # | Élément du parcours idéal | Status | Fichier existant | Écart |
|---|--------------------------|--------|-----------------|-------|
| 3.1 | Page Boutique (`/dashboard/packs`) avec filtrage par niveau | ✅ | `PacksPage.tsx` — filtre par niveau_scolaire, affiche les packs | Conforme |
| 3.2 | Affichage uniquement des packs adaptés au niveau de l'élève | ✅ | `PacksPage.tsx` filtre par `niveau_scolaire` | Conforme |
| 3.3 | **Configurateur Pack Basic** : choix 1 Langue + 1 Spécialité | ❌ | `PacksPage.tsx` affiche les packs mais le bouton "Acheter" redirige vers `/dashboard/my-pack` sans wizard de configuration | Pas de step-form de sélection de matières |
| 3.4 | **Configurateur Pack Silver** : choix 2 Langues + 2 Spécialités | ❌ | Idem 3.3 | Pas de step-form |
| 3.5 | Pack Golden : activation immédiate sans choix | ✅ | Le bouton "Acheter" pour Golden n'a pas de step de configuration | Conforme (par défaut) |
| 3.6 | **Paiement & Confirmation** : validation DT wallet → entitlements mis à jour | ⚠️ | `StudentPackPage.tsx` appelle `POST /api/abonnements/change-tier` mais PAS de flux de premier achat avec configuration de matières | Le premier achat avec sélection de matières n'est pas flow-ui |
| 3.7 | Affichage du prix en TND | ✅ | `PacksPage.tsx` et `StudentPackPage.tsx` affichent `pack.price` / `pack.prix_tnd` | Conforme |

### Étape 4 : Utilisation Quotidienne & Reconfiguration Trimestrielle

| # | Élément du parcours idéal | Status | Fichier existant | Écart |
|---|--------------------------|--------|-----------------|-------|
| 4.1 | Dashboard avec matières actives en avant | ⚠️ | `StudentDashboard.tsx` affiche les cours inscrits mais PAS les matières du pack sélectionné | Les matières actives du pack ne sont pas mises en avant |
| 4.2 | Navigation pédagogique Matière → Parcours → Leçon → Chapitre → Élément | ✅ | `MonParcoursPage.tsx`, `PathwayCatalogPage.tsx`, `CoursePlayerPage.tsx` | Hiérarchie implémentée |
| 4.3 | **Reconfiguration Trimestrielle** : lien dans les paramètres pour modifier les matières (Basic/Silver) | ❌ | `StudentPackPage.tsx` affiche les packs disponibles et permet le change-tier, mais PAS de bouton "Reconfigurer mes matières pour ce trimestre" | Pas d'UI de reconfiguration, pas d'API backend `/reconfigure-matieres` |
| 4.4 | Affichage du trimestre en cours | ❌ | Aucune indication du trimestre actuel ni de la date de reconfiguration | Pas de composant `TrimesterBadge` ou `TrimesterInfo` |
| 4.5 | Historique des choix de matières par trimestre | ❌ | Aucune donnée ni UI | Non implémenté |

### Étape 5 : Inscription aux Formations Hors-Scolaires (Soft Skills)

| # | Élément du parcours idéal | Status | Fichier existant | Écart |
|---|--------------------------|--------|-----------------|-------|
| 5.1 | Catalogue des Formations Soft Skills (`/dashboard/soft-skills`) | ✅ | `SoftSkillsCatalogPage.tsx` — liste les formations par catégorie | Conforme |
| 5.2 | Golden : accès gratuit aux formations incluses | ⚠️ | La page affiche "Incluses (Pack Golden)" dans les conditions d'accès mais ne vérifie PAS le tier de l'élève pour afficher le bon bouton | Le bouton "Commencer" s'affiche pour tous, pas de vérification Golden |
| 5.3 | Basic/Silver/Gratuit : formations gratuites accessibles, payantes avec bouton "Acheter" | ⚠️ | Le bouton affiche "Commencer" (gratuit) ou "Voir" (payant) mais ne déclenche PAS d'achat DT | Le flux d'achat d'une formation payante n'est pas implémenté |
| 5.4 | **Espace de suivi** "Mes Formations Hors-Scolaires" dans le Dashboard | ❌ | Aucune page ni section dans le Dashboard pour les formations en cours | Non implémenté |

---

### Routes existantes vs routes requises

| Route requise | Route existante | Status |
|--------------|----------------|--------|
| `/` (Landing Page) | `/login` (redirect) | ⚠️ Pas de landing |
| `/register` | `/register` | ✅ |
| `/login` | `/login` | ✅ |
| `/dashboard` | `/dashboard` → `StudentDashboard` | ✅ |
| `/dashboard/courses` | `/dashboard/courses` → `CatalogPage` | ✅ |
| `/dashboard/courses/:id` | `/dashboard/courses/:id` → `CoursePlayerPage` | ✅ |
| `/catalog/packs` | `/dashboard/packs` → `PacksPage` | ✅ (route décalée) |
| `/skills-catalog` | `/dashboard/soft-skills` → `SoftSkillsCatalogPage` | ✅ (route décalée) |
| `/my-skills` | — | ❌ Aucune route |
| `/settings/subscription` | `/dashboard/my-pack` → `StudentPackPage` | ⚠️ Pas de reconfiguration |

---

## 2. IDENTIFICATION DES ÉCARTS CRITIQUES

### Écart 1 : TRIGGER CONVERSION — Modale fin de quota gratuit ❌ CRITIQUE

**Fait :** Le système backend décompte les 3 leçons gratuites par trimestre (table `PackPurchase` avec `tier=gratuit`). Cependant, aucun composant frontend ne vérifie ce quota et ne déclenche la modale de conversion.

**Impact :** L'élève gratuit arrive au bout de ses 3 leçons sans aucun signal visuel. Le tunnel de conversion (Gratuit → Basique/Silver) est rompu.

**Composants manquants :**
- `useQuotaGuard.ts` — hook qui vérifie `quota_info.gratuit` et déclenche un callback quand `lessons_completed >= 3`
- `QuotaExhaustedModal.tsx` — modale avec CTA vers `/dashboard/packs`

---

### Écart 2 : CONFIGURATEUR DE PACK — Wizard de sélection de matières ❌ CRITIQUE

**Fait :** `PacksPage.tsx` affiche les packs et le bouton redirige vers `StudentPackPage.tsx` qui permet le `change-tier`. Mais il n'y a PAS d'étape intermédiaire pour choisir les matières.

**Règle CDG :**
- **Basic** : 1 Langue + 1 Spécialité
- **Silver** : 2 Langues + 2 Spécialités

**Impact :** L'élève ne peut pas personnaliser son pack. Le backend accepte un achat sans matières spécifiées, ce qui contredit la spec.

**Composants manquants :**
- `usePackConfigurator.ts` — hook gérant l'état du wizard (step 1: choix tier, step 2: sélection matières, step 3: confirmation)
- `PackConfiguratorModal.tsx` — modal step-form avec grille de sélection de matières
- `MatiereSelector.tsx` — composant de sélection avec filtres Langue/Spécialité

---

### Étape 3 : RECONFIGURATION TRIMESTRIELLE ❌ CRITIQUE

**Fait :** La spec exige qu'au début de chaque trimestre, les élèves Basic/Silver puissent modifier leurs matières. Aucune UI ni API backend n'existe pour cela.

**Règle CDG :**
- T1 : 15/9 → 15/12
- T2 : 5/1 → 31/3
- T3 : 1/4 → 15/6
- La reconfiguration n'est possible qu'au début du trimestre

**Impact :** Les élèves Basic/Silver sont figés sur leurs choix initiaux. Le cycle trimestriel n'est pas respecté.

**Composants manquants :**
- `useTrimesterReconfiguration.ts` — hook calculant le trimestre actuel et la fenêtre de reconfiguration
- `TrimesterReconfigBanner.tsx` — bannière dans le Dashboard/Settings indiquant "Nouveau trimestre — reconfigurez vos matières"
- `MatiereReconfigurationPage.tsx` — page dédiée avec sélection de nouvelles matières + confirmation

---

### Écart 4 : Jauges de Quota Gratuit dans le Dashboard ⚠️ IMPORTANT

**Fait :** `StudentDashboard.tsx` affiche les cours inscrits et la progression, mais PAS la jauge "2/3 leçons gratuites utilisées ce trimestre".

**Impact :** L'élève ne visualise pas sa consommation du quota gratuit, ce qui réduit la pression vers la conversion.

**Modification requise :**
- Ajouter un composant `QuotaGauge` dans `StudentDashboard.tsx` affichant `lessons_completed / 3` avec une barre de progression colorée

---

### Écart 5 : VÉRIFICATION TIER DANS SOFT SKILLS ⚠️ IMPORTANT

**Fait :** `SoftSkillsCatalogPage.tsx` affiche "Commencer" pour toutes les formations sans vérifier si l'élève est Golden (gratuit) ou non (payant).

**Impact :** Un élève Gratuit ou Basic pourrait accéder à des formations payantes sans payer.

**Modification requise :**
- Ajouter `useAuthStore().user.subscription_plan` ou appeler `tierApi.dashboard()` pour récupérer le tier
- Conditionner le bouton : Golden → "S'inscrire gratuitement" ; autres → "Acheter cette formation" (avec flux DT)

---

### Écart 6 : Espace "Mes Formations Hors-Scolaires" ❌ MANQUANT

**Fait :** Aucune page ni section dans le Dashboard ne liste les formations Soft Skills auxquelles l'élève est inscrit.

**Impact :** L'élève ne peut pas suivre ses formations non-scolaires.

**Composants manquants :**
- Route `/dashboard/my-skills`
- `MySoftSkillsPage.tsx` — liste des formations en cours avec progression
- `useMySoftSkills.ts` — hook pour récupérer les inscriptions Soft Skills

---

### Écart 7 : PAGE D'ACCUEIL (LANDING PAGE) ⚠️ IMPORTANT

**Fait :** Le route `/` redirige vers `/login`. Il n'y a pas de page marketing présentant la plateforme.

**Impact :** Pas de vitrine publique pour les prospects.

**Composants manquants :**
- `LandingPage.tsx` — page marketing avec présentation, témoignages, CTA vers `/register`

---

### Écart 8 : PAGE GESTION ABONNEMENT AVEC HISTORIQUE ⚠️ MOYEN

**Fait :** `StudentPackPage.tsx` affiche le pack actuel et les packs disponibles, mais PAS l'historique des factures ni le bouton "Upgrade vers Golden" clairement séparé.

**Impact :** L'élève ne voit pas son historique de paiements.

**Modification requise :**
- Ajouter un onglet "Historique" avec les transactions liées aux achats de packs
- Séparer clairement la zone "Upgrade" de la zone "Configuration"

---

### Écart 9 : DESIGN SYSTEM NON UTILISÉ PAR LES PAGES ÉLÈVE ⚠️ MOYEN

**Fait :** Aucune des 14 pages student n'importe de `src/components/ui/` (Button, Modal, Spinner, EmptyState, Input). Toutes utilisent du HTML brut ou des boutons inline.

**Impact :** Incohérence visuelle, pas de accessibilité aria, double maintenance.

---

## 3. PLAN DE RÉALISATION

### Phase 1 — Trigger Conversion (Quota Gratuit) — Priorité CRITIQUE

| Élément | Type | Fichier cible | Description |
|---------|------|---------------|-------------|
| `useQuotaGuard.ts` | Hook | `src/features/student/hooks/useQuotaGuard.ts` | Vérifie le quota gratuit (3 leçons/trimestre). Retourne `{ remaining, exhausted, loading }`. Écoute les changements de `dashboard.lessons_completed` |
| `QuotaExhaustedModal.tsx` | Composant | `src/features/student/components/quota/QuotaExhaustedModal.tsx` | Modale de conversion : "Vous avez consommé votre quota gratuit. Débloquez l'accès complet !" avec CTA vers `/dashboard/packs` |
| `QuotaGauge.tsx` | Composant | `src/features/student/components/quota/QuotaGauge.tsx` | Jauge visuelle `X/3 leçons` avec barre de progression |
| `StudentDashboard.tsx` | Modification | `src/features/student/pages/StudentDashboard.tsx` | Intégrer `QuotaGauge` + `useQuotaGuard` + `QuotaExhaustedModal` |

### Phase 2 — Configurateur de Pack — Priorité CRITIQUE

| Élément | Type | Fichier cible | Description |
|---------|------|---------------|-------------|
| `usePackConfigurator.ts` | Hook | `src/features/student/hooks/usePackConfigurator.ts` | Gère le state du wizard : step (tier → matières → confirmation), selectedTier, selectedMatieres (par catégorie), validation (1L+1S pour Basic, 2L+2S pour Silver) |
| `PackConfiguratorModal.tsx` | Composant | `src/features/student/components/pack/PackConfiguratorModal.tsx` | Modal step-form en 3 étapes. Utilise `Button`, `Modal` de `src/components/ui/` |
| `MatiereSelector.tsx` | Composant | `src/features/student/components/pack/MatiereSelector.tsx` | Grille de sélection de matières avec filtres Langue/Spécialité. Utilise `Button` de `src/components/ui/` |
| `PackCard.tsx` | Composant | `src/features/student/components/pack/PackCard.tsx` | Card de pack refactorisée avec bouton "Configurer et acheter" au lieu de redirect |
| `PacksPage.tsx` | Modification | `src/features/student/pages/PacksPage.tsx` | Remplacer le redirect par l'ouverture de `PackConfiguratorModal` |
| `abonnementApi.ts` | API | `src/api/abonnementApi.ts` | Ajouter `configurePack(packId, matieres[])` → `POST /api/abonnements/packs/{packId}/configure` |

### Phase 3 — Reconfiguration Trimestrielle — Priorité CRITIQUE

| Élément | Type | Fichier cible | Description |
|---------|------|---------------|-------------|
| `useTrimesterReconfiguration.ts` | Hook | `src/features/student/hooks/useTrimesterReconfiguration.ts` | Calcule le trimestre actuel (T1/T2/T3), la fenêtre de reconfiguration (premiers 15 jours), si reconfig déjà faite ce trimestre |
| `TrimesterReconfigBanner.tsx` | Composant | `src/features/student/components/trimester/TrimesterReconfigBanner.tsx` | Bannière contextuelle dans Dashboard + Settings : "Nouveau trimestre ! Reconfigurez vos matières" avec CTA |
| `MatiereReconfigurationPage.tsx` | Page | `src/features/student/pages/MatiereReconfigurationPage.tsx` | Page dédiée `/dashboard/reconfigure-pack` avec sélection de nouvelles matières + confirmation |
| `TrimesterBadge.tsx` | Composant | `src/features/student/components/trimester/TrimesterBadge.tsx` | Badge affichant "T1", "T2", "T3" + dates |
| `StudentPackPage.tsx` | Modification | `src/features/student/pages/StudentPackPage.tsx` | Ajouter section "Reconfiguration trimestrielle" avec `TrimesterReconfigBanner` |
| `StudentDashboard.tsx` | Modification | `src/features/student/pages/StudentDashboard.tsx` | Ajouter `TrimesterBadge` dans le header |
| `abonnementApi.ts` | API | `src/api/abonnementApi.ts` | Ajouter `reconfigureMatieres(packId, newMatieres[])` → `POST /api/abonnements/reconfigure` |

### Phase 4 — Soft Skills & Suivi — Priorité IMPORTANT

| Élément | Type | Fichier cible | Description |
|---------|------|---------------|-------------|
| `useMySoftSkills.ts` | Hook | `src/features/student/hooks/useMySoftSkills.ts` | Récupère les formations Soft Skills inscrites + progression |
| `MySoftSkillsPage.tsx` | Page | `src/features/student/pages/MySoftSkillsPage.tsx` | Page `/dashboard/my-skills` — liste des formations avec progression |
| `SoftSkillsCatalogPage.tsx` | Modification | `src/pages/learner/SoftSkillsCatalogPage.tsx` | Vérifier le tier de l'élève pour afficher le bon bouton (Gratuit/Payant/Inclus Golden) |
| Route | Modification | `src/App.tsx` | Ajouter `/dashboard/my-skills` → `MySoftSkillsPage` |
| Sidebar | Modification | `src/components/layout/DashboardLayout.tsx` | Ajouter "Mes Formations" dans la section Commercial |

### Phase 5 — Design System Migration — Priorité MOYEN

| Élément | Type | Fichiers cibles | Description |
|---------|------|-----------------|-------------|
| Remplacer tous les `<button>` par `<Button>` | Refactor | 14 pages student | Utiliser `Button` avec variants (primary, secondary, ghost) |
| Remplacer les loaders inline par `<Spinner>` / `<PageSpinner>` | Refactor | 14 pages student | Utiliser le Design System |
| Remplacer les modales custom par `<Modal>` / `<ConfirmModal>` | Refactor | 4 pages (Pack, Wallet, Profile, Inbox) | Utiliser le Design System |
| Remplacer les empty states par `<EmptyState>` | Refactor | 6 pages | Utiliser le Design System |
| Remplacer les inputs par `<Input>` | Refactor | 4 pages (Profile, Onboarding, Packs filter, Search) | Utiliser le Design System |

### Phase 6 — Landing Page — Priorité MOYEN

| Élément | Type | Fichier cible | Description |
|---------|------|---------------|-------------|
| `LandingPage.tsx` | Page | `src/pages/public/LandingPage.tsx` | Page marketing : hero, features, témoignages, CTA |
| Route | Modification | `src/App.tsx` | Ajouter `/` → `LandingPage` (au lieu de redirect `/login`) |

---

## 4. EXEMPLE DE CODE — Configurateur de Pack (Phase 2)

> **Fonctionnalité la plus critique** : le Configurateur de Pack est le cœur du tunnel de conversion. Sans lui, l'élève ne peut pas personnaliser son pack Basic/Silver.

### 4.1 Hook : `usePackConfigurator.ts`

```typescript
// src/features/student/hooks/usePackConfigurator.ts

import { useState, useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { abonnementApi } from "../../../api";

interface Matiere {
  id: number;
  name: string;
  category: "langue" | "specialite";
  niveau_scolaire: string;
}

interface PackConfig {
  id: number;
  tier: string;
  name: string;
  prix_tnd: number;
  niveau_scolaire: string;
}

interface UsePackConfiguratorReturn {
  step: "tier" | "matieres" | "confirm" | "success";
  selectedPack: PackConfig | null;
  selectedMatieres: number[];
  availableMatieres: Matiere[];
  loading: boolean;
  error: string | null;
  maxLangues: number;
  maxSpecialites: number;
  currentLangues: number;
  currentSpecialites: number;
  canProceed: boolean;
  validationMessage: string;
  selectPack: (pack: PackConfig) => void;
  toggleMatiere: (matiereId: number) => void;
  goBack: () => void;
  confirmPurchase: () => Promise<void>;
  reset: () => void;
}

export function usePackConfigurator(
  userNiveau: string | null
): UsePackConfiguratorReturn {
  const { t } = useTranslation();
  const [step, setStep] = useState<"tier" | "matieres" | "confirm" | "success">("tier");
  const [selectedPack, setSelectedPack] = useState<PackConfig | null>(null);
  const [selectedMatieres, setSelectedMatieres] = useState<number[]>([]);
  const [availableMatieres, setAvailableMatieres] = useState<Matiere[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const maxLangues = selectedPack?.tier === "silver" ? 2 : selectedPack?.tier === "basique" ? 1 : 0;
  const maxSpecialites = selectedPack?.tier === "silver" ? 2 : selectedPack?.tier === "basique" ? 1 : 0;

  const langues = useMemo(
    () => availableMatieres.filter((m) => m.category === "langue"),
    [availableMatieres]
  );
  const specialites = useMemo(
    () => availableMatieres.filter((m) => m.category === "specialite"),
    [availableMatieres]
  );

  const selectedLangues = useMemo(
    () => selectedMatieres.filter((id) => langues.some((l) => l.id === id)).length,
    [selectedMatieres, langues]
  );
  const selectedSpecialites = useMemo(
    () => selectedMatieres.filter((id) => specialites.some((s) => s.id === id)).length,
    [selectedMatieres, specialites]
  );

  const canProceed = useMemo(() => {
    if (step === "tier") return !!selectedPack;
    if (step === "matieres") {
      if (!selectedPack || selectedPack.tier === "golden") return true;
      return selectedLangues === maxLangues && selectedSpecialites === maxSpecialites;
    }
    return true;
  }, [step, selectedPack, selectedLangues, selectedSpecialites, maxLangues, maxSpecialites]);

  const validationMessage = useMemo(() => {
    if (step !== "matieres" || !selectedPack || selectedPack.tier === "golden") return "";
    const languesNeeded = maxLangues - selectedLangues;
    const specNeeded = maxSpecialites - selectedSpecialites;
    if (languesNeeded > 0 && specNeeded > 0) {
      return t("packConfig.selectRemaining", {
        langues: languesNeeded,
        specialites: specNeeded,
      });
    }
    if (languesNeeded > 0) {
      return t("packConfig.selectLangues", { count: languesNeeded });
    }
    if (specNeeded > 0) {
      return t("packConfig.selectSpecialites", { count: specNeeded });
    }
    return t("packConfig.readyToConfirm");
  }, [step, selectedPack, maxLangues, maxSpecialites, selectedLangues, selectedSpecialites, t]);

  const selectPack = useCallback(async (pack: PackConfig) => {
    setSelectedPack(pack);
    setSelectedMatieres([]);
    setError(null);

    if (pack.tier === "golden") {
      setStep("confirm");
      return;
    }

    try {
      setLoading(true);
      const matieres = await abonnementApi.getAvailableMatieres(
        pack.niveau_scolaire
      );
      setAvailableMatieres(matieres);
      setStep("matieres");
    } catch (err: any) {
      setError(err.message || t("packConfig.errorLoadingMatieres"));
    } finally {
      setLoading(false);
    }
  }, [t]);

  const toggleMatiere = useCallback(
    (matiereId: number) => {
      setSelectedMatieres((prev) => {
        if (prev.includes(matiereId)) {
          return prev.filter((id) => id !== matiereId);
        }

        const matiere = availableMatieres.find((m) => m.id === matiereId);
        if (!matiere) return prev;

        const currentCount =
          matiere.category === "langue" ? selectedLangues : selectedSpecialites;
        const maxCount =
          matiere.category === "langue" ? maxLangues : maxSpecialites;

        if (currentCount >= maxCount) return prev;

        return [...prev, matiereId];
      });
    },
    [availableMatieres, selectedLangues, selectedSpecialites, maxLangues, maxSpecialites]
  );

  const goBack = useCallback(() => {
    if (step === "matieres") setStep("tier");
    else if (step === "confirm") {
      if (selectedPack?.tier === "golden") setStep("tier");
      else setStep("matieres");
    }
  }, [step, selectedPack]);

  const confirmPurchase = useCallback(async () => {
    if (!selectedPack) return;
    setLoading(true);
    setError(null);
    try {
      await abonnementApi.purchasePack(selectedPack.id, {
        matieres:
          selectedPack.tier !== "golden" ? selectedMatieres : undefined,
      });
      setStep("success");
    } catch (err: any) {
      setError(err.message || t("packConfig.purchaseError"));
    } finally {
      setLoading(false);
    }
  }, [selectedPack, selectedMatieres, t]);

  const reset = useCallback(() => {
    setStep("tier");
    setSelectedPack(null);
    setSelectedMatieres([]);
    setAvailableMatieres([]);
    setError(null);
  }, []);

  return {
    step,
    selectedPack,
    selectedMatieres,
    availableMatieres,
    loading,
    error,
    maxLangues,
    maxSpecialites,
    currentLangues: selectedLangues,
    currentSpecialites: selectedSpecialites,
    canProceed,
    validationMessage,
    selectPack,
    toggleMatiere,
    goBack,
    confirmPurchase,
    reset,
  };
}
```

### 4.2 Composant : `PackConfiguratorModal.tsx`

```typescript
// src/features/student/components/pack/PackConfiguratorModal.tsx

import { Fragment } from "react";
import { useTranslation } from "react-i18next";
import { Modal, Button } from "../../../../components/ui";
import { usePackConfigurator } from "../../hooks/usePackConfigurator";
import { MatiereSelector } from "./MatiereSelector";
import { CheckCircle, ArrowLeft, Loader2 } from "lucide-react";

interface Pack {
  id: number;
  tier: string;
  name: string;
  prix_tnd: number;
  niveau_scolaire: string;
}

interface PackConfiguratorModalProps {
  isOpen: boolean;
  onClose: () => void;
  pack: Pack;
  userNiveau: string | null;
}

const TIER_LABELS: Record<string, string> = {
  basique: "Basique",
  silver: "Silver",
  golden: "Golden",
};

const TIER_DESCRIPTIONS: Record<string, string> = {
  basique: "1 Matiere de Langue + 1 Matiere de Specialite",
  silver: "2 Matieres de Langues + 2 Matieres de Specialites",
  golden: "Acces illimite a toutes les matieres + Soft Skills",
};

export function PackConfiguratorModal({
  isOpen,
  onClose,
  pack,
  userNiveau,
}: PackConfiguratorModalProps) {
  const { t } = useTranslation();
  const configurator = usePackConfigurator(userNiveau);

  const handleClose = () => {
    configurator.reset();
    onClose();
  };

  const stepLabels = ["Pack", "Matieres", "Confirmation"];

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title={t("packConfig.title")}>
      <div className="space-y-6">
        {/* Step Indicator */}
        <div className="flex items-center gap-2">
          {stepLabels.map((label, i) => {
            const stepIndex =
              configurator.step === "tier"
                ? 0
                : configurator.step === "matieres"
                ? 1
                : configurator.step === "confirm"
                ? 2
                : 2;
            const isActive = i === stepIndex;
            const isDone = i < stepIndex;
            return (
              <Fragment key={label}>
                <div className="flex items-center gap-2">
                  <div
                    className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
                      isDone
                        ? "bg-green-500 text-white"
                        : isActive
                        ? "bg-navy text-white"
                        : "bg-gray-200 text-gray-500"
                    }`}
                  >
                    {isDone ? "✓" : i + 1}
                  </div>
                  <span
                    className={`text-xs font-medium ${
                      isActive ? "text-navy" : "text-gray-400"
                    }`}
                  >
                    {label}
                  </span>
                </div>
                {i < stepLabels.length - 1 && (
                  <div
                    className={`flex-1 h-0.5 ${
                      isDone ? "bg-green-500" : "bg-gray-200"
                    }`}
                  />
                )}
              </Fragment>
            );
          })}
        </div>

        {/* Error */}
        {configurator.error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-sm text-red-700">
            {configurator.error}
          </div>
        )}

        {/* Step: Tier Selection (already selected, just showing info) */}
        {configurator.step === "tier" && (
          <div className="space-y-4">
            <div className="bg-navy/5 rounded-2xl p-6">
              <h3 className="font-semibold text-navy text-lg">
                {TIER_LABELS[pack.tier]} — {pack.name}
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                {TIER_DESCRIPTIONS[pack.tier]}
              </p>
              <p className="text-2xl font-[300] text-navy mt-3">
                {pack.prix_tnd}{" "}
                <span className="text-sm text-gray-400">TND</span>
              </p>
            </div>

            {pack.tier !== "golden" && (
              <p className="text-sm text-gray-500">
                {t("packConfig.willSelectMatieres", {
                  count: pack.tier === "silver" ? 4 : 2,
                })}
              </p>
            )}
          </div>
        )}

        {/* Step: Matiere Selection */}
        {configurator.step === "matieres" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-600">
                {configurator.validationMessage}
              </p>
              <div className="flex gap-3 text-xs">
                <span className="px-2 py-1 bg-blue-50 text-blue-700 rounded-full">
                  Langues: {configurator.currentLangues}/{configurator.maxLangues}
                </span>
                <span className="px-2 py-1 bg-purple-50 text-purple-700 rounded-full">
                  Specialites: {configurator.currentSpecialites}/
                  {configurator.maxSpecialites}
                </span>
              </div>
            </div>

            <MatiereSelector
              matieres={configurator.availableMatieres}
              selectedIds={configurator.selectedMatieres}
              onToggle={configurator.toggleMatiere}
              maxLangues={configurator.maxLangues}
              maxSpecialites={configurator.maxSpecialites}
            />
          </div>
        )}

        {/* Step: Confirmation */}
        {configurator.step === "confirm" && (
          <div className="space-y-4">
            <div className="bg-green-50 border border-green-200 rounded-2xl p-6">
              <div className="flex items-center gap-3 mb-3">
                <CheckCircle className="w-6 h-6 text-green-600" />
                <h3 className="font-semibold text-green-800">
                  {t("packConfig.confirmTitle")}
                </h3>
              </div>
              <div className="space-y-2 text-sm text-green-700">
                <p>
                  <span className="font-medium">{t("packConfig.pack")}:</span>{" "}
                  {TIER_LABELS[pack.tier]}
                </p>
                {pack.tier !== "golden" && (
                  <p>
                    <span className="font-medium">
                      {t("packConfig.matieres")}:
                    </span>{" "}
                    {configurator.selectedMatieres.length} selectionnees
                  </p>
                )}
                <p>
                  <span className="font-medium">{t("packConfig.price")}:</span>{" "}
                  {pack.prix_tnd} TND
                </p>
              </div>
            </div>

            <p className="text-xs text-gray-500">
              {t("packConfig.confirmDisclaimer")}
            </p>
          </div>
        )}

        {/* Step: Success */}
        {configurator.step === "success" && (
          <div className="text-center py-8 space-y-4">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
            <h3 className="text-lg font-semibold text-navy">
              {t("packConfig.successTitle")}
            </h3>
            <p className="text-sm text-gray-600">
              {t("packConfig.successDesc")}
            </p>
            <Button onClick={handleClose} variant="primary">
              {t("packConfig.goToDashboard")}
            </Button>
          </div>
        )}

        {/* Actions */}
        {configurator.step !== "success" && (
          <div className="flex items-center justify-between pt-4 border-t border-gray-100">
            {configurator.step !== "tier" ? (
              <Button
                onClick={configurator.goBack}
                variant="secondary"
                className="flex items-center gap-2"
              >
                <ArrowLeft className="w-4 h-4" />
                {t("common.back")}
              </Button>
            ) : (
              <div />
            )}

            <Button
              onClick={
                configurator.step === "confirm"
                  ? configurator.confirmPurchase
                  : () => {
                      if (configurator.step === "tier") {
                        configurator.selectPack(pack);
                      } else {
                        // Move to confirm step
                        // This is handled internally by the hook's canProceed
                      }
                    }
              }
              disabled={!configurator.canProceed || configurator.loading}
              variant="primary"
              className="flex items-center gap-2"
            >
              {configurator.loading && (
                <Loader2 className="w-4 h-4 animate-spin" />
              )}
              {configurator.step === "confirm"
                ? t("packConfig.confirmPurchase")
                : t("common.next")}
            </Button>
          </div>
        )}
      </div>
    </Modal>
  );
}
```

### 4.3 Composant : `MatiereSelector.tsx`

```typescript
// src/features/student/components/pack/MatiereSelector.tsx

import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { Check } from "lucide-react";

interface Matiere {
  id: number;
  name: string;
  category: "langue" | "specialite";
  niveau_scolaire: string;
}

interface MatiereSelectorProps {
  matieres: Matiere[];
  selectedIds: number[];
  onToggle: (id: number) => void;
  maxLangues: number;
  maxSpecialites: number;
}

export function MatiereSelector({
  matieres,
  selectedIds,
  onToggle,
  maxLangues,
  maxSpecialites,
}: MatiereSelectorProps) {
  const { t } = useTranslation();

  const langues = useMemo(
    () => matieres.filter((m) => m.category === "langue"),
    [matieres]
  );
  const specialites = useMemo(
    () => matieres.filter((m) => m.category === "specialite"),
    [matieres]
  );

  const selectedLangues = selectedIds.filter((id) =>
    langues.some((l) => l.id === id)
  ).length;
  const selectedSpecialites = selectedIds.filter((id) =>
    specialites.some((s) => s.id === id)
  ).length;

  const renderSection = (
    title: string,
    items: Matiere[],
    selectedCount: number,
    maxCount: number,
    category: "langue" | "specialite"
  ) => (
    <div>
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-sm font-semibold text-navy">{title}</h4>
        <span
          className={`text-xs px-2 py-0.5 rounded-full ${
            selectedCount === maxCount
              ? "bg-green-100 text-green-700"
              : "bg-gray-100 text-gray-600"
          }`}
        >
          {selectedCount}/{maxCount}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-2">
        {items.map((matiere) => {
          const isSelected = selectedIds.includes(matiere.id);
          const isDisabled =
            !isSelected &&
            ((category === "langue" && selectedCount >= maxLangues) ||
              (category === "specialite" && selectedSpecialites >= maxSpecialites));

          return (
            <button
              key={matiere.id}
              onClick={() => onToggle(matiere.id)}
              disabled={isDisabled}
              className={`flex items-center gap-2 p-3 rounded-xl border-2 text-left text-sm transition-all ${
                isSelected
                  ? "border-navy bg-navy/5 text-navy font-medium"
                  : isDisabled
                  ? "border-gray-100 bg-gray-50 text-gray-400 cursor-not-allowed"
                  : "border-gray-200 hover:border-navy/30 text-gray-700"
              }`}
            >
              <div
                className={`w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 ${
                  isSelected
                    ? "border-navy bg-navy"
                    : "border-gray-300"
                }`}
              >
                {isSelected && <Check className="w-3 h-3 text-white" />}
              </div>
              <span className="truncate">{matiere.name}</span>
            </button>
          );
        })}
      </div>
    </div>
  );

  return (
    <div className="space-y-5">
      {maxLangues > 0 &&
        renderSection(
          t("packConfig.langues"),
          langues,
          selectedLangues,
          maxLangues,
          "langue"
        )}
      {maxSpecialites > 0 &&
        renderSection(
          t("packConfig.specialites"),
          specialites,
          selectedSpecialites,
          maxSpecialites,
          "specialite"
        )}
    </div>
  );
}
```

### 4.4 Ajout API : `abonnementApi.ts`

```typescript
// Ajouter dans src/api/abonnementApi.ts

export const abonnementApi = {
  // ... endpoints existants ...

  /**
   * Récupère les matières disponibles pour un niveau scolaire donné.
   * Utilisé par le configurateur de pack pour afficher les grilles de sélection.
   */
  getAvailableMatieres: async (niveauScolaire: string): Promise<Matiere[]> => {
    const response = await api.get<Matiere[]>(
      `/api/pathway/matieres?niveau_scolaire=${encodeURIComponent(niveauScolaire)}`
    );
    return response;
  },

  /**
   * Achète un pack avec sélection de matières.
   * Pour Basic: 1 langue + 1 spécialité. Pour Silver: 2 langues + 2 spécialités.
   * Pour Golden: pas de matières requises.
   */
  purchasePack: async (
    packId: number,
    options?: { matieres?: number[] }
  ): Promise<{ message: string; abonnement_id: number }> => {
    const response = await api.post(`/api/abonnements/packs/${packId}/purchase`, {
      matieres: options?.matieres,
    });
    return response;
  },

  /**
   * Reconfigure les matières d'un pack au début d'un trimestre.
   * Disponible uniquement pendant les 15 premiers jours du trimestre.
   */
  reconfigureMatieres: async (
    abonnementId: number,
    newMatieres: number[]
  ): Promise<{ message: string; effective_date: string }> => {
    const response = await api.post(
      `/api/abonnements/${abonnementId}/reconfigure`,
      { matieres: newMatieres }
    );
    return response;
  },
};
```

---

## 5. RÉSUMÉ DES PRIORITÉS

| Priorité | Phase | Impact UX | Effort dev | Nb fichiers |
|----------|-------|-----------|------------|-------------|
| **P0** | Trigger Conversion (Quota) | Critique — tunnel de conversion cassé | Moyen | 4 |
| **P0** | Configurateur de Pack | Critique — premier achat impossible | Élevé | 6 |
| **P0** | Reconfiguration Trimestrielle | Critique — cycle trimestriel non respecté | Élevé | 6 |
| **P1** | Vérification Tier Soft Skills | Important — accès non contrôlé | Faible | 1 |
| **P1** | Espace Mes Formations | Important — suivi impossible | Moyen | 3 |
| **P1** | Jauge Quota Dashboard | Important — visibilité manquante | Faible | 2 |
| **P2** | Design System Migration | Moyen — cohérence UI | Élevé | 14 |
| **P2** | Landing Page | Moyen — vitrine publique | Moyen | 2 |
| **P2** | Historique Abonnement | Moyen — transparence | Faible | 1 |

---

## 6. FICHIERS À CRÉER (Checklist)

```
src/features/student/hooks/
  ├── useQuotaGuard.ts
  ├── usePackConfigurator.ts
  ├── useTrimesterReconfiguration.ts
  └── useMySoftSkills.ts

src/features/student/components/
  ├── quota/
  │   ├── QuotaExhaustedModal.tsx
  │   └── QuotaGauge.tsx
  ├── pack/
  │   ├── PackConfiguratorModal.tsx
  │   ├── MatiereSelector.tsx
  │   └── PackCard.tsx
  └── trimester/
      ├── TrimesterReconfigBanner.tsx
      └── TrimesterBadge.tsx

src/features/student/pages/
  ├── MatiereReconfigurationPage.tsx
  └── MySoftSkillsPage.tsx

src/pages/public/
  └── LandingPage.tsx
```

## 7. FICHIERS À MODIFIER (Checklist)

```
src/features/student/pages/
  ├── StudentDashboard.tsx       ← +QuotaGauge, +TrimesterBadge, +useQuotaGuard
  ├── PacksPage.tsx              ← +PackConfiguratorModal (remplace redirect)
  └── StudentPackPage.tsx        ← +TrimesterReconfigBanner

src/pages/learner/
  └── SoftSkillsCatalogPage.tsx  ← +vérification tier

src/api/
  └── abonnementApi.ts           ← +purchasePack(matieres), +reconfigureMatieres, +getAvailableMatieres

src/App.tsx                      ← +route /dashboard/my-skills, +route /dashboard/reconfigure-pack
src/components/layout/DashboardLayout.tsx ← +sidebar "Mes Formations"
```
