import React, { useState, useEffect } from "react";
import { registerEmployee, listLocations, listShifts, createAssignment } from "../../services/api";
import Button from "../Common/Button";
import ErrorMessage from "../Common/ErrorMessage";
import styles from "./MultiStageRegistrationForm.module.css";

const TABS = [
  { id: "personal", label: "Personal Info", icon: "👤" },
  { id: "contact", label: "Contact", icon: "📧" },
  { id: "employment", label: "Employment", icon: "💼" },
  { id: "assignment", label: "Assignment", icon: "📍" },
  { id: "payroll", label: "Payroll", icon: "💰" },
];

const DEPARTMENTS = [
  "Engineering",
  "Sales",
  "Marketing",
  "Human Resources",
  "Finance",
  "Operations",
  "IT",
  "Legal",
  "Research",
  "Customer Support",
  "Construction",
  "Maintenance",
  "Other",
];

const MultiStageRegistrationForm = ({ onSuccess }) => {
  const [currentTab, setCurrentTab] = useState(0);
  const [formData, setFormData] = useState({
    // Personal Info
    full_name: "",
    identity_number: "",
    dob: "",
    sex: "",
    // Contact
    email: "",
    phone: "",
    // Employment
    department: "",
    position: "",
    // Assignment
    location_id: "",
    shift_id: "",
    assignment_title: "",
    hourly_rate: "",
    // Payroll
    base_salary: "",
    salary_components: {}, // {component_id: override_value}
  });
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState(null);
  const [employeeId, setEmployeeId] = useState(null);
  
  // Reference data
  const [locations, setLocations] = useState([]);
  const [shifts, setShifts] = useState([]);
  const [salaryComponents, setSalaryComponents] = useState([]);
  const [dataLoaded, setDataLoaded] = useState(false);
  
  // Load reference data on mount
  useEffect(() => {
    const loadReferenceData = async () => {
      try {
        const [locationsData, shiftsData] = await Promise.all([
          listLocations().catch(() => []),
          listShifts().catch(() => []),
        ]);
        setLocations(locationsData || []);
        setShifts(shiftsData || []);
        setSalaryComponents([]); // Salary components API not yet implemented
        setDataLoaded(true);
      } catch (err) {
        console.error("Failed to load reference data:", err);
        setDataLoaded(true); // Still allow form to work
      }
    };
    loadReferenceData();
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // Clear error for this field
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: null }));
    }
  };

  // Validate current tab fields
  const validateTab = (tabIndex) => {
    const newErrors = {};

    if (tabIndex === 0) {
      // Personal Info
      if (!formData.full_name.trim()) {
        newErrors.full_name = "Full name is required";
      } else if (formData.full_name.trim().length < 2) {
        newErrors.full_name = "Full name must be at least 2 characters";
      }
    }

    if (tabIndex === 1) {
      // Contact
      if (!formData.email.trim()) {
        newErrors.email = "Email is required";
      } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
        newErrors.email = "Please enter a valid email address";
      }
    }

    if (tabIndex === 2) {
      // Employment
      if (!formData.department) {
        newErrors.department = "Department is required";
      }
    }

    if (tabIndex === 3) {
      // Assignment
      if (!formData.location_id) {
        newErrors.location_id = "Work location is required";
      }
      if (!formData.shift_id) {
        newErrors.shift_id = "Work shift is required";
      }
    }

    // Tab 4 (Payroll) - optional, no required fields

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateTab(currentTab)) {
      setCurrentTab((prev) => Math.min(prev + 1, TABS.length - 1));
    }
  };

  const handlePrevious = () => {
    setCurrentTab((prev) => Math.max(prev - 1, 0));
  };

  const handleTabClick = (index) => {
    // Allow clicking on previous tabs or validate current before moving forward
    if (index < currentTab) {
      setCurrentTab(index);
    } else if (index === currentTab + 1 && validateTab(currentTab)) {
      setCurrentTab(index);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setApiError(null);

    if (!validateTab(currentTab)) {
      return;
    }

    setIsLoading(true);
    try {
      // Prepare data - only send non-empty fields
      const submitData = {};
      
      if (formData.full_name.trim()) submitData.full_name = formData.full_name.trim();
      if (formData.identity_number.trim()) submitData.identity_number = formData.identity_number.trim();
      if (formData.dob) submitData.dob = formData.dob;
      if (formData.sex) submitData.sex = formData.sex;
      if (formData.email.trim()) submitData.email = formData.email.trim();
      if (formData.phone.trim()) submitData.phone = formData.phone.trim();
      if (formData.department) submitData.department = formData.department;
      if (formData.position.trim()) submitData.position = formData.position.trim();

      console.log("Submitting registration:", submitData);
      const response = await registerEmployee(submitData);
      console.log("Registration response:", response);

      const id = response.person_id || response.employee_id || response.id;
      if (!id) {
        throw new Error("No ID returned from server");
      }
      
      // Create assignment if location and shift are specified
      if (formData.location_id && formData.shift_id) {
        try {
          const assignmentData = {
            person_id: id,
            location_id: formData.location_id,
            shift_id: formData.shift_id,
            title: formData.assignment_title || formData.position || null,
            rate: formData.hourly_rate ? parseFloat(formData.hourly_rate) : null,
            effective_from: new Date().toISOString().split('T')[0],
          };
          console.log("Creating assignment:", assignmentData);
          await createAssignment(assignmentData);
          console.log("Assignment created successfully");
        } catch (assignErr) {
          console.warn("Assignment creation failed:", assignErr);
          // Continue - employee was created successfully
        }
      }
      
      // Salary component overrides removed - API not yet implemented
      
      setEmployeeId(id);
    } catch (err) {
      console.error("Registration error:", err);
      const errorMessage = err.message || "Registration failed. Please try again.";
      setApiError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleContinue = () => {
    if (onSuccess && employeeId) {
      onSuccess({ employee_id: employeeId });
    }
  };

  // Success state - show employee ID
  if (employeeId) {
    return (
      <div className={styles.container}>
        <div className={styles.successContainer}>
          <div className={styles.successIcon}>
            <svg
              width="56"
              height="56"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
              <polyline points="22 4 12 14.01 9 11.01"></polyline>
            </svg>
          </div>
          <h2 className={styles.successTitle}>Registration Complete!</h2>
          <div className={styles.employeeIdBox}>
            <p className={styles.employeeIdLabel}>Employee ID:</p>
            <p className={styles.employeeId}>{employeeId}</p>
          </div>
          <p className={styles.successMessage}>
            Please save this ID. The employee will need it for future reference.
            <br />
            Next, let's enroll their face for attendance.
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
      <h2 className={styles.title}>Register New Employee</h2>
      <p className={styles.subtitle}>Fill in the employee details below</p>

      {/* Tab Navigation */}
      <div className={styles.tabNav}>
        {TABS.map((tab, index) => (
          <button
            key={tab.id}
            type="button"
            className={`${styles.tabButton} ${
              index === currentTab ? styles.tabActive : ""
            } ${index < currentTab ? styles.tabCompleted : ""}`}
            onClick={() => handleTabClick(index)}
          >
            <span className={styles.tabIcon}>{tab.icon}</span>
            <span className={styles.tabLabel}>{tab.label}</span>
            {index < currentTab && (
              <span className={styles.tabCheckmark}>✓</span>
            )}
          </button>
        ))}
      </div>

      {/* Progress Bar */}
      <div className={styles.progressBar}>
        <div
          className={styles.progressFill}
          style={{ width: `${((currentTab + 1) / TABS.length) * 100}%` }}
        />
      </div>

      <form onSubmit={handleSubmit} className={styles.form}>
        {/* Tab Content */}
        <div className={styles.tabContent}>
          {/* Personal Info Tab */}
          {currentTab === 0 && (
            <div className={styles.tabPanel}>
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
                  placeholder="Enter full name"
                  autoFocus
                />
                {errors.full_name && (
                  <span className={styles.errorText}>{errors.full_name}</span>
                )}
              </div>

              <div className={styles.formRow}>
                <div className={styles.formGroup}>
                  <label htmlFor="dob" className={styles.label}>
                    Date of Birth
                  </label>
                  <input
                    type="date"
                    id="dob"
                    name="dob"
                    value={formData.dob}
                    onChange={handleChange}
                    className={styles.input}
                    max={new Date().toISOString().split("T")[0]}
                  />
                </div>

                <div className={styles.formGroup}>
                  <label htmlFor="sex" className={styles.label}>
                    Sex
                  </label>
                  <select
                    id="sex"
                    name="sex"
                    value={formData.sex}
                    onChange={handleChange}
                    className={`${styles.input} ${styles.select}`}
                  >
                    <option value="">Select</option>
                    <option value="M">Male</option>
                    <option value="F">Female</option>
                  </select>
                </div>
              </div>

              <div className={styles.formGroup}>
                <label htmlFor="identity_number" className={styles.label}>
                  Identity Number
                </label>
                <input
                  type="text"
                  id="identity_number"
                  name="identity_number"
                  value={formData.identity_number}
                  onChange={handleChange}
                  className={styles.input}
                  placeholder="National ID / Passport number"
                />
                <span className={styles.helpText}>
                  Used for identification and payroll
                </span>
              </div>
            </div>
          )}

          {/* Contact Tab */}
          {currentTab === 1 && (
            <div className={styles.tabPanel}>
              <div className={styles.formGroup}>
                <label htmlFor="email" className={styles.label}>
                  Email Address <span className={styles.required}>*</span>
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
                  placeholder="employee@company.com"
                  autoFocus
                />
                {errors.email && (
                  <span className={styles.errorText}>{errors.email}</span>
                )}
              </div>

              <div className={styles.formGroup}>
                <label htmlFor="phone" className={styles.label}>
                  Phone Number
                </label>
                <input
                  type="tel"
                  id="phone"
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                  className={styles.input}
                  placeholder="+1 (555) 123-4567"
                />
              </div>
            </div>
          )}

          {/* Employment Tab */}
          {currentTab === 2 && (
            <div className={styles.tabPanel}>
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
                  autoFocus
                >
                  <option value="">Select a department</option>
                  {DEPARTMENTS.map((dept) => (
                    <option key={dept} value={dept}>
                      {dept}
                    </option>
                  ))}
                </select>
                {errors.department && (
                  <span className={styles.errorText}>{errors.department}</span>
                )}
              </div>

              <div className={styles.formGroup}>
                <label htmlFor="position" className={styles.label}>
                  Job Title / Position
                </label>
                <input
                  type="text"
                  id="position"
                  name="position"
                  value={formData.position}
                  onChange={handleChange}
                  className={styles.input}
                  placeholder="e.g., Software Engineer, Sales Manager"
                />
              </div>
            </div>
          )}

          {/* Assignment Tab */}
          {currentTab === 3 && (
            <div className={styles.tabPanel}>
              <div className={styles.formGroup}>
                <label htmlFor="location_id" className={styles.label}>
                  Work Location <span className={styles.required}>*</span>
                </label>
                <select
                  id="location_id"
                  name="location_id"
                  value={formData.location_id}
                  onChange={handleChange}
                  className={`${styles.input} ${styles.select} ${
                    errors.location_id ? styles.inputError : ""
                  }`}
                  autoFocus
                >
                  <option value="">Select a location</option>
                  {locations.map((loc) => (
                    <option key={loc.id} value={loc.id}>
                      {loc.name} {loc.city ? `(${loc.city})` : ""}
                    </option>
                  ))}
                </select>
                {errors.location_id && (
                  <span className={styles.errorText}>{errors.location_id}</span>
                )}
              </div>

              <div className={styles.formGroup}>
                <label htmlFor="shift_id" className={styles.label}>
                  Work Shift <span className={styles.required}>*</span>
                </label>
                <select
                  id="shift_id"
                  name="shift_id"
                  value={formData.shift_id}
                  onChange={handleChange}
                  className={`${styles.input} ${styles.select} ${
                    errors.shift_id ? styles.inputError : ""
                  }`}
                >
                  <option value="">Select a shift</option>
                  {shifts.map((shift) => (
                    <option key={shift.id} value={shift.id}>
                      {shift.name || `${shift.starts_at} - ${shift.ends_at}`}
                      {shift.is_overnight ? " (Overnight)" : ""}
                    </option>
                  ))}
                </select>
                {errors.shift_id && (
                  <span className={styles.errorText}>{errors.shift_id}</span>
                )}
              </div>

              <div className={styles.formRow}>
                <div className={styles.formGroup}>
                  <label htmlFor="assignment_title" className={styles.label}>
                    Assignment Title
                  </label>
                  <input
                    type="text"
                    id="assignment_title"
                    name="assignment_title"
                    value={formData.assignment_title}
                    onChange={handleChange}
                    className={styles.input}
                    placeholder="e.g., Site Supervisor"
                  />
                </div>

                <div className={styles.formGroup}>
                  <label htmlFor="hourly_rate" className={styles.label}>
                    Hourly Rate ($)
                  </label>
                  <input
                    type="number"
                    id="hourly_rate"
                    name="hourly_rate"
                    value={formData.hourly_rate}
                    onChange={handleChange}
                    className={styles.input}
                    placeholder="0.00"
                    min="0"
                    step="0.01"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Payroll Tab */}
          {currentTab === 4 && (
            <div className={styles.tabPanel}>
              <div className={styles.formGroup}>
                <label htmlFor="base_salary" className={styles.label}>
                  Base Daily Salary ($)
                </label>
                <input
                  type="number"
                  id="base_salary"
                  name="base_salary"
                  value={formData.base_salary}
                  onChange={handleChange}
                  className={styles.input}
                  placeholder="e.g., 100.00"
                  min="0"
                  step="0.01"
                  autoFocus
                />
                <span className={styles.helpText}>
                  Leave blank to use default rate
                </span>
              </div>

              <p className={styles.helpText} style={{ color: '#6b7280', fontStyle: 'italic' }}>
                Payroll functionality is not yet implemented in the backend.
              </p>

              {/* Final Summary */}
              <div className={styles.summaryBox}>
                <h4 className={styles.summaryTitle}>Registration Summary</h4>
                <dl className={styles.summaryList}>
                  <div className={styles.summaryItem}>
                    <dt>Name</dt>
                    <dd>{formData.full_name || "—"}</dd>
                  </div>
                  <div className={styles.summaryItem}>
                    <dt>Email</dt>
                    <dd>{formData.email || "—"}</dd>
                  </div>
                  <div className={styles.summaryItem}>
                    <dt>Department</dt>
                    <dd>{formData.department || "—"}</dd>
                  </div>
                  {formData.position && (
                    <div className={styles.summaryItem}>
                      <dt>Position</dt>
                      <dd>{formData.position}</dd>
                    </div>
                  )}
                  {formData.location_id && (
                    <div className={styles.summaryItem}>
                      <dt>Location</dt>
                      <dd>{locations.find(l => l.id === formData.location_id)?.name || "—"}</dd>
                    </div>
                  )}
                  {formData.shift_id && (
                    <div className={styles.summaryItem}>
                      <dt>Shift</dt>
                      <dd>{shifts.find(s => s.id === formData.shift_id)?.name || "—"}</dd>
                    </div>
                  )}
                  {formData.base_salary && (
                    <div className={styles.summaryItem}>
                      <dt>Base Salary</dt>
                      <dd>${formData.base_salary}/day</dd>
                    </div>
                  )}
                </dl>
              </div>
            </div>
          )}
        </div>

        {/* API Error */}
        {apiError && (
          <div className={styles.apiError}>
            <ErrorMessage message={apiError} onDismiss={() => setApiError(null)} />
          </div>
        )}

        {/* Navigation Buttons */}
        <div className={styles.buttonRow}>
          {currentTab > 0 && (
            <Button
              type="button"
              variant="secondary"
              onClick={handlePrevious}
              disabled={isLoading}
            >
              ← Previous
            </Button>
          )}
          
          <div className={styles.buttonSpacer} />
          
          {currentTab < TABS.length - 1 ? (
            <Button
              type="button"
              variant="primary"
              onClick={handleNext}
              disabled={isLoading}
            >
              Next →
            </Button>
          ) : (
            <Button
              type="submit"
              variant="primary"
              loading={isLoading}
              disabled={isLoading}
            >
              Register Employee
            </Button>
          )}
        </div>
      </form>
    </div>
  );
};

export default MultiStageRegistrationForm;

