import { useState, useEffect } from "react";
import { useTranslation } from 'react-i18next';
import { useAuthStore } from "../../../store/authStore";
import { DollarSign, TrendingUp, ShoppingCart, Calendar, RefreshCw } from "lucide-react";
import { teacherSalesApi } from "../../../api";
import { Button } from "../../../components/ui";

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
  const { t } = useTranslation();
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
      setError(t('teacher.sales.error'));
    }
    setLoading(false);
  };

  if (!isTeacher) {
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-3xl p-8 shadow-sm border border-black/5">
          <h1 className="text-3xl font-[300] text-navy">
            {t('teacher.sales.title')} <span className="italic text-orange">{t('teacher.sales.titleSuffix')}</span>
          </h1>
          <p className="text-gray mt-2">{t('teacher.sales.subtitle')}</p>
        </div>
        <div className="bg-white rounded-2xl p-12 shadow-sm border border-black/5 text-center">
          <DollarSign className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-700 mb-2">{t('teacher.sales.accessDenied')}</h3>
          <p className="text-gray-500">
            {t('teacher.sales.accessDeniedMessage')}
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
              {t('teacher.sales.title')} <span className="italic text-orange">{t('teacher.sales.titleSuffix')}</span>
            </h1>
            <p className="text-gray mt-2">{t('teacher.sales.subtitle')}</p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={fetchSales}
            loading={loading}
          >
            {!loading && <RefreshCw className="w-5 h-5 text-gray" />}
          </Button>
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
              <p className="text-sm text-gray">{t('teacher.sales.kpi.totalSales')}</p>
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
              <p className="text-sm text-gray">{t('teacher.sales.kpi.totalRevenue')}</p>
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
              <p className="text-sm text-gray">{t('teacher.sales.kpi.averagePerSale')}</p>
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
          <h2 className="text-lg font-semibold text-navy">{t('teacher.sales.historyTitle')}</h2>
        </div>
        
        {loading ? (
          <div className="p-12 text-center text-gray">{t('teacher.sales.loading')}</div>
        ) : error ? (
          <div className="p-12 text-center text-red-500">{error}</div>
        ) : salesData.sales.length === 0 ? (
          <div className="p-12 text-center text-gray">
            <ShoppingCart className="w-12 h-12 mx-auto mb-4 opacity-30" />
            <p>{t('teacher.sales.noResults')}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b bg-gray-50">
                  <th className="px-6 py-3 text-start text-xs font-medium text-gray-500 uppercase">{t('teacher.sales.table.id')}</th>
                  <th className="px-6 py-3 text-start text-xs font-medium text-gray-500 uppercase">{t('teacher.sales.table.course')}</th>
                  <th className="px-6 py-3 text-start text-xs font-medium text-gray-500 uppercase">{t('teacher.sales.table.amountPaid')}</th>
                  <th className="px-6 py-3 text-start text-xs font-medium text-gray-500 uppercase">{t('teacher.sales.table.commission')}</th>
                  <th className="px-6 py-3 text-start text-xs font-medium text-gray-500 uppercase">{t('teacher.sales.table.yourRevenue')}</th>
                  <th className="px-6 py-3 text-start text-xs font-medium text-gray-500 uppercase">{t('teacher.sales.table.date')}</th>
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
