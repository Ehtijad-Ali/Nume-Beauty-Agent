import { createContext, useContext, useMemo, useState, useCallback, useEffect } from "react";
import type { AuthUser } from "@/types";
import { authService, type LoginResponse } from "@/api";
import { tokenStorage } from "@/api/client";

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<AuthUser>;
  register: (payload: { email: string; password: string; full_name: string; role?: string }) => Promise<AuthUser>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function mapApiUser(u: any): AuthUser {
  return {
    id: u.id,
    name: u.full_name,
    email: u.email,
    role: (u.role?.name ?? "Viewer") as AuthUser["role"],
    avatarUrl: u.avatar_url,
  };
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // On mount: if we have an access token, hydrate the user from /auth/me
  const hydrate = useCallback(async () => {
    const token = tokenStorage.getAccess();
    if (!token) {
      setIsLoading(false);
      return;
    }
    try {
      const me = await authService.me();
      setUser(mapApiUser(me));
    } catch {
      tokenStorage.clear();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  // Listen for forced-logout events from the axios interceptor
  useEffect(() => {
    const handler = () => {
      tokenStorage.clear();
      setUser(null);
    };
    window.addEventListener("nume:unauthorized", handler);
    return () => window.removeEventListener("nume:unauthorized", handler);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const res: LoginResponse = await authService.login(email, password);
    tokenStorage.set(res.access_token, res.refresh_token);
    const u = mapApiUser(res.user);
    setUser(u);
    return u;
  }, []);

  const register = useCallback(async (payload: { email: string; password: string; full_name: string; role?: string }) => {
    await authService.register(payload);
    // Auto-login after register
    return login(payload.email, payload.password);
  }, [login]);

  const logout = useCallback(async () => {
    const refresh = tokenStorage.getRefresh();
    if (refresh) {
      await authService.logout(refresh);
    }
    tokenStorage.clear();
    setUser(null);
  }, []);

  const refreshUser = useCallback(async () => {
    try {
      const me = await authService.me();
      setUser(mapApiUser(me));
    } catch {
      /* ignore */
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ user, isAuthenticated: !!user, isLoading, login, register, logout, refreshUser }),
    [user, isLoading, login, register, logout, refreshUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
