import { API_BASE_URL, API_ENDPOINTS } from "../config/api";

/**
 * API Client utility functions with JWT token refresh
 */
class ApiClient {
  constructor(baseURL) {
    this.baseURL = baseURL;
  }

  getAccessToken() {
    return localStorage.getItem("access_token");
  }

  getRefreshToken() {
    return localStorage.getItem("refresh_token");
  }

  setTokens(accessToken, refreshToken) {
    localStorage.setItem("access_token", accessToken);
    if (refreshToken) {
      localStorage.setItem("refresh_token", refreshToken);
    }
  }

  clearTokens() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  }

  async refreshAccessToken() {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      throw new Error("No refresh token available");
    }

    try {
      const response = await fetch(`${this.baseURL}/api/v1/auth/refresh`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) {
        this.clearTokens();
        throw new Error("Token refresh failed");
      }

      const data = await response.json();
      this.setTokens(data.access_token, null);
      return data.access_token;
    } catch (error) {
      this.clearTokens();
      throw error;
    }
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const accessToken = this.getAccessToken();
    
    const config = {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(accessToken && { Authorization: `Bearer ${accessToken}` }),
        ...options.headers,
      },
    };

    try {
      let response = await fetch(url, config);
      
      // Handle 401 - try to refresh token
      if (response.status === 401 && accessToken) {
        try {
          const newToken = await this.refreshAccessToken();
          // Retry with new token
          config.headers.Authorization = `Bearer ${newToken}`;
          response = await fetch(url, config);
        } catch (refreshError) {
          // Refresh failed, redirect to login
          window.location.href = "/login";
          throw new Error("Session expired. Please login again.");
        }
      }

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.message || "An error occurred");
      }

      return data;
    } catch (error) {
      throw error;
    }
  }

  async uploadFile(endpoint, file, additionalData = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const accessToken = this.getAccessToken();
    const formData = new FormData();
    formData.append("file", file);

    // Append additional data as form fields
    Object.entries(additionalData).forEach(([key, value]) => {
      if (value !== null && value !== undefined) {
        formData.append(key, value);
      }
    });

    try {
      const headers = {};
      if (accessToken) {
        headers.Authorization = `Bearer ${accessToken}`;
      }

      let response = await fetch(url, {
        method: "POST",
        headers: headers,
        body: formData,
      });

      // Handle 401 - try to refresh token
      if (response.status === 401 && accessToken) {
        try {
          const newToken = await this.refreshAccessToken();
          // Retry with new token
          headers.Authorization = `Bearer ${newToken}`;
          response = await fetch(url, {
            method: "POST",
            headers: headers,
            body: formData,
          });
        } catch (refreshError) {
          // Refresh failed, redirect to login
          window.location.href = "/login";
          throw new Error("Session expired. Please login again.");
        }
      }

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.message || "Upload failed");
      }

      return data;
    } catch (error) {
      throw error;
    }
  }
}

const apiClient = new ApiClient(API_BASE_URL);

// ============================================================
// Employee/Person API
// ============================================================

/**
 * Register a new employee
 */
export const registerEmployee = async (employeeData) => {
  return apiClient.request(API_ENDPOINTS.REGISTER_EMPLOYEE, {
    method: "POST",
    body: JSON.stringify(employeeData),
  });
};

/**
 * Enroll face for an employee
 */
export const enrollFace = async (employeeId, imageFile) => {
  return apiClient.uploadFile(API_ENDPOINTS.ENROLL_FACE(employeeId), imageFile);
};

/**
 * Get employee details
 */
export const getEmployee = async (employeeId) => {
  return apiClient.request(API_ENDPOINTS.GET_EMPLOYEE(employeeId));
};

/**
 * Update employee details
 */
export const updateEmployee = async (employeeId, employeeData) => {
  return apiClient.request(API_ENDPOINTS.UPDATE_EMPLOYEE(employeeId), {
    method: "PUT",
    body: JSON.stringify(employeeData),
  });
};

/**
 * List all employees
 */
export const listEmployees = async (params = {}) => {
  const queryParams = new URLSearchParams();
  if (params.status) queryParams.append("status", params.status);
  if (params.role) queryParams.append("role", params.role);
  if (params.limit) queryParams.append("limit", params.limit);
  const queryString = queryParams.toString();
  const endpoint = queryString ? `${API_ENDPOINTS.LIST_EMPLOYEES}?${queryString}` : API_ENDPOINTS.LIST_EMPLOYEES;
  return apiClient.request(endpoint);
};

