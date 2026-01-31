import React, { useState, useEffect } from 'react';
import { listLocations, createLocation, updateLocation, deleteLocation } from '../../services/api';
import LoadingSpinner from '../Common/LoadingSpinner';
import ErrorMessage from '../Common/ErrorMessage';
import styles from './AdminPage.module.css';

const LocationsPage = () => {
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editingLocation, setEditingLocation] = useState(null);
  
  // Model-aligned form data
  const [formData, setFormData] = useState({
    name: '',
    street_address: '',
    region: '',
    city: '',
  });

  useEffect(() => {
    loadLocations();
  }, []);

  const loadLocations = async () => {
    try {
      setLoading(true);
      const data = await listLocations(false);
      setLocations(data);
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
      if (editingLocation) {
        await updateLocation(editingLocation.id, formData);
      } else {
        await createLocation(formData);
      }
      await loadLocations();
      setShowForm(false);
      setEditingLocation(null);
      resetForm();
    } catch (err) {
      setError(err.message);
    }
  };

  const resetForm = () => {
    setFormData({ name: '', street_address: '', region: '', city: '' });
  };

  const handleEdit = (location) => {
    setEditingLocation(location);
    setFormData({
      name: location.name,
      street_address: location.street_address || '',
      region: location.region || '',
      city: location.city || '',
    });
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this location?')) return;
    try {
      await deleteLocation(id);
      await loadLocations();
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className={styles.pageContainer}>
      <div className={styles.pageHeader}>
        <h1 className="heading-xl">Locations Management</h1>
        <button 
          onClick={() => { setShowForm(true); setEditingLocation(null); resetForm(); }} 
          className="btn btn-primary"
        >
          + Add Location
        </button>
      </div>

      {error && <ErrorMessage message={error} />}

      {showForm && (
        <div className="modal-overlay">
          <div className="glass-panel modal-content">
            <h2 className="section-title">{editingLocation ? 'Edit Location' : 'New Location'}</h2>
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
              
              <div className="form-group">
                <label className="label">Street Address</label>
                <input
                  type="text"
                  className="input-field"
                  value={formData.street_address}
                  onChange={(e) => setFormData({ ...formData, street_address: e.target.value })}
                />
              </div>

              <div className="form-grid" style={{ marginBottom: 0 }}>
                <div className="form-group">
                  <label className="label">City</label>
                  <input
                    type="text"
                    className="input-field"
                    value={formData.city}
                    onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="label">Region</label>
                  <input
                    type="text"
                    className="input-field"
                    value={formData.region}
                    onChange={(e) => setFormData({ ...formData, region: e.target.value })}
                  />
                </div>
              </div>
              
              <div className={styles.formActions} style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
                <button type="button" onClick={() => { setShowForm(false); setEditingLocation(null); }} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">Save Location</button>
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
              <th style={{ padding: '1rem' }}>Address</th>
              <th style={{ padding: '1rem' }}>City/Region</th>
              <th style={{ padding: '1rem', textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {locations.length === 0 ? (
              <tr>
                <td colSpan="4" style={{ textAlign: 'center', padding: '2rem', color: 'var(--color-text-secondary)' }}>No locations found.</td>
              </tr>
            ) : (
              locations.map((location) => (
                <tr key={location.id} style={{ borderBottom: '1px solid var(--color-border)' }}>
                  <td style={{ padding: '1rem', fontWeight: 500 }}>{location.name}</td>
                  <td style={{ padding: '1rem' }}>{location.street_address || '-'}</td>
                  <td style={{ padding: '1rem' }}>
                    {location.city && location.region ? `${location.city}, ${location.region}` : 
                     location.city || location.region || '-'}
                  </td>
                  <td style={{ padding: '1rem', textAlign: 'right' }}>
                    <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                      <button onClick={() => handleEdit(location)} className="btn btn-secondary" style={{ padding: '0.25rem 0.75rem', fontSize: '0.75rem' }}>Edit</button>
                      <button onClick={() => handleDelete(location.id)} className="btn btn-danger" style={{ padding: '0.25rem 0.75rem', fontSize: '0.75rem' }}>Delete</button>
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

export default LocationsPage;
