import { create } from "zustand";
import { tokenStorage } from "../utils/tokenStorage";

const API_URL = import.meta.env.VITE_API_URL || "";

interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  roles: string[];
  activeRole: string;
  school_id?: number;
  niveau_scolaire?: string;
  is_partner?: boolean;
  is_active?: boolean;
  language?: string;
  avatar_url?: string;
  email_verified?: boolean;
  impersonated_by?: number;
}

async function authAPI_login(email, password) {
  const params = new URLSearchParams();
  params.append("username", email);
  params.append("password", password);
  
  const res = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: params,
  });
  if (!res.ok) throw new Error("Login failed");
  return res.json();
}

async function authAPI_register(email, password, full_name, school_name, niveau_scolaire, role?: string) {
  const res = await fetch(`${API_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, full_name, school_name, niveau_scolaire, ...(role ? { role } : {}) }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Registration failed");
  }
  return res.json();
}

async function authAPI_registerTrialTeacher(email, password, full_name) {
  const res = await fetch(`${API_URL}/auth/register-trial-teacher`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, full_name }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Trial registration failed");
  }
  return res.json();
}

async function authAPI_registerTeacher(email, password, full_name, school_name, school_id) {
  const res = await fetch(`${API_URL}/auth/teacher-register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, full_name, school_name, school_id }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Teacher registration failed");
  }
  return res.json();
}

