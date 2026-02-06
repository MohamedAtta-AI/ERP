import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { login as loginAPI } from '../../services/api';
import LoadingSpinner from '../Common/LoadingSpinner';
import logoImage from '../../assets/erp_logo.png';
import styles from './LoginPage.module.css';

const LoginPage = () => {
  const [personId, setPersonId] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { login, isAuthenticated, loading: authLoading } = useAuth();
  const navigate = useNavigate();

  // Redirect if already authenticated
  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, authLoading, navigate]);

  // Show loading while checking auth state
  if (authLoading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh'
      }}>
        <LoadingSpinner size="large" message="Loading session..." />
      </div>
    );
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      // Use the login API function that sends form data
      const data = await loginAPI({
        username: personId,
        password: password,
      });
      
      // Login user with tokens
      login(
        {
          id: data.user.id,
          full_name: data.user.full_name,
          role: data.user.role,
          ...data.user,
        },
        data.access_token,
        data.refresh_token
      );

      // Redirect to unified dashboard
      navigate('/dashboard');
    } catch (err) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.loginContainer}>
      <div className={styles.loginCard}>
        <div className={styles.logo}>
          <img src={logoImage} alt="Ontime ERP" className={styles.logoImage} />
        </div>
        
        <h2 className={styles.title}>Sign In</h2>

        <form onSubmit={handleSubmit} className={styles.form}>
          {error && (
            <div className={styles.errorMessage}>
              {error}
            </div>
          )}

          <div className={styles.inputGroup}>
            <label htmlFor="personId">Person ID</label>
            <input
              id="personId"
              type="text"
              value={personId}
              onChange={(e) => setPersonId(e.target.value.toUpperCase())}
              placeholder="Enter your Person ID"
              required
              disabled={loading}
              autoComplete="username"
            />
          </div>

          <div className={styles.inputGroup}>
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
              disabled={loading}
              autoComplete="current-password"
            />
          </div>

          <button
            type="submit"
            className={styles.submitButton}
            disabled={loading || !personId || !password}
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div className={styles.footer}>
          <p>Quick Demo Login:</p>
          <div className={styles.demoButtons}>
            <button 
              type="button" 
              onClick={async () => { 
                setPersonId('ADMIN1');
                setPassword('admin123');
                setLoading(true);
                try {
                  const data = await loginAPI({
                    username: 'ADMIN1',
                    password: 'admin123',
                  });
                  login(
                    { id: data.user.id, full_name: data.user.full_name, role: data.user.role, ...data.user },
                    data.access_token,
                    data.refresh_token
                  );
                  navigate('/dashboard');
                } catch (err) {
                  setError(err.message);
                } finally {
                  setLoading(false);
                }
              }}
              className={styles.demoButton}
              disabled={loading}
            >
              Admin
            </button>
            <button 
              type="button" 
              onClick={async () => { 
                setPersonId('SUP001');
                setPassword('supervisor123');
                setLoading(true);
                try {
                  const data = await loginAPI({
                    username: 'SUP001',
                    password: 'supervisor123',
                  });
                  login(
                    { id: data.user.id, full_name: data.user.full_name, role: data.user.role, ...data.user },
                    data.access_token,
                    data.refresh_token
                  );
                  navigate('/dashboard');
                } catch (err) {
                  setError(err.message);
                } finally {
                  setLoading(false);
                }
              }}
              className={styles.demoButton}
              disabled={loading}
            >
              Supervisor
            </button>
            <button 
              type="button" 
              onClick={async () => { 
                setPersonId('WRK001');
                setPassword('worker123');
                setLoading(true);
                try {
                  const data = await loginAPI({
                    username: 'WRK001',
                    password: 'worker123',
                  });
                  login(
                    { id: data.user.id, full_name: data.user.full_name, role: data.user.role, ...data.user },
                    data.access_token,
                    data.refresh_token
                  );
                  navigate('/dashboard');
                } catch (err) {
                  setError(err.message);
                } finally {
                  setLoading(false);
                }
              }}
              className={styles.demoButton}
              disabled={loading}
            >
              Worker
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
