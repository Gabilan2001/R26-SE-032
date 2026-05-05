import React, { createContext, useEffect, useMemo, useState } from 'react';
import { loginUser, registerUser } from '../api/authApi';
import { clearToken, getToken, saveToken } from '../utils/tokenStorage';

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const existing = await getToken();
      setToken(existing);
      setLoading(false);
    })();
  }, []);

  const value = useMemo(() => ({
    token,
    loading,
    isAuthenticated: !!token,
    login: async (email, password) => {
      const res = await loginUser({ email, password });
      const next = res.data.access_token;
      await saveToken(next);
      setToken(next);
    },
    register: async (name, email, password) => {
      await registerUser({ name, email, password });
    },
    logout: async () => {
      await clearToken();
      setToken(null);
    },
  }), [token, loading]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
