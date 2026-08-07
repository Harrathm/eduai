import { useState } from "react";
import {
  Search, Coins, Wallet, Ban, CheckCircle, Shield, ShieldCheck,
  GraduationCap, Check, Minus, Plus, BookOpen, Upload,
} from "lucide-react";
import { Button, Spinner, PageSpinner, Modal, EmptyState, Input } from "../../../components/ui";
import { useUserManagement, type User } from "../hooks/useUserManagement";
import CsvImportStudents from "./CsvImportStudents";

export default function UserManagementView() {
  const {
    users, loading, search, setSearch, roleFilter, setRoleFilter,
    statusFilter, setStatusFilter, processing, schools, notification,
    stats, toggleUserStatus, handleBalanceChange, approveTeacher,
    updateUserRole, createUser,
  } = useUserManagement();

  const [balanceModal, setBalanceModal] = useState<{ user: User; type: "tokens" | "dt"; mode: "add" | "deduct"; amount: number } | null>(null);
  const [editRoleModal, setEditRoleModal] = useState<User | null>(null);
  const [newRole, setNewRole] = useState<string>("student");
  const [createModal, setCreateModal] = useState(false);
  const [newUser, setNewUser] = useState({ email: "", password: "", full_name: "", role: "student", school_id: 0 });
  const [showCsvImport, setShowCsvImport] = useState(false);

  const formatNumber = (num: number) => new Intl.NumberFormat("fr-TN").format(num);
  const formatCurrency = (num: number) => new Intl.NumberFormat("fr-TN", { style: "currency", currency: "TND" }).format(num);

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
          <Button onClick={() => setCreateModal(true)}>
            <Plus className="w-5 h-5" />
            Ajouter un utilisateur
          </Button>
        </div>
      </div>

      {/* Notification Toast */}
      {notification.show && (
        <div className={`fixed top-6 right-6 z-50 flex items-center gap-3 px-6 py-4 rounded-xl shadow-lg ${notification.type === "success" ? "bg-green-500 text-white" : "bg-red-500 text-white"}`}>
          {notification.type === "success" ? <Check className="w-5 h-5" /> : <CheckCircle className="w-5 h-5" />}
          <span className="font-medium">{notification.message}</span>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Total Users", value: stats.total, color: "text-navy" },
          { label: "Teachers", value: stats.teachers, color: "text-green-700" },
          { label: "Students", value: stats.students, color: "text-purple-700" },
          { label: "Actifs", value: stats.active, color: "text-emerald-700" },
        ].map((s) => (
          <div key={s.label} className="bg-gradient-to-br from-blue-50 to-cream rounded-2xl p-6">
            <div className={`text-3xl font-[300] ${s.color}`}>{s.value}</div>
            <div className="text-sm text-gray">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px] relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray" />
            <Input value={search} onChange={(e) => setSearch(e.target.value)} className="ps-12" placeholder="Rechercher..." />
          </div>
          <select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value as any)} className="px-4 py-3 bg-cream-m rounded-xl border border-black/5">
            <option value="all">Tous les rôles</option>
            <option value="student">Students</option>
            <option value="teacher">Teachers</option>
            <option value="admin_school">Admins École</option>
            <option value="pedagogical_admin">Resp. Pédago. (Plateforme)</option>
            <option value="pedagogical_lead">Resp. Pédago. (École)</option>
            <option value="super_admin">Super Admin</option>
          </select>
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value as any)} className="px-4 py-3 bg-cream-m rounded-xl border border-black/5">
            <option value="all">Tous status</option>
            <option value="active">Actifs</option>
            <option value="inactive">Inactifs</option>
          </select>
          <Button variant="secondary" onClick={() => setShowCsvImport(!showCsvImport)}>
            <Upload className="w-4 h-4" />
            Import CSV
          </Button>
        </div>
      </div>

      {showCsvImport && (
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
          <CsvImportStudents />
        </div>
      )}

      {/* Table */}
      <div className="bg-white rounded-2xl shadow-sm border border-black/5 overflow-hidden">
        {loading ? (
          <PageSpinner />
        ) : users.length === 0 ? (
          <EmptyState title="Aucun utilisateur trouvé" description="Modifiez vos filtres ou créez un nouvel utilisateur." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-cream-m">
                <tr>
                  {["User", "Rôle", "Status", "Tokens", "DT", "Actions"].map((h) => (
                    <th key={h} className={`text-start px-6 py-4 text-xs font-semibold text-gray uppercase ${h === "Tokens" || h === "DT" ? "text-end" : ""}`}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-black/5">
                {users.map((user) => (
                  <tr key={user.id} className="hover:bg-cream/50">
                    <td className="px-6 py-4">
                      <div className="font-medium">{user.full_name || "—"}</div>
                      <div className="text-sm text-gray">{user.email}</div>
                      {user.school_name && <div className="text-xs text-orange">{user.school_name}</div>}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        user.role === "super_admin" ? "bg-purple-600 text-white" :
                        user.role === "admin_school" ? "bg-purple-100 text-purple-700" :
                        user.role === "pedagogical_admin" ? "bg-blue-100 text-blue-700" :
                        user.role === "pedagogical_lead" ? "bg-teal-100 text-teal-700" :
                        user.role === "teacher" ? "bg-green-100 text-green-700" :
                        "bg-blue-100 text-blue-700"
                      }`}>
                        {user.role === "pedagogical_admin" ? "Resp. Pédago. (Plateforme)" : user.role === "pedagogical_lead" ? "Resp. Pédago. (École)" : user.role}
                      </span>
                      {user.role === "teacher" && !user.is_approved && (
                        <span className="ml-2 px-2 py-1 text-xs rounded-full bg-yellow-100 text-yellow-700">En attente</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <Button
                        variant={user.is_active ? "success" : "danger"}
                        size="sm"
                        onClick={() => toggleUserStatus(user.id, user.is_active)}
                      >
                        {user.is_active ? "Actif" : "Inactif"}
                      </Button>
                    </td>
                    <td className="px-6 py-4 text-end font-medium text-orange">{formatNumber(user.token_balance || 0)}</td>
                    <td className="px-6 py-4 text-end font-medium text-yellow-700">{formatCurrency(user.dt_balance || 0)}</td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-1">
                        <Button variant="ghost" size="sm" onClick={() => setBalanceModal({ user, type: "tokens", mode: "add", amount: 0 })} title="Ajouter Tokens"><Coins className="w-4 h-4" /></Button>
                        <Button variant="ghost" size="sm" onClick={() => setBalanceModal({ user, type: "tokens", mode: "deduct", amount: 0 })} title="Retirer Tokens"><Minus className="w-4 h-4" /></Button>
                        <Button variant="ghost" size="sm" onClick={() => setBalanceModal({ user, type: "dt", mode: "add", amount: 0 })} title="Ajouter DT"><Wallet className="w-4 h-4" /></Button>
                        <Button variant="ghost" size="sm" onClick={() => setBalanceModal({ user, type: "dt", mode: "deduct", amount: 0 })} title="Retirer DT"><Minus className="w-4 h-4" /></Button>
                        <Button variant="ghost" size="sm" onClick={() => { setEditRoleModal(user); setNewRole(user.role); }} title="Changer rôle"><Shield className="w-4 h-4" /></Button>
                        <Button variant={user.is_active ? "danger" : "success"} size="sm" onClick={() => toggleUserStatus(user.id, user.is_active)} title={user.is_active ? "Suspendre" : "Activer"}>
                          {user.is_active ? <Ban className="w-4 h-4" /> : <CheckCircle className="w-4 h-4" />}
                        </Button>
                        {user.role === "teacher" && !user.is_approved && (
                          <Button variant="success" size="sm" onClick={() => approveTeacher(user.id)} title="Approuver"><CheckCircle className="w-4 h-4" /></Button>
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
      <Modal open={!!balanceModal} onClose={() => setBalanceModal(null)} title={balanceModal ? `${balanceModal.mode === "add" ? "Ajouter" : "Retirer"} ${balanceModal.type === "tokens" ? "Tokens" : "DT"}` : ""}>
        {balanceModal && (
          <>
            <div className="bg-cream-m rounded-xl p-4 mb-6">
              <div className="text-sm text-gray">Utilisateur</div>
              <div className="font-medium">{balanceModal.user.full_name}</div>
            </div>
            <Input
              type="number"
              label={`Montant (${balanceModal.type === "tokens" ? "Tokens" : "DT"})`}
              value={balanceModal.amount || ""}
              onChange={(e) => setBalanceModal({ ...balanceModal, amount: Number(e.target.value) })}
            />
            <div className="flex gap-4 mt-6">
              <Button variant="ghost" className="flex-1" onClick={() => setBalanceModal(null)}>Annuler</Button>
              <Button className="flex-1" loading={processing} disabled={!balanceModal.amount} onClick={async () => {
                await handleBalanceChange(balanceModal.user, balanceModal.type, balanceModal.mode, balanceModal.amount);
                setBalanceModal(null);
              }}>
                Confirmer
              </Button>
            </div>
          </>
        )}
      </Modal>

      {/* Edit Role Modal */}
      <Modal open={!!editRoleModal} onClose={() => setEditRoleModal(null)} title="Changer le rôle">
        {editRoleModal && (
          <>
            <div className="space-y-3">
              {(["student", "teacher", "admin_school", "pedagogical_admin", "pedagogical_lead"] as const).map((role) => (
                <Button
                  key={role}
                  variant={newRole === role ? "primary" : "ghost"}
                  size="md"
                  onClick={() => setNewRole(role)}
                  className="w-full text-start"
                >
                  <div className="flex items-center gap-3">
                    {role === "student" && <GraduationCap className="w-5 h-5" />}
                    {role === "teacher" && <Shield className="w-5 h-5" />}
                    {role === "admin_school" && <ShieldCheck className="w-5 h-5" />}
                    {(role === "pedagogical_admin" || role === "pedagogical_lead") && <BookOpen className="w-5 h-5" />}
                    <span className="font-medium capitalize">{role === "admin_school" ? "Admin École" : role === "pedagogical_admin" ? "Resp. Pédago. (Plateforme)" : role === "pedagogical_lead" ? "Resp. Pédago. (École)" : role}</span>
                  </div>
                </Button>
              ))}
            </div>
            <div className="flex gap-4 mt-6">
              <Button variant="ghost" className="flex-1" onClick={() => setEditRoleModal(null)}>Annuler</Button>
              <Button className="flex-1" loading={processing} disabled={newRole === editRoleModal.role} onClick={async () => {
                await updateUserRole(editRoleModal, newRole);
                setEditRoleModal(null);
              }}>
                Sauvegarder
              </Button>
            </div>
          </>
        )}
      </Modal>

      {/* Create User Modal */}
      <Modal open={createModal} onClose={() => setCreateModal(false)} title="Ajouter un utilisateur" maxWidth="max-w-lg">
        <div className="space-y-4">
          <Input label="Email *" type="email" value={newUser.email} onChange={(e) => setNewUser({ ...newUser, email: e.target.value })} placeholder="utilisateur@eduai.tn" />
          <Input label="Mot de passe *" type="password" value={newUser.password} onChange={(e) => setNewUser({ ...newUser, password: e.target.value })} placeholder="Mot de passe" />
          <Input label="Nom complet" value={newUser.full_name} onChange={(e) => setNewUser({ ...newUser, full_name: e.target.value })} placeholder="Nom et prénom" />
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray mb-2">Rôle</label>
              <select value={newUser.role} onChange={(e) => setNewUser({ ...newUser, role: e.target.value })} className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5">
                <option value="student">Étudiant</option>
                <option value="teacher">Enseignant</option>
                <option value="admin_school">Admin École</option>
                <option value="pedagogical_admin">Resp. Pédago. (Plateforme)</option>
                <option value="pedagogical_lead">Resp. Pédago. (École)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray mb-2">École</label>
              <select value={newUser.school_id} onChange={(e) => setNewUser({ ...newUser, school_id: Number(e.target.value) })} className="w-full px-4 py-3 bg-cream-m rounded-xl border border-black/5">
                <option value={0}>— Aucune école —</option>
                {schools.map((s) => (
                  <option key={s.id} value={s.id}>{s.name} ({s.subscription_tier})</option>
                ))}
              </select>
            </div>
          </div>
          {newUser.school_id > 0 && (
            <div className="bg-blue-50 rounded-xl p-3 text-sm text-blue-700">
              L'utilisateur sera associé à l'école sélectionnée et bénéficiera des droits de son abonnement.
            </div>
          )}
        </div>
        <div className="flex gap-4 mt-6">
          <Button variant="ghost" className="flex-1" onClick={() => setCreateModal(false)}>Annuler</Button>
          <Button className="flex-1" disabled={!newUser.email || !newUser.password} onClick={async () => {
            const ok = await createUser(newUser);
            if (ok) { setCreateModal(false); setNewUser({ email: "", password: "", full_name: "", role: "student", school_id: 0 }); }
          }}>
            Créer l'utilisateur
          </Button>
        </div>
      </Modal>
    </div>
  );
}
