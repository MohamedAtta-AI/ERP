import React, { useState } from "react";
import { registerEmployee } from "../../services/api";
import Button from "../Common/Button";
import ErrorMessage from "../Common/ErrorMessage";
import styles from "./RegistrationForm.module.css";

const RegistrationForm = ({ onSuccess }) => {
  const [formData, setFormData] = useState({
    full_name: "",
    email: "",
    department: "",
    phone: "",
    position: "",
  });
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [employeeId, setEmployeeId] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // Clear error for this field
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: null }));
    }
  };

  const validate = () => {
    const newErrors = {};

    if (!formData.full_name.trim()) {
      newErrors.full_name = "Full name is required";
    }

    if (!formData.email.trim()) {
      newErrors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = "Please enter a valid email address";
    }

    if (!formData.department.trim()) {
      newErrors.department = "Department is required";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!validate()) {
      return;
    }

    setIsLoading(true);
    try {
      const response = await registerEmployee(formData);
      setEmployeeId(response.employee_id);
    } catch (err) {
      setError(err.message || "Registration failed. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleContinue = () => {
    if (onSuccess && employeeId) {
      onSuccess({ employee_id: employeeId });
    }
  };

  if (employeeId) {
    return (
      <div className={styles.container}>
        <div className={styles.successContainer}>
          <div className={styles.successIcon}>
            <svg
              width="48"
              height="48"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
              <polyline points="22 4 12 14.01 9 11.01"></polyline>
            </svg>
          </div>
          <h2 className={styles.successTitle}>Registration Successful!</h2>
          <div className={styles.employeeIdBox}>
            <p className={styles.employeeIdLabel}>Your Employee ID:</p>
            <p className={styles.employeeId}>{employeeId}</p>
          </div>
          <p className={styles.successMessage}>
            Please save this ID. You will need it for future reference.
            <br />
            Now let's enroll your face for attendance.
          </p>
          <Button variant="primary" onClick={handleContinue} fullWidth>
            Continue to Face Enrollment
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <h2 className={styles.title}>Employee Registration</h2>
      <p className={styles.subtitle}>Please fill in your details to register</p>

      <form onSubmit={handleSubmit} className={styles.form}>
        <div className={styles.formGroup}>
          <label htmlFor="full_name" className={styles.label}>
            Full Name <span className={styles.required}>*</span>
          </label>
          <input
            type="text"
            id="full_name"
            name="full_name"
            value={formData.full_name}
            onChange={handleChange}
            className={`${styles.input} ${
              errors.full_name ? styles.inputError : ""
            }`}
            placeholder="Enter your full name"
          />
          {errors.full_name && (
            <span className={styles.errorText}>{errors.full_name}</span>
          )}
        </div>

        <div className={styles.formGroup}>
          <label htmlFor="email" className={styles.label}>
            Email <span className={styles.required}>*</span>
          </label>
          <input
            type="email"
            id="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            className={`${styles.input} ${
              errors.email ? styles.inputError : ""
            }`}
            placeholder="Enter your email"
          />
          {errors.email && (
            <span className={styles.errorText}>{errors.email}</span>
          )}
        </div>

        <div className={styles.formGroup}>
          <label htmlFor="department" className={styles.label}>
            Department <span className={styles.required}>*</span>
          </label>
          <select
            id="department"
            name="department"
            value={formData.department}
            onChange={handleChange}
            className={`${styles.input} ${styles.select} ${
              errors.department ? styles.inputError : ""
            }`}
          >
            <option value="">Select a department</option>
            <option value="Engineering">Engineering</option>
            <option value="Sales">Sales</option>
            <option value="Marketing">Marketing</option>
            <option value="HR">Human Resources</option>
            <option value="Finance">Finance</option>
            <option value="Operations">Operations</option>
            <option value="IT">IT</option>
            <option value="Other">Other</option>
          </select>
          {errors.department && (
            <span className={styles.errorText}>{errors.department}</span>
          )}
        </div>

        <div className={styles.formGroup}>
          <label htmlFor="position" className={styles.label}>
            Position
          </label>
          <input
            type="text"
            id="position"
            name="position"
            value={formData.position}
            onChange={handleChange}
            className={styles.input}
            placeholder="Enter your job title (optional)"
          />
        </div>

        <div className={styles.formGroup}>
          <label htmlFor="phone" className={styles.label}>
            Phone
          </label>
          <input
            type="tel"
            id="phone"
            name="phone"
            value={formData.phone}
            onChange={handleChange}
            className={styles.input}
            placeholder="Enter your phone number (optional)"
          />
        </div>

        {error && (
          <ErrorMessage message={error} onDismiss={() => setError(null)} />
        )}

        <Button type="submit" variant="primary" loading={isLoading} fullWidth>
          Register
        </Button>
      </form>
    </div>
  );
};

export default RegistrationForm;
