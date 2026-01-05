import { useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import ProtectedRoute from "./components/Common/ProtectedRoute";
import LoginPage from "./components/Auth/LoginPage";
import MainDashboard from "./components/Dashboard/MainDashboard";
import AttendancePage from "./components/Attendance/AttendancePage";
import RegistrationPage from "./components/Registration/RegistrationPage";
import AdminPage from "./components/Admin/AdminPage";
import LocationsPage from "./components/Admin/LocationsPage";
import ShiftsPage from "./components/Admin/ShiftsPage";
import SkillsPage from "./components/Admin/SkillsPage";
import PersonsPage from "./components/Admin/PersonsPage";
import PayrollDashboard from "./components/Admin/PayrollDashboard";
import SalaryAdvancesPage from "./components/Admin/SalaryAdvancesPage";
import LoansPage from "./components/Admin/LoansPage";
import ReportsPage from "./components/Admin/ReportsPage";
import WorkersPage from "./components/Supervisor/WorkersPage";
import OvertimeManagementPage from "./components/Supervisor/OvertimeManagementPage";
import LoadingSpinner from "./components/Common/LoadingSpinner";
import { faceDetectionService } from "./services/faceDetectionService";

// Role-based redirect component
const RoleBasedRedirect = () => {
  const { user, loading } = useAuth();
  
  // Wait for auth state to be restored from localStorage
  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh'
      }}>
        <LoadingSpinner size="large" message="Loading session..." />
      </div>
    );
  }
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  
  // Both admin and supervisor go to the same dashboard
  return <Navigate to="/dashboard" replace />;
};

function App() {
  // Preload face detection models on app startup
  useEffect(() => {
    faceDetectionService.ensureModelsLoaded().catch((err) => {
      console.warn("Face detection preload failed, will retry on use:", err);
    });
  }, []);

  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />
          
          {/* Protected routes - admin and supervisor only */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute allowedRoles={['admin', 'supervisor']}>
                <MainDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/attendance"
            element={
              <ProtectedRoute allowedRoles={['admin', 'supervisor']}>
                <AttendancePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/register"
            element={
              <ProtectedRoute allowedRoles={['admin', 'supervisor']}>
                <RegistrationPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <AdminPage />
              </ProtectedRoute>
            }
          />
          {/* Admin pages */}
          <Route
            path="/admin/locations"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <LocationsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/shifts"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <ShiftsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/skills"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <SkillsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/persons"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <PersonsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/payroll"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <PayrollDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/advances"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <SalaryAdvancesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/loans"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <LoansPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/reports"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <ReportsPage />
              </ProtectedRoute>
            }
          />
          {/* Supervisor pages */}
          <Route
            path="/supervisor/workers"
            element={
              <ProtectedRoute allowedRoles={['supervisor', 'admin']}>
                <WorkersPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/supervisor/overtime"
            element={
              <ProtectedRoute allowedRoles={['supervisor', 'admin']}>
                <OvertimeManagementPage />
              </ProtectedRoute>
            }
          />
          
          {/* Default redirect */}
          <Route path="/" element={<RoleBasedRedirect />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