async function authAPI_me(token) {
  const res = await fetch(`${API_URL}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to get user");
  return res.json();
}

// FIX #6 — vérification email via le token renvoyé par /auth/register
// (posture non bloquante : en production ce token serait transmis par email).
async function authAPI_verifyEmail(token: string) {
  const res = await fetch(`${API_URL}/auth/verify-email`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || "Verification failed");
  return data;
}

const PENDING_VERIFICATION_KEY = "eduai_pending_email_verification";

function readPendingVerification(): string | null {
  try {
    return sessionStorage.getItem(PENDING_VERIFICATION_KEY);
  } catch {
    return null;
  }
}

// Correction M1 : révoque côté serveur les refresh tokens avant de nettoyer
// le stockage local. Fire-and-forget : la déconnexion locale ne doit jamais échouer.
async function authAPI_logout(token?: string | null) {
  if (!token) return;
  try {
    await fetch(`${API_URL}/auth/logout`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({}),
    });
  } catch {
    // réseau indisponible → les refresh tokens expireront naturellement ;
    // on poursuit quand même la déconnexion locale.
  }
}

async function authAPI_switchContext(token: string, role: string) {
  const res = await fetch(`${API_URL}/auth/switch-context`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ role }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Context switch failed");
  }
  return res.json();
}

async function authAPI_stopImpersonation(token: string) {
  const res = await fetch(`${API_URL}/auth/impersonate/stop`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Stop impersonation failed");
  }
  return res.json();
}

function decodeJWT(token: string): any {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch {
    return null;
  }
}

export const useAuthStore = create((set, get) => ({
  user: tokenStorage.getUser() as User | null,
  token: tokenStorage.getToken(),
  isLoading: false,
  error: null,
  // FIX #6 — token de vérification en attente (session courante uniquement)
  verificationToken: readPendingVerification(),

  login: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      const data = await authAPI_login(email, password);
      tokenStorage.setToken(data.access_token);
      if (data.refresh_token) tokenStorage.setRefreshToken(data.refresh_token);
      
      // Decode JWT to get roles and activeRole
      const jwtPayload = decodeJWT(data.access_token);
      const user = await authAPI_me(data.access_token);
      
      // Enrich user with JWT claims
      if (jwtPayload) {
        user.roles = jwtPayload.roles || [user.role];
        user.activeRole = jwtPayload.active_role || user.role;
        user.impersonated_by = jwtPayload.impersonated_by;
      } else {
        user.roles = [user.role];
        user.activeRole = user.role;
      }
      
      tokenStorage.setUser(user);
      set({ token: data.access_token, user, isLoading: false });
      return true;
    } catch (err) {
      tokenStorage.clearAll();
      set({ error: err.message, isLoading: false, token: null, user: null });
      return false;
    }
  },

  logout: () => {
    const { token } = get();
    // Correction M1 : révocation serveur des refresh tokens (fire-and-forget)
    authAPI_logout(token);
    tokenStorage.clearAll();
    set({ token: null, user: null });
  },

  setUser: (user: any) => {
    tokenStorage.setUser(user);
    set({ user });
  },

  switchRole: async (role: string) => {
    const { token, user } = get();
    if (!token || !user) return false;
    
    try {
      const data = await authAPI_switchContext(token, role);
      tokenStorage.setToken(data.access_token);
      if (data.refresh_token) tokenStorage.setRefreshToken(data.refresh_token);
      
      // Decode new JWT to get updated claims
      const jwtPayload = decodeJWT(data.access_token);
      const updatedUser = await authAPI_me(data.access_token);
      
      if (jwtPayload) {
        updatedUser.roles = jwtPayload.roles || [updatedUser.role];
        updatedUser.activeRole = jwtPayload.active_role || role;
        updatedUser.impersonated_by = jwtPayload.impersonated_by;
      }
      
      tokenStorage.setUser(updatedUser);
      set({ token: data.access_token, user: updatedUser });
      return true;
    } catch (err) {
      console.error("Switch role failed:", err);
      return false;
    }
  },

  stopImpersonation: async () => {
    const { token } = get();
    if (!token) return false;
    
    try {
      const data = await authAPI_stopImpersonation(token);
      tokenStorage.setToken(data.access_token);
      if (data.refresh_token) tokenStorage.setRefreshToken(data.refresh_token);
      
      // Decode new JWT to get support user's claims
      const jwtPayload = decodeJWT(data.access_token);
      const user = await authAPI_me(data.access_token);
      
      if (jwtPayload) {
        user.roles = jwtPayload.roles || [user.role];
        user.activeRole = jwtPayload.active_role || user.role;
        user.impersonated_by = undefined;
      }
      
      tokenStorage.setUser(user);
      set({ token: data.access_token, user });
      
      // Refresh the page to reset all state
      window.location.reload();
      return true;
    } catch (err) {
      console.error("Stop impersonation failed:", err);
      return false;
    }
  },

  register: async (email, password, full_name, school_name, niveau_scolaire, role?: string) => {
    set({ isLoading: true, error: null });
    try {
      const data = await authAPI_register(email, password, full_name, school_name, niveau_scolaire, role);
      tokenStorage.setToken(data.access_token);
      if (data.refresh_token) tokenStorage.setRefreshToken(data.refresh_token);
      const user = await authAPI_me(data.access_token);
      user.roles = [user.role];
      user.activeRole = user.role;
      // FIX #6 — compte actif dès l'inscription ; la vérification est en attente
      user.email_verified = false;
      tokenStorage.setUser(user);
      let verificationToken: string | null = null;
      if (data.email_verification_token) {
        verificationToken = data.email_verification_token;
        try {
          sessionStorage.setItem(PENDING_VERIFICATION_KEY, verificationToken);
        } catch {
          /* stockage indisponible : le token reste dans l'état du store */
        }
      }
      set({ token: data.access_token, user, isLoading: false, verificationToken });
      return true;
    } catch (err) {
      set({ error: err.message, isLoading: false });
      return false;
    }
  },

  verifyEmail: async (tokenArg?: string) => {
    const tok = tokenArg || get().verificationToken || readPendingVerification();
    if (!tok) return false;
    try {
      await authAPI_verifyEmail(tok);
      try { sessionStorage.removeItem(PENDING_VERIFICATION_KEY); } catch { /* noop */ }
      const { token, user } = get();
      let updated: User | null = user;
      if (token) {
        try {
          updated = await authAPI_me(token);
          updated.roles = updated.roles || [updated.role];
          updated.activeRole = updated.activeRole || updated.role;
          tokenStorage.setUser(updated);
        } catch {
          /* session expirée : on garde l'utilisateur courant */
        }
      }
      if (updated) updated.email_verified = true;
      set({ verificationToken: null, user: updated });
      return true;
    } catch {
      return false;
    }
  },

  registerTrialTeacher: async (email, password, full_name) => {
    set({ isLoading: true, error: null });
    try {
      const data = await authAPI_registerTrialTeacher(email, password, full_name);
      tokenStorage.setToken(data.access_token);
      if (data.refresh_token) tokenStorage.setRefreshToken(data.refresh_token);
      const user = await authAPI_me(data.access_token);
      user.roles = [user.role];
      user.activeRole = user.role;
      tokenStorage.setUser(user);
      set({ token: data.access_token, user, isLoading: false });
      return true;
    } catch (err) {
      set({ error: err.message, isLoading: false });
      return false;
    }
  },

  registerTeacher: async (email, password, full_name, school_name, school_id) => {
    set({ isLoading: true, error: null });
    try {
      await authAPI_registerTeacher(email, password, full_name, school_name, school_id);
      set({ isLoading: false });
      return "pending";
    } catch (err) {
      set({ error: err.message, isLoading: false });
      return false;
    }
  },

  restore: async () => {
    const token = tokenStorage.getToken();
    const user = tokenStorage.getUser() as User | null;
    
    if (!token || !user) {
      set({ token: null, user: null });
      return;
    }
    
    try {
      const freshUser = await authAPI_me(token);
      
      // Decode JWT to get roles and activeRole
      const jwtPayload = decodeJWT(token);
      if (jwtPayload) {
        freshUser.roles = jwtPayload.roles || [freshUser.role];
        freshUser.activeRole = jwtPayload.active_role || freshUser.role;
        freshUser.impersonated_by = jwtPayload.impersonated_by;
      } else {
        freshUser.roles = [freshUser.role];
        freshUser.activeRole = freshUser.role;
      }
      
      tokenStorage.setUser(freshUser);
      set({ token, user: freshUser });
    } catch (err) {
      // Expected when token is missing or expired — silently clear session
      tokenStorage.clearAll();
      set({ token: null, user: null });
    }
  },
}));