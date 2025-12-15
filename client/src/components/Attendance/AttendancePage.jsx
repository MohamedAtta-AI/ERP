import React, { useState } from "react";
import { Link } from "react-router-dom";
import RegistrationForm from "../Registration/RegistrationForm";
import FaceCapture from "../FaceCapture/FaceCapture";
import AttendanceCheck from "./AttendanceCheck";
import { enrollFace } from "../../services/api";
import ErrorMessage from "../Common/ErrorMessage";
import styles from "./AttendancePage.module.css";

const AttendancePage = () => {
  const [mode, setMode] = useState("menu"); // menu, register, enroll, attendance
  const [employeeId, setEmployeeId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const handleRegistrationSuccess = (data) => {
    setEmployeeId(data.employee_id);
    setMode("enroll");
  };

  const handleFaceCapture = async (imageFile) => {
    if (!employeeId) {
      setError("Employee ID is required");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      await enrollFace(employeeId, imageFile);
      setSuccess(true);
    } catch (err) {
      setError(err.message || "Face enrollment failed. Please try again.");
      setIsLoading(false);
    }
  };

  const handleEnrollmentComplete = () => {
    setMode("menu");
    setEmployeeId(null);
    setSuccess(false);
    setIsLoading(false);
  };

  const handleBack = () => {
    setMode("menu");
    setEmployeeId(null);
    setError(null);
    setSuccess(false);
    setIsLoading(false);
  };

  if (mode === "register") {
    return (
      <div className={styles.page}>
        <div className={styles.header}>
          <button onClick={handleBack} className={styles.backButton}>
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M19 12H5M12 19l-7-7 7-7" />
            </svg>
            Back
          </button>
        </div>
        <RegistrationForm onSuccess={handleRegistrationSuccess} />
      </div>
    );
  }

  if (mode === "enroll") {
    return (
      <div className={styles.page}>
        <div className={styles.header}>
          <button
            onClick={() => setMode("register")}
            className={styles.backButton}
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M19 12H5M12 19l-7-7 7-7" />
            </svg>
            Back
          </button>
        </div>
        <div className={styles.container}>
          {success ? (
            <div className={styles.successContainer}>
              <div className={styles.successIcon}>
                <svg
                  width="64"
                  height="64"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                  <polyline points="22 4 12 14.01 9 11.01"></polyline>
                </svg>
              </div>
              <h2 className={styles.successTitle}>Enrollment Complete!</h2>
              <div className={styles.successInfo}>
                <p>
                  Employee <strong>{employeeId}</strong> has been successfully
                  registered with face recognition.
                </p>
                <p className={styles.successNote}>
                  You can now use your face for attendance check-in.
                </p>
              </div>
              <button
                className={styles.doneButton}
                onClick={handleEnrollmentComplete}
              >
                Done
              </button>
            </div>
          ) : (
            <>
              <h2 className={styles.title}>Face Enrollment</h2>
              <div className={styles.employeeIdBadge}>
                Employee ID: <strong>{employeeId}</strong>
              </div>
              <p className={styles.instructions}>
                Position your face in the circle. Ensure good lighting and look
                directly at the camera.
              </p>

              {error && (
                <div className={styles.errorWrapper}>
                  <ErrorMessage
                    message={error}
                    onDismiss={() => setError(null)}
                  />
                </div>
              )}

              {isLoading ? (
                <div className={styles.loadingContainer}>
                  <div className={styles.spinner}></div>
                  <p>Enrolling your face...</p>
                </div>
              ) : (
                <FaceCapture
                  employeeId={employeeId}
                  onCapture={handleFaceCapture}
                  onCancel={() => setMode("register")}
                  requiresLiveness={true}
                  mode="registration"
                />
              )}
            </>
          )}
        </div>
      </div>
    );
  }

  if (mode === "attendance") {
    return (
      <div className={styles.page}>
        <div className={styles.header}>
          <button onClick={handleBack} className={styles.backButton}>
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M19 12H5M12 19l-7-7 7-7" />
            </svg>
            Back
          </button>
        </div>
        <AttendanceCheck onBack={handleBack} />
      </div>
    );
  }

  // Menu mode - no camera active here
  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <Link to="/" className={styles.backButton}>
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
          Back to Dashboard
        </Link>
      </div>
      <div className={styles.menuContainer}>
        <h1 className={styles.menuTitle}>Attendance Management</h1>
        <p className={styles.menuSubtitle}>Choose an option to get started</p>

        <div className={styles.menuGrid}>
          <div className={styles.menuCard} onClick={() => setMode("register")}>
            <div className={styles.menuIcon} style={{ color: "#10b981" }}>
              <svg
                width="48"
                height="48"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                <circle cx="8.5" cy="7" r="4"></circle>
                <path d="M20 8v6"></path>
                <path d="M23 11h-6"></path>
              </svg>
            </div>
            <h3 className={styles.menuCardTitle}>New Registration</h3>
            <p className={styles.menuCardDescription}>
              Register a new employee and enroll their face for attendance
            </p>
          </div>

          <div
            className={styles.menuCard}
            onClick={() => setMode("attendance")}
          >
            <div className={styles.menuIcon} style={{ color: "#1e40af" }}>
              <svg
                width="48"
                height="48"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <circle cx="12" cy="12" r="10"></circle>
                <polyline points="12 6 12 12 16 14"></polyline>
              </svg>
            </div>
            <h3 className={styles.menuCardTitle}>Check In / Out</h3>
            <p className={styles.menuCardDescription}>
              Verify your identity with face recognition and record attendance
            </p>
            <p className={styles.menuCardNote}>(Must be registered first)</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AttendancePage;
