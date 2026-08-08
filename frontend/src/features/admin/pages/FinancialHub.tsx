import { useState, useEffect } from "react";
import { useAuthStore } from "../../../store/authStore";
import { Search, Download, Edit2, Save, X, Wallet, Coins, TrendingUp } from "lucide-react";
import { Button, Spinner } from "@/components/ui";
import { adminUsersAll } from "../../../api";

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
      const data = await adminUsersAll.list();
      setUsers(Array.isArray(data) ? data : (data as any).items || []);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const updateBalance = async (userId: number) => {
    if (!token) return;
    try {
      await adminUsersAll.update(userId, {
        token_balance: editValues.token_balance,
        dt_balance: editValues.dt_balance,
      });
      setEditingId(null);
      fetchUsers();
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
                className="w-full ps-12 pe-4 py-3 bg-cream-m rounded-xl border border-black/5 focus:border-orange focus:outline-none"
                placeholder="Rechercher..."
              />
            </div>
          </div>
          <div className="flex gap-2">
            {(["all", "admin", "teacher", "student"] as const).map((f) => (
              <Button
                key={f}
                variant={filter === f ? "primary" : "ghost"}
                onClick={() => setFilter(f)}
              >
                {f}
              </Button>
            ))}
          </div>
          <Button variant="secondary">
            <Download className="w-4 h-4" />
            Exporter
          </Button>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-3xl shadow-sm border border-black/5 overflow-hidden">
        {loading ? (
          <div className="text-center py-12"><Spinner size="lg" /></div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-cream-m">
                <tr>
                  <th className="text-start px-6 py-4 text-xs font-semibold text-gray uppercase">
                    Utilisateur
                  </th>
                  <th className="text-start px-6 py-4 text-xs font-semibold text-gray uppercase">
                    Rôle
                  </th>
                  <th className="text-start px-6 py-4 text-xs font-semibold text-gray uppercase">
                    Status
                  </th>
                  <th className="text-end px-6 py-4 text-xs font-semibold text-gray uppercase">
                    Tokens
                  </th>
                  <th className="text-end px-6 py-4 text-xs font-semibold text-gray uppercase">
                    DT
                  </th>
                  <th className="text-end px-6 py-4 text-xs font-semibold text-gray uppercase">
                    Tokens Dépensés
                  </th>
                  <th className="text-end px-6 py-4 text-xs font-semibold text-gray uppercase">
                    DT Dépensés
                  </th>
                  <th className="text-end px-6 py-4 text-xs font-semibold text-gray uppercase">
                    DT Gagnés
                  </th>
                  <th className="text-start px-6 py-4 text-xs font-semibold text-gray uppercase">
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
                    <td className="px-6 py-4 text-end font-medium">
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
                          className="w-20 px-2 py-1 bg-cream-m rounded text-end"
                        />
                      ) : (
                        u.token_balance
                      )}
                    </td>
                    <td className="px-6 py-4 text-end font-medium">
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
                          className="w-20 px-2 py-1 bg-cream-m rounded text-end"
                        />
                      ) : (
                        u.dt_balance
                      )}
                    </td>
                    <td className="px-6 py-4 text-end text-gray text-sm">
                      {u.total_tokens_spent}
                    </td>
                    <td className="px-6 py-4 text-end text-gray text-sm">
                      {u.total_dt_spent}
                    </td>
                    <td className="px-6 py-4 text-end">
                      <span className="text-green-600 font-medium">
                        +{u.total_dt_earned}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      {editingId === u.id ? (
                        <div className="flex gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => updateBalance(u.id)}
                          >
                            <Save className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setEditingId(null)}
                          >
                            <X className="w-4 h-4" />
                          </Button>
                        </div>
                      ) : (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setEditingId(u.id);
                            setEditValues({
                              token_balance: u.token_balance,
                              dt_balance: u.dt_balance,
                            });
                          }}
                        >
                          <Edit2 className="w-4 h-4 text-gray" />
                        </Button>
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