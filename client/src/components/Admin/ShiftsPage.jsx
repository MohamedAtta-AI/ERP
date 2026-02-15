import React, { useEffect, useMemo, useState } from "react";
import { createShift, deleteShift, listShifts, updateShift } from "../../services/api";
import ErrorMessage from "../Common/ErrorMessage";
import ModuleHeader from "../Common/ModuleHeader";
import styles from "./ManagementUI.module.css";

const initialForm = { name: "", start_time: "08:00", end_time: "17:00" };
const DATA_EVENT = "erp:data-changed";

const normalizeTime = (value) => (value && value.length === 5 ? `${value}:00` : value);

const ShiftsPage = () => {
  const [shifts, setShifts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [query, setQuery] = useState("");
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(initialForm);

  const loadShifts = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listShifts(false);
      setShifts(data || []);
    } catch (e) {
      setError(e.message || "Failed to load shifts");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadShifts();
  }, []);

  useEffect(() => {
    if (!success) return;
    const t = setTimeout(() => setSuccess(null), 2500);
    return () => clearTimeout(t);
  }, [success]);

  const filtered = useMemo(() => {
    const term = query.trim().toLowerCase();
    if (!term) return shifts;
    return shifts.filter((shift) =>
      [shift.name, shift.start_time, shift.end_time]
        .filter(Boolean)
        .some((v) => String(v).toLowerCase().includes(term))
    );
  }, [shifts, query]);

  const handleEdit = (shift) => {
    setEditing(shift);
    setForm({
      name: shift.name || "",
      start_time: shift.start_time ? shift.start_time.substring(0, 5) : "08:00",
      end_time: shift.end_time ? shift.end_time.substring(0, 5) : "17:00",
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        name: form.name,
        start_time: normalizeTime(form.start_time),
        end_time: normalizeTime(form.end_time),
      };
      if (editing) {
        await updateShift(editing.id, payload);
        setSuccess("Shift updated");
      } else {
        await createShift(payload);
        setSuccess("Shift created");
      }
      window.dispatchEvent(new CustomEvent(DATA_EVENT, { detail: { type: "shift" } }));
      setEditing(null);
      setForm(initialForm);
      await loadShifts();
    } catch (e) {
      setError(e.message || "Failed to save shift");
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this shift?")) return;
    try {
      await deleteShift(id);
      setSuccess("Shift deleted");
      window.dispatchEvent(new CustomEvent(DATA_EVENT, { detail: { type: "shift" } }));
      await loadShifts();
    } catch (e) {
      setError(e.message || "Failed to delete shift");
    }
  };

  return (
    <div className={styles.page}>
      <ModuleHeader title="Shift Management" />

      {error && <ErrorMessage message={error} />}
      {success && <div className={styles.success}>{success}</div>}

      <div className={styles.layout}>
        <div>
          <div className={styles.toolbar} style={{ gridTemplateColumns: "2fr 140px" }}>
            <input className="input-field" placeholder="Search shift name or time..." value={query} onChange={(e) => setQuery(e.target.value)} />
            <button className="btn btn-secondary" onClick={loadShifts}>Refresh</button>
          </div>
          <div className={styles.statRow}>
            <div className={styles.statCard}><span className={styles.statLabel}>Visible Shifts</span><span className={styles.statValue}>{filtered.length}</span></div>
          </div>
          <div className={styles.tableWrap}>
            {loading ? (
              <div className={styles.empty}>Loading shifts...</div>
            ) : filtered.length === 0 ? (
              <div className={styles.empty}>No shifts found.</div>
            ) : (
              <table className={styles.table} style={{ minWidth: "760px" }}>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Start</th>
                    <th>End</th>
                    <th>Duration</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((shift) => {
                    const start = shift.start_time?.substring(0, 5) || "--:--";
                    const end = shift.end_time?.substring(0, 5) || "--:--";
                    return (
                      <tr key={shift.id}>
                        <td>{shift.name}</td>
                        <td>{start}</td>
                        <td>{end}</td>
                        <td className={styles.muted}>{start} - {end}</td>
                        <td>
                          <div className={styles.rowActions}>
                            <button className="btn btn-secondary" onClick={() => handleEdit(shift)}>Edit</button>
                            <button className="btn btn-danger" onClick={() => handleDelete(shift.id)}>Delete</button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>
        </div>

        <div className={styles.panel}>
          <h3 className={styles.panelTitle}>{editing ? "Edit Shift" : "Create Shift"}</h3>
          <form onSubmit={handleSubmit} className={styles.formGridTight}>
            <div className="form-group">
              <label className="label">Shift Name</label>
              <input className="input-field" value={form.name} onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))} required />
            </div>
            <div className="form-group">
              <label className="label">Start Time</label>
              <input type="time" className="input-field" value={form.start_time} onChange={(e) => setForm((p) => ({ ...p, start_time: e.target.value }))} required />
            </div>
            <div className="form-group">
              <label className="label">End Time</label>
              <input type="time" className="input-field" value={form.end_time} onChange={(e) => setForm((p) => ({ ...p, end_time: e.target.value }))} required />
            </div>
            <div className={styles.rowActions}>
              <button className="btn btn-primary" type="submit">{editing ? "Update" : "Create"}</button>
              {editing && (
                <button type="button" className="btn btn-secondary" onClick={() => { setEditing(null); setForm(initialForm); }}>
                  Cancel Edit
                </button>
              )}
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ShiftsPage;
