import { useState } from "react";
import { Link } from "react-router-dom";
import { Mail, ArrowLeft, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await fetch("/auth/forgot-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      if (res.ok) {
        setSent(true);
      } else {
        setError(data.detail || "Une erreur est survenue.");
      }
    } catch {
      setError("Erreur réseau. Veuillez réessayer.");
    }
    setLoading(false);
  };

  if (sent) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-cream px-4">
        <div className="bg-white rounded-3xl max-w-md w-full p-8 shadow-sm border border-black/5 text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle className="w-8 h-8 text-green-600" />
          </div>
          <h1 className="text-2xl font-semibold text-navy mb-4">Email envoyé</h1>
          <p className="text-gray mb-6">
            Si un compte existe avec l'adresse <strong>{email}</strong>, vous recevrez
            un lien de réinitialisation du mot de passe.
          </p>
          <Link
            to="/login"
            className="inline-flex items-center gap-2 text-orange font-medium hover:underline"
          >
            <ArrowLeft className="w-4 h-4" />
            Retour à la connexion
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-cream px-4">
      <div className="bg-white rounded-3xl max-w-md w-full p-8 shadow-sm border border-black/5">
        <Link
          to="/login"
          className="inline-flex items-center gap-1 text-sm text-gray hover:text-navy mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          Retour
        </Link>

        <div className="w-12 h-12 bg-orange/10 rounded-xl flex items-center justify-center mb-6">
          <Mail className="w-6 h-6 text-orange" />
        </div>

        <h1 className="text-2xl font-semibold text-navy mb-2">
          Mot de passe oublié
        </h1>
        <p className="text-gray text-sm mb-6">
          Entrez votre adresse email et nous vous enverrons un lien pour
          réinitialiser votre mot de passe.
        </p>

        {error && (
          <div className="bg-red-50 text-red-700 text-sm px-4 py-3 rounded-xl mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full px-5 py-3 bg-cream-m rounded-xl border border-black/5 focus:outline-none focus:ring-2 focus:ring-orange/30"
            placeholder="votre@email.com"
            required
            autoFocus
          />
          <Button
            type="submit"
            variant="primary"
            loading={loading}
            disabled={loading || !email}
          >
            {loading ? "Envoi en cours..." : "Envoyer le lien"}
          </Button>
        </form>
      </div>
    </div>
  );
}
