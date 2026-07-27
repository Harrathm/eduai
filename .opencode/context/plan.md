# Plan — EDUAI Learning

## Status: Post-completion review
Toutes les priorités 1-5 sont complétées. 122 tests passent. Aucun bloquage.

## Remaining work (à valider avec l'utilisateur)

### 1. Ajuster dates calendrier scolaire
- Confirmer dates exactes bulletin officiel Ministère Éducation Tunisien 2025-2026
- Impact: `school_calendar.py` — uniquement les constantes

### 2. Gamification (à valider)
- Badges, streaks, classements par palier
- Nécessite UX/UI design

### 3. Page profil utilisateur
- LanguageSelector existe dans sidebar mais pas de page profile dédiée
- `PUT /auth/me/language` existe déjà côté backend

### 4. UI invitation admin
- Endpoint `GET /auth/schools/join/{code}` existe
- Pas de page admin pour générer/afficher les codes d'invitation

### 5. Détection 1ère connexion
- OnboardingPage créée mais nécessite un appel API explicite
- Possibilité de redirect automatique au login

### 6. Tâche planifiée
- Génération auto daily/weekly goals via scheduler
