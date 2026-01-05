import React, { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import {
  listLocations, createLocation, deleteLocation, updateLocation,
  listShifts, createShift, deleteShift, updateShift,
  listEmployees, getAttendanceHistory, reconcileAttendance, getEmployee, updateEmployee,
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
  { id: "payroll", label: "Payroll", icon: "💰" },
];

const AdminPage = () => {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState("overview");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  // Data states
  const [locations, setLocations] = useState([]);
  const [filteredLocations, setFilteredLocations] = useState([]);
  const [shifts, setShifts] = useState([]);
  const [filteredShifts, setFilteredShifts] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [filteredEmployees, setFilteredEmployees] = useState([]);
  const [overtimeRequests, setOvertimeRequests] = useState([]);
  const [filteredOvertime, setFilteredOvertime] = useState([]);
  const [payrollPeriods, setPayrollPeriods] = useState([]);
  const [todayAttendance, setTodayAttendance] = useState([]);
  const [searchTerms, setSearchTerms] = useState({
    locations: '',
    shifts: '',
    employees: '',
    overtime: '',
  });
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [editEmployeeMode, setEditEmployeeMode] = useState(false);
  const [editEmployeeForm, setEditEmployeeForm] = useState({});
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
      setFilteredLocations(locationsData || []);
      setShifts(shiftsData || []);
      setFilteredShifts(shiftsData || []);
      setEmployees(employeesData || []);
      setFilteredEmployees(employeesData || []);
      setOvertimeRequests(overtimeData || []);
      setFilteredOvertime(overtimeData || []);
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

  // Filter data based on search terms
  useEffect(() => {
    if (!searchTerms.locations.trim()) {
      setFilteredLocations(locations);
    } else {
      setFilteredLocations(locations.filter(loc =>
        loc.name?.toLowerCase().includes(searchTerms.locations.toLowerCase()) ||
        loc.city?.toLowerCase().includes(searchTerms.locations.toLowerCase())
      ));
    }
  }, [searchTerms.locations, locations]);

  useEffect(() => {
    if (!searchTerms.shifts.trim()) {
      setFilteredShifts(shifts);
    } else {
      setFilteredShifts(shifts.filter(shift =>
        shift.name?.toLowerCase().includes(searchTerms.shifts.toLowerCase())
      ));
    }
  }, [searchTerms.shifts, shifts]);

  useEffect(() => {
    if (!searchTerms.employees.trim()) {
      setFilteredEmployees(employees);
    } else {
      setFilteredEmployees(employees.filter(emp =>
        emp.full_name?.toLowerCase().includes(searchTerms.employees.toLowerCase()) ||
        (emp.person_id || emp.id)?.toLowerCase().includes(searchTerms.employees.toLowerCase()) ||
        emp.email?.toLowerCase().includes(searchTerms.employees.toLowerCase())
      ));
    }
  }, [searchTerms.employees, employees]);

  useEffect(() => {
    if (!searchTerms.overtime.trim()) {
      setFilteredOvertime(overtimeRequests);
    } else {
      setFilteredOvertime(overtimeRequests.filter(req =>
        req.person_name?.toLowerCase().includes(searchTerms.overtime.toLowerCase()) ||
        req.person_id?.toLowerCase().includes(searchTerms.overtime.toLowerCase())
      ));
    }
  }, [searchTerms.overtime, overtimeRequests]);

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
    const reason = window.prompt('Rejection reason:');
    if (!reason) return;
    try {
      await rejectOvertime(id, reason);
      setSuccessMessage("Overtime rejected");
      loadData();
    } catch (err) {
      setError(err.message || "Failed to reject overtime");
    }
  };

  // Handle edit employee
  const handleEditEmployee = async (employee) => {
    try {
      const details = await getEmployee(employee.person_id || employee.id);
      setSelectedEmployee(details);
      setEditEmployeeForm({
        full_name: details.full_name || '',
        phone: details.phone || '',
        email: details.email || '',
        department: details.department || '',
        position: details.position || '',
        identity_number: details.identity_number || '',
        dob: details.dob || '',
        sex: details.sex || '',
      });
      setEditEmployeeMode(true);
    } catch (err) {
      setError(err.message || "Failed to load employee details");
    }
  };

  const handleSaveEmployee = async (e) => {
    e.preventDefault();
    try {
      await updateEmployee(selectedEmployee.person_id || selectedEmployee.id, editEmployeeForm);
      setSuccessMessage("Employee updated successfully!");
      setEditEmployeeMode(false);
      setSelectedEmployee(null);
      loadData();
    } catch (err) {
      setError(err.message || "Failed to update employee");
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
                <div className={styles.headerActions}>
                  <input
                    type="text"
                    placeholder="Search locations..."
                    value={searchTerms.locations}
                    onChange={(e) => setSearchTerms({ ...searchTerms, locations: e.target.value })}
                    className={styles.searchInput}
                  />
                  <button
                    className={styles.addBtn}
                    onClick={() => setShowAddLocation(!showAddLocation)}
                  >
                    {showAddLocation ? "Cancel" : "+ Add Location"}
                  </button>
                </div>
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
                {filteredLocations.length === 0 ? (
                  <p className={styles.emptyText}>
                    {searchTerms.locations ? 'No locations found matching your search' : 'No locations configured'}
                  </p>
                ) : (
                  filteredLocations.map((loc) => (
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
                <div className={styles.headerActions}>
                  <input
                    type="text"
                    placeholder="Search shifts..."
                    value={searchTerms.shifts}
                    onChange={(e) => setSearchTerms({ ...searchTerms, shifts: e.target.value })}
                    className={styles.searchInput}
                  />
                  <button
                    className={styles.addBtn}
                    onClick={() => setShowAddShift(!showAddShift)}
                  >
                    {showAddShift ? "Cancel" : "+ Add Shift"}
                  </button>
                </div>
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
                {filteredShifts.length === 0 ? (
                  <p className={styles.emptyText}>
                    {searchTerms.shifts ? 'No shifts found matching your search' : 'No shifts configured'}
                  </p>
                ) : (
                  filteredShifts.map((shift) => (
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
                <div className={styles.headerActions}>
                  <input
                    type="text"
                    placeholder="Search employees..."
                    value={searchTerms.employees}
                    onChange={(e) => setSearchTerms({ ...searchTerms, employees: e.target.value })}
                    className={styles.searchInput}
                  />
                  <Link to="/register" className={styles.addBtn}>+ Register New</Link>
                </div>
              </div>

              <div className={styles.itemList}>
                {filteredEmployees.length === 0 ? (
                  <p className={styles.emptyText}>
                    {searchTerms.employees ? 'No employees found matching your search' : 'No employees registered'}
                  </p>
                ) : (
                  filteredEmployees.map((emp) => (
                    <div key={emp.id || emp.person_id} className={styles.itemCard}>
                      <div className={styles.itemInfo}>
                        <span className={styles.itemName}>{emp.full_name}</span>
                        <span className={styles.itemMeta}>
                          ID: {emp.id || emp.person_id}
                          {emp.department && ` • ${emp.department}`}
                          {emp.position && ` • ${emp.position}`}
                          {emp.email && ` • ${emp.email}`}
                          {emp.phone && ` • ${emp.phone}`}
                        </span>
                      </div>
                      <div className={styles.actionGroup}>
                        <span className={`${styles.badge} ${
                          emp.has_face_enrolled ? styles.badgeSuccess : styles.badgeWarning
                        }`}>
                          {emp.has_face_enrolled ? "Face Enrolled" : "No Face"}
                        </span>
                        <button
                          className={styles.editBtn}
                          onClick={() => handleEditEmployee(emp)}
                        >
                          Edit
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* Edit Employee Modal */}
          {editEmployeeMode && selectedEmployee && (
            <div className={styles.formModal}>
              <div className={styles.formCard}>
                <h2>Edit Employee: {selectedEmployee.full_name}</h2>
                <form onSubmit={handleSaveEmployee}>
                  <div className={styles.formGroup}>
                    <label>Full Name *</label>
                    <input
                      type="text"
                      value={editEmployeeForm.full_name}
                      onChange={(e) => setEditEmployeeForm({ ...editEmployeeForm, full_name: e.target.value })}
                      required
                      className={styles.input}
                    />
                  </div>
                  <div className={styles.formGroup}>
                    <label>Email</label>
                    <input
                      type="email"
                      value={editEmployeeForm.email}
                      onChange={(e) => setEditEmployeeForm({ ...editEmployeeForm, email: e.target.value })}
                      className={styles.input}
                    />
                  </div>
                  <div className={styles.formGroup}>
                    <label>Phone</label>
                    <input
                      type="tel"
                      value={editEmployeeForm.phone}
                      onChange={(e) => setEditEmployeeForm({ ...editEmployeeForm, phone: e.target.value })}
                      className={styles.input}
                    />
                  </div>
                  <div className={styles.formGroup}>
                    <label>Department</label>
                    <input
                      type="text"
                      value={editEmployeeForm.department}
                      onChange={(e) => setEditEmployeeForm({ ...editEmployeeForm, department: e.target.value })}
                      className={styles.input}
                    />
                  </div>
                  <div className={styles.formGroup}>
                    <label>Position</label>
                    <input
                      type="text"
                      value={editEmployeeForm.position}
                      onChange={(e) => setEditEmployeeForm({ ...editEmployeeForm, position: e.target.value })}
                      className={styles.input}
                    />
                  </div>
                  <div className={styles.formGroup}>
                    <label>Identity Number</label>
                    <input
                      type="text"
                      value={editEmployeeForm.identity_number}
                      onChange={(e) => setEditEmployeeForm({ ...editEmployeeForm, identity_number: e.target.value })}
                      className={styles.input}
                    />
                  </div>
                  <div className={styles.formActions}>
                    <button type="submit" className={styles.submitBtn}>Save</button>
                    <button
                      type="button"
                      onClick={() => {
                        setEditEmployeeMode(false);
                        setSelectedEmployee(null);
                      }}
                      className={styles.cancelButton}
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}

          {/* Overtime Tab */}
          {activeTab === "overtime" && !isLoading && (
            <div className={styles.section}>
              <div className={styles.sectionHeader}>
                <h2 className={styles.sectionTitle}>Pending Overtime Requests</h2>
                <div className={styles.headerActions}>
                  <input
                    type="text"
                    placeholder="Search requests..."
                    value={searchTerms.overtime}
                    onChange={(e) => setSearchTerms({ ...searchTerms, overtime: e.target.value })}
                    className={styles.searchInput}
                  />
                  <button onClick={handleReconcile} className={styles.addBtn}>
                    🔄 Reconcile
                  </button>
                </div>
              </div>

              <div className={styles.itemList}>
                {filteredOvertime.length === 0 ? (
                  <p className={styles.emptyText}>
                    {searchTerms.overtime ? 'No requests found matching your search' : 'No pending overtime requests'}
                  </p>
                ) : (
                  filteredOvertime.map((req) => (
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

