// API Configuration
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// API Endpoints
export const API_ENDPOINTS = {
  // Auth
  LOGIN: "/api/v1/auth/login",
  
  // Employee/Person endpoints
  REGISTER_EMPLOYEE: "/api/v1/employees",
  ENROLL_FACE: (employeeId) => `/api/v1/employees/${employeeId}/enroll-face`,
  GET_EMPLOYEE: (employeeId) => `/api/v1/employees/${employeeId}`,
  LIST_EMPLOYEES: "/api/v1/employees",
  CHECK_IDENTITY: "/api/v1/employees/check-identity",
  PAYMENT_INFO: (employeeId) => `/api/v1/employees/${employeeId}/payment-info`,
  UPLOAD_DOCUMENT: (employeeId) => `/api/v1/employees/${employeeId}/documents`,
  
  // Attendance endpoints
  VERIFY_ATTENDANCE: "/api/v1/attendance/verify",
  CHECK_IN: "/api/v1/attendance/check-in",
  CHECK_OUT: "/api/v1/attendance/check-out",
  ATTENDANCE_HISTORY: "/api/v1/attendance/history",
  RECONCILE_ATTENDANCE: "/api/v1/attendance/reconcile",
  
  // Location endpoints
  LOCATIONS: "/api/v1/locations",
  LOCATION: (id) => `/api/v1/locations/${id}`,
  
  // Shift endpoints
  SHIFTS: "/api/v1/shifts",
  SHIFT: (id) => `/api/v1/shifts/${id}`,
  
  // Assignment endpoints
  ASSIGNMENTS: "/api/v1/assignments",
  ASSIGNMENT: (id) => `/api/v1/assignments/${id}`,
  
  // Overtime endpoints
  OVERTIME_REQUESTS: "/api/v1/attendance/overtime",
  OVERTIME_REQUEST: (id) => `/api/v1/attendance/overtime/${id}`,
};

// Quality Check Thresholds
export const QUALITY_THRESHOLDS = {
  BRIGHTNESS_MIN: 50,
  BRIGHTNESS_MAX: 200,
  SHARPNESS_MIN: 100,
  FACE_SIZE_MIN: 0.2, // 20% of image area
  FACE_SIZE_MAX: 0.4, // 40% of image area
  HEAD_YAW_MAX: 15, // degrees
  HEAD_PITCH_MAX: 15, // degrees
  HEAD_ROLL_MAX: 15, // degrees
};

// Liveness Detection Settings
export const LIVENESS_SETTINGS = {
  REQUIRED_BLINKS: 1,
  HEAD_MOVEMENT_THRESHOLD: 10, // degrees
  TIMEOUT_SECONDS: 30,
};

// Auto Capture Settings
export const AUTO_CAPTURE_SETTINGS = {
  FRAMES_TO_CAPTURE: 3,
  QUALITY_CHECK_DURATION: 2000, // ms
};
