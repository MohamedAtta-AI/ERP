import React, { useState, useEffect } from 'react';
import { listLoans, createLoan, approveLoan, getLoanRepaymentSchedule } from '../../services/api';
import { listEmployees } from '../../services/api';
import LoadingSpinner from '../Common/LoadingSpinner';
import ErrorMessage from '../Common/ErrorMessage';
import styles from './AdminPage.module.css';

const LoansPage = () => {
  const [loans, setLoans] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [selectedLoan, setSelectedLoan] = useState(null);
  const [schedule, setSchedule] = useState(null);
  const [formData, setFormData] = useState({
    person_id: '',
    principal_amount: '',
    interest_rate: '0',
    loan_date: new Date().toISOString().split('T')[0],
    number_of_installments: 12,
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [loansData, employeesData] = await Promise.all([
        listLoans(),
        listEmployees({ status: 'active' }),
      ]);
      setLoans(loansData);
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
      await createLoan({
        ...formData,
        principal_amount: parseFloat(formData.principal_amount),
        interest_rate: parseFloat(formData.interest_rate),
        number_of_installments: parseInt(formData.number_of_installments),
      });
      await loadData();
      setShowForm(false);
      setFormData({ person_id: '', principal_amount: '', interest_rate: '0', loan_date: new Date().toISOString().split('T')[0], number_of_installments: 12 });
    } catch (err) {
      setError(err.message);
    }
  };

  const handleApprove = async (id) => {
    if (!window.confirm('Are you sure you want to approve this loan?')) return;
    try {
      await approveLoan(id);
      await loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleViewSchedule = async (id) => {
    try {
      const scheduleData = await getLoanRepaymentSchedule(id);
      setSchedule(scheduleData);
      setSelectedLoan(id);
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className={styles.pageContainer}>
      <div className={styles.pageHeader}>
        <h1>Loans Management</h1>
        <button onClick={() => setShowForm(true)} className={styles.addButton}>
          + New Loan
        </button>
      </div>

      {error && <ErrorMessage message={error} />}

      {showForm && (
        <div className={styles.formModal}>
          <div className={styles.formCard}>
            <h2>New Loan</h2>
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
                <label>Principal Amount *</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.principal_amount}
                  onChange={(e) => setFormData({ ...formData, principal_amount: e.target.value })}
                  required
                />
              </div>
              <div className={styles.formGroup}>
                <label>Interest Rate (%)</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.interest_rate}
                  onChange={(e) => setFormData({ ...formData, interest_rate: e.target.value })}
                />
              </div>
              <div className={styles.formGroup}>
                <label>Loan Date *</label>
                <input
                  type="date"
                  value={formData.loan_date}
                  onChange={(e) => setFormData({ ...formData, loan_date: e.target.value })}
                  required
                />
              </div>
              <div className={styles.formGroup}>
                <label>Number of Installments *</label>
                <input
                  type="number"
                  min="1"
                  value={formData.number_of_installments}
                  onChange={(e) => setFormData({ ...formData, number_of_installments: e.target.value })}
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
              <th>Principal</th>
              <th>Interest Rate</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loans.map((loan) => (
              <tr key={loan.id}>
                <td>{loan.person?.full_name || loan.person_id}</td>
                <td>{loan.principal_amount}</td>
                <td>{loan.interest_rate}%</td>
                <td>
                  <span className={styles.statusBadge}>{loan.status}</span>
                </td>
                <td>
                  {loan.status === 'pending' && (
                    <button onClick={() => handleApprove(loan.id)} className={styles.approveButton}>
                      Approve
                    </button>
                  )}
                  <button onClick={() => handleViewSchedule(loan.id)} className={styles.viewButton}>
                    Schedule
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {schedule && selectedLoan && (
        <div className={styles.formModal}>
          <div className={styles.formCard}>
            <h2>Repayment Schedule</h2>
            <div className={styles.tableContainer}>
              <table className={styles.dataTable}>
                <thead>
                  <tr>
                    <th>Installment</th>
                    <th>Due Date</th>
                    <th>Amount</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {schedule.installments?.map((inst, idx) => (
                    <tr key={idx}>
                      <td>{idx + 1}</td>
                      <td>{inst.due_date}</td>
                      <td>{inst.amount}</td>
                      <td>{inst.status || 'pending'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <button onClick={() => { setSchedule(null); setSelectedLoan(null); }} className={styles.cancelButton}>
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default LoansPage;

