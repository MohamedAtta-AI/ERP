import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import PersonRegistrationWizard from "./PersonRegistrationWizard";
import FaceCapture from "../FaceCapture/FaceCapture";
import { enrollFace } from "../../services/api";
import ErrorMessage from "../Common/ErrorMessage";
import styles from "./RegistrationPage.module.css";

/**
 * Registration Page
 * 
 * Full registration flow with multi-stage form and face enrollment.
 * Accessible from dashboard by admin only.
 */
const RegistrationPage = () => {
  const [mode, setMode] = useState("form"); // form, enroll, success
  const [employeeId, setEmployeeId] = useState(null);
  const [employeeName, setEmployeeName] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleRegistrationSuccess = (data) => {
    setEmployeeId(data.employee_id);
    setEmployeeName(data.full_name || "");
    setMode("enroll");
  };

  // Handle multi-angle face capture (for registration)
  const handleMultiFaceCapture = async (imageFiles) => {
    if (!employeeId) {
      setError("Employee ID is required");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Enroll each face angle
      let enrolledCount = 0;
      for (const file of imageFiles) {
        await enrollFace(employeeId, file);
        enrolledCount++;
      }
      console.log(`Enrolled ${enrolledCount} face angles for ${employeeId}`);
      setMode("success");
    } catch (err) {
      setError(err.message || "Face enrollment failed. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  // Handle single face capture (fallback)
  const handleFaceCapture = async (imageFile) => {
    if (!employeeId) {
      setError("Employee ID is required");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      await enrollFace(employeeId, imageFile);
      setMode("success");
    } catch (err) {
      setError(err.message || "Face enrollment failed. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDone = () => {
    navigate('/dashboard');
  };

  const handleRegisterAnother = () => {
    setMode("form");
    setEmployeeId(null);
    setError(null);
    setIsLoading(false);
  };

  return (
    <div className={styles.page}>
      {/* Header */}
      <div className={styles.header}>
        <Link to="/dashboard" className={styles.backButton}>
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

      {/* Form Mode */}
      {mode === "form" && (
        <PersonRegistrationWizard onSuccess={handleRegistrationSuccess} />
      )}

      {/* Enrollment Mode */}
      {mode === "enroll" && (
        <div className={styles.container}>
          <h2 className={styles.title}>Face Enrollment</h2>
          <div className={styles.employeeIdBadge}>
            Employee ID: <strong>{employeeId}</strong>
          </div>
          <p className={styles.instructions}>
            We'll capture your face from 3 angles (front, left, right) for
            better recognition accuracy.
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
              onMultiCapture={handleMultiFaceCapture}
              onCancel={() => setMode("form")}
              mode="registration"
            />
          )}
        </div>
      )}

      {/* Success Mode */}
      {mode === "success" && (
        <div className={styles.container}>
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
            <h2 className={styles.successTitle}>Registration Complete!</h2>
            <div className={styles.successInfo}>
              <p>
                Employee <strong>{employeeId}</strong> has been successfully
                registered with face recognition.
              </p>
              <p className={styles.successNote}>
                They can now use face recognition for attendance check-in.
              </p>
            </div>
            <div className={styles.buttonGroup}>
              <button
                className={styles.secondaryButton}
                onClick={handleRegisterAnother}
              >
                Register Another
              </button>
              <button
                className={styles.primaryButton}
                onClick={handleDone}
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RegistrationPage;

