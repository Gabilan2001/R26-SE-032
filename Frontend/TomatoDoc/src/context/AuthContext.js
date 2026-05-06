import React, { createContext, useEffect, useMemo, useState } from 'react';
import { loginUser, registerUser } from '../api/authApi';
import { clearToken, getToken, saveToken, clearUser, getUser, saveUser } from '../utils/tokenStorage';

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const existing = await getToken();
      const existingUser = await getUser();
      setToken(existing);
      setUser(existingUser);
      setLoading(false);
    })();
  }, []);

  const value = useMemo(() => ({
    token,
    user,
    loading,
    isAuthenticated: !!token,
    login: async (email, password) => {
      const res = await loginUser({ email, password });
      const next = res.data.access_token;
      const nextUser = res.data.user || null;
      await saveToken(next);
      await saveUser(nextUser);
      setToken(next);
      setUser(nextUser);
    },
    register: async (name, email, password) => {
      await registerUser({ name, email, password });
    },
    logout: async () => {
      await clearToken();
      await clearUser();
      setToken(null);
      setUser(null);
    },
  }), [token, user, loading]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
