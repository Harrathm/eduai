import { useState, useEffect, useCallback, useMemo } from "react";
import { userApi, schoolApi, walletAdmin } from "../../../api";

export interface User {
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

export type RoleFilter = "all" | "teacher" | "student" | "admin_school" | "pedagogical_admin" | "pedagogical_lead" | "super_admin";
export type StatusFilter = "all" | "active" | "inactive";

interface Notification {
  show: boolean;
  message: string;
  type: "success" | "error";
}

export function useUserManagement() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState<RoleFilter>("all");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [processing, setProcessing] = useState(false);
  const [schools, setSchools] = useState<{ id: number; name: string; subscription_tier: string; max_users: number }[]>([]);
  const [notification, setNotification] = useState<Notification>({ show: false, message: "", type: "success" });

  const showNotification = useCallback((message: string, type: "success" | "error" = "success") => {
    setNotification({ show: true, message, type });
    setTimeout(() => setNotification({ show: false, message: "", type: "success" }), 3000);
  }, []);

  const fetchSchools = useCallback(async () => {
    try {
      const data = await schoolApi.list();
      setSchools(Array.isArray(data) ? data : data.items || []);
    } catch (err) {
      console.error("fetchSchools error:", err);
    }
  }, []);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, any> = {};
      if (roleFilter !== "all") params.role = roleFilter;
      const data = await userApi.list(params);
      setUsers(Array.isArray(data) ? data : data.items || []);
    } catch (err) {
      console.error("fetchUsers exception:", err);
      setUsers([]);
    }
    setLoading(false);
  }, [roleFilter]);

  useEffect(() => {
    fetchUsers();
    fetchSchools();
  }, [fetchUsers, fetchSchools]);

  const toggleUserStatus = useCallback(async (userId: number, isActive: boolean) => {
    setProcessing(true);
    try {
      await userApi.toggleActive(userId);
      showNotification(isActive ? "✓ Utilisateur suspendu" : "✓ Utilisateur réactivé");
      fetchUsers();
    } catch (err) {
      console.error(err);
      showNotification("✗ Erreur lors de la modification du statut", "error");
    }
    setProcessing(false);
  }, [fetchUsers, showNotification]);

  const handleBalanceChange = useCallback(async (
    user: User,
    type: "tokens" | "dt",
    mode: "add" | "deduct",
    amount: number
  ) => {
    if (amount <= 0) {
      showNotification("✗ Veuillez entrer un montant valide", "error");
      return;
    }
    if (mode === "deduct") {
      if (type === "tokens" && user.token_balance < amount) {
        showNotification("✗ Solde tokens insuffisant", "error");
        return;
      }
      if (type === "dt" && user.dt_balance < amount) {
        showNotification("✗ Solde DT insuffisant", "error");
        return;
      }
    }
    setProcessing(true);
    try {
      const action = mode === "add" ? walletAdmin.add : walletAdmin.deduct;
      const amountTokens = type === "tokens" ? amount : 0;
      const amountDt = type === "dt" ? amount : 0;
      await action(user.id, amountTokens, amountDt, `Admin ${mode} ${type}`);
      const actionText = mode === "add" ? "ajoutés" : "retirés";
      const typeText = type === "tokens" ? "Tokens" : "DT";
      showNotification(`✓ Succès: ${amount} ${typeText} ${actionText} à ${user.email}`);
      setTimeout(() => fetchUsers(), 2000);
    } catch (err) {
      console.error("handleBalanceChange error:", err);
      showNotification("✗ Erreur réseau", "error");
    }
    setProcessing(false);
  }, [fetchUsers, showNotification]);

  const approveTeacher = useCallback(async (userId: number) => {
    setProcessing(true);
    try {
      await userApi.approve(userId);
      fetchUsers();
    } catch (err) {
      console.error(err);
    }
    setProcessing(false);
  }, [fetchUsers]);

  const updateUserRole = useCallback(async (user: User, newRole: string) => {
    setProcessing(true);
    try {
      fetchUsers();
      showNotification(`✓ Rôle modifié: ${newRole.toUpperCase()} pour ${user.email}`);
    } catch (err) {
      console.error(err);
      showNotification("✗ Erreur lors du changement de rôle", "error");
    }
    setProcessing(false);
  }, [fetchUsers, showNotification]);

  const createUser = useCallback(async (newUser: { email: string; password: string; full_name: string; role: string; school_id: number }) => {
    if (!newUser.email || !newUser.password) return false;
    try {
      await userApi.create({
        email: newUser.email,
        password: newUser.password,
        full_name: newUser.full_name,
        role: newUser.role,
        school_id: newUser.school_id || undefined,
      } as any);
      showNotification(`✓ Utilisateur ${newUser.email} créé`);
      fetchUsers();
      return true;
    } catch (err) {
      console.error(err);
      showNotification("✗ Erreur lors de la création", "error");
      return false;
    }
  }, [fetchUsers, showNotification]);

  const filteredUsers = useMemo(() =>
    users.filter((u) =>
      search === "" ||
      u.full_name?.toLowerCase().includes(search.toLowerCase()) ||
      u.email.toLowerCase().includes(search.toLowerCase())
    ),
    [users, search]
  );

  const stats = useMemo(() => ({
    total: users.length,
    teachers: users.filter((u) => u.role === "teacher").length,
    students: users.filter((u) => u.role === "student").length,
    active: users.filter((u) => u.is_active).length,
  }), [users]);

  return {
    users: filteredUsers,
    loading,
    search,
    setSearch,
    roleFilter,
    setRoleFilter,
    statusFilter,
    setStatusFilter,
    processing,
    schools,
    notification,
    stats,
    toggleUserStatus,
    handleBalanceChange,
    approveTeacher,
    updateUserRole,
    createUser,
  };
}
