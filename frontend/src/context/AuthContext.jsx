import { createContext, useContext, useState, useEffect } from "react";
import { api } from "../services/api";
import { getPortalConfig } from "../utils/portalConfig";

const AuthContext = createContext(null);

function saveSession(tokenValue, userPayload) {
  sessionStorage.setItem("blood_token", tokenValue);
  sessionStorage.setItem("blood_user", JSON.stringify(userPayload));
}

function clearSession() {
  sessionStorage.removeItem("blood_token");
  sessionStorage.removeItem("blood_user");
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => sessionStorage.getItem("blood_token") || null);
  const [loading, setLoading] = useState(true);

  // Synchronize per-tab authenticated session on mount
  useEffect(() => {
    async function verifyExistingSession() {
      const portal = getPortalConfig();
      const storedToken = sessionStorage.getItem("blood_token");

      if (!storedToken) {
        if (portal.isDirectAdmin) {
          try {
            const adminRes = await api.post("/auth/admin-portal", {});
            if (adminRes.success && adminRes.data) {
              saveSession(adminRes.data.token, adminRes.data.user);
              setToken(adminRes.data.token);
              setUser(adminRes.data.user);
            }
          } catch (err) {
            console.error("Failed to establish direct admin session:", err);
          } finally {
            setLoading(false);
          }
          return;
        }
        setUser(null);
        setLoading(false);
        return;
      }

      try {
        const response = await api.get("/auth/me");
        if (response.success && response.data) {
          if (portal.isDirectAdmin && response.data.role !== "admin") {
            const adminRes = await api.post("/auth/admin-portal", {});
            if (adminRes.success && adminRes.data) {
              saveSession(adminRes.data.token, adminRes.data.user);
              setToken(adminRes.data.token);
              setUser(adminRes.data.user);
              return;
            }
          }
          setUser(response.data);
          sessionStorage.setItem("blood_user", JSON.stringify(response.data));
        } else {
          clearSession();
          setToken(null);
          setUser(null);
        }
      } catch {
        clearSession();
        setToken(null);
        setUser(null);
      } finally {
        setLoading(false);
      }
    }

    verifyExistingSession();
  }, []);

  const login = async (email, password, selectedRole = null) => {
    const payload = { email, password };
    if (selectedRole) {
      payload.role = selectedRole;
    }
    const response = await api.post("/auth/login", payload);
    if (response.success && response.data) {
      const { token: receivedToken, user: userPayload } = response.data;
      saveSession(receivedToken, userPayload);
      setToken(receivedToken);
      setUser(userPayload);
      return userPayload;
    }
    throw new Error(response.error || "Login failed");
  };

  const registerDonor = async (payload) => {
    const response = await api.post("/auth/register/donor", payload);
    if (response.success && response.data) {
      const { token: receivedToken, user: userPayload } = response.data;
      saveSession(receivedToken, userPayload);
      setToken(receivedToken);
      setUser(userPayload);
      return userPayload;
    }
    throw new Error(response.error || "Donor registration failed");
  };

  const registerRequester = async (payload) => {
    const response = await api.post("/auth/register/requester", payload);
    if (response.success && response.data) {
      const { token: receivedToken, user: userPayload } = response.data;
      saveSession(receivedToken, userPayload);
      setToken(receivedToken);
      setUser(userPayload);
      return userPayload;
    }
    throw new Error(response.error || "Requester registration failed");
  };

  const registerHospital = async (payload) => {
    const response = await api.post("/auth/register/hospital", payload);
    if (response.success && response.data) {
      const { token: receivedToken, user: userPayload } = response.data;
      saveSession(receivedToken, userPayload);
      setToken(receivedToken);
      setUser(userPayload);
      return userPayload;
    }
    throw new Error(response.error || "Hospital registration failed");
  };

  const logout = () => {
    clearSession();
    setToken(null);
    setUser(null);
  };

  const refreshProfile = async () => {
    try {
      const response = await api.get("/auth/me");
      if (response.success && response.data) {
        setUser(response.data);
        sessionStorage.setItem("blood_user", JSON.stringify(response.data));
      }
    } catch (err) {
      console.error("Failed to refresh profile:", err);
    }
  };

  const value = {
    user,
    token,
    role: user?.role || null,
    isAuthenticated: Boolean(token && user),
    loading,
    login,
    logout,
    registerDonor,
    registerRequester,
    registerHospital,
    refreshProfile,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
