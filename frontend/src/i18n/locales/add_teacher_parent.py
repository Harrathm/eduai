import json
import os

LOCALE_DIR = r"D:\RAG_APP_new\frontend\src\i18n\locales"

# FR additions
teacher_fr = {
    "dashboard": {
        "title": "Tableau de Bord",
        "welcome": "Bienvenue, ",
        "myCourses": "Mes Cours",
        "myClasses": "Mes Classes",
        "students": "Étudiants",
        "aiCredits": "Crédits IA",
        "quickAccess": "Accès Rapide",
        "aiStudio": "AI Studio",
        "revenue": "Revenus",
        "wallet": "Wallet",
        "viewAll": "Voir tout",
        "eleves": "élèves",
        "cours": "cours"
    },
    "aiStudio": {
        "title": "AI",
        "titleSuffix": "Studio",
        "subtitle": "Générez du contenu pédagogique avec l'IA",
        "tokens": "tokens",
        "contentType": "Type de contenu",
        "subject": "Matière",
        "level": "Niveau",
        "trimester": "Trimestre",
        "description": "Description du contenu désiré",
        "placeholder": "Décrivez ce que vous voulez générer... Ex: 'Un devoir sur les équations du premier degré pour les élèves de 3ème année collège, comprenant 5 exercices de difficulté progressive'",
        "estimatedCost": "Coût estimé: ~5 tokens",
        "generating": "Génération...",
        "generate": "Générer",
        "result": "Résultat",
        "copy": "Copier",
        "history": "Historique",
        "loading": "Chargement...",
        "noHistory": "Aucun historique",
        "quickGenerations": "Générations rapides",
        "error": "Erreur de connexion.",
        "subjects": {
            "mathematiques": "Mathématiques",
            "physique": "Physique",
            "chimie": "Chimie",
            "biologie": "Biologie",
            "histoire": "Histoire",
            "geographie": "Géographie",
            "francais": "Français",
            "anglais": "Anglais",
            "informatique": "Informatique",
            "pedagogie": "Pédagogie"
        },
        "levels": {
            "primaire": "Primaire",
            "college": "Collège",
            "lycee": "Lycée",
            "universite": "Université"
        },
        "trimesters": {
            "t1": "Trimestre 1",
            "t2": "Trimestre 2",
            "t3": "Trimestre 3"
        },
        "contentTypes": {
            "homework": "Devoir",
            "lesson": "Leçon",
            "lesson_plan": "Plan de leçon",
            "outline": "Plan annuel",
            "quiz": "Quiz",
            "summary": "Résumé"
        }
    },
    "elements": {
        "title": "Éléments",
        "titleSuffix": "Pédagogiques",
        "subtitle": "Créez et gérez vos contenus pédagogiques",
        "newElement": "Nouvel Élément",
        "loading": "Chargement...",
        "noResults": "Aucun élément trouvé",
        "filters": {
            "all": "Tous",
            "brouillon": "Brouillon",
            "en_review": "En Review",
            "publie": "Publié",
            "rejete": "Rejeté"
        },
        "toasts": {
            "created": "Élément créé",
            "submitted": "Soumis pour validation",
            "contentAdded": "Contenu ajouté",
            "modified": "Élément modifié"
        },
        "btn": {
            "submit": "Soumettre",
            "addContent": "Ajouter contenu",
            "edit": "Modifier",
            "cancel": "Annuler",
            "create": "Créer",
            "save": "Enregistrer"
        },
        "modal": {
            "createTitle": "Nouvel Élément",
            "editTitle": "Modifier",
            "addContentTitle": "Ajouter contenu",
            "workflowTitle": "Workflow"
        },
        "fields": {
            "title": "Titre",
            "description": "Description (optionnel)",
            "lessonId": "Lecon ID (optionnel)",
            "difficulty": "Difficulté",
            "htmlContent": "Contenu HTML",
            "videoUrl": "URL vidéo",
            "duration": "Durée (secondes)",
            "quizSoon": "Formulaire quiz à venir"
        },
        "difficulty": {
            "facile": "Facile",
            "moyen": "Moyen",
            "difficile": "Difficile"
        },
        "types": {
            "texte": "Texte",
            "video": "Vidéo",
            "image": "Image",
            "quiz": "Quiz"
        },
        "workflow": {
            "noTransitions": "Aucune transition enregistrée"
        }
    },
    "validation": {
        "title": "Validation",
        "titleSuffix": "Pédagogique",
        "subtitle": "Valider ou rejeter les contenus de votre périmètre pédagogique",
        "stats": {
            "total": "Total",
            "pending": "En attente",
            "validated": "Validés",
            "rejected": "Rejetés"
        },
        "filters": {
            "all": "Tous",
            "pending": "En attente",
            "validated": "Validés",
            "rejected": "Rejetés"
        },
        "loading": "Chargement...",
        "error": "Erreur de connexion. Veuillez réessayer.",
        "noResults": "Aucun contenu à afficher",
        "noResultsDesc": "Vous n'avez aucun contenu dans votre périmètre",
        "table": {
            "id": "ID",
            "notion": "Notion",
            "level": "Niveau",
            "type": "Type",
            "status": "Statut",
            "actions": "Actions"
        },
        "badges": {
            "validated": "Validé",
            "rejected": "Rejeté",
            "pending": "En attente"
        },
        "toasts": {
            "validated": "Contenu validé",
            "validateError": "Erreur réseau",
            "rejected": "Contenu rejeté",
            "rejectError": "Erreur réseau"
        },
        "btn": {
            "validate": "Valider",
            "reject": "Rejeter"
        },
        "rejectModal": {
            "title": "Rejeter le contenu",
            "message": "Rejeter le contenu ?",
            "description": "Le contenu repassera en statut \"À valider\".",
            "commentLabel": "Commentaire de rejet (obligatoire)",
            "commentPlaceholder": "Expliquez la raison du rejet...",
            "cancel": "Annuler",
            "confirm": "Rejeter"
        }
    },
    "abonnements": {
        "title": "Mes",
        "titleSuffix": "Abonnements",
        "subtitle": "Gérez vos abonnements et découvrez les packs disponibles",
        "mySubscriptions": "Mes abonnements",
        "noActive": "Aucun abonnement actif",
        "availablePacks": "Packs disponibles",
        "loading": "Chargement...",
        "noPacks": "Aucun pack disponible",
        "tiers": {
            "gratuit": "Gratuit",
            "basique": "Basique"
        },
        "features": {
            "level": "Niveau",
            "aiQuestions": "AI Questions",
            "included": "Inclus",
            "aiQuiz": "AI Quiz"
        },
        "badges": {
            "subscribed": "Abonné"
        },
        "btn": {
            "upgrade": "Upgrade",
            "cancel": "Annuler",
            "subscribe": "Souscrire",
            "confirm": "Confirmer"
        },
        "gracePeriod": "Période de grâce",
        "toasts": {
            "created": "Abonnement créé !",
            "networkError": "Erreur réseau",
            "upgraded": "Upgrade effectué !",
            "cancelled": "Abonnement annulé (grâce 7 jours)"
        },
        "confirmModal": {
            "subscribeTitle": "Souscrire à ce pack ?",
            "upgradeTitle": "Upgrade cet abonnement ?",
            "cancelTitle": "Annuler cet abonnement ?",
            "cancelMessage": "L'annulation prendra effet à la fin de la période de grâce (7 jours).",
            "upgradeMessage": "Le pack sera activé immédiatement.",
            "subscribeMessage": "Le changement de tier sera appliqué.",
            "cancel": "Annuler",
            "confirm": "Confirmer"
        }
    },
    "parcours": {
        "title": "Parcours",
        "subtitle": "Créez et gérez vos parcours pédagogiques",
        "newParcours": "Nouveau Parcours",
        "loading": "Chargement...",
        "noResults": "Aucun parcours. Créez-en un pour commencer.",
        "chapters": "chapitres",
        "btn": {
            "addParagraph": "Ajouter un paragraphe",
            "addLesson": "Ajouter une leçon",
            "addChapter": "Ajouter un chapitre",
            "cancel": "Annuler",
            "save": "Enregistrer"
        },
        "modal": {
            "editTitle": "Modifier",
            "createTitle": "Créer"
        },
        "fields": {
            "title": "Titre",
            "subject": "Matière",
            "level": "Niveau scolaire",
            "description": "Description",
            "content": "Contenu"
        },
        "toasts": {
            "created": "Parcours créé",
            "modified": "Modifié"
        }
    },
    "bibliotheque": {
        "title": "Bibliothèque",
        "titleSuffix": "Pédagogique",
        "subtitle": "Recherchez des contenus et compétences",
        "tabs": {
            "search": "Recherche",
            "skills": "Compétences"
        },
        "searchPlaceholder": "Rechercher un contenu...",
        "searchButton": "Rechercher",
        "searching": "Recherche en cours...",
        "noResults": "Aucun résultat",
        "noResultsHint": "Entrez un terme de recherche",
        "globalBadge": "Global",
        "noSkills": "Aucune compétence disponible"
    },
    "reorientation": {
        "title": "Réorientations",
        "titleSuffix": "en attente",
        "subtitle": "Validez ou annulez les changements de niveau automatiques de vos élèves",
        "loading": "Chargement...",
        "accessDenied": "Vous devez être désigné Responsable Pédagogique pour voir les réorientations.",
        "noResults": "Aucune notification de réorientation disponible.",
        "noPending": "Aucune réorientation en attente",
        "profile": "Profil #",
        "student": "Élève #",
        "notifiedOn": "Notifié le",
        "expiredSilence": "Expiré (silence = accepté)",
        "deadline": "Deadline:",
        "btn": {
            "confirm": "Confirmer",
            "cancel": "Annuler"
        },
        "badges": {
            "confirmed": "Confirmé",
            "cancelled": "Annulé"
        },
        "toasts": {
            "confirmed": "Réorientation confirmée",
            "cancelled": "Réorientation annulée",
            "error": "Erreur"
        }
    },
    "sales": {
        "title": "Mes",
        "titleSuffix": "Revenus",
        "subtitle": "Consultez vos ventes et revenus",
        "accessDenied": "Fonctionnalité réservée",
        "accessDeniedMessage": "Vous devez être enseignant pour accéder à cette page.",
        "kpi": {
            "totalSales": "Total ventes",
            "totalRevenue": "Revenu total",
            "avgPerSale": "Moyenne par vente"
        },
        "historyTitle": "Historique des ventes",
        "loading": "Chargement...",
        "noResults": "Aucune vente enregistrée",
        "table": {
            "id": "ID",
            "course": "Cours",
            "amountPaid": "Montant payé",
            "commission": "Commission",
            "revenue": "Votre revenu",
            "date": "Date"
        },
        "error": "Erreur de connexion"
    },
    "wallet": {
        "title": "Mon",
        "titleSuffix": "Portefeuille",
        "subtitle": "Crédits IA et historique d'utilisation",
        "noCredits": "Aucun crédit IA",
        "noCreditsDesc": "Vous n'avez pas encore de crédits IA. Contactez votre école ou achetez des crédits.",
        "aiCredits": "Crédits IA",
        "tokens": "Tokens",
        "detailBySource": "Détail par source",
        "expiresOn": "expire le",
        "credits": "crédits",
        "recentHistory": "Historique récent",
        "loading": "Chargement...",
        "noTransactions": "Aucune transaction",
        "pools": {
            "trial": "Essai",
            "subscription": "Abonnement",
            "school": "École",
            "purchased": "Acheté",
            "dt_purchased": "DT Achetés"
        }
    },
    "classroom": {
        "title": "Classroom",
        "titleSuffix": "Manager",
        "subtitle": "Gérez vos classes",
        "newClass": "Nouvelle Classe",
        "myClasses": "Mes Classes",
        "loading": "Chargement...",
        "noClasses": "Aucune classe",
        "createFirst": "Créer une classe",
        "students": "élèves",
        "coursesCount": "cours",
        "selectClass": "Sélectionnez une classe pour voir les détails",
        "studentsTitle": "Élèves",
        "addStudent": "Ajouter élève",
        "noStudents": "Aucun élève dans cette classe",
        "confirmDelete": "Supprimer cette classe?",
        "modal": {
            "createTitle": "Nouvelle Classe",
            "namePlaceholder": "Nom de la classe...",
            "descPlaceholder": "Description (optionnel)...",
            "cancel": "Annuler",
            "create": "Créer"
        }
    },
    "addStudent": {
        "title": "Ajouter un élève",
        "searchPlaceholder": "Rechercher par nom ou email...",
        "searching": "Recherche en cours...",
        "noResults": "Aucun élève trouvé",
        "hint": "Tapez au moins 2 caractères pour rechercher",
        "addButton": "Ajouter",
        "closeButton": "Fermer"
    },
    "learning": {
        "title": "Mon",
        "titleSuffix": "Apprentissage",
        "subtitle": "Vos cours créés et le catalogue disponible",
        "myCourses": "Mes Cours Créés",
        "noCourses": "Vous n'avez pas encore créé de cours",
        "searchPlaceholder": "Rechercher une formation...",
        "categories": {
            "all": "Toutes catégories",
            "pedagogie": "Pédagogie",
            "technologie": "Technologie",
            "gestion": "Gestion"
        },
        "loading": "Chargement...",
        "noResults": "Aucune formation trouvée",
        "modules": "modules",
        "minutes": "min",
        "free": "Gratuit",
        "viewCourse": "Voir le cours"
    }
}

