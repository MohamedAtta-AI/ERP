import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import { getAttendanceHistory, listOvertimeRequests, listEmployees } from "../../services/api";
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
  const [recentActivity, setRecentActivity] = useState([]);
  const [loading, setLoading] = useState(true);

  const isAdmin = user?.role === 'admin';

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const today = new Date().toISOString().split('T')[0];
      
      // Fetch today's attendance using authenticated API client
      let attendance = [];
      try {
        attendance = await getAttendanceHistory({
          start_date: today,
          end_date: today,
          limit: 100
        });
      } catch (err) {
        console.warn('Failed to fetch attendance:', err);
      }
      
      // Fetch pending overtime using authenticated API client
      let overtime = [];
      try {
        overtime = await listOvertimeRequests({ status: 'pending' });
      } catch (err) {
        console.warn('Failed to fetch overtime:', err);
      }

      // Fetch total employees count
      let totalEmployees = 0;
      try {
        const employees = await listEmployees({ limit: 1000 });
        totalEmployees = employees.length || 0;
      } catch (err) {
        console.warn('Failed to fetch employees:', err);
      }

      // Calculate stats
      const presentIds = new Set(attendance.map(a => a.person_id));
      const presentCount = attendance.filter(a => a.check_in && !a.check_out).length;
      const absentCount = totalEmployees > 0 ? Math.max(0, totalEmployees - presentCount) : 0;
      
      setStats({
        totalEmployees: totalEmployees,
        presentToday: presentCount,
        absentToday: absentCount,
        pendingOvertime: overtime.length || 0,
      });

      // Build recent activity from attendance
      const activity = attendance.slice(0, 5).map(a => ({
        id: a.id,
        type: a.check_out ? 'checkout' : 'checkin',
        title: a.check_out ? 'Check Out' : 'Check In',
        description: `${a.person_name || a.person_id} - ${a.check_out ? 'Left' : 'Arrived'}`,
        time: new Date(a.check_out || a.check_in).toLocaleTimeString(),
      }));
      setRecentActivity(activity);
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
        {/* Main Content Area */}
        <div className={styles.mainContent}>
          {/* Welcome Section */}
          <div className={styles.welcomeSection}>
            <h1 className={styles.welcomeTitle}>
              Welcome back, {user?.full_name?.split(' ')[0] || 'User'}
            </h1>
            <p className={styles.welcomeSubtitle}>
              {isAdmin 
                ? "Manage attendance, payroll, and workers from here."
                : "Take attendance and manage your team from here."}
            </p>
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

            {isAdmin && (
              <div className={styles.kpiCard}>
                <div className={styles.kpiIcon} style={{ backgroundColor: "#E0E7FF" }}>
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#6366F1" strokeWidth="2">
                    <line x1="12" y1="1" x2="12" y2="23"></line>
                    <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
                  </svg>
                </div>
                <div className={styles.kpiContent}>
                  <h3 className={styles.kpiTitle}>Payroll Runs</h3>
                  <p className={styles.kpiValue}>0</p>
                </div>
              </div>
            )}
          </div>

          {/* Modules Section */}
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

              {/* Register Workers - Admin and Supervisor */}
              <Link to="/register" className={styles.moduleCard}>
                <div className={styles.moduleIcon} style={{ color: "#3B82F6" }}>
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                    <circle cx="8.5" cy="7" r="4"></circle>
                    <line x1="20" y1="8" x2="20" y2="14"></line>
                    <line x1="23" y1="11" x2="17" y2="11"></line>
                  </svg>
                </div>
                <span className={styles.moduleName}>Register Worker</span>
                <span className={styles.moduleDescription}>Add new workers</span>
              </Link>

              {/* Workers Management - Supervisor/Admin */}
              <Link to="/supervisor/workers" className={styles.moduleCard}>
                <div className={styles.moduleIcon} style={{ color: "#8B5CF6" }}>
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                    <circle cx="9" cy="7" r="4"></circle>
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                    <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                  </svg>
                </div>
                <span className={styles.moduleName}>My Workers</span>
                <span className={styles.moduleDescription}>View & edit team members</span>
              </Link>

              {/* Overtime Management */}
              <Link to="/supervisor/overtime" className={styles.moduleCard}>
                <div className={styles.moduleIcon} style={{ color: "#F59E0B" }}>
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <polyline points="12 6 12 12 16 14"></polyline>
                  </svg>
                </div>
                <span className={styles.moduleName}>Overtime</span>
                <span className={styles.moduleDescription}>Review pending requests</span>
              </Link>

              {/* Admin-only modules */}
              {/* Admin-only modules */}
              {isAdmin && (
                <>
                  <Link to="/admin/payroll" className={styles.moduleCard}>
                    <div className={styles.moduleIcon} style={{ color: "#10B981" }}>
                      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <line x1="12" y1="1" x2="12" y2="23"></line>
                        <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
                      </svg>
                    </div>
                    <span className={styles.moduleName}>Payroll</span>
                    <span className={styles.moduleDescription}>Manage payroll runs</span>
                  </Link>
                  <Link to="/admin" className={styles.moduleCard}>
                    <div className={styles.moduleIcon} style={{ color: "#6366F1" }}>
                      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="3"></circle>
                        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
                      </svg>
                    </div>
                    <span className={styles.moduleName}>Admin Panel</span>
                    <span className={styles.moduleDescription}>Manage system settings</span>
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className={styles.sidebar}>
          {/* Quick Actions */}
          <div className={styles.quickActionsSection}>
            <h2 className={styles.sectionTitle}>Quick Actions</h2>
            <div className={styles.quickActionsGrid}>
              <Link
                to="/attendance"
                className={styles.quickActionBtn}
                style={{ backgroundColor: "#10B981", color: "white" }}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                  <circle cx="8.5" cy="7" r="4"></circle>
                  <path d="M20 8v6"></path>
                  <path d="M23 11h-6"></path>
                </svg>
                <span>Take Attendance</span>
              </Link>

              <Link
                to="/register"
                className={styles.quickActionBtn}
                style={{ backgroundColor: "#3B82F6", color: "white" }}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                  <circle cx="8.5" cy="7" r="4"></circle>
                  <line x1="20" y1="8" x2="20" y2="14"></line>
                  <line x1="23" y1="11" x2="17" y2="11"></line>
                </svg>
                <span>Register Worker</span>
              </Link>

              {isAdmin && (
                <Link
                  to="/admin/payroll"
                  className={styles.quickActionBtn}
                  style={{ backgroundColor: "#6366F1", color: "white" }}
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="12" y1="1" x2="12" y2="23"></line>
                    <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
                  </svg>
                  <span>Payroll</span>
                </Link>
              )}
            </div>
          </div>

          {/* Recent Activity */}
          <div className={styles.recentActivitySection}>
            <h2 className={styles.sectionTitle}>
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                style={{ display: "inline", marginRight: "8px" }}
              >
                <circle cx="12" cy="12" r="10"></circle>
                <polyline points="12 6 12 12 16 14"></polyline>
              </svg>
              Recent Activity
            </h2>
            <div className={styles.activityList}>
              {recentActivity.length > 0 ? (
                recentActivity.map((activity) => (
                  <div key={activity.id} className={styles.activityItem}>
                    <div
                      className={styles.activityIcon}
                      style={{ backgroundColor: activity.type === 'checkin' ? "#10B981" : "#F59E0B" }}
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                        {activity.type === 'checkin' ? (
                          <>
                            <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                            <circle cx="8.5" cy="7" r="4"></circle>
                            <path d="M20 8v6"></path>
                            <path d="M23 11h-6"></path>
                          </>
                        ) : (
                          <>
                            <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                            <circle cx="8.5" cy="7" r="4"></circle>
                            <line x1="23" y1="11" x2="17" y2="11"></line>
                          </>
                        )}
                      </svg>
                    </div>
                    <div className={styles.activityContent}>
                      <p className={styles.activityTitle}>{activity.title}</p>
                      <p className={styles.activityDescription}>{activity.description}</p>
                      <span className={styles.activityTime}>{activity.time}</span>
                    </div>
                  </div>
                ))
              ) : (
                <div className={styles.activityItem}>
                  <div className={styles.activityContent}>
                    <p className={styles.activityDescription}>No recent activity</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MainDashboard;

