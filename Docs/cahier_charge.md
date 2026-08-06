Voici le cahier des charges mis à jour, intégrant toutes nos décisions stratégiques et architecturales. Il est formaté en Markdown prêt à être utilisé.

***

```markdown
# 📄 Cahier des Charges Fonctionnel & Technique — EDUAI Learning

---

## 👥 1. Gestion des Rôles & Matrice des Droits (RBAC/ABAC)

La plateforme **EDUAI Learning** s'articule autour de **7 rôles utilisateurs** structurés pour assurer la gouvernance administrative, la modération pédagogique et la distribution commerciale B2C/B2B. 

### 1.1. Description des Rôles & Gouvernance
1. **Super-Admin (Platform Owner) :** Administrateur global du SaaS (gestion de la plateforme, abonnements B2B, clés d'API IA, grille tarifaire). N'a aucun accès direct au contenu privé des écoles (RGPD).
2. **Support Technicien (Rôle Caché IT) :** Rôle distinct du Super-Admin. N'a pas accès à la facturation, mais dispose d'un mode "Impersonation" tracé (Audit Log) en lecture-seule pour débugger les environnements privés B2B.
3. **Admin École (B2B Client) :** Responsable d'établissement gérant ses classes, ses enseignants, ses élèves et son quota de licences. Peut activer une "Validation de sortie" (Opt-in) pour autoriser ses professeurs à soumettre du contenu à la bibliothèque globale.
4. **Admin Pédagogique (Platform Curriculum Manager) :** Responsable de la qualité globale du contenu, gérant la file de modération finale avant publication globale.
5. **Leader Pédagogique (Inspecteur / Chef de Département) :** Expert disciplinaire global encadrant les enseignants d'une matière. Effectue la pré-validation des cours soumis. **N'a aucun accès aux cours privés générés au sein des écoles (Cloisonnement Multi-tenant).**
6. **Teacher (Enseignant) :** Rôle unifié. 
   * *Par défaut (Client) :* Utilise le moteur IA pour ses classes.
   * *Évolution (Partner) :* Attribut activé automatiquement après la première validation d'un de ses cours soumis à la bibliothèque globale. Débloque le Dashboard "Créateur" et la signature des CGU de propriété intellectuelle.
7. **Parent (Tuteur) :** Gère les achats de la série Famille, suit la progression globale de ses enfants et achète des formations hors-scolaires. N'a pas accès aux devoirs privés des classes B2B.
8. **Élève (Learner) :** Accède aux cours selon son pack (Gratuit, Basic, Silver, Golden) ou sa licence B2B, interagit avec le Copilote IA.

> 🔄 **Multi-Rôles (Context Switcher) :** Un utilisateur possédant plusieurs responsabilités (ex: Admin École ET Leader Pédagogique) utilise un compte unique avec un sélecteur de contexte dans le header pour basculer entre ses tableaux de bord sans se reconnecter.

### 1.2. Matrice d'Accès Fonctionnelle

| Module / Fonctionnalité | Super Admin | Support (IT) | Admin École | Admin Pédag. | Leader Pédag. | Teacher | Parent | Élève |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Gestion SaaS / Tenant** | 🟢 Total | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 |
| **Licences B2B Écoles** | 🟢 Total | 🔴 | 🟡 Sa structure | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 |
| **Gestion Classes & Élèves** | 🟢 Total | 🟡 Impersonation | 🟢 Son école | 🔴 | 🔴 | 🟡 Ses classes | 🔴 | 🔴 |
| **Workflow de Modération** | 🔴 | 🔴 | 🟡 Val. Sortie | 🟢 Valideur | 🟡 Pré-validation | 🟡 Soumission | 🔴 | 🔴 |
| **Génération de Cours IA** | 🟢 | 🔴 | 🔴 | 🟢 | 🟢 | 🟢 Total | 🔴 | 🔴 |
| **Création Contenu Privé** | 🔴 | 🟡 Lecture (Imp.) | 🔴 | 🔴 | 🔴 | 🟢 Total | 🔴 | 🔴 |
| **Suivi & Analytique** | 🟢 Global | 🟡 Debug | 🟢 Son école | 🟢 Global | 🟢 Sa matière | 🟡 Ses élèves | 🟡 Ses enfants | 🟡 Ses stats |
| **Gestion Packs / Achats** | 🟢 Config | 🔴 | 🟢 Achat École | 🔴 | 🔴 | 🔴 | 🟢 Achat Famille | 🟡 Choix Matières |
| **Formations Soft Skills** | 🟢 Config | 🔴 | 🔴 | 🔴 | 🔴 | 🟡 Inscription | 🟡 Achat/Suivi | 🟡 Accès selon Pack |
| **Assistant IA Copilote** | 🟢 Admin | 🔴 | 🔴 | 🟢 Pédag. | 🟢 Pédag. | 🟢 Mode Teacher | 🔴 | 🟢 Coach Élève |

### 1.3. Architecture des Droits : Modèle Hybride RBAC + ABAC

Pour éviter l'explosion des rôles en base de données et gérer la complexité des packs, la plateforme utilise une architecture hybride :
* **RBAC (Role-Based) pour le macro :** L'utilisateur a un rôle (ex: `ROLE_ELEVE`) lui donnant accès aux interfaces générales (Dashboard, Boutique).
* **ABAC (Attribute-Based) pour le micro :** L'accès fin aux contenus est géré par un moteur d'attributs qui vérifie l'équation : `Rôle + Pack actif (B2B/B2C) + Matières sélectionnées (Trimestre en cours) + Quota restant`.
* *Exemple :* Un élève "Basic" clique sur un cours d'Histoire. Le moteur ABAC vérifie si l'Histoire est dans son tableau `Matières_Selectionnees_T1`. Si non, accès refusé (Upsell).

### 1.4. Règles de Cumul et Isolation (B2B vs B2C)

* **Règle de l'Accès Maximal :** Si un élève possède une licence École (ex: Basic) et une licence Parent (ex: Golden), le système lui attribue dynamiquement le niveau d'accès le plus élevé (Golden).
* **Silos de Données :** Les devoirs privés et notes de classe (B2B) appartiennent à l'École. L'Admin École ne voit pas les achats B2C du Parent. Le Parent voit les statistiques globales scolaires mais pas le contenu privé des devoirs B2B.
* **Rupture de Licence B2B :** En cas de non-renouvellement par l'école, l'élève perd l'accès à l'"Espace Classe" (devoirs privés), mais conserve l'accès à la bibliothèque globale si le parent maintient son abonnement B2C.

---

## 📚 2. Module Pédagogique & Bibliothèque de Contenus

### 2.1. Structure Granulaire des Contenus
$$\text{Élément Pédagogique} \longrightarrow \text{Chapitre} \longrightarrow \text{Leçon} \longrightarrow \text{Parcours} \longrightarrow \text{Matière} \longrightarrow \text{Niveau d'Étude}$$

* **Types d'Éléments :** Textes, Vidéos, Images, Quizzes, Documents PDF / Exercices.
* **Niveaux de Difficulté (Apprentissage Adaptatif) :** Basique, Moyen, Difficile.
* **Méta-données d'Indexation (Tagging) :** `Matière`, `Niveau d'étude`, `Compétence ciblée`, `Langue` (Arabe / Français), `Durée estimée`, `Niveau de difficulté`.

