# Guide Utilisateur EDUAI Learning - Admin Pedagogique (Platform Curriculum Manager)

> **Version** : 1.0 — Aout 2026
> **Branche** : phase1-critical
> **Derniere mise a jour** : 06/08/2026

---

## Table des matieres

1. [Introduction au Role](#1-introduction-au-rle)
2. [Workflow de Moderation & Governance Globale](#2-workflow-de-modration--governance-globale)
3. [Gestion de la Bibliotheque Globale](#3-gestion-de-la-bibliothque-globale)
4. [CMS Versioning](#4-cms-versioning)
5. [Construction des Parcours Globaux & Tags ABAC](#5-construction-des-parcours-globaux--tags-abac)
6. [Rapport de Generation](#6-rapport-de-gnration)

---

## 1. Introduction au Role

### Qui est l'Admin Pedagogique ?

L'Admin Pedagogique (egalement appele **Platform Curriculum Manager**) est un role **global** (pas scope a une seule ecole) dont la mission principale est de garantir la **qualite pedagogique** du contenu distribue sur l'ensemble de la plateforme EDUAI Learning.

Ce role est defini dans le code backend comme `pedagogical_admin` et est autorise par la dependance `require_pedagogical_admin` (fichier `deps.py:121`).

### Perimetre d'action vs Super-Admin

| Capacite | Super-Admin | Admin Pedagogique |
|----------|-------------|-------------------|
| Validation B2B des cours | Oui | **Oui (exclusif)** |
| Gestion de l'arborescence | Oui | **Oui** |
| AI Factory | Oui | **Oui** |
| Bibliotheque globale | Oui | **Oui** |
| CMS Versioning | Oui | **Oui** |
| Tags ABAC | Oui | **Oui** |
| Gestion financiere/SaaS | **Oui** | Non |
| Impersonation | **Oui** | Non |
| Gestion des ecoles | **Oui** | Non |
| Mode maintenance | **Oui** | Non |
| Parametres plateforme | **Oui** | Non |

### Le Context Switcher

Si votre compte possede plusieurs roles (ex: `["pedagogical_admin", "admin_school"]`), un **dropdown de contexte** apparait dans la barre laterale. Selectionnez le role **"Admin Pedagogique"** pour activer les permissions pedagogiques globales.

**Important :** Le role `pedagogical_admin` est **global** — il ne necessite pas de `school_id` et donne un acces a toutes les ecoles.

---

## 2. Workflow de Moderation & Governance Globale

### La file d'attente de validation

**Chemin :** `Admin Panel` > `Review Pedago.`

> **Note :** C'est la seule page reservee exclusivement au role `pedagogical_admin`. Elle n'est visible que par ce role dans la barre laterale.

**Comment acceder :**
1. Cliquez sur **"Review Pedago."** dans la barre laterale
2. La page affiche tous les cours soumis pour validation pedagogique
3. Par defaut, le filtre est sur **"En attente de review"** (`pending_review`)

**Donnees affichees par cours :**
- **Titre** du cours
- **Badge de statut pedagogique** (code couleur) :
  - `Brouillon` (gris)
  - `En revue` (jaune) — en attente de votre validation
  - `Approuve` (bleu) — approuve pour la plateforme
  - `Approuve B2B` (vert) — autorise pour la distribution B2B
  - `Rejete` (rouge)
  - `Revision` (orange)
- **Badge de proprietaire** :
  - `Independant` (violet) — cours d'un enseignant independant
  - `Catalogue EDUAI` (bleu) — cours genere par l'IA
  - `Ecole` (gris) — cours d'une ecole
- **Description** du cours
- **Date de validation** (si applicable)

### Filtres disponibles

| Filtre | Description |
|--------|-------------|
| `En attente de review` | Cours avec statut `pending_review` (defaut) |
| `Tous les statuts` | Affiche tous les cours |
| `Approuves (Plateforme)` | Cours avec statut `approved_for_platform` |
| `Approuves (B2B)` | Cours avec statut `approved_for_b2b` |
| `Rejetes` | Cours avec statut `rejected` |
| `Revision demandee` | Cours avec statut `revision_requested` |

### Validation B2B : Le pouvoir exclusif

Seul l'Admin Pedagogique peut effectuer la **validation B2B** — c'est-dire autoriser un cours pour la distribution a travers le SaaS B2B (toutes les ecoles).

**Pour valider un cours :**
1. Selectionnez un cours avec le statut `pending_review`
2. Cliquez sur le bouton vert **"Approuver B2B"**
3. Un appel `PUT /api/pedagogical/courses/{course_id}/review` est effectue avec `action: "approved_for_b2b"`
4. Le cours passe en statut `approved_for_b2b`
5. Le cours devient accessible a toutes les ecoles via le catalogue B2B
6. Un toast de confirmation vert s'affiche : *"Cours approuve pour la distribution B2B"*

**Pour demander une revision :**
1. Selectionnez un cours avec le statut `pending_review`
2. Cliquez sur le bouton orange **"Demander revision"**
3. Un appel `PUT /api/pedagogical/courses/{course_id}/review` est effectue avec `action: "needs_revision"`
4. Le cours passe en statut `needs_revision`
5. L'enseignant sera notifie et pourra soumettre une nouvelle version

### Cycle de vie d'un contenu

```
draft → pending_review → approved_for_b2b → published
                     ↘ needs_revision → pending_review (resoumission)
                     ↘ approved_local (par pedagogical_lead uniquement)
```

| Statut | Description | Qui peut le mettre |
|--------|-------------|-------------------|
| `draft` | Brouillon, pas encore soumis | Auteur du cours |
| `pending_review` | Soumis pour review pedagogique | Auteur du cours |
| `approved_for_b2b` | Approuve pour distribution B2B | **Admin Pedagogique UNIQUEMENT** |
| `approved_local` | Approuve localement (une seule ecole) | Pedagogical Lead (scope ecole) |
| `needs_revision` | Revision demandee | Admin Pedagogique ou Pedagogical Lead |
| `published` | Publie et visible par les eleves | Systeme (apres validation) |
| `archived` | Archive, plus visible | Admin Pedagogique, Super-Admin, ou auteur |

**Transition interdite :** Un cours `approved_local` peut etre promu en `approved_for_b2b` par l'Admin Pedagogique, mais jamais l'inverse.

### Rapports de contenu IA

**Chemin :** `Admin Panel` > `Review Pedago.` > onglet Reports

Les utilisateurs peuvent signaler des reponses IA incorrectes. L'Admin Pedagogique gere ces signalements.

**Endpoints :**
- `GET /api/pedagogical/reports` : Liste les signalements (filtre par statut, defaut: `pending`)
- `PUT /api/pedagogical/reports/{report_id}/resolve` : Resoudre (`resolved`) ou rejeter (`dismissed`) un signalement

### Escalations pedagogiques

**Endpoints :**
- `GET /api/pedagogical/escalations` : Liste les escalades (filtre par statut, defaut: `pending`)
- `PUT /api/pedagogical/escalations/{escalation_id}/resolve` : Resoudre une escalade

Les escalades proviennent des Pedagogical Leads qui n'ont pas pu resoudre un cas localement.

### Couverture curriculaire

**Endpoint :** `GET /api/pedagogical/reports/curriculum-coverage`

Rapport montrant :
- Nombre de cours par categorie/niveau
- Nombre d'ecoles couvertes
- Uniquement les cours approuves

---

## 3. Gestion de la Bibliotheque Globale

### Les Elements Pedagogiques

**Chemin :** `Admin Panel` > `Arborescence` (pour l'arborescence) ou via API

Un element pedagogique (`ElementPedagogique`) est une unite de contenu reutilisable. Il peut etre de 5 types :

| Type | Description |
|------|-------------|
| `texte` | Contenu textuel (lecon, fiche, cours) |
| `video` | Video educative |
| `image` | Image pédagogique (schema, diagramme) |
| `quiz` | Quiz d'evaluation |
| `pdf` | Document PDF |

**Champs cles d'un element :**

| Champ | Description |
|-------|-------------|
| `titre` | Titre de l'element |
| `type` | `texte`, `video`, `image`, `quiz`, `pdf` |
| `statut` | `brouillon`, `en_review`, `publie`, `rejete`, `brouillon_ia` |
| `difficulte` | `basique`, `moyen`, `difficile` |
| `est_global` | `true` = dans la bibliotheque globale |
| `est_libre` | `true` = element independant (pas lie a une lecon) |
| `auteur_id` | ID de l'auteur |

### Workflow de validation des elements

```
brouillon → en_review → publie → brouillon (retour en edition)
                   ↘ rejete → en_review (resoumission)
```

**Statut special : `brouillon_ia`**

Les elements generes par l'AI Factory demarrent avec le statut `brouillon_ia` (pas le standard `brouillon`). Ce statut signifie que l'element a ete genere par l'IA et attend une **validation humaine** avant de pouvoir entrer dans le workflow standard.

**Pour valider un element :**
1. Trouvez l'element en statut `en_review`
2. Appelez `POST /api/pathway/elements/{element_id}/validate`
3. L'element passe en statut `publie`
4. Si `est_global = true`, il apparait dans la bibliotheque globale

**Pour rejeter un element :**
1. Trouvez l'element en statut `en_review`
2. Appelez `POST /api/pathway/elements/{element_id}/reject` avec un commentaire
3. L'element passe en statut `rejete`
4. L'auteur peut le corriger et le resoumettre

### Atomisation : Comment l'IA separe les lecons

Lorsqu'un cours est publie via l'AI Factory, la fonction `_create_atomized_elements()` (fichier `ai_factory_service.py:521`) cree automatiquement **4 elements pedagogiques** par lecon :

| Element | Type | Contenu |
|---------|------|---------|
| Element Texte | `texte` | Le contenu textuel de la lecon |
| Element Quiz | `quiz` | Les questions du quiz d'evaluation |
| Element Image | `image` | Le prompt DALL-E pour generer l'image |
| Element Video | `video` | La description de la scene video |

**Tous ces elements sont crees avec :**
- `statut = "brouillon_ia"` (en attente de validation)
- `est_global = false` (pas encore dans la bibliotheque globale)
- `difficulte = "moyen"` (defaut)
- `metadonnees = {"source": "ai_factory", "course_title": ..., "generated_at": ...}`

### Reference vs Duplication

Les enseignants peuvent utiliser les elements de la bibliotheque globale dans leurs cours privés de deux manieres :

1. **Reference** : L'element est lie a la lecon sans etre copie. Si l'element est mis a jour dans la bibliotheque, le changement se propage.

2. **Duplication** : L'element est copie dans le cours prive de l'enseignant. Les modifications locales n'affectent pas la bibliotheque globale.

**Pour promouvoir un element vers la bibliotheque globale :**
1. L'element doit etre en statut `publie`
2. Appelez `POST /api/pathway/elements/{element_id}/promote-global`
3. `est_global` passe a `true`
4. Un snapshot `ContentPromotion` est cree pour tracer l'historique

### Recherche dans la bibliotheque

**Endpoint :** `GET /api/bibliotheque/search`

Parametres de recherche :
- `q` : Texte de recherche (titre)
- `type` : Filtre par type (`texte`, `video`, `image`, `quiz`, `pdf`)
- `matiere` : Filtre par matiere
- `niveau_scolaire` : Filtre par niveau
- `difficulte` : Filtre par difficulte (`basique`, `moyen`, `difficile`)
- `est_global` : Filtre les elements globaux uniquement

Seuls les elements avec `statut="publie"` sont retournes.

### Competences

**Endpoints :**
- `GET /api/bibliotheque/competences` : Liste les competences (filtres: `matiere`, `niveau_scolaire`)
- `POST /api/bibliotheque/competences` : Creer une competence (nom unique)
- `DELETE /api/bibliotheque/competences/{id}` : Supprimer une competence

---

## 4. CMS Versioning

### Fork de Cursus

Le systeme de versioning permet de creer des versions successives d'un cours sans ecraser le contenu existant.

**Chemin :** `Admin Panel` > `Courses` > [Selectionner un cours] > `Creer une nouvelle version`

**Comment creer une nouvelle version :**
1. Selectionnez un cours existant
2. Cliquez sur **"Creer une nouvelle version"**
3. Un appel `POST /api/courses/{course_id}/create-draft-version` est effectue
4. Le systeme effectue un **deep copy** du cours :
   - Copie du cours principal
   - Copie de tous les modules
   - Copie de toutes les lecons de chaque module
5. La nouvelle version recoit :
   - `version_number` = version_precedente + 1
   - `title` = "{titre_original} (V{N})"
   - `status` = `"draft"`
   - `is_active_version` = `false`
   - `pedagogical_status` = `"draft"`
   - `visibility` = `"private"`
6. La version originale reste active (`is_active_version = true`)

### Impact sur les eleves : V1 et V2

**Principe fondamental :** Les eleves en cours continuent la V1, les nouveaux eleves commencent la V2.

**Exemple concret :**
- Cours "Mathematiques 3eme" (V1) — publie en septembre
- 150 eleves sont inscrits et avancent dans le cours V1
- En janvier, l'Admin Pedagogique cree une V2 avec du contenu mis a jour
- **Les 150 eleves continuent la V1** (pas d'interruption)
- **Les nouveaux eleves de janvier commencent la V2**
- La V1 reste active tant que des eleves la suivent

### Publication d'une version

**Endpoint :** `POST /api/courses/{course_id}/publish-version`

**Logique de publication :**
1. Le systeme trouve toutes les versions avec le meme titre de base
2. **Toutes les anciennes versions actives sont desactivees** :
   - `is_active_version = false`
   - `status = "archived"`
3. La nouvelle version est activee :
   - `is_active_version = true`
   - `status = "published"`
   - `pedagogical_status = "approved_local"`
   - `published_at` = date actuelle
4. Les eleves qui commencent le cours apres cette date verront la nouvelle version

### Rollback

**Endpoint :** `POST /api/courses/{course_id}/rollback/{target_version_id}`

**Comment revenir a une version precedente :**
1. Allez dans la liste des versions du cours
2. Selectionnez la version cible (ex: V1)
3. Cliquez sur **"Rollback vers cette version"**
4. Le systeme :
   - Desactive la version actuelle (`is_active_version = false`, `status = "archived"`)
   - Reactive la version cible (`is_active_version = true`, `status = "published"`)
5. Les nouveaux eleves verront desormais la version restauree

### Consultation des versions

**Endpoint :** `GET /api/courses/{course_id}/versions`

Retourne la liste de toutes les versions avec :
- `version_number` : Numero de version
- `is_active_version` : Version actuellement active
- `status` : Statut du cours
- `pedagogical_status` : Statut pedagogique
- `created_at` / `updated_at` : Dates de creation/modification

---

## 5. Construction des Parcours Globaux & Tags ABAC

### Arborescence officielle

**Chemin :** `Admin Panel` > `Arborescence`

L'arborescence suit la structure officielle du systeme educatif tunisien :

```
Niveau d'etude (20 niveaux)
  └── Matiere (235 matieres : 100 langues + 135 specialites)
        └── Chapitre (ChapterPathway)
              └── Notion (Notion)
                    └── Contenu (ContenuNotion)
```

**Niveaux d'etude disponibles :**

| Cycle | Niveaux |
|-------|---------|
| **Base** | 7eme, 8eme, 9eme Annee Base |
| **Secondaire** | 1ere Annee Secondaire, 2eme Lettres/Sciences/Technologie/Economie, 3eme Lettres/Mathematiques/Sciences Exp./Economie/Info/Techniques |
| **Bac** | Bac Lettres, Bac Mathematiques, Bac Sciences Exp., Bac Economie, Bac Info |

**Matieres par type :**

| Type | Exemples | Nombre |
|------|----------|--------|
| **Langues** (`type_matiere='langue'`) | العربية, الفرنسية, الانقليزية, الإسبانية, الألمانية | 5 par niveau |
| **Specialites** (`type_matiere='specialite'`) | رياضيات, علوم طبيعية, تاريخ / جغرافيا, فلسفة... | Variable par filiere |

### Builder de Parcours

**Pour creer un parcours :**
1. Allez dans `Admin Panel` > `Arborescence`
2. Selectionnez un **niveau d'etude** (ex: 9eme Annee Base)
3. Selectionnez une **matiere** (ex: رياضيات)
4. Cliquez sur **"Ajouter un chapitre"**
5. Entrez le nom du chapitre (ex: "Les fractions")
6. Pour chaque chapitre, ajoutez des **notions** (ex: "Definition", "Addition", "Multiplication")
7. Pour chaque notion, ajoutez des **contenus** avec le type d'assimilation :
   - `remediation` : Pour les eleves en difficulte
   - `standard` : Niveau standard
   - `avance` : Pour les eleves avances

**Types de contenu disponibles :**
- `video` : Video educative
- `fiche` : Fiche de revision
- `quiz` : Quiz d'evaluation
- `banque_exercices` : Banque d'exercices
- `evaluation_ia` : Evaluation par IA

### Configuration des seuils par matiere

**Chemin :** `Admin Panel` > `Seuils Config`

Chaque matiere a 3 seuils qui determinent le niveau d'assimilation de l'eleve :

| Seuil | Description | Defaut |
|-------|-------------|--------|
| `remediation_threshold` | En dessous de ce score, l'eleve a besoin de remediation | 40% |
| `standard_threshold` | Au-dessus de ce score, l'eleve est au niveau standard | 75% |
| `avance_threshold` | Au-dessus de ce score, l'eleve est au niveau avance | 75% |

**Pour modifier les seuils :**
1. Allez dans `Admin Panel` > `Seuils Config`
2. Selectionnez une matiere
3. Modifiez les valeurs des seuils
4. Enregistrez

### Tags Pack_Requis (ABAC)

Le systeme ABAC (Attribute-Based Access Control) determine quel pack d'abonnement est requis pour acceder a un cours.

**Tags disponibles :**

| Tag | Pack requis | Acces |
|-----|-------------|-------|
| `Basic` | Basique, Silver, ou Golden | Cours de base |
| `Silver` | Silver ou Golden uniquement | Contenu premium |
| `Golden` | Golden uniquement | Contenu exclusif |

**Comment taguer un cours :**
1. Selectionnez un cours
2. Definissez le champ `tag_pack_requis`
3. Les eleves sans le pack requis verront une **modale Upsell** leur proposant de souscrire

**Exemple :**
- Cours "Introduction a la programmation" → tag `Basic`
- Cours "Algorithmique avancee" → tag `Silver`
- Cours "Projets personnalises" → tag `Golden`

**Fonctionnement de la verification ABAC (`check_abac_access`) :**

```
1. Le cours est-il gratuit ? → Acces accorde
2. L'utilisateur est-il l'auteur ? → Acces accorde
3. A-t-il une inscription active ? → Acces accorde
4. A-t-il achete le cours ? → Acces accorde
5. Son ecole a-t-elle acces ? → Acces accorde
6. Son pack personnel correspond-il ? → Acces accorde
7. Son pack ecole correspond-il ? → Acces accorde
8. Son abonnement (tier) est-il suffisant ? → Acces accorde
9. Sinon → Acces refuse (HTTP 402 + Upsell)
```

### Gestion des Specialites Pedagogiques

**Chemin :** `Admin Panel` > `Specialites Pedago.`

**Pour creer une specialite :**
1. Allez dans `Admin Panel` > `Specialites Pedago.`
2. Cliquez sur **"Creer une specialite"**
3. Remplissez :
   - **Nom** de la specialite
   - **Cycle scolaire** (Base, Secondaire, Bac)
   - **Matieres associees** (selection multiple)
4. Enregistrez

**Pour assigner un responsable pedagogique :**
1. Selectionnez une specialite
2. Cliquez sur **"Assigner un responsable"**
3. Selectionnez l'enseignant (`user_id`)
4. Selectionnez les niveaux d'etude couverts
5. Enregistrez

Le responsable pedagogique pourra ensuite valider les contenus de sa specialite.

---

## 6. Rapport de Generation

**Partie Admin Pedagogique (Platform Curriculum Manager) : COMPLETE**

Le document couvre :
- Introduction au role avec distinction Super-Admin vs Admin Pedagogique
- Workflow de moderation complet (file d'attente, validation B2B, cycle de vie)
- Bibliotheque globale (elements pedagogiques, atomisation, reference vs duplication)
- CMS Versioning (fork, impact eleves V1/V2, rollback)
- Parcours globaux (arborescence officielle tunisienne, builder, tags ABAC)
- Gestion des seuils et specialites pedagogiques

**Fonctionnalites cles documentees :**
- Page exclusive `Review Pedago.` (reseree au `pedagogical_admin`)
- Validation B2B exclusive (seul le pedagogical_admin peut approuver)
- AI Factory (4 etapes : Topic → Plan → Generate → Preview)
- 20 niveaux d'etude, 235 matieres (100 langues + 135 specialites)
- Systeme ABAC avec 3 tiers (Basic/Silver/Golden)
- Workflow complet des elements (brouillon → en_review → publie)

**Pret pour le role suivant : Leader Pedagogique (Pedagogical Lead)**
