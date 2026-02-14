import React, { useEffect, useMemo, useRef, useState } from "react";
import Papa from "papaparse";
import * as XLSX from "xlsx";
import {
  createAssignment,
  downloadEmployeeDocument,
  deleteEmployeeDocument,
  deleteEmployee,
  listAssignments,
  listEmployeeDocuments,
  listEmployees,
  listLocations,
  listShifts,
  registerEmployee,
  savePaymentInfo,
  uploadDocument,
  updateAssignment,
  updateEmployee,
} from "../../services/api";
import { useAuth } from "../../contexts/AuthContext";
import ErrorMessage from "../Common/ErrorMessage";
import ModuleHeader from "../Common/ModuleHeader";
import styles from "./ManagementUI.module.css";

const emptyAssignment = () => ({
  site_id: "",
  shift_id: "",
  title: "",
  rate: "",
  effective_from: new Date().toISOString().split("T")[0],
  effective_to: "",
});

const EXPORT_COLUMNS = [
  "id",
  "full_name",
  "role",
  "status",
  "has_face_registered",
  "face_embeddings_count",
  "phone",
  "email",
  "nationalID",
  "passport",
  "dob",
  "sex",
  "street_address",
  "city",
  "region",
  "worker_type",
  "pay_cycle",
  "supervisor_id",
  "supervisor_name",
  "overtime_eligible",
  "incentive_eligible",
  "hire_date",
  "termination_date",
  "payment_method",
  "bank_name",
  "account_holder",
  "account_number",
  "iban",
  "branch_code",
  "wallet_provider",
  "wallet_number",
];

const normalizeKey = (value) =>
  String(value || "")
    .trim()
    .toLowerCase()
    .replace(/\s+/g, "_")
    .replace(/[^a-z0-9_]/g, "");

const parseBoolean = (value, fallback = false) => {
  if (value === null || value === undefined || value === "") return fallback;
  const normalized = String(value).trim().toLowerCase();
  if (["true", "1", "yes", "y"].includes(normalized)) return true;
  if (["false", "0", "no", "n"].includes(normalized)) return false;
  return fallback;
};

const normalizeRole = (value) => {
  const v = String(value || "").trim().toLowerCase();
  if (["admin", "supervisor", "worker"].includes(v)) return v;
  return "worker";
};

const normalizeStatus = (value) => {
  const v = String(value || "").trim().toLowerCase();
  const allowed = ["active", "inactive", "suspended", "terminated", "on_leave"];
  if (allowed.includes(v)) return v;
  return "active";
};

const normalizeWorkerType = (value) => {
  const v = String(value || "").trim().toLowerCase();
  if (v === "temporary") return "temp";
  if (["permanent", "temp", "contractor"].includes(v)) return v;
  return null;
};

const normalizePayCycle = (value) => {
  const v = String(value || "").trim().toLowerCase();
  if (["daily", "weekly", "biweekly", "monthly"].includes(v)) return v;
  return null;
};

const maskIfExists = (value) => (value ? String(value) : "-");
const DATA_EVENT = "erp:data-changed";
const DOC_TYPES = [
  { value: "national_id", label: "National ID" },
  { value: "passport", label: "Passport" },
  { value: "drivers_license", label: "Driver's License" },
  { value: "visa", label: "Visa" },
  { value: "other", label: "Other" },
];