### 2.2. Workflow de Modération & Governance

[ Enseignant (Génération IA Privée) ] ──> (Optionnel) Soumission globale
│
▼
[ Admin École ] (Si "Validation de sortie" activée)
│
▼
[ Leader Pédagogique ] (Pré-validation disciplinaire globale)
│
▼
[ Admin Pédagogique ] (Validation & Indexation Globale)
│
▼
[ Bibliothèque Globale SaaS ]
│
▼
[ Attribution Statut "Teacher Partner" + Signature CGU ]


---

## 💼 3. Module Commercial & Tarification

### 3.1. Séries de Packs
1. **Série Individuelle :** Apprenants indépendants sans établissement partenaire.
2. **Série Famille :** Réduction dégressive automatique au checkout (1<sup>er</sup> enfant : 100% | 2<sup>ème</sup> : -20% | 3<sup>ème</sup> et plus : -25%).
3. **Série École (B2B) :** Licences attribuables par l'Admin École via un espace d'administration dédié.

### 3.2. Tiers de Packs & Matrice d'Accès

La gestion des accès à ces packs est gérée par le moteur ABAC (voir section 1.3).

| Pack | Périmètre des Contenus | Règle de Configuration |
| :--- | :--- | :--- |
| **Gratuit** | Quota de **3 leçons / trimestre** | Attribution automatique à l'inscription. Reset trimestriel. Compteur d'attribut décrémenté à chaque consommation. |
| **Basic** | **2 Matières au choix** | 1 Langue + 1 Spécialité. Modifiable à chaque début de trimestre via table `User_Pack_Config`. |
| **Silver** | **4 Matières au choix** | 2 Langues + 2 Spécialités. Modifiable à chaque début de trimestre. |
| **Golden** | **Accès Illimité** | Accès total au niveau d'étude + formations *Soft Skills*. |

