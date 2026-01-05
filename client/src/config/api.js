// API Configuration
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// API Endpoints
export const API_ENDPOINTS = {
  // Employee/Person endpoints
  REGISTER_EMPLOYEE: "/api/v1/employees/register",
  UPDATE_EMPLOYEE: (employeeId) => `/api/v1/employees/${employeeId}`,
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
  
  // Auth endpoints
  LOGIN: "/api/v1/auth/login",
  REFRESH: "/api/v1/auth/refresh",
  LOGOUT: "/api/v1/auth/logout",
  ME: "/api/v1/auth/me",
  
  // Payroll endpoints (additional)
  PREVIEW_PAYROLL: (runId) => `/api/v1/payroll/runs/${runId}/preview`,
  APPROVE_PAYROLL: (runId) => `/api/v1/payroll/runs/${runId}/approve`,
  LOCK_PAYROLL: (runId) => `/api/v1/payroll/runs/${runId}/lock`,
  RETROACTIVE_PAYROLL: (runId) => `/api/v1/payroll/runs/${runId}/retroactive`,
  
  // Salary advances
  SALARY_ADVANCES: "/api/v1/salary-advances",
  SALARY_ADVANCE: (id) => `/api/v1/salary-advances/${id}`,
  APPROVE_ADVANCE: (id) => `/api/v1/salary-advances/${id}/approve`,
  
  // Loans
  LOANS: "/api/v1/loans",
  LOAN: (id) => `/api/v1/loans/${id}`,
  APPROVE_LOAN: (id) => `/api/v1/loans/${id}/approve`,
  LOAN_REPAYMENT_SCHEDULE: (id) => `/api/v1/loans/${id}/repayment-schedule`,
  
  // Payslips
  PAYSLIPS: "/api/v1/payslips",
  PAYSLIP: (id) => `/api/v1/payslips/${id}`,
  PAYSLIP_PDF: (id) => `/api/v1/payslips/${id}/pdf`,
  
  // Reports
  ATTENDANCE_REPORT: "/api/v1/reports/attendance",
  PAYROLL_REPORT: "/api/v1/reports/payroll",
  
  // Bank transfers
  BANK_TRANSFERS: "/api/v1/bank-transfers",
  BANK_TRANSFER_FILE: (id) => `/api/v1/bank-transfers/${id}/file`,
  
  // Settlements
  SETTLEMENTS: "/api/v1/settlements",
  SETTLEMENT: (id) => `/api/v1/settlements/${id}`,
  APPROVE_SETTLEMENT: (id) => `/api/v1/settlements/${id}/approve`,
  
  // Skills
  SKILLS: "/api/v1/skills",
  SKILL: (id) => `/api/v1/skills/${id}`,
  SKILL_LOCATION_PRICING: "/api/v1/skills/location-pricing",
  
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
