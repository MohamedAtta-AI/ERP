import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { listOvertimeRequests, approveOvertime, rejectOvertime, createOvertimeRequest } from '../../services/api';
import { listEmployees } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import LoadingSpinner from '../Common/LoadingSpinner';
import ErrorMessage from '../Common/ErrorMessage';
import styles from './SupervisorPage.module.css';

const OvertimeManagementPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [requests, setRequests] = useState([]);
  const [filteredRequests, setFilteredRequests] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [workers, setWorkers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    person_id: '',
    overtime_date: new Date().toISOString().split('T')[0],
    hours: '',
    notes: '',
  });

  useEffect(() => {
    loadData();
  }, []);

  // Filter requests based on search term
  useEffect(() => {
    if (!searchTerm.trim()) {
      setFilteredRequests(requests);
    } else {
      const filtered = requests.filter(req =>
        req.person_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        req.person_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        req.overtime_date?.includes(searchTerm)
      );
      setFilteredRequests(filtered);
    }
  }, [searchTerm, requests]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [requestsData, workersData] = await Promise.all([
        listOvertimeRequests({ status: 'pending' }),
        listEmployees({ supervisor_id: user.id, status: 'active' }),
      ]);
      setRequests(requestsData);
      setWorkers(workersData);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      await createOvertimeRequest({
        person_id: formData.person_id,
        overtime_date: formData.overtime_date,
        hours: parseFloat(formData.hours),
        notes: formData.notes || null,
      });
      setSuccess('Overtime request created successfully!');
      setShowForm(false);
      setFormData({ person_id: '', overtime_date: new Date().toISOString().split('T')[0], hours: '', notes: '' });
      await loadData();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (id) => {
    try {
      setLoading(true);
      await approveOvertime(id);
      setSuccess('Overtime request approved!');
      await loadData();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async (id) => {
    const reason = window.prompt('Rejection reason:');
    if (!reason) return;
    try {
      setLoading(true);
      await rejectOvertime(id, reason);
      setSuccess('Overtime request rejected');
      await loadData();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading && requests.length === 0) return <LoadingSpinner />;

  return (
    <div className={styles.pageContainer}>
      <div className={styles.pageHeader}>
        <div className={styles.headerLeft}>
          <button onClick={() => navigate('/dashboard')} className={styles.backButton}>
            ← Back to Dashboard
          </button>
          <h1>Overtime Management</h1>
        </div>
        <div className={styles.headerRight}>
          <input
            type="text"
            placeholder="Search requests..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className={styles.searchInput}
          />
          <button onClick={() => setShowForm(true)} className={styles.addButton}>
            + New Request
          </button>
        </div>
      </div>

      {error && <ErrorMessage message={error} onDismiss={() => setError(null)} />}
      {success && <div className={styles.successMessage}>{success}</div>}

      {showForm && (
        <div className={styles.formModal}>
          <div className={styles.formCard}>
            <h2>New Overtime Request</h2>
            <form onSubmit={handleSubmit}>
              <div className={styles.formGroup}>
                <label>Worker *</label>
                <select
                  value={formData.person_id}
                  onChange={(e) => setFormData({ ...formData, person_id: e.target.value })}
                  required
                >
                  <option value="">Select Worker</option>
                  {workers.map((worker) => (
                    <option key={worker.id} value={worker.id}>{worker.full_name}</option>
                  ))}
                </select>
              </div>
              <div className={styles.formGroup}>
                <label>Date *</label>
                <input
                  type="date"
                  value={formData.overtime_date}
                  onChange={(e) => setFormData({ ...formData, overtime_date: e.target.value })}
                  required
                />
              </div>
              <div className={styles.formGroup}>
                <label>Hours *</label>
                <input
                  type="number"
                  step="0.5"
                  min="0.5"
                  value={formData.hours}
                  onChange={(e) => setFormData({ ...formData, hours: e.target.value })}
                  required
                />
              </div>
              <div className={styles.formGroup}>
                <label>Notes</label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  rows={3}
                  placeholder="Optional reason or notes"
                />
              </div>
              <div className={styles.formActions}>
                <button type="submit" className={styles.submitButton}>Submit</button>
                <button type="button" onClick={() => setShowForm(false)} className={styles.cancelButton}>
                  Cancel
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
              <th>Worker</th>
              <th>Date</th>
              <th>Hours</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredRequests.length === 0 ? (
              <tr>
                <td colSpan="5" style={{ textAlign: 'center', padding: '2rem' }}>
                  {searchTerm ? 'No requests found matching your search' : 'No overtime requests found'}
                </td>
              </tr>
            ) : (
              filteredRequests.map((request) => (
                <tr key={request.id}>
                  <td>{request.person_name || request.person_id}</td>
                  <td>{request.overtime_date || request.date}</td>
                  <td>{request.hours}</td>
                  <td>
                    <span className={styles.statusBadge}>{request.status}</span>
                  </td>
                  <td>
                    {request.status === 'pending' && (
                      <>
                        <button onClick={() => handleApprove(request.id)} className={styles.approveButton} disabled={loading}>
                          Approve
                        </button>
                        <button onClick={() => handleReject(request.id)} className={styles.rejectButton} disabled={loading}>
                          Reject
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default OvertimeManagementPage;

