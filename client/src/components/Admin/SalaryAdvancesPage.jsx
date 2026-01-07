import React, { useState, useEffect } from 'react';
import { listSalaryAdvances, createSalaryAdvance, approveSalaryAdvance } from '../../services/api';
import { listEmployees } from '../../services/api';
import LoadingSpinner from '../Common/LoadingSpinner';
import ErrorMessage from '../Common/ErrorMessage';
import styles from './AdminPage.module.css';

const SalaryAdvancesPage = () => {
  const [advances, setAdvances] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    person_id: '',
    amount: '',
    requested_date: new Date().toISOString().split('T')[0],
    deduction_periods: 1,
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [advancesData, employeesData] = await Promise.all([
        listSalaryAdvances(),
        listEmployees({ status: 'active' }),
      ]);
      setAdvances(advancesData);
      setEmployees(employeesData);
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
      await createSalaryAdvance({
        ...formData,
        amount: parseFloat(formData.amount),
        deduction_periods: parseInt(formData.deduction_periods),
      });
      await loadData();
      setShowForm(false);
      setFormData({ person_id: '', amount: '', requested_date: new Date().toISOString().split('T')[0], deduction_periods: 1 });
    } catch (err) {
      setError(err.message);
    }
  };

  const handleApprove = async (id) => {
    if (!window.confirm('Are you sure you want to approve this advance?')) return;
    try {
      await approveSalaryAdvance(id);
      await loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className={styles.pageContainer}>
      <div className={styles.pageHeader}>
        <h1>Salary Advances</h1>
        <button onClick={() => setShowForm(true)} className={styles.addButton}>
          + New Advance
        </button>
      </div>

      {error && <ErrorMessage message={error} />}

      {showForm && (
        <div className={styles.formModal}>
          <div className={styles.formCard}>
            <h2>New Salary Advance</h2>
            <form onSubmit={handleSubmit}>
              <div className={styles.formGroup}>
                <label>Employee *</label>
                <select
                  value={formData.person_id}
                  onChange={(e) => setFormData({ ...formData, person_id: e.target.value })}
                  required
                >
                  <option value="">Select Employee</option>
                  {employees.map((emp) => (
                    <option key={emp.id} value={emp.id}>{emp.full_name}</option>
                  ))}
                </select>
              </div>
              <div className={styles.formGroup}>
                <label>Amount *</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.amount}
                  onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                  required
                />
              </div>
              <div className={styles.formGroup}>
                <label>Requested Date *</label>
                <input
                  type="date"
                  value={formData.requested_date}
                  onChange={(e) => setFormData({ ...formData, requested_date: e.target.value })}
                  required
                />
              </div>
              <div className={styles.formGroup}>
                <label>Deduction Periods *</label>
                <input
                  type="number"
                  min="1"
                  value={formData.deduction_periods}
                  onChange={(e) => setFormData({ ...formData, deduction_periods: e.target.value })}
                  required
                />
              </div>
              <div className={styles.formActions}>
                <button type="submit" className={styles.submitButton}>Create</button>
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
              <th>Employee</th>
              <th>Amount</th>
              <th>Requested Date</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {advances.map((advance) => (
              <tr key={advance.id}>
                <td>{advance.person?.full_name || advance.person_id}</td>
                <td>{advance.amount}</td>
                <td>{advance.requested_date}</td>
                <td>
                  <span className={styles.statusBadge}>{advance.status}</span>
                </td>
                <td>
                  {advance.status === 'pending' && (
                    <button onClick={() => handleApprove(advance.id)} className={styles.approveButton}>
                      Approve
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default SalaryAdvancesPage;