parent_fr = {
    "childDetail": {
        "detachConfirm": "Voulez-vous vraiment détacher cet enfant ?",
        "rechargeError": "Erreur lors de la recharge",
        "levelUndefined": "Niveau non défini",
        "tabs": {
            "wallet": "Portefeuille",
            "pack": "Pack"
        },
        "detachButton": "Détacher",
        "walletBalance": "Solde portefeuille",
        "rechargeButton": "Recharger",
        "packLabel": "Pack",
        "activePacks": "actif",
        "activePacksPlural": "actifs",
        "badges": "Badge",
        "badgesPlural": "s",
        "avgScore": "Score moyen",
        "rechargeTitle": "Recharger le portefeuille de",
        "rechargeDesc": "Le solde DT est utilisé pour accéder au contenu premium (cours, quiz IA, exercices).",
        "amountPlaceholder": "Montant personnalisé (TND)",
        "payButton": "Payer via Konnect",
        "cancelButton": "Annuler",
        "activePacksTitle": "Packs Actifs",
        "packNumber": "Pack #",
        "validUntil": "Valide jusqu'au",
        "objectives": "Objectifs",
        "objectivePrefix": "objectif:",
        "badgesObtained": "Badges Obtenus",
        "recentScores": "Scores Récents",
        "chapterPrefix": "Chapitre #"
    },
    "wallet": {
        "title": "Portefeuille de",
        "subtitle": "Solde de crédits IA et rechargement",
        "aiCredits": "Crédits IA",
        "dtPurchased": "DT Achetés",
        "activePacks": "Packs actifs",
        "rechargeTitle": "Recharger le portefeuille",
        "redirecting": "Redirection vers Konnect pour le paiement...",
        "rechargeSuccess": "Recharge effectuée avec succès.",
        "networkError": "Erreur réseau.",
        "backToDashboard": "Retour au tableau de bord",
        "detailBySource": "Détail par source",
        "expiresOn": "expire le",
        "credits": "crédits",
        "noCredits": "Aucun crédit disponible.",
        "rechargeViaKonnect": "Recharger via Konnect",
        "redirectingShort": "Redirection...",
        "pools": {
            "trial": "Essai",
            "subscription": "Abonnement",
            "school": "École",
            "purchased": "Acheté",
            "dt_purchased": "DT Achetés"
        }
    },
    "messaging": {
        "title": "Messagerie",
        "newMessage": "Nouveau message",
        "cancel": "Annuler",
        "recipient": "Destinataire :",
        "recipientTeacher": "Professeur",
        "recipientAdmin": "Administration",
        "subjectPlaceholder": "Sujet",
        "messagePlaceholder": "Votre message...",
        "sending": "Envoi...",
        "sendButton": "Envoyer",
        "from": "De:",
        "noMessages": "Aucun message.",
        "toasts": {
            "sent": "Message envoyé !",
            "sendError": "Erreur lors de l'envoi"
        }
    },
    "famille": {
        "title": "Ma",
        "titleSuffix": "Famille",
        "subtitle": "Gérez vos enfants et bénéficiez des remises famille",
        "familyDiscounts": "Remises Famille",
        "familyAccount": "Compte famille",
        "linkedChildren": "enfants rattachés",
        "linkChild": "Rattacher un enfant",
        "childEmailPlaceholder": "Email de l'élève",
        "linking": "Liaison...",
        "linkButton": "Rattacher",
        "linkedChildrenTitle": "Enfants rattachés",
        "noLinkedChildren": "Aucun enfant rattaché.",
        "tableHeaders": {
            "rank": "Rang",
            "discount": "Remise"
        },
        "viewButton": "Voir",
        "discounts": {
            "first": "1er enfant",
            "firstRate": "0%",
            "firstLabel": "Tarif plein",
            "second": "2ème enfant",
            "secondRate": "-20%",
            "secondLabel": "Remise familiale",
            "third": "3ème enfant+",
            "thirdRate": "-25%",
            "thirdLabel": "Remise familiale maximale"
        },
        "toasts": {
            "linkedSuccess": "Enfant lié avec succès.",
            "networkError": "Erreur réseau.",
            "removed": "Enfant retiré.",
            "removeError": "Erreur réseau."
        },
        "removeConfirm": "Retirer cet enfant de la famille ?"
    },
    "pack": {
        "title": "Pack de",
        "subtitle": "Abonnement et configuration",
        "gracePeriod": "Période de grâce",
        "graceMessage": "Pack en période de grâce — expire dans",
        "graceDays": "jour(s)",
        "graceHint": "Souscrivez à un nouveau pack pour maintenir l'accès.",
        "activePack": "Pack Actif",
        "packLabel": "Pack",
        "accessLabel": "Accès",
        "expirationLabel": "Expiration",
        "availablePacksFor": "Packs disponibles pour",
        "levelLabel": "ce niveau",
        "backButton": "Retour",
        "activeStatus": "Actif",
        "subscribeButton": "Souscrire",
        "tiers": {
            "gratuit": "Gratuit",
            "basique": "Basique",
            "silver": "Silver",
            "golden": "Golden"
        },
        "features": {
            "freeQuota": "3 leçons / trimestre",
            "basicQuota": "2 matières au choix",
            "silverQuota": "4 matières au choix",
            "goldenQuota": "Accès illimité"
        }
    }
}

