# EDUAI Learning
### Plateforme ERP & LMS pour établissements privés en Tunisie

## Rapport détaillé — Modules Pédagogique & Commercial
*Architecture des contenus, gouvernance éditoriale et matrice d'accès commerciale*

Août 2026

---

## Sommaire

1. [Synthèse générale](#synthèse-générale)
2. [Module A — Architecture Pédagogique & Bibliothèque de Contenus](#module-a--architecture-pédagogique--bibliothèque-de-contenus)
   - A.1 Hiérarchie de contenu
   - A.2 Rattachement matière/niveau
   - A.3 Types d'éléments pédagogiques
   - A.4 Taxonomie des compétences
   - A.5 Gouvernance & workflow de modération
3. [Module B — Matrice Commerciale & Gestion des Accès](#module-b--matrice-commerciale--gestion-des-accès)
   - B.1 Séries de packs
   - B.2 Conflit licence École / achat individuel
   - B.3 Tiers de packs
   - B.4 Relation avec le système de tokens IA
   - B.5 Facturation et échecs de paiement
4. [Synthèse des décisions clés](#synthèse-des-décisions-clés)

---

## Synthèse générale

Ce rapport documente les deux modules qui structurent respectivement le contenu pédagogique et le modèle économique d'EDUAI Learning : l'**Architecture Pédagogique & Bibliothèque de Contenus** d'une part, et la **Matrice Commerciale & Gestion des Accès** d'autre part.

Les règles présentées ici sont définitives — elles ont été discutées, clarifiées et validées point par point, notamment sur les aspects les plus sensibles : l'articulation entre bibliothèque locale d'établissement et bibliothèque globale (qui constitue une exception délibérée et contrôlée à l'isolation multi-tenant), et les mécaniques de tarification familiale et de licences B2B. Ce document sert de référence à la spécification technique déjà transmise à l'outil de développement IA.

---

## Module A — Architecture Pédagogique & Bibliothèque de Contenus

### A.1 — Hiérarchie de contenu

Le contenu pédagogique est organisé selon une hiérarchie à sept niveaux, permettant une granularité fine tout en restant extensible :

> **Niveau d'étude → Matière → Parcours → Chapitre → Leçon → Paragraphe → Sous-paragraphe → Élément Pédagogique**

- Le **Parcours** est le conteneur du programme officiel d'une matière/niveau donné.
- Le **Chapitre** regroupe plusieurs Leçons.
- Le **Paragraphe** est modélisé comme une entité auto-référencée (`parent_paragraphe_id` nullable), permettant une profondeur illimitée sans modification future du schéma.
- L'**Élément Pédagogique** est la brique atomique, rattachée à un paragraphe ou directement à une leçon si aucun découpage n'est nécessaire.

### A.2 — Rattachement matière/niveau

Chaque élément combine un rattachement primaire unique et des tags secondaires optionnels :

- **Rattachement primaire** : matière et niveau obligatoires, déterminant la place hiérarchique et l'affichage par défaut.
- **Tags secondaires (multi-matière)** : table de liaison permettant d'étiqueter un élément comme pertinent pour d'autres matières, à des fins de recherche transversale, sans dupliquer le contenu.

### A.3 — Types d'éléments pédagogiques

Cinq types de contenu sont supportés, chacun avec des champs spécifiques en plus d'un socle commun (matière, niveau, compétence ciblée, langue, durée estimée, niveau de difficulté, statut de workflow) :

| Type | Champs spécifiques |
|---|---|
| **Texte** | Contenu riche, nombre de mots |
| **Vidéo** | Référence de stockage, durée réelle, sous-titres AR/FR, miniature |
| **Image** | Référence de stockage, légende, texte alternatif |
| **Quiz** | Questions typées (QCM/vrai-faux/réponse courte), barème, corrigé, tentatives autorisées |
| **Document PDF/Exercice** | Fichier source avec corrigé structuré associé, compatible avec la correction guidée par l'IA tuteur |

Le niveau de difficulté (Basique/Moyen/Difficile) est taggé au niveau de l'élément entier plutôt que question par question, pour un modèle plus simple à ce stade.

### A.4 — Taxonomie des compétences

Les compétences ciblées proviennent d'une **liste fermée par matière et par niveau**, alignée sur le système d'objectifs à cinq horizons déjà en place dans EDUAI — aucun champ texte libre, pour garder un reporting exploitable.

### A.5 — Gouvernance & workflow de modération

Trois rôles distincts interviennent dans la création et la validation du contenu :

| Rôle | Nature | Fonction |
|---|---|---|
| **Enseignant Partenaire** | Staff EDUAI, rémunéré pour créer du contenu | Accès direct aux outils d'édition, alimente la bibliothèque globale |
| **Enseignant Client** | Enseignant d'un établissement abonné | Usage IA pour ses classes ; peut soumettre ses créations à la modération |
| **Responsable Pédagogique** | Rôle transverse EDUAI (pas par établissement) | Valide/rejette tout contenu avant publication globale |

**Cycle de vie du contenu :**

> **Brouillon → En attente de relecture → Publié**
> **→ Rejeté (avec commentaire) → retour Brouillon**

- Un contenu **Publié** puis modifié repart en *En attente de relecture* comme nouvelle version ; l'ancienne reste visible et utilisable jusqu'à validation de la nouvelle.
- Un contenu **Rejeté** conserve le commentaire du Responsable Pédagogique et peut être resoumis après correction.

**Isolation bibliothèque locale / bibliothèque globale** *(point d'architecture le plus sensible du module)*

Le contenu créé par un Enseignant Client reste par défaut dans la bibliothèque locale de son établissement, strictement isolée comme toute donnée tenant. La promotion vers la bibliothèque globale se fait par **copie/snapshot** au moment de la validation — jamais par lien live vers la donnée source. C'est une exception délibérée et auditée à l'isolation multi-tenant fixée dès les fondations techniques du projet. Le contenu publié globalement affiche une attribution générique, sans exposer l'établissement d'origine, pour protéger la confidentialité de l'école cliente.

---

## Module B — Matrice Commerciale & Gestion des Accès

### B.1 — Séries de packs

**Série Individuelle**
Un apprenant indépendant, un compte, un pack.

**Série Famille**
- Un compte famille (payeur unique) lie plusieurs comptes enfants.
- Rang déterminé par la **date d'inscription** : 1er enfant inscrit = tarif plein, 2e = **-20%**, 3e et suivants = **-25%**, quel que soit le pack choisi par chacun.
- Le rang est figé à l'inscription de chaque enfant ; seul l'ajout d'un nouvel enfant recalcule le rang des suivants.
- Le recalcul de la remise s'applique **au prochain renouvellement uniquement**, jamais rétroactivement sur un cycle de facturation en cours.

**Série École (B2B)**
- Quota fixe de licences, pouvant **mixer plusieurs tiers** dans un même quota (ex : 100 Basique + 50 Golden).
- Espace Admin Établissement pour affecter/désaffecter les licences aux comptes élèves.
- **Réaffectation immédiate** possible dès qu'un élève quitte : la licence redevient disponible instantanément. L'historique de progression de l'élève sortant est archivé, jamais supprimé ; le nouvel élève assigné démarre avec un profil vierge.

### B.2 — Conflit licence École / achat individuel

Lorsqu'un élève dispose à la fois d'une licence École et d'un achat individuel actif, l'accès effectif correspond à **l'union des deux** : pour chaque matière, le plus large des deux accès prévaut, afin de ne jamais pénaliser l'élève. Le prélèvement individuel continue de courir séparément — la résolution d'un doublon de facturation reste un cas de support manuel, signalé par le parent.

### B.3 — Tiers de packs

| Pack | Périmètre | Règle de gestion |
|---|---|---|
| **Gratuit** | 3 leçons offertes / trimestre, majorité des matières | Décompte à la complétion (pas à l'ouverture) ; reset auto au trimestre ; matières exclues configurables |
| **Basique** | 2 matières au choix (1 Langue + 1 Spécialité), accès illimité | Reconfigurable à chaque début de trimestre |
| **Silver** | 4 matières au choix (2 Langues + 2 Spécialités), accès illimité | Reconfigurable à chaque début de trimestre |
| **Golden** | Accès illimité toutes matières + Formations Non-Scolaires | Aucune restriction |

**Règles complémentaires :**
- Basique/Silver : accès illimité dans les matières choisies. Au changement de matière en début de trimestre, l'historique de progression sur l'ancienne matière reste accessible en lecture seule.
- **Upgrade** de tier possible à tout moment, avec proratisation immédiate de la facturation.
- **Downgrade** possible uniquement à la fin du trimestre en cours, pour éviter l'abus d'accès temporaire suivi d'un désabonnement immédiat.

### B.4 — Relation avec le système de tokens IA

Le tier de pack de contenu et le système de crédits IA restent **complètement indépendants**. Un élève en pack Gratuit peut acheter des recharges de tokens IA séparément ; un élève Golden ne dispose pas de tokens illimités automatiquement. La gestion des tokens reste gouvernée par le modèle d'allocation par établissement déjà spécifié dans l'écosystème IA.

### B.5 — Facturation et échecs de paiement

En cas d'échec de paiement, une période de **grâce de 7 jours** est accordée avec accès maintenu, suivie d'un **downgrade automatique vers le pack Gratuit** à l'expiration de la grâce — ni coupure brutale, ni gratuité illimitée.

---

## Synthèse des décisions clés

Tableau récapitulatif des arbitrages les plus structurants pris au cours de la discussion, à conserver comme référence rapide.

| Question | Décision retenue |
|---|---|
| Ordre de calcul de la remise familiale | Basé sur la date d'inscription ; rang figé par enfant, recalcul au renouvellement suivant seulement |
| Nature des Enseignants Partenaires | Staff EDUAI rémunéré spécifiquement pour produire du contenu global |
| Réaffectation des licences École | Immédiate ; historique élève sortant archivé, nouveau profil vierge pour l'élève entrant |
| Hiérarchie de contenu | Sept niveaux avec Paragraphe/Sous-paragraphe auto-référencés pour une profondeur illimitée |
| Tagging matière des éléments | Rattachement primaire unique + tags secondaires multi-matière pour la recherche |
| Isolation bibliothèque locale/globale | Promotion par copie/snapshot uniquement, jamais par lien live — exception auditée à l'isolation multi-tenant |
| Conflit licence École / individuel | Union des deux accès, jamais de restriction ; doublon de facturation géré manuellement |
| Lien pack de contenu / tokens IA | Systèmes indépendants — aucun couplage automatique entre tier de contenu et quota IA |
