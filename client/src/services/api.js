import { API_BASE_URL, API_ENDPOINTS } from "../config/api";

/**
 * API Client utility functions
 */
class ApiClient {
  constructor(baseURL) {
    this.baseURL = baseURL;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);
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
    const formData = new FormData();
    formData.append("file", file);

    // Append additional data as JSON string if provided
    if (Object.keys(additionalData).length > 0) {
      formData.append("data", JSON.stringify(additionalData));
    }

    try {
      const response = await fetch(url, {
        method: "POST",
        body: formData,
      });

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
 * Verify attendance (face recognition)
 */
export const verifyAttendance = async (imageFile) => {
  return apiClient.uploadFile(API_ENDPOINTS.VERIFY_ATTENDANCE, imageFile);
};

/**
 * Record check-in
 */
export const checkIn = async (employeeId, location = null) => {
  return apiClient.request(API_ENDPOINTS.CHECK_IN, {
    method: "POST",
    body: JSON.stringify({ employee_id: employeeId, location }),
  });
};

/**
 * Record check-out
 */
export const checkOut = async (employeeId) => {
  return apiClient.request(API_ENDPOINTS.CHECK_OUT, {
    method: "POST",
    body: JSON.stringify({ employee_id: employeeId }),
  });
};

/**
 * Get attendance history
 */
export const getAttendanceHistory = async (employeeId = null) => {
  const endpoint = employeeId
    ? `${API_ENDPOINTS.ATTENDANCE_HISTORY}?employee_id=${employeeId}`
    : API_ENDPOINTS.ATTENDANCE_HISTORY;
  return apiClient.request(endpoint);
};

/**
 * Health check
 */
export const healthCheck = async () => {
  return apiClient.request(API_ENDPOINTS.HEALTH);
};
