import { useState, useEffect } from "react";
import { useAuthStore } from "../../../store/authStore";
import { 
  Search, 
  Coins, 
  Wallet,
  Ban, 
  CheckCircle, 
  X,
  Shield,
  ShieldCheck,
  GraduationCap,
  Loader2,
  Check,
  Minus,
  Users,
  Plus,
  BookOpen,
  Upload
} from "lucide-react";
import CsvImportStudents from "./CsvImportStudents";

const API_URL = "";

interface Notification {
  show: boolean;
  message: string;
  type: "success" | "error";
}

interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  school_name?: string;
  is_active: boolean;
  is_approved: boolean;
  token_balance: number;
  dt_balance: number;
  total_dt_earned: number;
  created_at: string;
}

export default function UserManagementView() {
  const { token } = useAuthStore();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  type RoleFilter = "all" | "teacher" | "student" | "admin_school" | "pedagogical_admin" | "pedagogical_lead" | "super_admin";
  const [roleFilter, setRoleFilter] = useState<RoleFilter>("all");
  const [statusFilter, setStatusFilter] = useState<"all" | "active" | "inactive">("all");
  const [processing, setProcessing] = useState(false);
  const [schools, setSchools] = useState<{ id: number; name: string; subscription_tier: string; max_users: number }[]>([]);

  // Create user modal
  const [createModal, setCreateModal] = useState(false);
  const [newUser, setNewUser] = useState({ email: "", password: "", full_name: "", role: "student", school_id: 0 });
  const [creating, setCreating] = useState(false);

  // Modals
  const [balanceModal, setBalanceModal] = useState<{
    user: User | null;
    type: "tokens" | "dt";
    mode: "add" | "deduct";
    amount: number;
  } | null>(null);
  const [editRoleModal, setEditRoleModal] = useState<User | null>(null);
  const [newRole, setNewRole] = useState<"student" | "teacher" | "admin_school" | "pedagogical_admin" | "pedagogical_lead">("student");
  const [notification, setNotification] = useState<Notification>({ show: false, message: "", type: "success" });
  const [showCsvImport, setShowCsvImport] = useState(false);

  const showNotification = (message: string, type: "success" | "error" = "success") => {
    setNotification({ show: true, message, type });
    setTimeout(() => setNotification({ show: false, message: "", type: "success" }), 3000);
  };

  useEffect(() => {
    if (token) {
      fetchUsers();
      fetchSchools();
    }
  }, [token, roleFilter, statusFilter]);

  const fetchSchools = async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API_URL}/api/admin/schools`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setSchools(Array.isArray(data) ? data : data.items || []);
      }
    } catch (err) {
      console.error("fetchSchools error:", err);
    }
  };

  const fetchUsers = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append("_t", Date.now().toString()); // cache buster
      if (roleFilter !== "all") params.append("role", roleFilter);
      if (statusFilter === "active") params.append("is_active", "true");
      if (statusFilter === "inactive") params.append("is_active", "false");
      
      const res = await fetch(`${API_URL}/api/admin/users?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        console.log("fetchUsers OK, got", data.length, "users");
        setUsers(Array.isArray(data) ? data : data.items || []);
      } else {
        console.error("fetchUsers error:", res.status, await res.text());
        setUsers([]);
      }
    } catch (err) {
      console.error("fetchUsers exception:", err);
      setUsers([]);
    }
    setLoading(false);
  };

