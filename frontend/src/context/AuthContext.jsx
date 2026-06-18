import { createContext, useContext, useEffect, useState } from "react";
import api from "../api/axios";
import { clearApiCache } from "../hooks/useApiQuery";

const AuthContext = createContext(null);

// Module-level guard so React 18 StrictMode's double-mount (dev) and any
// remounts never fire /auth/me more than once.
let meInflight = null;

function clearAuthStorage() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setLoading(false);
      return;
    }
    meInflight =
      meInflight?.token === token
        ? meInflight
        : { token, promise: api.get("/auth/me").then((r) => r.data) };
    meInflight.promise
      .then((data) => setUser(data))
      .catch(() => {
        clearAuthStorage();
        clearApiCache();
      })
      .finally(() => {
        setLoading(false);
        meInflight = null;
      });
  }, []);

  const login = async (phone, password) => {
    const { data } = await api.post("/auth/login", { phone, password });
    clearApiCache();
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    const me = await api.get("/auth/me");
    setUser(me.data);
    return me.data;
  };

  const logout = async () => {
    try { await api.post("/auth/logout"); } catch (_) {}
    clearAuthStorage();
    clearApiCache();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
