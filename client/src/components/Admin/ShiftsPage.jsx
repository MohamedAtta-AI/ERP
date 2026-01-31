import React, { useState, useEffect } from 'react';
import { listShifts, createShift, updateShift, deleteShift } from '../../services/api';
import LoadingSpinner from '../Common/LoadingSpinner';
import ErrorMessage from '../Common/ErrorMessage';
import styles from './AdminPage.module.css';

const ShiftsPage = () => {
  const [shifts, setShifts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editingShift, setEditingShift] = useState(null);
  
  // Model-aligned form data: name, start_time, end_time
  const [formData, setFormData] = useState({
    name: '',
    start_time: '',
    end_time: '',
  });

  useEffect(() => {
    loadShifts();
  }, []);

  const loadShifts = async () => {
    try {
      setLoading(true);
      const data = await listShifts(false);
      setShifts(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // Ensure time format is HH:MM:SS or HH:MM
      const payload = {
          ...formData,
          // Append seconds if missing, assuming input type="time" gives HH:MM
          start_time: formData.start_time.length === 5 ? `${formData.start_time}:00` : formData.start_time,
          end_time: formData.end_time.length === 5 ? `${formData.end_time}:00` : formData.end_time,
      };

      if (editingShift) {
        await updateShift(editingShift.id, payload);
      } else {
        await createShift(payload);
      }
      await loadShifts();
      setShowForm(false);
      setEditingShift(null);
      resetForm();
    } catch (err) {
      setError(err.message);
    }
  };

  const resetForm = () => {
    setFormData({ name: '', start_time: '', end_time: '' });
  };

  const handleEdit = (shift) => {
    setEditingShift(shift);
    setFormData({
      name: shift.name,
      start_time: shift.start_time ? shift.start_time.substring(0, 5) : '', // Slice to HH:MM for input
      end_time: shift.end_time ? shift.end_time.substring(0, 5) : '',
    });
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this shift?')) return;
    try {
      await deleteShift(id);
      await loadShifts();
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className={styles.pageContainer}>
      <div className={styles.pageHeader}>
        <h1 className="heading-xl">Shifts Management</h1>
        <button 
            onClick={() => { setShowForm(true); setEditingShift(null); resetForm(); }} 
            className="btn btn-primary"
        >
          + Add Shift
        </button>
      </div>

      {error && <ErrorMessage message={error} />}

      {showForm && (
        <div className="modal-overlay">
          <div className="glass-panel modal-content">
            <h2 className="section-title">{editingShift ? 'Edit Shift' : 'New Shift'}</h2>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="label">Name *</label>
                <input
                  type="text"
                  className="input-field"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>
              <div className="form-grid" style={{ marginBottom: 0 }}>
                <div className="form-group">
                  <label className="label">Start Time *</label>
                  <input
                    type="time"
                    className="input-field"
                    value={formData.start_time}
                    onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="label">End Time *</label>
                  <input
                    type="time"
                    className="input-field"
                    value={formData.end_time}
                    onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                    required
                  />
                </div>
              </div>
              
              <div className={styles.formActions} style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
                <button type="button" onClick={() => { setShowForm(false); setEditingShift(null); }} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">Save Shift</button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="glass-panel" style={{ padding: '2rem', marginTop: '1.5rem' }}>
        <table className={styles.dataTable} style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--color-border)' }}>
              <th style={{ padding: '1rem' }}>Name</th>
              <th style={{ padding: '1rem' }}>Start Time</th>
              <th style={{ padding: '1rem' }}>End Time</th>
              <th style={{ padding: '1rem', textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {shifts.length === 0 ? (
                <tr>
                    <td colSpan="4" style={{ textAlign: 'center', padding: '2rem', color: 'var(--color-text-secondary)' }}>No shifts found.</td>
                </tr>
            ) : (
                shifts.map((shift) => (
                <tr key={shift.id} style={{ borderBottom: '1px solid var(--color-border)' }}>
                    <td style={{ padding: '1rem', fontWeight: 500 }}>{shift.name}</td>
                    <td style={{ padding: '1rem' }}>{shift.start_time}</td>
                    <td style={{ padding: '1rem' }}>{shift.end_time}</td>
                    <td style={{ padding: '1rem', textAlign: 'right' }}>
                        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                            <button onClick={() => handleEdit(shift)} className="btn btn-secondary" style={{ padding: '0.25rem 0.75rem', fontSize: '0.75rem' }}>Edit</button>
                            <button onClick={() => handleDelete(shift.id)} className="btn btn-danger" style={{ padding: '0.25rem 0.75rem', fontSize: '0.75rem' }}>Delete</button>
                        </div>
                    </td>
                </tr>
                ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ShiftsPage;
