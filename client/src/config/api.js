// API Configuration
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// API Endpoints
export const API_ENDPOINTS = {
  // Employee/Person endpoints
  REGISTER_EMPLOYEE: "/api/v1/employees/register",
  ENROLL_FACE: (employeeId) => `/api/v1/employees/${employeeId}/enroll-face`,
  GET_EMPLOYEE: (employeeId) => `/api/v1/employees/${employeeId}`,
  LIST_EMPLOYEES: "/api/v1/employees",
  
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
  
  // Payroll endpoints
  PAYROLL_PERIODS: "/api/v1/payroll/periods",
  PAYROLL_RUNS: "/api/v1/payroll/runs",
  PAYROLL_RUN: (runId) => `/api/v1/payroll/runs/${runId}`,
  PAYROLL_COMPONENTS: "/api/v1/payroll/components",
  EMPLOYEE_COMPONENTS: (employeeId) => `/api/v1/payroll/employee-components/${employeeId}`,
  
  // Overtime endpoints
  OVERTIME_REQUESTS: "/api/v1/overtime",
  OVERTIME_REQUEST: (id) => `/api/v1/overtime/${id}`,
  APPROVE_OVERTIME: (id) => `/api/v1/overtime/${id}/approve`,
  REJECT_OVERTIME: (id) => `/api/v1/overtime/${id}/reject`,
  
  // Health
  HEALTH: "/api/v1/health",
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
