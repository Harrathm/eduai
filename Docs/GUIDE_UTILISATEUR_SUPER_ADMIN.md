# Guide Utilisateur EDUAI Learning - Super-Admin (Platform Owner)

> **Version** : 1.0 — Aout 2026
> **Branche** : phase1-critical
> **Derniere mise a jour** : 06/08/2026

---

## Table des matieres

1. [Introduction au Role](#1-introduction-au-rle)
2. [Gestion du SaaS et des Tenants](#2-gestion-du-saas-et-des-tenants)
3. [Gestion Financiere et Monetisation](#3-gestion-financire-et-monetisation)
4. [Gestion Pedagogique Globale](#4-gestion-pdagogique-globale)
5. [Gestion des Utilisateurs et RBAC](#5-gestion-des-utilisateurs-et-rbac)
6. [Parametres de la Plateforme](#6-paramtres-de-la-plateforme)

---

## 1. Introduction au Role

### Qui est le Super-Admin ?

Le Super-Admin (egalement appele **Platform Owner**) est le role le plus eleve de la hierarchie EDUAI Learning. Il a un acces **global** a l'ensemble des donnees et fonctionnalites de la plateforme, sans restriction de tenant (ecole).

### Perimetre d'action

| Aspect | Super-Admin | Admin Ecole | Pedagogical Admin |
|--------|-------------|-------------|-------------------|
| Visibilite des donnees | **Global** (toutes les ecoles) | Scope ecole uniquement | **Global** (pedagogie) |
| Gestion des packs | Creer/Modifier/Supprimer | Lecture seule | Lecture seule |
| Gestion des utilisateurs | Tous les roles | Users de son ecole | Users pedagogiques |
| Settings plateforme | **Lecture/Ecriture** | Lecture seule | Lecture seule |
| Impersonation | **Oui** | Non | Non |
| Mode maintenance | **Oui** | Non | Non |

### Le Context Switcher

Si votre compte possede **plusieurs roles** (ex: `["super_admin", "pedagogical_admin"]`), un **dropdown de contexte** apparait dans la barre laterale. Il permet de basculer entre vos roles sans se deconnecter.

**Comment ca marche :**
1. Le dropdown affiche tous les roles assigns a votre compte
2. En cliquant sur un role, un appel `POST /auth/switch-context` est effectue
3. Un nouveau JWT est emis avec le `active_role` mis a jour
4. La navigation et les permissions s'adaptent immediatement au role selectionne

### Le mode Impersonation

Le Super-Admin peut **impersonner** n'importe quel utilisateur de la plateforme pour le support technique ou le debogage.

**Comment l'activer :**
1. Allez dans **Gestion des Utilisateurs** (`/dashboard/admin/users`)
2. Trouvez l'utilisateur cible dans la table
3. Cliquez sur l'action **Impersonate** (icone de masque)
4. Un appel `POST /auth/impersonate/{target_user_id}` est effectue
5. Vous etes desormais connecte en tant que cet utilisateur

**Indicateurs visuels :**
- Une **banniere rouge** s'affiche en haut de l'ecran avec le message : *"Vous impersonnez [Nom de l'utilisateur]"*
- Un bouton **"Arrêter l'impersonation"** permet de revenir a votre session admin
- Un **Audit Log** enregistre toutes les actions effectuees pendant l'impersonation

**Comment arreter :**
- Cliquez sur **"Arrêter l'impersonation"** dans la banniere rouge
- Un appel `POST /auth/impersonate/stop` est effectue
- Vous recuperez votre token admin et la page se recharge

---

## 2. Gestion du SaaS et des Tenants (Ecoles B2B)

### Creation d'une ecole

**Chemin :** `Admin Panel` > `Schools` > `+ Creer une ecole`

**Etapes :**
1. Cliquez sur le bouton **"+ Creer une ecole"** en haut a droite
2. Remplissez le formulaire :
   - **Nom de l'ecole** (obligatoire)
   - **Slug** (gener automatiquement a partir du nom, unique)
   - **Domaine** (ex: `lycee-tunis.tn`)
   - **Type d'ecole** : `real`, `demo`, ou `individual`
   - **Tier d'abonnement** : `free`, `teacher_pro`, `school`, ou `institution`
   - **Utilisateurs max** (defaut: 10)
   - **Logo URL** (optionnel)
   - **Couleur principale** (defaut: `#FF6B35`)
3. Cliquez sur **"Creer"**

**Apres creation :**
- Un **code d'invitation** est genere automatiquement (format unique)
- L'ecole est en attente de validation (`pending_validation = True`)
- Le Super-Admin doit approuver l'ecole via le bouton **"Approuver"**

### Gestion des abonnements des ecoles

**Chemin :** `Admin Panel` > `Schools` > [Selectionner une ecole]

Les tiers d'abonnement d'ecole sont :

| Tier | Description | Capacites |
|------|-------------|-----------|
| `free` | Gratuit | Fonctionnalites de base |
| `teacher_pro` | Enseignant Pro | Acces aux outils IA avances |
| `school` | Ecole | Gestion multi-classes + analytics |
| `institution` | Institution | Toutes les fonctionnalites + support dedie |

**Pour modifier l'abonnement d'une ecole :**
1. Selectionnez l'ecole dans la liste
2. Cliquez sur **"Modifier"**
3. Changez le `subscription_tier`
4. Definissez la date d'expiration (`subscription_expires_at`)
5. Enregistrez

### Gestion des codes d'invitation

**Chemin :** `Admin Panel` > `Invite Codes`

**Fonctionnalites :**
- **Liste des codes** : Tableau montrant chaque ecole avec son code d'invitation
- **Copier** : Copie le code dans le presse-papier (format: `EDUAI-XXXXX`)
- **Regenerer** : Cree un nouveau code (l'ancien est invalide)

**Pour regenerer un code :**
1. Selectionnez l'ecole dans la table
2. Cliquez sur **"Regenerer"**
3. Confirmez l'action
4. L'ancien code est desactive, le nouveau est affiche

**Comment les eleves/enseignants utilisent le code :**
1. Sur la page d'inscription, selectionnez "Rejoindre une ecole"
2. Entrez le code d'invitation
3. Le compte est lie a l'ecole automatiquement

---

## 3. Gestion Financiere et Monetisation

### Packs et Tarification

**Chemin :** `Admin Panel` > `Finance` > `Packs`

**Structure d'un PackDefinition :**

| Champ | Description | Exemple |
|-------|-------------|---------|
| `nom` | Nom du pack | "Pack Basique 9eme" |
| `description` | Description detailssee | "Acces a 2 matieres au choix" |
| `tier` | Niveau : `gratuit`, `basique`, `silver`, `golden` | `basique` |
| `niveau_scolaire` | Niveau scolaire tunisien | `9eme de base` |
| `matieres` | JSON des matieres couvertes | `["العربية", "رياضيات"]` |
| `prix_tnd` | Prix en Dinars Tunisiens | `19.99` |
| `features` | Fonctionnalites incluses | `["Acces IA", "Quiz"]` |
| `est_actif` | Actif/Inactif | `true` |

**Pour creer un pack :**
1. Allez dans `Admin Panel` > `Finance`
2. Cliquez sur **"+ Creer un pack"**
3. Remplissez les champs
4. Definissez les matieres (pour `basique` : 1 langue + 1 specialite, pour `silver` : 2 langues + 2 specialites)
5. Pour `golden` : acces illimite (pas de matieres a selectionner)
6. Enregistrez

**Hierarchie des tiers :**

```
gratuit (0) < basique (1) < silver (2) < golden (3)
```

- **Upgrade** : prise d'effet immediate
- **Downgrade** : reporte au prochain trimestre scolaire

**Calendrier des trimestres (Tunisie) :**
- **T1** : 15 Septembre — 19 Decembre
- **T2** : 5 Janvier — 27 Mars
- **T3** : 6 Avril — 19 Juin

### Bulk Seats (Licences en gros)

**Chemin :** `Admin Panel` > `Finance` > `Bulk Seats`

Les Bulk Seats permettent aux ecoles d'acheter des **places en gros** pour des formations specifiques (categorief: `Teacher_Training`).

**Comment acheter des Bulk Seats :**
1. Allez dans `Admin Panel` > `Finance` > `Bulk Seats`
2. Cliquez sur **"Acheter des vouchers"**
3. Selectionnez la formation (doit etre de type `Teacher_Training`)
4. Definissez la quantite
5. Confirmez l'achat

**Generation des codes :**
- Chaque voucher recoit un code unique au format : `BULK-XXXX-YYYY`
- Les codes sont affiches dans la table des Bulk Seats

**Redemption d'un code :**
1. L'enseignant/eleve va sur la page de la formation
2. Il entre le code Bulk Seat
3. Il est inscrit automatiquement a la formation
4. Le voucher passe en statut `consumed`

**Tableau des Vouchers :**

| Champ | Description |
|-------|-------------|
| `code` | Code unique du voucher |
| `formation` | Formation associee |
| `status` | `unused` ou `consumed` |
| `consumed_by` | Utilisateur qui a utilise le voucher |
| `created_at` | Date de creation |

### Revenue Share

**Chemin :** `Admin Panel` > `Finance` > `Revenue Share`

Le systeme de Revenue Share retribue les **Teacher Partners** (enseignants avec `is_partner = True`) en fonction de la consommation IA de leurs cours.

**Fonctionnement :**
1. Un cron job mensuel (`calculate_monthly_teacher_revenue`) tourne le 1er de chaque mois a 02h00
2. Pour chaque cours d'un Teacher Partner, le systeme compte le nombre d'eleves premium qui ont utilise le cours
3. Le calcul : `nombre_eleves_premium * 0.05 TND` par cours par mois
4. Les revenus sont enregistres dans le `teacher_revenue_ledger`

**Tableau `teacher_revenue_ledger` :**

| Champ | Description |
|-------|-------------|
| `teacher_id` | Enseignant partenaire |
| `lesson_id` | Lecon concernee |
| `consumption_count` | Nombre de consommations IA |
| `revenue_amount` | Montant des revenus (TND) |
| `period_month` | Mois de la periode |

**Pour consulter les revenus :**
1. Allez dans `Admin Panel` > `Finance` > `Revenue Share`
2. Selectionnez l'enseignant
3. Consultez le rapport mensuel avec le detail par lecon

**Endpoints disponibles :**
- `GET /api/teacher/revenue-report` : Rapport mensuel detaille
- `GET /api/teacher/revenue-history` : Historique sur N mois (defaut: 6)

### Wallet et Credits

**Chemin :** `Admin Panel` > `Finance` > `Wallets`

**Pools de credits :**

| Pool | Description |
|------|-------------|
| `trial` | Credits d'essai gratuit |
| `dt_purchased` | DT achetes (argent reel) |
| `school_allocated` | Credits alloues par l'ecole |
| `purchased` | Credits achetes par l'eleve |

**Pour gerer les wallets :**
1. Allez dans `Admin Panel` > `Finance` > `Wallets`
2. Selectionnez un utilisateur
3. Actions disponibles :
   - **Ajouter des credits** : DT ou tokens
   - **Deduire des credits** : Avec motif obligatoire
   - **Consulter l'historique** : Toutes les transactions

**Operations :**
- `POST /api/admin/wallets/{user_id}/add` : Ajouter des credits
- `POST /api/admin/wallets/{user_id}/deduct` : Deduire des credits
- `GET /api/admin/wallets` : Lister tous les wallets

---

## 4. Gestion Pedagogique Globale

### AI Factory

**Chemin :** `Admin Panel` > `AI Factory`

L'AI Factory est un generateur de contenu pedagogique assiste par intelligence artificielle. Il genere automatiquement des cours complets a partir d'un sujet.

**Processus en 4 etapes :**

#### Etape 1 : Generer un plan
1. Entrez le **sujet** du cours (ex: "La Photosynthese")
2. Selectionnez si vous voulez utiliser le **RAG** (contexte de la bibliotheque)
3. Cliquez sur **"Generer le plan"**
4. L'IA genere une structure JSON avec modules et lecons

**Exemple de plan genere :**
```json
{
  "title": "La Photosynthese",
  "modules": [
    {
      "title": "Introduction a la photosynthese",
      "lessons": [
        {"title": "Definition et importance", "type": "texte"},
        {"title": "Les reactifs et produits", "type": "texte"}
      ]
    }
  ]
}
```

#### Etape 2 : Editer le plan
- Modifiez les titres, ajoutez/supprimez des modules ou lecons
- Reorganisez l'ordre si necessaire
- Cliquez sur **"Valider le plan"**

#### Etape 3 : Generer le contenu
- L'IA genere le contenu de chaque lecon (texte detaille)
- Un quiz de 5 questions est genere pour chaque lecon
- Des prompts d'images (DALL-E) et de video sont crees
- Cliquez sur **"Generer le contenu"**

#### Etape 4 : Publier
- Preview du cours complet
- Cliquez sur **"Publier dans la bibliotheque"**
- Le cours est cree avec le statut `brouillon_ia` (en attente de validation humaine)

**Publication automatique (`publish_course`) :**
Le systeme cree automatiquement :
- `Course` (cours principal)
- `Module` (modules du cours)
- `Lesson` (lecons de chaque module)
- `Quiz` + `QuizQuestion` + `QuizOption` (quiz d'evaluation)
- `ElementPedagogique` (elements atomises pour la bibliotheque, statut: `brouillon_ia`)

### Bibliotheque Globale

**Chemin :** `Admin Panel` > `Review Pedago.`

La bibliotheque globale contient tous les elements pedagogiques (`ElementPedagogique`) generes par l'IA ou soumis par les enseignants.

**Workflow de validation :**

```
brouillon_ia → en_review → publie (ou rejete)
```

**Pour valider un element :**
1. Allez dans `Admin Panel` > `Review Pedago.`
2. Filtrez par statut : `en_review`
3. Selectionnez un element
4. Cliquez sur **"Approuver"** ou **"Rejeter"**
5. L'element passe en statut `publie` et devient disponible dans le catalogue

**Pour soumettre un element (enseignant) :**
1. L'enseignant cree un element pedagogique
2. Il le soumet pour review (`POST /api/pathway/elements/{id}/submit`)
3. L'element passe en statut `en_review`
4. Le Pedagogical Admin ou Super-Admin le valide

### CMS Versioning

**Chemin :** `Admin Panel` > `Courses` > [Selectionner un cours] > `Versions`

Le systeme de versioning permet de creer des versions successives d'un cours sans ecraser le contenu existant.

**Comment creer une nouvelle version :**
1. Selectionnez un cours existant
2. Cliquez sur **"Creer une nouvelle version"**
3. Une copie du cours est creee avec `version_number` incrementee
4. La version precedente reste accessible (`is_active_version = True`)
5. Modifiez le contenu de la nouvelle version
6. Cliquez sur **"Publier"** pour activer la nouvelle version

**Fonctionnalites :**
- `create-draft-version` : Cree une copie modifiable
- `publish-version` : Active la nouvelle version (desactive les autres)
- `rollback` : Revient a la version precedente
- `versions` : Liste toutes les versions d'un cours

**Champs du modele :**
- `version_number` : Numero de version (commence a 1)
- `is_active_version` : Version actuellement visible par les eleves
- `category_cible` : `Scolaire`, `Teacher_Training`, `Soft_Skills`
- `tag_pack_requis` : Tier ABAC requis (`Basic`, `Silver`, `Golden`)

### Parcours Globaux

**Chemin :** `Admin Panel` > `Arborescence`

Les parcours globaux suivent l'arborescence officielle tunisienne :

```
Niveau d'etude → Matiere → Chapitre → Lecon → Element Pedagogique
```

**Arborescence officielle (exemple 9eme Annee Base) :**

| Type | Matieres |
|------|----------|
| **Langues** (type_matiere='langue') | العربية, الفرنسية, الانقليزية, الإسبانية, الألمانية |
| **Specialites** (type_matiere='specialite') | تاريخ / جغرافيا, تفكير إسلامي, تربية مدنية, رياضيات, علوم طبيعية, علوم فيزيائية, تكنولوجيا, إعلامية, تربية تشكilique, تربية موسيقique |

**Pour gerer l'arborescence :**
1. Allez dans `Admin Panel` > `Arborescence`
2. Niveaux d'etude : 20 niveaux (7eme Base a Bac)
3. Matieres : 235 matieres (100 langues + 135 specialites)
4. Ajoutez/supprimez des chapitres et lecons
5. Configurez les seuils par matiere (`remediation_threshold`, `standard_threshold`, `avance_threshold`)

**Tags ABAC :**
- `Basic` : Cours accessibles aux packs Basique et superieurs
- `Silver` : Cours accessibles aux packs Silver et Golden uniquement
- `Golden` : Cours accessibles uniquement aux packs Golden

---

## 5. Gestion des Utilisateurs et RBAC

### Creation d'utilisateurs

**Chemin :** `Admin Panel` > `Users` > `+ Creer un utilisateur`

**Etapes :**
1. Cliquez sur **"+ Creer un utilisateur"**
2. Remplissez le formulaire :
   - **Email** (obligatoire, unique par ecole)
   - **Mot de passe** (obligatoire)
   - **Nom complet**
   - **Role** : `student`, `teacher`, `admin_school`, `pedagogical_admin`, `pedagogical_lead`, `super_admin`, `parent`
   - **Ecole** (optionnel, pour les roles lies a une ecole)
3. Cliquez sur **"Creer"**

### Import CSV en masse

**Chemin :** `Admin Panel` > `Users` > `+ Import CSV`

**Format CSV attendu :**
```
email,full_name,role,password
eleve1@lycee.tn,Ahmed Ben Ali,student,motdepasse123
enseignant@lycee.tn,Sara Ben Ahmed,teacher,motdepasse123
```

**Etapes :**
1. Cliquez sur **"Importer CSV"**
2. Collez le contenu CSV ou chargez un fichier
3. Cliquez sur **"Importer"**
4. Le systeme affiche le resultat : nombre crees, erreurs detaillees

### Gestion du multi-roles

**Chemin :** `Admin Panel` > `Users` > [Selectionner un utilisateur] > `Modifier`

Un utilisateur peut avoir **plusieurs roles** simultanement via le champ `roles` (JSON array).

**Exemple :**
```json
{
  "roles": ["admin_school", "pedagogical_lead"],
  "active_context_role": "admin_school"
}
```

**Comment assigner plusieurs roles :**
1. Selectionnez l'utilisateur
2. Cliquez sur **"Modifier"**
3. Dans le champ **"Roles"**, selectionnez les roles desires
4. Definissez le **role actif par defaut** (`active_context_role`)
5. Enregistrez

**Roles disponibles :**

| Role | Description | Portee |
|------|-------------|--------|
| `super_admin` | Administrateur plateforme | Global |
| `admin_school` | Administrateur d'ecole | Scope ecole |
| `pedagogical_admin` | Admin pedagogique | Global (pedagogie) |
| `pedagogical_lead` | Responsable pedagogique | Scope ecole |
| `teacher` | Enseignant | Scope ecole |
| `student` | Eleve | Scope ecole |
| `parent` | Parent d'eleve | Scope famille |

### Mode Impersonation (Support Technique)

**Chemin :** `Admin Panel` > `Users` > [Selectionner un utilisateur] > `Impersonate`

**Processus complet :**
1. Le Super-Admin clique sur **"Impersonate"** pour un utilisateur
2. Un appel `POST /auth/impersonate/{target_user_id}` est effectue
3. Un enregistrement `AuditImpersonation` est cree :
   ```json
   {
     "support_user_id": 1,
     "target_user_id": 42,
     "started_at": "2026-08-06T12:00:00Z",
     "ip_address": "192.168.1.100"
   }
   ```
4. Un nouveau JWT est emis avec le claim `impersonated_by: 1`
5. La banniere rouge s'affiche avec le nom de l'utilisateur impersonne
6. Toutes les actions sont enregistrees dans l'Audit Log

**Pour arreter :**
1. Cliquez sur **"Arrêter l'impersonation"** dans la banniere rouge
2. Un appel `POST /auth/impersonate/stop` est effectue
3. Le JWT original du Super-Admin est restaure
4. La page se recharge automatiquement

---

## 6. Parametres de la Plateforme

**Chemin :** `Admin Panel` > `Settings`

### Configuration des cles d'API IA

**Onglet :** `AI Providers`

**Fournisseurs supportes :**

| Fournisseur | Usage | Configuration |
|-------------|-------|---------------|
| **Groq** | LLM principal (Llama 3.3 70B) | Cle API |
| **OpenAI** | DALL-E (generation d'images) | Cle API |
| **NVIDIA** | Modele alternatif | Cle API + Endpoint |
| **OpenRouter** | Modele alternatif | Cle API |
| **Anthropic** | Modele alternatif | Cle API |
| **MiniMax** | Modele alternatif | Cle API |

**Pour configurer un fournisseur :**
1. Allez dans `Admin Panel` > `Settings` > `AI Providers`
2. Selectionnez le fournisseur
3. Entrez la **cle API**
4. Cliquez sur **"Tester la connexion"**
5. Si le test reussit, enregistrez

**Test de connexion :**
- Endpoint : `POST /api/admin/settings/test-provider`
- Verifie que la cle API est valide et que le modele repond

### Configuration des limites de tokens

**Onglet :** `Token Limits`

**Par role :**

| Role | Tokens/jour (defaut) |
|------|---------------------|
| `student` | 1000 |
| `teacher` | 5000 |
| `admin_school` | 10000 |
| `super_admin` | Illimite |

**Pour modifier :**
1. Allez dans `Admin Panel` > `Settings` > `Token Limits`
2. Modifiez les limites par role
3. Enregistrez
4. Cliquez sur **"Vider le cache"** pour appliquer immediatement

### Mode Maintenance

**Onglet :** `Maintenance`

**Interrupteurs disponibles :**

| Parametre | Description |
|-----------|-------------|
| `maintenance_mode` | Active le mode maintenance global |
| `allow_teacher_registration` | Autorise l'auto-inscription des enseignants |
| `allow_new_signups` | Autorise les nouvelles inscriptions |

**Pour activer le mode maintenance :**
1. Allez dans `Admin Panel` > `Settings` > `Maintenance`
2. Activez **"Mode Maintenance"**
3. Les utilisateurs verront un ecran d'information leur indiquant que la plateforme est en maintenance
4. Les admins peuvent toujours se connecter

### Gestion des parametres

**Actions disponibles :**
- **Lister** : `GET /api/admin/settings` — Affiche tous les parametres
- **Modifier** : `PATCH /api/admin/settings` — Modifie un parametre
- **Appliquer en lot** : `POST /api/admin/settings/apply` — Applique plusieurs parametres
- **Vider le cache** : `POST /api/admin/settings/refresh-cache` — Invalide le cache en memoire

---

## 7. Navigation Complete du Super-Admin

### Barre laterale principale

| # | Menu | Chemin | Description |
|---|------|--------|-------------|
| 1 | **Overview** | `/dashboard/admin` | Tableau de bord avec KPI (users, cours, revenus) |
| 2 | **Users** | `/dashboard/admin/users` | Gestion complete des utilisateurs |
| 3 | **Schools** | `/dashboard/admin/schools` | Gestion des ecoles B2B |
| 4 | **Course Dist.** | `/dashboard/admin/course-distribution` | Distribution des cours aux ecoles |
| 5 | **Teacher Catalog** | `/dashboard/admin/teacher-catalog` | Catalogue des formations enseignants |
| 6 | **Courses** | `/dashboard/admin/courses` | Gestion des cours |
| 7 | **Review Pedago.** | `/dashboard/admin/pedagogical-review` | Validation du contenu pedagogique |
| 8 | **Arborescence** | `/dashboard/admin/arborescence` | Arborescence officielle tunisienne |
| 9 | **Statut Publication** | `/dashboard/admin/publication-status` | Etat de publication des notions |
| 10 | **Finance** | `/dashboard/admin/finance` | Transactions, wallets, revenue |
| 11 | **Analytics** | `/dashboard/admin/analytics` | Metriques et analyses |
| 12 | **Teacher Queue** | `/dashboard/admin/teachers` | File d'attente des inscriptions enseignants |
| 13 | **Token Packages** | `/dashboard/admin/packages` | Gestion des packages de tokens |
| 14 | **Invite Codes** | `/dashboard/admin/invite-codes` | Codes d'invitation des ecoles |
| 15 | **Audit Log** | `/dashboard/admin/audit` | Journal d'audit des actions admin |
| 16 | **Seuils Config** | `/dashboard/admin/seuils-config` | Configuration des seuils par matiere |
| 17 | **Specialites Pedago.** | `/dashboard/admin/specialites-pedagogiques` | Gestion des specialites pedagogiques |
| 18 | **AI Factory** | `/dashboard/admin/ai-factory` | Generateur de contenu IA |
| 19 | **Broadcast** | `/dashboard/admin/broadcast` | Envoi de messages broadcast |
| 20 | **Inbox** | `/dashboard/admin/inbox` | Messagerie interne admin |
| 21 | **Settings** | `/dashboard/admin/settings` | Parametres de la plateforme |

### Ecrans cles du Super-Admin

**Tableau de bord (`/dashboard/admin`) :**
- KPI : Total users, eleves, enseignants, cours, revenus
- Graphique de tendance des revenus
- Graphique d'evolution des inscriptions
- Graphique de couts API

**Gestion des users (`/dashboard/admin/users`) :**
- Tableau avec recherche, filtrage par role/statut
- Actions : modifier, changer le role, ajuster le solde, activer/desactiver, supprimer
- Import CSV pour creation en masse

**Gestion des ecoles (`/dashboard/admin/schools`) :**
- Liste des ecoles avec statut d'abonnement
- Actions : modifier, regenerer le code d'invitation, approuver
- Vue detaillee avec stats de l'ecole

**Finance (`/dashboard/admin/finance`) :**
- Transactions avec filtrage par type/date
- Wallets globaux avec ajout/deduction de credits
- Revenue Share pour les Teacher Partners
- Bulk Seats pour les formations

**AI Factory (`/dashboard/admin/ai-factory`) :**
- Generateur de cours en 4 etapes
- Integration RAG pour le contexte
- Publication automatique dans la bibliotheque

**Settings (`/dashboard/admin/settings`) :**
- 6 onglets : General, AI Providers, Pricing, Token Limits, Maintenance, Error Logs
- Test de connexion aux fournisseurs IA
- Gestion du mode maintenance

---

## 8. Rapport de Generation

**Partie Super-Admin (Platform Owner) : COMPLETE**

Le document couvre :
- Introduction au role avec Context Switcher et Impersonation
- Gestion SaaS/Tenants (ecoles B2B, codes d'invitation)
- Gestion financiere (packs, Bulk Seats, Revenue Share, Wallets)
- Gestion pedagogique (AI Factory, Bibliotheque, CMS Versioning, Parcours)
- Gestion utilisateurs/RBAC (multi-roles, import CSV, impersonation)
- Parametres plateforme (API IA, tokens, maintenance)
- Navigation complete (21 menus admin)

**Pret pour le role suivant : Admin Pedagogique**
