import { API_BASE_URL, API_ENDPOINTS } from "../config/api";

const AUTH_UNAUTHORIZED_EVENT = "auth:unauthorized";

/**
 * Get access token from localStorage
 */
const getAccessToken = () => {
  return localStorage.getItem('access_token');
};

/**
 * Turn API error detail (string or array of { msg, loc }) into a single display string
 */
function formatErrorDetail(detail, fallback = "An error occurred") {
  if (detail == null) return fallback;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((d) => (d && typeof d.msg === "string" ? d.msg : JSON.stringify(d))).join(". ");
  }
  if (typeof detail === "object" && detail.message) return detail.message;
  return fallback;
}

/**
 * API Client utility functions
 */
class ApiClient {
  constructor(baseURL) {
    this.baseURL = baseURL;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const token = getAccessToken();
    
    const config = {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(token && { "Authorization": `Bearer ${token}` }),
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);
      
      // Handle non-JSON responses (e.g., 401, 403)
      let data;
      const contentType = response.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
        data = await response.json();
      } else {
        const text = await response.text();
        data = { detail: text || "An error occurred" };
      }

      if (!response.ok) {
        // Handle 401 Unauthorized - token might be expired
        if (response.status === 401) {
          // Clear auth data and redirect to login
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('user');
          if (typeof window !== "undefined") {
            window.dispatchEvent(new Event(AUTH_UNAUTHORIZED_EVENT));
          }
        }
        throw new Error(formatErrorDetail(data.detail, data.message || "An error occurred"));
      }

      return data;
    } catch (error) {
      throw error;
    }
  }

  async uploadFile(endpoint, file, additionalData = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const token = getAccessToken();
    const formData = new FormData();
    formData.append("file", file);

    // Append additional data as form fields
    Object.entries(additionalData).forEach(([key, value]) => {
      if (value !== null && value !== undefined) {
        formData.append(key, value);
      }
    });

    const headers = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, {
        method: "POST",
        headers,
        body: formData,
      });

      let data;
      const contentType = response.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
        data = await response.json();
      } else {
        const text = await response.text();
        data = { detail: text || "Upload failed" };
      }

      if (!response.ok) {
        if (response.status === 401) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('user');
          if (typeof window !== "undefined") {
            window.dispatchEvent(new Event(AUTH_UNAUTHORIZED_EVENT));
          }
        }
        throw new Error(formatErrorDetail(data.detail, data.message || "Upload failed"));
      }

      return data;
    } catch (error) {
      throw error;
    }
  }

  async requestBlob(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const token = getAccessToken();
    const config = {
      ...options,
      headers: {
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers,
      },
    };

    const response = await fetch(url, config);
    if (!response.ok) {
      if (response.status === 401) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        localStorage.removeItem("user");
        if (typeof window !== "undefined") {
          window.dispatchEvent(new Event(AUTH_UNAUTHORIZED_EVENT));
        }
      }
      let detail = "Failed to download file";
      try {
        const data = await response.json();
        detail = formatErrorDetail(data.detail, detail);
      } catch {
        const text = await response.text();
        if (text) detail = text;
      }
      throw new Error(detail);
    }

    const blob = await response.blob();
    const contentDisposition = response.headers.get("content-disposition") || "";
    const nameMatch = contentDisposition.match(/filename="?([^"]+)"?/i);
    const filename = nameMatch?.[1] || "download";
    return { blob, filename };
  }
}

const apiClient = new ApiClient(API_BASE_URL);

/**
 * Login user
 */
export const login = async (credentials) => {
  const formData = new FormData();
  formData.append('username', credentials.username);
  formData.append('password', credentials.password);
  
  // Login endpoint expects form data for OAuth2
  const url = `${API_BASE_URL}${API_ENDPOINTS.LOGIN}`;
  const response = await fetch(url, {
      method: 'POST',
      body: formData,
  });
  
  const data = await response.json();
  if (!response.ok) {
      throw new Error(data.detail || "Login failed");
  }
  return data;
};

/**
 * Change current user's password
 */
export const changePassword = async ({ current_password, new_password }) => {
  return apiClient.request(API_ENDPOINTS.CHANGE_PASSWORD, {
    method: "POST",
    body: JSON.stringify({ current_password, new_password }),
  });
};

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
    method: "PATCH",
    body: JSON.stringify(employeeData),
  });
};

