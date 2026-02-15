import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import AttendanceCheck from "./AttendanceCheck";
import AttendanceReports from "./AttendanceReports";
import ModuleHeader from "../Common/ModuleHeader";
import styles from "./AttendancePage.module.css";

/**
 * Attendance Page
 * 
 * Simple page that goes directly to attendance check-in.
 * Registration is handled separately from the dashboard.
 */
const AttendancePage = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("capture");
  
  return (
    <div className={styles.page}>
      <ModuleHeader title="Take Attendance" className={styles.header} />
      <div className={styles.tabs}>
        <button
          type="button"
          className={`${styles.tab} ${activeTab === "capture" ? styles.tabActive : ""}`}
          onClick={() => setActiveTab("capture")}
        >
          Live Capture
        </button>
        <button
          type="button"
          className={`${styles.tab} ${activeTab === "reports" ? styles.tabActive : ""}`}
          onClick={() => setActiveTab("reports")}
        >
          Attendance Reports
        </button>
      </div>

      {activeTab === "capture" ? (
        <AttendanceCheck onBack={() => navigate("/dashboard")} />
      ) : (
        <AttendanceReports />
      )}
    </div>
  );
};

export default AttendancePage;
