import { useState, useEffect, useRef } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuthStore } from "../../../store/authStore";

const NIVEAUX = [
  { group: "Primaire", items: ["1ère année","2ème année","3ème année","4ème année","5ème année","6ème année"] },
  { group: "Préparatoire", items: ["7ème de base","8ème de base","9ème de base"] },
  { group: "Secondaire", items: [
    "1ère année secondaire",
    "2ème année sciences","2ème année lettres","2ème année technologie de l'informatique","2ème année économie et services",
    "3ème année lettres","3ème année mathématiques","3ème année sciences expérimentales","3ème année économie et gestion","3ème année sciences de l'informatique","3ème année sciences techniques",
    "4ème année lettres","4ème année mathématiques","4ème année sciences expérimentales","4ème année économie et gestion","4ème année sciences de l'informatique","4ème année sciences techniques",
  ] },
];

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [schoolName, setSchoolName] = useState("");
  const [niveauScolaire, setNiveauScolaire] = useState("");
  const [role, setRole] = useState<"student" | "teacher">("student");
  const [trialMode, setTrialMode] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const { register, registerTrialTeacher, registerTeacher, isLoading, error } = useAuthStore();
  const navigate = useNavigate();

  // School search state
  const [schoolQuery, setSchoolQuery] = useState("");
  const [schoolResults, setSchoolResults] = useState<{id: number; name: string}[]>([]);
  const [selectedSchool, setSelectedSchool] = useState<{id: number; name: string} | null>(null);
  const [showDropdown, setShowDropdown] = useState(false);
  const [schoolNotFound, setSchoolNotFound] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const searchSchools = async (query: string) => {
    if (query.length < 2) {
      setSchoolResults([]);
      setSchoolNotFound(false);
      return;
    }
    try {
      const res = await fetch(`/auth/schools/search?q=${encodeURIComponent(query)}`);
      const data = await res.json();
      setSchoolResults(data);
      setSchoolNotFound(data.length === 0);
    } catch {
      setSchoolResults([]);
      setSchoolNotFound(true);
    }
  };

  const handleSchoolInputChange = (value: string) => {
    setSchoolQuery(value);
    setSelectedSchool(null);
    setShowDropdown(true);
    setSchoolNotFound(false);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => searchSchools(value), 300);
  };

  const handleSelectSchool = (school: {id: number; name: string}) => {
    setSelectedSchool(school);
    setSchoolName(school.name);
    setSchoolQuery(school.name);
    setShowDropdown(false);
    setSchoolNotFound(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (role === "teacher" && trialMode) {
      const success = await registerTrialTeacher(email, password, fullName);
      if (success) navigate("/dashboard");
      return;
    }

    if (role === "teacher" && !trialMode) {
      if (!selectedSchool) {
        setSchoolNotFound(true);
        return;
      }
      const result = await registerTeacher(email, password, fullName, schoolName, selectedSchool.id);
      if (result === "pending") {
        setSubmitted(true);
      }
      return;
    }

    const success = await register(email, password, fullName, schoolName, role === "student" ? niveauScolaire : undefined);
    if (success) {
      const userStr = localStorage.getItem("user");
      const user = userStr ? JSON.parse(userStr) : null;
      const r = user?.role?.toUpperCase();
      if (r === "SUPER_ADMIN") navigate("/dashboard/admin");
      else if (r === "ADMIN_SCHOOL") navigate("/dashboard/school");
      else navigate("/dashboard");
    }
  };

  if (submitted) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-cream">
        <div className="bg-white rounded-3xl p-10 shadow-sm border border-black/5 max-w-md w-full text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="text-2xl font-[300] text-navy mb-2">Demande envoyée</h2>
          <p className="text-gray text-sm mb-6">
            Votre demande d'inscription enseignant a été soumise. L'administrateur de l'école examinera votre candidature et vous recevrez un email une fois la décision prise.
          </p>
          <Link to="/login" className="inline-block bg-gradient-to-r from-orange to-orange-l text-white font-semibold py-3 px-8 rounded-xl hover:opacity-90 transition-all">
            Retour à la connexion
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex">
      {/* Left side - Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-navy relative overflow-hidden">
        <div className="absolute w-[700px] h-[700px] rounded-full bg-gradient-to-br from-orange/20 to-transparent -top-[200px] -right-[150px]" />
        <div className="absolute w-[500px] h-[500px] rounded-full bg-gradient-to-br from-orange-l/10 to-transparent -bottom-[150px] -left-[100px]" />
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[length:64px_64px]" />

        <div className="relative z-10 flex flex-col justify-center items-center text-center p-12">
          <div className="mb-8">
            <span className="inline-flex items-center gap-3 bg-orange/10 border border-orange/30 text-orange-l text-xs font-bold tracking-[3px] uppercase px-5 py-2 rounded-full">
              <span className="w-2 h-2 bg-orange rounded-full animate-pulse" />
              Plateforme EdTech · IA · SaaS
            </span>
          </div>

          <h1 className="text-6xl font-[300] text-white mb-4 leading-tight">
            EDU<span className="italic text-orange-l">AI</span>
            <br />Learning
          </h1>

          <p className="text-orange-l/60 text-sm font-light tracking-[4px] uppercase mb-6">
            La Startup Éducative Complète
          </p>

          <p className="text-white/50 max-w-md leading-relaxed font-light">
            Créez votre compte et rejoignez la première plateforme éducative tunisienne qui combine LMS, IA Générative et SaaS.
          </p>

          <div className="flex gap-12 mt-16">
            <div>
              <div className="text-4xl font-[300] text-orange-l">5</div>
              <div className="text-white/30 text-xs tracking-[2px] uppercase mt-2">Modules</div>
            </div>
            <div>
              <div className="text-4xl font-[300] text-orange-l">3</div>
              <div className="text-white/30 text-xs tracking-[2px] uppercase mt-2">Revenus</div>
            </div>
            <div>
              <div className="text-4xl font-[300] text-orange-l">24/7</div>
              <div className="text-white/30 text-xs tracking-[2px] uppercase mt-2">Tuteur IA</div>
            </div>
          </div>
        </div>
      </div>

      {/* Right side - Register Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 bg-cream">
        <div className="w-full max-w-md">
          <div className="lg:hidden mb-12 text-center">
            <h1 className="text-4xl font-[300] text-navy">
              EDU<span className="italic text-orange">AI</span>
            </h1>
          </div>

          <div className="bg-white rounded-3xl p-10 shadow-sm border border-black/5">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-[300] text-navy mb-2">Créer un compte</h2>
              <p className="text-gray text-sm">Rejoignez EDUAI Learning</p>
            </div>

            {error && (
              <div className="bg-orange-p border border-orange/30 text-orange text-sm px-5 py-3 rounded-xl mb-6">
                {error}
              </div>
            )}

            {/* Role selector */}
            <div className="flex gap-2 mb-6 p-1 bg-cream-m rounded-xl">
              <button
                type="button"
                onClick={() => { setRole("student"); setTrialMode(false); }}
                className={`flex-1 py-2.5 rounded-lg text-sm font-semibold transition-all ${
                  role === "student"
                    ? "bg-white text-navy shadow-sm"
                    : "text-gray hover:text-navy"
                }`}
              >
                Élève
              </button>
              <button
                type="button"
                onClick={() => setRole("teacher")}
                className={`flex-1 py-2.5 rounded-lg text-sm font-semibold transition-all ${
                  role === "teacher"
                    ? "bg-white text-navy shadow-sm"
                    : "text-gray hover:text-navy"
                }`}
              >
                Enseignant
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="block text-xs font-semibold text-gray tracking-wide uppercase mb-2">
                  Nom complet
                </label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full px-5 py-3 bg-cream-m rounded-xl border border-black/5 focus:border-orange focus:outline-none transition-colors"
                  placeholder="Jean Dupont"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray tracking-wide uppercase mb-2">
                  Email
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-5 py-3 bg-cream-m rounded-xl border border-black/5 focus:border-orange focus:outline-none transition-colors"
                  placeholder="vous@ecole.edu"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray tracking-wide uppercase mb-2">
                  Mot de passe
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-5 py-3 bg-cream-m rounded-xl border border-black/5 focus:border-orange focus:outline-none transition-colors"
                  placeholder="••••••••"
                  required
                  minLength={8}
                />
              </div>

              {role === "student" && (
                <div>
                  <label className="block text-xs font-semibold text-gray tracking-wide uppercase mb-2">
                    Niveau scolaire
                  </label>
                  <select
                    value={niveauScolaire}
                    onChange={(e) => setNiveauScolaire(e.target.value)}
                    className="w-full px-5 py-3 bg-cream-m rounded-xl border border-black/5 focus:border-orange focus:outline-none transition-colors"
                    required
                  >
                    <option value="">Sélectionnez votre niveau</option>
                    {NIVEAUX.map((g) => (
                      <optgroup key={g.group} label={g.group}>
                        {g.items.map((n) => (
                          <option key={n} value={n}>{n}</option>
                        ))}
                      </optgroup>
                    ))}
                  </select>
                </div>
              )}

              {role === "teacher" && !trialMode && (
                <div ref={searchRef} className="relative">
                  <label className="block text-xs font-semibold text-gray tracking-wide uppercase mb-2">
                    Nom de l'école
                  </label>
                  <input
                    type="text"
                    value={schoolQuery}
                    onChange={(e) => handleSchoolInputChange(e.target.value)}
                    onFocus={() => schoolQuery.length >= 2 && setShowDropdown(true)}
                    className="w-full px-5 py-3 bg-cream-m rounded-xl border border-black/5 focus:border-orange focus:outline-none transition-colors"
                    placeholder="Rechercher votre école..."
                    required
                    autoComplete="off"
                  />
                  {showDropdown && schoolResults.length > 0 && (
                    <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-xl shadow-lg max-h-60 overflow-auto">
                      {schoolResults.map((school) => (
                        <button
                          key={school.id}
                          type="button"
                          onClick={() => handleSelectSchool(school)}
                          className="w-full text-left px-5 py-3 hover:bg-orange/5 transition-colors border-b border-gray-100 last:border-0"
                        >
                          <span className="text-sm text-navy">{school.name}</span>
                        </button>
                      ))}
                    </div>
                  )}
                  {schoolNotFound && (
                    <p className="text-red-500 text-sm mt-2">
                      Cette école n'appartient pas au système. Veuillez contacter l'administrateur.
                    </p>
                  )}
                </div>
              )}

              {role === "teacher" && (
                <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
                  <p className="text-sm text-blue-800 mb-3">
                    {trialMode
                      ? "Vous allez créer un compte de démonstration lié à l'école EDUAI. Vous aurez accès à toutes les fonctionnalités pendant 30 jours."
                      : "Vous souhaitez rejoindre une école existante ? Votre demande sera examinée par l'administrateur."}
                  </p>
                  <button
                    type="button"
                    onClick={() => setTrialMode(!trialMode)}
                    className="text-sm text-blue-600 font-semibold hover:underline"
                  >
                    {trialMode ? "Rejoindre une école existante" : "Tester gratuitement (école de démo)"}
                  </button>
                </div>
              )}

              <button
                type="submit"
                disabled={isLoading}
                className="w-full bg-gradient-to-r from-orange to-orange-l text-white font-semibold py-4 rounded-xl hover:opacity-90 hover:translate-y-[-2px] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading
                  ? "Création en cours..."
                  : role === "teacher" && trialMode
                    ? "Commencer l'essai gratuit"
                    : "Créer mon compte"}
              </button>
            </form>
          </div>

          <p className="text-center text-gray text-sm mt-8">
            Déjà un compte ?{" "}
            <Link to="/login" className="text-orange font-semibold hover:underline">
              Se connecter
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
