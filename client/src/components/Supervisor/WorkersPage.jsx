import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { listEmployees, getAttendanceHistory, updateEmployee, getEmployee, checkIn, checkOut } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import LoadingSpinner from '../Common/LoadingSpinner';
import ErrorMessage from '../Common/ErrorMessage';
import styles from './SupervisorPage.module.css';

const WorkersPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [workers, setWorkers] = useState([]);
  const [filteredWorkers, setFilteredWorkers] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [selectedWorker, setSelectedWorker] = useState(null);
  const [attendance, setAttendance] = useState([]);
  const [editMode, setEditMode] = useState(false);
  const [editingWorker, setEditingWorker] = useState(null);
  const [editForm, setEditForm] = useState({});

  useEffect(() => {
    loadWorkers();
  }, []);

  // Filter workers based on search term
  useEffect(() => {
    if (!searchTerm.trim()) {
      setFilteredWorkers(workers);
    } else {
      const filtered = workers.filter(worker =>
        worker.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (worker.person_id || worker.id)?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        worker.email?.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredWorkers(filtered);
    }
  }, [searchTerm, workers]);

  const loadWorkers = async () => {
    try {
      setLoading(true);
      // Supervisors can only see workers under them
      const data = await listEmployees({ supervisor_id: user.id, status: 'active' });
      setWorkers(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleViewAttendance = async (workerId) => {
    try {
      const today = new Date().toISOString().split('T')[0];
      const data = await getAttendanceHistory({ person_id: workerId, start_date: today, end_date: today });
      setAttendance(data);
      setSelectedWorker(workerId);
      setEditMode(false);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleEditWorker = async (worker) => {
    try {
      // Get full worker details
      const details = await getEmployee(worker.person_id || worker.id);
      setEditingWorker(details);
      setEditForm({
        full_name: details.full_name || '',
        phone: details.phone || '',
        email: details.email || '',
        department: details.department || '',
        position: details.position || '',
        identity_number: details.identity_number || '',
      });
      setEditMode(true);
      setSelectedWorker(null);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleEditChange = (e) => {
    const { name, value } = e.target;
    setEditForm(prev => ({ ...prev, [name]: value }));
  };

  const handleSaveWorker = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      await updateEmployee(editingWorker.person_id || editingWorker.id, editForm);
      setSuccess('Worker updated successfully!');
      setEditMode(false);
      setEditingWorker(null);
      loadWorkers(); // Refresh list
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelEdit = () => {
    setEditMode(false);
    setEditingWorker(null);
    setEditForm({});
  };

  const handleManualCheckIn = async (workerId) => {
    try {
      setLoading(true);
      await checkIn(workerId);
      setSuccess('Check-in recorded successfully!');
      await handleViewAttendance(workerId);
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleManualCheckOut = async (workerId) => {
    try {
      setLoading(true);
      await checkOut(workerId);
      setSuccess('Check-out recorded successfully!');
      await handleViewAttendance(workerId);
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !editMode && !selectedWorker) return <LoadingSpinner />;

  return (
    <div className={styles.pageContainer}>
      <div className={styles.pageHeader}>
        <div className={styles.headerLeft}>
          <button onClick={() => navigate('/dashboard')} className={styles.backButton}>
            ← Back to Dashboard
          </button>
          <h1>My Workers</h1>
        </div>
        <div className={styles.headerRight}>
          <input
            type="text"
            placeholder="Search workers..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className={styles.searchInput}
          />
        </div>
      </div>

      {error && <ErrorMessage message={error} onDismiss={() => setError(null)} />}
      {success && <div className={styles.successMessage}>{success}</div>}

      {/* Edit Worker Modal */}
      {editMode && editingWorker && (
        <div className={styles.modalOverlay}>
          <div className={styles.modal}>
            <h2>Edit Worker Details</h2>
            <form onSubmit={handleSaveWorker} className={styles.editForm}>
              <div className={styles.formGroup}>
                <label>Full Name</label>
                <input
                  type="text"
                  name="full_name"
                  value={editForm.full_name}
                  onChange={handleEditChange}
                  className={styles.formInput}
                  required
                />
              </div>
              <div className={styles.formGroup}>
                <label>Phone</label>
                <input
                  type="tel"
                  name="phone"
                  value={editForm.phone}
                  onChange={handleEditChange}
                  className={styles.formInput}
                />
              </div>
              <div className={styles.formGroup}>
                <label>Email</label>
                <input
                  type="email"
                  name="email"
                  value={editForm.email}
                  onChange={handleEditChange}
                  className={styles.formInput}
                />
              </div>
              <div className={styles.formGroup}>
                <label>Department</label>
                <input
                  type="text"
                  name="department"
                  value={editForm.department}
                  onChange={handleEditChange}
                  className={styles.formInput}
                />
              </div>
              <div className={styles.formGroup}>
                <label>Position</label>
                <input
                  type="text"
                  name="position"
                  value={editForm.position}
                  onChange={handleEditChange}
                  className={styles.formInput}
                />
              </div>
              <div className={styles.formGroup}>
                <label>Identity Number</label>
                <input
                  type="text"
                  name="identity_number"
                  value={editForm.identity_number}
                  onChange={handleEditChange}
                  className={styles.formInput}
                />
              </div>
              <div className={styles.formActions}>
                <button type="button" onClick={handleCancelEdit} className={styles.cancelButton}>
                  Cancel
                </button>
                <button type="submit" className={styles.saveButton} disabled={loading}>
                  {loading ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className={styles.tableContainer}>
        <table className={styles.dataTable}>
          <thead>
            <tr>
              <th>ID</th>
              <th>Full Name</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredWorkers.length === 0 ? (
              <tr>
                <td colSpan="4" style={{ textAlign: 'center', padding: '2rem' }}>
                  {searchTerm ? 'No workers found matching your search' : 'No workers found'}
                </td>
              </tr>
            ) : (
              filteredWorkers.map((worker) => (
                <tr key={worker.id || worker.person_id}>
                  <td>{worker.person_id || worker.id}</td>
                  <td>{worker.full_name}</td>
                  <td>
                    <span className={worker.status === 'active' ? styles.activeBadge : styles.inactiveBadge}>
                      {worker.status || 'active'}
                    </span>
                  </td>
                  <td className={styles.actionButtons}>
                    <button onClick={() => handleEditWorker(worker)} className={styles.editButton}>
                      Edit
                    </button>
                    <button onClick={() => handleViewAttendance(worker.person_id || worker.id)} className={styles.viewButton}>
                      View Attendance
                    </button>
                    <button onClick={() => handleManualCheckIn(worker.person_id || worker.id)} className={styles.checkInButton}>
                      Check In
                    </button>
                    <button onClick={() => handleManualCheckOut(worker.person_id || worker.id)} className={styles.checkOutButton}>
                      Check Out
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {selectedWorker && (
        <div className={styles.section}>
          <div className={styles.sectionHeader}>
            <h2>Attendance History</h2>
            <button onClick={() => setSelectedWorker(null)} className={styles.closeButton}>
              Close
            </button>
          </div>
          {attendance.length === 0 ? (
            <p className={styles.emptyText}>No attendance records found</p>
          ) : (
          <div className={styles.tableContainer}>
            <table className={styles.dataTable}>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Check In</th>
                  <th>Check Out</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {attendance.map((att) => (
                  <tr key={att.id}>
                    <td>{att.attendance_date}</td>
                    <td>{att.check_in || '-'}</td>
                    <td>{att.check_out || '-'}</td>
                    <td>{att.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          )}
        </div>
      )}
    </div>
  );
};

export default WorkersPage;