const EmployeeManagementPage = () => {
  const { hasRole } = useAuth();
  const isAdmin = hasRole("admin");
  const isSupervisorOnly = hasRole("supervisor") && !isAdmin;
  const fileInputRef = useRef(null);

  const [employees, setEmployees] = useState([]);
  const [locations, setLocations] = useState([]);
  const [shifts, setShifts] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [documents, setDocuments] = useState([]);

  const [loading, setLoading] = useState(true);
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const [query, setQuery] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [faceFilter, setFaceFilter] = useState("");

  const [selectedId, setSelectedId] = useState(null);
  const [editForm, setEditForm] = useState(null);
  const [newAssignment, setNewAssignment] = useState(emptyAssignment());
  const [showAddAssignmentForm, setShowAddAssignmentForm] = useState(false);
  const [showAddDocumentForm, setShowAddDocumentForm] = useState(false);
  const [terminateDates, setTerminateDates] = useState({});
  const [documentType, setDocumentType] = useState("national_id");
  const [documentFile, setDocumentFile] = useState(null);
  const [openingDocumentId, setOpeningDocumentId] = useState(null);

  const loadEmployees = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = { limit: 1000 };
      if (roleFilter) payload.role = roleFilter;
      if (statusFilter) payload.status = statusFilter;
      const data = await listEmployees(payload);
      setEmployees(data || []);
    } catch (e) {
      setError(e.message || "Failed to load employees");
    } finally {
      setLoading(false);
    }
  };

  const loadLookups = async () => {
    const [sites, shiftsData] = await Promise.all([
      listLocations(false).catch(() => []),
      listShifts(false).catch(() => []),
    ]);
    setLocations(sites || []);
    setShifts(shiftsData || []);
  };

  useEffect(() => {
    loadEmployees();
  }, [roleFilter, statusFilter]);

  useEffect(() => {
    loadLookups();
    const onDataChanged = (event) => {
      const changeType = event?.detail?.type;
      if (!changeType || ["employee", "site", "shift"].includes(changeType)) {
        loadEmployees();
        loadLookups();
      }
    };
    const onFocus = () => {
      loadEmployees();
      loadLookups();
    };
    window.addEventListener(DATA_EVENT, onDataChanged);
    window.addEventListener("focus", onFocus);
    return () => {
      window.removeEventListener(DATA_EVENT, onDataChanged);
      window.removeEventListener("focus", onFocus);
    };
  }, []);

  useEffect(() => {
    if (!success) return;
    const t = setTimeout(() => setSuccess(null), 3500);
    return () => clearTimeout(t);
  }, [success]);

  const selectedEmployee = useMemo(
    () => employees.find((employee) => employee.id === selectedId) || null,
    [employees, selectedId]
  );

  const filteredEmployees = useMemo(() => {
    const term = query.trim().toLowerCase();
    return employees.filter((employee) => {
      if (faceFilter === "yes" && !employee.has_face_registered) return false;
      if (faceFilter === "no" && employee.has_face_registered) return false;
      if (!term) return true;
      return [
        employee.id,
        employee.full_name,
        employee.email,
        employee.phone,
        employee.nationalID,
        employee.passport,
        employee.city,
        employee.region,
        employee.supervisor_name,
      ]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(term));
    });
  }, [employees, query, faceFilter]);

  const stats = useMemo(() => {
    const total = filteredEmployees.length;
    const face = filteredEmployees.filter((employee) => employee.has_face_registered).length;
    const active = filteredEmployees.filter((employee) => employee.status === "active").length;
    return { total, face, active };
  }, [filteredEmployees]);

  const loadAssignments = async (personId) => {
    try {
      const data = await listAssignments({ person_id: personId });
      setAssignments(data || []);
      const initialDates = {};
      (data || []).forEach((assignment) => {
        initialDates[assignment.id] = assignment.effective_to || "";
      });
      setTerminateDates(initialDates);
    } catch (e) {
      setError(e.message || "Failed to load assignments");
    }
  };

  const loadDocuments = async (personId) => {
    try {
      const data = await listEmployeeDocuments(personId);
      setDocuments(data || []);
    } catch (e) {
      setError(e.message || "Failed to load documents");
    }
  };

  const handleSelect = async (employee) => {
    setSelectedId(employee.id);
    setEditForm({
      full_name: employee.full_name || "",
      email: employee.email || "",
      phone: employee.phone || "",
      status: employee.status || "active",
      role: employee.role || "worker",
      supervisor_id: employee.supervisor_id || "",
    });
    setNewAssignment(emptyAssignment());
    setShowAddAssignmentForm(false);
    setShowAddDocumentForm(false);
    setDocumentFile(null);
    setDocumentType("national_id");
    await loadAssignments(employee.id);
    await loadDocuments(employee.id);
  };

  const supervisors = useMemo(
    () => employees.filter((employee) => employee.role === "supervisor" || employee.role === "admin"),
    [employees]
  );

  const handleSave = async () => {
    if (!selectedEmployee || !editForm) return;
    try {
      const payload = {
        full_name: editForm.full_name,
        email: editForm.email || null,
        phone: editForm.phone,
        status: editForm.status,
        supervisor_id: editForm.supervisor_id || null,
      };
      if (!isSupervisorOnly) payload.role = editForm.role;
      await updateEmployee(selectedEmployee.id, payload);

      const assignmentUpdates = assignments
        .filter((assignment) => (terminateDates[assignment.id] || "") !== (assignment.effective_to || ""))
        .map((assignment) =>
          updateAssignment(assignment.id, {
            effective_to: terminateDates[assignment.id] || null,
          })
        );

      if (showAddAssignmentForm && newAssignment.site_id && newAssignment.shift_id && newAssignment.effective_from) {
        assignmentUpdates.push(
          createAssignment({
            person_id: selectedEmployee.id,
            site_id: newAssignment.site_id,
            shift_id: newAssignment.shift_id,
            title: newAssignment.title || null,
            rate: newAssignment.rate ? Number(newAssignment.rate) : 0,
            effective_from: newAssignment.effective_from,
            effective_to: newAssignment.effective_to || null,
          })
        );
      }

      if (assignmentUpdates.length > 0) {
        await Promise.all(assignmentUpdates);
      }

      window.dispatchEvent(new CustomEvent(DATA_EVENT, { detail: { type: "employee" } }));
      setSuccess("Employee and assignments saved");
      setShowAddAssignmentForm(false);
      setNewAssignment(emptyAssignment());
      await loadEmployees();
      await loadAssignments(selectedEmployee.id);
    } catch (e) {
      setError(e.message || "Failed to update employee");
    }
  };

  const handleDeleteEmployee = async () => {
    if (!selectedEmployee || !isAdmin) return;
    if (!window.confirm(`Delete ${selectedEmployee.full_name}?`)) return;
    try {
      await deleteEmployee(selectedEmployee.id);
      window.dispatchEvent(new CustomEvent(DATA_EVENT, { detail: { type: "employee" } }));
      setSelectedId(null);
      setAssignments([]);
      setDocuments([]);
      setSuccess("Employee deleted");
      await loadEmployees();
    } catch (e) {
      setError(e.message || "Failed to delete employee. Make sure you are admin and the employee can be updated.");
    }
  };

  const buildExportRows = () =>
    filteredEmployees.map((employee) => {
      const row = {};
      EXPORT_COLUMNS.forEach((column) => {
        row[column] = employee[column] ?? "";
      });
      return row;
    });

  const handleExportCSV = () => {
    const rows = buildExportRows();
    const csv = Papa.unparse(rows, { columns: EXPORT_COLUMNS });
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `employees_export_${new Date().toISOString().split("T")[0]}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleExportExcel = () => {
    const rows = buildExportRows();
    const worksheet = XLSX.utils.json_to_sheet(rows, { header: EXPORT_COLUMNS });
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "Employees");
    XLSX.writeFile(workbook, `employees_export_${new Date().toISOString().split("T")[0]}.xlsx`);
  };

  const parseFileRows = async (file) => {
    const lower = file.name.toLowerCase();
    if (lower.endsWith(".csv")) {
      return new Promise((resolve, reject) => {
        Papa.parse(file, {
          header: true,
          skipEmptyLines: true,
          complete: (result) => resolve(result.data || []),
          error: reject,
        });
      });
    }
    if (lower.endsWith(".xlsx") || lower.endsWith(".xls")) {
      const buffer = await file.arrayBuffer();
      const workbook = XLSX.read(buffer, { type: "array" });
      const firstSheet = workbook.SheetNames[0];
      return XLSX.utils.sheet_to_json(workbook.Sheets[firstSheet], { defval: "" });
    }
    throw new Error("Unsupported file format. Use CSV or Excel (.xlsx/.xls).");
  };

  const mapRow = (row) => {
    const normalized = {};
    Object.entries(row || {}).forEach(([key, value]) => {
      normalized[normalizeKey(key)] = value;
    });
    return normalized;
  };

  const processImport = async (rawRows) => {
    const existingMap = new Map(employees.map((employee) => [employee.id, employee]));
    let created = 0;
    let updated = 0;
    let failed = 0;
    const failures = [];

    for (let i = 0; i < rawRows.length; i += 1) {
      const normalized = mapRow(rawRows[i]);
      const line = i + 2;
      try {
        const employeeId = String(normalized.id || normalized.employee_id || "").trim();
        const role = normalizeRole(normalized.role);
        const status = normalizeStatus(normalized.status);
        const workerType = normalizeWorkerType(normalized.worker_type);
        const payCycle = normalizePayCycle(normalized.pay_cycle);
        const fullName = String(normalized.full_name || "").trim();
        const phone = String(normalized.phone || "").trim();

        if (!fullName || !phone) {
          throw new Error("Missing required fields: full_name and phone");
        }

        const commonPayload = {
          full_name: fullName,
          email: String(normalized.email || "").trim() || null,
          phone,
          nationalID: String(normalized.nationalid || normalized.national_id || "").trim() || null,
          passport: String(normalized.passport || "").trim() || null,
          dob: String(normalized.dob || "").trim() || null,
          sex: String(normalized.sex || "").trim() || null,
          street_address: String(normalized.street_address || "").trim() || null,
          region: String(normalized.region || "").trim() || null,
          city: String(normalized.city || "").trim() || null,
          role,
          status,
          worker_type: workerType,
          pay_cycle: payCycle,
          supervisor_id: String(normalized.supervisor_id || "").trim() || null,
          overtime_eligible: parseBoolean(normalized.overtime_eligible, true),
          incentive_eligible: parseBoolean(normalized.incentive_eligible, true),
          hire_date: String(normalized.hire_date || "").trim() || null,
          termination_date: String(normalized.termination_date || "").trim() || null,
        };

        let personId = employeeId;
        if (employeeId && existingMap.has(employeeId)) {
          await updateEmployee(employeeId, {
            full_name: commonPayload.full_name,
            email: commonPayload.email,
            phone: commonPayload.phone,
            status: commonPayload.status,
            role: commonPayload.role,
            supervisor_id: commonPayload.supervisor_id,
            street_address: commonPayload.street_address,
            city: commonPayload.city,
          });
          updated += 1;
        } else {
          const createdEmployee = await registerEmployee(commonPayload);
          personId = createdEmployee.id;
          created += 1;
        }

        const paymentMethod = String(normalized.payment_method || "").trim();
        if (personId && paymentMethod) {
          await savePaymentInfo(personId, {
            person_id: personId,
            payment_method: paymentMethod,
            bank_name: String(normalized.bank_name || "").trim() || null,
            account_holder: String(normalized.account_holder || "").trim() || null,
            account_number: String(normalized.account_number || "").trim() || null,
            iban: String(normalized.iban || "").trim() || null,
            branch_code: String(normalized.branch_code || "").trim() || null,
            wallet_provider: String(normalized.wallet_provider || "").trim() || null,
            wallet_number: String(normalized.wallet_number || "").trim() || null,
          }).catch(() => null);
        }
      } catch (e) {
        failed += 1;
        failures.push(`Row ${line}: ${e.message || "Unknown import error"}`);
      }
    }

    return { created, updated, failed, failures };
  };

  const handleImportFile = async (event) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;

    setImporting(true);
    setError(null);
    try {
      const rows = await parseFileRows(file);
      if (!rows.length) {
        setError("Import file is empty.");
        return;
      }
      const result = await processImport(rows);
      await loadEmployees();
      window.dispatchEvent(new CustomEvent(DATA_EVENT, { detail: { type: "employee" } }));
      const summary = `Import complete. Created: ${result.created}, Updated: ${result.updated}, Failed: ${result.failed}.`;
      if (result.failed > 0) {
        setError(`${summary} ${result.failures.slice(0, 3).join(" | ")}`);
      } else {
        setSuccess(summary);
      }
    } catch (e) {
      setError(e.message || "Failed to import file");
    } finally {
      setImporting(false);
    }
  };

  const handleUploadDocument = async () => {
    if (!selectedEmployee) return;
    if (!documentFile) {
      setError("Please choose a file to upload.");
      return;
    }
    try {
      await uploadDocument(selectedEmployee.id, documentFile, documentType);
      setSuccess("Document uploaded");
      setDocumentFile(null);
      setShowAddDocumentForm(false);
      await loadDocuments(selectedEmployee.id);
    } catch (e) {
      setError(e.message || "Failed to upload document");
    }
  };

  const handleDeleteDocument = async (docId) => {
    if (!selectedEmployee) return;
    if (!window.confirm("Delete this document?")) return;
    try {
      await deleteEmployeeDocument(selectedEmployee.id, docId);
      setSuccess("Document deleted");
      await loadDocuments(selectedEmployee.id);
    } catch (e) {
      setError(e.message || "Failed to delete document");
    }
  };

  const handleOpenDocument = async (docId) => {
    if (!selectedEmployee) return;
    const previewWindow = window.open("", "_blank", "noopener,noreferrer");
    try {
      setOpeningDocumentId(docId);
      const { blob } = await downloadEmployeeDocument(selectedEmployee.id, docId);
      const objectUrl = URL.createObjectURL(blob);
      if (previewWindow) {
        previewWindow.location.href = objectUrl;
      } else {
        window.open(objectUrl, "_blank", "noopener,noreferrer");
      }
      setTimeout(() => URL.revokeObjectURL(objectUrl), 10000);
    } catch (e) {
      if (previewWindow) previewWindow.close();
      setError(e.message || "Failed to open document");
    } finally {
      setOpeningDocumentId(null);
    }
  };

  return (
    <div className={styles.page}>
      <ModuleHeader title="Employee Management" />

      {error && <ErrorMessage message={error} />}
      {success && <div className={styles.success}>{success}</div>}

      <div className={styles.toolbar}>
        <input
          className="input-field"
          placeholder="Search by ID, name, phone, national ID, city, supervisor..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <select className="select-field" value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)}>
          <option value="">All Roles</option>
          <option value="admin">Admin</option>
          <option value="supervisor">Supervisor</option>
          <option value="worker">Worker</option>
        </select>
        <select className="select-field" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">All Statuses</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
          <option value="suspended">Suspended</option>
          <option value="terminated">Terminated</option>
          <option value="on_leave">On Leave</option>
        </select>
        <select className="select-field" value={faceFilter} onChange={(e) => setFaceFilter(e.target.value)}>
          <option value="">All Face States</option>
          <option value="yes">Face Registered</option>
          <option value="no">No Face</option>
        </select>
        <button className="btn btn-secondary" onClick={loadEmployees} disabled={importing}>
          Refresh
        </button>
      </div>

      <div className={styles.rowActions} style={{ marginBottom: "0.75rem" }}>
        <button className="btn btn-secondary" onClick={handleExportCSV} disabled={loading || importing}>
          Export CSV
        </button>
        <button className="btn btn-secondary" onClick={handleExportExcel} disabled={loading || importing}>
          Export Excel
        </button>
        <button className="btn btn-primary" onClick={() => fileInputRef.current?.click()} disabled={importing}>
          {importing ? "Importing..." : "Import CSV/Excel"}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.xlsx,.xls"
          style={{ display: "none" }}
          onChange={handleImportFile}
        />
      </div>

      <div className={styles.statRow}>
        <div className={styles.statCard}><span className={styles.statLabel}>Visible Employees</span><span className={styles.statValue}>{stats.total}</span></div>
        <div className={styles.statCard}><span className={styles.statLabel}>Active</span><span className={styles.statValue}>{stats.active}</span></div>
        <div className={styles.statCard}><span className={styles.statLabel}>Face Registered</span><span className={styles.statValue}>{stats.face}</span></div>
      </div>

      <div className={styles.layout}>
        <div className={styles.tableWrap}>
          {loading ? (
            <div className={styles.empty}>Loading employees...</div>
          ) : filteredEmployees.length === 0 ? (
            <div className={styles.empty}>No employees match current filters.</div>
          ) : (
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Full Name</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Face</th>
                  <th>Phone</th>
                  <th>Email</th>
                  <th>National ID</th>
                  <th>Passport</th>
                  <th>DOB</th>
                  <th>Sex</th>
                  <th>Address</th>
                  <th>City</th>
                  <th>Region</th>
                  <th>Worker Type</th>
                  <th>Pay Cycle</th>
                  <th>Supervisor</th>
                  <th>OT Eligible</th>
                  <th>Incentive Eligible</th>
                  <th>Hire Date</th>
                  <th>Termination</th>
                  <th>Payment Method</th>
                  <th>Bank</th>
                  <th>Wallet</th>
                </tr>
              </thead>
              <tbody>
                {filteredEmployees.map((employee) => (
                  <tr
                    key={employee.id}
                    className={`${styles.tableRow} ${selectedId === employee.id ? styles.tableRowSelected : ""}`}
                    onClick={() => handleSelect(employee)}
                  >
                    <td>{employee.id}</td>
                    <td>{employee.full_name}</td>
                    <td>{employee.role}</td>
                    <td>{employee.status}</td>
                    <td>
                      <span className={`${styles.badge} ${employee.has_face_registered ? styles.ok : styles.warn}`}>
                        {employee.has_face_registered ? "Registered" : "Missing"}
                      </span>
                    </td>
                    <td>{maskIfExists(employee.phone)}</td>
                    <td>{maskIfExists(employee.email)}</td>
                    <td>{maskIfExists(employee.nationalID)}</td>
                    <td>{maskIfExists(employee.passport)}</td>
                    <td>{maskIfExists(employee.dob)}</td>
                    <td>{maskIfExists(employee.sex)}</td>
                    <td>{maskIfExists(employee.street_address)}</td>
                    <td>{maskIfExists(employee.city)}</td>
                    <td>{maskIfExists(employee.region)}</td>
                    <td>{maskIfExists(employee.worker_type)}</td>
                    <td>{maskIfExists(employee.pay_cycle)}</td>
                    <td>{maskIfExists(employee.supervisor_name || employee.supervisor_id)}</td>
                    <td>{employee.overtime_eligible ? "Yes" : "No"}</td>
                    <td>{employee.incentive_eligible ? "Yes" : "No"}</td>
                    <td>{maskIfExists(employee.hire_date)}</td>
                    <td>{maskIfExists(employee.termination_date)}</td>
                    <td>{maskIfExists(employee.payment_method)}</td>
                    <td>{maskIfExists(employee.bank_name)}</td>
                    <td>{maskIfExists(employee.wallet_number)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className={styles.panel}>
          {!selectedEmployee || !editForm ? (
            <div className={styles.empty}>Select a row to edit employee and assignments.</div>
          ) : (
            <>
              <h3 className={styles.panelTitle}>Edit {selectedEmployee.full_name}</h3>
              <div className={styles.formGridTight}>
                <div className="form-group">
                  <label className="label">Full Name</label>
                  <input className="input-field" value={editForm.full_name} onChange={(e) => setEditForm((p) => ({ ...p, full_name: e.target.value }))} />
                </div>
                <div className="form-group">
                  <label className="label">Phone</label>
                  <input className="input-field" value={editForm.phone} onChange={(e) => setEditForm((p) => ({ ...p, phone: e.target.value }))} />
                </div>
                <div className="form-group">
                  <label className="label">Email</label>
                  <input className="input-field" value={editForm.email} onChange={(e) => setEditForm((p) => ({ ...p, email: e.target.value }))} />
                </div>
                <div className="form-group">
                  <label className="label">Status</label>
                  <select className="select-field" value={editForm.status} onChange={(e) => setEditForm((p) => ({ ...p, status: e.target.value }))}>
                    <option value="active">Active</option>
                    <option value="inactive">Inactive</option>
                    <option value="suspended">Suspended</option>
                    <option value="terminated">Terminated</option>
                    <option value="on_leave">On Leave</option>
                  </select>
                </div>
                {!isSupervisorOnly && (
                  <div className="form-group">
                    <label className="label">Role</label>
                    <select className="select-field" value={editForm.role} onChange={(e) => setEditForm((p) => ({ ...p, role: e.target.value }))}>
                      <option value="worker">Worker</option>
                      <option value="supervisor">Supervisor</option>
                      <option value="admin">Admin</option>
                    </select>
                  </div>
                )}
                <div className="form-group">
                  <label className="label">Supervisor</label>
                  <select className="select-field" value={editForm.supervisor_id} onChange={(e) => setEditForm((p) => ({ ...p, supervisor_id: e.target.value }))}>
                    <option value="">None</option>
                    {supervisors
                      .filter((supervisor) => supervisor.id !== selectedEmployee.id)
                      .map((supervisor) => (
                        <option key={supervisor.id} value={supervisor.id}>
                          {supervisor.full_name} ({supervisor.role})
                        </option>
                      ))}
                  </select>
                </div>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "1rem" }}>
                <h3 className={styles.panelTitle} style={{ margin: 0 }}>Assignments</h3>
                <button
                  className="btn btn-secondary"
                  style={{ width: "34px", height: "34px", padding: 0, borderRadius: "999px", fontSize: "1.2rem", lineHeight: 1 }}
                  onClick={() => setShowAddAssignmentForm((prev) => !prev)}
                  title="Add Assignment"
                >
                  +
                </button>
              </div>
              {assignments.length === 0 ? (
                <div className={styles.empty}>No assignments found.</div>
              ) : (
                <ul className={styles.assignList}>
                  {assignments.map((assignment) => (
                    <li key={assignment.id} className={styles.assignItem}>
                      <div>
                        <div><strong>{assignment.title || "Assignment"}</strong></div>
                        <div className={styles.assignMeta}>
                          Site: {locations.find((l) => l.id === assignment.site_id)?.name || assignment.site_id} | Shift: {shifts.find((s) => s.id === assignment.shift_id)?.name || assignment.shift_id} | Rate: {assignment.rate}
                        </div>
                        <div className={styles.assignMeta}>
                          {assignment.effective_from} to {assignment.effective_to || "open"}
                        </div>
                      </div>
                      <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem", alignItems: "flex-start" }}>
                        <label className="label" style={{ margin: 0, fontSize: "0.75rem" }}>Termination Date</label>
                        <input
                          type="date"
                          className="input-field"
                          style={{ width: "160px", padding: "0.35rem 0.45rem" }}
                          value={terminateDates[assignment.id] || ""}
                          onChange={(e) => setTerminateDates((prev) => ({ ...prev, [assignment.id]: e.target.value }))}
                        />
                      </div>
                    </li>
                  ))}
                </ul>
              )}

              {showAddAssignmentForm && (
                <>
                  <div className={styles.formGridTight}>
                    <div className="form-group">
                      <label className="label">Site</label>
                      <select className="select-field" value={newAssignment.site_id} onChange={(e) => setNewAssignment((p) => ({ ...p, site_id: e.target.value }))}>
                        <option value="">Select...</option>
                        {locations.map((location) => (
                          <option key={location.id} value={location.id}>{location.name}</option>
                        ))}
                      </select>
                    </div>
                    <div className="form-group">
                      <label className="label">Shift</label>
                      <select className="select-field" value={newAssignment.shift_id} onChange={(e) => setNewAssignment((p) => ({ ...p, shift_id: e.target.value }))}>
                        <option value="">Select...</option>
                        {shifts.map((shift) => (
                          <option key={shift.id} value={shift.id}>{shift.name}</option>
                        ))}
                      </select>
                    </div>
                    <div className="form-group">
                      <label className="label">Title</label>
                      <input className="input-field" value={newAssignment.title} onChange={(e) => setNewAssignment((p) => ({ ...p, title: e.target.value }))} />
                    </div>
                    <div className="form-group">
                      <label className="label">Rate</label>
                      <input type="number" className="input-field" value={newAssignment.rate} onChange={(e) => setNewAssignment((p) => ({ ...p, rate: e.target.value }))} />
                    </div>
                    <div className="form-group">
                      <label className="label">From</label>
                      <input type="date" className="input-field" value={newAssignment.effective_from} onChange={(e) => setNewAssignment((p) => ({ ...p, effective_from: e.target.value }))} />
                    </div>
                    <div className="form-group">
                      <label className="label">To</label>
                      <input type="date" className="input-field" value={newAssignment.effective_to} onChange={(e) => setNewAssignment((p) => ({ ...p, effective_to: e.target.value }))} />
                    </div>
                  </div>
                  <div className={styles.rowActions}>
                    <button
                      className="btn btn-secondary"
                      onClick={() => {
                        setShowAddAssignmentForm(false);
                        setNewAssignment(emptyAssignment());
                      }}
                    >
                      Cancel
                    </button>
                  </div>
                </>
              )}

              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "1rem" }}>
                <h3 className={styles.panelTitle} style={{ margin: 0 }}>Documents</h3>
                <button
                  className="btn btn-secondary"
                  style={{ width: "34px", height: "34px", padding: 0, borderRadius: "999px", fontSize: "1.2rem", lineHeight: 1 }}
                  onClick={() => setShowAddDocumentForm((prev) => !prev)}
                  title="Add Document"
                >
                  +
                </button>
              </div>
              {documents.length === 0 ? (
                <div className={styles.empty}>No documents uploaded.</div>
              ) : (
                <ul className={styles.assignList}>
                  {documents.map((document) => (
                    <li key={document.id} className={styles.assignItem}>
                      <div>
                        <div><strong>{document.type?.replace("_", " ")}</strong></div>
                        <div className={styles.assignMeta}>
                          {document.uploaded_at ? new Date(document.uploaded_at).toLocaleString() : "-"}
                        </div>
                        <div className={styles.assignMeta}>
                          {document.file_name || String(document.url || "").split(/[\\/]/).pop() || document.url}
                        </div>
                      </div>
                      <div className={styles.rowActions}>
                        <button
                          className="btn btn-secondary"
                          onClick={() => handleOpenDocument(document.id)}
                          disabled={openingDocumentId === document.id}
                        >
                          {openingDocumentId === document.id ? "Opening..." : "Open"}
                        </button>
                        <button className="btn btn-danger" onClick={() => handleDeleteDocument(document.id)}>
                          Delete
                        </button>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
              {showAddDocumentForm && (
                <div style={{ marginTop: "0.75rem" }}>
                  <div className={styles.formGridTight}>
                    <div className="form-group">
                      <label className="label">Document Type</label>
                      <select className="select-field" value={documentType} onChange={(e) => setDocumentType(e.target.value)}>
                        {DOC_TYPES.map((docType) => (
                          <option key={docType.value} value={docType.value}>{docType.label}</option>
                        ))}
                      </select>
                    </div>
                    <div className="form-group">
                      <label className="label">File</label>
                      <input
                        type="file"
                        className="input-field"
                        accept=".pdf,.jpg,.jpeg,.png"
                        onChange={(e) => setDocumentFile(e.target.files?.[0] || null)}
                      />
                    </div>
                  </div>
                  <div className={styles.rowActions}>
                    <button className="btn btn-primary" onClick={handleUploadDocument}>Upload Document</button>
                    <button className="btn btn-secondary" onClick={() => setShowAddDocumentForm(false)}>Cancel</button>
                  </div>
                </div>
              )}
              <div style={{ marginTop: "1.25rem", paddingTop: "1rem", borderTop: "1px solid var(--color-border)" }}>
                <div className={styles.rowActions}>
                  <button className="btn btn-primary" onClick={handleSave}>Save Changes</button>
                  {isAdmin && (
                    <button className="btn btn-danger" onClick={handleDeleteEmployee}>Delete Employee</button>
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default EmployeeManagementPage;
