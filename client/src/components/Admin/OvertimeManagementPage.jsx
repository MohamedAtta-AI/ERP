import React, { useEffect, useMemo, useState } from "react";
import {
  approveOvertime,
  deleteOvertimeRequest,
  listEmployees,
  listOvertimeRequests,
  rejectOvertime,
  submitOvertimeRequest,
} from "../../services/api";
import { useAuth } from "../../contexts/AuthContext";
import ErrorMessage from "../Common/ErrorMessage";
import ModuleHeader from "../Common/ModuleHeader";
import styles from "./ManagementUI.module.css";

const DATA_EVENT = "erp:data-changed";

const OvertimeManagementPage = () => {
  const { hasRole, user } = useAuth();
  const isAdmin = hasRole("admin");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const [employees, setEmployees] = useState([]);
  const [requests, setRequests] = useState([]);

  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [personFilter, setPersonFilter] = useState("");

  const [form, setForm] = useState({
    person_id: "",
    overtime_date: new Date().toISOString().split("T")[0],
    hours: "",
    notes: "",
  });

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [peopleData, requestData] = await Promise.all([
        listEmployees({ limit: 1000 }).catch(() => []),
        listOvertimeRequests().catch(() => []),
      ]);
      setEmployees(peopleData || []);
      setRequests(requestData || []);

      if (!form.person_id && peopleData.length > 0) {
        const defaultPerson = isAdmin
          ? peopleData.find((person) => person.role === "worker") || peopleData[0]
          : peopleData.find((person) => person.id === user?.id) || peopleData[0];
        if (defaultPerson) setForm((prev) => ({ ...prev, person_id: defaultPerson.id }));
      }
    } catch (e) {
      setError(e.message || "Failed to load overtime data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const onDataChanged = (event) => {
      const changeType = event?.detail?.type;
      if (!changeType || ["employee", "overtime"].includes(changeType)) {
        loadData();
      }
    };
    const onFocus = () => loadData();
    window.addEventListener(DATA_EVENT, onDataChanged);
    window.addEventListener("focus", onFocus);
    return () => {
      window.removeEventListener(DATA_EVENT, onDataChanged);
      window.removeEventListener("focus", onFocus);
    };
  }, []);

  useEffect(() => {
    if (!success) return;
    const t = setTimeout(() => setSuccess(null), 2500);
    return () => clearTimeout(t);
  }, [success]);

  const filteredRequests = useMemo(() => {
    const term = query.trim().toLowerCase();
    return requests.filter((request) => {
      if (statusFilter && request.status !== statusFilter) return false;
      if (personFilter && request.person_id !== personFilter) return false;
      if (!term) return true;
      return [request.person_name, request.person_id, request.notes, request.overtime_date]
        .filter(Boolean)
        .some((v) => String(v).toLowerCase().includes(term));
    });
  }, [requests, query, statusFilter, personFilter]);

  const stats = useMemo(() => {
    const total = filteredRequests.length;
    const pending = filteredRequests.filter((request) => request.status === "overtime_pending").length;
    const approved = filteredRequests.filter((request) => request.status === "overtime_approved").length;
    return { total, pending, approved };
  }, [filteredRequests]);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.person_id || !form.overtime_date || !form.hours) {
      setError("Person, date and hours are required.");
      return;
    }
    try {
      await submitOvertimeRequest({
        person_id: form.person_id,
        overtime_date: form.overtime_date,
        hours: Number(form.hours),
        notes: form.notes || null,
      });
      window.dispatchEvent(new CustomEvent(DATA_EVENT, { detail: { type: "overtime" } }));
      setSuccess("Overtime request created");
      setForm((prev) => ({ ...prev, hours: "", notes: "" }));
      await loadData();
    } catch (e) {
      setError(e.message || "Failed to create overtime request");
    }
  };

  const handleApprove = async (id) => {
    try {
      await approveOvertime(id);
      window.dispatchEvent(new CustomEvent(DATA_EVENT, { detail: { type: "overtime" } }));
      setSuccess("Request approved");
      await loadData();
    } catch (e) {
      setError(e.message || "Failed to approve request");
    }
  };

  const handleReject = async (id) => {
    const reason = window.prompt("Rejection reason:", "Rejected by admin") || "Rejected by admin";
    try {
      await rejectOvertime(id, reason);
      window.dispatchEvent(new CustomEvent(DATA_EVENT, { detail: { type: "overtime" } }));
      setSuccess("Request rejected");
      await loadData();
    } catch (e) {
      setError(e.message || "Failed to reject request");
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this overtime request?")) return;
    try {
      await deleteOvertimeRequest(id);
      window.dispatchEvent(new CustomEvent(DATA_EVENT, { detail: { type: "overtime" } }));
      setSuccess("Request deleted");
      await loadData();
    } catch (e) {
      setError(e.message || "Failed to delete request");
    }
  };

  return (
    <div className={styles.page}>
      <ModuleHeader title="Overtime Management" />

      {error && <ErrorMessage message={error} />}
      {success && <div className={styles.success}>{success}</div>}

      <div className={styles.panel} style={{ marginBottom: "1rem" }}>
        <h3 className={styles.panelTitle}>Create Overtime Request</h3>
        <form onSubmit={handleCreate} className={styles.formGridTight}>
          <div className="form-group">
            <label className="label">Person</label>
            <select className="select-field" value={form.person_id} onChange={(e) => setForm((p) => ({ ...p, person_id: e.target.value }))}>
              <option value="">Select...</option>
              {employees.map((employee) => (
                <option key={employee.id} value={employee.id}>
                  {employee.full_name} ({employee.role})
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label className="label">Date</label>
            <input type="date" className="input-field" value={form.overtime_date} onChange={(e) => setForm((p) => ({ ...p, overtime_date: e.target.value }))} />
          </div>
          <div className="form-group">
            <label className="label">Hours</label>
            <input type="number" min="0" step="0.5" className="input-field" value={form.hours} onChange={(e) => setForm((p) => ({ ...p, hours: e.target.value }))} />
          </div>
          <div className="form-group">
            <label className="label">Notes</label>
            <input className="input-field" value={form.notes} onChange={(e) => setForm((p) => ({ ...p, notes: e.target.value }))} />
          </div>
          <button className="btn btn-primary" type="submit">Submit</button>
        </form>
      </div>

      <div className={styles.toolbar} style={{ gridTemplateColumns: "2fr 1fr 1fr 140px" }}>
        <input className="input-field" placeholder="Search by person/date/notes..." value={query} onChange={(e) => setQuery(e.target.value)} />
        <select className="select-field" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">All Statuses</option>
          <option value="overtime_pending">Pending</option>
          <option value="overtime_approved">Approved</option>
          <option value="overtime_rejected">Rejected</option>
        </select>
        <select className="select-field" value={personFilter} onChange={(e) => setPersonFilter(e.target.value)}>
          <option value="">All People</option>
          {employees.map((employee) => (
            <option key={employee.id} value={employee.id}>{employee.full_name}</option>
          ))}
        </select>
        <button className="btn btn-secondary" onClick={loadData}>Refresh</button>
      </div>

      <div className={styles.statRow}>
        <div className={styles.statCard}><span className={styles.statLabel}>Visible Requests</span><span className={styles.statValue}>{stats.total}</span></div>
        <div className={styles.statCard}><span className={styles.statLabel}>Pending</span><span className={styles.statValue}>{stats.pending}</span></div>
        <div className={styles.statCard}><span className={styles.statLabel}>Approved</span><span className={styles.statValue}>{stats.approved}</span></div>
      </div>

      <div className={styles.tableWrap}>
        {loading ? (
          <div className={styles.empty}>Loading overtime requests...</div>
        ) : filteredRequests.length === 0 ? (
          <div className={styles.empty}>No overtime requests match current filters.</div>
        ) : (
          <table className={styles.table} style={{ minWidth: "1100px" }}>
            <thead>
              <tr>
                <th>Person</th>
                <th>ID</th>
                <th>Date</th>
                <th>Hours</th>
                <th>Status</th>
                <th>Notes</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredRequests.map((request) => (
                <tr key={request.id}>
                  <td>{request.person_name}</td>
                  <td>{request.person_id}</td>
                  <td>{request.overtime_date}</td>
                  <td>{request.hours}</td>
                  <td>
                    <span
                      className={`${styles.badge} ${
                        request.status === "overtime_approved"
                          ? styles.ok
                          : request.status === "overtime_rejected"
                          ? styles.danger
                          : styles.warn
                      }`}
                    >
                      {request.status}
                    </span>
                  </td>
                  <td className={styles.muted}>{request.notes || "-"}</td>
                  <td>
                    <div className={styles.rowActions}>
                      {isAdmin && request.status !== "overtime_approved" && (
                        <button className="btn btn-primary" onClick={() => handleApprove(request.id)}>Approve</button>
                      )}
                      {isAdmin && request.status !== "overtime_rejected" && (
                        <button className="btn btn-secondary" onClick={() => handleReject(request.id)}>Reject</button>
                      )}
                      <button className="btn btn-danger" onClick={() => handleDelete(request.id)}>Delete</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default OvertimeManagementPage;
