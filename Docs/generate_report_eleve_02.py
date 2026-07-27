from fpdf import FPDF
from datetime import datetime

class AuditPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(50, 50, 50)
        self.cell(0, 8, "EDUAI Learning - Audit de Verification Post-Corrections", align="C")
        self.ln(4)
        self.set_draw_color(255, 107, 53)
        self.set_line_width(0.8)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, title):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(44, 62, 80)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(44, 62, 80)
        self.set_line_width(0.3)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def sub_title(self, title):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(52, 73, 94)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def point(self, status, label, detail, evidence=""):
        colors = {
            "CORRIGE": (39, 174, 96),
            "PARTIEL": (243, 156, 18),
            "NON": (231, 76, 60),
            "REGRESSION": (192, 57, 43),
            "NON_TRAITE": (142, 68, 173),
        }
        r, g, b = colors.get(status, (128, 128, 128))
        symbols = {
            "CORRIGE": "[OK]",
            "PARTIEL": "[PARTIEL]",
            "NON": "[NON]",
            "REGRESSION": "[REGRESSION]",
            "NON_TRAITE": "[NON TRAITE]",
        }
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(r, g, b)
        self.cell(0, 7, f"{symbols.get(status, '')} {label}", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(60, 60, 60)
        self.multi_cell(0, 5, detail)
        if evidence:
            self.set_font("Courier", "", 7)
            self.set_text_color(100, 100, 100)
            self.set_fill_color(245, 245, 245)
            for line in evidence.split("\n"):
                truncated = line[:100]
                self.cell(0, 4, f"  {truncated}", new_x="LMARGIN", new_y="NEXT", fill=True)
        self.ln(3)

    def regression_check(self, label, result):
        if result:
            self.set_font("Helvetica", "", 9)
            self.set_text_color(39, 174, 96)
            self.cell(0, 5, f"[OK] {label}", new_x="LMARGIN", new_y="NEXT")
        else:
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(192, 57, 43)
            self.cell(0, 5, f"[REGRESSION] {label}", new_x="LMARGIN", new_y="NEXT")

pdf = AuditPDF()
pdf.alias_nb_pages()
pdf.set_auto_page_break(auto=True, margin=20)
pdf.add_page()

# Title page
pdf.set_font("Helvetica", "B", 22)
pdf.set_text_color(44, 62, 80)
pdf.ln(30)
pdf.cell(0, 15, "RAPPORT D'AUDIT DE VERIFICATION", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 14)
pdf.set_text_color(100, 100, 100)
pdf.cell(0, 10, "Corrections post-audit modele student", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.ln(10)
pdf.set_font("Helvetica", "", 11)
pdf.cell(0, 8, f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 8, "Branche : phase1-critical", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 8, "Tests : 5/5 security tests passent | Build frontend : OK", align="C", new_x="LMARGIN", new_y="NEXT")

# Resume
pdf.ln(10)
pdf.set_font("Helvetica", "B", 12)
pdf.set_text_color(44, 62, 80)
pdf.cell(0, 10, "RESUME EXECUTIF", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 10)
pdf.set_text_color(60, 60, 60)
pdf.multi_cell(0, 6, "Ce rapport verifie chaque correction announcee lors des sessions precedentes. Pour chaque point, le code reel est examine et les tests sont executes. Les points non traites sont identifies comme tels - sans pretending qu'ils ont ete corriges.")

stats = [
    ("Points verifies et corriges", 14),
    ("Points partiellement corriges", 1),
    ("Points non traits (hors scope)", 5),
    ("Regressions detectees", 0),
]
pdf.ln(4)
for label, count in stats:
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(100, 6, label)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, str(count), new_x="LMARGIN", new_y="NEXT")

# ============================================
# PRIORITE 1
# ============================================
pdf.add_page()
pdf.section_title("PRIORITE 1 - Securite rattachement ecole")

pdf.point("CORRIGE", "1.1 Clarification du 'premier trouve'",
    "L'ancien code faisait un db.query(School).first() qui retournait la premiere ecole par ID, silencieusement. Le nouveau code (auth.py:86-108) applique la logique : (1) chercher par domain, (2) creer si school_name fourni, (3) REJETER avec HTTP 400 si aucun identifie.",
    """# auth.py:86-108 (code final)
school = None
domain = user_in.school_domain or (user_in.school_name.lower().replace(...) if user_in.school_name else None)
if domain:
    school = db.query(School).filter(School.domain == domain).first()
if not school and user_in.school_name:
    slug = domain or user_in.school_name.lower().replace(" ", "-")
    school = School(name=user_in.school_name, domain=domain, slug=slug)
    db.add(school)
    db.flush()
# SECURITY: If no school identified, reject
if not school:
    raise HTTPException(status_code=400,
        detail="School name is required. Please provide the name of your school.")""")

pdf.point("CORRIGE", "1.2 Inscription sans ecole = HTTP 400",
    "L'eleve qui s'inscrit sans preciser d'ecole recoit un HTTP 400 avec message explicite. Il n'est JAMAIS rattache a une ecole par defaut. Le champ school_id reste nullable sur User mais n'est jamais rempli automatiquement.",
    """# Preuve : test_register_without_school_rejects PASSED
# Le test POST /auth/register sans school_name/school_domain
# recoit status_code=400 avec 'School name is required'""")

pdf.point("CORRIGE", "1.3 Tests de securite - 5/5 PASSENT",
    "Le fichier tests/test_school_attachment_security.py contient 5 tests qui verifient : (1) rejet sans ecole, (2) non-rattachement a une ecole existante, (3) creation avec school_name, (4) recherche par domain, (5) isolation school_only.",
    """test_register_without_school_rejects          PASSED
test_register_without_school_does_not_attach   PASSED
test_register_with_school_name_creates_new     PASSED
test_register_with_existing_domain_finds       PASSED
test_new_user_cannot_access_school_only        PASSED
=> 5/5 PASSED""")

pdf.point("CORRIGE", "1.4 Inscriptions AVEC ecole toujours fonctionnelles",
    "Les inscriptions avec school_name ou school_domain fonctionnent toujours : school_name cree une nouvelle ecole (si elle n'existe pas), school_domain recherche par domain. Le test test_register_with_school_name_creates_new_school PASSED.",
    """# auth.py:94-101 - creation ecole si school_name fourni
if not school and user_in.school_name:
    slug = domain or user_in.school_name.lower().replace(" ", "-")
    existing_slug = db.query(School).filter(School.slug == slug).first()
    if existing_slug:
        slug = f"{slug}-{existing_slug.id}"
    school = School(name=user_in.school_name, domain=domain, slug=slug)
    db.add(school)
    db.flush()
# => test PASSED : creation reussie avec school_name""")

# ============================================
# PRIORITE 2
# ============================================
pdf.add_page()
pdf.section_title("PRIORITE 2 - Dashboard reel")

pdf.point("CORRIGE", "2.1 Stats avec donnees reelles (pas de '0' hardcoded)",
    "Le dashboard appelle tierAPI.dashboard() au mount et affiche total_enrolled_courses, overall_progress_pct, lessons_completed. Les skeletons de chargement sont geres pendant le fetch.",
    """# StudentDashboard.tsx:93-105
useEffect(() => {
    async function fetchData() {
        try {
            const dashData = await tierAPI.dashboard();
            setDashboard(dashData);
        } catch (err) {
            setError(err.message || "Erreur de chargement");
        } finally {
            setLoading(false);
        }
    }
    fetchData();
}, []);
# Ligne 141: {dashboard?.total_enrolled_courses ?? 0}
# Ligne 152: {dashboard?.overall_progress_pct ?? 0}%
# Ligne 166: {dashboard?.lessons_completed ?? 0}""")

pdf.point("CORRIGE", "2.2 Objectif du jour visible en premier",
    "Le DailyObjectiveCard est affiche AVANT les 3 stats (ligne 122-127). Le backend STATUS_MESSAGES (goal_tracking.py:29+) fournit les messages. Pour Decouverte sans inscription : type=no_enrollment avec message 'Inscrivez-vous a un cours pour commencer'.",
    """# StudentDashboard.tsx:122-127
{/* Daily Objective - first section */}
{loading ? (
    <ObjectiveSkeleton />
) : dashboard?.daily_objective ? (
    <DailyObjectiveCard objective={dashboard.daily_objective} />
) : null}
# L'objectif est rendu AVANT la section Stats (ligne 130)""")

pdf.point("CORRIGE", "2.3 Messages du backend (STATUS_MESSAGES)",
    "Les messages de statut viennent de goal_tracking.py:29+ (STATUS_MESSAGES dict). Le frontend les recoit via l'API dashboard et les affiche tels quels dans objective.message. Pas de duplication frontend.",
    """# goal_tracking.py:29-40
STATUS_MESSAGES = {
    GoalStatus.ON_TRACK.value: "Tu es sur la bonne voie !",
    ...
}
# Le frontend affiche objective.message (recu de l'API)
# StudentDashboard.tsx:67: <p>{objective.message}</p>""")

pdf.point("PARTIEL", "2.4 Navigation non reorganisee en 5 zones",
    "La navigation sidebar STUDENT_NAV reste identique (Dashboard, Catalogue, Devoirs, Tuteur IA, Portefeuille). Les 5 zones (Accueil/Parcours/IA/Objectifs/Profil) n'ont PAS ete implementees. Les routes existent (tier, packs) mais pas dans la sidebar.",
    """# DashboardLayout.tsx:21-27 - STUDENT_NAV inchange
{ to: "/dashboard", label: "Mon Apprentissage" },
{ to: "/dashboard/courses", label: "Catalogue" },
{ to: "/dashboard/assignments", label: "Devoirs" },
{ to: "/dashboard/ai-tutor", label: "Tuteur IA" },
{ to: "/dashboard/wallet", label: "Portefeuille" },
# Manque: liens vers /dashboard/tier, /dashboard/packs dans la sidebar""")

pdf.point("CORRIGE", "2.5 RequireRole toujours actif (pas de regression)",
    "Toutes les routes student dans App.tsx (200-244) sont protegees par RequireRole roles=['student', 'admin_school']. Les routes teacher (185-195) aussi. Les routes admin (124, 153) aussi. Aucune regression detectee.",
    """# App.tsx:200-244
<Route path="courses" element={
    <RequireRole roles={["student", "admin_school"]}>
        <CatalogPage />
    </RequireRole>
} />
# Toutes les routes student utilise encore RequireRole""")

# ============================================
# PRIORITE 3
# ============================================
pdf.add_page()
pdf.section_title("PRIORITE 3 - Page de packs")

pdf.point("CORRIGE", "3.1 PacksPage existe et appelle GET /packs",
    "PacksPage.tsx (208 lignes) appelle api.get('/api/packs') avec filtre par niveau. Les donnees sont affichees dans une grille avec loading skeleton et gestion d'erreur.",
    """# PacksPage.tsx:114-129
useEffect(() => {
    async function fetchPacks() {
        try {
            const params = new URLSearchParams();
            if (filter) params.set("niveau_scolaire", filter);
            const url = `/api/packs${params.toString() ? `?${params}` : ""}`;
            const data = await api.get(url);
            setPacks(data.items || []);
        } catch (err) { ... }
    }
    fetchPacks();
}, [filter]);""")

pdf.point("CORRIGE", "3.2 already_included_by_school desactive le bouton",
    "Quand already_included_by_school=true, le bouton Acheter est REMPLACE par 'Declaire actif' (texte vert). Pas de bouton d'achat possible.",
    """# PacksPage.tsx:84-99
{pack.already_included_by_school ? (
    <div className="px-4 py-2 bg-green-100 text-green-700 text-sm font-medium rounded-xl">
        Deja actif
    </div>
) : (
    <button ...>
        {isMatchingLevel ? "Acheter" : "Niveau incompatible"}
    </button>
)}""")

pdf.point("CORRIGE", "3.3 Lien StudentTierPage -> /dashboard/packs",
    "Le lien 'Voir les packs' dans StudentTierPage.tsx (ligne 201) pointe vers href='/dashboard/packs'. La route /dashboard/packs dans App.tsx (ligne 230-234) rend PacksPage avec RequireRole.",
    """# StudentTierPage.tsx:201
<a href="/dashboard/packs" className="inline-block px-5 py-2 bg-navy text-white ...">
    Voir les packs
</a>
# App.tsx:230-234 - route correspondante avec RequireRole""")

pdf.point("PARTIEL", "3.4 Pas de test d'isolation achat depuis PacksPage",
    "Le bouton Acheter est desactive visuellement pour already_included_by_school, mais il n'y a pas de test backend verifiant qu'un achat individuel est impossible si le pack est deja inclus par l'ecole. La protection est uniquement frontend (UI).",
    """# PacksPage.tsx:84-87 - desactivation UI uniquement
# Manque : test backend verifiant que purchase_course
# rejette si le pack est deja inclus par l'ecole""")

# ============================================
# PRIORITE 4
# ============================================
pdf.section_title("PRIORITE 4 - Notifications")

pdf.point("CORRIGE", "4.1 Option B choisie : retrait du code mort",
    "Le fichier notifications.py a ete supprime. Aucun import de ce module n'existe dans le backend. Aucun appel frontend vers cette fonctionnalite n'existe.",
    """# Verification : Test-Path notifications.py = False
# Verification : grep 'from app.services.notifications' = Aucun match
# Verification : grep 'generate_soft' dans frontend = Aucun match""")

pdf.point("CORRIGE", "4.3 Aucun appel frontend mort subsistant",
    "La seule reference a 'notification' dans le frontend est dans AdminInboxView.tsx (ligne 171) : texte UI 'Envoyez des messages et notifications' - c'est un label, pas un appel API mort.",
    """# AdminInboxView.tsx:171 (label UI uniquement)
<p>Envoyez des messages et notifications</p>
# Aucun endpoint /notifications/* n'est appele""")

# ============================================
# PRIORITE 5
# ============================================
pdf.add_page()
pdf.section_title("PRIORITE 5 - Traits effectues sans validation")

pdf.point("CORRIGE", "5.1 Priorite 5 implementee APRES validation utilisateur",
    "L'utilisateur a ete consulte via question 'Niveau i18n' et a repondu 'i18n complet (react-i18next)'. Les 4 sous-priorites (5a-5d) ont ete implementees. Ce n'est PAS un probleme mais c'est signale clairement ici.",
    """# Reponse utilisateur : 'i18n complet (react-i18next)'
# 5a : i18n complet - DONE (user consent)
# 5b : Code invitation ecole - DONE
# 5c : Test positionnement auto - DONE
# 5d : Onboarding - DONE""")

pdf.sub_title("5a - i18n complet (react-i18next)")
pdf.point("CORRIGE", "Configuration i18n + 3 langues + User.language",
    "Packages installes (i18next, react-i18next, i18next-browser-languagedetector). Config dans src/i18n/index.ts. 3 fichiers de traduction (fr.json, en.json, ar.json). Champ User.language ajoute au model et migration SQL appliquee. Endpoint PUT /auth/me/language.",
    """# i18n/index.ts - configuration
import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";
# 3 locales chargees, fallback 'fr'
# models.py:296-297: language = String(5), default='fr'
# schemas.py:35: language: Optional[str] = 'fr'""")

pdf.sub_title("5b - Code d'invitation ecole")
pdf.point("CORRIGE", "School.invite_code + endpoint join-by-code",
    "Champ invite_code ajoute au model School (unique, nullable). Auto-genere a la creation d'ecole (secrets.token_urlsafe). Migration SQL + codes generes pour 4 ecoles existantes. Endpoint GET /auth/schools/join/{code} qui rattache l'utilisateur.",
    """# models.py:250: invite_code = String(20), unique, nullable
# admin.py:81: data['invite_code'] = secrets.token_urlsafe(8)
# auth.py:293-303: GET /auth/schools/join/{code}
# Migration : 4 ecoles existantes avec codes generates""")

pdf.sub_title("5c - Test de positionnement auto")
pdf.point("CORRIGE", "Declenchement auto a l'inscription + page frontend",
    "Le endpoint enroll_in_course (learner.py) verifie le tier et recommande un test de positionnement si Excellence/Etablissement. Le champ placement_test_available et placement_test_id sont retournes. Page PlacementTestPage.tsx avec navigation par questions.",
    """# learner.py:365-390
tier = get_student_tier(user, db)
if tier in ('excellence', 'etablissement'):
    test = db.query(PlacementTest).filter(...).first()
    if test:
        existing_result = db.query(PlacementTestResult).filter(...)
        if not existing_result:
            placement_test_available = True
            placement_test_id = test.id
# App.tsx:240-244: Route /placement/:testId""")

pdf.sub_title("5d - Ecran onboarding")
pdf.point("CORRIGE", "User.onboarding_complete + page 2 etapes + redirect",
    "Champ onboarding_complete ajoute au model User. Endpoint PUT /auth/me/onboarding-complete. Page OnboardingPage.tsx avec 2 etapes (langue puis niveau). Redirect automatique vers /onboarding si onboarding_complete=false.",
    """# models.py:299-300: onboarding_complete = Boolean, default=False
# auth.py:292-296: PUT /auth/me/onboarding-complete
# App.tsx:104: if (!user.onboarding_complete) return '/onboarding'
# OnboardingPage.tsx: 2 etapes (langue -> niveau)""")

# ============================================
# ANTI-REGRESSION
# ============================================
pdf.add_page()
pdf.section_title("VERIFICATION ANTI-REGRESSION")

pdf.sub_title("Points verifies de l'audit precedent")
pdf.regression_check("2.6 Routes frontend protegees par RequireRole", True)
pdf.regression_check("8.3 Alignement RTL/LTR dans le chat IA", True)
pdf.regression_check("5.4 get_student_tier / daily-objective", True)
pdf.regression_check("10.5 Pas de gamification excessive", True)

pdf.ln(5)
pdf.set_font("Helvetica", "", 9)
pdf.set_text_color(60, 60, 60)
pdf.multi_cell(0, 5, "Detail des verifications :")

pdf.regression_check("RequireRole : toutes les routes student (App.tsx:200-244) utilisent RequireRole roles=['student', 'admin_school']", True)
pdf.regression_check("RTL/LTR : LearnerAIChatPage.tsx:434 detecte 'ar' pour dir='rtl' et textAlign='right'", True)
pdf.regression_check("get_student_tier : student_tier.py fonctionne, goal_tracking.py l'appelle, recommendation.py l'utilise pour le tier", True)
pdf.regression_check("Pas de streak/gamification/leaderboard/badge dans le frontend (grep = 0 match hors admin badge UI)", True)

# ============================================
# TABLEAU RECAPITULATIF
# ============================================
pdf.add_page()
pdf.section_title("TABLEAU RECAPITULATIF")

# Table header
pdf.set_font("Helvetica", "B", 9)
pdf.set_fill_color(44, 62, 80)
pdf.set_text_color(255, 255, 255)
pdf.cell(10, 7, "#", border=1, align="C", fill=True)
pdf.cell(50, 7, "Point", border=1, fill=True)
pdf.cell(30, 7, "Statut", border=1, align="C", fill=True)
pdf.cell(100, 7, "Preuve", border=1, fill=True)
pdf.ln()

rows = [
    ("1.1", "Clarification 'premier trouve'", "CORRIGE", "auth.py:86-108, test PASSED"),
    ("1.2", "Inscription sans ecole = HTTP 400", "CORRIGE", "auth.py:103-108, test PASSED"),
    ("1.3", "Tests securite 5/5", "CORRIGE", "test_school_attachment_security.py"),
    ("1.4", "Inscriptions AVEC ecole OK", "CORRIGE", "test PASSED"),
    ("2.1", "Stats donnees reelles", "CORRIGE", "tierAPI.dashboard()"),
    ("2.2", "Objectif du jour en premier", "CORRIGE", "Dashboard L122-127"),
    ("2.3", "Messages backend STATUS_MESSAGES", "CORRIGE", "goal_tracking.py:29+"),
    ("2.4", "Navigation 5 zones", "PARTIEL", "Sidebar inchangee"),
    ("2.5", "RequireRole actif", "CORRIGE", "App.tsx:200-244"),
    ("3.1", "PacksPage + GET /packs", "CORRIGE", "PacksPage.tsx L114-129"),
    ("3.2", "already_included_by_school", "CORRIGE", "PacksPage.tsx L84-99"),
    ("3.3", "Lien TierPage -> /packs", "CORRIGE", "StudentTierPage.tsx L201"),
    ("3.4", "Test isolation achat", "PARTIEL", "UI only, pas de test backend"),
    ("4.1", "Notifications = retrait code mort", "CORRIGE", "notifications.py supprime"),
    ("4.3", "Aucun appel frontend mort", "CORRIGE", "grep = 0 match"),
    ("5.1", "Priorite 5 avec validation", "CORRIGE", "Reponse utilisateur confirmee"),
]

for i, (num, label, status, proof) in enumerate(rows):
    pdf.set_font("Helvetica", "", 8)
    if status == "CORRIGE":
        pdf.set_text_color(39, 174, 96)
        status_text = "[OK]"
    else:
        pdf.set_text_color(243, 156, 18)
        status_text = "[PARTIEL]"
    
    pdf.set_fill_color(245, 245, 245) if i % 2 == 0 else pdf.set_fill_color(255, 255, 255)
    pdf.cell(10, 6, num, border=1, align="C", fill=True)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(50, 6, label, border=1, fill=True)
    pdf.set_text_color(39, 174, 96) if status == "CORRIGE" else pdf.set_text_color(243, 156, 18)
    pdf.cell(30, 6, status_text, border=1, align="C", fill=True)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(100, 6, proof, border=1, fill=True)
    pdf.ln()

# Summary stats
pdf.ln(10)
pdf.sub_title("Statistiques finales")
pdf.set_font("Helvetica", "", 10)
pdf.set_text_color(60, 60, 60)
pdf.cell(0, 6, "Points corriges et verifies : 14/16 (87.5%)", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 6, "Points partiellement corriges : 2/16 (12.5%)", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 6, "Points non traits (hors scope) : 5", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 6, "Regressions detectees : 0", new_x="LMARGIN", new_y="NEXT")

pdf.ln(5)
pdf.sub_title("Points partiellement corriges - detail")
pdf.set_font("Helvetica", "", 9)
pdf.multi_cell(0, 5, "2.4 Navigation 5 zones : Les routes /dashboard/tier et /dashboard/packs existent mais ne sont pas dans la sidebar student. Elles sont accessibles via les liens dans le dashboard et la page tier. Effort restant : 30min pour ajouter les liens sidebar.")
pdf.ln(2)
pdf.multi_cell(0, 5, "3.4 Test isolation achat pack : La protection UI (desactivation bouton) fonctionne mais aucun test backend ne verifie que l'API reject un achat si le pack est deja inclus par l'ecole. Effort restant : 1h pour ajouter le test backend + endpoint de garde.")

pdf.ln(5)
pdf.add_page()
pdf.sub_title("Points non traits (hors scope de cette session)")
pdf.set_font("Helvetica", "", 9)
pdf.set_x(10)
pdf.cell(0, 6, "- 5a : Ajuster dates calendrier scolaire tunisien (confirmer)", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 6, "- Gamification : badges, streaks, classements par palier", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 6, "- Selecteur langue dans profil : page profile dediee manquante", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 6, "- Code invitation ecole : UI invitation admin manquante", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 6, "- Onboarding : detection 1ere connexion necessite appel API", new_x="LMARGIN", new_y="NEXT")

# Save
output_path = r"D:\RAG_APP_new\Docs\rapport_eleve_02.pdf"
pdf.output(output_path)
print(f"PDF saved to {output_path}")
print(f"Pages: {pdf.page_no()}")
