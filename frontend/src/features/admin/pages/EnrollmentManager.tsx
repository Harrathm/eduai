import { useState, useEffect } from "react";
import { useAuthStore } from "../../../store/authStore";
import { Check, X, Search, Download } from "lucide-react";
import { Button, Spinner } from "@/components/ui";
import { adminTeacherRegistrations } from "../../../api";

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
      const data = await adminTeacherRegistrations.list();
      setRegistrations(Array.isArray(data) ? data : (data as any).items || []);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const approveRegistration = async (id: number) => {
    if (!token) return;
    try {
      await adminTeacherRegistrations.approve(id);
      fetchRegistrations();
    } catch (err) {
      console.error(err);
    }
  };

  const rejectRegistration = async (id: number) => {
    if (!token) return;
    try {
      await adminTeacherRegistrations.reject(id);
      fetchRegistrations();
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
          <Button variant="secondary">
            <Download className="w-4 h-4" />
            Exporter CSV
          </Button>
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
                className="w-full ps-12 pe-4 py-3 bg-cream-m rounded-xl border border-black/5 focus:border-orange focus:outline-none"
                placeholder="Rechercher..."
              />
            </div>
          </div>
          <div className="flex gap-2">
            {(["all", "pending", "approved", "rejected"] as const).map((f) => (
              <Button
                key={f}
                variant={filter === f ? "primary" : "ghost"}
                onClick={() => setFilter(f)}
              >
                {f}
                {f === "pending" &&
                  registrations.filter((r) => r.status === "pending").length > 0 && (
                    <span className="ml-2 bg-white text-orange text-xs px-2 py-0.5 rounded-full">
                      {registrations.filter((r) => r.status === "pending").length}
                    </span>
                  )}
              </Button>
            ))}
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-3xl shadow-sm border border-black/5 overflow-hidden">
        {loading ? (
          <div className="text-center py-12"><Spinner size="lg" /></div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-12 text-gray">
            Aucune inscription trouvée
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-cream-m">
              <tr>
                <th className="text-start px-6 py-4 text-xs font-semibold text-gray uppercase">
                  Enseignant
                </th>
                <th className="text-start px-6 py-4 text-xs font-semibold text-gray uppercase">
                  École
                </th>
                <th className="text-start px-6 py-4 text-xs font-semibold text-gray uppercase">
                  Status
                </th>
                <th className="text-start px-6 py-4 text-xs font-semibold text-gray uppercase">
                  Date
                </th>
                <th className="text-start px-6 py-4 text-xs font-semibold text-gray uppercase">
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
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => approveRegistration(r.id)}
                        >
                          <Check className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => rejectRegistration(r.id)}
                        >
                          <X className="w-4 h-4" />
                        </Button>
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