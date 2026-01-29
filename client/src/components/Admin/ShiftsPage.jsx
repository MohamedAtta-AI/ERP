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
  const [formData, setFormData] = useState({
    name: '',
    start_time: '',
    end_time: '',
    active: true,
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
      if (editingShift) {
        await updateShift(editingShift.id, formData);
      } else {
        await createShift(formData);
      }
      await loadShifts();
      setShowForm(false);
      setEditingShift(null);
      setFormData({ name: '', start_time: '', end_time: '', active: true });
    } catch (err) {
      setError(err.message);
    }
  };

  const handleEdit = (shift) => {
    setEditingShift(shift);
    setFormData({
      name: shift.name,
      start_time: shift.start_time || '',
      end_time: shift.end_time || '',
      active: shift.active,
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
        <h1>Shifts Management</h1>
        <button onClick={() => { setShowForm(true); setEditingShift(null); setFormData({ name: '', start_time: '', end_time: '', active: true }); }} className={styles.addButton}>
          + Add Shift
        </button>
      </div>

      {error && <ErrorMessage message={error} />}

      {showForm && (
        <div className={styles.formModal}>
          <div className={styles.formCard}>
            <h2>{editingShift ? 'Edit Shift' : 'New Shift'}</h2>
            <form onSubmit={handleSubmit}>
              <div className={styles.formGroup}>
                <label>Name *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>
              <div className={styles.formGroup}>
                <label>Start Time *</label>
                <input
                  type="time"
                  value={formData.start_time}
                  onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                  required
                />
              </div>
              <div className={styles.formGroup}>
                <label>End Time *</label>
                <input
                  type="time"
                  value={formData.end_time}
                  onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                  required
                />
              </div>
              <div className={styles.formGroup}>
                <label>
                  <input
                    type="checkbox"
                    checked={formData.active}
                    onChange={(e) => setFormData({ ...formData, active: e.target.checked })}
                  />
                  Active
                </label>
              </div>
              <div className={styles.formActions}>
                <button type="submit" className={styles.submitButton}>Save</button>
                <button type="button" onClick={() => { setShowForm(false); setEditingShift(null); }} className={styles.cancelButton}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className={styles.tableContainer}>
        <table className={styles.dataTable}>
          <thead>
            <tr>
              <th>Name</th>
              <th>Start Time</th>
              <th>End Time</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {shifts.map((shift) => (
              <tr key={shift.id}>
                <td>{shift.name}</td>
                <td>{shift.start_time}</td>
                <td>{shift.end_time}</td>
                <td>
                  <span className={shift.active ? styles.activeBadge : styles.inactiveBadge}>
                    {shift.active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td>
                  <button onClick={() => handleEdit(shift)} className={styles.editButton}>Edit</button>
                  <button onClick={() => handleDelete(shift.id)} className={styles.deleteButton}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ShiftsPage;







