import React from "react";
import { useNavigate } from "react-router-dom";
import AttendanceCheck from "./AttendanceCheck";
import styles from "./AttendancePage.module.css";

/**
 * Attendance Page
 * 
 * Simple page that goes directly to attendance check-in.
 * Registration is handled separately from the dashboard.
 */
const AttendancePage = () => {
  const navigate = useNavigate();
  
  // Go directly to attendance mode - no menu needed since registration is separate
  return (
    <div className={styles.page}>
      <AttendanceCheck onBack={() => navigate('/dashboard')} />
    </div>
  );
};

export default AttendancePage;