# EN additions
teacher_en = {
    "dashboard": {
        "title": "Dashboard",
        "welcome": "Welcome, ",
        "myCourses": "My Courses",
        "myClasses": "My Classes",
        "students": "Students",
        "aiCredits": "AI Credits",
        "quickAccess": "Quick Access",
        "aiStudio": "AI Studio",
        "revenue": "Revenue",
        "wallet": "Wallet",
        "viewAll": "View All",
        "eleves": "students",
        "cours": "courses"
    },
    "aiStudio": {
        "title": "AI",
        "titleSuffix": "Studio",
        "subtitle": "Generate educational content with AI",
        "tokens": "tokens",
        "contentType": "Content Type",
        "subject": "Subject",
        "level": "Level",
        "trimester": "Trimester",
        "description": "Description of desired content",
        "placeholder": "Describe what you want to generate... Ex: 'A homework on first-degree equations for 3rd year college students, including 5 exercises of progressive difficulty'",
        "estimatedCost": "Estimated cost: ~5 tokens",
        "generating": "Generating...",
        "generate": "Generate",
        "result": "Result",
        "copy": "Copy",
        "history": "History",
        "loading": "Loading...",
        "noHistory": "No history",
        "quickGenerations": "Quick generations",
        "error": "Connection error.",
        "subjects": {
            "mathematiques": "Mathematics",
            "physique": "Physics",
            "chimie": "Chemistry",
            "biologie": "Biology",
            "histoire": "History",
            "geographie": "Geography",
            "francais": "French",
            "anglais": "English",
            "informatique": "Computer Science",
            "pedagogie": "Pedagogy"
        },
        "levels": {
            "primaire": "Primary",
            "college": "Middle School",
            "lycee": "High School",
            "universite": "University"
        },
        "trimesters": {
            "t1": "Trimester 1",
            "t2": "Trimester 2",
            "t3": "Trimester 3"
        },
        "contentTypes": {
            "homework": "Homework",
            "lesson": "Lesson",
            "lesson_plan": "Lesson Plan",
            "outline": "Annual Outline",
            "quiz": "Quiz",
            "summary": "Summary"
        }
    },
    "elements": {
        "title": "Pedagogical",
        "titleSuffix": "Elements",
        "subtitle": "Create and manage your educational content",
        "newElement": "New Element",
        "loading": "Loading...",
        "noResults": "No elements found",
        "filters": {
            "all": "All",
            "brouillon": "Draft",
            "en_review": "In Review",
            "publie": "Published",
            "rejete": "Rejected"
        },
        "toasts": {
            "created": "Element created",
            "submitted": "Submitted for validation",
            "contentAdded": "Content added",
            "modified": "Element modified"
        },
        "btn": {
            "submit": "Submit",
            "addContent": "Add content",
            "edit": "Edit",
            "cancel": "Cancel",
            "create": "Create",
            "save": "Save"
        },
        "modal": {
            "createTitle": "New Element",
            "editTitle": "Edit",
            "addContentTitle": "Add content",
            "workflowTitle": "Workflow"
        },
        "fields": {
            "title": "Title",
            "description": "Description (optional)",
            "lessonId": "Lesson ID (optional)",
            "difficulty": "Difficulty",
            "htmlContent": "HTML Content",
            "videoUrl": "Video URL",
            "duration": "Duration (seconds)",
            "quizSoon": "Quiz form coming soon"
        },
        "difficulty": {
            "facile": "Easy",
            "moyen": "Medium",
            "difficile": "Hard"
        },
        "types": {
            "texte": "Text",
            "video": "Video",
            "image": "Image",
            "quiz": "Quiz"
        },
        "workflow": {
            "noTransitions": "No transitions recorded"
        }
    },
    "validation": {
        "title": "Pedagogical",
        "titleSuffix": "Validation",
        "subtitle": "Validate or reject content in your pedagogical scope",
        "stats": {
            "total": "Total",
            "pending": "Pending",
            "validated": "Validated",
            "rejected": "Rejected"
        },
        "filters": {
            "all": "All",
            "pending": "Pending",
            "validated": "Validated",
            "rejected": "Rejected"
        },
        "loading": "Loading...",
        "error": "Connection error. Please try again.",
        "noResults": "No content to display",
        "noResultsDesc": "You have no content in your scope",
        "table": {
            "id": "ID",
            "notion": "Notion",
            "level": "Level",
            "type": "Type",
            "status": "Status",
            "actions": "Actions"
        },
        "badges": {
            "validated": "Validated",
            "rejected": "Rejected",
            "pending": "Pending"
        },
        "toasts": {
            "validated": "Content validated",
            "validateError": "Network error",
            "rejected": "Content rejected",
            "rejectError": "Network error"
        },
        "btn": {
            "validate": "Validate",
            "reject": "Reject"
        },
        "rejectModal": {
            "title": "Reject content",
            "message": "Reject this content?",
            "description": "Content will return to \"To Validate\" status.",
            "commentLabel": "Rejection comment (required)",
            "commentPlaceholder": "Explain the reason for rejection...",
            "cancel": "Cancel",
            "confirm": "Reject"
        }
    },
    "abonnements": {
        "title": "My",
        "titleSuffix": "Subscriptions",
        "subtitle": "Manage your subscriptions and discover available packs",
        "mySubscriptions": "My subscriptions",
        "noActive": "No active subscription",
        "availablePacks": "Available packs",
        "loading": "Loading...",
        "noPacks": "No packs available",
        "tiers": {
            "gratuit": "Free",
            "basique": "Basic"
        },
        "features": {
            "level": "Level",
            "aiQuestions": "AI Questions",
            "included": "Included",
            "aiQuiz": "AI Quiz"
        },
        "badges": {
            "subscribed": "Subscribed"
        },
        "btn": {
            "upgrade": "Upgrade",
            "cancel": "Cancel",
            "subscribe": "Subscribe",
            "confirm": "Confirm"
        },
        "gracePeriod": "Grace Period",
        "toasts": {
            "created": "Subscription created!",
            "networkError": "Network error",
            "upgraded": "Upgrade completed!",
            "cancelled": "Subscription cancelled (7-day grace)"
        },
        "confirmModal": {
            "subscribeTitle": "Subscribe to this pack?",
            "upgradeTitle": "Upgrade this subscription?",
            "cancelTitle": "Cancel this subscription?",
            "cancelMessage": "Cancellation will take effect at the end of the grace period (7 days).",
            "upgradeMessage": "The pack will be activated immediately.",
            "subscribeMessage": "The tier change will be applied.",
            "cancel": "Cancel",
            "confirm": "Confirm"
        }
    },
    "parcours": {
        "title": "Pathways",
        "subtitle": "Create and manage your educational pathways",
        "newParcours": "New Pathway",
        "loading": "Loading...",
        "noResults": "No pathways. Create one to get started.",
        "chapters": "chapters",
        "btn": {
            "addParagraph": "Add a paragraph",
            "addLesson": "Add a lesson",
            "addChapter": "Add a chapter",
            "cancel": "Cancel",
            "save": "Save"
        },
        "modal": {
            "editTitle": "Edit",
            "createTitle": "Create"
        },
        "fields": {
            "title": "Title",
            "subject": "Subject",
            "level": "Grade Level",
            "description": "Description",
            "content": "Content"
        },
        "toasts": {
            "created": "Pathway created",
            "modified": "Modified"
        }
    },
    "bibliotheque": {
        "title": "Pedagogical",
        "titleSuffix": "Library",
        "subtitle": "Search for content and skills",
        "tabs": {
            "search": "Search",
            "skills": "Skills"
        },
        "searchPlaceholder": "Search content...",
        "searchButton": "Search",
        "searching": "Searching...",
        "noResults": "No results",
        "noResultsHint": "Enter a search term",
        "globalBadge": "Global",
        "noSkills": "No skills available"
    },
    "reorientation": {
        "title": "Reorientations",
        "titleSuffix": "pending",
        "subtitle": "Validate or cancel automatic level changes for your students",
        "loading": "Loading...",
        "accessDenied": "You must be designated as Pedagogical Lead to view reorientations.",
        "noResults": "No reorientation notifications available.",
        "noPending": "No pending reorientations",
        "profile": "Profile #",
        "student": "Student #",
        "notifiedOn": "Notified on",
        "expiredSilence": "Expired (silence = accepted)",
        "deadline": "Deadline:",
        "btn": {
            "confirm": "Confirm",
            "cancel": "Cancel"
        },
        "badges": {
            "confirmed": "Confirmed",
            "cancelled": "Cancelled"
        },
        "toasts": {
            "confirmed": "Reorientation confirmed",
            "cancelled": "Reorientation cancelled",
            "error": "Error"
        }
    },
    "sales": {
        "title": "My",
        "titleSuffix": "Revenue",
        "subtitle": "View your sales and revenue",
        "accessDenied": "Feature restricted",
        "accessDeniedMessage": "You must be a teacher to access this page.",
        "kpi": {
            "totalSales": "Total sales",
            "totalRevenue": "Total revenue",
            "avgPerSale": "Average per sale"
        },
        "historyTitle": "Sales History",
        "loading": "Loading...",
        "noResults": "No sales recorded",
        "table": {
            "id": "ID",
            "course": "Course",
            "amountPaid": "Amount paid",
            "commission": "Commission",
            "revenue": "Your revenue",
            "date": "Date"
        },
        "error": "Connection error"
    },
    "wallet": {
        "title": "My",
        "titleSuffix": "Wallet",
        "subtitle": "AI credits and usage history",
        "noCredits": "No AI credits",
        "noCreditsDesc": "You don't have AI credits yet. Contact your school or purchase credits.",
        "aiCredits": "AI Credits",
        "tokens": "Tokens",
        "detailBySource": "Detail by source",
        "expiresOn": "expires on",
        "credits": "credits",
        "recentHistory": "Recent history",
        "loading": "Loading...",
        "noTransactions": "No transactions",
        "pools": {
            "trial": "Trial",
            "subscription": "Subscription",
            "school": "School",
            "purchased": "Purchased",
            "dt_purchased": "DT Purchased"
        }
    },
    "classroom": {
        "title": "Classroom",
        "titleSuffix": "Manager",
        "subtitle": "Manage your classes",
        "newClass": "New Class",
        "myClasses": "My Classes",
        "loading": "Loading...",
        "noClasses": "No classes",
        "createFirst": "Create a class",
        "students": "students",
        "coursesCount": "courses",
        "selectClass": "Select a class to view details",
        "studentsTitle": "Students",
        "addStudent": "Add student",
        "noStudents": "No students in this class",
        "confirmDelete": "Delete this class?",
        "modal": {
            "createTitle": "New Class",
            "namePlaceholder": "Class name...",
            "descPlaceholder": "Description (optional)...",
            "cancel": "Cancel",
            "create": "Create"
        }
    },
    "addStudent": {
        "title": "Add a student",
        "searchPlaceholder": "Search by name or email...",
        "searching": "Searching...",
        "noResults": "No students found",
        "hint": "Type at least 2 characters to search",
        "addButton": "Add",
        "closeButton": "Close"
    },
    "learning": {
        "title": "My",
        "titleSuffix": "Learning",
        "subtitle": "Your created courses and available catalog",
        "myCourses": "My Created Courses",
        "noCourses": "You haven't created any courses yet",
        "searchPlaceholder": "Search training...",
        "categories": {
            "all": "All categories",
            "pedagogie": "Pedagogy",
            "technologie": "Technology",
            "gestion": "Management"
        },
        "loading": "Loading...",
        "noResults": "No training found",
        "modules": "modules",
        "minutes": "min",
        "free": "Free",
        "viewCourse": "View course"
    }
}