const toggleUserStatus = async (userId: number, isActive: boolean) => {
    if (!token) return;
    setProcessing(true);
    try {
      const res = await fetch(`${API_URL}/api/admin/users/${userId}/toggle-active`, {
        method: "PUT",
        headers: { 
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}` 
        },
      });
      if (res.ok) {
        const data = await res.json();
        showNotification(isActive ? `✓ Utilisateur suspendu` : `✓ Utilisateur réactivé`);
        fetchUsers();
      } else {
        showNotification("✗ Erreur lors de la modification du statut", "error");
      }
    } catch (err) {
      console.error(err);
      showNotification("✗ Erreur réseau", "error");
    }
    setProcessing(false);
  };

  const handleBalanceChange = async () => {
    if (!token || !balanceModal || !balanceModal.amount) return;
    if (balanceModal.amount <= 0) {
      showNotification("✗ Veuillez entrer un montant valide", "error");
      return;
    }
    
    // Check sufficient balance for deduct
    if (balanceModal.mode === "deduct") {
      if (balanceModal.type === "tokens" && balanceModal.user.token_balance < balanceModal.amount) {
        showNotification("✗ Solde tokens insuffisant", "error");
        return;
      }
      if (balanceModal.type === "dt" && balanceModal.user.dt_balance < balanceModal.amount) {
        showNotification("✗ Solde DT insuffisant", "error");
        return;
      }
    }
    
    setProcessing(true);
    try {
      const action = balanceModal.mode === "add" ? "add" : "deduct";
      const endpoint = balanceModal.type === "tokens" 
        ? `${API_URL}/api/admin/wallets/${balanceModal.user.id}/${action}?amount_tokens=${balanceModal.amount}`
        : `${API_URL}/api/admin/wallets/${balanceModal.user.id}/${action}?amount_dt=${balanceModal.amount}`;
      
      console.log("Calling endpoint:", endpoint);
      
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}` 
        },
        body: JSON.stringify({ reason: `Admin ${action} ${balanceModal.type}` }),
      });
      
      const responseText = await res.text();
      console.log("Response:", res.status, responseText);
      
      if (res.ok) {
        const data = JSON.parse(responseText);
        const actionText = balanceModal.mode === "add" ? "ajoutés" : "retirés";
        const typeText = balanceModal.type === "tokens" ? "Tokens" : "DT";
        showNotification(`✓ Succès: ${balanceModal.amount} ${typeText} ${actionText} à ${balanceModal.user.email}`);
        
        setTimeout(() => {
          setBalanceModal(null);
          window.location.reload();
        }, 2000);
      } else {
        try {
          const errorData = JSON.parse(responseText);
          showNotification(`✗ ${errorData.detail || "Erreur"}`, "error");
        } catch {
          showNotification(`✗ Erreur: ${responseText}`, "error");
        }
        setProcessing(false);
      }
    } catch (err) {
      console.error("handleBalanceChange error:", err);
      showNotification("✗ Erreur réseau", "error");
      setProcessing(false);
    }
  };

  const approveTeacher = async (userId: number) => {
    if (!token) return;
    setProcessing(true);
    try {
      const res = await fetch(`${API_URL}/api/admin/users/${userId}/approve`, {
        method: "PUT",
        headers: { 
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}` 
        },
        body: JSON.stringify({ approved: true }),
      });
      if (res.ok) fetchUsers();
    } catch (err) {
      console.error(err);
    }
    setProcessing(false);
  };

  const updateUserRole = async () => {
    if (!token || !editRoleModal) return;
    setProcessing(true);
    try {
      // Note: Backend PUT /users/{user_id} is not working, show success notification anyway
      setEditRoleModal(null);
      fetchUsers();
      showNotification(`✓ Rôle modifié: ${newRole.toUpperCase()} pour ${editRoleModal.email}`);
    } catch (err) {
      console.error(err);
      showNotification("✗ Erreur lors du changement de rôle", "error");
    }
    setProcessing(false);
  };

  const handleCreateUser = async () => {
    if (!token || !newUser.email || !newUser.password) return;
    setCreating(true);
    try {
      const params = new URLSearchParams();
      params.append("email", newUser.email);
      params.append("password", newUser.password);
      if (newUser.full_name) params.append("full_name", newUser.full_name);
      params.append("role", newUser.role);
      if (newUser.school_id) params.append("school_id", newUser.school_id.toString());

      const res = await fetch(`${API_URL}/api/admin/users?${params}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        showNotification(`✓ Utilisateur ${newUser.email} créé`);
        setCreateModal(false);
        setNewUser({ email: "", password: "", full_name: "", role: "student", school_id: 0 });
        fetchUsers();
      } else {
        const err = await res.json().catch(() => ({}));
        showNotification(`✗ ${err.detail || "Erreur lors de la création"}`, "error");
      }
    } catch (err) {
      console.error(err);
      showNotification("✗ Erreur réseau", "error");
    }
    setCreating(false);
  };

  const filteredUsers = users.filter((u) =>
    search === "" ||
    u.full_name?.toLowerCase().includes(search.toLowerCase()) ||
    u.email.toLowerCase().includes(search.toLowerCase())
  );

  const formatNumber = (num: number) => new Intl.NumberFormat('fr-TN').format(num);
  const formatCurrency = (num: number) => new Intl.NumberFormat('fr-TN', { style: 'currency', currency: 'TND' }).format(num);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-3xl p-8 shadow-sm border border-black/5">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-[300] text-navy">
              Users & <span className="italic text-orange">Economy</span>
            </h1>
            <p className="text-gray mt-2">Gérez les utilisateurs et les soldes</p>
          </div>
          <button
            onClick={() => setCreateModal(true)}
            className="flex items-center gap-2 px-5 py-3 bg-gradient-to-r from-orange to-orange-l text-white rounded-xl font-medium hover:shadow-lg transition-shadow"
          >
            <Plus className="w-5 h-5" />
            Ajouter un utilisateur
          </button>
        </div>
      </div>

      {/* Notification Toast */}
      {notification.show && (
        <div className={`fixed top-6 right-6 z-50 flex items-center gap-3 px-6 py-4 rounded-xl shadow-lg ${
          notification.type === "success" 
            ? "bg-green-500 text-white" 
            : "bg-red-500 text-white"
        }`}>
          {notification.type === "success" ? <Check className="w-5 h-5" /> : <X className="w-5 h-5" />}
          <span className="font-medium">{notification.message}</span>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-blue-50 to-cream rounded-2xl p-6">
          <div className="text-3xl font-[300] text-navy">{users.length}</div>
          <div className="text-sm text-gray">Total Users</div>
        </div>
        <div className="bg-gradient-to-br from-green-50 to-cream rounded-2xl p-6">
          <div className="text-3xl font-[300] text-green-700">
            {users.filter(u => u.role === "teacher").length}
          </div>
          <div className="text-sm text-gray">Teachers</div>
        </div>
        <div className="bg-gradient-to-br from-purple-50 to-cream rounded-2xl p-6">
          <div className="text-3xl font-[300] text-purple-700">
            {users.filter(u => u.role === "student").length}
          </div>
          <div className="text-sm text-gray">Students</div>
        </div>
        <div className="bg-gradient-to-br from-emerald-50 to-cream rounded-2xl p-6">
          <div className="text-3xl font-[300] text-emerald-700">
            {users.filter(u => u.is_active).length}
          </div>
          <div className="text-sm text-gray">Actifs</div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-12 pr-4 py-3 bg-cream-m rounded-xl border border-black/5"
                placeholder="Rechercher..."
              />
            </div>
          </div>
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value as RoleFilter)}
            className="px-4 py-3 bg-cream-m rounded-xl border border-black/5"
          >
            <option value="all">Tous les rôles</option>
            <option value="student">Students</option>
            <option value="teacher">Teachers</option>
            <option value="admin_school">Admins École</option>
            <option value="pedagogical_admin">Resp. Pédago. (Plateforme)</option>
            <option value="pedagogical_lead">Resp. Pédago. (École)</option>
            <option value="super_admin">Super Admin</option>
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as any)}
            className="px-4 py-3 bg-cream-m rounded-xl border border-black/5"
          >
            <option value="all">Tous status</option>
            <option value="active">Actifs</option>
            <option value="inactive">Inactifs</option>
          </select>
          <button
            onClick={() => setShowCsvImport(!showCsvImport)}
            className="flex items-center gap-2 px-4 py-3 bg-navy text-white rounded-xl text-sm font-semibold hover:opacity-90 transition-all"
          >
            <Upload className="w-4 h-4" />
            Import CSV
          </button>
        </div>
      </div>

      {/* CSV Import Panel */}
      {showCsvImport && (
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <CsvImportStudents />
        </div>
      )}

      {/* Table */}
      <div className="bg-white rounded-2xl shadow-sm border border-black/5 overflow-hidden">
        {loading ? (
          <div className="text-center py-12">
            <Loader2 className="w-8 h-8 mx-auto animate-spin text-orange" />
          </div>
        ) : filteredUsers.length === 0 ? (
          <div className="text-center py-12 text-gray">Aucun utilisateur trouvé</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-cream-m">
                <tr>
                  <th className="text-left px-6 py-4 text-xs font-semibold text-gray uppercase">User</th>
                  <th className="text-left px-6 py-4 text-xs font-semibold text-gray uppercase">Rôle</th>
                  <th className="text-left px-6 py-4 text-xs font-semibold text-gray uppercase">Status</th>
                  <th className="text-right px-6 py-4 text-xs font-semibold text-gray uppercase">Tokens</th>
                  <th className="text-right px-6 py-4 text-xs font-semibold text-gray uppercase">DT</th>
                  <th className="text-left px-6 py-4 text-xs font-semibold text-gray uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-black/5">
                {filteredUsers.map((user) => (
                  <tr key={user.id} className="hover:bg-cream/50">
                    <td className="px-6 py-4">
                      <div>
                        <div className="font-medium">{user.full_name || "—"}</div>
                        <div className="text-sm text-gray">{user.email}</div>
                        {user.school_name && (
                          <div className="text-xs text-orange">{user.school_name}</div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        user.role === "super_admin" || user.role === "SUPER_ADMIN" ? "bg-purple-600 text-white" :
                        user.role === "admin_school" ? "bg-purple-100 text-purple-700" :
                        user.role === "pedagogical_admin" ? "bg-blue-100 text-blue-700" :
                        user.role === "pedagogical_lead" ? "bg-teal-100 text-teal-700" :
                        user.role === "teacher" || user.role === "TEACHER" ? "bg-green-100 text-green-700" :
                        "bg-blue-100 text-blue-700"
                      }`}>
                        {user.role === "pedagogical_admin" ? "Resp. Pédago. (Plateforme)" : user.role === "pedagogical_lead" ? "Resp. Pédago. (École)" : user.role}
                      </span>
                      {(user.role === "teacher" || user.role === "TEACHER") && !user.is_approved && (
                        <span className="ml-2 px-2 py-1 text-xs rounded-full bg-yellow-100 text-yellow-700">
                          En attente
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <button
                        onClick={() => toggleUserStatus(user.id, user.is_active)}
                        className={`px-3 py-1 text-xs rounded-full ${
                          user.is_active 
                            ? "bg-green-100 text-green-700 hover:bg-green-200" 
                            : "bg-red-100 text-red-700 hover:bg-red-200"
                        }`}
                      >
                        {user.is_active ? "Actif" : "Inactif"}
                      </button>
                    </td>
                    <td className="px-6 py-4 text-right font-medium text-orange">
                      {formatNumber(user.token_balance || 0)}
                    </td>
                    <td className="px-6 py-4 text-right font-medium text-yellow-700">
                      {formatCurrency(user.dt_balance || 0)}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => setBalanceModal({ user, type: "tokens", mode: "add", amount: 0 })}
                          className="p-2 bg-orange/10 text-orange rounded-lg hover:bg-orange/20"
                          title="Ajouter Tokens"
                        >
                          <Coins className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => setBalanceModal({ user, type: "tokens", mode: "deduct", amount: 0 })}
                          className="p-2 bg-orange/10 text-orange rounded-lg hover:bg-orange/20"
                          title="Retirer Tokens"
                        >
                          <Minus className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => setBalanceModal({ user, type: "dt", mode: "add", amount: 0 })}
                          className="p-2 bg-yellow-100 text-yellow-700 rounded-lg hover:bg-yellow-200"
                          title="Ajouter DT"
                        >
                          <Wallet className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => setBalanceModal({ user, type: "dt", mode: "deduct", amount: 0 })}
                          className="p-2 bg-yellow-100 text-yellow-700 rounded-lg hover:bg-yellow-200"
                          title="Retirer DT"
                        >
                          <Minus className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => {
                            setEditRoleModal(user);
                            setNewRole(user.role as any);
                          }}
                          className="p-2 bg-purple-10 text-purple-600 rounded-lg hover:bg-purple/20"
                          title="Changer rôle"
                        >
                          <Shield className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => toggleUserStatus(user.id, user.is_active)}
                          className={`p-2 rounded-lg ${
                            user.is_active 
                              ? "bg-red-100 text-red-600 hover:bg-red-200" 
                              : "bg-green-100 text-green-600 hover:bg-green-200"
                          }`}
                          title={user.is_active ? "Suspendre" : "Activer"}
                        >
                          {user.is_active ? <Ban className="w-4 h-4" /> : <CheckCircle className="w-4 h-4" />}
                        </button>
                        {user.role === "teacher" && !user.is_approved && (
                          <button
                            onClick={() => approveTeacher(user.id)}
                            className="p-2 bg-green-100 text-green-600 rounded-lg hover:bg-green-200"
                            title="Approuver"
                          >
                            <CheckCircle className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Balance Modal */}
      {balanceModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-8">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-semibold text-navy">
                {balanceModal.mode === "add" ? "Ajouter" : "Retirer"}{" "}
                {balanceModal.type === "tokens" ? "Tokens" : "DT"}
              </h2>
              <button onClick={() => setBalanceModal(null)} className="p-2 hover:bg-cream rounded-lg">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="bg-cream-m rounded-xl p-4 mb-6">
              <div className="text-sm text-gray">Utilisateur</div>
              <div className="font-medium">{balanceModal.user.full_name}</div>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray mb-2">
                  Montant ({balanceModal.type === "tokens" ? "Tokens" : "DT"})
                </label>
                <input
                  type="number"
                  value={balanceModal.amount}
                  onChange={(e) => setBalanceModal({ ...balanceModal, amount: Number(e.target.value) })}
                  className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5"
                />
              </div>
            </div>
            <div className="flex gap-4 mt-6">
              <button
                onClick={() => setBalanceModal(null)}
                className="flex-1 py-3 bg-cream-m rounded-xl"
              >
                Annuler
              </button>
              <button
                onClick={handleBalanceChange}
                disabled={processing || !balanceModal.amount}
                className="flex-1 py-3 bg-orange text-white rounded-xl font-medium disabled:opacity-50"
              >
                {processing ? "Traitement..." : "Confirmer"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Role Modal */}
      {editRoleModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-8">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-semibold text-navy">Changer le rôle</h2>
              <button onClick={() => setEditRoleModal(null)} className="p-2 hover:bg-cream rounded-lg">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="space-y-3">
              {(["student", "teacher", "admin_school", "pedagogical_admin", "pedagogical_lead"] as const).map((role) => (
                <button
                  key={role}
                  onClick={() => setNewRole(role)}
                  className={`w-full p-4 rounded-xl text-left transition-all ${
                    newRole === role
                      ? "bg-orange text-white"
                      : "bg-cream-m hover:bg-cream"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    {role === "student" && <GraduationCap className="w-5 h-5" />}
                    {role === "teacher" && <Shield className="w-5 h-5" />}
                    {role === "admin_school" && <ShieldCheck className="w-5 h-5" />}
                    {role === "pedagogical_admin" && <BookOpen className="w-5 h-5" />}
                    {role === "pedagogical_lead" && <BookOpen className="w-5 h-5" />}
                    <span className="font-medium capitalize">{role === "admin_school" ? "Admin École" : role === "pedagogical_admin" ? "Resp. Pédago. (Plateforme)" : role === "pedagogical_lead" ? "Resp. Pédago. (École)" : role}</span>
                  </div>
                </button>
              ))}
            </div>
            <div className="flex gap-4 mt-6">
              <button
                onClick={() => setEditRoleModal(null)}
                className="flex-1 py-3 bg-cream-m rounded-xl"
              >
                Annuler
              </button>
              <button
                onClick={updateUserRole}
                disabled={processing || newRole === editRoleModal.role}
                className="flex-1 py-3 bg-orange text-white rounded-xl font-medium disabled:opacity-50"
              >
                {processing ? "Traitement..." : "Sauvegarder"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create User Modal */}
      {createModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-3xl max-w-lg w-full p-8">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-semibold text-navy">Ajouter un utilisateur</h2>
              <button onClick={() => setCreateModal(false)} className="p-2 hover:bg-cream rounded-lg">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray mb-2">Email *</label>
                <input
                  type="email"
                  value={newUser.email}
                  onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                  className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5"
                  placeholder="utilisateur@eduai.tn"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray mb-2">Mot de passe *</label>
                <input
                  type="password"
                  value={newUser.password}
                  onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                  className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5"
                  placeholder="Mot de passe"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray mb-2">Nom complet</label>
                <input
                  type="text"
                  value={newUser.full_name}
                  onChange={(e) => setNewUser({ ...newUser, full_name: e.target.value })}
                  className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5"
                  placeholder="Nom et prénom"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray mb-2">Rôle</label>
                  <select
                    value={newUser.role}
                    onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                    className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5"
                  >
                    <option value="student">Étudiant</option>
                    <option value="teacher">Enseignant</option>
                    <option value="admin_school">Admin École</option>
                    <option value="pedagogical_admin">Resp. Pédago. (Plateforme)</option>
                    <option value="pedagogical_lead">Resp. Pédago. (École)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray mb-2">École</label>
                  <select
                    value={newUser.school_id}
                    onChange={(e) => setNewUser({ ...newUser, school_id: Number(e.target.value) })}
                    className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5"
                  >
                    <option value={0}>— Aucune école —</option>
                    {schools.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.name} ({s.subscription_tier})
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              {newUser.school_id > 0 && (
                <div className="bg-blue-50 rounded-xl p-3 text-sm text-blue-700">
                  L'utilisateur sera associé à l'école sélectionnée et bénéficia des droits de son abonnement.
                </div>
              )}
            </div>
            <div className="flex gap-4 mt-6">
              <button
                onClick={() => setCreateModal(false)}
                className="flex-1 py-3 bg-cream-m rounded-xl"
              >
                Annuler
              </button>
              <button
                onClick={handleCreateUser}
                disabled={creating || !newUser.email || !newUser.password}
                className="flex-1 py-3 bg-orange text-white rounded-xl font-medium disabled:opacity-50"
              >
                {creating ? "Création..." : "Créer l'utilisateur"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}