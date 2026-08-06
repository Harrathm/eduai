# Guide Utilisateur EDUAI Learning - Parent

> **Version** : 1.0 — Aout 2026
> **Branche** : phase1-critical
> **Derniere mise a jour** : 06/08/2026

---

## Table des matieres

1. [Introduction au Role](#1-introduction-au-rle)
2. [Rattacher un Enfant](#2-rattacher-un-enfant)
3. [Tableau de Bord Parent](#3-tableau-de-bord-parent)
4. [Suivi de l'Enfant](#4-suivi-de-lenfant)
5. [Recharger le Portefeuille de l'Enfant](#5-recharger-le-portefeuille-de-lenfant)
6. [Gestion du Pack de l'Enfant](#6-gestion-du-pack-de-lenfant)
7. [Messagerie](#7-messagerie)
8. [Compte Famille & Remises](#8-compte-famille--remises)

---

## 1. Introduction au Role

### Qui est le Parent ?

Le Parent (`parent`) est un role de **supervision** — vous pouvez suivre la progression de vos enfants rattaches, recharger leur portefeuille, et communiquer avec les enseignants.

### Perimetre d'action

| Action | Disponible |
|--------|-----------|
| Voir le tableau de bord de vos enfants | Oui |
| Suivre la progression de vos enfants | Oui |
| Recharger le portefeuille de vos enfants | Oui |
| Gerer les packs de vos enfants | Oui |
| Envoyer des messages aux enseignants | Oui |
| Gerer le compte famille (remises) | Oui |
| Creer/modifier des cours | **Non** |
| Acceder au Tuteur IA | **Non** |
| Acceder aux cours | **Non** |
| Modifier le profil d'un enfant | **Non** |

### Restrictions importantes

- Vous ne pouvez rattacher que des eleves de **votre ecole** (meme `school_id`)
- Vous ne pouvez rattacher que des eleves **non deja rattaches** a un autre parent
- Vous ne pouvez acceder qu'aux donnees de **vos propres enfants rattaches**
- Le profil personnel n'est pas accessible aux parents

---

## 2. Rattacher un Enfant

### Etape 1 : Acceder a la page de liaison

**Depuis le tableau de bord :**
1. Allez dans `Tableau de bord`
2. Descendez jusqu'a la section "Rattacher un enfant"
3. Entrez l'email de votre enfant

**Depuis la page Famille :**
1. Allez dans `Ma Famille`
2. Cliquez sur "Rattacher un enfant"
3. Entrez l'email de votre enfant

### Etape 2 : Envoyer la demande

**Endpoint :** `POST /api/parents/me/enfants/lier`

**Body :** `{"email_eleve": "eleve@example.com"}`

**Validations :**
1. L'eleve doit exister (email + role `student`)
2. L'eleve doit etre dans la **meme ecole** que vous
3. L'eleve ne doit pas deja etre rattache a un autre parent

**En cas d'erreur :**
- `404` : Eleve non trouve
- `403` : L'eleve n'appartient pas a votre ecole
- `400` : Cet eleve est deja rattache

### Etape 3 : Acces active

Une fois le lien etabli :
- L'eleve apparait dans votre tableau de bord
- Vous pouvez suivre sa progression
- Vous pouvez recharger son portefeuille
- Vous pouvez lui acheter des packs

### Retirer un enfant

**Depuis le detail de l'enfant :**
1. Allez dans le detail de l'enfant
2. Cliquez sur "Detacher"
3. Confirmez

**Depuis la page Famille :**
1. Allez dans `Ma Famille`
2. Cliquez sur l'icone corbeille a cote de l'enfant
3. Confirmez

**Endpoint :** `DELETE /api/parents/me/enfants/{eleve_id}/delier`

**Effet :** Le lien est supprime. Vous perdez l'acces aux donnees de l'enfant.

---

## 3. Tableau de Bord Parent

### Que contient le tableau de bord ?

**Chemin :** `Tableau de bord` (apres connexion)

**3 cartes de synthese :**
| Carte | Description |
|-------|-------------|
| **Enfants rattaches** | Nombre total d'enfants lies a votre compte |
| **Packs actifs** | Nombre total de packs actifs sur tous vos enfants |
| **DT depenses** | Montant total depense pour vos enfants |

**Liste des enfants :**
Pour chaque enfant :
- **Nom complet** (lien cliquable vers le detail)
- **Niveau scolaire**
- **Solde DT** (portefeuille)
- **Packs actifs** (nombre)
- **Liens rapides** : Portefeuille, Pack

**Section "Rattacher un enfant" :**
- Champ email + bouton "Rattacher"

**Messagerie integree :**
- Messages recus
- Formulaire de composition

---

## 4. Suivi de l'Enfant

### Detail d'un enfant

**Chemin :** `Tableau de bord` > [Nom de l'enfant] ou `Ma Famille` > [Nom de l'enfant]

**Page :** `ChildDetailPage`

**Informations affichees :**
- Nom complet et niveau scolaire
- Solde du portefeuille
- Pack actif (tier, matieres, date de fin)
- Badges gagnes
- Streak (jours consecutifs)
- Score moyen

### Suivi pedagogique

**Endpoint :** `GET /api/parents/me/enfants/{eleve_id}/suivi`

Retourne :
- Progression globale par matiere
- Taux de completion des lecons
- Derniere activite
- Resultats aux quizzes

### Progression detaillee

**Endpoint :** `GET /api/parents/me/enfants/{eleve_id}/progression`

Retourne :
- Detail par chapitre
- Scores par notion
- Tendance de progression (hausse/baisse/stable)
- Points forts et points faibles

---

## 5. Recharger le Portefeuille de l'Enfant

### Acceder a la page wallet

**Chemin :** `Tableau de bord` > [Enfant] > Portefeuille

**Page :** `ParentWalletPage`

### Recharger via Konnect

**Endpoint :** `POST /api/konnect/parents/me/enfants/{eleve_id}/credit-wallet`

**Montants autorises :** Entre 0 et 2000 DT

**Processus :**
1. Selectionnez l'enfant
2. Entrez le montant (en DT)
3. Selectionnez le mode de paiement (Konnect)
4. Confirmez
5. Le solde est credite immediatement

### Voir l'historique

Le solde et l'historique sont affiches dans la page wallet de l'enfant.

---

## 6. Gestion du Pack de l'Enfant

### Voir le pack actuel

**Chemin :** `Tableau de bord` > [Enfant] > Pack

**Page :** `ParentPackPage`

Le pack actuel de l'enfant est affiche :
- Tier (Gratuit, Basique, Silver, Golden)
- Matieres incluses
- Date de debut et de fin
- Statut (actif, grace, expire)

### Acheter un pack

**Endpoint :** `POST /api/abonnements/packs/{pack_id}/purchase`

Le parent peut acheter un pack pour son enfant. Le pack est scope au niveau scolaire de l'enfant.

**Processus :**
1. Selectionnez le pack
2. Selectionnez les matieres (si applicable)
3. Confirmez l'achat
4. Le pack est actif immediatement

### Remises famille

Si vous avez un compte famille, des remises s'appliquent automatiquement :
- **1er enfant** : Prix normal (pas de remise)
- **2eme enfant** : -20%
- **3eme enfant et plus** : -25%

---

## 7. Messagerie

### Envoyer un message

**Endpoint :** `POST /api/parents/me/messages`

**Destinataires :** Enseignants ou Administrateurs de l'ecole

**Pour envoyer un message :**
1. Selectionnez le destinataire (enseignant ou admin)
2. Entrez le sujet
3. Entrez le message
4. Envoyez

**Conditions :**
- Vous devez avoir au moins un enfant rattache
- Le destinataire doit etre dans la meme ecole

### Lire les messages

**Endpoint :** `GET /api/parents/me/messages`

Affiche :
- Messages recus
- Messages envoyes
- Statut (lu/non lu)

### Marquer comme lu

**Endpoint :** `PUT /api/parents/me/messages/{message_id}/read`

---

## 8. Compte Famille & Remises

### Le concept

Le systeme de compte famille gere les remises pour les familles avec plusieurs enfants inscrits.

### Creer un compte famille

Le compte famille est cree automatiquement lors de la premiere utilisation.

### Ajouter un enfant au compte famille

**Endpoint :** `POST /api/famille/enfants`

**Body :** `{"enfant_id": 123}`

### Retirer un enfant du compte famille

**Endpoint :** `DELETE /api/famille/enfants/{enfant_id}`

### Barreme des remises

| Enfant | Remise |
|--------|--------|
| 1er | 0% (prix normal) |
| 2eme | -20% |
| 3eme et plus | -25% |

**Maximum :** 5 enfants par compte famille

### Consulter le compte famille

**Endpoint :** `GET /api/famille/compte`

Retourne :
- Liste des enfants rattaches
- Remises appliquees
- Montant total depense

---

## Recapitulatif des permissions

### Ce que vous POUVEZ faire (Parent)

| Action | Condition |
|--------|-----------|
| Voir le tableau de bord | Au moins 1 enfant rattache |
| Rattacher un enfant | Meme ecole, non deja rattache |
| Retirer un enfant | Lien existant |
| Suivre la progression | Enfant rattache |
| Recharger le portefeuille | Enfant rattache, max 2000 DT |
| Acheter un pack | Enfant rattache |
| Envoyer des messages | Au moins 1 enfant rattache |
| Gerer le compte famille | Compte famille existant |
| Beneficier des remises | 2+ enfants dans le compte famille |

### Ce que vous NE POUVEZ PAS faire

| Action | Qui peut le faire |
|--------|-------------------|
| Creer/modifier des cours | Enseignants |
| Noter les devoirs | Enseignants |
| Acceder au Tuteur IA | Eleves |
| Modifier le profil d'un enfant | Eleves |
| Gestion admin de l'ecole | Admins |

---

## Partie Parent : COMPLETE

Le document couvre :
- Introduction au role et perimetre d'action
- Rattacher/retirer un enfant (validations, erreurs)
- Tableau de bord (3 cartes, liste enfants, messagerie)
- Suivi pedagogique (progression, scores, tendances)
- Recharge du portefeuille (Konnect, montants)
- Gestion des packs (achat, remises famille)
- Messagerie (enseignants, admins)
- Compte famille et systeme de remises (0%/-20%/-25%)

---

## Resume des 6 Guides Generes

| Role | Document | Lignes |
|------|----------|--------|
| Super-Admin | `GUIDE_UTILISATEUR_SUPER_ADMIN.md` | ~498 |
| Admin Pedagogique | `GUIDE_UTILISATEUR_ADMIN_PEDAGOGIQUE.md` | ~350 |
| Leader Pedagogique | `GUIDE_UTILISATEUR_LEADER_PEDAGOGIQUE.md` | ~397 |
| Enseignant | `GUIDE_UTILISATEUR_ENSEIGNANT.md` | ~502 |
| Eleve | `GUIDE_UTILISATEUR_ELEVE.md` | ~537 |
| Parent | `GUIDE_UTILISATEUR_PARENT.md` | (ce document) |