parent_en = {
    "childDetail": {
        "detachConfirm": "Are you sure you want to detach this child?",
        "rechargeError": "Error during recharge",
        "levelUndefined": "Level not defined",
        "tabs": {
            "wallet": "Wallet",
            "pack": "Pack"
        },
        "detachButton": "Detach",
        "walletBalance": "Wallet balance",
        "rechargeButton": "Recharge",
        "packLabel": "Pack",
        "activePacks": "active",
        "activePacksPlural": "active",
        "badges": "Badge",
        "badgesPlural": "s",
        "avgScore": "Average score",
        "rechargeTitle": "Recharge wallet of",
        "rechargeDesc": "DT balance is used to access premium content (courses, AI quizzes, exercises).",
        "amountPlaceholder": "Custom amount (TND)",
        "payButton": "Pay via Konnect",
        "cancelButton": "Cancel",
        "activePacksTitle": "Active Packs",
        "packNumber": "Pack #",
        "validUntil": "Valid until",
        "objectives": "Objectives",
        "objectivePrefix": "objective:",
        "badgesObtained": "Badges Earned",
        "recentScores": "Recent Scores",
        "chapterPrefix": "Chapter #"
    },
    "wallet": {
        "title": "Wallet of",
        "subtitle": "AI credits balance and recharge",
        "aiCredits": "AI Credits",
        "dtPurchased": "DT Purchased",
        "activePacks": "Active packs",
        "rechargeTitle": "Recharge wallet",
        "redirecting": "Redirecting to Konnect for payment...",
        "rechargeSuccess": "Recharge successful.",
        "networkError": "Network error.",
        "backToDashboard": "Back to dashboard",
        "detailBySource": "Detail by source",
        "expiresOn": "expires on",
        "credits": "credits",
        "noCredits": "No credits available.",
        "rechargeViaKonnect": "Recharge via Konnect",
        "redirectingShort": "Redirecting...",
        "pools": {
            "trial": "Trial",
            "subscription": "Subscription",
            "school": "School",
            "purchased": "Purchased",
            "dt_purchased": "DT Purchased"
        }
    },
    "messaging": {
        "title": "Messaging",
        "newMessage": "New message",
        "cancel": "Cancel",
        "recipient": "Recipient:",
        "recipientTeacher": "Teacher",
        "recipientAdmin": "Administration",
        "subjectPlaceholder": "Subject",
        "messagePlaceholder": "Your message...",
        "sending": "Sending...",
        "sendButton": "Send",
        "from": "From:",
        "noMessages": "No messages.",
        "toasts": {
            "sent": "Message sent!",
            "sendError": "Error sending message"
        }
    },
    "famille": {
        "title": "My",
        "titleSuffix": "Family",
        "subtitle": "Manage your children and benefit from family discounts",
        "familyDiscounts": "Family Discounts",
        "familyAccount": "Family account",
        "linkedChildren": "linked children",
        "linkChild": "Link a child",
        "childEmailPlaceholder": "Student email",
        "linking": "Linking...",
        "linkButton": "Link",
        "linkedChildrenTitle": "Linked children",
        "noLinkedChildren": "No children linked.",
        "tableHeaders": {
            "rank": "Rank",
            "discount": "Discount"
        },
        "viewButton": "View",
        "discounts": {
            "first": "1st child",
            "firstRate": "0%",
            "firstLabel": "Full price",
            "second": "2nd child",
            "secondRate": "-20%",
            "secondLabel": "Family discount",
            "third": "3rd child+",
            "thirdRate": "-25%",
            "thirdLabel": "Maximum family discount"
        },
        "toasts": {
            "linkedSuccess": "Child linked successfully.",
            "networkError": "Network error.",
            "removed": "Child removed.",
            "removeError": "Network error."
        },
        "removeConfirm": "Remove this child from the family?"
    },
    "pack": {
        "title": "Pack of",
        "subtitle": "Subscription and configuration",
        "gracePeriod": "Grace Period",
        "graceMessage": "Pack in grace period — expires in",
        "graceDays": "day(s)",
        "graceHint": "Subscribe to a new pack to maintain access.",
        "activePack": "Active Pack",
        "packLabel": "Pack",
        "accessLabel": "Access",
        "expirationLabel": "Expiration",
        "availablePacksFor": "Available packs for",
        "levelLabel": "this level",
        "backButton": "Back",
        "activeStatus": "Active",
        "subscribeButton": "Subscribe",
        "tiers": {
            "gratuit": "Free",
            "basique": "Basic",
            "silver": "Silver",
            "golden": "Golden"
        },
        "features": {
            "freeQuota": "3 lessons / trimester",
            "basicQuota": "2 subjects of your choice",
            "silverQuota": "4 subjects of your choice",
            "goldenQuota": "Unlimited access"
        }
    }
}

