import { useState, useEffect } from "react";
import { useAuthStore } from "../../../store/authStore";
import { Check, X, Search, Download } from "lucide-react";

const API_URL = "";

interface TeacherRegistration {
  id: number;
  email: string;
  full_name: string;
  school_name: string;
  status: "pending" | "approved" | "rejected";
  requested_at: string;
}

export default function EnrollmentManager() {
  const { token } = useAuthStore();
  const [registrations, setRegistrations] = useState<TeacherRegistration[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<"all" | "pending" | "approved" | "rejected">("all");

  useEffect(() => {
    fetchRegistrations();
  }, [token]);

  const fetchRegistrations = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/admin/teacher-registrations`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setRegistrations(Array.isArray(data) ? data : data.items || []);
      }
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const approveRegistration = async (id: number) => {
    if (!token) return;
    try {
      const res = await fetch(`${API_URL}/api/admin/teacher-registrations/${id}/review?status=approved`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (res.ok) fetchRegistrations();
    } catch (err) {
      console.error(err);
    }
  };

  const rejectRegistration = async (id: number) => {
    if (!token) return;
    try {
      const res = await fetch(`${API_URL}/api/admin/teacher-registrations/${id}/review?status=rejected&rejection_reason=Rejected%20by%20admin`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (res.ok) fetchRegistrations();
    } catch (err) {
      console.error(err);
    }
  };

  const filtered = registrations.filter((r) => {
    const matches = search
      ? r.full_name.toLowerCase().includes(search.toLowerCase()) ||
        r.email.toLowerCase().includes(search.toLowerCase())
      : true;
    return matches && (filter === "all" || r.status === filter);
  });

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-black/5">
        <div className="flex justify-between items-center mb-2">
          <div>
            <h1 className="text-3xl font-[300] text-navy">
              Enrollment <span className="italic text-orange">Manager</span>
            </h1>
            <p className="text-gray mt-2">
              Gérez les inscriptions des enseignants
            </p>
          </div>
          <button className="flex items-center gap-2 px-4 py-2 bg-navy text-white rounded-xl text-sm font-medium">
            <Download className="w-4 h-4" />
            Exporter CSV
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-3xl p-6 shadow-sm border border-black/5">
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-12 pr-4 py-3 bg-cream-m rounded-xl border border-black/5 focus:border-orange focus:outline-none"
                placeholder="Rechercher..."
              />
            </div>
          </div>
          <div className="flex gap-2">
            {(["all", "pending", "approved", "rejected"] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-4 py-2 rounded-xl text-sm font-medium capitalize ${
                  filter === f
                    ? "bg-orange text-white"
                    : "bg-cream-m text-gray hover:bg-cream"
                }`}
              >
                {f}
                {f === "pending" &&
                  registrations.filter((r) => r.status === "pending").length > 0 && (
                    <span className="ml-2 bg-white text-orange text-xs px-2 py-0.5 rounded-full">
                      {registrations.filter((r) => r.status === "pending").length}
                    </span>
                  )}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-3xl shadow-sm border border-black/5 overflow-hidden">
        {loading ? (
          <div className="text-center py-12 text-gray">Chargement...</div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-12 text-gray">
            Aucune inscription trouvée
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-cream-m">
              <tr>
                <th className="text-left px-6 py-4 text-xs font-semibold text-gray uppercase">
                  Enseignant
                </th>
                <th className="text-left px-6 py-4 text-xs font-semibold text-gray uppercase">
                  École
                </th>
                <th className="text-left px-6 py-4 text-xs font-semibold text-gray uppercase">
                  Status
                </th>
                <th className="text-left px-6 py-4 text-xs font-semibold text-gray uppercase">
                  Date
                </th>
                <th className="text-left px-6 py-4 text-xs font-semibold text-gray uppercase">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-black/5">
              {filtered.map((r) => (
                <tr key={r.id} className="hover:bg-cream/50">
                  <td className="px-6 py-4">
                    <div>
                      <div className="font-medium">{r.full_name}</div>
                      <div className="text-sm text-gray">{r.email}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-gray">{r.school_name}</td>
                  <td className="px-6 py-4">
                    <span
                      className={`px-3 py-1 text-xs rounded-full ${
                        r.status === "pending"
                          ? "bg-yellow-100 text-yellow-700"
                          : r.status === "approved"
                          ? "bg-green-100 text-green-700"
                          : "bg-red-100 text-red-700"
                      }`}
                    >
                      {r.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-gray text-sm">
                    {new Date(r.requested_at).toLocaleDateString("fr-FR")}
                  </td>
                  <td className="px-6 py-4">
                    {r.status === "pending" && (
                      <div className="flex gap-2">
                        <button
                          onClick={() => approveRegistration(r.id)}
                          className="p-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200"
                        >
                          <Check className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => rejectRegistration(r.id)}
                          className="p-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}