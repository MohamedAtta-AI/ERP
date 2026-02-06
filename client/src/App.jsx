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
import PersonsPage from "./components/Admin/PersonsPage";
import ReportsPage from "./components/Admin/ReportsPage";
import LoadingSpinner from "./components/Common/LoadingSpinner";
import { faceDetectionService } from "./services/faceDetectionService";

// Role-based redirect component
const RoleBasedRedirect = () => {
  const { user, loading } = useAuth();
  
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
  
  return <Navigate to="/dashboard" replace />;
};

function App() {
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
          
          {/* Protected routes */}
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
            path="/admin/persons"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <PersonsPage />
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
          
          {/* Default redirect */}
          <Route path="/" element={<RoleBasedRedirect />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
