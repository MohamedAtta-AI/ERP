import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

// Session expiration time: 24 hours (in milliseconds)
const SESSION_EXPIRATION_TIME = 24 * 60 * 60 * 1000;
const SESSION_KEY = 'user';
const SESSION_TIMESTAMP_KEY = 'user_session_timestamp';

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check if session is expired
  const isSessionExpired = () => {
    const timestamp = localStorage.getItem(SESSION_TIMESTAMP_KEY);
    if (!timestamp) return true;
    
    const sessionTime = parseInt(timestamp, 10);
    const now = Date.now();
    return (now - sessionTime) > SESSION_EXPIRATION_TIME;
  };

  // Clear expired session
  const clearSession = () => {
    localStorage.removeItem(SESSION_KEY);
    localStorage.removeItem(SESSION_TIMESTAMP_KEY);
    setUser(null);
  };

  useEffect(() => {
    // Check for stored user session
    const storedUser = localStorage.getItem(SESSION_KEY);
    
    if (storedUser) {
      try {
        // Check if session is expired
        if (isSessionExpired()) {
          clearSession();
        } else {
          // Restore user and update session timestamp
          const userData = JSON.parse(storedUser);
          setUser(userData);
          // Update session timestamp to extend session
          localStorage.setItem(SESSION_TIMESTAMP_KEY, Date.now().toString());
        }
      } catch (e) {
        // Invalid stored data, clear it
        clearSession();
      }
    }
    setLoading(false);
  }, []);

  const login = (userData) => {
    setUser(userData);
    localStorage.setItem(SESSION_KEY, JSON.stringify(userData));
    // Store session timestamp
    localStorage.setItem(SESSION_TIMESTAMP_KEY, Date.now().toString());
  };

  const logout = () => {
    clearSession();
  };

  const hasRole = (role) => {
    if (!user || !user.role) return false;
    return user.role.toLowerCase() === role.toLowerCase();
  };

  const hasAnyRole = (roles) => {
    if (!user || !user.role) return false;
    return roles.some(role => user.role.toLowerCase() === role.toLowerCase());
  };

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      login,
      logout,
      hasRole,
      hasAnyRole,
      isAuthenticated: !!user,
    }}>
      {children}
    </AuthContext.Provider>
  );
};

