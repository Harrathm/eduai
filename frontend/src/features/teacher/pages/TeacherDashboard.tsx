import { useAuthStore } from "../../../store/authStore";

export default function TeacherDashboard() {
  const { user } = useAuthStore();
  
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-navy rounded-3xl p-8">
        <h1 className="text-4xl font-[300] text-white">
          Tableau de <span className="italic text-orange-l">Bord</span>
        </h1>
        <p className="text-white/50 mt-2">Bienvenue, {user?.full_name}</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <div className="text-4xl font-[300] text-orange">0</div>
          <div className="text-sm text-gray mt-1">Mes Cours</div>
        </div>
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <div className="text-4xl font-[300] text-green-600">0</div>
          <div className="text-sm text-gray mt-1">Étudiants</div>
        </div>
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <div className="text-4xl font-[300] text-yellow-600">0</div>
          <div className="text-sm text-gray mt-1">DT Revenus</div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-black/5">
        <h2 className="text-2xl font-[300] text-navy mb-6">Accès Rapide</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <a href="/dashboard/courses" className="block p-6 bg-gradient-to-br from-orange-p to-cream rounded-2xl text-center hover:shadow-md transition-shadow cursor-pointer">
            <div className="text-3xl mb-2">📚</div>
            <div className="font-medium text-navy">Mes Cours</div>
          </a>
          <a href="/dashboard/assignments" className="block p-6 bg-gradient-to-br from-blue-50 to-cream rounded-2xl text-center hover:shadow-md transition-shadow cursor-pointer">
            <div className="text-3xl mb-2">📝</div>
            <div className="font-medium text-navy">Devoirs</div>
          </a>
          <a href="/dashboard/ai-studio" className="block p-6 bg-gradient-to-br from-purple-50 to-cream rounded-2xl text-center hover:shadow-md transition-shadow cursor-pointer">
            <div className="text-3xl mb-2">🎨</div>
            <div className="font-medium text-navy">IA Studio</div>
          </a>
          <a href="/dashboard/wallet" className="block p-6 bg-gradient-to-br from-green-50 to-cream rounded-2xl text-center hover:shadow-md transition-shadow cursor-pointer">
            <div className="text-3xl mb-2">💰</div>
            <div className="font-medium text-navy">Revenus</div>
          </a>
        </div>
      </div>
    </div>
  );
}