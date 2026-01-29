import React, { useState, useEffect } from 'react';
import { listEmployees, getEmployee } from '../../services/api';
import LoadingSpinner from '../Common/LoadingSpinner';
import ErrorMessage from '../Common/ErrorMessage';
import styles from './AdminPage.module.css';

const PersonsPage = () => {
  const [persons, setPersons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedPerson, setSelectedPerson] = useState(null);
  const [filters, setFilters] = useState({ status: '', role: '' });

  useEffect(() => {
    loadPersons();
  }, [filters]);

  const loadPersons = async () => {
    try {
      setLoading(true);
      const params = {};
      if (filters.status) params.status = filters.status;
      if (filters.role) params.role = filters.role;
      const data = await listEmployees(params);
      setPersons(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetails = async (personId) => {
    try {
      const person = await getEmployee(personId);
      setSelectedPerson(person);
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className={styles.pageContainer}>
      <div className={styles.pageHeader}>
        <h1>Persons Management</h1>
        <div className={styles.filters}>
          <select value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
            <option value="">All Statuses</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
          <select value={filters.role} onChange={(e) => setFilters({ ...filters, role: e.target.value })}>
            <option value="">All Roles</option>
            <option value="admin">Admin</option>
            <option value="supervisor">Supervisor</option>
            <option value="worker">Worker</option>
          </select>
        </div>
      </div>

      {error && <ErrorMessage message={error} />}

      <div className={styles.tableContainer}>
        <table className={styles.dataTable}>
          <thead>
            <tr>
              <th>ID</th>
              <th>Full Name</th>
              <th>Role</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {persons.map((person) => (
              <tr key={person.id}>
                <td>{person.person_id || person.id}</td>
                <td>{person.full_name}</td>
                <td>{person.role || 'worker'}</td>
                <td>
                  <span className={person.status === 'active' ? styles.activeBadge : styles.inactiveBadge}>
                    {person.status || 'active'}
                  </span>
                </td>
                <td>
                  <button onClick={() => handleViewDetails(person.id)} className={styles.viewButton}>View</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selectedPerson && (
        <div className={styles.formModal}>
          <div className={styles.formCard}>
            <h2>Person Details</h2>
            <div className={styles.detailsGrid}>
              <div><strong>ID:</strong> {selectedPerson.person_id || selectedPerson.id}</div>
              <div><strong>Full Name:</strong> {selectedPerson.full_name}</div>
              <div><strong>Role:</strong> {selectedPerson.role || 'worker'}</div>
              <div><strong>Status:</strong> {selectedPerson.status || 'active'}</div>
              {selectedPerson.email && <div><strong>Email:</strong> {selectedPerson.email}</div>}
              {selectedPerson.phone && <div><strong>Phone:</strong> {selectedPerson.phone}</div>}
            </div>
            <button onClick={() => setSelectedPerson(null)} className={styles.cancelButton}>Close</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default PersonsPage;