/**
 * Soft-delete employee
 */
export const deleteEmployee = async (employeeId) => {
  return apiClient.request(API_ENDPOINTS.DELETE_EMPLOYEE(employeeId), {
    method: "DELETE",
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

/**
 * Check if national ID or passport is already registered (for live form validation).
 * @returns {{ nationalID_taken: boolean, passport_taken: boolean }}
 */
export const checkIdentity = async (nationalID = "", passport = "") => {
  const params = new URLSearchParams();
  if (nationalID != null && String(nationalID).trim()) params.set("national_id", String(nationalID).trim());
  if (passport != null && String(passport).trim()) params.set("passport", String(passport).trim());
  const query = params.toString();
  const endpoint = query ? `${API_ENDPOINTS.CHECK_IDENTITY}?${query}` : API_ENDPOINTS.CHECK_IDENTITY;
  return apiClient.request(endpoint);
};

/**
 * Save payment info for an employee
 */
export const savePaymentInfo = async (employeeId, paymentData) => {
  return apiClient.request(API_ENDPOINTS.PAYMENT_INFO(employeeId), {
    method: "POST",
    body: JSON.stringify(paymentData),
  });
};

/**
 * Upload a document for an employee
 */
export const uploadDocument = async (employeeId, file, docType) => {
  return apiClient.uploadFile(API_ENDPOINTS.UPLOAD_DOCUMENT(employeeId), file, {
    type: docType,
  });
};

/**
 * List employee documents
 */
export const listEmployeeDocuments = async (employeeId) => {
  return apiClient.request(API_ENDPOINTS.LIST_DOCUMENTS(employeeId));
};

/**
 * Delete employee document
 */
export const deleteEmployeeDocument = async (employeeId, docId) => {
  return apiClient.request(API_ENDPOINTS.DELETE_DOCUMENT(employeeId, docId), {
    method: "DELETE",
  });
};

/**
 * Download employee document
 */
export const downloadEmployeeDocument = async (employeeId, docId) => {
  return apiClient.requestBlob(API_ENDPOINTS.DOWNLOAD_DOCUMENT(employeeId, docId));
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
export const verifyAttendance = async (imageFile, siteId = null, shiftId = null) => {
  return apiClient.uploadFile(API_ENDPOINTS.VERIFY_ATTENDANCE, imageFile, {
    site_id: siteId,
    shift_id: shiftId,
  });
};

/**
 * Record check-in
 */
export const checkIn = async (imageFile, siteId = null, shiftId = null) => {
  return apiClient.uploadFile(API_ENDPOINTS.CHECK_IN, imageFile, {
    site_id: siteId,
    shift_id: shiftId,
  });
};

/**
 * Record check-out
 */
export const checkOut = async (imageFile, siteId = null, shiftId = null) => {
  return apiClient.uploadFile(API_ENDPOINTS.CHECK_OUT, imageFile, {
    site_id: siteId,
    shift_id: shiftId,
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
 * Import attendance rows
 */
export const importAttendanceRows = async (rows, replaceExisting = false) => {
  return apiClient.request(API_ENDPOINTS.IMPORT_ATTENDANCE, {
    method: "POST",
    body: JSON.stringify({
      rows,
      replace_existing: replaceExisting,
    }),
  });
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
 * Submit overtime request
 */
export const submitOvertimeRequest = async (overtimeData) => {
  return apiClient.request(API_ENDPOINTS.OVERTIME_REQUESTS, {
    method: "POST",
    body: JSON.stringify(overtimeData),
  });
};

/**
 * Approve overtime request
 */
export const approveOvertime = async (overtimeId) => {
  return apiClient.request(API_ENDPOINTS.OVERTIME_REQUEST(overtimeId), {
    method: "PATCH",
    body: JSON.stringify({ status: "approved" }),
  });
};

/**
 * Reject overtime request
 */
export const rejectOvertime = async (overtimeId, reason = "") => {
  return apiClient.request(API_ENDPOINTS.OVERTIME_REQUEST(overtimeId), {
    method: "PATCH",
    body: JSON.stringify({ status: "rejected", rejection_reason: reason }),
  });
};

/**
 * Delete overtime request
 */
export const deleteOvertimeRequest = async (overtimeId) => {
  return apiClient.request(API_ENDPOINTS.OVERTIME_REQUEST(overtimeId), {
    method: "DELETE",
  });
};
