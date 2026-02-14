import React from "react";
import { useNavigate } from "react-router-dom";
import styles from "./ModuleHeader.module.css";

const ModuleHeader = ({ title, className = "" }) => {
  const navigate = useNavigate();

  return (
    <div className={`${styles.header} ${className}`.trim()}>
      <button
        type="button"
        className={styles.backButton}
        onClick={() => navigate("/dashboard")}
      >
        <svg
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          aria-hidden="true"
        >
          <path d="M19 12H5M12 19l-7-7 7-7" />
        </svg>
        Back to Dashboard
      </button>
      {title ? <h1 className={styles.title}>{title}</h1> : <div className={styles.spacer} />}
      <div className={styles.spacer} />
    </div>
  );
};

export default ModuleHeader;
