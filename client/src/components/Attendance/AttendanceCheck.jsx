import React, { useState } from "react";
import FaceCapture from "../FaceCapture/FaceCapture";
import { verifyAttendance, checkIn } from "../../services/api";
import Button from "../Common/Button";
import ErrorMessage from "../Common/ErrorMessage";
import styles from "./AttendanceCheck.module.css";

const AttendanceCheck = ({ onBack }) => {
  const [step, setStep] = useState("capture"); // capture, verifying, success, error
  const [error, setError] = useState(null);
  const [employeeData, setEmployeeData] = useState(null);

  const handleCapture = async (imageFile) => {
    setStep("verifying");
    setError(null);

    try {
      // Verify face
      const verifyResult = await verifyAttendance(imageFile);

      if (verifyResult && verifyResult.match_found) {
        setEmployeeData(verifyResult);

        // Record check-in
        try {
          await checkIn(verifyResult.employee_id);
        } catch (checkInErr) {
          console.error("Check-in error:", checkInErr);
          // Continue even if check-in fails - we've verified the person
        }

        setStep("success");
      } else {
        setError("Face not recognized. Have you registered yet?");
        setStep("capture");
      }
    } catch (err) {
      console.error("Verification error:", err);
      // Check if it's a "not found" error (no registered face)
      const errorMsg = err.message || "";
      if (errorMsg.includes("not recognized") || errorMsg.includes("404")) {
        setError(
          "Face not recognized. Please register first using 'New Registration'."
        );
      } else {
        setError(errorMsg || "Verification failed. Please try again.");
      }
      setStep("capture");
    }
  };

  const handleRetry = () => {
    setStep("capture");
    setError(null);
    setEmployeeData(null);
  };

  if (step === "verifying") {
    return (
      <div className={styles.container}>
        <div className={styles.verifyingContainer}>
          <div className={styles.spinner}></div>
          <p className={styles.verifyingMessage}>Verifying your identity...</p>
        </div>
      </div>
    );
  }

  if (step === "success" && employeeData) {
    return (
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
          <h2 className={styles.successTitle}>Check-in Successful!</h2>
          <div className={styles.employeeInfo}>
            <p className={styles.employeeName}>{employeeData.full_name}</p>
            <p className={styles.employeeId}>ID: {employeeData.employee_id}</p>
            {employeeData.department && (
              <p className={styles.department}>{employeeData.department}</p>
            )}
            <p className={styles.checkInTime}>
              Checked in at {new Date().toLocaleTimeString()}
            </p>
            {employeeData.similarity_score && (
              <p className={styles.confidence}>
                Match confidence:{" "}
                {(employeeData.similarity_score * 100).toFixed(1)}%
              </p>
            )}
          </div>
          <Button variant="primary" onClick={handleRetry} fullWidth>
            Check In Another Person
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <h2 className={styles.title}>Attendance Check-In</h2>
      <p className={styles.subtitle}>
        Position your face in the frame for verification
      </p>

      {error && (
        <div className={styles.errorWrapper}>
          <ErrorMessage message={error} onDismiss={() => setError(null)} />
        </div>
      )}

      <FaceCapture
        onCapture={handleCapture}
        onCancel={onBack}
        requiresLiveness={false}
        mode="attendance"
      />
    </div>
  );
};

export default AttendanceCheck;
