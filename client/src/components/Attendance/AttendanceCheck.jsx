import React, { useState, useRef, useCallback, useEffect } from "react";
import FaceCapture from "../FaceCapture/FaceCapture";
import { verifyAttendance, checkIn, checkOut, getAttendanceHistory } from "../../services/api";
import styles from "./AttendanceCheck.module.css";

/**
 * Rapid Attendance Check Component
 * 
 * Features:
 * - Continuous scanning - never stops camera
 * - Shows "Verified" indicator briefly on success
 * - On failure/spoofing, logs to console and continues scanning
 * - Supports both check-in and check-out based on existing attendance
 * - Ready for next person immediately
 */
const AttendanceCheck = ({ onBack }) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [verificationStatus, setVerificationStatus] = useState(null); // "verified" | "verifying" | null
  const [lastVerifiedPerson, setLastVerifiedPerson] = useState(null);
  const [lastAction, setLastAction] = useState(null); // "check-in" | "check-out"
  const [recentCheckins, setRecentCheckins] = useState([]); // Last few check-ins for display
  const [captureKey, setCaptureKey] = useState(0); // Key to force FaceCapture remount
  const statusTimeoutRef = useRef(null);

  // Auto-clear verification status and reset for next capture
  useEffect(() => {
    if (verificationStatus === "verified") {
      statusTimeoutRef.current = setTimeout(() => {
        setVerificationStatus(null);
        setLastVerifiedPerson(null);
        setLastAction(null);
        // Force FaceCapture to remount for next person
        setCaptureKey((k) => k + 1);
      }, 2500); // Show "Verified" for 2.5 seconds
    }
    return () => {
      if (statusTimeoutRef.current) {
        clearTimeout(statusTimeoutRef.current);
      }
    };
  }, [verificationStatus]);

  // Check if person has already checked in today
  const checkTodayAttendance = useCallback(async (personId) => {
    try {
      const today = new Date().toISOString().split('T')[0];
      const history = await getAttendanceHistory({
        person_id: personId,
        start_date: today,
        end_date: today,
        limit: 1,
      });
      if (history && history.length > 0) {
        return history[0]; // Return today's attendance record
      }
    } catch (err) {
      console.error("Error checking attendance:", err);
    }
    return null;
  }, []);

  const handleCapture = useCallback(async (imageFile) => {
    if (isProcessing) return;
    
    setIsProcessing(true);
    setVerificationStatus("verifying");

    try {
      // Verify face with backend (includes anti-spoofing check)
      const verifyResult = await verifyAttendance(imageFile);

      // Check for spoofing
      if (verifyResult && verifyResult.is_real === false) {
        console.warn("🚨 SPOOFING DETECTED - Anti-spoofing check failed", {
          timestamp: new Date().toISOString(),
          is_real: verifyResult.is_real,
          message: verifyResult.message || "Spoofing attempt",
        });
        // Continue scanning - don't show error to user
        setVerificationStatus(null);
        setCaptureKey((k) => k + 1);
        setIsProcessing(false);
        return;
      }

      if (verifyResult && verifyResult.match_found) {
        // High confidence check - don't proceed for low confidence matches
        const confidence = verifyResult.similarity_score || 0;
        if (confidence < 0.65) {
          console.log("⚠️ Low confidence match - rejecting", {
            confidence,
            timestamp: new Date().toISOString(),
          });
          // Continue scanning
          setVerificationStatus(null);
          setCaptureKey((k) => k + 1);
          setIsProcessing(false);
          return;
        }

        const personId = verifyResult.person_id || verifyResult.employee_id;
        
        // Check if person has already checked in today
        const todayAttendance = await checkTodayAttendance(personId);
        let action = "check-in";
        
        if (todayAttendance && todayAttendance.check_in && !todayAttendance.check_out) {
          // Already checked in but not out - perform check-out
          action = "check-out";
          try {
            await checkOut(imageFile);
            console.log("✅ Check-out recorded for", personId);
          } catch (checkOutErr) {
            console.warn("Check-out recording failed:", checkOutErr);
            // Continue - verification was successful
          }
        } else if (!todayAttendance || !todayAttendance.check_in) {
          // Not checked in yet - perform check-in
          try {
            await checkIn(imageFile);
            console.log("✅ Check-in recorded for", personId);
          } catch (checkInErr) {
            console.warn("Check-in recording failed:", checkInErr);
            // Continue - verification was successful
          }
        } else {
          // Already checked in AND out today
          action = "already-done";
          console.log("ℹ️ Already checked in and out today", personId);
        }

        // Add to recent check-ins
        const checkinRecord = {
          id: Date.now(),
          name: verifyResult.full_name,
          personId: personId,
          time: new Date().toLocaleTimeString(),
          confidence: confidence,
          action: action === "check-in" ? "In" : action === "check-out" ? "Out" : "Done",
        };

        setRecentCheckins((prev) => [checkinRecord, ...prev].slice(0, 5));

        // Show verified status
        setLastVerifiedPerson(verifyResult);
        setLastAction(action);
        setVerificationStatus("verified");
      } else {
        // No match found - log and continue scanning
        console.log("👤 Face not recognized - continuing scan", {
          timestamp: new Date().toISOString(),
          match_found: verifyResult?.match_found,
        });
        setVerificationStatus(null);
        setCaptureKey((k) => k + 1);
      }
    } catch (err) {
      console.error("❌ Verification error:", err);
      const errorMsg = err.message || "";
      
      if (errorMsg.includes("spoof") || errorMsg.includes("real")) {
        console.warn("🚨 SPOOFING DETECTED (error response)", {
          timestamp: new Date().toISOString(),
          error: errorMsg,
        });
      }
      
      // Continue scanning on any error
      setVerificationStatus(null);
      setCaptureKey((k) => k + 1);
    } finally {
      setIsProcessing(false);
    }
  }, [isProcessing, checkTodayAttendance]);

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
            verificationResult={
              verificationStatus === "verifying"
                ? { verifying: true }
                : verificationStatus === "verified" && lastVerifiedPerson
                ? {
                    verified: true,
                    full_name: lastVerifiedPerson.full_name,
                    person_id: lastVerifiedPerson.person_id || lastVerifiedPerson.employee_id,
                    action: lastAction,
                  }
                : null
            }
          />

          {/* Verifying Status Indicator */}
          {verificationStatus === "verifying" && (
            <div className={styles.statusIndicator}>
              <div className={styles.statusSpinner} />
              <span>Verifying...</span>
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
                  <div className={styles.checkinMeta}>
                    {checkin.action && (
                      <span className={`${styles.checkinAction} ${
                        checkin.action === "In" ? styles.actionIn : 
                        checkin.action === "Out" ? styles.actionOut : styles.actionDone
                      }`}>
                        {checkin.action}
                      </span>
                    )}
                    <span className={styles.checkinTime}>{checkin.time}</span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Instructions */}
      <div className={styles.instructions}>
        <p>Position your face in the yellow box. Check-in is automatic when recognized.</p>
      </div>
    </div>
  );
};

export default AttendanceCheck;
