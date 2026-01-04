import React, { useState, useRef, useCallback, useEffect } from "react";
import FaceCapture from "../FaceCapture/FaceCapture";
import { verifyAttendance, checkIn } from "../../services/api";
import styles from "./AttendanceCheck.module.css";

/**
 * Rapid Attendance Check Component
 * 
 * Features:
 * - Stays on same screen after recognition
 * - Shows result overlay briefly, then auto-resets
 * - Ready for next person immediately without touching anything
 * - Only shows result when high confidence + anti-spoofing passed
 */
const AttendanceCheck = ({ onBack }) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState(null); // { success: boolean, data: object, message: string }
  const [recentCheckins, setRecentCheckins] = useState([]); // Last few check-ins for display
  const [captureKey, setCaptureKey] = useState(0); // Key to force FaceCapture remount
  const resultTimeoutRef = useRef(null);

  // Auto-clear result after display and reset capture
  useEffect(() => {
    if (result) {
      resultTimeoutRef.current = setTimeout(() => {
        setResult(null);
        // Force FaceCapture to remount for next person
        setCaptureKey((k) => k + 1);
      }, 3500); // Show result for 3.5 seconds then auto-clear
    }
    return () => {
      if (resultTimeoutRef.current) {
        clearTimeout(resultTimeoutRef.current);
      }
    };
  }, [result]);

  const handleCapture = useCallback(async (imageFile) => {
    if (isProcessing) return;
    
    setIsProcessing(true);
    setResult(null);

    try {
      // Verify face with backend (includes anti-spoofing check)
      const verifyResult = await verifyAttendance(imageFile);

      if (verifyResult && verifyResult.match_found) {
        // Only show success if anti-spoofing passed (is_real = true)
        if (verifyResult.is_real === false) {
          setResult({
            success: false,
            message: "Spoofing detected. Please use your real face.",
            data: null,
          });
          setIsProcessing(false);
          return;
        }

        // High confidence check - don't show result for low confidence matches
        const confidence = verifyResult.similarity_score || 0;
        if (confidence < 0.65) {
          setResult({
            success: false,
            message: "Low confidence match. Please try again.",
            data: null,
          });
          setIsProcessing(false);
          return;
        }

        // Record check-in
        try {
          await checkIn(verifyResult.person_id || verifyResult.employee_id);
        } catch (checkInErr) {
          console.warn("Check-in recording failed:", checkInErr);
          // Continue - verification was successful
        }

        // Add to recent check-ins
        const checkinRecord = {
          id: Date.now(),
          name: verifyResult.full_name,
          personId: verifyResult.person_id || verifyResult.employee_id,
          time: new Date().toLocaleTimeString(),
          confidence: confidence,
        };

        setRecentCheckins((prev) => [checkinRecord, ...prev].slice(0, 5));

        setResult({
          success: true,
          message: `Welcome, ${verifyResult.full_name}!`,
          data: verifyResult,
        });
      } else {
        setResult({
          success: false,
          message: "Face not recognized. Please register first.",
          data: null,
        });
      }
    } catch (err) {
      console.error("Verification error:", err);
      const errorMsg = err.message || "";
      
      if (errorMsg.includes("spoof") || errorMsg.includes("real")) {
        setResult({
          success: false,
          message: "Spoofing detected. Use your real face.",
          data: null,
        });
      } else if (errorMsg.includes("not recognized") || errorMsg.includes("404")) {
        setResult({
          success: false,
          message: "Face not recognized. Please register first.",
          data: null,
        });
      } else {
        setResult({
          success: false,
          message: "Verification failed. Please try again.",
          data: null,
        });
      }
    } finally {
      setIsProcessing(false);
    }
  }, [isProcessing]);

  const handleCancel = useCallback(() => {
    if (onBack) {
      onBack();
    }
  }, [onBack]);

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
        <button className={styles.backButton} onClick={handleCancel}>
          ← Back
        </button>
        <h1 className={styles.title}>Attendance Check-In</h1>
        <div className={styles.headerSpacer} />
      </div>

      {/* Main Content */}
      <div className={styles.mainContent}>
        {/* Face Capture Area */}
        <div className={styles.captureSection}>
          <FaceCapture
            key={captureKey}
            onCapture={handleCapture}
            onCancel={handleCancel}
            requiresLiveness={false}
            mode="attendance"
          />

          {/* Processing Overlay */}
          {isProcessing && (
            <div className={styles.processingOverlay}>
              <div className={styles.spinner} />
              <span>Verifying...</span>
            </div>
          )}

          {/* Result Overlay - shows briefly then auto-clears */}
          {result && (
            <div 
              className={`${styles.resultOverlay} ${
                result.success ? styles.resultSuccess : styles.resultError
              }`}
            >
              <div className={styles.resultIcon}>
                {result.success ? (
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                    <polyline points="22 4 12 14.01 9 11.01" />
                  </svg>
                ) : (
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="15" y1="9" x2="9" y2="15" />
                    <line x1="9" y1="9" x2="15" y2="15" />
                  </svg>
                )}
              </div>
              <div className={styles.resultMessage}>{result.message}</div>
              {result.success && result.data && (
                <div className={styles.resultDetails}>
                  <span className={styles.personId}>
                    ID: {result.data.person_id || result.data.employee_id}
                  </span>
                  <span className={styles.checkTime}>
                    {new Date().toLocaleTimeString()}
                  </span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Recent Check-ins Sidebar */}
        <div className={styles.sidebar}>
          <h3 className={styles.sidebarTitle}>Recent Check-ins</h3>
          {recentCheckins.length === 0 ? (
            <p className={styles.noCheckins}>No check-ins yet</p>
          ) : (
            <ul className={styles.checkinList}>
              {recentCheckins.map((checkin) => (
                <li key={checkin.id} className={styles.checkinItem}>
                  <div className={styles.checkinInfo}>
                    <span className={styles.checkinName}>{checkin.name}</span>
                    <span className={styles.checkinId}>{checkin.personId}</span>
                  </div>
                  <span className={styles.checkinTime}>{checkin.time}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Instructions */}
      <div className={styles.instructions}>
        <p>Position your face in the frame. Check-in is automatic when your face is recognized.</p>
      </div>
    </div>
  );
};

export default AttendanceCheck;
