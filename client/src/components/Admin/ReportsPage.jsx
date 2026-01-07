import React, { useState } from 'react';
import { generateAttendanceReport, generatePayrollReport } from '../../services/api';
import LoadingSpinner from '../Common/LoadingSpinner';
import ErrorMessage from '../Common/ErrorMessage';
import styles from './AdminPage.module.css';

const ReportsPage = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [attendanceParams, setAttendanceParams] = useState({
    start_date: '',
    end_date: '',
    location_id: '',
    format: 'pdf',
  });
  const [payrollParams, setPayrollParams] = useState({
    period_id: '',
    location_id: '',
    format: 'pdf',
  });

  const handleAttendanceReport = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      const result = await generateAttendanceReport(attendanceParams);
      // In a real app, this would download the file
      alert(`Report generated: ${JSON.stringify(result)}`);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePayrollReport = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      const result = await generatePayrollReport(payrollParams);
      // In a real app, this would download the file
      alert(`Report generated: ${JSON.stringify(result)}`);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.pageContainer}>
      <div className={styles.pageHeader}>
        <h1>Reports</h1>
      </div>

      {error && <ErrorMessage message={error} />}
      {loading && <LoadingSpinner />}

      <div className={styles.section}>
        <h2>Attendance Report</h2>
        <form onSubmit={handleAttendanceReport} className={styles.form}>
          <div className={styles.formGroup}>
            <label>Start Date *</label>
            <input
              type="date"
              value={attendanceParams.start_date}
              onChange={(e) => setAttendanceParams({ ...attendanceParams, start_date: e.target.value })}
              required
            />
          </div>
          <div className={styles.formGroup}>
            <label>End Date *</label>
            <input
              type="date"
              value={attendanceParams.end_date}
              onChange={(e) => setAttendanceParams({ ...attendanceParams, end_date: e.target.value })}
              required
            />
          </div>
          <div className={styles.formGroup}>
            <label>Format</label>
            <select
              value={attendanceParams.format}
              onChange={(e) => setAttendanceParams({ ...attendanceParams, format: e.target.value })}
            >
              <option value="pdf">PDF</option>
              <option value="excel">Excel</option>
            </select>
          </div>
          <button type="submit" className={styles.submitButton}>Generate Report</button>
        </form>
      </div>

      <div className={styles.section}>
        <h2>Payroll Report</h2>
        <form onSubmit={handlePayrollReport} className={styles.form}>
          <div className={styles.formGroup}>
            <label>Period ID *</label>
            <input
              type="text"
              value={payrollParams.period_id}
              onChange={(e) => setPayrollParams({ ...payrollParams, period_id: e.target.value })}
              required
            />
          </div>
          <div className={styles.formGroup}>
            <label>Format</label>
            <select
              value={payrollParams.format}
              onChange={(e) => setPayrollParams({ ...payrollParams, format: e.target.value })}
            >
              <option value="pdf">PDF</option>
              <option value="excel">Excel</option>
            </select>
          </div>
          <button type="submit" className={styles.submitButton}>Generate Report</button>
        </form>
      </div>
    </div>
  );
};

export default ReportsPage;



