import React, { useCallback, useEffect, useMemo, useState } from "react";
import FaceCapture from "../FaceCapture/FaceCapture";
import {
  checkIn,
  checkOut,
  listLocations,
  listShifts,
  verifyAttendance,
} from "../../services/api";
import styles from "./AttendanceCheck.module.css";

const DATA_EVENT = "erp:data-changed";

const AttendanceCheck = ({ onBack }) => {
  const [locations, setLocations] = useState([]);
  const [shifts, setShifts] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [captureKey, setCaptureKey] = useState(0);

  const [sessionSetup, setSessionSetup] = useState({
    mode: "check-in",
    site_id: "",
    shift_id: "",
  });
  const [sessionStarted, setSessionStarted] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [recent, setRecent] = useState([]);

  useEffect(() => {
    const loadReferenceData = async () => {
      const [siteData, shiftData] = await Promise.all([
        listLocations(true).catch(() => []),
        listShifts(true).catch(() => []),
      ]);
      setLocations(siteData || []);
      setShifts(shiftData || []);

      setSessionSetup((prev) => {
        const next = { ...prev };
        const siteStillExists = siteData?.some((location) => location.id === prev.site_id);
        const shiftStillExists = shiftData?.some((shift) => shift.id === prev.shift_id);
        if (!siteStillExists) next.site_id = siteData?.[0]?.id || "";
        if (!shiftStillExists) next.shift_id = shiftData?.[0]?.id || "";
        return next;
      });
    };

    const onDataChanged = (event) => {
      const changeType = event?.detail?.type;
      if (!changeType || ["site", "shift"].includes(changeType)) {
        loadReferenceData();
      }
    };
    const onFocus = () => loadReferenceData();

    loadReferenceData();
    window.addEventListener(DATA_EVENT, onDataChanged);
    window.addEventListener("focus", onFocus);
    return () => {
      window.removeEventListener(DATA_EVENT, onDataChanged);
      window.removeEventListener("focus", onFocus);
    };
  }, []);

  const canStartSession = useMemo(
    () => Boolean(sessionSetup.mode && sessionSetup.site_id && sessionSetup.shift_id),
    [sessionSetup]
  );

  const handleBack = () => {
    setSessionStarted(false);
    setFeedback(null);
    setCaptureKey((key) => key + 1);
    if (onBack) onBack();
  };

  const pushRecent = (name, personId, stateText) => {
    const item = {
      id: `${Date.now()}-${personId || "unknown"}`,
      name,
      personId,
      stateText,
      at: new Date().toLocaleTimeString(),
    };
    setRecent((prev) => [item, ...prev].slice(0, 8));
  };

  const finishCapture = () => {
    setIsProcessing(false);
    setCaptureKey((key) => key + 1);
  };

  const handleCapture = useCallback(
    async (imageFile) => {
      if (isProcessing || !sessionStarted) return;
      setIsProcessing(true);
      setFeedback({ type: "info", text: "Verifying face..." });

      try {
        const verifyResult = await verifyAttendance(
          imageFile,
          sessionSetup.site_id,
          sessionSetup.shift_id
        );

        if (!verifyResult?.match_found) {
          setFeedback({ type: "error", text: "Face not recognized. Try again." });
          pushRecent("Unknown", "-", "Not recognized");
          finishCapture();
          return;
        }

        const personName = verifyResult.full_name || "Unknown";
        const personId = verifyResult.person_id || "-";
        const current = verifyResult.current_status || "none";
        const mode = sessionSetup.mode;

        if (mode === "check-in") {
          if (current === "checked-in" || current === "checked-out") {
            setFeedback({
              type: "warn",
              text: `${personName} is already checked in for today.`,
            });
            pushRecent(personName, personId, "Already checked in");
            finishCapture();
            return;
          }

          await checkIn(imageFile, sessionSetup.site_id, sessionSetup.shift_id);
          setFeedback({
            type: "success",
            text: `Check-in succeeded for ${personName}.`,
          });
          pushRecent(personName, personId, "Checked in");
          finishCapture();
          return;
        }

        if (current === "checked-out") {
          setFeedback({
            type: "warn",
            text: `${personName} already checked out today.`,
          });
          pushRecent(personName, personId, "Already checked out");
          finishCapture();
          return;
        }
        if (current === "none") {
          setFeedback({
            type: "error",
            text: `${personName} has no check-in yet. Check-in is required first.`,
          });
          pushRecent(personName, personId, "No check-in found");
          finishCapture();
          return;
        }

        await checkOut(imageFile, sessionSetup.site_id, sessionSetup.shift_id);
        setFeedback({
          type: "success",
          text: `Check-out succeeded for ${personName}.`,
        });
        pushRecent(personName, personId, "Checked out");
      } catch (error) {
        setFeedback({
          type: "error",
          text: error?.message || "Attendance action failed.",
        });
      } finally {
        finishCapture();
      }
    },
    [isProcessing, sessionStarted, sessionSetup]
  );

  if (!sessionStarted) {
    return (
      <div className={styles.container}>
        <div className={styles.header}>
          <button className={styles.backButton} onClick={handleBack}>Back</button>
          <h1 className={styles.title}>Attendance Session Setup</h1>
          <div className={styles.headerSpacer} />
        </div>
        <div className={styles.setupCard}>
          <div className={styles.setupGrid}>
            <div className={styles.formGroup}>
              <label className={styles.label}>Mode</label>
              <select
                className={styles.selectField}
                value={sessionSetup.mode}
                onChange={(e) =>
                  setSessionSetup((prev) => ({ ...prev, mode: e.target.value }))
                }
              >
                <option value="check-in">Check In</option>
                <option value="check-out">Check Out</option>
              </select>
            </div>
            <div className={styles.formGroup}>
              <label className={styles.label}>Location</label>
              <select
                className={styles.selectField}
                value={sessionSetup.site_id}
                onChange={(e) =>
                  setSessionSetup((prev) => ({ ...prev, site_id: e.target.value }))
                }
              >
                <option value="">Select location...</option>
                {locations.map((location) => (
                  <option key={location.id} value={location.id}>
                    {location.name}
                  </option>
                ))}
              </select>
            </div>
            <div className={styles.formGroup}>
              <label className={styles.label}>Shift</label>
              <select
                className={styles.selectField}
                value={sessionSetup.shift_id}
                onChange={(e) =>
                  setSessionSetup((prev) => ({ ...prev, shift_id: e.target.value }))
                }
              >
                <option value="">Select shift...</option>
                {shifts.map((shift) => (
                  <option key={shift.id} value={shift.id}>
                    {shift.name} ({shift.start_time}-{shift.end_time})
                  </option>
                ))}
              </select>
            </div>
          </div>
          <button
            className={styles.startBtn}
            disabled={!canStartSession}
            onClick={() => setSessionStarted(true)}
          >
            Start Session
          </button>
          <p className={styles.setupHint}>
            This setup is used for all captures until you leave this module.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <button className={styles.backButton} onClick={handleBack}>Back</button>
        <h1 className={styles.title}>
          Attendance: {sessionSetup.mode === "check-in" ? "Check In" : "Check Out"}
        </h1>
        <button className={styles.backButton} onClick={() => setSessionStarted(false)}>
          Change Setup
        </button>
      </div>

      <div className={styles.meta}>
        <span>
          Location: {locations.find((location) => location.id === sessionSetup.site_id)?.name || "-"}
        </span>
        <span>
          Shift: {shifts.find((shift) => shift.id === sessionSetup.shift_id)?.name || "-"}
        </span>
      </div>

      <div className={styles.mainContent}>
        <div className={styles.captureSection}>
          <FaceCapture
            key={captureKey}
            onCapture={handleCapture}
            onCancel={handleBack}
            requiresLiveness={false}
            mode="attendance"
            verificationResult={isProcessing ? { verifying: true } : null}
          />
        </div>

        <div className={styles.sidebar}>
          <h3 className={styles.sidebarTitle}>Last Results</h3>
          {feedback && (
            <div className={`${styles.feedback} ${styles[`feedback_${feedback.type}`]}`}>
              {feedback.text}
            </div>
          )}
          <h4 className={styles.sidebarSubtitle}>Recent</h4>
          {recent.length === 0 ? (
            <p className={styles.emptyText}>No attendance actions yet.</p>
          ) : (
            <ul className={styles.recentList}>
              {recent.map((item) => (
                <li key={item.id} className={styles.recentItem}>
                  <div>{item.name}</div>
                  <div className={styles.recentMeta}>
                    {item.personId} | {item.stateText} | {item.at}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
};

export default AttendanceCheck;
