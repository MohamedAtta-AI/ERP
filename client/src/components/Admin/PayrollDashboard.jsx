import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { listPayrollPeriods, createPayrollPeriod, listPayrollRuns, createPayrollRun, getPayrollRun, previewPayrollRun, approvePayrollRun, lockPayrollRun } from '../../services/api';
import LoadingSpinner from '../Common/LoadingSpinner';
import ErrorMessage from '../Common/ErrorMessage';
import styles from './AdminPage.module.css';

const PayrollDashboard = () => {
  const navigate = useNavigate();
  const [periods, setPeriods] = useState([]);
  const [filteredPeriods, setFilteredPeriods] = useState([]);
  const [runs, setRuns] = useState([]);
  const [filteredRuns, setFilteredRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [showPeriodForm, setShowPeriodForm] = useState(false);
  const [selectedPeriod, setSelectedPeriod] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [periodFormData, setPeriodFormData] = useState({
    start_date: '',
    end_date: '',
    period_type: 'monthly',
  });

  useEffect(() => {
    loadData();
  }, []);

  // Filter periods and runs based on search
  useEffect(() => {
    if (!searchTerm.trim()) {
      setFilteredPeriods(periods);
      setFilteredRuns(runs);
    } else {
      setFilteredPeriods(periods.filter(p =>
        p.start_date?.includes(searchTerm) ||
        p.end_date?.includes(searchTerm) ||
        p.period_type?.toLowerCase().includes(searchTerm.toLowerCase())
      ));
      setFilteredRuns(runs.filter(r =>
        r.period_id?.toString().includes(searchTerm) ||
        r.status?.toLowerCase().includes(searchTerm.toLowerCase())
      ));
    }
  }, [searchTerm, periods, runs]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [periodsData, runsData] = await Promise.all([
        listPayrollPeriods(),
        listPayrollRuns(),
      ]);
      setPeriods(periodsData);
      setFilteredPeriods(periodsData);
      setRuns(runsData);
      setFilteredRuns(runsData);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePeriod = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      await createPayrollPeriod(periodFormData);
      setSuccess('Payroll period created successfully!');
      await loadData();
      setShowPeriodForm(false);
      setPeriodFormData({ start_date: '', end_date: '', period_type: 'monthly' });
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateRun = async (periodId) => {
    try {
      setLoading(true);
      await createPayrollRun(periodId);
      setSuccess('Payroll run created successfully!');
      await loadData();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePreview = async (runId) => {
    try {
      const preview = await previewPayrollRun(runId);
      alert(`Preview: ${JSON.stringify(preview, null, 2)}`);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleApprove = async (runId) => {
    if (!window.confirm('Are you sure you want to approve this payroll run?')) return;
    try {
      await approvePayrollRun(runId);
      await loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleLock = async (runId) => {
    if (!window.confirm('Are you sure you want to lock this payroll run?')) return;
    try {
      await lockPayrollRun(runId);
      await loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading && periods.length === 0 && runs.length === 0) return <LoadingSpinner />;

  return (
    <div className={styles.pageContainer}>
      <div className={styles.pageHeader}>
        <div className={styles.headerLeft}>
          <button onClick={() => navigate('/dashboard')} className={styles.backButton}>
            ← Back to Dashboard
          </button>
          <h1>Payroll Dashboard</h1>
        </div>
        <div className={styles.headerRight}>
          <input
            type="text"
            placeholder="Search periods/runs..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className={styles.searchInput}
          />
          <button onClick={() => setShowPeriodForm(true)} className={styles.addButton}>
            + Create Period
          </button>
        </div>
      </div>

      {error && <ErrorMessage message={error} onDismiss={() => setError(null)} />}
      {success && <div className={styles.successMessage}>{success}</div>}

      {showPeriodForm && (
        <div className={styles.formModal}>
          <div className={styles.formCard}>
            <h2>Create Payroll Period</h2>
            <form onSubmit={handleCreatePeriod}>
              <div className={styles.formGroup}>
                <label>Start Date *</label>
                <input
                  type="date"
                  value={periodFormData.start_date}
                  onChange={(e) => setPeriodFormData({ ...periodFormData, start_date: e.target.value })}
                  required
                />
              </div>
              <div className={styles.formGroup}>
                <label>End Date *</label>
                <input
                  type="date"
                  value={periodFormData.end_date}
                  onChange={(e) => setPeriodFormData({ ...periodFormData, end_date: e.target.value })}
                  required
                />
              </div>
              <div className={styles.formGroup}>
                <label>Period Type *</label>
                <select
                  value={periodFormData.period_type}
                  onChange={(e) => setPeriodFormData({ ...periodFormData, period_type: e.target.value })}
                  required
                >
                  <option value="monthly">Monthly</option>
                  <option value="weekly">Weekly</option>
                  <option value="biweekly">Biweekly</option>
                </select>
              </div>
              <div className={styles.formActions}>
                <button type="submit" className={styles.submitButton}>Create</button>
                <button type="button" onClick={() => setShowPeriodForm(false)} className={styles.cancelButton}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className={styles.section}>
        <h2>Payroll Periods</h2>
        <div className={styles.tableContainer}>
          <table className={styles.dataTable}>
            <thead>
              <tr>
                <th>Start Date</th>
                <th>End Date</th>
                <th>Type</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredPeriods.length === 0 ? (
                <tr>
                  <td colSpan="5" style={{ textAlign: 'center', padding: '2rem' }}>
                    {searchTerm ? 'No periods found matching your search' : 'No payroll periods configured'}
                  </td>
                </tr>
              ) : (
                filteredPeriods.map((period) => (
                  <tr key={period.id}>
                    <td>{period.start_date}</td>
                    <td>{period.end_date}</td>
                    <td>{period.period_type}</td>
                    <td>
                      <span className={styles.statusBadge}>{period.status}</span>
                    </td>
                    <td>
                      <button onClick={() => handleCreateRun(period.id)} className={styles.actionButton}>
                        Create Run
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className={styles.section}>
        <h2>Payroll Runs</h2>
        <div className={styles.tableContainer}>
          <table className={styles.dataTable}>
            <thead>
              <tr>
                <th>Period</th>
                <th>Status</th>
                <th>Total Amount</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredRuns.length === 0 ? (
                <tr>
                  <td colSpan="4" style={{ textAlign: 'center', padding: '2rem' }}>
                    {searchTerm ? 'No runs found matching your search' : 'No payroll runs found'}
                  </td>
                </tr>
              ) : (
                filteredRuns.map((run) => (
                  <tr key={run.id}>
                    <td>{run.period_id}</td>
                    <td>
                      <span className={styles.statusBadge}>{run.status}</span>
                    </td>
                    <td>{run.total_amount || '-'}</td>
                    <td>
                      <button onClick={() => handlePreview(run.id)} className={styles.viewButton}>Preview</button>
                      {run.status === 'draft' && (
                        <>
                          <button onClick={() => handleApprove(run.id)} className={styles.approveButton}>Approve</button>
                          <button onClick={() => handleLock(run.id)} className={styles.lockButton}>Lock</button>
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
    </div>
  );
};

export default PayrollDashboard;

