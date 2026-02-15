import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { changePassword, login as loginAPI } from '../../services/api';
import LoadingSpinner from '../Common/LoadingSpinner';
import logoImage from '../../assets/erp_logo.png';
import styles from './LoginPage.module.css';

const LoginPage = () => {
  const [personId, setPersonId] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [passwordUpdateError, setPasswordUpdateError] = useState(null);
  const [passwordUpdateLoading, setPasswordUpdateLoading] = useState(false);
  const [pendingPasswordChange, setPendingPasswordChange] = useState(null);
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const { login, isAuthenticated, loading: authLoading } = useAuth();
  const navigate = useNavigate();

  // Redirect if already authenticated
  useEffect(() => {
    if (!authLoading && isAuthenticated && !pendingPasswordChange) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, authLoading, pendingPasswordChange, navigate]);

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

      if (data.require_password_change) {
        setPendingPasswordChange({
          currentPassword: password,
          userId: data.user.id,
          fullName: data.user.full_name,
        });
        setPassword('');
        return;
      }

      // Redirect to unified dashboard
      navigate('/dashboard');
    } catch (err) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const validateNewPassword = (value) => {
    if (!value || value.length < 8) return 'Password must be at least 8 characters.';
    if (!/[A-Z]/.test(value)) return 'Password must include an uppercase letter.';
    if (!/[a-z]/.test(value)) return 'Password must include a lowercase letter.';
    if (!/[0-9]/.test(value)) return 'Password must include a number.';
    if (!/[^A-Za-z0-9]/.test(value)) return 'Password must include a special character.';
    return null;
  };

  const handlePasswordUpdate = async (e) => {
    e.preventDefault();
    setPasswordUpdateError(null);

    const validationError = validateNewPassword(newPassword);
    if (validationError) {
      setPasswordUpdateError(validationError);
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordUpdateError('New password and confirmation do not match.');
      return;
    }
    if (newPassword === pendingPasswordChange?.currentPassword) {
      setPasswordUpdateError('Please choose a different password from the default password.');
      return;
    }

    setPasswordUpdateLoading(true);
    try {
      await changePassword({
        current_password: pendingPasswordChange.currentPassword,
        new_password: newPassword,
      });
      setPendingPasswordChange(null);
      setNewPassword('');
      setConfirmPassword('');
      navigate('/dashboard');
    } catch (err) {
      setPasswordUpdateError(err.message || 'Failed to update password.');
    } finally {
      setPasswordUpdateLoading(false);
    }
  };

  return (
    <div className={styles.loginContainer}>
      <div className={styles.loginCard}>
        <div className={styles.logo}>
          <img src={logoImage} alt="Ontime ERP" className={styles.logoImage} />
        </div>
        
        <h2 className={styles.title}>
          {pendingPasswordChange ? 'Set New Password' : 'Sign In'}
        </h2>

        {pendingPasswordChange ? (
          <div className={styles.passwordSetupCard}>
            <div className={styles.passwordSetupIntro}>
              <p>
                Welcome, <strong>{pendingPasswordChange.fullName}</strong>.
              </p>
              <p>
                Your supervisor account was created with the default password
                <code> Welcome@123 </code>. Set a private password to continue.
              </p>
            </div>
            <form onSubmit={handlePasswordUpdate} className={styles.form}>
              {passwordUpdateError && (
                <div className={styles.errorMessage}>
                  {passwordUpdateError}
                </div>
              )}
              <div className={styles.inputGroup}>
                <label htmlFor="newPassword">New Password</label>
                <input
                  id="newPassword"
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Enter new password"
                  required
                  disabled={passwordUpdateLoading}
                  autoComplete="new-password"
                />
              </div>
              <div className={styles.inputGroup}>
                <label htmlFor="confirmPassword">Confirm New Password</label>
                <input
                  id="confirmPassword"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Confirm new password"
                  required
                  disabled={passwordUpdateLoading}
                  autoComplete="new-password"
                />
              </div>
              <ul className={styles.passwordRules}>
                <li>At least 8 characters</li>
                <li>Uppercase, lowercase, number, and special character</li>
              </ul>
              <button
                type="submit"
                className={styles.submitButton}
                disabled={passwordUpdateLoading || !newPassword || !confirmPassword}
              >
                {passwordUpdateLoading ? 'Updating...' : 'Update Password'}
              </button>
            </form>
          </div>
        ) : (
          <>
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

          </>
        )}
      </div>
    </div>
  );
};

export default LoginPage;
