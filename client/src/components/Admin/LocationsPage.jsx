import React, { useEffect, useMemo, useState } from "react";
import { createLocation, deleteLocation, listLocations, updateLocation } from "../../services/api";
import ErrorMessage from "../Common/ErrorMessage";
import ModuleHeader from "../Common/ModuleHeader";
import styles from "./ManagementUI.module.css";

const initialForm = { name: "", street_address: "", city: "", region: "" };
const DATA_EVENT = "erp:data-changed";

const LocationsPage = () => {
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [query, setQuery] = useState("");
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(initialForm);

  const loadLocations = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listLocations(false);
      setLocations(data || []);
    } catch (e) {
      setError(e.message || "Failed to load locations");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLocations();
  }, []);

  useEffect(() => {
    if (!success) return;
    const t = setTimeout(() => setSuccess(null), 2500);
    return () => clearTimeout(t);
  }, [success]);

  const filtered = useMemo(() => {
    const term = query.trim().toLowerCase();
    if (!term) return locations;
    return locations.filter((location) =>
      [location.name, location.street_address, location.city, location.region]
        .filter(Boolean)
        .some((v) => String(v).toLowerCase().includes(term))
    );
  }, [locations, query]);

  const handleEdit = (location) => {
    setEditing(location);
    setForm({
      name: location.name || "",
      street_address: location.street_address || "",
      city: location.city || "",
      region: location.region || "",
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editing) {
        await updateLocation(editing.id, form);
        setSuccess("Location updated");
      } else {
        await createLocation(form);
        setSuccess("Location created");
      }
      window.dispatchEvent(new CustomEvent(DATA_EVENT, { detail: { type: "site" } }));
      setForm(initialForm);
      setEditing(null);
      await loadLocations();
    } catch (e) {
      setError(e.message || "Failed to save location");
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this location?")) return;
    try {
      await deleteLocation(id);
      setSuccess("Location deleted");
      window.dispatchEvent(new CustomEvent(DATA_EVENT, { detail: { type: "site" } }));
      await loadLocations();
    } catch (e) {
      setError(e.message || "Failed to delete location");
    }
  };

  return (
    <div className={styles.page}>
      <ModuleHeader title="Location Management" />

      {error && <ErrorMessage message={error} />}
      {success && <div className={styles.success}>{success}</div>}

      <div className={styles.layout}>
        <div>
          <div className={styles.toolbar} style={{ gridTemplateColumns: "2fr 140px" }}>
            <input className="input-field" placeholder="Search name, address, city, region..." value={query} onChange={(e) => setQuery(e.target.value)} />
            <button className="btn btn-secondary" onClick={loadLocations}>Refresh</button>
          </div>
          <div className={styles.statRow}>
            <div className={styles.statCard}><span className={styles.statLabel}>Visible Locations</span><span className={styles.statValue}>{filtered.length}</span></div>
          </div>
          <div className={styles.tableWrap}>
            {loading ? (
              <div className={styles.empty}>Loading locations...</div>
            ) : filtered.length === 0 ? (
              <div className={styles.empty}>No locations found.</div>
            ) : (
              <table className={styles.table} style={{ minWidth: "900px" }}>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Street Address</th>
                    <th>City</th>
                    <th>Region</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((location) => (
                    <tr key={location.id}>
                      <td>{location.name}</td>
                      <td>{location.street_address || "-"}</td>
                      <td>{location.city || "-"}</td>
                      <td>{location.region || "-"}</td>
                      <td>
                        <div className={styles.rowActions}>
                          <button className="btn btn-secondary" onClick={() => handleEdit(location)}>Edit</button>
                          <button className="btn btn-danger" onClick={() => handleDelete(location.id)}>Delete</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        <div className={styles.panel}>
          <h3 className={styles.panelTitle}>{editing ? "Edit Location" : "Create Location"}</h3>
          <form onSubmit={handleSubmit} className={styles.formGridTight}>
            <div className="form-group">
              <label className="label">Name</label>
              <input className="input-field" value={form.name} onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))} required />
            </div>
            <div className="form-group">
              <label className="label">Street Address</label>
              <input className="input-field" value={form.street_address} onChange={(e) => setForm((p) => ({ ...p, street_address: e.target.value }))} />
            </div>
            <div className="form-group">
              <label className="label">City</label>
              <input className="input-field" value={form.city} onChange={(e) => setForm((p) => ({ ...p, city: e.target.value }))} />
            </div>
            <div className="form-group">
              <label className="label">Region</label>
              <input className="input-field" value={form.region} onChange={(e) => setForm((p) => ({ ...p, region: e.target.value }))} />
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

export default LocationsPage;
