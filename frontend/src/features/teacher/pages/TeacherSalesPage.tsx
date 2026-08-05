import { useState, useEffect } from "react";
import { useAuthStore } from "../../../store/authStore";
import { DollarSign, TrendingUp, ShoppingCart, Calendar, RefreshCw } from "lucide-react";
import { teacherSalesApi } from "../../../api";

interface Sale {
  id: number;
  course_id: number;
  amount_paid: number;
  platform_fee: number;
  teacher_revenue: number;
  purchased_at: string;
}

interface SalesData {
  total_sales: number;
  total_revenue: number;
  sales: Sale[];
}

export default function TeacherSalesPage() {
  const { token, user } = useAuthStore();
  const [salesData, setSalesData] = useState<SalesData>({ total_sales: 0, total_revenue: 0, sales: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const isTeacher = user?.role?.toUpperCase() === "TEACHER";

  useEffect(() => {
    if (isTeacher) {
      fetchSales();
    }
  }, [token, isTeacher]);

  const fetchSales = async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const data = await teacherSalesApi.mySales();
      setSalesData(data);
    } catch (err) {
      setError("Erreur de connexion");
    }
    setLoading(false);
  };

  if (!isTeacher) {
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-3xl p-8 shadow-sm border border-black/5">
          <h1 className="text-3xl font-[300] text-navy">
            Mes <span className="italic text-orange">Revenus</span>
          </h1>
          <p className="text-gray mt-2">Consultez vos ventes et revenus</p>
        </div>
        <div className="bg-white rounded-2xl p-12 shadow-sm border border-black/5 text-center">
          <DollarSign className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-700 mb-2">Fonctionnalité réservée</h3>
          <p className="text-gray-500">
            Vous devez être enseignant pour accéder à cette page.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-black/5">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-[300] text-navy">
              Mes <span className="italic text-orange">Revenus</span>
            </h1>
            <p className="text-gray mt-2">Consultez vos ventes et revenus</p>
          </div>
          <button
            onClick={fetchSales}
            disabled={loading}
            className="p-2 hover:bg-white rounded-xl shadow-sm border border-black/5"
          >
            <RefreshCw className={`w-5 h-5 text-gray ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-blue-100 rounded-xl">
              <ShoppingCart className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray">Total ventes</p>
              <p className="text-2xl font-bold text-navy">{salesData.total_sales}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-green-100 rounded-xl">
              <DollarSign className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray">Revenu total</p>
              <p className="text-2xl font-bold text-navy">{salesData.total_revenue.toFixed(2)} TND</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-purple-100 rounded-xl">
              <TrendingUp className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray">Moyenne par vente</p>
              <p className="text-2xl font-bold text-navy">
                {salesData.total_sales > 0 
                  ? (salesData.total_revenue / salesData.total_sales).toFixed(2) 
                  : "0.00"} TND
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Sales List */}
      <div className="bg-white rounded-2xl shadow-sm border border-black/5">
        <div className="p-6 border-b">
          <h2 className="text-lg font-semibold text-navy">Historique des ventes</h2>
        </div>
        
        {loading ? (
          <div className="p-12 text-center text-gray">Chargement...</div>
        ) : error ? (
          <div className="p-12 text-center text-red-500">{error}</div>
        ) : salesData.sales.length === 0 ? (
          <div className="p-12 text-center text-gray">
            <ShoppingCart className="w-12 h-12 mx-auto mb-4 opacity-30" />
            <p>Aucune vente enregistrée</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b bg-gray-50">
                  <th className="px-6 py-3 text-start text-xs font-medium text-gray-500 uppercase">ID</th>
                  <th className="px-6 py-3 text-start text-xs font-medium text-gray-500 uppercase">Cours</th>
                  <th className="px-6 py-3 text-start text-xs font-medium text-gray-500 uppercase">Montant payé</th>
                  <th className="px-6 py-3 text-start text-xs font-medium text-gray-500 uppercase">Commission</th>
                  <th className="px-6 py-3 text-start text-xs font-medium text-gray-500 uppercase">Votre revenu</th>
                  <th className="px-6 py-3 text-start text-xs font-medium text-gray-500 uppercase">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {salesData.sales.map((sale) => (
                  <tr key={sale.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm text-gray">#{sale.id}</td>
                    <td className="px-6 py-4 text-sm font-medium text-navy">Cours #{sale.course_id}</td>
                    <td className="px-6 py-4 text-sm text-gray">{sale.amount_paid.toFixed(2)} TND</td>
                    <td className="px-6 py-4 text-sm text-orange">{sale.platform_fee.toFixed(2)} TND</td>
                    <td className="px-6 py-4 text-sm font-semibold text-green-600">{sale.teacher_revenue.toFixed(2)} TND</td>
                    <td className="px-6 py-4 text-sm text-gray">
                      <div className="flex items-center gap-1">
                        <Calendar className="w-4 h-4" />
                        {sale.purchased_at ? new Date(sale.purchased_at).toLocaleDateString("fr-FR") : "—"}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