# AR additions
teacher_ar = {
    "dashboard": {
        "title": "لوحة التحكم",
        "welcome": "مرحباً، ",
        "myCourses": "دروسي",
        "myClasses": "فِئَاتي",
        "students": "الطلاب",
        "aiCredits": "ائتمانات الذكاء الاصطناعي",
        "quickAccess": "وصول سريع",
        "aiStudio": "استوديو الذكاء الاصطناعي",
        "revenue": "الإيرادات",
        "wallet": "المحفظة",
        "viewAll": "عرض الكل",
        "eleves": "طالب",
        "cours": "دورة"
    },
    "aiStudio": {
        "title": "الذكاء",
        "titleSuffix": "الاصطناعي",
        "subtitle": "توليد المحتوى التعليمي بالذكاء الاصطناعي",
        "tokens": "رموز",
        "contentType": "نوع المحتوى",
        "subject": "المادة",
        "level": "المستوى",
        "trimester": "الفصل",
        "description": "وصف المحتوى المطلوب",
        "placeholder": "صف ما تريد توليده... مثال: 'واجب عن المعادلات من الدرجة الأولى لطلاب السنة الثالثة إعدادي، يحتوي على 5 تمارين بمستويات تدريجية'",
        "estimatedCost": "التكلفة التقديرية: ~5 رموز",
        "generating": "جارٍ التوليد...",
        "generate": "توليد",
        "result": "النتيجة",
        "copy": "نسخ",
        "history": "السجل",
        "loading": "جارٍ التحميل...",
        "noHistory": "لا يوجد سجل",
        "quickGenerations": "توليدات سريعة",
        "error": "خطأ في الاتصال.",
        "subjects": {
            "mathematiques": "الرياضيات",
            "physique": "الفيزياء",
            "chimie": "الكيمياء",
            "biologie": "الأحياء",
            "histoire": "التاريخ",
            "geographie": "الجغرافيا",
            "francais": "الفرنسية",
            "anglais": "الإنجليزية",
            "informatique": "علوم الحاسوب",
            "pedagogie": "التربية"
        },
        "levels": {
            "primaire": "ابتدائي",
            "college": "إعدادي",
            "lycee": "ثانوي",
            "universite": "جامعي"
        },
        "trimesters": {
            "t1": "الفصل الأول",
            "t2": "الفصل الثاني",
            "t3": "الفصل الثالث"
        },
        "contentTypes": {
            "homework": "واجب",
            "lesson": "درس",
            "lesson_plan": "خطة الدرس",
            "outline": "المخطط السنوي",
            "quiz": "اختبار",
            "summary": "ملخص"
        }
    },
    "elements": {
        "title": "العناصر",
        "titleSuffix": "التربوية",
        "subtitle": "إنشاء وإدارة محتواك التعليمي",
        "newElement": "عنصر جديد",
        "loading": "جارٍ التحميل...",
        "noResults": "لم يتم العثور على عناصر",
        "filters": {
            "all": "الكل",
            "brouillon": "مسودة",
            "en_review": "قيد المراجعة",
            "publie": "منشور",
            "rejete": "مرفوض"
        },
        "toasts": {
            "created": "تم إنشاء العنصر",
            "submitted": "أُرسل للمراجعة",
            "contentAdded": "تمت إضافة المحتوى",
            "modified": "تم تعديل العنصر"
        },
        "btn": {
            "submit": "إرسال",
            "addContent": "إضافة محتوى",
            "edit": "تعديل",
            "cancel": "إلغاء",
            "create": "إنشاء",
            "save": "حفظ"
        },
        "modal": {
            "createTitle": "عنصر جديد",
            "editTitle": "تعديل",
            "addContentTitle": "إضافة محتوى",
            "workflowTitle": "سير العمل"
        },
        "fields": {
            "title": "العنوان",
            "description": "الوصف (اختياري)",
            "lessonId": "معرّف الدرس (اختياري)",
            "difficulty": "الصعوبة",
            "htmlContent": "المحتوى HTML",
            "videoUrl": "رابط الفيديو",
            "duration": "المدة (ثوانٍ)",
            "quizSoon": "استمارة الاختبار قادمة قريباً"
        },
        "difficulty": {
            "facile": "سهل",
            "moyen": "متوسط",
            "difficile": "صعب"
        },
        "types": {
            "texte": "نص",
            "video": "فيديو",
            "image": "صورة",
            "quiz": "اختبار"
        },
        "workflow": {
            "noTransitions": "لا توجد انتقالات مسجلة"
        }
    },
    "validation": {
        "title": "المراجعة",
        "titleSuffix": "التربوية",
        "subtitle": "التحقق أو رفض المحتوى في نطاقك التربوي",
        "stats": {
            "total": "الإجمالي",
            "pending": "قيد الانتظار",
            "validated": "تم التحقق",
            "rejected": "مرفوض"
        },
        "filters": {
            "all": "الكل",
            "pending": "قيد الانتظار",
            "validated": "تم التحقق",
            "rejected": "مرفوض"
        },
        "loading": "جارٍ التحميل...",
        "error": "خطأ في الاتصال. يرجى المحاولة مرة أخرى.",
        "noResults": "لا يوجد محتوى لعرضه",
        "noResultsDesc": "ليس لديك أي محتوى في نطاقك",
        "table": {
            "id": "المعرّف",
            "notion": "مفهوم",
            "level": "المستوى",
            "type": "النوع",
            "status": "الحالة",
            "actions": "الإجراءات"
        },
        "badges": {
            "validated": "تم التحقق",
            "rejected": "مرفوض",
            "pending": "قيد الانتظار"
        },
        "toasts": {
            "validated": "تم التحقق من المحتوى",
            "validateError": "خطأ في الشبكة",
            "rejected": "تم رفض المحتوى",
            "rejectError": "خطأ في الشبكة"
        },
        "btn": {
            "validate": "تحقق",
            "reject": "رفض"
        },
        "rejectModal": {
            "title": "رفض المحتوى",
            "message": "رفض هذا المحتوى؟",
            "description": "سيعود المحتوى إلى حالة \"المطلوب التحقق\".",
            "commentLabel": "تعليق الرفض (مطلوب)",
            "commentPlaceholder": "اشرح سبب الرفض...",
            "cancel": "إلغاء",
            "confirm": "رفض"
        }
    },
    "abonnements": {
        "title": "اشتراكاتي",
        "titleSuffix": "",
        "subtitle": "إدارة اشتراكاتك واكتشاف الباقات المتاحة",
        "mySubscriptions": "اشتراكاتي",
        "noActive": "لا يوجد اشتراك نشط",
        "availablePacks": "الباقات المتاحة",
        "loading": "جارٍ التحميل...",
        "noPacks": "لا توجد باقات متاحة",
        "tiers": {
            "gratuit": "مجاني",
            "basique": "أساسي"
        },
        "features": {
            "level": "المستوى",
            "aiQuestions": "أسئلة الذكاء الاصطناعي",
            "included": "مشمول",
            "aiQuiz": "اختبار الذكاء الاصطناعي"
        },
        "badges": {
            "subscribed": "مشترك"
        },
        "btn": {
            "upgrade": "ترقية",
            "cancel": "إلغاء",
            "subscribe": "اشتراك",
            "confirm": "تأكيد"
        },
        "gracePeriod": "فترة السماح",
        "toasts": {
            "created": "تم إنشاء الاشتراك!",
            "networkError": "خطأ في الشبكة",
            "upgraded": "تمت الترقية!",
            "cancelled": "تم إلغاء الاشتراك (فترة سماح 7 أيام)"
        },
        "confirmModal": {
            "subscribeTitle": "الاشتراك في هذه الباقة؟",
            "upgradeTitle": "ترقية هذا الاشتراك؟",
            "cancelTitle": "إلغاء هذا الاشتراك؟",
            "cancelMessage": "سيتم الإلغاء في نهاية فترة السماح (7 أيام).",
            "upgradeMessage": "سيتم تفعيل الباقة فوراً.",
            "subscribeMessage": "سيتم تطبيق تغيير المستوى.",
            "cancel": "إلغاء",
            "confirm": "تأكيد"
        }
    },
    "parcours": {
        "title": "المسارات",
        "subtitle": "إنشاء وإدارة مساراتك التعليمية",
        "newParcours": "مسار جديد",
        "loading": "جارٍ التحميل...",
        "noResults": "لا توجد مسارات. أنشئ مساراً للبدء.",
        "chapters": "فصول",
        "btn": {
            "addParagraph": "إضافة فقرة",
            "addLesson": "إضافة درس",
            "addChapter": "إضافة فصل",
            "cancel": "إلغاء",
            "save": "حفظ"
        },
        "modal": {
            "editTitle": "تعديل",
            "createTitle": "إنشاء"
        },
        "fields": {
            "title": "العنوان",
            "subject": "المادة",
            "level": "المستوى الدراسي",
            "description": "الوصف",
            "content": "المحتوى"
        },
        "toasts": {
            "created": "تم إنشاء المسار",
            "modified": "تم التعديل"
        }
    },
    "bibliotheque": {
        "title": "المكتبة",
        "titleSuffix": "التربوية",
        "subtitle": "البحث عن المحتوى والمهارات",
        "tabs": {
            "search": "بحث",
            "skills": "المهارات"
        },
        "searchPlaceholder": "البحث عن محتوى...",
        "searchButton": "بحث",
        "searching": "جارٍ البحث...",
        "noResults": "لا توجد نتائج",
        "noResultsHint": "أدخل مصطلح البحث",
        "globalBadge": "عام",
        "noSkills": "لا توجد مهارات متاحة"
    },
    "reorientation": {
        "title": "الإحالات",
        "titleSuffix": "قيد الانتظار",
        "subtitle": "التحقق أو إلغاء تغييرات المستوى التلقائية لطلابك",
        "loading": "جارٍ التحميل...",
        "accessDenied": "يجب تعيينك مسؤولاً تربوياً لعرض الإحالات.",
        "noResults": "لا توجد إشعارات إحالة متاحة.",
        "noPending": "لا توجد إحالات قيد الانتظار",
        "profile": "الملف #",
        "student": "الطالب #",
        "notifiedOn": "تم الإشعار في",
        "expiredSilence": "منتهي (الصمت = مقبول)",
        "deadline": "الموعد النهائي:",
        "btn": {
            "confirm": "تأكيد",
            "cancel": "إلغاء"
        },
        "badges": {
            "confirmed": "مؤكد",
            "cancelled": "ملغي"
        },
        "toasts": {
            "confirmed": "تم تأكيد الإحالة",
            "cancelled": "تم إلغاء الإحالة",
            "error": "خطأ"
        }
    },
    "sales": {
        "title": "إيراداتي",
        "titleSuffix": "",
        "subtitle": "عرض مبيعاتك وإيراداتك",
        "accessDenied": "ميزة مقيدة",
        "accessDeniedMessage": "يجب أن تكون معلماً للوصول إلى هذه الصفحة.",
        "kpi": {
            "totalSales": "إجمالي المبيعات",
            "totalRevenue": "إجمالي الإيرادات",
            "avgPerSale": "المتوسط لكل عملية"
        },
        "historyTitle": "سجل المبيعات",
        "loading": "جارٍ التحميل...",
        "noResults": "لا توجد مبيعات مسجلة",
        "table": {
            "id": "المعرّف",
            "course": "الدورة",
            "amountPaid": "المبلغ المدفوع",
            "commission": "العمولة",
            "revenue": "إيرادك",
            "date": "التاريخ"
        },
        "error": "خطأ في الاتصال"
    },
    "wallet": {
        "title": "محفظتي",
        "titleSuffix": "",
        "subtitle": "ائتمانات الذكاء الاصطناعي وسجل الاستخدام",
        "noCredits": "لا توجد ائتمانات ذكاء اصطناعي",
        "noCreditsDesc": "ليس لديك ائتمانات ذكاء اصطناعي بعد. اتصل بمدرستك أو اشترِ ائتمانات.",
        "aiCredits": "ائتمانات الذكاء الاصطناعي",
        "tokens": "الرموز",
        "detailBySource": "التفاصيل حسب المصدر",
        "expiresOn": "تنتهي في",
        "credits": "ائتمان",
        "recentHistory": "السجل الأخير",
        "loading": "جارٍ التحميل...",
        "noTransactions": "لا توجد معاملات",
        "pools": {
            "trial": "تجريبي",
            "subscription": "اشتراك",
            "school": "المدرسة",
            "purchased": "مشتراة",
            "dt_purchased": "دينار مشتراة"
        }
    },
    "classroom": {
        "title": "الصف",
        "titleSuffix": "الإداري",
        "subtitle": "إدارة فِئَاتك",
        "newClass": "فِئَة جديدة",
        "myClasses": "فِئَاتي",
        "loading": "جارٍ التحميل...",
        "noClasses": "لا توجد فِئَات",
        "createFirst": "إنشاء فِئَة",
        "students": "طالب",
        "coursesCount": "دورة",
        "selectClass": "اختر فِئَة لعرض التفاصيل",
        "studentsTitle": "الطلاب",
        "addStudent": "إضافة طالب",
        "noStudents": "لا يوجد طلاب في هذه الفِئَة",
        "confirmDelete": "حذف هذه الفِئَة؟",
        "modal": {
            "createTitle": "فِئَة جديدة",
            "namePlaceholder": "اسم الفِئَة...",
            "descPlaceholder": "الوصف (اختياري)...",
            "cancel": "إلغاء",
            "create": "إنشاء"
        }
    },
    "addStudent": {
        "title": "إضافة طالب",
        "searchPlaceholder": "بحث بالاسم أو البريد...",
        "searching": "جارٍ البحث...",
        "noResults": "لم يتم العثور على طلاب",
        "hint": "اكتب حرفين على الأقل للبحث",
        "addButton": "إضافة",
        "closeButton": "إغلاق"
    },
    "learning": {
        "title": "تعلمي",
        "titleSuffix": "",
        "subtitle": "دوراتك المنشأة والكتالوج المتاح",
        "myCourses": "دوراتي المنشأة",
        "noCourses": "لم تنشئ أي دورة بعد",
        "searchPlaceholder": "البحث عن تدريب...",
        "categories": {
            "all": "جميع الفئات",
            "pedagogie": "التربية",
            "technologie": "التكنولوجيا",
            "gestion": "الإدارة"
        },
        "loading": "جارٍ التحميل...",
        "noResults": "لم يتم العثور على تدريب",
        "modules": "وحدات",
        "minutes": "دقيقة",
        "free": "مجاني",
        "viewCourse": "عرض الدورة"
    }
}