// ============================================================
// Location API
// ============================================================

/**
 * List all locations
 */
export const listLocations = async (activeOnly = true) => {
  const endpoint = `${API_ENDPOINTS.LOCATIONS}?active_only=${activeOnly}`;
  return apiClient.request(endpoint);
};

/**
 * Create a new location
 */
export const createLocation = async (locationData) => {
  return apiClient.request(API_ENDPOINTS.LOCATIONS, {
    method: "POST",
    body: JSON.stringify(locationData),
  });
};

/**
 * Update a location
 */
export const updateLocation = async (locationId, locationData) => {
  return apiClient.request(API_ENDPOINTS.LOCATION(locationId), {
    method: "PUT",
    body: JSON.stringify(locationData),
  });
};

/**
 * Delete a location
 */
export const deleteLocation = async (locationId) => {
  return apiClient.request(API_ENDPOINTS.LOCATION(locationId), {
    method: "DELETE",
  });
};

// ============================================================
// Shift API
// ============================================================

/**
 * List all shifts
 */
export const listShifts = async (activeOnly = true) => {
  const endpoint = `${API_ENDPOINTS.SHIFTS}?active_only=${activeOnly}`;
  return apiClient.request(endpoint);
};

/**
 * Create a new shift
 */
export const createShift = async (shiftData) => {
  return apiClient.request(API_ENDPOINTS.SHIFTS, {
    method: "POST",
    body: JSON.stringify(shiftData),
  });
};

/**
 * Update a shift
 */
export const updateShift = async (shiftId, shiftData) => {
  return apiClient.request(API_ENDPOINTS.SHIFT(shiftId), {
    method: "PUT",
    body: JSON.stringify(shiftData),
  });
};

/**
 * Delete a shift
 */
export const deleteShift = async (shiftId) => {
  return apiClient.request(API_ENDPOINTS.SHIFT(shiftId), {
    method: "DELETE",
  });
};

// ============================================================
// Assignment API
// ============================================================

/**
 * List all assignments
 */
export const listAssignments = async (params = {}) => {
  const queryParams = new URLSearchParams();
  if (params.person_id) queryParams.append("person_id", params.person_id);
  if (params.location_id) queryParams.append("location_id", params.location_id);
  if (params.active_only !== undefined) queryParams.append("active_only", params.active_only);
  const queryString = queryParams.toString();
  const endpoint = queryString ? `${API_ENDPOINTS.ASSIGNMENTS}?${queryString}` : API_ENDPOINTS.ASSIGNMENTS;
  return apiClient.request(endpoint);
};

/**
 * Create a new assignment
 */
export const createAssignment = async (assignmentData) => {
  return apiClient.request(API_ENDPOINTS.ASSIGNMENTS, {
    method: "POST",
    body: JSON.stringify(assignmentData),
  });
};

/**
 * Update an assignment
 */
export const updateAssignment = async (assignmentId, assignmentData) => {
  return apiClient.request(API_ENDPOINTS.ASSIGNMENT(assignmentId), {
    method: "PUT",
    body: JSON.stringify(assignmentData),
  });
};

/**
 * Delete an assignment
 */
export const deleteAssignment = async (assignmentId) => {
  return apiClient.request(API_ENDPOINTS.ASSIGNMENT(assignmentId), {
    method: "DELETE",
  });
};

// ============================================================
// Attendance API
// ============================================================

/**
 * Verify attendance (face recognition)
 */
export const verifyAttendance = async (imageFile, locationId = null, shiftId = null) => {
  return apiClient.uploadFile(API_ENDPOINTS.VERIFY_ATTENDANCE, imageFile, {
    location_id: locationId,
    shift_id: shiftId,
  });
};

/**
 * Record check-in
 */
export const checkIn = async (personId, locationId = null, shiftId = null) => {
  return apiClient.request(API_ENDPOINTS.CHECK_IN, {
    method: "POST",
    body: JSON.stringify({ 
      person_id: personId, 
      location_id: locationId,
      shift_id: shiftId,
    }),
  });
};

/**
 * Record check-out
 */
export const checkOut = async (personId) => {
  return apiClient.request(API_ENDPOINTS.CHECK_OUT, {
    method: "POST",
    body: JSON.stringify({ person_id: personId }),
  });
};

/**
 * Get attendance history
 */
