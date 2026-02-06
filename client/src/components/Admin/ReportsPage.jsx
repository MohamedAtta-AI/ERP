import React from 'react';
import ErrorMessage from '../Common/ErrorMessage';
import styles from './AdminPage.module.css';

const ReportsPage = () => {
  const handleAttendanceReport = async (e) => {
    e.preventDefault();
    alert("Reports functionality is not yet implemented in the backend.");
  };


  return (
    <div className={styles.pageContainer}>
      <div className={styles.pageHeader}>
        <h1>Reports</h1>
      </div>

      <div className={styles.section}>
        <h2>Attendance Report</h2>
        <p className={styles.helpText} style={{ color: '#6b7280', fontStyle: 'italic', marginBottom: '1rem' }}>
          Reports functionality is not yet implemented in the backend.
        </p>
        <form onSubmit={handleAttendanceReport} className={styles.form}>
          <div className={styles.formGroup}>
            <label>Start Date *</label>
            <input
              type="date"
              disabled
              style={{ opacity: 0.6, cursor: 'not-allowed' }}
            />
          </div>
          <div className={styles.formGroup}>
            <label>End Date *</label>
            <input
              type="date"
              disabled
              style={{ opacity: 0.6, cursor: 'not-allowed' }}
            />
          </div>
          <div className={styles.formGroup}>
            <label>Format</label>
            <select disabled style={{ opacity: 0.6, cursor: 'not-allowed' }}>
              <option value="pdf">PDF</option>
              <option value="excel">Excel</option>
            </select>
          </div>
          <button type="submit" className={styles.submitButton} disabled style={{ opacity: 0.6, cursor: 'not-allowed' }}>
            Generate Report
          </button>
        </form>
      </div>

    </div>
  );
};

export default ReportsPage;







