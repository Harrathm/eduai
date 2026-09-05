import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { BookOpen, Zap, ExternalLink } from "lucide-react";
import { enrollmentApi } from "../../../api";
import { PageWrapper } from "../../../components/ui";

interface EnrolledFormation {
  id: number;
  title: string;
  category: string | null;
  thumbnail_url: string | null;
  progress_percent: number;
  status: string;
}

export default function MySkillsPage() {
  const [formations, setFormations] = useState<EnrolledFormation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchEnrolled();
  }, []);

  const fetchEnrolled = async () => {
    setLoading(true);
    try {
      const data = await enrollmentApi.myCourses();
      const list = Array.isArray(data) ? data : (data.items || []);
      const softSkills = list.filter(
        (c: any) => c.category === "soft_skills" || c.category?.startsWith("soft_")
      );
      setFormations(softSkills);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  return (
    <PageWrapper
      title="Mes Formations"
      subtitle="Formations Soft Skills auxquelles vous êtes inscrit"
      icon={<Zap className="w-8 h-8" />}
    >
      {/* Content */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white rounded-2xl p-6 shadow-sm border border-black/5 animate-pulse">
              <div className="h-5 w-48 bg-gray-200 rounded mb-3" />
              <div className="h-4 w-32 bg-gray-100 rounded mb-4" />
              <div className="h-2 bg-gray-100 rounded-full" />
            </div>
          ))}
        </div>
      ) : formations.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 shadow-sm border border-black/5 text-center">
          <BookOpen className="w-12 h-12 text-orange/30 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-navy mb-2">Aucune formation en cours</h3>
          <p className="text-sm text-gray-500 mb-4">
            Inscrivez-vous à des formations Soft Skills pour commencer.
          </p>
          <Link
            to="/dashboard/soft-skills"
            className="inline-flex items-center gap-2 px-4 py-2 bg-orange text-white text-sm font-medium rounded-xl hover:bg-orange/90"
          >
            Découvrir le catalogue
            <ExternalLink className="w-4 h-4" />
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {formations.map((f) => (
            <div key={f.id} className="bg-white rounded-2xl p-6 shadow-sm border border-black/5 hover:shadow-md transition-all">
              <div className="flex items-start justify-between mb-3">
                <h3 className="font-semibold text-navy">{f.title}</h3>
                <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                  f.status === "completed" ? "bg-green-100 text-green-700"
                  : f.status === "active" ? "bg-blue-100 text-blue-700"
                  : "bg-gray-100 text-gray-600"
                }`}>
                  {f.status === "completed" ? "Terminé" : f.status === "active" ? "En cours" : f.status}
                </span>
              </div>
              {f.category && (
                <p className="text-xs text-orange capitalize mb-3">{f.category.replace(/_/g, " ")}</p>
              )}
              <div className="mb-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] text-gray-400">Progression</span>
                  <span className="text-[10px] font-semibold text-navy">{f.progress_percent ?? 0}%</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-1.5">
                  <div
                    className="bg-orange h-1.5 rounded-full transition-all"
                    style={{ width: `${Math.min(f.progress_percent ?? 0, 100)}%` }}
                  />
                </div>
              </div>
              <Link
                to={`/dashboard/courses/${f.id}`}
                className="block w-full text-center px-3 py-2 bg-cream hover:bg-cream-m text-navy text-xs font-medium rounded-xl transition-colors"
              >
                Reprendre
              </Link>
            </div>
          ))}
        </div>
      )}
    </PageWrapper>
  );
}
