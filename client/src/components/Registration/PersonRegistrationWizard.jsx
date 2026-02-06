import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { 
  registerEmployee, 
  savePaymentInfo, 
  createAssignment, 
  listLocations, 
  listShifts,
  listEmployees,
  uploadDocument
} from '../../services/api';
import ErrorMessage from '../Common/ErrorMessage';

const STEPS = [
  { id: 1, title: 'Personal Information', icon: '👤' },
  { id: 2, title: 'Payment Details', icon: '💳' },
  { id: 3, title: 'Assignment', icon: '📍' },
];

const STORAGE_KEY = 'erp_registration_form_data';

const PersonRegistrationWizard = ({ onSuccess }) => {
  const { user, hasRole } = useAuth();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successId, setSuccessId] = useState(null);

  // Reference Data
  const [locations, setLocations] = useState([]);
  const [shifts, setShifts] = useState([]);
  const [supervisors, setSupervisors] = useState([]);

  // Load form data from localStorage on mount
  const getInitialFormData = () => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        return JSON.parse(saved);
      }
    } catch (e) {
      console.warn('Failed to load saved form data:', e);
    }
    return {
    // Personal
    full_name: '',
    email: '',
    phone: '',
    nationalID: '',
    passport: '',
    dob: '',
    sex: '',
    street_address: '',
    region: '',
    city: '',
    role: 'worker', // Default
    status: 'active',
    worker_type: 'permanent',
    pay_cycle: 'monthly',
    supervisor_id: '',
    overtime_eligible: true,
    incentive_eligible: true,
    hire_date: new Date().toISOString().split('T')[0],

    // Payment
    payment_method: 'cash',
    bank_name: '',
    account_holder: '',
    account_number: '',
    iban: '',
    branch_code: '',
    wallet_provider: '',
    wallet_number: '',

    // Assignment
    site_id: '',
    shift_id: '',
    assignment_title: '',
    rate: '',
    effective_from: new Date().toISOString().split('T')[0],
    effective_to: '',
    termination_date: '',
  };
  };

  const [formData, setFormData] = useState(getInitialFormData);
  const [documents, setDocuments] = useState([]); // Array of {type: string, file: File}

  // Save form data to localStorage whenever it changes
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(formData));
    } catch (e) {
      console.warn('Failed to save form data:', e);
    }
  }, [formData]);

  // Clear saved form data on successful submission
  const clearSavedData = () => {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (e) {
      console.warn('Failed to clear saved form data:', e);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      try {
        const [locs, shfs, emps] = await Promise.all([
          listLocations(true).catch(() => []),
          listShifts(true).catch(() => []),
          listEmployees({ role: 'supervisor' }).catch(() => [])
        ]);
        setLocations(locs || []);
        setShifts(shfs || []);
        // Filter supervisors from employees if needed, assuming listEmployees supports role filter or we filter manually
        const sups = Array.isArray(emps) ? emps.filter(e => e.role === 'supervisor' || e.role === 'admin') : [];
        setSupervisors(sups);
      } catch (err) {
        console.error("Error loading reference data", err);
      }
    };
    loadData();
  }, []);

  // Update role based on logged in user permissions
  useEffect(() => {
    if (user) {
      if (hasRole('supervisor') && !hasRole('admin')) {
        setFormData(prev => ({ ...prev, role: 'worker' }));
      }
    }
  }, [user, hasRole]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => {
      const updates = {
        ...prev,
        [name]: type === 'checkbox' ? checked : value
      };
      
      // Clear wallet_provider when payment method changes
      if (name === 'payment_method') {
        if (value === 'instapay') {
          updates.wallet_provider = '';
        } else if (value !== 'wallet') {
          updates.wallet_provider = '';
        }
      }
      
      // Clear worker_type when role changes from worker
      if (name === 'role' && value !== 'worker') {
        updates.worker_type = '';
      }
      
      return updates;
    });
  };

  const validateStep = (currentStep) => {
    if (currentStep === 1) {
      if (!formData.full_name) return "Full Name is required";
      if (!formData.nationalID) return "National ID is required";
      if (formData.nationalID.length !== 14 || !/^\d{14}$/.test(formData.nationalID)) {
        return "National ID must be exactly 14 digits";
      }
      if (!formData.phone) return "Phone is required";
      if (formData.phone.length !== 11 || !/^\d{11}$/.test(formData.phone)) {
        return "Phone must be exactly 11 digits (no country code)";
      }
      // Check permissions
      if (hasRole('supervisor') && !hasRole('admin') && formData.role !== 'worker') {
        return "Supervisors can only register workers.";
      }
    }
    if (currentStep === 2) {
      // Validate wallet/instapay phone numbers
      if (formData.payment_method === 'wallet') {
        if (!formData.wallet_provider) return "Wallet provider is required";
        if (!formData.wallet_number) return "Wallet phone number is required";
        if (formData.wallet_number.length !== 11 || !/^\d{11}$/.test(formData.wallet_number)) {
          return "Wallet phone number must be exactly 11 digits (no country code)";
        }
      }
      if (formData.payment_method === 'instapay') {
        if (!formData.wallet_number) return "Instapay phone number is required";
        if (formData.wallet_number.length !== 11 || !/^\d{11}$/.test(formData.wallet_number)) {
          return "Instapay phone number must be exactly 11 digits (no country code)";
        }
      }
    }
    // Step 3 optional?
    return null;
  };

  const handleNext = () => {
    const err = validateStep(step);
    if (err) {
      setError(err);
      return;
    }
    setError(null);
    setStep(prev => prev + 1);
  };

  const handleBack = () => {
    setError(null);
    setStep(prev => prev - 1);
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    try {
      // 1. Register Person
      const personPayload = {
        full_name: formData.full_name,
        email: formData.email || null,
        phone: formData.phone || null,
        nationalID: formData.nationalID || null,
        passport: formData.passport || null,
        dob: formData.dob || null,
        sex: formData.sex || null,
        street_address: formData.street_address || null,
        region: formData.region || null,
        city: formData.city || null,
        role: formData.role,
        status: formData.status,
        worker_type: formData.worker_type || null,
        pay_cycle: formData.pay_cycle || null,
        supervisor_id: formData.supervisor_id || null,
        overtime_eligible: formData.overtime_eligible,
        incentive_eligible: formData.incentive_eligible,
        hire_date: formData.hire_date || new Date().toISOString().split('T')[0],
        termination_date: formData.termination_date || null,
        // password_hash is optional - backend will generate default if not provided
      };

      const personRes = await registerEmployee(personPayload);
      const personId = personRes.id || personRes.person_id || personRes.employee_id;

      if (!personId) throw new Error("Failed to get Person ID from registration response");

      // Clear saved form data on success
      clearSavedData();

      // 2. Save Payment Info
      if (formData.payment_method) {
        const paymentPayload = {
          payment_method: formData.payment_method,
          bank_name: formData.bank_name || null,
          account_holder: formData.account_holder || null,
          account_number: formData.account_number || null,
          iban: formData.iban || null,
          branch_code: formData.branch_code || null,
          // Only set wallet_provider for wallet payment method, not for instapay
          wallet_provider: formData.payment_method === 'wallet' ? (formData.wallet_provider || null) : null,
          wallet_number: formData.wallet_number || null,
          person_id: personId
        };
        await savePaymentInfo(personId, paymentPayload).catch(e => console.warn("Payment info failed", e));
      }

      // 3. Create Assignment
      if (formData.site_id && formData.shift_id) {
        const assignmentPayload = {
          person_id: personId,
          site_id: formData.site_id,
          shift_id: formData.shift_id,
          title: formData.assignment_title || formData.role,
          rate: formData.rate ? parseFloat(formData.rate) : 0,
          effective_from: formData.effective_from,
          effective_to: formData.effective_to || null,
        };
        await createAssignment(assignmentPayload).catch(e => console.warn("Assignment failed", e));
      }

      // 4. Upload Documents
      if (documents.length > 0) {
        for (const doc of documents) {
          try {
            await uploadDocument(personId, doc.file, doc.type);
          } catch (e) {
            console.warn(`Failed to upload document ${doc.type}:`, e);
          }
        }
      }

      setSuccessId(personId);
      if (onSuccess) onSuccess({ employee_id: personId, full_name: formData.full_name });

    } catch (err) {
      console.error(err);
      setError(err.message || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-panel" style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
      <h2 className="heading-xl" style={{ textAlign: 'center' }}>New Registration</h2>
      
      {/* Stepper */}
      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '2rem' }}>
        {STEPS.map((s, idx) => (
          <div key={s.id} style={{ display: 'flex', alignItems: 'center' }}>
            <div style={{ 
              width: '40px', height: '40px', borderRadius: '50%', 
              backgroundColor: step >= s.id ? 'var(--color-primary)' : 'var(--color-border)',
              color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontWeight: 600
            }}>
              {s.id}
            </div>
            {idx < STEPS.length - 1 && (
              <div style={{ width: '50px', height: '2px', backgroundColor: step > s.id ? 'var(--color-primary)' : 'var(--color-border)', margin: '0 10px' }} />
            )}
          </div>
        ))}
      </div>

      {error && <ErrorMessage message={error} />}

      <div style={{ minHeight: '400px' }}>
        {step === 1 && (
          <div className="form-animation">
            <h3 className="section-title">Personal Information</h3>
            <div className="form-grid">
              <div className="form-group">
                <label className="label">Full Name *</label>
                <input name="full_name" value={formData.full_name} onChange={handleChange} className="input-field" placeholder="John Doe" />
              </div>
              {hasRole('admin') && (
                <div className="form-group">
                  <label className="label">Role</label>
                  <select name="role" value={formData.role} onChange={handleChange} className="select-field">
                    <option value="worker">Worker</option>
                    <option value="supervisor">Supervisor</option>
                  </select>
                </div>
              )}
              <div className="form-group">
                <label className="label">National ID *</label>
                <input 
                  name="nationalID" 
                  value={formData.nationalID} 
                  onChange={handleChange} 
                  className="input-field" 
                  placeholder="14 digits"
                  maxLength={14}
                  pattern="[0-9]{14}"
                />
              </div>
              <div className="form-group">
                <label className="label">Passport</label>
                <input name="passport" value={formData.passport} onChange={handleChange} className="input-field" />
              </div>
              <div className="form-group">
                <label className="label">Email</label>
                <input name="email" type="email" value={formData.email} onChange={handleChange} className="input-field" />
              </div>
              <div className="form-group">
                <label className="label">Phone *</label>
                <input 
                  name="phone" 
                  value={formData.phone} 
                  onChange={handleChange} 
                  className="input-field" 
                  placeholder="11 digits (no country code)"
                  maxLength={11}
                  pattern="[0-9]{11}"
                />
              </div>
              <div className="form-group">
                <label className="label">Date of Birth</label>
                <input name="dob" type="date" value={formData.dob} onChange={handleChange} className="input-field" />
              </div>
              <div className="form-group">
                <label className="label">Sex</label>
                <select name="sex" value={formData.sex} onChange={handleChange} className="select-field">
                  <option value="">Select...</option>
                  <option value="M">Male</option>
                  <option value="F">Female</option>
                </select>
              </div>
              <div className="form-group">
                <label className="label">Street Address</label>
                <input name="street_address" value={formData.street_address} onChange={handleChange} className="input-field" />
              </div>
              <div className="form-group">
                <label className="label">Region</label>
                <input name="region" value={formData.region} onChange={handleChange} className="input-field" />
              </div>
              <div className="form-group">
                <label className="label">City</label>
                <input name="city" value={formData.city} onChange={handleChange} className="input-field" />
              </div>
              <div className="form-group">
                <label className="label">Hire Date *</label>
                <input 
                  name="hire_date" 
                  type="date" 
                  value={formData.hire_date} 
                  onChange={handleChange} 
                  className="input-field"
                  required
                />
              </div>
              <div className="form-group">
                <label className="label">Termination Date</label>
                <input 
                  name="termination_date" 
                  type="date" 
                  value={formData.termination_date} 
                  onChange={handleChange} 
                  className="input-field"
                />
              </div>
              {formData.role === 'worker' && (
                <>
                  <div className="form-group">
                    <label className="label">Worker Type</label>
                    <select name="worker_type" value={formData.worker_type} onChange={handleChange} className="select-field">
                      <option value="">Select...</option>
                      <option value="permanent">Permanent</option>
                      <option value="temporary">Temporary</option>
                      <option value="contractor">Contractor</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="label">Supervisor</label>
                    <select name="supervisor_id" value={formData.supervisor_id} onChange={handleChange} className="select-field">
                      <option value="">None</option>
                      {supervisors.map(s => (
                        <option key={s.id} value={s.id}>{s.full_name}</option>
                      ))}
                    </select>
                  </div>
                </>
              )}
              <div className="form-group">
                <label className="label">Pay Cycle</label>
                <select name="pay_cycle" value={formData.pay_cycle} onChange={handleChange} className="select-field">
                  <option value="">Select...</option>
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="biweekly">Biweekly</option>
                  <option value="monthly">Monthly</option>
                </select>
              </div>
              <div className="form-group">
                <label className="label" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <input 
                    type="checkbox" 
                    name="overtime_eligible" 
                    checked={formData.overtime_eligible} 
                    onChange={handleChange}
                  />
                  Overtime Eligible
                </label>
              </div>
              <div className="form-group">
                <label className="label" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <input 
                    type="checkbox" 
                    name="incentive_eligible" 
                    checked={formData.incentive_eligible} 
                    onChange={handleChange}
                  />
                  Incentive Eligible
                </label>
              </div>
              <div className="form-group" style={{ gridColumn: '1 / -1', marginTop: '1rem' }}>
                <label className="label">Documents (Optional)</label>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {documents.map((doc, idx) => (
                    <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem', backgroundColor: '#f3f4f6', borderRadius: '4px' }}>
                      <span style={{ flex: 1, fontSize: '0.875rem' }}>
                        <strong>{doc.type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}:</strong> {doc.file.name}
                      </span>
                      <button
                        type="button"
                        onClick={() => setDocuments(docs => docs.filter((_, i) => i !== idx))}
                        style={{ padding: '0.25rem 0.5rem', backgroundColor: '#ef4444', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '0.875rem' }}
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                  <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                    <select
                      id="doc-type-select"
                      style={{ flex: 1, padding: '0.5rem', borderRadius: '4px', border: '1px solid #d1d5db', fontSize: '0.875rem' }}
                    >
                      <option value="">Select document type...</option>
                      <option value="national_id">National ID</option>
                      <option value="passport">Passport</option>
                      <option value="drivers_license">Driver's License</option>
                      <option value="visa">Visa</option>
                      <option value="other">Other</option>
                    </select>
                    <input
                      type="file"
                      id="doc-file-input"
                      accept=".pdf,.jpg,.jpeg,.png"
                      style={{ display: 'none' }}
                      onChange={(e) => {
                        const file = e.target.files[0];
                        const typeSelect = document.getElementById('doc-type-select');
                        const docType = typeSelect.value;
                        if (file && docType) {
                          setDocuments(docs => [...docs, { type: docType, file }]);
                          typeSelect.value = '';
                          e.target.value = '';
                        } else if (file && !docType) {
                          alert('Please select a document type first');
                          e.target.value = '';
                        }
                      }}
                    />
                    <button
                      type="button"
                      onClick={() => {
                        const typeSelect = document.getElementById('doc-type-select');
                        const fileInput = document.getElementById('doc-file-input');
                        if (typeSelect.value) {
                          fileInput.click();
                        } else {
                          alert('Please select a document type first');
                        }
                      }}
                      style={{ padding: '0.5rem 1rem', backgroundColor: '#3b82f6', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '0.875rem' }}
                    >
                      Add Document
                    </button>
                  </div>
                  <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: 0 }}>
                    Supported formats: PDF, JPG, PNG. Documents will be uploaded after registration.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="form-animation">
            <h3 className="section-title">Payment Details</h3>
            <div className="form-group">
              <label className="label">Payment Method</label>
              <select name="payment_method" value={formData.payment_method} onChange={handleChange} className="select-field">
                <option value="cash">Cash</option>
                <option value="bank_transfer">Bank Transfer</option>
                <option value="wallet">Wallet</option>
                <option value="instapay">Instapay</option>
              </select>
            </div>

            {formData.payment_method === 'bank_transfer' && (
              <div className="form-grid">
                <div className="form-group">
                  <label className="label">Bank Name</label>
                  <input name="bank_name" value={formData.bank_name} onChange={handleChange} className="input-field" />
                </div>
                <div className="form-group">
                  <label className="label">Account Holder</label>
                  <input name="account_holder" value={formData.account_holder} onChange={handleChange} className="input-field" />
                </div>
                <div className="form-group">
                  <label className="label">Account Number</label>
                  <input name="account_number" value={formData.account_number} onChange={handleChange} className="input-field" />
                </div>
                <div className="form-group">
                  <label className="label">IBAN</label>
                  <input name="iban" value={formData.iban} onChange={handleChange} className="input-field" />
                </div>
              </div>
            )}

            {formData.payment_method === 'wallet' && (
               <div className="form-grid">
                 <div className="form-group">
                   <label className="label">Provider *</label>
                   <select name="wallet_provider" value={formData.wallet_provider} onChange={handleChange} className="select-field" required>
                     <option value="">Select Provider...</option>
                     <option value="Vodafone Cash">Vodafone Cash</option>
                     <option value="Etsalat Cash">Etsalat Cash</option>
                     <option value="Orange Cash">Orange Cash</option>
                     <option value="WE Pay">WE Pay</option>
                   </select>
                 </div>
                 <div className="form-group">
                   <label className="label">Phone Number *</label>
                   <input 
                     name="wallet_number" 
                     value={formData.wallet_number} 
                     onChange={handleChange} 
                     className="input-field"
                     placeholder="11 digits (no country code)"
                     maxLength={11}
                     pattern="[0-9]{11}"
                     required
                   />
                 </div>
               </div>
            )}

            {formData.payment_method === 'instapay' && (
               <div className="form-grid">
                 <div className="form-group">
                   <label className="label">Phone Number *</label>
                   <input 
                     name="wallet_number" 
                     value={formData.wallet_number} 
                     onChange={handleChange} 
                     className="input-field"
                     placeholder="11 digits (no country code)"
                     maxLength={11}
                     pattern="[0-9]{11}"
                     required
                   />
                 </div>
               </div>
            )}
          </div>
        )}

        {step === 3 && (
          <div className="form-animation">
             <h3 className="section-title">Assignment</h3>
             <div className="form-grid">
               <div className="form-group">
                 <label className="label">Site</label>
                 <select name="site_id" value={formData.site_id} onChange={handleChange} className="select-field">
                   <option value="">Select Site...</option>
                   {locations.map(l => (
                     <option key={l.id} value={l.id}>{l.name}</option>
                   ))}
                 </select>
               </div>
               <div className="form-group">
                 <label className="label">Shift</label>
                 <select name="shift_id" value={formData.shift_id} onChange={handleChange} className="select-field">
                   <option value="">Select Shift...</option>
                   {shifts.map(s => (
                     <option key={s.id} value={s.id}>{s.name} ({s.start_time}-{s.end_time})</option>
                   ))}
                 </select>
               </div>
               <div className="form-group">
                 <label className="label">Rate</label>
                 <input name="rate" type="number" value={formData.rate} onChange={handleChange} className="input-field" placeholder="0.00" />
               </div>
               <div className="form-group">
                 <label className="label">Title</label>
                 <input name="assignment_title" value={formData.assignment_title} onChange={handleChange} className="input-field" placeholder="e.g. Guard" />
               </div>
               <div className="form-group">
                 <label className="label">Effective From</label>
                 <input name="effective_from" type="date" value={formData.effective_from} onChange={handleChange} className="input-field" />
               </div>
               <div className="form-group">
                 <label className="label">Effective To</label>
                 <input name="effective_to" type="date" value={formData.effective_to} onChange={handleChange} className="input-field" />
               </div>
             </div>
          </div>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '2rem' }}>
        <button 
          onClick={handleBack} 
          className="btn btn-secondary" 
          disabled={step === 1 || loading}
          style={{ visibility: step === 1 ? 'hidden' : 'visible' }}
        >
          Back
        </button>
        
        {step < 3 ? (
          <button onClick={handleNext} className="btn btn-primary">Next</button>
        ) : (
          <button onClick={handleSubmit} className="btn btn-primary" disabled={loading}>
            {loading ? 'Registering...' : 'Submit Registration'}
          </button>
        )}
      </div>
    </div>
  );
};

export default PersonRegistrationWizard;
