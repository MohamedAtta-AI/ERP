import React, { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import {
  listLocations, createLocation, deleteLocation,
  listShifts, createShift, deleteShift,
  listEmployees, getAttendanceHistory, reconcileAttendance,
  listOvertimeRequests, approveOvertime, rejectOvertime,
  listPayrollPeriods, listPayrollRuns,
} from "../../services/api";
import { useAuth } from "../../contexts/AuthContext";
import erpLogo from "../../assets/erp_logo.png";
import styles from "./AdminPage.module.css";

const TABS = [
  { id: "overview", label: "Overview", icon: "📊" },
  { id: "locations", label: "Locations", icon: "📍" },
  { id: "shifts", label: "Shifts", icon: "⏰" },
  { id: "employees", label: "Employees", icon: "👥" },
  { id: "overtime", label: "Overtime", icon: "⏱️" },
];

const AdminPage = () => {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState("overview");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  // Data states
  const [locations, setLocations] = useState([]);
  const [shifts, setShifts] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [overtimeRequests, setOvertimeRequests] = useState([]);
  const [payrollPeriods, setPayrollPeriods] = useState([]);
  const [todayAttendance, setTodayAttendance] = useState([]);
  const [stats, setStats] = useState({
    totalEmployees: 0,
    presentToday: 0,
    pendingOvertime: 0,
    totalLocations: 0,
  });

  // Form states
  const [showAddLocation, setShowAddLocation] = useState(false);
  const [showAddShift, setShowAddShift] = useState(false);
  const [newLocation, setNewLocation] = useState({ name: "", city: "", address: "" });
  const [newShift, setNewShift] = useState({ name: "", starts_at: "08:00", ends_at: "17:00", is_overnight: false });

  // Load data
  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const today = new Date().toISOString().split('T')[0];
      
      const [
        locationsData,
        shiftsData,
        employeesData,
        overtimeData,
        payrollData,
        attendanceData,
      ] = await Promise.all([
        listLocations().catch(() => []),
        listShifts().catch(() => []),
        listEmployees({ status: "active" }).catch(() => []),
        listOvertimeRequests({ status: "pending" }).catch(() => []),
        listPayrollPeriods().catch(() => []),
        getAttendanceHistory({ start_date: today, end_date: today, limit: 100 }).catch(() => []),
      ]);

      setLocations(locationsData || []);
      setShifts(shiftsData || []);
      setEmployees(employeesData || []);
      setOvertimeRequests(overtimeData || []);
      setPayrollPeriods(payrollData || []);
      setTodayAttendance(attendanceData || []);

      // Calculate stats
      setStats({
        totalEmployees: (employeesData || []).length,
        presentToday: (attendanceData || []).filter(a => a.check_in).length,
        pendingOvertime: (overtimeData || []).length,
        totalLocations: (locationsData || []).length,
      });
    } catch (err) {
      console.error("Failed to load data:", err);
      setError("Failed to load data. Please refresh.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Handle create location
  const handleCreateLocation = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      await createLocation(newLocation);
      setNewLocation({ name: "", city: "", address: "" });
      setShowAddLocation(false);
      setSuccessMessage("Location created successfully!");
      loadData();
    } catch (err) {
      setError(err.message || "Failed to create location");
    }
  };

  // Handle create shift
  const handleCreateShift = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      await createShift(newShift);
      setNewShift({ name: "", starts_at: "08:00", ends_at: "17:00", is_overnight: false });
      setShowAddShift(false);
      setSuccessMessage("Shift created successfully!");
      loadData();
    } catch (err) {
      setError(err.message || "Failed to create shift");
    }
  };

  // Handle reconcile attendance
  const handleReconcile = async () => {
    setError(null);
    try {
      const result = await reconcileAttendance();
      setSuccessMessage(
        `Reconciliation complete: ${result.absent_marked} marked absent, ` +
        `${result.overtime_requests_created} overtime requests created.`
      );
      loadData();
    } catch (err) {
      setError(err.message || "Reconciliation failed");
    }
  };

  // Handle approve overtime
  const handleApproveOvertime = async (id) => {
    try {
      await approveOvertime(id);
      setSuccessMessage("Overtime approved!");
      loadData();
    } catch (err) {
      setError(err.message || "Failed to approve overtime");
    }
  };

  // Handle reject overtime
  const handleRejectOvertime = async (id) => {
    try {
      await rejectOvertime(id, "Rejected by admin");
      setSuccessMessage("Overtime rejected");
      loadData();
    } catch (err) {
      setError(err.message || "Failed to reject overtime");
    }
  };

  // Clear messages after 3 seconds
  useEffect(() => {
    if (successMessage) {
      const timer = setTimeout(() => setSuccessMessage(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [successMessage]);

  return (
    <div className={styles.page}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <img src={erpLogo} alt="ERP Logo" className={styles.logo} />
          <span className={styles.headerTitle}>Admin Dashboard</span>
        </div>
        <div className={styles.headerRight}>
          <span className={styles.userName}>{user?.full_name || "Admin"}</span>
          <Link to="/dashboard" className={styles.backLink}>← Dashboard</Link>
          <button onClick={logout} className={styles.logoutBtn}>Logout</button>
        </div>
      </header>

      {/* Main Content */}
      <div className={styles.main}>
        {/* Sidebar Navigation */}
        <nav className={styles.sidebar}>
          {TABS.map((tab) => (
            <button
              key={tab.id}
              className={`${styles.navItem} ${activeTab === tab.id ? styles.navItemActive : ""}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <span className={styles.navIcon}>{tab.icon}</span>
              <span className={styles.navLabel}>{tab.label}</span>
            </button>
          ))}
        </nav>

        {/* Content Area */}
        <div className={styles.content}>
          {/* Messages */}
          {error && (
            <div className={styles.errorBanner}>
              {error}
              <button onClick={() => setError(null)}>×</button>
            </div>
          )}
          {successMessage && (
            <div className={styles.successBanner}>
              {successMessage}
            </div>
          )}

          {isLoading && <div className={styles.loading}>Loading...</div>}

          {/* Overview Tab */}
          {activeTab === "overview" && !isLoading && (
            <div className={styles.overview}>
              <h2 className={styles.sectionTitle}>System Overview</h2>
              <div className={styles.statsGrid}>
                <div className={styles.statCard}>
                  <div className={styles.statIcon}>👥</div>
                  <div className={styles.statInfo}>
                    <span className={styles.statValue}>{stats.totalEmployees}</span>
                    <span className={styles.statLabel}>Total Employees</span>
                  </div>
                </div>
                <div className={styles.statCard}>
                  <div className={styles.statIcon}>✓</div>
                  <div className={styles.statInfo}>
                    <span className={styles.statValue}>{stats.presentToday}</span>
                    <span className={styles.statLabel}>Present Today</span>
                  </div>
                </div>
                <div className={styles.statCard}>
                  <div className={styles.statIcon}>⏱️</div>
                  <div className={styles.statInfo}>
                    <span className={styles.statValue}>{stats.pendingOvertime}</span>
                    <span className={styles.statLabel}>Pending Overtime</span>
                  </div>
                </div>
                <div className={styles.statCard}>
                  <div className={styles.statIcon}>📍</div>
                  <div className={styles.statInfo}>
                    <span className={styles.statValue}>{stats.totalLocations}</span>
                    <span className={styles.statLabel}>Locations</span>
                  </div>
                </div>
              </div>

              <div className={styles.actionsSection}>
                <h3>Quick Actions</h3>
                <div className={styles.actionButtons}>
                  <button onClick={handleReconcile} className={styles.actionBtn}>
                    🔄 Reconcile Today's Attendance
                  </button>
                  <button onClick={() => setActiveTab("overtime")} className={styles.actionBtn}>
                    ⏱️ Review Overtime ({stats.pendingOvertime})
                  </button>
                  <Link to="/register" className={styles.actionBtn}>
                    ➕ Register New Employee
                  </Link>
                  <Link to="/attendance" className={styles.actionBtn}>
                    📋 Take Attendance
                  </Link>
                </div>
              </div>

              <div className={styles.recentSection}>
                <h3>Today's Attendance ({todayAttendance.length})</h3>
                {todayAttendance.length === 0 ? (
                  <p className={styles.emptyText}>No attendance records today</p>
                ) : (
                  <div className={styles.attendanceList}>
                    {todayAttendance.slice(0, 10).map((record) => (
                      <div key={record.id} className={styles.attendanceItem}>
                        <span className={styles.attendanceName}>{record.person_name}</span>
                        <span className={`${styles.attendanceStatus} ${
                          record.check_out ? styles.statusOut : styles.statusIn
                        }`}>
                          {record.check_in ? new Date(record.check_in).toLocaleTimeString() : "—"}
                          {record.check_out && ` → ${new Date(record.check_out).toLocaleTimeString()}`}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Locations Tab */}
          {activeTab === "locations" && !isLoading && (
            <div className={styles.section}>
              <div className={styles.sectionHeader}>
                <h2 className={styles.sectionTitle}>Locations</h2>
                <button
                  className={styles.addBtn}
                  onClick={() => setShowAddLocation(!showAddLocation)}
                >
                  {showAddLocation ? "Cancel" : "+ Add Location"}
                </button>
              </div>

              {showAddLocation && (
                <form onSubmit={handleCreateLocation} className={styles.addForm}>
                  <input
                    type="text"
                    placeholder="Location Name *"
                    value={newLocation.name}
                    onChange={(e) => setNewLocation({ ...newLocation, name: e.target.value })}
                    required
                    className={styles.input}
                  />
                  <input
                    type="text"
                    placeholder="City"
                    value={newLocation.city}
                    onChange={(e) => setNewLocation({ ...newLocation, city: e.target.value })}
                    className={styles.input}
                  />
                  <input
                    type="text"
                    placeholder="Address"
                    value={newLocation.address}
                    onChange={(e) => setNewLocation({ ...newLocation, address: e.target.value })}
                    className={styles.input}
                  />
                  <button type="submit" className={styles.submitBtn}>Create</button>
                </form>
              )}

              <div className={styles.itemList}>
                {locations.length === 0 ? (
                  <p className={styles.emptyText}>No locations configured</p>
                ) : (
                  locations.map((loc) => (
                    <div key={loc.id} className={styles.itemCard}>
                      <div className={styles.itemInfo}>
                        <span className={styles.itemName}>{loc.name}</span>
                        {loc.city && <span className={styles.itemMeta}>{loc.city}</span>}
                        {loc.address && <span className={styles.itemMeta}>{loc.address}</span>}
                      </div>
                      <button
                        className={styles.deleteBtn}
                        onClick={() => deleteLocation(loc.id).then(loadData)}
                      >
                        Delete
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* Shifts Tab */}
          {activeTab === "shifts" && !isLoading && (
            <div className={styles.section}>
              <div className={styles.sectionHeader}>
                <h2 className={styles.sectionTitle}>Shifts</h2>
                <button
                  className={styles.addBtn}
                  onClick={() => setShowAddShift(!showAddShift)}
                >
                  {showAddShift ? "Cancel" : "+ Add Shift"}
                </button>
              </div>

              {showAddShift && (
                <form onSubmit={handleCreateShift} className={styles.addForm}>
                  <input
                    type="text"
                    placeholder="Shift Name"
                    value={newShift.name}
                    onChange={(e) => setNewShift({ ...newShift, name: e.target.value })}
                    className={styles.input}
                  />
                  <div className={styles.timeInputs}>
                    <label>
                      Start Time:
                      <input
                        type="time"
                        value={newShift.starts_at}
                        onChange={(e) => setNewShift({ ...newShift, starts_at: e.target.value })}
                        required
                        className={styles.input}
                      />
                    </label>
                    <label>
                      End Time:
                      <input
                        type="time"
                        value={newShift.ends_at}
                        onChange={(e) => setNewShift({ ...newShift, ends_at: e.target.value })}
                        required
                        className={styles.input}
                      />
                    </label>
                  </div>
                  <label className={styles.checkboxLabel}>
                    <input
                      type="checkbox"
                      checked={newShift.is_overnight}
                      onChange={(e) => setNewShift({ ...newShift, is_overnight: e.target.checked })}
                    />
                    Overnight Shift
                  </label>
                  <button type="submit" className={styles.submitBtn}>Create</button>
                </form>
              )}

              <div className={styles.itemList}>
                {shifts.length === 0 ? (
                  <p className={styles.emptyText}>No shifts configured</p>
                ) : (
                  shifts.map((shift) => (
                    <div key={shift.id} className={styles.itemCard}>
                      <div className={styles.itemInfo}>
                        <span className={styles.itemName}>{shift.name || "Unnamed Shift"}</span>
                        <span className={styles.itemMeta}>
                          {shift.starts_at} → {shift.ends_at}
                          {shift.is_overnight && " (Overnight)"}
                        </span>
                      </div>
                      <button
                        className={styles.deleteBtn}
                        onClick={() => deleteShift(shift.id).then(loadData)}
                      >
                        Delete
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* Employees Tab */}
          {activeTab === "employees" && !isLoading && (
            <div className={styles.section}>
              <div className={styles.sectionHeader}>
                <h2 className={styles.sectionTitle}>Employees ({employees.length})</h2>
                <Link to="/register" className={styles.addBtn}>+ Register New</Link>
              </div>

              <div className={styles.itemList}>
                {employees.length === 0 ? (
                  <p className={styles.emptyText}>No employees registered</p>
                ) : (
                  employees.map((emp) => (
                    <div key={emp.id || emp.person_id} className={styles.itemCard}>
                      <div className={styles.itemInfo}>
                        <span className={styles.itemName}>{emp.full_name}</span>
                        <span className={styles.itemMeta}>
                          ID: {emp.id || emp.person_id}
                          {emp.department && ` • ${emp.department}`}
                          {emp.position && ` • ${emp.position}`}
                        </span>
                      </div>
                      <span className={`${styles.badge} ${
                        emp.has_face_enrolled ? styles.badgeSuccess : styles.badgeWarning
                      }`}>
                        {emp.has_face_enrolled ? "Face Enrolled" : "No Face"}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* Overtime Tab */}
          {activeTab === "overtime" && !isLoading && (
            <div className={styles.section}>
              <div className={styles.sectionHeader}>
                <h2 className={styles.sectionTitle}>Pending Overtime Requests</h2>
                <button onClick={handleReconcile} className={styles.addBtn}>
                  🔄 Reconcile
                </button>
              </div>

              <div className={styles.itemList}>
                {overtimeRequests.length === 0 ? (
                  <p className={styles.emptyText}>No pending overtime requests</p>
                ) : (
                  overtimeRequests.map((req) => (
                    <div key={req.id} className={styles.itemCard}>
                      <div className={styles.itemInfo}>
                        <span className={styles.itemName}>{req.person_name || req.person_id}</span>
                        <span className={styles.itemMeta}>
                          Date: {req.overtime_date} • Hours: {req.hours}
                        </span>
                      </div>
                      <div className={styles.actionGroup}>
                        <button
                          className={styles.approveBtn}
                          onClick={() => handleApproveOvertime(req.id)}
                        >
                          ✓ Approve
                        </button>
                        <button
                          className={styles.rejectBtn}
                          onClick={() => handleRejectOvertime(req.id)}
                        >
                          ✗ Reject
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* Payroll Tab */}
          {activeTab === "payroll" && !isLoading && (
            <div className={styles.section}>
              <div className={styles.sectionHeader}>
                <h2 className={styles.sectionTitle}>Payroll Periods</h2>
              </div>

              <div className={styles.itemList}>
                {payrollPeriods.length === 0 ? (
                  <p className={styles.emptyText}>No payroll periods configured</p>
                ) : (
                  payrollPeriods.map((period) => (
                    <div key={period.id} className={styles.itemCard}>
                      <div className={styles.itemInfo}>
                        <span className={styles.itemName}>
                          {period.start_date} to {period.end_date}
                        </span>
                        <span className={`${styles.badge} ${
                          period.status === "open" ? styles.badgeSuccess :
                          period.status === "closed" ? styles.badgeWarning :
                          styles.badgeLocked
                        }`}>
                          {period.status}
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminPage;