export const getAttendanceHistory = async (params = {}) => {
  const queryParams = new URLSearchParams();
  if (params.person_id) queryParams.append("person_id", params.person_id);
  if (params.start_date) queryParams.append("start_date", params.start_date);
  if (params.end_date) queryParams.append("end_date", params.end_date);
  if (params.limit) queryParams.append("limit", params.limit);
  const queryString = queryParams.toString();
  const endpoint = queryString ? `${API_ENDPOINTS.ATTENDANCE_HISTORY}?${queryString}` : API_ENDPOINTS.ATTENDANCE_HISTORY;
  return apiClient.request(endpoint);
};

/**
 * Reconcile attendance for a date (mark absent, create overtime requests)
 */
export const reconcileAttendance = async (targetDate = null) => {
  const body = targetDate ? { target_date: targetDate } : {};
  return apiClient.request(API_ENDPOINTS.RECONCILE_ATTENDANCE, {
    method: "POST",
    body: JSON.stringify(body),
  });
};

// ============================================================
// Payroll API
// ============================================================

/**
 * List payroll periods
 */
export const listPayrollPeriods = async () => {
  return apiClient.request(API_ENDPOINTS.PAYROLL_PERIODS);
};

/**
 * Create a payroll period
 */
export const createPayrollPeriod = async (periodData) => {
  return apiClient.request(API_ENDPOINTS.PAYROLL_PERIODS, {
    method: "POST",
    body: JSON.stringify(periodData),
  });
};

/**
 * List salary components
 */
export const listSalaryComponents = async () => {
  return apiClient.request(API_ENDPOINTS.PAYROLL_COMPONENTS);
};

/**
 * Create a salary component
 */
export const createSalaryComponent = async (componentData) => {
  return apiClient.request(API_ENDPOINTS.PAYROLL_COMPONENTS, {
    method: "POST",
    body: JSON.stringify(componentData),
  });
};

/**
 * Get employee salary components
 */
export const getEmployeeComponents = async (employeeId) => {
  return apiClient.request(API_ENDPOINTS.EMPLOYEE_COMPONENTS(employeeId));
};

/**
 * Set employee salary component override
 */
export const setEmployeeComponent = async (employeeId, componentId, valueOverride) => {
  return apiClient.request(API_ENDPOINTS.EMPLOYEE_COMPONENTS(employeeId), {
    method: "POST",
    body: JSON.stringify({ component_id: componentId, value_override: valueOverride }),
  });
};

/**
 * Create/run payroll for a period
 */
export const createPayrollRun = async (periodId, locationId = null) => {
  return apiClient.request(API_ENDPOINTS.PAYROLL_RUNS, {
    method: "POST",
    body: JSON.stringify({ period_id: periodId, location_id: locationId }),
  });
};

/**
 * Get payroll run details
 */
export const getPayrollRun = async (runId) => {
  return apiClient.request(API_ENDPOINTS.PAYROLL_RUN(runId));
};

/**
 * List payroll runs
 */
export const listPayrollRuns = async (periodId = null) => {
  const endpoint = periodId 
    ? `${API_ENDPOINTS.PAYROLL_RUNS}?period_id=${periodId}` 
    : API_ENDPOINTS.PAYROLL_RUNS;
  return apiClient.request(endpoint);
};

// ============================================================
// Overtime API
// ============================================================

/**
 * List overtime requests
 */
export const listOvertimeRequests = async (params = {}) => {
  const queryParams = new URLSearchParams();
  if (params.person_id) queryParams.append("person_id", params.person_id);
  if (params.status) queryParams.append("status", params.status);
  if (params.start_date) queryParams.append("start_date", params.start_date);
  if (params.end_date) queryParams.append("end_date", params.end_date);
  const queryString = queryParams.toString();
  const endpoint = queryString ? `${API_ENDPOINTS.OVERTIME_REQUESTS}?${queryString}` : API_ENDPOINTS.OVERTIME_REQUESTS;
  return apiClient.request(endpoint);
};

/**
 * Create an overtime request
 */
export const createOvertimeRequest = async (overtimeData) => {
  return apiClient.request(API_ENDPOINTS.OVERTIME_REQUESTS, {
    method: "POST",
    body: JSON.stringify(overtimeData),
  });
};

/**
 * Approve overtime request
 */
export const approveOvertime = async (overtimeId) => {
  return apiClient.request(API_ENDPOINTS.APPROVE_OVERTIME(overtimeId), {
    method: "POST",
  });
};

