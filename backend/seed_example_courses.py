"""
Seed script for EDUAI Learning Platform - Example Courses
Creates two complete courses:
1. Teacher course: "Pédagogie Numérique avec IA" (accessible to teachers)
2. Student course: "Mathématiques Fondamentales" (accessible to students)
Usage: python seed_example_courses.py
"""

import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("TESTING", "true")

from app.db import SessionLocal
from app.models import (
    School, User, Course, Module, Lesson, Quiz, QuizQuestion, QuizOption,
    CourseStatus, UserRole, CourseEnrollment, ContentType
)


def seed_courses():
    print("=" * 60)
    print("EDUAI Learning Platform - Example Courses Seed")
    print("=" * 60)

    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        # Get school and users
        school = db.query(School).filter(School.slug == "pro-school").first()
        if not school:
            print("ERROR: pro-school not found. Run seed.py first!")
            return

        teacher = db.query(User).filter(User.email == "teacher@pro-school.edu").first()
        student1 = db.query(User).filter(User.email == "student1@pro-school.edu").first()
        student2 = db.query(User).filter(User.email == "student2@pro-school.edu").first()

        if not teacher:
            print("ERROR: teacher@pro-school.edu not found. Run seed.py first!")
            return

        print(f"\nSchool: {school.name} (id={school.id})")
        print(f"Teacher: {teacher.email} (id={teacher.id})")

        # ========================================
        # COURSE 1: PÉDAGOGIE NUMÉRIQUE AVEC IA (Teachers)
        # ========================================
        print("\n" + "=" * 60)
        print("COURSE 1: Pédagogie Numérique avec IA (Teachers)")
        print("=" * 60)

        existing_teacher_course = db.query(Course).filter(
            Course.title == "Pédagogie Numérique avec IA"
        ).first()

        if not existing_teacher_course:
            course1 = Course(
                school_id=school.id,
                author_id=teacher.id,
                title="Pédagogie Numérique avec IA",
                short_description="Maîtrisez les outils d'IA pour révolutionner votre enseignement",
                description="Ce cours complet vous apprendra à intégrer l'intelligence artificielle dans vos pratiques pédagogiques. Découvrez comment personnaliser l'apprentissage, créer du contenu interactif, et évaluer efficacement vos élèves grâce aux outils modernes.",
                category="pedagogy",
                level="intermediate",
                language="fr",
                status=CourseStatus.PUBLISHED,
                is_published=True,
                price_tokens=100,
                price_dt=50.0,
                max_students=50,
                published_at=now,
                slug="pedagogie-numerique-ia",
                visibility="public",
                enrollment_type="open",
                tags=["IA", "pédagogie", "enseignement", "numérique"],
                learning_objectives="Intégrer l'IA dans l'enseignement\nCréer du contenu pédagogique personnalisé\nUtiliser les outils d'évaluation intelligente\nAnalyser les données d'apprentissage",
            )
            db.add(course1)
            db.flush()

            # Module 1: Introduction à l'IA en Éducation
            m1 = Module(course_id=course1.id, title="Introduction à l'IA en Éducation", description="Comprendre les fondamentaux de l'IA appliquée à l'enseignement", order=0)
            db.add(m1)
            db.flush()

            # Lesson 1.1: Qu'est-ce que l'IA pédagogique?
            l1_1 = Lesson(
                module_id=m1.id, school_id=school.id, teacher_id=teacher.id,
                title="Qu'est-ce que l'IA pédagogique?",
                description="Découvrez comment l'intelligence artificielle transforme l'éducation",
                lesson_type="text", content_type=ContentType.TEXT,
                content_text="""# L'IA dans l'Éducation

L'intelligence artificielle révolutionne le domaine de l'éducation en offrant de nouvelles possibilités pour personnaliser et améliorer l'apprentissage.

## Définitions Clés

**Intelligence Artificielle (IA)**: Technologie permettant aux machines de simuler l'intelligence humaine, y compris l'apprentissage, le raisonnement et l'auto-correction.

**IA Éducative**: Application spécifique de l'IA pour améliorer les processus d'enseignement et d'apprentissage.

## Les 5 Domaines Principaux

1. **Tutoring Intelligent** : Systèmes qui s'adaptent au niveau de chaque élève
2. **Évaluation Automatisée** : Correction et feedback instantanés
3. **Création de Contenu** : Génération automatique d'exercices et de quiz
4. **Analyse Prédictive** : Identification des élèves en difficulté
5. **Personnalisation** : Parcours d'apprentissage uniques

## Avantages pour l'Enseignant

- Gain de temps sur les tâches répétitives
- Meilleure compréhension des besoins individuels
- Outils créatifs pour concevoir des cours engageants
- Données précises pour prendre des décisions pédagogiques

## Tendances Actuelles

L'adoption de l'IA en éducation a augmenté de 47% en 2024, avec des outils comme ChatGPT, Claude et Gemini qui transforment la façon dont les enseignants préparent leurs cours et interagissent avec leurs élèves.""",
                content_html="<h1>L'IA dans l'Éducation</h1><p>L'intelligence artificielle révolutionne le domaine de l'éducation...</p>",
                video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                video_duration_seconds=900,
                order=0, duration_minutes=15, is_free=True,
            )
            db.add(l1_1)
            db.flush()

            # Quiz 1.1
            q1_1 = Quiz(lesson_id=l1_1.id, title="Quiz: Introduction à l'IA", description="Testez vos connaissances sur l'IA en éducation", passing_score_percent=70)
            db.add(q1_1)
            db.flush()

            # Question 1
            qq1 = QuizQuestion(quiz_id=q1_1.id, question_text="Quel est le principal avantage de l'IA en éducation?", question_type="mcq", points=2, order_index=0)
            db.add(qq1)
            db.flush()
            db.add_all([
                QuizOption(question_id=qq1.id, option_text="Remplacer les enseignants", is_correct=False, order_index=0),
                QuizOption(question_id=qq1.id, option_text="Personnaliser l'apprentissage", is_correct=True, order_index=1),
                QuizOption(question_id=qq1.id, option_text="Réduire le temps d'enseignement", is_correct=False, order_index=2),
                QuizOption(question_id=qq1.id, option_text="Éliminer les examens", is_correct=False, order_index=3),
            ])

            # Question 2
            qq2 = QuizQuestion(quiz_id=q1_1.id, question_text="Parmi ces domaines, lequel n'est PAS un domaine principal de l'IA éducative?", question_type="mcq", points=2, order_index=1)
            db.add(qq2)
            db.flush()
            db.add_all([
                QuizOption(question_id=qq2.id, option_text="Tutoring intelligent", is_correct=False, order_index=0),
                QuizOption(question_id=qq2.id, option_text="Gestion financière", is_correct=True, order_index=1),
                QuizOption(question_id=qq2.id, option_text="Évaluation automatisée", is_correct=False, order_index=2),
                QuizOption(question_id=qq2.id, option_text="Création de contenu", is_correct=False, order_index=3),
            ])

            # Lesson 1.2: Outils IA pour Enseignants
            l1_2 = Lesson(
                module_id=m1.id, school_id=school.id, teacher_id=teacher.id,
                title="Panorama des Outils IA pour Enseignants",
                description="Découvrez les meilleurs outils d'IA du moment",
                lesson_type="video", content_type=ContentType.VIDEO,
                content_text="""# Les Meilleurs Outils IA pour Enseignants en 2025

## Création de Contenu

### ChatGPT / Claude
- Génération de quiz et d'exercices
- Création de plans de cours
- Rédaction de commentaires pour élèves

### Canva AI
- Création de présentations visuelles
- Design de supports pédagogiques
- Infographies automatiques

## Évaluation et Feedback

### Gradescope
- Correction automatique des copies
- Analyse de la progression
- Rapports détaillés

### Turnitin AI
- Détection de plagiats
- Vérification de l'originalité

## Tutoring Intelligent

### Khan Academy (Khanmigo)
- Tutorat personnalisé
- Explications adaptées au niveau

### Duolingo Max
- Apprentissage des langues avec IA
- Conversation avec IA""",
                content_html="<h1>Les Meilleurs Outils IA pour Enseignants en 2025</h1>",
                video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                video_duration_seconds=1200,
                order=1, duration_minutes=20,
            )
            db.add(l1_2)
            db.flush()

            # Quiz 1.2
            q1_2 = Quiz(lesson_id=l1_2.id, title="Quiz: Outils IA", description="Quel outil pour quelle utilisation?", passing_score_percent=70)
            db.add(q1_2)
            db.flush()

            qq3 = QuizQuestion(quiz_id=q1_2.id, question_text="Quel outil est recommandé pour créer des présentations visuelles avec IA?", question_type="mcq", points=1, order_index=0)
            db.add(qq3)
            db.flush()
            db.add_all([
                QuizOption(question_id=qq3.id, option_text="Gradescope", is_correct=False, order_index=0),
                QuizOption(question_id=qq3.id, option_text="Canva AI", is_correct=True, order_index=1),
                QuizOption(question_id=qq3.id, option_text="Khan Academy", is_correct=False, order_index=2),
                QuizOption(question_id=qq3.id, option_text="Turnitin", is_correct=False, order_index=3),
            ])

            # Module 2: Création de Contenu Pédagogique avec IA
            m2 = Module(course_id=course1.id, title="Création de Contenu Pédagogique avec IA", description="Techniques avancées pour créer du contenu engageant", order=1)
            db.add(m2)
            db.flush()

            # Lesson 2.1: Générer des Quiz avec IA
            l2_1 = Lesson(
                module_id=m2.id, school_id=school.id, teacher_id=teacher.id,
                title="Générer des Quiz et Exercices avec IA",
                description="Créez des évaluations pertinentes en quelques clics",
                lesson_type="text", content_type=ContentType.TEXT,
                content_text="""# Créer des Quiz avec l'IA

## Méthodologie en 4 Étapes

### Étape 1: Définir les Objectifs
- Quelles compétences voulez-vous évaluer?
- Quel niveau de difficulté?
- Quel format (QCM, vrai/faux, questions ouvertes)?

### Étape 2: Rédiger le Prompt
Exemple de prompt efficace:
```
Crée un quiz de 5 questions sur les bases de Python pour des élèves de 2ème année.
Format: QCM avec 4 options chacune.
Niveau: débutant.
Inclus les réponses correctes et des explications.
```

### Étape 3: Vérifier et Ajuster
- Vérifiez l'exactitude des réponses
- Adaptez le vocabulaire à votre classe
- Ajoutez des contextes réels

### Étape 4: Intégrer dans votre Cours
- Exportez en format LMS
- Importez dans votre plateforme
- Testez avec un petit groupe

## Prompt Engineering pour Enseignants

| Élément | Description | Exemple |
|---------|-------------|---------|
| Contexte | Le cadre du cours | "Cours de SVT, chapitre 2" |
| Audience | Niveau des élèves | "Terminale, 17 ans" |
| Format | Type de sortie | "QCM, 4 options" |
| Difficulté | Niveau requis | "Moyen, application" |
| Quantité | Nombre d'éléments | "10 questions" |""",
                content_html="<h1>Créer des Quiz avec l'IA</h1>",
                order=0, duration_minutes=25, is_free=True,
            )
            db.add(l2_1)
            db.flush()

            # Quiz 2.1
            q2_1 = Quiz(lesson_id=l2_1.id, title="Quiz: Création de Quiz IA", description="Maîtrisez l'art de créer des quiz avec IA", passing_score_percent=80)
            db.add(q2_1)
            db.flush()

            qq4 = QuizQuestion(quiz_id=q2_1.id, question_text="Quelle est la première étape pour créer un quiz avec IA?", question_type="mcq", points=2, order_index=0)
            db.add(qq4)
            db.flush()
            db.add_all([
                QuizOption(question_id=qq4.id, option_text="Écrire le prompt directement", is_correct=False, order_index=0),
                QuizOption(question_id=qq4.id, option_text="Définir les objectifs pédagogiques", is_correct=True, order_index=1),
                QuizOption(question_id=qq4.id, option_text="Choisir l'outil IA", is_correct=False, order_index=2),
                QuizOption(question_id=qq4.id, option_text="Tester avec les élèves", is_correct=False, order_index=3),
            ])

            # Lesson 2.2: Créer des Cours Vidéo avec IA
            l2_2 = Lesson(
                module_id=m2.id, school_id=school.id, teacher_id=teacher.id,
                title="Créer des Cours Vidéo avec IA",
                description="Produisez des vidéos pédagogiques professionnelles",
                lesson_type="video", content_type=ContentType.VIDEO,
                content_text="""# Créer des Cours Vidéo avec IA

## Outils Recommandés

### Pour les Présentations Animées
- **Lumen5**: Transforme du texte en vidéos animées
- **Synthesia**: Avatar IA pour présenter le cours
- **HeyGen**: Vidéos avec présentateurs virtuels

### Pour l'Enregistrement d'Écran
- **Loom**: Enregistrement simple avec webcam
- **OBS Studio**: Gratuit et puissant

### Pour le Montage
- **Descript**: Montage basé sur le texte
- **CapCut**: Montage gratuit avec effets IA

## Processus de Création

1. **Script** : Rédigez le texte avec ChatGPT/Claude
2. **Storyboard** : Planifiez les visuels
3. **Enregistrement** : Capturez votre écran ou utilisez des avatars
4. **Montage** : Ajoutez musique, transitions, sous-titres
5. **Publication** : Exportez et intégrez au cours

## Conseils pour des Vidéos Engageantes

- Gardez les vidéos courtes (5-10 minutes)
- Utilisez des visuels variés
- Ajoutez des questions interactives
- Incluez des résumés à chaque fin de section""",
                content_html="<h1>Créer des Cours Vidéo avec IA</h1>",
                video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                video_duration_seconds=1800,
                order=1, duration_minutes=30,
            )
            db.add(l2_2)
            db.flush()

            # Module 3: Analyse et Suivi des Élèves
            m3 = Module(course_id=course1.id, title="Analyse et Suivi des Élèves", description="Utilisez les données pour améliorer vos résultats", order=2)
            db.add(m3)
            db.flush()

            # Lesson 3.1: Tableaux de Bord et Analytics
            l3_1 = Lesson(
                module_id=m3.id, school_id=school.id, teacher_id=teacher.id,
                title="Comprendre les Tableaux de Bord IA",
                description="Lisez et interprétez les données de vos élèves",
                lesson_type="text", content_type=ContentType.TEXT,
                content_text="""# Tableaux de Bord IA en Éducation

## Indicateurs Clés à Suivre

### Taux de Réussite
- Pourcentage d'élèves ayant atteint l'objectif
- Comparaison avant/après utilisation de l'IA

### Temps Moyen par Activité
- Durée d'apprentissage par chapitre
- Identification des sections difficiles

### Points de Difficulté
- Questions les plus ratées
- Concepts nécessitant des explications supplémentaires

### Engagement
- Taux de connexion
- Participation aux activités interactives

## Interprétation des Données

| Donnée | Signification | Action |
|--------|---------------|--------|
| < 50% réussite | Difficulté globale | Revoir la méthodologie |
| Temps > moyenne | Contenu trop long | Simplifier ou segmenter |
| Questions ratées | Concepts flous | Créer des exercices ciblés |
| Faible engagement | Motivation en baisse | Ajouter des activités ludiques

## Outils de Visualisation

- **Google Data Studio** : Graphiques interactifs
- **Power BI** : Tableaux de bord avancés
- **Outils intégrés** : Analytics des LMS modernes""",
                content_html="<h1>Tableaux de Bord IA en Éducation</h1>",
                order=0, duration_minutes=20,
            )
            db.add(l3_1)
            db.flush()

            # Final Quiz for Course 1
            q_final = Quiz(lesson_id=l3_1.id, title="Quiz Final: Pédagogie Numérique", description="Évaluation finale du cours", passing_score_percent=70)
            db.add(q_final)
            db.flush()

            qq5 = QuizQuestion(quiz_id=q_final.id, question_text="Quel est l'objectif principal de l'IA en pédagogie?", question_type="mcq", points=3, order_index=0)
            db.add(qq5)
            db.flush()
            db.add_all([
                QuizOption(question_id=qq5.id, option_text="Automatiser tout l'enseignement", is_correct=False, order_index=0),
                QuizOption(question_id=qq5.id, option_text="Assister l'enseignant et personnaliser l'apprentissage", is_correct=True, order_index=1),
                QuizOption(question_id=qq5.id, option_text="Remplacer les livres papier", is_correct=False, order_index=2),
                QuizOption(question_id=qq5.id, option_text="Réduire les coûts uniquement", is_correct=False, order_index=3),
            ])

            qq6 = QuizQuestion(quiz_id=q_final.id, question_text="Dans quelle situation l'IA est-elle le plus utile pour un enseignant?", question_type="mcq", points=3, order_index=1)
            db.add(qq6)
            db.flush()
            db.add_all([
                QuizOption(question_id=qq6.id, option_text="Pour surveiller les élèves", is_correct=False, order_index=0),
                QuizOption(question_id=qq6.id, option_text="Pour créer du contenu personnalisé et évaluer la progression", is_correct=True, order_index=1),
                QuizOption(question_id=qq6.id, option_text="Pour remplacer les réunions parents-professeurs", is_correct=False, order_index=2),
                QuizOption(question_id=qq6.id, option_text="Pour gérer l'administration scolaire", is_correct=False, order_index=3),
            ])

            db.commit()
            print(f"  [OK] Course '{course1.title}' created with 3 modules, 6 lessons, 4 quizzes")
        else:
            course1 = existing_teacher_course
            print(f"  Course '{course1.title}' already exists (id={course1.id})")

        # ========================================
        # COURSE 2: MATHÉMATIQUES FONDAMENTALES (Students)
        # ========================================
        print("\n" + "=" * 60)
        print("COURSE 2: Mathématiques Fondamentales (Students)")
        print("=" * 60)

        existing_student_course = db.query(Course).filter(
            Course.title == "Mathématiques Fondamentales"
        ).first()

        if not existing_student_course:
            course2 = Course(
                school_id=school.id,
                author_id=teacher.id,
                title="Mathématiques Fondamentales",
                short_description="Renforcez vos bases en mathématiques avec des exercices pratiques",
                description="Ce cours vous permettra de maîtriser les concepts essentiels des mathématiques: arithmétique, algèbre, géométrie et analyse. Chaque chapitre contient des vidéos explicatives, des exercices interactifs et des quiz pour valider vos acquis.",
                category="mathematics",
                level="beginner",
                language="fr",
                status=CourseStatus.PUBLISHED,
                is_published=True,
                price_tokens=75,
                price_dt=35.0,
                max_students=200,
                published_at=now,
                slug="mathematiques-fondamentales",
                visibility="public",
                enrollment_type="open",
                tags=["maths", "arithmétique", "algèbre", "géométrie"],
                learning_objectives="Maîtriser les opérations de base\nRésoudre des équations simples\nComprendre les figures géométriques\nDévelopper la logique mathématique",
            )
            db.add(course2)
            db.flush()

            # Module 1: Arithmétique
            m1 = Module(course_id=course2.id, title="Arithmétique de Base", description="Nombres, opérations et propriétés fondamentales", order=0)
            db.add(m1)
            db.flush()

            # Lesson 1.1: Les Nombres Naturels
            l1_1 = Lesson(
                module_id=m1.id, school_id=school.id, teacher_id=teacher.id,
                title="Les Nombres Naturels et leurs Opérations",
                description="Addition, soustraction, multiplication et division",
                lesson_type="video", content_type=ContentType.VIDEO,
                content_text="""# Les Nombres Naturels

## Définition
Les nombres naturels sont les nombres entiers positifs: 0, 1, 2, 3, 4, 5...

## Les 4 Opérations Fondamentales

### Addition (+)
- Propriété commutative: a + b = b + a
- Propriété associative: (a + b) + c = a + (b + c)
- Élément neutre: a + 0 = a

### Soustraction (-)
- Inverse de l'addition
- a - b = a + (-b)

### Multiplication (× ou ·)
- Propriété commutative: a × b = b × a
- Propriété distributive: a × (b + c) = a × b + a × c
- Élément neutre: a × 1 = a

### Division (÷ ou /)
- Inverse de la multiplication
- Diviseur ≠ 0
- a ÷ b = c si et seulement si a = b × c

## Exercices Pratiques

1. Calculez: 245 + 367
2. Quel est le résultat de: 12 × 15?
3. Simplifiez: (3 + 5) × 2
4. Vérifiez: 144 ÷ 12 = ?""",
                content_html="<h1>Les Nombres Naturels</h1>",
                video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                video_duration_seconds=600,
                order=0, duration_minutes=10, is_free=True,
            )
            db.add(l1_1)
            db.flush()

            # Quiz 1.1
            q1_1 = Quiz(lesson_id=l1_1.id, title="Quiz: Arithmétique", description="Testez vos compétences en calcul", passing_score_percent=60)
            db.add(q1_1)
            db.flush()

            qq1 = QuizQuestion(quiz_id=q1_1.id, question_text="Quel est le résultat de 15 × 12?", question_type="mcq", points=1, order_index=0)
            db.add(qq1)
            db.flush()
            db.add_all([
                QuizOption(question_id=qq1.id, option_text="160", is_correct=False, order_index=0),
                QuizOption(question_id=qq1.id, option_text="180", is_correct=True, order_index=1),
                QuizOption(question_id=qq1.id, option_text="170", is_correct=False, order_index=2),
                QuizOption(question_id=qq1.id, option_text="190", is_correct=False, order_index=3),
            ])

            qq2 = QuizQuestion(quiz_id=q1_1.id, question_text="Quelle est la propriété: a × (b + c) = a × b + a × c?", question_type="mcq", points=1, order_index=1)
            db.add(qq2)
            db.flush()
            db.add_all([
                QuizOption(question_id=qq2.id, option_text="Propriété commutative", is_correct=False, order_index=0),
                QuizOption(question_id=qq2.id, option_text="Propriété associative", is_correct=False, order_index=1),
                QuizOption(question_id=qq2.id, option_text="Propriété distributive", is_correct=True, order_index=2),
                QuizOption(question_id=qq2.id, option_text="Propriété de l'élément neutre", is_correct=False, order_index=3),
            ])

            # Lesson 1.2: Les Nombres Décimaux
            l1_2 = Lesson(
                module_id=m1.id, school_id=school.id, teacher_id=teacher.id,
                title="Les Nombres Décimaux",
                description="Comprendre et manipuler les nombres à virgule",
                lesson_type="text", content_type=ContentType.TEXT,
                content_text="""# Les Nombres Décimaux

## Définition
Un nombre décimal s'écrit avec une partie entière et une partie décimale séparées par une virgule.

Exemple: 3,14 (trois virgule quatorze)

## Représentation

### Sur une Droite Graduée
```
0     0,5     1     1,5     2
|------|------|------|------|
```

### Fractions Décimales
- 0,5 = 1/2
- 0,25 = 1/4
- 0,1 = 1/10
- 0,01 = 1/100

## Opérations sur les Décimaux

### Addition/Soustraction
Aligner les virgules:
```
  3,14
+ 2,56
------
  5,70
```

### Multiplication
1. Multiplier comme des entiers
2. Compter le nombre total de décimales
3. Placer la virgule

Exemple: 2,5 × 3,4 = 8,50

### Division
1. transformer le diviseur en entier
2. Déplacer la virgule du dividende du même nombre de places
3. Diviser normalement

## Exercices
1. Calculez: 4,56 + 2,78
2. Multipliez: 3,2 × 1,5
3. Divisez: 7,2 ÷ 1,2""",
                content_html="<h1>Les Nombres Décimaux</h1>",
                order=1, duration_minutes=20,
            )
            db.add(l1_2)
            db.flush()

            # Module 2: Algèbre
            m2 = Module(course_id=course2.id, title="Introduction à l'Algèbre", description="Variables, expressions et équations", order=1)
            db.add(m2)
            db.flush()

            # Lesson 2.1: Les Variables et Expressions
            l2_1 = Lesson(
                module_id=m2.id, school_id=school.id, teacher_id=teacher.id,
                title="Les Variables et Expressions Algébriques",
                description="Comprendre les lettres dans les mathématiques",
                lesson_type="video", content_type=ContentType.VIDEO,
                content_text="""# Variables et Expressions Algébriques

## Qu'est-ce qu'une Variable?
Une variable est une lettre qui représente un nombre inconnu ou variable.
On utilise souvent x, y, z, a, b, c...

## Expressions Algébriques

### Définition
Une expression algébrique est un ensemble de termes reliés par des opérations.

### Exemples
- 2x + 3 (deux fois x plus trois)
- a² - b² (a au carré moins b au carré)
- 3(x + y) (trois fois la somme de x et y)

## Évaluer une Expression

Pour évaluer 2x + 3 pour x = 5:
2(5) + 3 = 10 + 3 = 13

## Simplifier des Expressions

### Règles de Base
- Combiner les termes semblables: 3x + 2x = 5x
- Appliquer la distributivité: 2(x + 3) = 2x + 6
- Factoriser: x² - 9 = (x - 3)(x + 3)

## Exercices
1. Évaluez 4x - 7 pour x = 3
2. Simplifiez: 5a + 3a - 2a
3. Développez: 3(x + 2)""",
                content_html="<h1>Variables et Expressions Algébriques</h1>",
                video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                video_duration_seconds=900,
                order=0, duration_minutes=15,
            )
            db.add(l2_1)
            db.flush()

            # Quiz 2.1
            q2_1 = Quiz(lesson_id=l2_1.id, title="Quiz: Variables", description="Testez vos connaissances sur les variables", passing_score_percent=70)
            db.add(q2_1)
            db.flush()

            qq3 = QuizQuestion(quiz_id=q2_1.id, question_text="Si x = 4, quelle est la valeur de 2x + 5?", question_type="mcq", points=1, order_index=0)
            db.add(qq3)
            db.flush()
            db.add_all([
                QuizOption(question_id=qq3.id, option_text="9", is_correct=False, order_index=0),
                QuizOption(question_id=qq3.id, option_text="13", is_correct=True, order_index=1),
                QuizOption(question_id=qq3.id, option_text="11", is_correct=False, order_index=2),
                QuizOption(question_id=qq3.id, option_text="8", is_correct=False, order_index=3),
            ])

            # Lesson 2.2: Les Équations du 1er Degré
            l2_2 = Lesson(
                module_id=m2.id, school_id=school.id, teacher_id=teacher.id,
                title="Résoudre les Équations du 1er Degré",
                description="Méthode pas à pas pour résoudre ax + b = 0",
                lesson_type="text", content_type=ContentType.TEXT,
                content_text="""# Équations du 1er Degré

## Définition
Une équation du 1er degré est de la forme: ax + b = 0
où a ≠ 0

## Méthode de Résolution

### Étape 1: Isoler le terme en x
ax + b = 0
ax = -b

### Étape 2: Diviser par a
x = -b/a

## Exemple Complet

Résoudre: 3x + 6 = 0

1. 3x = -6
2. x = -6/3
3. x = -2

### Vérification
3(-2) + 6 = -6 + 6 = 0 ✓

## Équations Plus Complexes

### Forme: ax + b = cx + d
1. Regrouper les x d'un côté
2. Les constantes de l'autre
3. Simplifier

Exemple: 2x + 3 = x + 7
- 2x - x = 7 - 3
- x = 4

## Exercices
1. Résolvez: 5x - 10 = 0
2. Résolvez: 2x + 8 = x + 12
3. Résolvez: 3(x - 1) = 2x + 4""",
                content_html="<h1>Équations du 1er Degré</h1>",
                order=1, duration_minutes=25,
            )
            db.add(l2_2)
            db.flush()

            # Quiz 2.2
            q2_2 = Quiz(lesson_id=l2_2.id, title="Quiz: Équations", description="Résolvez ces équations", passing_score_percent=70)
            db.add(q2_2)
            db.flush()

            qq4 = QuizQuestion(quiz_id=q2_2.id, question_text="Quelle est la solution de 2x - 8 = 0?", question_type="mcq", points=2, order_index=0)
            db.add(qq4)
            db.flush()
            db.add_all([
                QuizOption(question_id=qq4.id, option_text="x = 2", is_correct=False, order_index=0),
                QuizOption(question_id=qq4.id, option_text="x = 4", is_correct=True, order_index=1),
                QuizOption(question_id=qq4.id, option_text="x = -4", is_correct=False, order_index=2),
                QuizOption(question_id=qq4.id, option_text="x = 8", is_correct=False, order_index=3),
            ])

            # Module 3: Géométrie
            m3 = Module(course_id=course2.id, title="Géométrie Plane", description="Figures, angles et calculs de surface", order=2)
            db.add(m3)
            db.flush()

            # Lesson 3.1: Les Figures Géométriques
            l3_1 = Lesson(
                module_id=m3.id, school_id=school.id, teacher_id=teacher.id,
                title="Les Figures Géométriques de Base",
                description="Carré, rectangle, triangle et cercle",
                lesson_type="text", content_type=ContentType.TEXT,
                content_text="""# Figures Géométriques de Base

## Le Carré

### Propriétés
- 4 côtés égaux
- 4 angles droits (90°)
- Diagonales égales et perpendiculaires

### Formules
- Périmètre: P = 4 × côté
- Aire: A = côté²
- Diagonale: d = côté × √2

## Le Rectangle

### Propriétés
- 2 côtésopposés égaux
- 4 angles droits
- Diagonales égales

### Formules
- Périmètre: P = 2 × (longueur + largeur)
- Aire: A = longueur × largeur
- Diagonale: d = √(longueur² + largeur²)

## Le Triangle

### Types
- **Équilatéral**: 3 côtés égaux
- **Isocèle**: 2 côtés égaux
- **Scalène**: 3 côtés différents

### Formules
- Périmètre: P = côté1 + côté2 + côté3
- Aire: A = (base × hauteur) / 2

## Le Cercle

### Éléments
- **Rayon (r)**: Distance du centre à la circonférence
- **Diamètre (d)**: Distance entre deux points opposés (d = 2r)
- **Circonférence (C)**: Périmètre du cercle

### Formules
- Circonférence: C = 2 × π × r
- Aire: A = π × r²

## Exercices
1. Calculez l'aire d'un carré de côté 5 cm
2. Quel est le périmètre d'un rectangle 8×3?
3. Calculez l'aire d'un triangle de base 10 et hauteur 6""",
                content_html="<h1>Figures Géométriques de Base</h1>",
                order=0, duration_minutes=20,
            )
            db.add(l3_1)
            db.flush()

            # Quiz 3.1
            q3_1 = Quiz(lesson_id=l3_1.id, title="Quiz: Géométrie", description="Testez vos connaissances géométriques", passing_score_percent=70)
            db.add(q3_1)
            db.flush()

            qq5 = QuizQuestion(quiz_id=q3_1.id, question_text="Quelle est la formule de l'aire d'un cercle?", question_type="mcq", points=1, order_index=0)
            db.add(qq5)
            db.flush()
            db.add_all([
                QuizOption(question_id=qq5.id, option_text="A = π × r", is_correct=False, order_index=0),
                QuizOption(question_id=qq5.id, option_text="A = π × r²", is_correct=True, order_index=1),
                QuizOption(question_id=qq5.id, option_text="A = 2 × π × r", is_correct=False, order_index=2),
                QuizOption(question_id=qq5.id, option_text="A = d × π", is_correct=False, order_index=3),
            ])

            # Lesson 3.2: Les Angles
            l3_2 = Lesson(
                module_id=m3.id, school_id=school.id, teacher_id=teacher.id,
                title="Les Angles et leurs Mesures",
                description="Comprendre et mesurer les angles",
                lesson_type="video", content_type=ContentType.VIDEO,
                content_text="""# Les Angles

## Définition
Un angle est formé par deux demi-droites issues d'un même point (sommet).

## Classification des Angles

| Type | Mesure | Description |
|------|--------|-------------|
| Aigu | < 90° | Plus petit qu'un angle droit |
| Droit | = 90° | Forme un carré |
| Obtus | > 90° et < 180° | Plus grand qu'un angle droit |
| Plat | = 180° | Demi-tour |
| Concave | > 180° | Plus grand qu'un demi-tour |

## Addition d'Angles

La somme des angles d'un triangle est toujours 180°.

Exemple: Si un triangle a des angles de 60° et 80°, le troisième angle est:
180° - 60° - 80° = 40°

## Angles Complémentaires et Supplémentaires

- **Complémentaires**: Deux angles dont la somme est 90°
- **Supplémentaires**: Deux angles dont la somme est 180°

## Angles Opposés par le Sommet

Quand deux droites se croisent, les angles opposés par le sommet sont égaux.

## Exercices
1. Un triangle a des angles de 45° et 90°. Quel est le 3ème angle?
2. Quel est le complémentaire de 35°?
3. Quel est le supplémentaire de 120°?""",
                content_html="<h1>Les Angles</h1>",
                video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                video_duration_seconds=720,
                order=1, duration_minutes=12,
            )
            db.add(l3_2)
            db.flush()

            # Final Quiz for Course 2
            q_final = Quiz(lesson_id=l3_2.id, title="Quiz Final: Maths Fondamentales", description="Évaluation finale complète", passing_score_percent=60)
            db.add(q_final)
            db.flush()

            qq6 = QuizQuestion(quiz_id=q_final.id, question_text="Quel est le résultat de 3² + 4²?", question_type="mcq", points=2, order_index=0)
            db.add(qq6)
            db.flush()
            db.add_all([
                QuizOption(question_id=qq6.id, option_text="7", is_correct=False, order_index=0),
                QuizOption(question_id=qq6.id, option_text="12", is_correct=False, order_index=1),
                QuizOption(question_id=qq6.id, option_text="25", is_correct=True, order_index=2),
                QuizOption(question_id=qq6.id, option_text="49", is_correct=False, order_index=3),
            ])

            qq7 = QuizQuestion(quiz_id=q_final.id, question_text="Quel est le périmètre d'un carré de côté 6 cm?", question_type="mcq", points=2, order_index=1)
            db.add(qq7)
            db.flush()
            db.add_all([
                QuizOption(question_id=qq7.id, option_text="12 cm", is_correct=False, order_index=0),
                QuizOption(question_id=qq7.id, option_text="24 cm", is_correct=True, order_index=1),
                QuizOption(question_id=qq7.id, option_text="36 cm", is_correct=False, order_index=2),
                QuizOption(question_id=qq7.id, option_text="6 cm", is_correct=False, order_index=3),
            ])

            db.commit()
            print(f"  [OK] Course '{course2.title}' created with 3 modules, 6 lessons, 4 quizzes")
        else:
            course2 = existing_student_course
            print(f"  Course '{course2.title}' already exists (id={course2.id})")

        # ========================================
        # ENROLL STUDENTS
        # ========================================
        print("\n" + "=" * 60)
        print("ENROLLING STUDENTS")
        print("=" * 60)

        # Enroll students in the math course
        for student in [student1, student2]:
            if student:
                existing = db.query(CourseEnrollment).filter(
                    CourseEnrollment.student_id == student.id,
                    CourseEnrollment.course_id == course2.id,
                ).first()
                if not existing:
                    enroll = CourseEnrollment(student_id=student.id, course_id=course2.id, status="active")
                    db.add(enroll)
                    print(f"  [OK] {student.email} enrolled in '{course2.title}'")

        db.commit()

        # ========================================
        # SUMMARY
        # ========================================
        print("\n" + "=" * 60)
        print("SEED COMPLETE")
        print("=" * 60)
        print()
        print("COURSES CREATED:")
        print(f"  1. {course1.title} (Teachers)")
        print(f"     - 3 modules, 6 lessons, 4 quizzes")
        print(f"     - Price: {course1.price_tokens} tokens / {course1.price_dt} DT")
        print()
        print(f"  2. {course2.title} (Students)")
        print(f"     - 3 modules, 6 lessons, 4 quizzes")
        print(f"     - Price: {course2.price_tokens} tokens / {course2.price_dt} DT")
        print()
        print("STUDENTS ENROLLED:")
        print(f"  - student1@pro-school.edu -> {course2.title}")
        print(f"  - student2@pro-school.edu -> {course2.title}")
        print()
        print("CONTENT TYPES INCLUDED:")
        print("  [OK] Text lessons with rich content")
        print("  [OK] Video lessons with URLs")
        print("  [OK] Quizzes with MCQ questions")
        print("  [OK] Explanations and practice exercises")
        print()
        print("LOGIN TO TEST:")
        print(f"  Teacher: teacher@pro-school.edu / password123")
        print(f"  Student: student1@pro-school.edu / password123")

    except Exception as e:
        db.rollback()
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    seed_courses()
