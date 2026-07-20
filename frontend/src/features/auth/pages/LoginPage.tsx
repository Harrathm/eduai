import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuthStore } from "../../../store/authStore";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const { login, isLoading, error } = useAuthStore();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    const success = await login(email, password);
    if (success) {
      const userStr = localStorage.getItem("user");
      const user = userStr ? JSON.parse(userStr) : null;
      const role = user?.role?.toUpperCase();
      if (role === "SUPER_ADMIN" || role === "PEDAGOGICAL_ADMIN") {
        navigate("/dashboard/admin");
      } else if (role === "ADMIN_SCHOOL" || role === "PEDAGOGICAL_LEAD") {
        navigate("/dashboard/school");
      } else {
        navigate("/dashboard");
      }
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left side - Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-navy relative overflow-hidden">
        {/* Orb effects */}
        <div className="absolute w-[700px] h-[700px] rounded-full bg-gradient-to-br from-orange/20 to-transparent -top-[200px] -right-[150px]" />
        <div className="absolute w-[500px] h-[500px] rounded-full bg-gradient-to-br from-orange-l/10 to-transparent -bottom-[150px] -left-[100px]" />
        
        {/* Grid */}
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
            La première plateforme éducative tunisienne qui combine LMS, IA Générative, SaaS et Academy en une solution unique, scalable et monétisable.
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

      {/* Right side - Login Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 bg-cream">
        <div className="w-full max-w-md">
          <div className="lg:hidden mb-12 text-center">
            <h1 className="text-4xl font-[300] text-navy">
              EDU<span className="italic text-orange">AI</span>
            </h1>
          </div>
          
          <div className="bg-white rounded-3xl p-10 shadow-sm border border-black/5">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-[300] text-navy mb-2">Bienvenue</h2>
              <p className="text-gray text-sm">Connectez-vous pour continuer</p>
            </div>
            
            {error && (
              <div className="bg-orange-p border border-orange/30 text-orange text-sm px-5 py-3 rounded-xl mb-6">
                {error}
              </div>
            )}
            
            <form onSubmit={handleSubmit} className="space-y-5">
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
                />
              </div>
              
              <button
                type="submit"
                disabled={isLoading}
                className="w-full bg-gradient-to-r from-orange to-orange-l text-white font-semibold py-4 rounded-xl hover:opacity-90 hover:translate-y-[-2px] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? "Connexion..." : "Se connecter"}
              </button>
            </form>
          </div>
          
          <p className="text-center text-gray text-sm mt-8">
            Pas encore de compte ?{" "}
            <Link to="/register" className="text-orange font-semibold hover:underline">
              S'inscrire
            </Link>
          </p>

          <p className="text-center text-sm mt-4">
            <Link to="/register" className="text-navy/60 hover:text-navy transition-colors">
              Enseignant ? <span className="text-orange font-semibold">Essayez gratuitement</span>
            </Link>
          </p>

          <p className="text-center text-gray text-sm mt-4">
            © 2025 EDUAI Learning — Dossier de présentation confidentiel
          </p>
        </div>
      </div>
    </div>
  );
}