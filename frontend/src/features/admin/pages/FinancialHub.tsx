import { useState, useEffect } from "react";
import { useAuthStore } from "../../../store/authStore";
import { Search, Download, Edit2, Save, X, Wallet, Coins, TrendingUp } from "lucide-react";

const API_URL = "";

interface UserAccount {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  token_balance: number;
  dt_balance: number;
  total_tokens_spent: number;
  total_dt_spent: number;
  total_dt_earned: number;
}

export default function FinancialHub() {
  const { token } = useAuthStore();
  const [users, setUsers] = useState<UserAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editValues, setEditValues] = useState({ token_balance: 0, dt_balance: 0 });
  const [filter, setFilter] = useState<"all" | "admin" | "teacher" | "student">("all");

  useEffect(() => {
    fetchUsers();
  }, [token, filter]);

  const fetchUsers = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/admin/users-all`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setUsers(Array.isArray(data) ? data : data.items || []);
      }
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const updateBalance = async (userId: number) => {
    if (!token) return;
    try {
      const res = await fetch(`${API_URL}/api/admin/users/${userId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          token_balance: editValues.token_balance,
          dt_balance: editValues.dt_balance,
        }),
      });
      if (res.ok) {
        setEditingId(null);
        fetchUsers();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const filtered = users.filter((u) => {
    const matches = search
      ? u.full_name.toLowerCase().includes(search.toLowerCase()) ||
        u.email.toLowerCase().includes(search.toLowerCase())
      : true;
    return matches && (filter === "all" || u.role === filter);
  });

  const totals = users.reduce(
    (acc, u) => ({
      tokens: acc.tokens + u.token_balance,
      dt: acc.dt + u.dt_balance,
      tokensSpent: acc.tokensSpent + u.total_tokens_spent,
      dtSpent: acc.dtSpent + u.total_dt_spent,
      dtEarned: acc.dtEarned + u.total_dt_earned,
    }),
    { tokens: 0, dt: 0, tokensSpent: 0, dtSpent: 0, dtEarned: 0 }
  );

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-black/5">
        <h1 className="text-3xl font-[300] text-navy">
          Financial <span className="italic text-orange">Hub</span>
        </h1>
        <p className="text-gray mt-2">
          Gérez les utilisateurs et leurs soldes (Tokens & DT)
        </p>
      </div>

      {/* Totals */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-orange-p to-cream rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-2">
            <Coins className="w-5 h-5 text-orange" />
            <span className="text-sm text-gray">Total Tokens</span>
          </div>
          <div className="text-3xl font-[300] text-navy">{totals.tokens}</div>
        </div>
        <div className="bg-gradient-to-br from-yellow-50 to-cream rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-2">
            <Wallet className="w-5 h-5 text-yellow-600" />
            <span className="text-sm text-gray">Total DT</span>
          </div>
          <div className="text-3xl font-[300] text-navy">{totals.dt}</div>
        </div>
        <div className="bg-gradient-to-br from-green-50 to-cream rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-5 h-5 text-green-600" />
            <span className="text-sm text-gray">Revenus DT</span>
          </div>
          <div className="text-3xl font-[300] text-green-700">{totals.dtEarned}</div>
        </div>
        <div className="bg-gradient-to-br from-purple-50 to-cream rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-2">
            <Coins className="w-5 h-5 text-purple-600" />
            <span className="text-sm text-gray">Tokens Consommés</span>
          </div>
          <div className="text-3xl font-[300] text-purple-700">{totals.tokensSpent}</div>
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
            {(["all", "admin", "teacher", "student"] as const).map((f) => (
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
              </button>
            ))}
          </div>
          <button className="flex items-center gap-2 px-4 py-2 bg-navy text-white rounded-xl text-sm font-medium">
            <Download className="w-4 h-4" />
            Exporter
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-3xl shadow-sm border border-black/5 overflow-hidden">
        {loading ? (
          <div className="text-center py-12 text-gray">Chargement...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-cream-m">
                <tr>
                  <th className="text-left px-6 py-4 text-xs font-semibold text-gray uppercase">
                    Utilisateur
                  </th>
                  <th className="text-left px-6 py-4 text-xs font-semibold text-gray uppercase">
                    Rôle
                  </th>
                  <th className="text-left px-6 py-4 text-xs font-semibold text-gray uppercase">
                    Status
                  </th>
                  <th className="text-right px-6 py-4 text-xs font-semibold text-gray uppercase">
                    Tokens
                  </th>
                  <th className="text-right px-6 py-4 text-xs font-semibold text-gray uppercase">
                    DT
                  </th>
                  <th className="text-right px-6 py-4 text-xs font-semibold text-gray uppercase">
                    Tokens Dépensés
                  </th>
                  <th className="text-right px-6 py-4 text-xs font-semibold text-gray uppercase">
                    DT Dépensés
                  </th>
                  <th className="text-right px-6 py-4 text-xs font-semibold text-gray uppercase">
                    DT Gagnés
                  </th>
                  <th className="text-left px-6 py-4 text-xs font-semibold text-gray uppercase">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-black/5">
                {filtered.map((u) => (
                  <tr key={u.id} className="hover:bg-cream/50">
                    <td className="px-6 py-4">
                      <div>
                        <div className="font-medium">{u.full_name}</div>
                        <div className="text-sm text-gray">{u.email}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`px-2 py-1 text-xs rounded-full ${
                          u.role === "admin"
                            ? "bg-purple-100 text-purple-700"
                            : u.role === "teacher"
                            ? "bg-green-100 text-green-700"
                            : "bg-blue-100 text-blue-700"
                        }`}
                      >
                        {u.role}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`px-2 py-1 text-xs rounded-full ${
                          u.is_active
                            ? "bg-green-100 text-green-700"
                            : "bg-red-100 text-red-700"
                        }`}
                      >
                        {u.is_active ? "Actif" : "Inactif"}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right font-medium">
                      {editingId === u.id ? (
                        <input
                          type="number"
                          value={editValues.token_balance}
                          onChange={(e) =>
                            setEditValues({
                              ...editValues,
                              token_balance: Number(e.target.value),
                            })
                          }
                          className="w-20 px-2 py-1 bg-cream-m rounded text-right"
                        />
                      ) : (
                        u.token_balance
                      )}
                    </td>
                    <td className="px-6 py-4 text-right font-medium">
                      {editingId === u.id ? (
                        <input
                          type="number"
                          value={editValues.dt_balance}
                          onChange={(e) =>
                            setEditValues({
                              ...editValues,
                              dt_balance: Number(e.target.value),
                            })
                          }
                          className="w-20 px-2 py-1 bg-cream-m rounded text-right"
                        />
                      ) : (
                        u.dt_balance
                      )}
                    </td>
                    <td className="px-6 py-4 text-right text-gray text-sm">
                      {u.total_tokens_spent}
                    </td>
                    <td className="px-6 py-4 text-right text-gray text-sm">
                      {u.total_dt_spent}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <span className="text-green-600 font-medium">
                        +{u.total_dt_earned}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      {editingId === u.id ? (
                        <div className="flex gap-1">
                          <button
                            onClick={() => updateBalance(u.id)}
                            className="p-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200"
                          >
                            <Save className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => setEditingId(null)}
                            className="p-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => {
                            setEditingId(u.id);
                            setEditValues({
                              token_balance: u.token_balance,
                              dt_balance: u.dt_balance,
                            });
                          }}
                          className="p-2 bg-cream-m rounded-lg hover:bg-cream"
                        >
                          <Edit2 className="w-4 h-4 text-gray" />
                        </button>
                      )}
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