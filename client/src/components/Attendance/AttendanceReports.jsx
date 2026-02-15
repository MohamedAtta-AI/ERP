import React, { useEffect, useMemo, useRef, useState } from "react";
import Papa from "papaparse";
import * as XLSX from "xlsx";
import {
  getAttendanceHistory,
  importAttendanceRows,
  listEmployees,
} from "../../services/api";
import ErrorMessage from "../Common/ErrorMessage";
import styles from "./AttendanceReports.module.css";

const EXPORT_COLUMNS = [
  "attendance_id",
  "person_id",
  "person_name",
  "attendance_date",
  "check_in",
  "check_out",
  "overtime_hours",
  "location_name",
  "shift_name",
  "assignment_title",
  "assignment_rate",
];

const IMPORT_COLUMNS = [
  "person_id",
  "attendance_date",
  "check_in",
  "check_out",
  "site_name",
  "shift_name",
  "overtime_hours",
];

const normalizeKey = (value) =>
  String(value || "")
    .trim()
    .toLowerCase()
    .replace(/\s+/g, "_")
    .replace(/[^a-z0-9_]/g, "");

const AttendanceReports = () => {
  const fileInputRef = useRef(null);
  const [records, setRecords] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const [query, setQuery] = useState("");
  const [personFilter, setPersonFilter] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [replaceExisting, setReplaceExisting] = useState(false);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [peopleData, historyData] = await Promise.all([
        listEmployees({ limit: 1000 }).catch(() => []),
        getAttendanceHistory({
          person_id: personFilter || undefined,
          start_date: startDate || undefined,
          end_date: endDate || undefined,
          limit: 5000,
        }),
      ]);
      setEmployees(peopleData || []);
      setRecords(historyData || []);
    } catch (e) {
      setError(e.message || "Failed to load attendance report");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [personFilter, startDate, endDate]);

  useEffect(() => {
    if (!success) return;
    const timer = setTimeout(() => setSuccess(null), 3000);
    return () => clearTimeout(timer);
  }, [success]);

  const filtered = useMemo(() => {
    const term = query.trim().toLowerCase();
    return records.filter((record) => {
      if (!term) return true;
      return [
        record.person_id,
        record.person_name,
        record.attendance_date,
        record.location_name,
        record.shift_name,
        record.overtime_hours,
        record.assignment_title,
        record.assignment_rate,
      ]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(term));
    });
  }, [records, query]);

  const stats = useMemo(() => {
    const total = filtered.length;
    const completed = filtered.filter((record) => record.check_in && record.check_out).length;
    const open = filtered.filter((record) => record.check_in && !record.check_out).length;
    return { total, completed, open };
  }, [filtered]);

  const exportRows = useMemo(
    () =>
      filtered.map((record) => ({
        attendance_id: record.id,
        person_id: record.person_id,
        person_name: record.person_name,
        attendance_date: record.attendance_date,
        check_in: record.check_in,
        check_out: record.check_out || "",
        overtime_hours: Number(record.overtime_hours || 0),
        location_name: record.location_name || "",
        shift_name: record.shift_name || "",
        assignment_title: record.assignment_title || "",
        assignment_rate: record.assignment_rate ?? "",
      })),
    [filtered]
  );

  const handleExportCSV = () => {
    const csv = Papa.unparse(exportRows, { columns: EXPORT_COLUMNS });
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `attendance_report_${new Date().toISOString().split("T")[0]}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleExportExcel = () => {
    const worksheet = XLSX.utils.json_to_sheet(exportRows, { header: EXPORT_COLUMNS });
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "Attendance");
    XLSX.writeFile(workbook, `attendance_report_${new Date().toISOString().split("T")[0]}.xlsx`);
  };

  const handleDownloadTemplate = () => {
    const sample = [
      {
        person_id: "",
        attendance_date: new Date().toISOString().split("T")[0],
        check_in: "",
        check_out: "",
        site_name: "",
        shift_name: "",
        overtime_hours: 0,
      },
    ];
    const worksheet = XLSX.utils.json_to_sheet(sample, { header: IMPORT_COLUMNS });
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "Template");
    XLSX.writeFile(workbook, "attendance_import_template.xlsx");
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

  const handleImportFile = async (event) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    setImporting(true);
    setError(null);
    try {
      const rawRows = await parseFileRows(file);
      if (!rawRows.length) {
        setError("Import file is empty.");
        return;
      }
      const rows = rawRows
        .map((row) => {
          const normalized = {};
          Object.entries(row || {}).forEach(([key, value]) => {
            normalized[normalizeKey(key)] = value;
          });
          const personId = String(normalized.person_id || "").trim();
          const attendanceDate = String(normalized.attendance_date || "").trim();
          const checkIn = String(normalized.check_in || "").trim();
          const checkOut = String(normalized.check_out || "").trim();
          const siteName = String(normalized.site_name || "").trim();
          const shiftName = String(normalized.shift_name || "").trim();
          const siteId = String(normalized.site_id || "").trim();
          const shiftId = String(normalized.shift_id || "").trim();
          const overtimeHoursRaw = String(normalized.overtime_hours || "").trim();
          const overtimeHours = overtimeHoursRaw === "" ? 0 : Number(overtimeHoursRaw);
          if (!personId || !attendanceDate) return null;
          return {
            person_id: personId,
            attendance_date: attendanceDate,
            check_in: checkIn || null,
            check_out: checkOut || null,
            site_name: siteName || null,
            shift_name: shiftName || null,
            // Backward compatibility if users still upload IDs.
            site_id: siteId || null,
            shift_id: shiftId || null,
            overtime_hours: Number.isFinite(overtimeHours) && overtimeHours > 0 ? overtimeHours : 0,
          };
        })
        .filter(Boolean);

      if (!rows.length) {
        setError("No valid rows found. Required columns: person_id, attendance_date.");
        return;
      }

      const result = await importAttendanceRows(rows, replaceExisting);
      await loadData();
      setSuccess(
        `Import complete. Created: ${result.created}, Updated: ${result.updated}, Skipped: ${result.skipped}, Failed: ${result.failed}.`
      );
      if (result.failed > 0 && result.errors?.length) {
        setError(result.errors.join(" | "));
      }
    } catch (e) {
      setError(e.message || "Failed to import attendance file");
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className={styles.wrap}>
      {error && <ErrorMessage message={error} />}
      {success && <div className={styles.success}>{success}</div>}

      <div className={styles.topBar}>
        <div className={styles.toolbar}>
          <input
            className="input-field"
            placeholder="Search by person, date, location, shift, overtime..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <select className="select-field" value={personFilter} onChange={(e) => setPersonFilter(e.target.value)}>
            <option value="">All Employees</option>
            {employees.map((employee) => (
              <option key={employee.id} value={employee.id}>
                {employee.full_name} ({employee.id})
              </option>
            ))}
          </select>
          <input type="date" className="input-field" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
          <input type="date" className="input-field" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
          <button className="btn btn-secondary" onClick={loadData}>
            Refresh
          </button>
        </div>
      </div>

      <div className={styles.actions}>
        <button className="btn btn-secondary" onClick={handleExportCSV} disabled={loading || importing}>
          Export CSV
        </button>
        <button className="btn btn-secondary" onClick={handleExportExcel} disabled={loading || importing}>
          Export Excel
        </button>
        <button className="btn btn-secondary" onClick={handleDownloadTemplate}>
          Download Import Template
        </button>
        <label className={styles.replaceToggle}>
          <input type="checkbox" checked={replaceExisting} onChange={(e) => setReplaceExisting(e.target.checked)} />
          Replace existing rows
        </label>
        <button className="btn btn-primary" onClick={() => fileInputRef.current?.click()} disabled={importing}>
          {importing ? "Importing..." : "Import CSV/Excel"}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.xlsx,.xls"
          onChange={handleImportFile}
          style={{ display: "none" }}
        />
      </div>

      <div className={styles.stats}>
        <div className={styles.card}><span>Visible Records</span><strong>{stats.total}</strong></div>
        <div className={styles.card}><span>Completed</span><strong>{stats.completed}</strong></div>
        <div className={styles.card}><span>Open Check-ins</span><strong>{stats.open}</strong></div>
      </div>

      <div className={styles.tableWrap}>
        {loading ? (
          <div className={styles.empty}>Loading attendance report...</div>
        ) : filtered.length === 0 ? (
          <div className={styles.empty}>No attendance records match the current filters.</div>
        ) : (
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Person</th>
                <th>ID</th>
                <th>Date</th>
                <th>Check In</th>
                <th>Check Out</th>
                <th>Overtime</th>
                <th>Location</th>
                <th>Shift</th>
                <th>Title</th>
                <th>Rate</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((record) => (
                <tr key={record.id}>
                  <td>{record.person_name}</td>
                  <td>{record.person_id}</td>
                  <td>{record.attendance_date}</td>
                  <td>{record.check_in ? new Date(record.check_in).toLocaleString() : "-"}</td>
                  <td>{record.check_out ? new Date(record.check_out).toLocaleString() : "-"}</td>
                  <td>{Number(record.overtime_hours || 0)}</td>
                  <td>{record.location_name || "-"}</td>
                  <td>{record.shift_name || "-"}</td>
                  <td>{record.assignment_title || "-"}</td>
                  <td>{record.assignment_rate ?? "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default AttendanceReports;
