import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { API_BASE_URL } from '../../config/api';
import LoadingSpinner from '../Common/LoadingSpinner';
import logoImage from '../../assets/erp_logo.png';
import styles from './LoginPage.module.css';

const LoginPage = () => {
  const [personId, setPersonId] = useState('');
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
      // Fetch person details
      const response = await fetch(`${API_BASE_URL}/api/v1/employees/${personId}`);
      if (!response.ok) {
        throw new Error('Invalid person ID');
      }

      const person = await response.json();
      
      // Determine role
      const role = person.role || 'worker';
      
      // Only allow admin and supervisor roles
      if (role !== 'admin' && role !== 'supervisor') {
        throw new Error('Access denied. Only admins and supervisors can log in.');
      }
      
      // Login user
      login({
        id: person.person_id || person.id,
        full_name: person.full_name,
        role: role,
        ...person,
      });

      // Redirect to unified dashboard
      navigate('/dashboard');
    } catch (err) {
      setError(err.message || 'Login failed. Please check your person ID.');
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
        <p className={styles.subtitle}>Enter your Person ID to continue</p>

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
              placeholder="Enter your 6-character ID"
              maxLength={6}
              required
              disabled={loading}
            />
          </div>

          <button
            type="submit"
            className={styles.submitButton}
            disabled={loading || !personId}
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
                // Directly call login logic
                setLoading(true);
                try {
                  const response = await fetch(`${API_BASE_URL}/api/v1/employees/ADMIN1`);
                  if (!response.ok) throw new Error('Failed to fetch admin');
                  const person = await response.json();
                  login({ id: person.id, full_name: person.full_name, role: person.role || 'admin', ...person });
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
                setPersonId('SUPER1');
                // Directly call login logic
                setLoading(true);
                try {
                  const response = await fetch(`${API_BASE_URL}/api/v1/employees/SUPER1`);
                  if (!response.ok) throw new Error('Failed to fetch supervisor');
                  const person = await response.json();
                  login({ id: person.id, full_name: person.full_name, role: person.role || 'supervisor', ...person });
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
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
