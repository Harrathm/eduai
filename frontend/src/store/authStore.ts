import { create } from "zustand";
import { tokenStorage } from "../utils/tokenStorage";

const API_URL = import.meta.env.VITE_API_URL || "";

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

async function authAPI_register(email, password, full_name, school_name, niveau_scolaire) {
  const res = await fetch(`${API_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, full_name, school_name, niveau_scolaire }),
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

export const useAuthStore = create((set, get) => ({
  user: tokenStorage.getUser(),
  token: tokenStorage.getToken(),
  isLoading: false,
  error: null,

  login: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      const data = await authAPI_login(email, password);
      tokenStorage.setToken(data.access_token);
      if (data.refresh_token) tokenStorage.setRefreshToken(data.refresh_token);
      const user = await authAPI_me(data.access_token);
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
    tokenStorage.clearAll();
    set({ token: null, user: null });
  },

  setUser: (user: any) => {
    tokenStorage.setUser(user);
    set({ user });
  },

  register: async (email, password, full_name, school_name, niveau_scolaire) => {
    set({ isLoading: true, error: null });
    try {
      const data = await authAPI_register(email, password, full_name, school_name, niveau_scolaire);
      tokenStorage.setToken(data.access_token);
      if (data.refresh_token) tokenStorage.setRefreshToken(data.refresh_token);
      const user = await authAPI_me(data.access_token);
      tokenStorage.setUser(user);
      set({ token: data.access_token, user, isLoading: false });
      return true;
    } catch (err) {
      set({ error: err.message, isLoading: false });
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
    const user = tokenStorage.getUser();
    
    if (!token || !user) {
      set({ token: null, user: null });
      return;
    }
    
    try {
      const freshUser = await authAPI_me(token);
      tokenStorage.setUser(freshUser);
      set({ token, user: freshUser });
    } catch (err) {
      // Expected when token is missing or expired — silently clear session
      tokenStorage.clearAll();
      set({ token: null, user: null });
    }
  },
}));