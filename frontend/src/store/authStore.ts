import { create } from "zustand";

// Use consistent localhost for both frontend and backend
const API_URL = "";

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
  user: JSON.parse(localStorage.getItem("user") || "null"),
  token: localStorage.getItem("token"),
  isLoading: false,
  error: null,

  login: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      const data = await authAPI_login(email, password);
      localStorage.setItem("token", data.access_token);
      const user = await authAPI_me(data.access_token);
      localStorage.setItem("user", JSON.stringify(user));
      set({ token: data.access_token, user, isLoading: false });
      return true;
    } catch (err) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      set({ error: err.message, isLoading: false, token: null, user: null });
      return false;
    }
  },

  logout: () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    set({ token: null, user: null });
  },

  register: async (email, password, full_name, school_name, niveau_scolaire) => {
    set({ isLoading: true, error: null });
    try {
      const data = await authAPI_register(email, password, full_name, school_name, niveau_scolaire);
      localStorage.setItem("token", data.access_token);
      const user = await authAPI_me(data.access_token);
      localStorage.setItem("user", JSON.stringify(user));
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
      localStorage.setItem("token", data.access_token);
      const user = await authAPI_me(data.access_token);
      localStorage.setItem("user", JSON.stringify(user));
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
    const token = localStorage.getItem("token");
    const userStr = localStorage.getItem("user");
    
    if (!token || !userStr) {
      set({ token: null, user: null });
      return;
    }
    
    try {
      const user = await authAPI_me(token);
      localStorage.setItem("user", JSON.stringify(user));
      set({ token, user });
    } catch (err) {
      // Expected when token is missing or expired — silently clear session
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      set({ token: null, user: null });
    }
  },
}));