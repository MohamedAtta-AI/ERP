// API Configuration
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// API Endpoints
export const API_ENDPOINTS = {
  REGISTER_EMPLOYEE: "/api/v1/employees/register",
  ENROLL_FACE: (employeeId) => `/api/v1/employees/${employeeId}/enroll-face`,
  GET_EMPLOYEE: (employeeId) => `/api/v1/employees/${employeeId}`,
  VERIFY_ATTENDANCE: "/api/v1/attendance/verify",
  CHECK_IN: "/api/v1/attendance/check-in",
  CHECK_OUT: "/api/v1/attendance/check-out",
  ATTENDANCE_HISTORY: "/api/v1/attendance/history",
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
