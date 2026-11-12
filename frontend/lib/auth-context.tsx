"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { API_BASE_URL } from "./api";

export interface UserSummary {
  id: string;
  email: string;
  full_name: string;
  role: "USER" | "ADMIN" | "COMMUNITY_MODERATOR";
  preferred_language: string;
  senior_mode: boolean;
}

interface AuthContextType {
  user: UserSummary | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string; role?: string }>;
  register: (data: { email: string; password: string; full_name: string; preferred_language: string }) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserSummary | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    // Check saved session in local storage
    try {
      const storedToken = localStorage.getItem("suraksha_token");
      const storedUser = localStorage.getItem("suraksha_user");
      if (storedToken && storedUser) {
        setToken(storedToken);
        setUser(JSON.parse(storedUser));
      }
    } catch (e) {
      console.error("Failed to load stored session", e);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const res = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) {
        return { success: false, error: data.detail || "Authentication failed." };
      }

      setToken(data.access_token);
      setUser(data.user);
      localStorage.setItem("suraksha_token", data.access_token);
      localStorage.setItem("suraksha_user", JSON.stringify(data.user));
      return { success: true, role: data.user.role };
    } catch (err: any) {
      return { success: false, error: err.message || "Network error. Is backend online?" };
    }
  };

  const register = async (data: { email: string; password: string; full_name: string; preferred_language: string }) => {
    try {
      const res = await fetch(`${API_BASE_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      const resData = await res.json();
      if (!res.ok) {
        return { success: false, error: resData.detail || "Registration failed." };
      }

      setToken(resData.access_token);
      setUser(resData.user);
      localStorage.setItem("suraksha_token", resData.access_token);
      localStorage.setItem("suraksha_user", JSON.stringify(resData.user));
      return { success: true };
    } catch (err: any) {
      return { success: false, error: err.message || "Network error. Is backend online?" };
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("suraksha_token");
    localStorage.removeItem("suraksha_user");
  };

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

