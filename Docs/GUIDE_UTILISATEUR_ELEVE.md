# Guide Utilisateur EDUAI Learning - Eleve (Student)

> **Version** : 1.0 — Aout 2026
> **Branche** : phase1-critical
> **Derniere mise a jour** : 06/08/2026

---

## Table des matieres

1. [Premiers pas](#1-premiers-pas)
2. [Tableau de Bord (Hub Cockpit)](#2-tableau-de-bord-hub-cockpit)
3. [Mon Pack & Abonnement](#3-mon-pack--abonnement)
4. [Quota Gratuit & Trimestre](#4-quota-gratuit--trimestre)
5. [Mes Matieres & Cours](#5-mes-matieres--cours)
6. [Parcours Pedagogique](#6-parcours-pdagogique)
7. [Tuteur IA](#7-tuteur-ia)
8. [Wallet & Credits](#8-wallet--credits)
9. [Gamification](#9-gamification)
10. [Mes Notes & Signets](#10-mes-notes--signets)

---

## 1. Premiers pas

### Inscription

Lors de votre premiere connexion, vous etes redirige vers la page d'onboarding.

**Etape 1 : Selection de la langue**
- Francais, Anglais, ou Arabe
- Cette preference est sauvegardee et appliquee a toute l'interface

**Etape 2 : Selection du niveau scolaire**
- 20 niveaux disponibles (7eme base, 8eme base, 9eme base, 1ere-2eme-3eme-4eme annee secondaire, Bac...)
- Cette selection determine les packs et cours disponibles

**Etape 3 : Rejoindre une ecole (optionnel)**
- Entrez le code d'invitation de votre ecole
- Le code est fourni par l'administrateur de l'ecole
- Vous etes ajoute a l'ecole et vos cours y seront disponibles

### Profil

**Chemin :** `Profil`

Vous pouvez modifier :
- **Nom complet**
- **Niveau scolaire**
- **Langue** de l'interface

---

## 2. Tableau de Bord (Hub Cockpit)

### Structure du tableau de bord

Le tableau de bord est organise en grille 3 colonnes :

**Colonne principale (2 colonnes) :**

| Widget | Description |
|--------|-------------|
| **Assistant IA Copilote** | Raccourcis vers Quiz, Expliquer erreur, Aide Devoir — redirige vers le Tuteur IA |
| **Reprendre l'Apprentissage** | Derniere lecon suivie avec barre de progression et bouton "Continuer" |
| **Mes Matieres** | Grille des matieres accessibles (jusqu'a 6) avec barre de progression |

**Colonne secondaire (1 colonne) :**

| Widget | Description |
|--------|-------------|
| **Statistiques** | Temps d'apprentissage (estime), lecons terminees, progression globale |
| **Formations Soft Skills** | Jusqu'a 3 formations avec lien vers "Mes Formations" et "Catalogue" |
| **Annonces & Rappels** | Messages non lus, dernier message, rappel de devoirs |
| **Portefeuille** | Solde DT, equivalents tokens, bouton "Voir Details" |

**En-tete (pleine largeur) :**
- Photo de profil + prenom
- Badge de pack (couleur selon le tier)
- Badge de trimestre (T1, T2, T3)
- Bouton "Ameliorer mon pack"

**Banniere dynamique :**
- Pack Gratuit : Jauge de quota (utilise/limite)
- Pack Basic/Silver : Banniere de reconfiguration trimestrielle
- Pack Golden : "Acces Illimite Actif"

### Data source

Le tableau de bord appelle 6 endpoints en parallel :
- `GET /api/learner/dashboard` — progression, stats, matieres
- `GET /api/abonnements/mes-abonnements` — pack actif
- `GET /api/wallet/balance` — solde
- `GET /api/inbox/messages` — messages
- `GET /api/catalog/courses?category=soft_skills` — formations soft skills
- `GET /api/abonnements/packs` — catalogue de packs

---

## 3. Mon Pack & Abonnement

### Les 4 tiers de packs

| Tier | Nom | Matieres | Prix | Acces |
|------|-----|----------|------|-------|
| **Gratuit** | Starter | — | Gratuit | 3 lecons / trimestre |
| **Basique** | Basic | 1 langue + 1 specialite | Variable | Acces aux matieres selectionnees |
| **Silver** | Premium | 2 langues + 2 specialites | Variable | Acces etendu |
| **Golden** | Elite | Toutes les matieres | Variable | Acces illimite + Soft Skills |

### Consulter les packs disponibles

**Chemin :** `Packs` ou `Mon Abonnement`

**Endpoint :** `GET /api/abonnements/packs?niveau_scolaire={votre_niveau}`

Les packs sont filtres par votre niveau scolaire. Chaque pack affiche :
- Nom et badge de tier (couleur)
- Matieres incluses (liste)
- Prix en DT (Dinars Tunisiens)
- Validite (90 jours pour les packs payants)

### Acheter un pack

**Etape 1 :** Selectionnez un pack
**Etape 2 :** Selectionnez vos matieres (Modal Configurateur)
- **Basique** : 1 langue + 1 specialite
- **Silver** : 2 langues + 2 specialites
- **Golden** : Pas de selection (acces illimite)
**Etape 3 :** Confirmez l'achat
**Etape 4 :** Le pack est actif immediatement

**Endpoint :** `POST /api/abonnements/packs/{pack_id}/purchase`

**Body :** `{"matieres": [id1, id2, ...]}`

### Regles d'achat

- **Un seul pack actif** a la fois — vous ne pouvez pas souscrire a un 2eme pack tant que le premier est actif
- **Niveau scolaire** — le pack doit correspondre a votre niveau
- **Pas de downgrade pendant un trimestre** — si vous changez de tier, le downgrade prendra effet au prochain trimestre

### Changer de tier (Upgrade/Downgrade)

**Upgrade** (Basique → Silver, Silver → Golden) :
- Application **immediate**
- Vous accedez aux nouvelles matieres immediatement

**Downgrade** (Golden → Silver, Silver → Basique) :
- Application **differee** au debut du prochain trimestre
- Vous gardez l'acces actuel jusqu'a la fin du trimestre

**Endpoint :** `POST /api/abonnements/change-tier`

### Annuler un downgrade programme

Si vous avez programme un downgrade mais avez change d'avis :

**Endpoint :** `DELETE /api/abonnements/cancel-scheduled-change`

### Annuler un abonnement

**Endpoint :** `DELETE /api/abonnements/{id}/cancel`

**Delai de grace :** 7 jours avant la fin effective pour les tiers payants.

### Mon Pack (sommaire)

**Endpoint :** `GET /api/abonnements/mon-pack`

Retourne :
- Pack actif avec tier, matieres, date de debut/fin
- Statut (actif, grace, expire)
- Date de prochaine reconfiguration

---

## 4. Quota Gratuit & Trimestre

### Quota gratuit (Pack Gratuit)

Les eleves gratuits ont un quota de **3 lecons par trimestre**.

**Comment ca marche :**
1. Vous avez acces a 3 lecons pendant le trimestre en cours
2. Chaque lecon consultee est comptabilisee
3. A 3 lecons, un message s'affiche : "Quota atteint"
4. Une modale vous propose de souscrire a un pack

**Jauge de quota :**
- Affichee dans le tableau de bord
- Barre de progression coloree (vert < 33%, orange 33-66%, rouge 66-100%)
- Compteur `utilise/limite`

**Pack payant :** Quota illimite — pas de restriction.

### Calendrier trimestriel (Tunisie 2026-2027)

| Trimestre | Dates | Fin de la fenetre de reconfiguration |
|-----------|-------|-------------------------------------|
| **T1** | 15 septembre — 19 decembre 2026 | 30 septembre 2026 |
| **T2** | 5 janvier — 27 mars 2027 | 20 janvier 2027 |
| **T3** | 6 avril — 19 juin 2027 | 21 avril 2027 |

### Reconfiguration trimestrielle

**Condition :** Packs Basic et Silver uniquement, pendant les **15 premieres jours** de chaque trimestre.

**Quand la reconfiguration est possible :**
1. Un nouveau trimestre commence
2. Vous avez un pack Basic ou Silver actif
3. Vous n'avez pas encore reconfigure ce trimestre
4. Vous etes dans les 15 premiers jours du trimestre

**Comment reconfigurer :**
1. La banniere "Reconfiguration" apparait dans le tableau de bord
2. Cliquez sur "Reconfigurer"
3. Selectionnez les nouvelles matieres
4. Confirmez

**Effets :**
- Les nouvelles matieres sont actives immediatement
- Les anciennes matieres ne sont plus accessibles
- La reconfiguration est definitif pour ce trimestre

**Pack Golden :** Pas de reconfiguration necessaire (acces illimite).
**Pack Gratuit :** Pas de reconfiguration (pas de pack).

---

## 5. Mes Matieres & Cours

### Catalogue de cours

**Chemin :** `Cours`

**Endpoint :** `GET /api/catalog/courses`

Le catalogue affiche les cours disponibles avec :
- Titre et description
- Matiere et niveau
- Nombre de lecons
- Note moyenne
- Nombre d'eleves inscrits
- Badge du pack requis (si applicable)

### S'inscrire a un cours

**Endpoint :** `POST /api/learner/courses/{id}/enroll`

**Conditions :**
- Le cours est public
- Vous avez le pack requis (ou le cours est gratuit)
- Vous n'etes pas deja inscrit

### Mes cours inscrits

**Endpoint :** `GET /api/learner/my-courses`

Affiche la liste des cours auxquels vous etes inscrit avec :
- Progression (%)
- Nombre de lecons terminees
- Derniere lecon consultee

### Suivre un cours

**Chemin :** `Cours` > [Cours] > [Lecon]

**Contenu d'une lecon :**
- Texte educatif
- Video (si disponible)
- Quiz d'evaluation
- Exercices

**Endpoint :** `GET /api/learner/lessons/{id}`

### Progression

**Mettre a jour la progression :**
- En cliquant sur une lecon, le systeme la marque "en cours"
- En terminant une lecon, marquez-la "terminee"
- La progression est sauvegardee automatiquement

**Endpoint :** `POST /api/learner/lessons/{id}/progress`

### Certificats

Lorsque vous terminez 100% d'un cours, un certificat est genere automatiquement.

**Endpoint :** `GET /api/learner/certificates`

---

## 6. Parcours Pedagogique

### Catalogue de parcours

**Chemin :** `Parcours`

**Endpoint :** `GET /api/pathway/catalog`

Le catalogue affiche les parcours officiels tunisiens :
- Niveaux d'etude
- Matieres disponibles par niveau
- Packs requis pour chaque matiere

### Mon Parcours

**Chemin :** `Mon Parcours`

**Endpoint :** `GET /api/pathway/mon-parcours`

Vue detaillee de votre progression :
- Niveau scolaire
- Matiere selectionnee
- Chapitres avec progression
- Notions par chapitre
- Score de maitrise par notion

### Profil d'assimilation

**Endpoint :** `GET /api/pathway/eleves/{id}/profil-assimilation`

Votre profil personnel :
- Niveau de maitrise par matiere
- Points forts et points faibles
- Tendance de progression

### Enrollement automatique

**Endpoint :** `POST /api/pathway/auto-enroll-from-test`

Apres un test de placement, le systeme vous inscrit automatiquement au parcours adapte.

### Placement Test

**Endpoint :** `GET /api/placement/tests`

Tests diagnostiques pour evaluer votre niveau :
- 3 niveaux de competence : remediation, standard, avance
- Resultat : recommandation de parcours adapte

---

## 7. Tuteur IA

### Le Tuteur IA (page complete)

**Chemin :** `Tuteur IA`

Fonctionnalites :
- **Poser une question** — Reponse en streaming (SSE)
- **Expliquer un concept** — Explication detaillee
- **Corriger un devoir** — Correction automatique
- **Generer un quiz** — Questions adaptees a votre niveau
- **Historique** — Conversations sauvegardees

**Endpoint :** `POST /api/ai/ask`

### Le Tuteur IA flottant

Disponible sur **toutes les pages** — un mini-chat en bas a droite de l'ecran.

### Niveaux d'acces IA

| Palier | Fonctionnalites |
|--------|----------------|
| **Decouverte** | Poser des questions, expliquer, corriger |
| **Excellence** | + Generer des exercices |
| **Etablissement** | + Generer du contenu personnalise |

### Couts en credits

Toutes les fonctionnalites IA consomment des credits de votre portefeuille. Le systeme verifie votre solde avant chaque appel.

### Contenu signale

Si vous trouvez une reponse IA incorrecte, vous pouvez la signaler via le systeme de signalement. L'Admin Pedagogique examinera le signalement.

---

## 8. Wallet & Credits

### Consulter le solde

**Chemin :** `Wallet`

**Endpoint :** `GET /api/wallet/balance`

Le solde est decompose par pool :
- **trial** — Credits d'essai
- **subscription** — Credits d'abonnement
- **school_allocated** — Credits alloues par l'ecole
- **purchased** — Credits achetes
- **dt_purchased** — Credits achetes (DT)

**Equivalent :** 1 credit = 500 tokens

### Historique des transactions

**Endpoint :** `GET /api/wallet/history`

Affiche l'historique des entrees et sorties de credits.

### Acheter des credits

**Endpoint :** `POST /api/wallet/purchase`

Offres disponibles :
- **1 mois** : 100 credits pour 15 DT
- **3 mois** : 350 credits pour 39 DT (-14%)
- **12 mois** : 1500 credits pour 129 DT (-29%)

### Packs d'etudes (Study Packs)

**Endpoint :** `GET /api/packs`

Achetez des packs de contenu specifiques.

---

## 9. Gamification

### Badges

**Chemin :** `Gamification`

**Endpoint :** `GET /api/gamification/badges`

Categories de badges :
- **Progression** — Badges d'avancement (premiere lecon, 10 lecons, 50 lecons...)
- **Quiz** — Badges de quiz (premier quiz, score parfait, 10 quizzes...)
- **Streak** — Badges de regularite (3 jours, 7 jours, 30 jours...)
- **Speciaux** — Badges speciaux (premiere inscription, premium...)

### Streak (Regularite)

**Endpoint :** `GET /api/gamification/streak`

- Compteur de jours consecutifs d'activite
- Activites trackees : connexion, quiz, objectif
- Calendrier de 30 jours avec code couleur :
  - Vert (15+ pts/jour)
  - Bleu (8-14 pts)
  - Orange (3-7 pts)
  - Gris (< 3 pts)

### Classements

**Endpoint :** `GET /api/gamification/rankings`

- Classement par palier (niveau d'abonnement)
- Top 50 eleves
- Votre position mise en evidence

---

## 10. Mes Notes & Signets

### Notes par lecon

**Ajouter une note :**
1. Ouvrez une lecon
2. Cliquez sur "Ajouter une note"
3. Entrez votre note personnelle
4. Sauvegardez

**Endpoint :** `POST /api/learner/lessons/{id}/notes`

**Consulter les notes :**
**Endpoint :** `GET /api/learner/lessons/{id}/notes`

### Signets

**Ajouter un signet :**
1. Ouvrez une lecon
2. Cliquez sur "Ajouter un signet"
3. Le signet est cree avec la position actuelle

**Endpoint :** `POST /api/learner/lessons/{id}/bookmarks`

**Consulter les signets :**
**Endpoint :** `GET /api/learner/lessons/{id}/bookmarks`

---

## Recapitulatif des permissions

### Ce que vous POUVEZ faire (Student)

| Action | Condition |
|--------|-----------|
| Parcourir le catalogue de cours | Toujours |
| S'inscrire a des cours | Pack requis (ou gratuit) |
| Suivre des lecons | Pack requis (ou quota gratuit) |
| Passer des quizzes | Toujours |
| Utiliser le Tuteur IA | Credits requis |
| Consulter le portefeuille | Toujours |
| Acheter des credits | Toujours |
| Acheter des packs | Un seul actif |
| Changer de tier | Up immediatif, Down differe |
| Reconfigurer les matieres | 15 jours / trimestre |
| Parcourir les parcours | Toujours |
| Voir les badges et classements | Toujours |
| Ajouter des notes et signets | Toujours |
| Consulter les messages | Toujours |
| Passer les tests de placement | Toujours |
| Obtenir des certificats | 100% de cours termine |

### Ce que vous NE POUVEZ PAS faire

| Action | Qui peut le faire |
|--------|-------------------|
| Creer/modifier des cours | Enseignants |
| Noter les devoirs | Enseignants |
| Gestion des classes | Enseignants |
| Creer du contenu IA | Enseignants |
| Valider le contenu | Leaders/Admin Pedago. |
| Gestion financiere | Admins |

---

## Partie Eleve : COMPLETE

Le document couvre :
- Premiers pas (inscription, onboarding, ecole)
- Tableau de bord Hub Cockpit (6 widgets, 6 appels API)
- Pack et abonnement (4 tiers, achat, upgrade, downgrade)
- Quota gratuit (3 lecons/trimestre) et calendrier
- Matieres et cours (catalogue, inscription, progression)
- Parcours pedagogique (officiel tunisien, profil d'assimilation)
- Tuteur IA (3 fonctionnalites, niveaux palier)
- Wallet (credits, achats, historique)
- Gamification (badges, streak, rankings)
- Notes et signets

**Pret pour le role suivant : Parent**