parent_ar = {
    "childDetail": {
        "detachConfirm": "هل أنت متأكد من فصل هذا الطفل؟",
        "rechargeError": "خطأ أثناء الشحن",
        "levelUndefined": "المستوى غير محدد",
        "tabs": {
            "wallet": "المحفظة",
            "pack": "الباقة"
        },
        "detachButton": "فصل",
        "walletBalance": "رصيد المحفظة",
        "rechargeButton": "شحن",
        "packLabel": "الباقة",
        "activePacks": "نشط",
        "activePacksPlural": "نشط",
        "badges": "شارة",
        "badgesPlural": "ة",
        "avgScore": "متوسط الدرجات",
        "rechargeTitle": "شحن محفظة",
        "rechargeDesc": "يُستخدم رصيد الدينار للوصول إلى المحتوى المميز (الدروس، اختبارات الذكاء الاصطناعي، التمارين).",
        "amountPlaceholder": "المبلغ المخصص (دينار تونسي)",
        "payButton": "الدفع عبر Konnect",
        "cancelButton": "إلغاء",
        "activePacksTitle": "الباقات النشطة",
        "packNumber": "الباقة #",
        "validUntil": "صالحة حتى",
        "objectives": "الأهداف",
        "objectivePrefix": "هدف:",
        "badgesObtained": "الشارات المحصل عليها",
        "recentScores": "الدرجات الأخيرة",
        "chapterPrefix": "الفصل #"
    },
    "wallet": {
        "title": "محفظة",
        "subtitle": "رصيد ائتمانات الذكاء الاصطناعي والشحن",
        "aiCredits": "ائتمانات الذكاء الاصطناعي",
        "dtPurchased": "دينار مشتراة",
        "activePacks": "الباقات النشطة",
        "rechargeTitle": "شحن المحفظة",
        "redirecting": "جارٍ التحويل إلى Konnect للدفع...",
        "rechargeSuccess": "تم الشحن بنجاح.",
        "networkError": "خطأ في الشبكة.",
        "backToDashboard": "العودة للوحة التحكم",
        "detailBySource": "التفاصيل حسب المصدر",
        "expiresOn": "تنتهي في",
        "credits": "ائتمان",
        "noCredits": "لا توجد ائتمانات متاحة.",
        "rechargeViaKonnect": "شحن عبر Konnect",
        "redirectingShort": "جارٍ التحويل...",
        "pools": {
            "trial": "تجريبي",
            "subscription": "اشتراك",
            "school": "المدرسة",
            "purchased": "مشتراة",
            "dt_purchased": "دينار مشتراة"
        }
    },
    "messaging": {
        "title": "الرسائل",
        "newMessage": "رسالة جديدة",
        "cancel": "إلغاء",
        "recipient": "المستلم:",
        "recipientTeacher": "المعلم",
        "recipientAdmin": "الإدارة",
        "subjectPlaceholder": "الموضوع",
        "messagePlaceholder": "رسالتك...",
        "sending": "جارٍ الإرسال...",
        "sendButton": "إرسال",
        "from": "من:",
        "noMessages": "لا توجد رسائل.",
        "toasts": {
            "sent": "تم إرسال الرسالة!",
            "sendError": "خطأ في الإرسال"
        }
    },
    "famille": {
        "title": "عائلتي",
        "titleSuffix": "",
        "subtitle": "إدارة أطفالك والاستفادة من خصومات العائلة",
        "familyDiscounts": "خصومات العائلة",
        "familyAccount": "حساب العائلة",
        "linkedChildren": "أطفال مرتبطون",
        "linkChild": "ربط طفل",
        "childEmailPlaceholder": "بريد الطالب الإلكتروني",
        "linking": "جارٍ الربط...",
        "linkButton": "ربط",
        "linkedChildrenTitle": "الأطفال المرتبطون",
        "noLinkedChildren": "لا يوجد أطفال مرتبطون.",
        "tableHeaders": {
            "rank": "الترتيب",
            "discount": "الخصم"
        },
        "viewButton": "عرض",
        "discounts": {
            "first": "الطفل الأول",
            "firstRate": "0%",
            "firstLabel": "السعر الكامل",
            "second": "الطفل الثاني",
            "secondRate": "-20%",
            "secondLabel": "خصم العائلة",
            "third": "الطفل الثالث+",
            "thirdRate": "-25%",
            "thirdLabel": "خصم العائلة الأقصى"
        },
        "toasts": {
            "linkedSuccess": "تم ربط الطفل بنجاح.",
            "networkError": "خطأ في الشبكة.",
            "removed": "تم إزالة الطفل.",
            "removeError": "خطأ في الشبكة."
        },
        "removeConfirm": "إزالة هذا الطفل من العائلة؟"
    },
    "pack": {
        "title": "باقة",
        "subtitle": "الاشتراك والتكوين",
        "gracePeriod": "فترة السماح",
        "graceMessage": "الباقة في فترة السماح — تنتهي في",
        "graceDays": "يوم(أيام)",
        "graceHint": "اشترك في باقة جديدة للحفاظ على الوصول.",
        "activePack": "الباقة النشطة",
        "packLabel": "الباقة",
        "accessLabel": "الوصول",
        "expirationLabel": "انتهاء الصلاحية",
        "availablePacksFor": "الباقات المتاحة لـ",
        "levelLabel": "هذا المستوى",
        "backButton": "رجوع",
        "activeStatus": "نشط",
        "subscribeButton": "اشتراك",
        "tiers": {
            "gratuit": "مجاني",
            "basique": "أساسي",
            "silver": "فضي",
            "golden": "ذهبي"
        },
        "features": {
            "freeQuota": "3 دروس / فصل",
            "basicQuota": "2 مادة من اختيارك",
            "silverQuota": "4 مواد من اختيارك",
            "goldenQuota": "وصول غير محدود"
        }
    }
}

# Process each file
for locale, teacher_data, parent_data in [
    ("fr", teacher_fr, parent_fr),
    ("en", teacher_en, parent_en),
    ("ar", teacher_ar, parent_ar),
]:
    filepath = os.path.join(LOCALE_DIR, f"{locale}.json")
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    data["teacher"] = teacher_data
    data["parent"] = parent_data
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Updated {locale}.json")

print("Done!")
