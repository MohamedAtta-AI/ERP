import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import { getAttendanceHistory, listEmployees, listOvertimeRequests } from "../../services/api";
import logoImage from "../../assets/erp_logo.png";
import styles from "./Dashboard.module.css";

const MainDashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    totalEmployees: 0,
    presentToday: 0,
    absentToday: 0,
    pendingOvertime: 0,
  });
  const [loading, setLoading] = useState(true);

  const isAdmin = user?.role === 'admin';
  const canRegister = user?.role === 'admin' || user?.role === 'supervisor';

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const today = new Date().toISOString().split('T')[0];
      const [employees, attendance, overtime] = await Promise.all([
        listEmployees({ role: "worker", limit: 1000 }).catch(() => []),
        getAttendanceHistory({
          start_date: today,
          end_date: today,
          limit: 5000,
        }).catch(() => []),
        listOvertimeRequests({ status: "pending" }).catch(() => []),
      ]);

      const workerIds = new Set((employees || []).map((employee) => employee.id));
      const totalEmployees = workerIds.size;
      const presentIds = new Set(
        (attendance || [])
          .map((record) => record.person_id)
          .filter((personId) => workerIds.has(personId))
      );
      const presentToday = presentIds.size;
      const absentToday = Math.max(totalEmployees - presentToday, 0);

      setStats({
        totalEmployees,
        presentToday,
        absentToday,
        pendingOvertime: (overtime || []).length,
      });

    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const getInitials = (name) => {
    if (!name) return 'U';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  if (loading) {
    return <div className={styles.loading}>Loading dashboard...</div>;
  }

  return (
    <div className={styles.dashboard}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.logo}>
          <img src={logoImage} alt="Ontime ERP" className={styles.logoImage} />
        </div>
        <div className={styles.headerActions}>
          <div className={styles.userProfile}>
            <div className={styles.avatar}>{getInitials(user?.full_name)}</div>
            <span className={styles.userName}>{user?.full_name || 'User'}</span>
            <span className={styles.userRole}>({user?.role})</span>
          </div>
          <button onClick={handleLogout} className={styles.logoutBtn}>
            Logout
          </button>
        </div>
      </header>

      <div className={styles.content}>
        <div className={styles.mainContent}>
          <div className={styles.welcomeSection}>
            <h1 className={styles.welcomeTitle}>Welcome, {user?.full_name?.split(' ')[0] || 'User'}</h1>
          </div>

          {/* KPI Cards */}
          <div className={styles.kpiGrid}>
            <div className={styles.kpiCard}>
              <div className={styles.kpiIcon} style={{ backgroundColor: "#D1FAE5" }}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10B981" strokeWidth="2">
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                  <circle cx="9" cy="7" r="4"></circle>
                  <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                  <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                </svg>
              </div>
              <div className={styles.kpiContent}>
                <h3 className={styles.kpiTitle}>Present Today</h3>
                <p className={styles.kpiValue}>{stats.presentToday}</p>
              </div>
            </div>

            <div className={styles.kpiCard}>
              <div className={styles.kpiIcon} style={{ backgroundColor: "#FEE2E2" }}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#EF4444" strokeWidth="2">
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                  <circle cx="9" cy="7" r="4"></circle>
                  <line x1="23" y1="11" x2="17" y2="11"></line>
                </svg>
              </div>
              <div className={styles.kpiContent}>
                <h3 className={styles.kpiTitle}>Absent Today</h3>
                <p className={styles.kpiValue}>{stats.absentToday}</p>
              </div>
            </div>

            <div className={styles.kpiCard}>
              <div className={styles.kpiIcon} style={{ backgroundColor: "#FEF3C7" }}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"></circle>
                  <polyline points="12 6 12 12 16 14"></polyline>
                </svg>
              </div>
              <div className={styles.kpiContent}>
                <h3 className={styles.kpiTitle}>Pending Overtime</h3>
                <p className={styles.kpiValue}>{stats.pendingOvertime}</p>
              </div>
            </div>
          </div>

          <div className={styles.modulesSection}>
            <h2 className={styles.sectionTitle}>Modules</h2>
            <div className={styles.modulesGrid}>
              <Link to="/attendance" className={styles.moduleCard}>
                <div className={styles.moduleIcon} style={{ color: "#10B981" }}>
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                    <circle cx="8.5" cy="7" r="4"></circle>
                    <path d="M20 8v6"></path>
                    <path d="M23 11h-6"></path>
                  </svg>
                </div>
                <span className={styles.moduleName}>Take Attendance</span>
                <span className={styles.moduleDescription}>Face recognition check-in</span>
              </Link>

              {canRegister && (
                <Link to="/register" className={styles.moduleCard}>
                  <div className={styles.moduleIcon} style={{ color: "#3B82F6" }}>
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                      <circle cx="8.5" cy="7" r="4"></circle>
                      <line x1="20" y1="8" x2="20" y2="14"></line>
                      <line x1="23" y1="11" x2="17" y2="11"></line>
                    </svg>
                  </div>
                  <span className={styles.moduleName}>
                    {isAdmin ? 'Register Employee' : 'Register Worker'}
                  </span>
                  <span className={styles.moduleDescription}>
                    {isAdmin ? 'Add workers and supervisors' : 'Add new workers'}
                  </span>
                </Link>
              )}

              <Link to="/overtime" className={styles.moduleCard}>
                <div className={styles.moduleIcon} style={{ color: "#F59E0B" }}>
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <polyline points="12 6 12 12 16 14"></polyline>
                  </svg>
                </div>
                <span className={styles.moduleName}>Overtime Management</span>
                <span className={styles.moduleDescription}>Create and manage overtime requests</span>
              </Link>

              <Link to="/employees" className={styles.moduleCard}>
                <div className={styles.moduleIcon} style={{ color: "#8B5CF6" }}>
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                    <circle cx="9" cy="7" r="4"></circle>
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                    <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                  </svg>
                </div>
                <span className={styles.moduleName}>Employee Management</span>
                <span className={styles.moduleDescription}>View, edit, assign and delete employees</span>
              </Link>

              {isAdmin && (
                <Link to="/admin/locations" className={styles.moduleCard}>
                  <div className={styles.moduleIcon} style={{ color: "#0EA5E9" }}>
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"></path>
                      <circle cx="12" cy="9" r="2.5"></circle>
                    </svg>
                  </div>
                  <span className={styles.moduleName}>Location Management</span>
                  <span className={styles.moduleDescription}>Manage sites and addresses</span>
                </Link>
              )}

              {isAdmin && (
                <Link to="/admin/shifts" className={styles.moduleCard}>
                  <div className={styles.moduleIcon} style={{ color: "#06B6D4" }}>
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="12" r="10"></circle>
                      <polyline points="12 6 12 12 16 14"></polyline>
                    </svg>
                  </div>
                  <span className={styles.moduleName}>Shift Management</span>
                  <span className={styles.moduleDescription}>Manage shifts and times</span>
                </Link>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MainDashboard;