---

## 🗺️ 4. Guide UX/UI & Parcours Élève (Student Journey)

### 4.1. Étapes du Parcours Élève
1. **Inscription & Onboarding :** Inscription ➔ Choix du Niveau ➔ Attribution automatique du **Pack Gratuit** (ABAC: Quota=3) ➔ Redirection Dashboard.
2. **Consommation & Trigger Conversion :** Consommation des 3 leçons offertes (ABAC: Quota=0) ➔ Modale d'incitation à l'achat vers la boutique.
3. **Configuration du Pack Payant :**
   - **Pack Basic :** Sélection de **1 Langue** + **1 Spécialité**.
   - **Pack Silver :** Sélection de **2 Langues** + **2 Spécialités**.
   - **Pack Golden :** Déblocage global immédiat.
4. **Apprentissage & Interaction IA :** Suivi des leçons + Assistance continue (Coach IA + Widget flottant).
5. **Reconfiguration Trimestrielle :** Modification des choix de matières (Basic/Silver) en début de trimestre (Mise à jour des attributs ABAC).
6. **Formations Soft Skills :** Inscription / Achat unitaire ou accès inclus (Golden).

---

## 🖥️ 5. Architecture du Dashboard Élève

┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 👤 HEADER PROFIL & STATUT (Nom, Niveau d'étude, Badge Pack, Bouton Upgrade)                            │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 📢 BANNIÈRE DYNAMIQUE DE STATUT & QUOTA (Gratuit: 2/3 leçons | Basic/Silver: Matières active T1)        │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 🚀 COLONNE PRINCIPALE (2/3)                                            │ 📊 COLONNE SECONDAIRE (1/3)   │
│                                                                        │                               │
│  🤖 1. BLOC ASSISTANT IA (COPILOTE PÉDAGOGIQUE)                        │ 📈 1. STATISTIQUES ÉLÈVE     │
│     • Recommandations contextuelles de révision                        │    • Temps d'apprentissage    │
│     • Actions Rapides : [ Quiz ] [ Expliquer erreur ] [ Aide Devoir ]  │    • Score moyen Quizzes      │
│     • Sélecteur de Langue : [ Français 🇫🇷 | Arabe 🇹🇳 ]                │                               │
│                                                                        │ 🌟 2. MES FORMATIONS SKILLS   │
│  ▶️ 2. REPRENDRE L'APPRENTISSAGE (Dernière leçon en cours)             │    • Suivi des Soft Skills    │
│                                                                        │    • Raccourci catalogue      │
│  📚 3. MES MATIÈRES ACCESSIBLES                                        │                               │
│     • Grille des cartes matières actives (Basic / Silver / Golden)     │ 🔔 3. RAPPELS & ANNONCES      │
└────────────────────────────────────────────────────────────────────────┴───────────────────────────────┘
[ 💬 Widget IA Flottant ]


---

## 💻 6. Arborescence des Pages Frontend

* **Zone Publique :**
  * `/` : Landing Page SaaS EDUAI Learning.
  * `/register` : Formulaire d'inscription avec sélection du Niveau d'Étude.
  * `/login` : Authentification.
* **Zone Élève Protégée :**
  * `/dashboard` : Tableau de bord principal (Bloc IA, Jauge Quota, Navigation cours).
  * `/courses` : Lecteur interactif de cours et d'exercices.
  * `/catalog/packs` : Boutique des packs avec configurateur de matières (1L+1S ou 2L+2S).
  * `/skills-catalog` : Catalogue des formations *Soft Skills* (Gratuites / Payantes).
  * `/my-skills` : Suivi des formations hors-scolaires activement suivies.
* **Zone Paramètres :**
  * `/settings/subscription` : Gestion du pack actif, reconfiguration trimestrielle et facturation.
```