/**
 * Reject overtime request
 */
export const rejectOvertime = async (overtimeId, reason = "") => {
  return apiClient.request(API_ENDPOINTS.REJECT_OVERTIME(overtimeId), {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
};

// ============================================================
// Auth API
// ============================================================

/**
 * Login
 */
export const login = async (personId) => {
  return apiClient.request(API_ENDPOINTS.LOGIN, {
    method: "POST",
    body: JSON.stringify({ person_id: personId }),
  });
};

/**
 * Refresh token
 */
export const refreshToken = async (refreshToken) => {
  return apiClient.request(API_ENDPOINTS.REFRESH, {
    method: "POST",
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
};

/**
 * Logout
 */
export const logout = async () => {
  return apiClient.request(API_ENDPOINTS.LOGOUT, {
    method: "POST",
  });
};

/**
 * Get current user
 */
export const getCurrentUser = async () => {
  return apiClient.request(API_ENDPOINTS.ME);
};

// ============================================================
// Skills API
// ============================================================

/**
 * List all skills
 */
export const listSkills = async () => {
  return apiClient.request(API_ENDPOINTS.SKILLS);
};

/**
 * Create a skill
 */
export const createSkill = async (skillData) => {
  return apiClient.request(API_ENDPOINTS.SKILLS, {
    method: "POST",
    body: JSON.stringify(skillData),
  });
};

/**
 * Update a skill
 */
export const updateSkill = async (skillId, skillData) => {
  return apiClient.request(API_ENDPOINTS.SKILL(skillId), {
    method: "PUT",
    body: JSON.stringify(skillData),
  });
};

/**
 * Delete a skill
 */
export const deleteSkill = async (skillId) => {
  return apiClient.request(API_ENDPOINTS.SKILL(skillId), {
    method: "DELETE",
  });
};

// ============================================================
// Salary Advances API
// ============================================================

/**
 * List salary advances
 */
export const listSalaryAdvances = async (params = {}) => {
  const queryParams = new URLSearchParams();
  if (params.person_id) queryParams.append("person_id", params.person_id);
  if (params.status) queryParams.append("status", params.status);
  const queryString = queryParams.toString();
  const endpoint = queryString ? `${API_ENDPOINTS.SALARY_ADVANCES}?${queryString}` : API_ENDPOINTS.SALARY_ADVANCES;
  return apiClient.request(endpoint);
};

/**
 * Create a salary advance
 */
export const createSalaryAdvance = async (advanceData) => {
  return apiClient.request(API_ENDPOINTS.SALARY_ADVANCES, {
    method: "POST",
    body: JSON.stringify(advanceData),
  });
};

/**
 * Get salary advance
 */
export const getSalaryAdvance = async (advanceId) => {
  return apiClient.request(API_ENDPOINTS.SALARY_ADVANCE(advanceId));
};

/**
 * Approve salary advance
 */
export const approveSalaryAdvance = async (advanceId) => {
  return apiClient.request(API_ENDPOINTS.APPROVE_ADVANCE(advanceId), {
    method: "POST",
  });
};

// ============================================================
// Loans API
// ============================================================

/**
 * List loans
 */
export const listLoans = async (params = {}) => {
  const queryParams = new URLSearchParams();
  if (params.person_id) queryParams.append("person_id", params.person_id);
  if (params.status) queryParams.append("status", params.status);
  const queryString = queryParams.toString();
  const endpoint = queryString ? `${API_ENDPOINTS.LOANS}?${queryString}` : API_ENDPOINTS.LOANS;
  return apiClient.request(endpoint);
};

/**
 * Create a loan
 */
export const createLoan = async (loanData) => {
  return apiClient.request(API_ENDPOINTS.LOANS, {
    method: "POST",
    body: JSON.stringify(loanData),
  });
};

/**
 * Get loan
 */
export const getLoan = async (loanId) => {
  return apiClient.request(API_ENDPOINTS.LOAN(loanId));
};

/**
 * Approve loan
 */
export const approveLoan = async (loanId) => {
  return apiClient.request(API_ENDPOINTS.APPROVE_LOAN(loanId), {
    method: "POST",
  });
};

/**
 * Get loan repayment schedule
 */
export const getLoanRepaymentSchedule = async (loanId) => {
  return apiClient.request(API_ENDPOINTS.LOAN_REPAYMENT_SCHEDULE(loanId));
};

// ============================================================
// Payslips API
// ============================================================

/**
 * List payslips
 */
export const listPayslips = async (params = {}) => {
  const queryParams = new URLSearchParams();
  if (params.person_id) queryParams.append("person_id", params.person_id);
  if (params.period_id) queryParams.append("period_id", params.period_id);
  const queryString = queryParams.toString();
  const endpoint = queryString ? `${API_ENDPOINTS.PAYSLIPS}?${queryString}` : API_ENDPOINTS.PAYSLIPS;
  return apiClient.request(endpoint);
};

/**
 * Get payslip
 */
export const getPayslip = async (payslipId) => {
  return apiClient.request(API_ENDPOINTS.PAYSLIP(payslipId));
};

/**
 * Download payslip PDF
 */
export const downloadPayslipPDF = async (payslipId) => {
  const accessToken = apiClient.getAccessToken();
  const response = await fetch(`${apiClient.baseURL}${API_ENDPOINTS.PAYSLIP_PDF(payslipId)}`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
  if (!response.ok) throw new Error("Failed to download payslip");
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `payslip-${payslipId}.pdf`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
};

// ============================================================
// Reports API
// ============================================================

/**
 * Generate attendance report
 */
export const generateAttendanceReport = async (params) => {
  return apiClient.request(API_ENDPOINTS.ATTENDANCE_REPORT, {
    method: "POST",
    body: JSON.stringify(params),
  });
};

/**
 * Generate payroll report
 */
export const generatePayrollReport = async (params) => {
  return apiClient.request(API_ENDPOINTS.PAYROLL_REPORT, {
    method: "POST",
    body: JSON.stringify(params),
  });
};

// ============================================================
// Bank Transfers API
// ============================================================

/**
 * Generate bank transfer file
 */
export const generateBankTransferFile = async (runId) => {
  return apiClient.request(API_ENDPOINTS.BANK_TRANSFERS, {
    method: "POST",
    body: JSON.stringify({ payroll_run_id: runId }),
  });
};

/**
 * Download bank transfer file
 */
export const downloadBankTransferFile = async (fileId) => {
  const accessToken = apiClient.getAccessToken();
  const response = await fetch(`${apiClient.baseURL}${API_ENDPOINTS.BANK_TRANSFER_FILE(fileId)}`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
  if (!response.ok) throw new Error("Failed to download bank file");
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `bank-transfer-${fileId}.csv`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
};

// ============================================================
// Settlements API
// ============================================================

/**
 * Calculate settlement
 */
export const calculateSettlement = async (personId, settlementDate) => {
  return apiClient.request(API_ENDPOINTS.SETTLEMENTS, {
    method: "POST",
    body: JSON.stringify({ person_id: personId, settlement_date: settlementDate }),
  });
};

/**
 * Get settlement
 */
export const getSettlement = async (settlementId) => {
  return apiClient.request(API_ENDPOINTS.SETTLEMENT(settlementId));
};

/**
 * Approve settlement
 */
export const approveSettlement = async (settlementId) => {
  return apiClient.request(API_ENDPOINTS.APPROVE_SETTLEMENT(settlementId), {
    method: "POST",
  });
};

// ============================================================
// Payroll Run Operations
// ============================================================

/**
 * Preview payroll run
 */
export const previewPayrollRun = async (runId) => {
  return apiClient.request(API_ENDPOINTS.PREVIEW_PAYROLL(runId), {
    method: "POST",
  });
};

/**
 * Approve payroll run
 */
export const approvePayrollRun = async (runId) => {
  return apiClient.request(API_ENDPOINTS.APPROVE_PAYROLL(runId), {
    method: "POST",
  });
};

/**
 * Lock payroll run
 */
export const lockPayrollRun = async (runId) => {
  return apiClient.request(API_ENDPOINTS.LOCK_PAYROLL(runId), {
    method: "POST",
  });
};

/**
 * Retroactive payroll adjustment
 */
export const retroactivePayroll = async (runId, adjustmentDate, adjustments) => {
  return apiClient.request(API_ENDPOINTS.RETROACTIVE_PAYROLL(runId), {
    method: "POST",
    body: JSON.stringify({ adjustment_date: adjustmentDate, adjustments }),
  });
};

// ============================================================
// Health API
// ============================================================

/**
 * Health check
 */
export const healthCheck = async () => {
  return apiClient.request(API_ENDPOINTS.HEALTH);
};
